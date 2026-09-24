#!/usr/bin/env python3
"""
hd_sprites.py — Build the 64-pixel-per-tile (4x) sprite sheets the engine uses on HiDPI displays.

The engine draws each 16-unit tile with 16 * density pixels and loads Graphics/4x/<Sheet>.png
when it exists; lower densities (32-pixel tiles) are derived from it on load, material-aware
(see rawbitmap::Rescale). This tool produces those 4x sheets:

  generate  Redraw sprites with Qwen-Image-2.1 (512x512 per 16x16 sprite, 20 steps, fp16: about
            two minutes each on the Vega 48). Each sprite, as the engine draws it, is the condition
            image for a prompt naming what it is (from sprite_catalog.py). Animation frames and
            variants are drawn after the sprite they belong to, with its finished redraw as a second
            condition image so the frames match. One RGBA master per sprite is kept under
            tools/asset_gen/masters/hd/<Sheet>/, so runs are resumable and never redo a sprite.
  assemble  Start from the classic sheet upscaled 4x with Scale2x (see hd_upscale.py), so sprites
            without a redraw still look right, then paste in each master: collapsed onto the 64-pixel grid
            (body parts also confined near their original silhouette so they still line up)
            and re-encoded into the sheet's palette with material pixels kept on their channels.
            Writes Graphics/4x/<Sheet>.png and, where the game has one, the -outlined variant.

Usage:
    ~/venv-qwenimage/bin/python tools/asset_gen/hd_sprites.py generate --sheet Item          # whole sheet
    ~/venv-qwenimage/bin/python tools/asset_gen/hd_sprites.py generate --sheet Item --once   # one chunk
    ~/venv-qwenimage/bin/python tools/asset_gen/hd_sprites.py assemble --sheet Item
    ~/venv-qwenimage/bin/python tools/asset_gen/hd_sprites.py list --sheet Char
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))

from sheet_codec import TRANSPARENT, Sheet, upscale_sheet  # noqa: E402
from sprite_forge import downsample, encode, upscale_reference  # noqa: E402

REPO = Path(__file__).parent.parent.parent
GRAPHICS = REPO / "Graphics"
HD = GRAPHICS / "4x"
MASTERS = Path(__file__).parent / "masters" / "hd"
CATALOG = Path(__file__).parent / "sprite_catalog.json"

SCALE = 4  # physical pixels per layout pixel in Graphics/4x
GEN_PX = 512  # generation size for a 16x16 sprite (8 image pixels per 64-grid pixel)
SHEETS = ["GLTerra", "OLTerra", "Item", "Char", "Humanoid", "WTerra"]
OUTLINED = {"Item", "Char", "Humanoid"}
OUTLINE_INDEX = 68  # the black the -outlined sheets use (file index)

# How far (in 4x pixels) a redraw may move the original silhouette's edge. Body parts and worn
# gear are composited at fixed offsets, so they must stay put; creatures, items and terrain may
# be redrawn freely within their own tile.
SILHOUETTE_SLACK = {"Humanoid": 2}

# What an unnamed sprite is called in its prompt; the model identifies it from the image.
UNNAMED = {
    "GLTerra": "a ground texture",
    "OLTerra": "a terrain feature",
    "WTerra": "a world map feature",
    "Item": "a fantasy item",
    "Char": "a fantasy creature",
    "Humanoid": "a body part or piece of worn equipment",
}

KIND = {
    "GLTerra": "a ground terrain tile, seen from above",
    "OLTerra": "a terrain feature tile (wall, door, furniture or plant) for a top-down map",
    "WTerra": "a world map terrain tile, seen from above",
    "Item": "an item icon",
    "Char": "a creature",
    "Humanoid": "a body part or piece of worn equipment for a paper-doll character sprite",
}

# A plain "redraw this sprite" keeps the model on the 16x16 grid; calling the reference a crude
# placeholder frees it to add real detail. Body parts must keep their exact outline instead.
PROMPT = (
    "The reference image is a crude, low-resolution {w}x{h} placeholder sprite of {what} ({kind}). Draw a "
    "brand-new, high-quality {W}x{H} pixel art sprite of {what} for a dark fantasy roguelike game, replacing "
    "it: the same pose, size, facing direction, position in the frame and main colours, but drawn with far "
    "more detail, smooth natural contours instead of blocky steps, crisp clean pixels, a dark outline and "
    "shading lit from the top left. Empty areas stay empty."
)
FIXED_OUTLINE_PROMPT = (
    "Redraw this tiny {w}x{h} pixel art game sprite of {what} ({kind}) as a detailed {W}x{H} pixel art sprite "
    "for a dark fantasy roguelike: four times the resolution with much more detail, crisp clean pixels, rich "
    "shading lit from the top left. Keep exactly the same outline, pose, colour regions and position in the "
    "frame, and leave the empty areas empty."
)
FRAME_PROMPT = (
    "Image 1 is a crude, low-resolution {w}x{h} placeholder sprite; image 2 is the finished high-quality "
    "{W}x{H} pixel art version of the same subject, {what}. Draw image 1 as a finished {W}x{H} pixel art "
    "sprite in exactly the style, colours, level of detail and design of image 2, with image 1's pose, "
    "outline and position in the frame. Empty areas stay empty."
)


@dataclass
class Sprite:
    sheet: str
    x: int
    y: int
    w: int
    h: int
    what: str
    base: "Sprite" = None  # the sprite this one is an animation frame or variant of

    @property
    def rect(self):
        return (self.x, self.y, self.w, self.h)

    @property
    def master(self):
        return MASTERS / self.sheet / f"{self.x}_{self.y}_{self.w}x{self.h}.png"


def sprites(sheet_name):
    """Every non-empty sprite on a sheet: catalogued rectangles first, then leftover 16x16 tiles
    named after the nearest catalogued sprite to their left (usually animation frames)."""
    catalog = json.loads(CATALOG.read_text()) if CATALOG.exists() else {}
    sheet = Sheet.load(GRAPHICS / f"{sheet_name}.png")
    kind = sheet.decode()[0]
    H, W = kind.shape
    covered = np.zeros((H // 16, W // 16), bool)
    found, named = [], {}

    for key, entry in catalog.items():
        name, rect = key.split(":")
        if name != sheet_name:
            continue
        x, y, w, h = map(int, rect.split(","))
        if x + w > W or y + h > H or not (kind[y : y + h, x : x + w] != TRANSPARENT).any():
            continue
        sprite = Sprite(sheet_name, x, y, w, h, " / ".join(entry["names"][:3]))
        found.append(sprite)
        covered[y // 16 : (y + h) // 16, x // 16 : (x + w) // 16] = True
        if w == 16 and h == 16:
            named[(x // 16, y // 16)] = sprite

    for ty in range(H // 16):
        for tx in range(W // 16):
            if covered[ty, tx] or not (kind[ty * 16 : ty * 16 + 16, tx * 16 : tx * 16 + 16] != TRANSPARENT).any():
                continue
            left = next((named[(lx, ty)] for lx in range(tx - 1, max(tx - 5, -1), -1) if (lx, ty) in named), None)
            what = left.what if left else UNNAMED[sheet_name]
            found.append(Sprite(sheet_name, tx * 16, ty * 16, 16, 16, what, base=left))
    return sorted(found, key=lambda s: (s.y, s.x))


def generate(sheet_name, limit, steps, seed):
    from qwen_image import Job, run_jobs

    sheet = Sheet.load(GRAPHICS / f"{sheet_name}.png")
    missing = [s for s in sprites(sheet_name) if not s.master.exists()]
    # Frames wait for their base sprite's master, which becomes their style reference; every
    # prompt (condition images included) is encoded before any image is drawn, so they can
    # only go in a later run.
    ready = [s for s in missing if s.base is None or s.base.master.exists()]
    # Named sprites first: they are the ones the game is known to use.
    ready.sort(key=lambda s: (s.base is not None, s.what == UNNAMED[sheet_name], s.y, s.x))
    todo = ready[:limit]
    waiting = len(missing) - len(ready)
    if not todo:
        print(f"{sheet_name}: nothing to generate ({waiting} frames wait for their base sprite)")
        return False
    jobs = []
    for s in todo:
        size = (GEN_PX * s.w // 16, GEN_PX * s.h // 16)
        refs = [upscale_reference(sheet, s.rect, size)]
        fmt = dict(w=s.w, h=s.h, W=s.w * SCALE, H=s.h * SCALE, what=s.what, kind=KIND[sheet_name])
        if s.base is not None:
            refs.append(Image.open(s.base.master))
            prompt = FRAME_PROMPT.format(**fmt)
        elif sheet_name in SILHOUETTE_SLACK:
            prompt = FIXED_OUTLINE_PROMPT.format(**fmt)
        else:
            prompt = PROMPT.format(**fmt)
        s.master.parent.mkdir(parents=True, exist_ok=True)
        jobs.append(Job(prompt, s.master, size[0], size[1], seed, refs))
    print(f"{sheet_name}: generating {len(jobs)} of {len(missing)} missing masters ({waiting} frames wait)", flush=True)
    run_jobs(jobs, steps=steps, precision="fp16")
    return True




def confine(small, original_opaque, slack):
    """Keep the redraw's alpha within `slack` pixels of the original silhouette, and fill the
    original's interior so body parts keep overlapping where the engine expects."""
    alpha = small[..., 3] >= 128
    grown = ndimage.binary_dilation(original_opaque, iterations=slack)
    core = ndimage.binary_erosion(original_opaque, iterations=slack)
    small = small.copy()
    small[..., 3] = np.where((alpha & grown) | core, 255, 0)
    return small


