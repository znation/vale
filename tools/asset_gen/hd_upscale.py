#!/usr/bin/env python3
"""
hd_upscale.py — High-density versions of the paletted graphics that are not AI-redrawn.

Fonts, UI symbols, effects, cursors and the death-screen smiley are upscaled with
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

import numpy as np

from sheet_codec import Sheet, upscale_sheet

REPO = Path(__file__).parent.parent.parent
GRAPHICS = REPO / "Graphics"

UPSCALED = ["Font", "Font2", "Font3", "Symbol", "Effect", "Cursor", "Smiley"]
WITH_2X = {"Font", "Font2", "Font3"}


def fine_dither(sheet, factor):
    """
    FOW.png darkens remembered-but-unseen squares by overwriting every other pixel (black is the
    mask colour) with a checkerboard. Scaled up, that checkerboard turns into coarse blocks; keep
    it one physical pixel fine instead, so it still reads as an even tint. A 2x version must exist
    too: averaging the pattern down would produce a solid colour the mask no longer hides.
    """
    pixels = sheet.pixels
    h, w = pixels.shape[0] * factor, pixels.shape[1] * factor
    y, x = np.mgrid[0:h, 0:w]
    return Sheet(sheet.path, np.where((x + y) % 2 == 0, pixels[0, 0], pixels[0, 1]).astype(pixels.dtype), sheet.palette)


def main():
    for name in UPSCALED:
        sheet = Sheet.load(GRAPHICS / f"{name}.png")
        for factor in (2, 4) if name in WITH_2X else (4,):
            out = GRAPHICS / f"{factor}x" / f"{name}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            upscale_sheet(sheet, factor).save(out)
            print(f"wrote {out.relative_to(REPO)}")

    fow = Sheet.load(GRAPHICS / "FOW.png")
    for factor in (2, 4):
        out = GRAPHICS / f"{factor}x" / "FOW.png"
        fine_dither(fow, factor).save(out)
        print(f"wrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
