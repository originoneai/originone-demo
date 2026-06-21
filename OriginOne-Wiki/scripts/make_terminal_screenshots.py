#!/usr/bin/env python3
"""Render terminal transcript text files to PNG screenshots."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]


def load_font(size: int = 18) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def text_width(font: ImageFont.FreeTypeFont | ImageFont.ImageFont, text: str) -> float:
    if hasattr(font, "getlength"):
        return float(font.getlength(text))
    return float(font.getbbox(text)[2])


def wrap_lines(
    lines: list[str],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        current = ""
        for char in line:
            candidate = current + char
            if current and text_width(font, candidate) > max_width:
                wrapped.append(current)
                current = "  " + char
            else:
                current = candidate
        wrapped.append(current)
    return wrapped


def render(transcript: Path, output: Path) -> None:
    text = transcript.read_text(encoding="utf-8").rstrip()
    raw_lines = text.splitlines() or [""]
    font = load_font()
    padding = 28
    line_h = 26
    raw_width = max(text_width(font, line) for line in raw_lines)
    width = int(min(1320, max(900, padding * 2 + raw_width)))
    lines = wrap_lines(raw_lines, font, width - padding * 2)
    height = padding * 2 + line_h * len(lines) + 36
    image = Image.new("RGB", (width, height), "#0f172a")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((12, 12, width - 12, height - 12), radius=14, fill="#111827", outline="#334155", width=1)
    draw.ellipse((30, 30, 42, 42), fill="#ef4444")
    draw.ellipse((50, 30, 62, 42), fill="#f59e0b")
    draw.ellipse((70, 30, 82, 42), fill="#22c55e")
    y = 64
    for line in lines:
        color = "#e5e7eb"
        if line.startswith("$"):
            color = "#93c5fd"
        elif line.startswith("+"):
            color = "#86efac"
        elif line.startswith("- ["):
            color = "#fde68a"
        draw.text((padding, y), line, font=font, fill=color)
        y += line_h
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("transcripts", nargs="*", type=Path)
    args = parser.parse_args()
    transcripts = args.transcripts or sorted((ROOT / "assets" / "screenshots").glob("*.txt"))
    for transcript in transcripts:
        output = transcript.with_suffix(".png")
        render(transcript, output)
        print(output)


if __name__ == "__main__":
    main()
