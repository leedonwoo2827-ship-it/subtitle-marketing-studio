"""Image-generation rendering via Gemini Nano Banana.

For card-news studios (Threads/Instagram/Kakao) we route through the
Ubion LiteLLM proxy to `gemini-3.1-flash-image-preview` and produce one
fully-designed PNG per card, replacing the earlier Playwright capture
of HTML+CSS.

Per-card cost is roughly $0.04 (≈60원 @ 1,504.71원/USD); a full carousel
of 22 cards (5 card studios combined) is ~$0.88 ≈ 1,324원.

Korean text in the image: Nano Banana renders Korean reasonably well for
short headlines but can occasionally distort longer strings. Prompts
quote the exact text and ask the model to keep it crisp/legible.
"""
from __future__ import annotations

import base64
import io
from dataclasses import dataclass, field
from pathlib import Path

from core.html_render import _parse_cards
from core.user_settings import IMAGE_COST_USD, IMAGE_MODEL


_CHANNEL_SIZES: dict[str, tuple[int, int]] = {
    "image_threads_quick":   (1080, 1350),
    "image_threads_insight": (1080, 1350),
    "image_instagram_info":  (1080, 1350),
    "image_instagram_story": (1080, 1350),
    "image_kakao":           (800, 800),
}

_STYLE_HINTS: dict[str, str] = {
    "image_threads_quick": (
        "modern minimalist composition, deep blue-to-purple gradient background, "
        "large bold Korean typography, subtle geometric accent shapes, "
        "clean negative space, infographic-quality visual hierarchy"
    ),
    "image_threads_insight": (
        "data-driven infographic style, navy and indigo palette, "
        "small decorative chart/diagram element, structured layout, "
        "professional B2B-feel, statistics-friendly composition"
    ),
    "image_instagram_info": (
        "information-card aesthetic, warm yellow-amber gradient, "
        "small icon or chart decoration, vivid but readable, "
        "modern Korean magazine layout"
    ),
    "image_instagram_story": (
        "vintage photo-essay aesthetic, warm sepia and rose tones, "
        "soft illustrated decorative motifs, storytelling mood, "
        "film-grain texture impression"
    ),
    "image_kakao": (
        "friendly chat-card style, bright yellow gradient, "
        "single clear message focus, rounded shapes, "
        "approachable everyday-marketing tone"
    ),
}


@dataclass
class ImageRenderResult:
    paths: list[Path] = field(default_factory=list)
    cost_usd: float = 0.0
    n_requested: int = 0
    error: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.paths) and not self.error


def _visual_prompt(card: dict, *, channel: str, size: tuple[int, int], brand: str, idx: int, total: int) -> str:
    w, h = size
    main = (card.get("main") or "").strip()
    sub = (card.get("sub") or "").strip()
    role = (card.get("role") or "").strip()
    style = _STYLE_HINTS.get(channel, "modern marketing card design")

    extra = ""
    if card.get("body"):
        extra += f'\n- Body caption (small, multi-line): "{card["body"]}"'
    if card.get("hashtags"):
        extra += f'\n- Hashtags row (smallest, bottom): "{card["hashtags"]}"'
    if card.get("cta"):
        extra += f'\n- CTA pill text: "{card["cta"]}"'

    return f"""Design a {w}x{h} pixel marketing carousel card for Korean social media.

Card {idx} of {total} · role: {role}
Visual style: {style}

EXACT Korean text to render in the image (must be crisp and legible, modern sans-serif like Pretendard):
- Main headline (largest, bold): "{main}"
- Supporting line (medium): "{sub}"{extra}
- Footer brand line (small): "{brand or 'Subtitle Marketing Studio'}"
- Tiny size tag (corner): "{w} × {h}"

Layout requirements:
- Single full-bleed background (gradient or pattern matching the style)
- Top-left: a small circular badge or icon symbolising the role ({role})
- Centre: the main headline with strong visual hierarchy, supporting line beneath
- Footer: thin horizontal divider, then brand line on the left and size tag on the right

No logos beyond the text. No watermarks. No frames around the card. Korean text must be exact — do not paraphrase, translate, or omit characters. Image should look like a professionally designed infographic card, not a stock photo."""


def _generate_one(prompt: str, *, base_url: str, api_key: str) -> tuple[bytes | None, str]:
    """Call Nano Banana via the Ubion LiteLLM proxy. Returns (png_bytes, error)."""
    try:
        from openai import OpenAI
    except ImportError as e:
        return None, f"missing dep: {e}"

    try:
        url = (base_url or "").rstrip("/")
        client = OpenAI(api_key=api_key, base_url=f"{url}/v1")
        resp = client.chat.completions.create(
            model=IMAGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            modalities=["image", "text"],
        )
        msg = resp.choices[0].message
        images = getattr(msg, "images", None)
        if not images:
            return None, "model returned no images"
        data_url = images[0].image_url.url
        b64 = data_url.split(",", 1)[1] if "," in data_url else data_url
        raw = base64.b64decode(b64)
        return raw, ""
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _ensure_size(raw: bytes, size: tuple[int, int]) -> bytes:
    """Resize PNG bytes to exact target dimensions via Pillow if needed."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(raw))
        if img.size == size:
            return raw
        img = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img
        resized = img.resize(size, Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception:
        return raw


def render(
    channel_key: str, md_text: str, out_dir: Path, *,
    base_url: str, api_key: str, brand: str = "",
) -> ImageRenderResult:
    if channel_key not in _CHANNEL_SIZES:
        return ImageRenderResult(error=f"unknown image channel: {channel_key}")
    if not api_key:
        return ImageRenderResult(error="API key not configured")
    size = _CHANNEL_SIZES[channel_key]

    cards = _parse_cards(md_text)
    if not cards:
        return ImageRenderResult(error="no cards parsed from markdown")

    cards_dir = out_dir / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    result = ImageRenderResult(n_requested=len(cards))
    last_error = ""

    for i, card in enumerate(cards, start=1):
        prompt = _visual_prompt(card, channel=channel_key, size=size, brand=brand, idx=i, total=len(cards))
        raw, err = _generate_one(prompt, base_url=base_url, api_key=api_key)
        if raw is None:
            last_error = err
            continue
        raw = _ensure_size(raw, size)
        out_path = cards_dir / f"card_{i}.png"
        out_path.write_bytes(raw)
        result.paths.append(out_path)
        result.cost_usd += IMAGE_COST_USD

    if not result.paths and last_error:
        result.error = last_error
    return result


def estimated_cost_usd(channel_key: str, md_text: str | None = None) -> float:
    """Estimate cost in USD given the channel and (optionally) actual parsed card count."""
    if md_text:
        n = len(_parse_cards(md_text))
    else:
        n = {
            "image_threads_quick": 3,
            "image_threads_insight": 5,
            "image_instagram_info": 5,
            "image_instagram_story": 7,
            "image_kakao": 2,
        }.get(channel_key, 0)
    return n * IMAGE_COST_USD
