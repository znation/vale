#!/usr/bin/env python3
"""
sprite_forge.py — Turn a high-resolution AI redraw back into a valid VALE sprite.

A redraw comes back as a large RGBA image (e.g. 512x512 for a 16x16 sprite). This module

  1. downsamples it to the sprite's pixel grid, detecting the grid phase the model
     actually drew on and taking a robust per-cell colour, and
  2. re-encodes every pixel into the engine's scheme (see sheet_codec.py): pixels that were
     material-coloured in the original stay material-coloured, on the same channel, with a
     brightness fitted to the new shading — so iron and mithril swords still look different
     in game — and every other pixel is snapped to the sheet's existing fixed palette.

The sheet palette is never modified, so sprites that are not redrawn are untouched.
"""

import numpy as np
from PIL import Image
from scipy import ndimage

from sheet_codec import FIXED, MATERIAL, PREVIEW_MATERIALS, TRANSPARENT, material_file_index

# How strongly a pixel prefers the class (material channel / fixed colour) the original sprite had nearby.
# Colour distances are RGB Euclidean (0-441); this is the cost per pixel of distance to that class.
SPATIAL_WEIGHT = 24.0
OPAQUE_ALPHA = 128


def downsample(img, width, height):
    """Collapse a pixel-art-style RGBA render to width x height, finding the grid phase it was drawn on."""
    a = np.asarray(img.convert("RGBA"), dtype=float)
    cell_x, cell_y = a.shape[1] / width, a.shape[0] / height
    best = None
    for phase_y in np.linspace(-cell_y / 2, cell_y / 2, 9)[:-1]:
        for phase_x in np.linspace(-cell_x / 2, cell_x / 2, 9)[:-1]:
            cells = _cells(a, width, height, phase_x, phase_y)
            score = sum(_cell_spread(c) for c in cells)
            if best is None or score < best[0]:
                best = (score, cells)
    out = np.zeros((height, width, 4), dtype=np.uint8)
    for i, c in enumerate(best[1]):
        y, x = divmod(i, width)
        opaque = c[..., 3] >= OPAQUE_ALPHA
        if opaque.mean() < 0.5:
            continue
        core = _core(c)
        core_opaque = core[core[..., 3] >= OPAQUE_ALPHA]
        px = core_opaque if len(core_opaque) else c[opaque]
        out[y, x, :3] = np.median(px[:, :3], axis=0)
        out[y, x, 3] = 255
    return out


def _cells(a, width, height, phase_x, phase_y):
    h, w = a.shape[:2]
    cx, cy = w / width, h / height
    cells = []
    for y in range(height):
        for x in range(width):
            x0 = int(round(x * cx + phase_x))
            y0 = int(round(y * cy + phase_y))
            x1, y1 = int(round(x0 + cx)), int(round(y0 + cy))
            c = a[max(y0, 0) : max(min(y1, h), 0), max(x0, 0) : max(min(x1, w), 0)]
            cells.append(c if c.size else np.zeros((1, 1, 4)))
    return cells


def _core(c):
    h, w = c.shape[:2]
    return c[h // 4 : h - h // 4 or h, w // 4 : w - w // 4 or w]


def _cell_spread(c):
    flat = c.reshape(-1, 4)
    return float(flat[:, :3].std(axis=0).sum() * (flat[:, 3] >= OPAQUE_ALPHA).mean() + flat[:, 3].std() * 0.5)


def encode(sheet, region, small, keep_silhouette=False, materials=PREVIEW_MATERIALS):
    """
    Map a downsampled RGBA sprite (h, w, 4) into file indices for `region` of `sheet`.

    keep_silhouette: use the original sprite's exact opaque mask (needed for humanoid body
    parts, which the engine composites at fixed offsets).
    """
    kind, channel, _, rgb = sheet.decode(region)
    h, w = kind.shape
    opaque = kind != TRANSPARENT if keep_silhouette else small[..., 3] >= OPAQUE_ALPHA
    colour = small[..., :3].astype(float)
    if keep_silhouette:
        # Where the redraw left a hole inside the original silhouette, borrow the nearest redrawn colour.
        have = small[..., 3] >= OPAQUE_ALPHA
        if have.any():
            _, (iy, ix) = ndimage.distance_transform_edt(~have, return_indices=True)
            colour = colour[iy, ix]

    fixed_idx = sheet.fixed_indices()
    fixed_rgb = sheet.palette[fixed_idx].astype(float)

    # Candidate classes: each material channel the original used, plus "fixed colour".
    classes = [("mat", c) for c in sorted(set(channel[kind == MATERIAL].tolist()))] + [("fixed", None)]
    costs, results = [], []
    for cls, ch in classes:
        present = (channel == ch) if cls == "mat" else (kind == FIXED)
        spatial = ndimage.distance_transform_edt(~present) if present.any() else np.full((h, w), 8.0)
        if cls == "mat":
            base = materials[ch]
            # Brightness t/8 of the material colour that best reproduces the redrawn pixel.
            t = np.clip(np.rint(8 * (colour @ base) / (base @ base)), 1, 15)
            err = np.linalg.norm(colour - t[..., None] * base / 8, axis=-1)
            results.append(material_file_index(ch, t.astype(int)))
        else:
            d = np.linalg.norm(colour[..., None, :] - fixed_rgb[None, None], axis=-1)
            nearest = d.argmin(axis=-1)
            err = d.min(axis=-1)
            results.append(fixed_idx[nearest])
        costs.append(err + SPATIAL_WEIGHT * spatial)

    choice = np.argmin(np.stack(costs), axis=0)
    out = np.choose(choice, results).astype(np.uint8)
    out[~opaque] = sheet.transparent_index
    return out


def silhouette_iou(sheet, region, small):
    kind = sheet.decode(region)[0]
    a = kind != TRANSPARENT
    b = small[..., 3] >= OPAQUE_ALPHA
    union = (a | b).sum()
    return float((a & b).sum() / union) if union else 1.0


def upscale_reference(sheet, region, size, materials=PREVIEW_MATERIALS):
    """The original sprite, rendered as the engine would and blown up (nearest) to `size`, as RGBA."""
    rgba = sheet.render(region, materials)
    return Image.fromarray(rgba, "RGBA").resize(size, Image.NEAREST)
