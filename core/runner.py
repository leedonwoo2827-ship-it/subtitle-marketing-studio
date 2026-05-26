"""Orchestrates studio execution: bulk parallel + single re-run."""
from __future__ import annotations

import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

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


@dataclass
class RunReport:
    results: dict[str, StudioResult] = field(default_factory=dict)


def _execute_one(key: str, ctx: StudioContext) -> StudioResult:
    studio = get_studio(key)
    res = StudioResult(key=key, title=studio.title, status="running")
    try:
        text = studio.render(ctx)
        out_dir = ctx.project_dir / key
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / studio.output_filename
        out_path.write_text(text, encoding="utf-8")
        res.output = text
        res.output_path = out_path
        res.status = "done"
    except Exception as e:
        res.error = f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}"
        res.status = "error"
    return res


def run_all(
    ctx: StudioContext,
    *,
    on_progress: Callable[[StudioResult], None] | None = None,
    keys: Iterable[str] | None = None,
) -> RunReport:
    """Run all (or a subset of) studios. Local provider → serial; remote → parallel."""
    selected = list(keys) if keys is not None else [s.key for s in list_studios()]
    workers = 1 if ctx.llm.is_local else max(1, int(getattr(ctx, "parallelism", 4)))
    report = RunReport()
    lock = threading.Lock()

    def _wrap(k: str) -> StudioResult:
        if on_progress:
            on_progress(StudioResult(key=k, title=get_studio(k).title, status="running"))
        r = _execute_one(k, ctx)
        with lock:
            report.results[k] = r
        if on_progress:
            on_progress(r)
        return r

    if workers == 1:
        for k in selected:
            _wrap(k)
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(_wrap, k): k for k in selected}
            for _ in as_completed(futures):
                pass
    return report


def run_one(ctx: StudioContext, key: str) -> StudioResult:
    return _execute_one(key, ctx)
