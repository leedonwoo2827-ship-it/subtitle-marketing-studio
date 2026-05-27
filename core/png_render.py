"""PNG rendering via Playwright headless Chromium.

Each `.studio-card` div in the HTML output is captured individually at its
natural rendered size (1080×1350 for cards, 800×800 for KakaoTalk). The
resulting PNGs go to `<project>/<studio_dir>/cards/card_<N>.png` so they
can be uploaded directly to Instagram/Threads/KakaoTalk channels.

First-time setup: `playwright install chromium` (auto-suggested by
setup.bat). If Chromium is missing at runtime, an informative error is
written so the user can recover.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


# Channel-specific defaults
_CHANNEL_SIZES: dict[str, tuple[int, int]] = {
    "cards_threads_quick":     (1080, 1350),
    "cards_threads_insight":   (1080, 1350),
    "cards_instagram_info":    (1080, 1350),
    "cards_instagram_story":   (1080, 1350),
    "cards_kakao":             (800, 800),
}


@dataclass
class PNGRenderResult:
    paths: list[Path]
    error: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.paths) and not self.error


def render(channel_key: str, html_text: str, out_dir: Path) -> PNGRenderResult:
    """Capture each .studio-card div as a PNG. Returns paths in card order.

    out_dir is the studio's folder (e.g. `data/projects/<proj>/01_threads_quick/`).
    PNGs land in `out_dir / cards / card_<N>.png`.
    """
    if channel_key not in _CHANNEL_SIZES:
        return PNGRenderResult(paths=[], error=f"unknown channel: {channel_key}")
    width, height = _CHANNEL_SIZES[channel_key]
    cards_dir = out_dir / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return PNGRenderResult(
            paths=[],
            error="playwright not installed. Run: pip install playwright",
        )

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                msg = str(e)
                if "Executable doesn't exist" in msg or "playwright install" in msg.lower():
                    return PNGRenderResult(
                        paths=[],
                        error="Chromium not installed. Run: python -m playwright install chromium",
                    )
                raise
            try:
                context = browser.new_context(
                    viewport={"width": width + 80, "height": max(height + 80, 900)},
                    device_scale_factor=1,
                )
                page = context.new_page()
                # `networkidle` lets Google Fonts CSS+woff2 finish downloading.
                page.set_content(html_text, wait_until="networkidle")
                # Also explicitly wait for the FontFace set to be loaded
                # (handles the case where fonts are still rendering after
                # CSS finished downloading).
                try:
                    page.evaluate("document.fonts && document.fonts.ready")
                    page.wait_for_function("document.fonts.status === 'loaded'", timeout=8000)
                except Exception:
                    pass  # If browser blocks the API, fall through — fallback fonts will be used
                cards = page.query_selector_all(".studio-card")
                if not cards:
                    return PNGRenderResult(paths=[], error="no .studio-card found")
                paths: list[Path] = []
                for i, card in enumerate(cards, start=1):
                    out = cards_dir / f"card_{i}.png"
                    card.screenshot(path=str(out), type="png", omit_background=False)
                    paths.append(out)
                return PNGRenderResult(paths=paths)
            finally:
                browser.close()
    except Exception as e:
        return PNGRenderResult(paths=[], error=f"{type(e).__name__}: {e}")
