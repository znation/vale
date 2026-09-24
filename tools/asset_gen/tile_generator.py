#!/usr/bin/env python3
"""
tile_generator.py — Redraw individual sprites in a VALE sprite sheet with Qwen-Image-2.1.

Each sprite is rendered as the engine draws it, blown up to the generation size and given to
Qwen-Image-2.1 as a condition image with a redraw prompt, so the result keeps the original's
pose and silhouette on the same pixel grid. The RGBA result is collapsed back to the sprite's
grid and re-encoded with sprite_forge.encode(): material-coloured pixels stay on their
material channel, everything else snaps to the sheet's existing palette, and the palette is
never changed. Nothing outside the redrawn sprites is touched.

(An earlier version of this tool requantized whole sheets with a new palette and ignored the
engine's reversed index order — see sheet_codec.py — which recoloured every sprite on the
sheet. Its output was reverted.)

Humanoid body parts are composited by the engine at fixed offsets, so on the Humanoid sheet
the original silhouette is kept exactly and only the shading is taken from the redraw.

Findings (2026-09-23): on 16x16 sprites Qwen-Image-2.1 redraws are faithful but add little
beyond an outline and darker shading, which reads worse on dark floors, so the shipped sheets
remain the original art. The tool is most useful for re-theming a sprite (pass --describe with
a new subject) or for larger sprites.

Usage:
    ~/venv-qwenimage/bin/python tools/asset_gen/tile_generator.py --sheet Char --tile 14,0 \\
        --describe "a black cat with yellow eyes" --preview /tmp/cat.png
    ~/venv-qwenimage/bin/python tools/asset_gen/tile_generator.py --sheet Item --rect 0,112,16,16 \\
        --describe "a ripe mango" --write
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from sheet_codec import Sheet, preview  # noqa: E402
from sprite_forge import downsample, encode, silhouette_iou, upscale_reference  # noqa: E402

REPO = Path(__file__).parent.parent.parent
GRAPHICS_DIR = REPO / "Graphics"
REGISTRY_DIR = Path(__file__).parent / "tile_registries"
WORK_DIR = Path(__file__).parent / "masters" / "tiles"

SHEETS = ["GLTerra", "OLTerra", "WTerra", "Item", "Char", "Humanoid", "Symbol", "Effect", "Smiley"]
OUTLINED_SHEETS = {"Char", "Humanoid", "Item"}
KEEP_SILHOUETTE_SHEETS = {"Humanoid"}

GEN_SIZE = 512
MIN_IOU = 0.6  # reject redraws whose silhouette drifted this far from the original

REDRAW = (
    "Redraw this {w}x{h} pixel art sprite of {what} for a dark fantasy roguelike game as a higher quality "
    "version on the same {w}x{h} pixel grid: same pose, same silhouette, same size and facing direction. "
    "Crisp hand-placed pixels, a clean dark outline, readable shading lit from the top left."
)


def registry_name(sheet, x, y):
    path = REGISTRY_DIR / f"{sheet.lower()}_tiles.json"
    if not path.exists():
        return None
    entry = json.loads(path.read_text()).get(f"{x // 16},{y // 16}")
    return entry and entry.get("name")


def parse_targets(args):
    targets = []
    for tile in args.tile or []:
        col, row = map(int, tile.split(","))
        targets.append((col * 16, row * 16, 16, 16))
    for rect in args.rect or []:
        targets.append(tuple(map(int, rect.split(","))))
    return targets


def main():
    parser = argparse.ArgumentParser(description="Redraw sprites in a VALE sheet with Qwen-Image-2.1.")
    parser.add_argument("--sheet", required=True, choices=SHEETS)
    parser.add_argument("--tile", action="append", metavar="COL,ROW", help="16x16 tile to redraw (repeatable)")
    parser.add_argument("--rect", action="append", metavar="X,Y,W,H", help="Pixel rect of a larger sprite")
    parser.add_argument("--describe", help="What the sprite depicts (defaults to the tile registry name)")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--write", action="store_true", help="Write the result into Graphics/<sheet>.png")
    parser.add_argument("--preview", help="Save a before/after comparison PNG here")
    args = parser.parse_args()

    targets = parse_targets(args)
    if not targets:
        parser.error("give at least one --tile or --rect")

    from qwen_image import Job, run_jobs

    sheet_path = GRAPHICS_DIR / f"{args.sheet}.png"
    sheet = Sheet.load(sheet_path)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    jobs = []
    for x, y, w, h in targets:
        what = args.describe or registry_name(args.sheet, x, y) or "a fantasy game sprite"
        ref = upscale_reference(sheet, (x, y, w, h), (GEN_SIZE, GEN_SIZE * h // w))
        out = WORK_DIR / f"{args.sheet}_{x}_{y}_{w}x{h}.png"
        jobs.append(Job(REDRAW.format(w=w, h=h, what=what), out, GEN_SIZE, GEN_SIZE * h // w, args.seed, [ref]))
    run_jobs(jobs, steps=args.steps)

    before = Sheet(sheet.path, sheet.pixels.copy(), sheet.palette)
    for (x, y, w, h), job in zip(targets, jobs):
        small = downsample(Image.open(job.output), w, h)
        iou = silhouette_iou(sheet, (x, y, w, h), small)
        if iou < MIN_IOU and args.sheet not in KEEP_SILHOUETTE_SHEETS:
            print(f"  ({x},{y}) rejected: silhouette IoU {iou:.2f} < {MIN_IOU}")
            continue
        keep = args.sheet in KEEP_SILHOUETTE_SHEETS
        sheet.pixels[y : y + h, x : x + w] = encode(sheet, (x, y, w, h), small, keep_silhouette=keep)
        print(f"  ({x},{y}) {w}x{h} redrawn, silhouette IoU {iou:.2f}")

    if args.preview:
        tiles = []
        for x, y, w, h in targets:
            tiles += [preview(s, (x, y, w, h), scale=8) for s in (before, sheet)]
        width = sum(t.width + 8 for t in tiles)
        board = Image.new("RGB", (width, max(t.height for t in tiles)), (255, 255, 255))
        px = 0
        for t in tiles:
            board.paste(t, (px, 0))
            px += t.width + 8
        board.save(args.preview)
        print(f"preview: {args.preview}")

    if args.write:
        sheet.save(sheet_path)
        print(f"wrote {sheet_path.relative_to(REPO)}")
        if args.sheet in OUTLINED_SHEETS:
            print(f"note: regenerate Graphics/{args.sheet}-outlined.png to match")


if __name__ == "__main__":
    main()
