#!/usr/bin/env python3
"""
scene_art.py — Full-screen art for VALE (main-menu backgrounds, dungeon entry images)
generated with Qwen-Image-2.1 within qwen_image.py's VRAM limits.

  * Menu1-5.png: the main menu shows MenuN behind option N (Start, Continue, Configuration,
    Highscores, Quit). The options are printed at y≈155-364 on black bars, so the art keeps
    its middle calm; a shared transparent "VALE" title logo is composited into the top band.
  * Wraithstalker.png / Shadowpaw.png: shown while entering those Gloomy Caves levels, with
    the busy text displaced to one side, so the subject sits on the other side over black.

Every image is rendered at 800x608 (the nearest size the model accepts), cropped to 800x600,
resized for each pixel density the engine supports (Graphics/, Graphics/2x/, Graphics/4x/) and
quantized to the 256-colour indexed PNG the engine requires. Renders are fp16 (see
qwen_image.run_jobs). Masters (the raw renders) are
kept under tools/asset_gen/masters/ (git-ignored) so post-processing can be redone without
regenerating; an existing Logo master is reused unless Logo is named with --only.

Usage:
    ~/venv-qwenimage/bin/python tools/asset_gen/scene_art.py            # generate + install all
    ~/venv-qwenimage/bin/python tools/asset_gen/scene_art.py --only Menu1 --seed 7
    ~/venv-qwenimage/bin/python tools/asset_gen/scene_art.py --install-only   # re-run post-processing
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))

REPO = Path(__file__).parent.parent.parent
GRAPHICS = REPO / "Graphics"
MASTERS = Path(__file__).parent / "masters"

SCREEN = (800, 600)
RENDER = (800, 608)  # multiple of 32; cropped to SCREEN

STYLE = (
    "Dark fantasy digital painting in the tradition of classic 1980s fantasy book covers: painterly brushwork, "
    "earthy palette of deep greens, slate blues and umber with warm firelight accents, atmospheric but clearly "
    "lit scene with a strong focal light, rich atmosphere, highly detailed, no text, no letters, no watermark."
)
MENU_LAYOUT = (
    " Wide establishing shot. The top of the image is open sky or shadow with little detail, and the centre of "
    "the image is calm and not busy."
)

SCENES = {
    "Menu1": (
        "A lone cloaked adventurer holding a lantern stands at the edge of a vast misty vale at dusk, seen from "
        "behind. A winding path descends past a ruined watchtower on a crag into the valley, toward jagged dark "
        "mountains." + MENU_LAYOUT
    ),
    "Menu2": (
        "An ancient forest of enormous moss-covered oaks at twilight. A narrow path winds between crumbling "
        "standing stones carved with runes, pale moonlight falls in shafts through the canopy, a few fireflies."
        + MENU_LAYOUT
    ),
    "Menu3": (
        "A dwarven forge hall deep beneath a mountain: a great anvil, hammers and tongs hanging on the walls, "
        "glowing embers in a stone hearth, massive rune-carved pillars fading into darkness." + MENU_LAYOUT
    ),
    "Menu4": (
        "A vast torch-lit hall of fallen heroes: tall stone statues of armoured warriors with swords line both "
        "walls, tattered banners hang from the vaulted ceiling, a great stone memorial slab at the far end."
        + MENU_LAYOUT
    ),
    "Menu5": (
        "The walled medieval town of Oakhaven at night, seen from a hill: timber-framed houses with warm glowing "
        "windows, a tall cathedral spire, chimney smoke, a starry sky over distant hills." + MENU_LAYOUT
    ),
    "Wraithstalker": (
        "Horror portrait of the Wraithstalker, a hulking hunched humanoid monster whose head is a huge gaping "
        "shark-like maw full of needle teeth, wearing a ragged fisherman's smock, a fishing rod over its shoulder "
        "and a wooden bucket of dead fish in one hand, wailing. Full figure, standing in the right half of the "
        "image, lit by a cold rim light. The entire left half of the image is plain pure black. Pure black "
        "background everywhere."
    ),
    "Shadowpaw": (
        "Horror portrait: Shadowpaw, a gigantic monstrous mutant rabbit with shaggy grey fur, blazing pale eyes and "
        "long fangs, looms out of the darkness behind a stocky bearded man in a long greatcoat and fur hat who "
        "holds a sickle. Both figures are in the left half of the image. The entire right third of the image is "
        "plain pure black. Pure black background everywhere."
    ),
}
PORTRAIT_STYLE = (
    "Grim dark fantasy ink and oil illustration, stark chiaroscuro, desaturated palette with a single sickly "
    "accent colour, highly detailed, no text, no letters, no watermark."
)

LOGO = (
    "The word \"VALE\" as a fantasy video game title logo: four large ornate capital letters forged from weathered "
    "dark iron with gold edging and faint engraved runes, a subtle ember glow along the edges, crisp clean "
    "silhouette, centred, no other text, no background elements."
)
LOGO_RENDER = (1152, 384)
LOGO_BOX = (70, 20, 730, 140)  # where the title sits on the 800x600 menu (above the first option at y=155)


def prompts():
    for name, text in SCENES.items():
        style = PORTRAIT_STYLE if name in ("Wraithstalker", "Shadowpaw") else STYLE
        yield name, f"{text} {style}"


def generate(names, seed, steps, regenerate_logo):
    from qwen_image import Job, run_jobs

    MASTERS.mkdir(parents=True, exist_ok=True)
    jobs = []
    if "Logo" in names and (regenerate_logo or not (MASTERS / "Logo.png").exists()):
        jobs.append(Job(LOGO, MASTERS / "Logo.png", *LOGO_RENDER, seed=seed, transparent=True))
    for name, text in prompts():
        if name in names:
            jobs.append(Job(text, MASTERS / f"{name}.png", *RENDER, seed=seed, transparent=False))
    if jobs:
        run_jobs(jobs, steps=steps, precision="fp16")


def to_indexed(img, colors=256):
    """Quantize to an indexed PNG the engine accepts: 8-bit, exactly 256 palette entries, no pure magenta."""
    img = img.convert("RGB")
    arr = np.asarray(img).copy()
    # (255, 0, 255) is the engine's transparent colour for masked blits; nudge any stray pixels off it.
    arr[(arr[..., 0] > 247) & (arr[..., 1] < 4) & (arr[..., 2] > 247)] = (240, 8, 240)
    img = Image.fromarray(arr)
    q = img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
    pal = (q.getpalette() + [0] * 768)[:768]
    q.putpalette(pal)
    return q


def compose_menu(background, logo, density=1):
    bg = background
    if logo is not None:
        x0, y0, x1, y1 = (v * density for v in LOGO_BOX)
        mark = logo.convert("RGBA")
        bbox = mark.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
        if bbox:
            mark = mark.crop(bbox)
        scale = min((x1 - x0) / mark.width, (y1 - y0) / mark.height)
        mark = mark.resize((round(mark.width * scale), round(mark.height * scale)), Image.LANCZOS)
        pos = (x0 + (x1 - x0 - mark.width) // 2, y0 + (y1 - y0 - mark.height) // 2)
        # A soft dark halo keeps the title readable over any background.
        halo = Image.new("L", bg.size, 0)
        halo.paste(mark.getchannel("A"), pos)
        halo = halo.filter(ImageFilter.GaussianBlur(10 * density)).point(lambda a: min(255, int(a * 1.6)))
        bg = Image.composite(Image.new("RGB", bg.size, (0, 0, 0)), bg, halo.point(lambda a: a * 3 // 4))
        bg.paste(mark, pos, mark)
    return bg


# The engine loads Graphics/<D>x/<name> at pixel density D (see graphics::ResolveDensityAsset);
# without one it would repeat each pixel of the 800x600 image D times.
DENSITIES = (1, 2, 4)


def install(names):
    logo_path = MASTERS / "Logo.png"
    logo = Image.open(logo_path) if logo_path.exists() else None
    for name in SCENES:
        if name not in names:
            continue
        master = MASTERS / f"{name}.png"
        if not master.exists():
            print(f"skip {name}: no master at {master}")
            continue
        img = Image.open(master).convert("RGB")
        scale = img.width / SCREEN[0]
        crop_h = round(SCREEN[1] * scale)
        top = (img.height - crop_h) // 2
        img = img.crop((0, top, img.width, top + crop_h))
        for density in DENSITIES:
            size = (SCREEN[0] * density, SCREEN[1] * density)
            frame = img.resize(size, Image.LANCZOS) if img.size != size else img
            if name.startswith("Menu"):
                frame = compose_menu(frame, logo, density)
            out = GRAPHICS / (f"{density}x/" if density > 1 else "") / f"{name}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            to_indexed(frame).save(out)
            print(f"installed {out.relative_to(REPO)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--only", nargs="+", help="Subset of: Logo " + " ".join(SCENES))
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--install-only", action="store_true", help="Rebuild Graphics/ PNGs from existing masters")
    args = parser.parse_args()
    names = set(args.only or ["Logo", *SCENES])
    if not args.install_only:
        generate(names, args.seed, args.steps, regenerate_logo=bool(args.only and "Logo" in args.only))
    install(names | ({"Menu1", "Menu2", "Menu3", "Menu4", "Menu5"} if "Logo" in names else set()))


if __name__ == "__main__":
    from qwen_image import run_then_exit

    run_then_exit(main)
