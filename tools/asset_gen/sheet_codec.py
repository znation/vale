#!/usr/bin/env python3
"""
sheet_codec.py — Read, render and write VALE sprite sheets with the engine's real pixel semantics.

The engine (FeLib/Source/rawbit.cpp) loads an 8-bit indexed PNG and *reverses* it:
engine index e = 255 - file index f, and palette entry e = PNG palette entry 255 - e.
Then, per pixel:

  * e >= 192 (file index 0..63): a material-colour pixel. Channel c = (e - 192) >> 4
    selects one of four colours the game supplies at draw time (main material,
    secondary material, skin, cloth, ... depending on the object), and the low
    nibble e & 15 is its brightness: colour * (e & 15) / 8, clamped.
  * otherwise a fixed palette colour, drawn as-is; magenta (255, 0, 255) is transparent.

Tools that requantize a sheet without honouring this (e.g. putting arbitrary colours
in file indices 0..63, or reordering the palette) break every sprite on the sheet.
The helpers here keep the original palette untouched and only emit valid indices.
"""

from dataclasses import dataclass

import numpy as np
from PIL import Image

MATERIAL_ZONE = 64  # file indices below this are material pixels
TRANSPARENT_RGB = (255, 0, 255)

# Representative colours for previews: steel, fir wood, leather, pale skin.
# (Values from Script/material.dat; channel meaning varies per object.)
PREVIEW_MATERIALS = np.array([(128, 128, 128), (140, 96, 48), (111, 64, 37), (180, 140, 110)], dtype=float)

TRANSPARENT, MATERIAL, FIXED = 0, 1, 2


def material_file_index(channel, intensity):
    """File index for a material pixel of `channel` (0-3) at brightness `intensity` (0-15)."""
    return 255 - (192 + 16 * channel + intensity)


@dataclass
class Sheet:
    path: str
    pixels: np.ndarray  # (H, W) uint8 file indices
    palette: np.ndarray  # (256, 3) PNG palette, file order

    @classmethod
    def load(cls, path):
        im = Image.open(path)
        if im.mode != "P":
            raise ValueError(f"{path} is {im.mode}; the engine needs 8-bit indexed PNGs")
        pal = np.array((im.getpalette() + [0] * 768)[:768]).reshape(256, 3)
        return cls(str(path), np.array(im), pal)

    def save(self, path=None):
        im = Image.fromarray(self.pixels, mode="P")
        im.putpalette(self.palette.astype(np.uint8).ravel().tolist())
        im.save(path or self.path)

    @property
    def transparent_index(self):
        # Several sheets have more than one magenta entry; the fixed zone's first one is the canonical choice.
        hits = [i for i in range(MATERIAL_ZONE, 256) if tuple(self.palette[i]) == TRANSPARENT_RGB]
        return hits[0]

    def fixed_indices(self):
        """File indices usable for fixed colours: the non-material zone minus transparent entries."""
        return np.array([i for i in range(MATERIAL_ZONE, 256) if tuple(self.palette[i]) != TRANSPARENT_RGB])

    def decode(self, region=None):
        """Return (kind, channel, intensity, fixed_rgb) arrays for a region (x, y, w, h)."""
        f = self.pixels if region is None else crop(self.pixels, region)
        f = f.astype(int)
        kind = np.full(f.shape, FIXED)
        kind[f < MATERIAL_ZONE] = MATERIAL
        rgb = self.palette[f]
        kind[(f >= MATERIAL_ZONE) & np.all(rgb == TRANSPARENT_RGB, axis=-1)] = TRANSPARENT
        e = 255 - f
        channel = np.where(kind == MATERIAL, (e - 192) >> 4, -1)
        intensity = np.where(kind == MATERIAL, e & 15, 0)
        return kind, channel, intensity, rgb

    def render(self, region=None, materials=PREVIEW_MATERIALS):
        """RGBA uint8 image of a region as the engine would draw it with the given material colours."""
        kind, channel, intensity, rgb = self.decode(region)
        out = np.zeros(kind.shape + (4,), dtype=np.uint8)
        fixed = kind == FIXED
        out[fixed, :3] = rgb[fixed]
        mat = kind == MATERIAL
        out[mat, :3] = np.clip(materials[channel[mat]] * intensity[mat, None] / 8, 0, 255)
        out[kind != TRANSPARENT, 3] = 255
        return out


def crop(a, region):
    x, y, w, h = region
    return a[y : y + h, x : x + w]


def preview(sheet, region=None, scale=1, background=(20, 20, 28)):
    """Engine-faithful RGB preview of a sheet (a Sheet or a path) or region, upscaled with nearest neighbour."""
    if not isinstance(sheet, Sheet):
        sheet = Sheet.load(sheet)
    rgba = sheet.render(region)
    img = Image.new("RGB", (rgba.shape[1], rgba.shape[0]), background)
    img.paste(Image.fromarray(rgba, "RGBA"), mask=Image.fromarray(rgba[..., 3]))
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def scale2x(pixels):
    """
    EPX / Scale2x on a 2D index array: each pixel becomes 2x2, copying an edge neighbour into a
    corner where two neighbours agree, which rounds off diagonals while keeping hard pixel-art
    edges. It only compares indices for equality, so material channels and transparency survive.
    """
    p = np.pad(pixels, 1, mode="edge")
    P = p[1:-1, 1:-1]
    A, B, C, D = p[:-2, 1:-1], p[1:-1, 2:], p[1:-1, :-2], p[2:, 1:-1]  # up, right, left, down
    out = np.empty((pixels.shape[0] * 2, pixels.shape[1] * 2), dtype=pixels.dtype)
    out[0::2, 0::2] = np.where((C == A) & (C != D) & (A != B), A, P)
    out[0::2, 1::2] = np.where((A == B) & (A != C) & (B != D), B, P)
    out[1::2, 0::2] = np.where((D == C) & (D != B) & (C != A), C, P)
    out[1::2, 1::2] = np.where((B == D) & (B != A) & (D != C), D, P)
    return out


def upscale_sheet(sheet, factor):
    """The sheet at `factor` (2 or 4) times the pixel density, via repeated Scale2x."""
    pixels = sheet.pixels
    while factor > 1:
        pixels = scale2x(pixels)
        factor //= 2
    return Sheet(sheet.path, pixels, sheet.palette)
