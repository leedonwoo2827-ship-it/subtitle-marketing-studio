"""Orchestrates studio execution: bulk parallel + single re-run.

Workers run in plain threads and DO NOT touch Streamlit. All UI updates
happen on the main thread using the returned RunReport.
"""
from __future__ import annotations

import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from core import docx_render, html_render, image_render, png_render
from studio import get_studio, list_studios
from studio._base import StudioContext


@dataclass
class StudioResult:
    key: str
    title: str
    status: str  # "pending" | "running" | "done" | "error"
    output: str = ""
    error: str = ""
    output_path: Path | None = None
    html_path: Path | None = None
    html: str = ""
    png_paths: list[Path] = field(default_factory=list)
    png_error: str = ""
    docx_path: Path | None = None
    docx_error: str = ""
    image_cost_usd: float = 0.0
    image_renderer_used: str = ""  # "image" (Nano Banana) | "playwright" | ""


@dataclass
class RunReport:
    results: dict[str, StudioResult] = field(default_factory=dict)


def studio_dir_name(studio) -> str:
    return f"{studio.order:02d}_{studio.key}"


def find_studio_dir(project_dir: Path, studio) -> Path | None:
    new = project_dir / studio_dir_name(studio)
    if new.exists():
        return new
    legacy = project_dir / studio.key
    if legacy.exists():
        return legacy
    return None


def _execute_one(key: str, ctx: StudioContext) -> StudioResult:
    studio = get_studio(key)
    res = StudioResult(key=key, title=studio.title, status="running")
    try:
        text = studio.render(ctx)
        legacy = ctx.project_dir / studio.key
        out_dir = ctx.project_dir / studio_dir_name(studio)
        if legacy.exists() and not out_dir.exists():
            legacy.rename(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        out_path = out_dir / "output.md"
        out_path.write_text(text, encoding="utf-8")
        res.output = text
        res.output_path = out_path

        html = html_render.render(
            studio.html_renderer, text,
            title=studio.title,
            brand=ctx.extra.get("brand_name", ""),
        )
        html_path = out_dir / "output.html"
        html_path.write_text(html, encoding="utf-8")
        res.html = html
        res.html_path = html_path

        # Card studios → Playwright PNG (HTML+CSS via Jinja2 template).
        # Image generation (Nano Banana) is kept available as opt-in only.
        if studio.png_renderer:
            png_result = png_render.render(studio.png_renderer, html, out_dir)
            res.png_paths = list(png_result.paths)
            res.png_error = png_result.error
            res.image_renderer_used = "playwright" if png_result.paths else ""

        if studio.docx_renderer:
            docx_result = docx_render.render(studio.docx_renderer, text, out_dir)
            res.docx_path = docx_result.path
            res.docx_error = docx_result.error

        res.status = "done"
    except Exception as e:
        res.error = f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=4)}"
        res.status = "error"
    return res


def run_all(
    ctx: StudioContext,
    *,
    keys: Iterable[str] | None = None,
) -> RunReport:
    selected = list(keys) if keys is not None else [s.key for s in list_studios()]
    workers = 1 if ctx.llm.is_local else max(1, int(getattr(ctx, "parallelism", 4)))
    report = RunReport()
    lock = threading.Lock()

    def _wrap(k: str) -> StudioResult:
        try:
            r = _execute_one(k, ctx)
        except Exception as e:
            r = StudioResult(
                key=k,
                title=get_studio(k).title if k else "?",
                status="error",
                error=f"runner: {type(e).__name__}: {e}\n{traceback.format_exc(limit=4)}",
            )
        with lock:
            report.results[k] = r
        return r

    if workers == 1:
        for k in selected:
            _wrap(k)
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(_wrap, k): k for k in selected}
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    k = futures[f]
                    with lock:
                        report.results.setdefault(
                            k,
                            StudioResult(
                                key=k,
                                title=get_studio(k).title,
                                status="error",
                                error=f"future: {type(e).__name__}: {e}",
                            ),
                        )

    for k in selected:
        report.results.setdefault(
            k,
            StudioResult(
                key=k, title=get_studio(k).title, status="error",
                error="worker returned no result (silently swallowed)",
            ),
        )
    return report


def run_one(ctx: StudioContext, key: str) -> StudioResult:
    return _execute_one(key, ctx)