def assemble(sheet_name):
    original = Sheet.load(GRAPHICS / f"{sheet_name}.png")
    base = upscale_sheet(original, SCALE)
    result = Sheet(str(HD / f"{sheet_name}.png"), base.pixels.copy(), base.palette)
    slack = SILHOUETTE_SLACK.get(sheet_name)
    done = 0
    for s in sprites(sheet_name):
        if not s.master.exists():
            continue
        rect = tuple(v * SCALE for v in s.rect)
        x, y, w, h = rect
        small = downsample(Image.open(s.master), w, h)
        if slack is not None:
            small = confine(small, base.decode(rect)[0] != TRANSPARENT, slack)
        result.pixels[y : y + h, x : x + w] = encode(base, rect, small)
        done += 1
    HD.mkdir(parents=True, exist_ok=True)
    result.save()
    print(f"wrote {Path(result.path).relative_to(REPO)} ({done} redrawn sprites)")
    if sheet_name in OUTLINED:
        outlined = Sheet(str(HD / f"{sheet_name}-outlined.png"), result.pixels.copy(), result.palette)
        kind = outlined.decode()[0]
        ring = ndimage.binary_dilation(kind != TRANSPARENT, structure=np.ones((3, 3)), iterations=SCALE)
        outlined.pixels[ring & (kind == TRANSPARENT)] = OUTLINE_INDEX
        outlined.save()
        print(f"wrote {Path(outlined.path).relative_to(REPO)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["generate", "assemble", "list"])
    parser.add_argument("--sheet", required=True, choices=SHEETS)
    parser.add_argument("--chunk", type=int, default=40, help="Sprites per model load (generate)")
    parser.add_argument("--once", action="store_true", help="Generate a single chunk instead of the whole sheet")
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--seed", type=int, default=3)
    args = parser.parse_args()
    if args.command == "generate":
        # Chunks keep the up-front prompt encoding short, and let animation frames join once the
        # sprite they follow has been drawn in an earlier chunk.
        while generate(args.sheet, args.chunk, args.steps, args.seed) and not args.once:
            pass
    elif args.command == "assemble":
        assemble(args.sheet)
    else:
        all_sprites = sprites(args.sheet)
        have = sum(s.master.exists() for s in all_sprites)
        for s in all_sprites:
            print(f"{'x' if s.master.exists() else ' '} {s.x:4d},{s.y:4d} {s.w}x{s.h}  {s.what}")
        print(f"{args.sheet}: {len(all_sprites)} sprites, {have} with masters")


if __name__ == "__main__":
    main()
