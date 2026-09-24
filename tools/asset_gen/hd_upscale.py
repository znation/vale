#!/usr/bin/env python3
"""
hd_upscale.py — High-density versions of the paletted graphics that are not AI-redrawn.

Fonts, UI symbols, effects, cursors, fog of war and the death-screen smiley are upscaled with
Scale2x (EPX, see sheet_codec.scale2x): the same pixel art, with diagonals and curves rounded
instead of every pixel turned into a block. It works on palette indices, so material-coloured
pixels and transparency are untouched. The sprite sheets that get AI redraws are built by
hd_sprites.py on the same Scale2x base.

Writes Graphics/4x/<name>.png for each (the engine derives 32-pixel tiles from those on load)
and, for the fonts, Graphics/2x/ as well, since a Scale2x pass reads better than a 4x font
scaled back down.

Usage:
    python tools/asset_gen/hd_upscale.py
"""

from pathlib import Path

from sheet_codec import Sheet, upscale_sheet

REPO = Path(__file__).parent.parent.parent
GRAPHICS = REPO / "Graphics"

UPSCALED = ["Font", "Font2", "Font3", "Symbol", "Effect", "Cursor", "FOW", "Smiley"]
WITH_2X = {"Font", "Font2", "Font3"}


def main():
    for name in UPSCALED:
        sheet = Sheet.load(GRAPHICS / f"{name}.png")
        for factor in (2, 4) if name in WITH_2X else (4,):
            out = GRAPHICS / f"{factor}x" / f"{name}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            upscale_sheet(sheet, factor).save(out)
            print(f"wrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
