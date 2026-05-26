"""Subtitle file parser. Normalizes .srt/.vtt/.ass/.txt into plain text."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# SRT/VTT timestamp lines: "00:00:01,200 --> 00:00:04,000" or "00:00:01.200 --> 00:00:04.000"
_TS = re.compile(r"^\s*\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}.*$")
# SRT cue index lines (a bare integer on its own line)
_CUE_INDEX = re.compile(r"^\s*\d+\s*$")
# Inline tags: <i>, </i>, {\an8}, etc.
_HTML_TAG = re.compile(r"<[^>]+>")
_ASS_OVERRIDE = re.compile(r"\{[^}]*\}")


@dataclass
class SubtitleResult:
    text: str
    line_count: int
    char_count: int
    source_format: str


def parse(path: str | Path, raw_bytes: bytes | None = None) -> SubtitleResult:
    p = Path(path)
    ext = p.suffix.lower().lstrip(".")
    if raw_bytes is None:
        raw = p.read_bytes()
    else:
        raw = raw_bytes
    text = _decode(raw)
    if ext == "srt":
        cleaned = _from_srt(text)
    elif ext == "vtt":
        cleaned = _from_vtt(text)
    elif ext == "ass" or ext == "ssa":
        cleaned = _from_ass(text)
    else:
        cleaned = _from_plain(text)
    return SubtitleResult(
        text=cleaned,
        line_count=cleaned.count("\n") + 1 if cleaned else 0,
        char_count=len(cleaned),
        source_format=ext or "txt",
    )


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _from_srt(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if _CUE_INDEX.match(s):
            continue
        if _TS.match(s):
            continue
        s = _HTML_TAG.sub("", s)
        lines.append(s)
    return _dedup_join(lines)


def _from_vtt(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.upper().startswith("WEBVTT"):
            continue
        if s.startswith("NOTE") or s.startswith("STYLE") or s.startswith("REGION"):
            continue
        if _TS.match(s):
            continue
        if _CUE_INDEX.match(s):
            continue
        s = _HTML_TAG.sub("", s)
        lines.append(s)
    return _dedup_join(lines)


def _from_ass(text: str) -> str:
    lines: list[str] = []
    in_events = False
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.lower().startswith("[events]"):
            in_events = True
            continue
        if s.startswith("[") and s.endswith("]"):
            in_events = False
            continue
        if not in_events:
            continue
        if s.lower().startswith("format:"):
            continue
        if s.lower().startswith("dialogue:"):
            parts = s.split(",", 9)
            if len(parts) == 10:
                body = parts[9]
                body = _ASS_OVERRIDE.sub("", body).replace("\\N", "\n").replace("\\n", "\n")
                for piece in body.splitlines():
                    piece = piece.strip()
                    if piece:
                        lines.append(piece)
    return _dedup_join(lines)


def _from_plain(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return _dedup_join(lines, dedupe=False)


def _dedup_join(lines: list[str], dedupe: bool = True) -> str:
    out: list[str] = []
    prev = None
    for ln in lines:
        ln = re.sub(r"\s+", " ", ln).strip()
        if not ln:
            continue
        if dedupe and ln == prev:
            continue
        out.append(ln)
        prev = ln
    return "\n".join(out)
