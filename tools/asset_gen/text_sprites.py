#!/usr/bin/env python3
"""
text_sprites.py — Draw VALE's 4x (64 pixels per tile) sprite sheets from written descriptions.

Every sprite that gets new art is described in prompts/<Sheet>.json, keyed by its rectangle on
the classic sheet ("x,y,w,h"):

    {"subject": "a wolf standing ...", "parts": {"A": "its whole furry body"}}
    {"frame_of": "400,0,16,16", "pose": "the next step of its walk ..."}   an animation frame
    {"frame_of": "128,32,16,16", "lean": -0.1}                           a frame made by leaning the base
    {"skip": "unused art"}                                               keeps the Scale2x art

An entry may also give its own "seed", to redraw a sprite that came out wrong.

Qwen-Image-2.1 draws each subject from text alone, in one shared STYLE, so nothing of the old
16-pixel art (its blockiness, or IVAN's look) carries over. Animation frames are the exception:
they are drawn from their own sprite's new drawing, so the frames match.

Material colours. Nearly every pixel of a VALE sprite takes its colour at draw time from a
material (an iron or a golden sword, a creature's fur, a villager's clothes): the engine keeps
only a channel (A-D) and a brightness per pixel (see sheet_codec.py). So each description names
the parts on each channel the original used, the prompt asks for those parts in marker colours
(A light grey, B orange, C green, D blue), and assembly turns the marker colours back into
channels, with the drawing's shading as the brightness. Details the original drew in fixed
colours (red eyes, a green banknote) keep their natural colours and snap to the sheet palette.

Assembly fits each drawing into the original sprite's opaque bounds, so things keep their size
and place in the tile (creatures stand on the same line, a ring stays small).

Usage:
    ~/venv-qwenimage/bin/python tools/asset_gen/text_sprites.py generate --sheet Char --once
    ~/venv-qwenimage/bin/python tools/asset_gen/text_sprites.py assemble --sheet Char
    ~/venv-qwenimage/bin/python tools/asset_gen/text_sprites.py status
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))

from sheet_codec import FIXED, MATERIAL, TRANSPARENT, Sheet, material_file_index, upscale_sheet  # noqa: E402

REPO = Path(__file__).parent.parent.parent
GRAPHICS = REPO / "Graphics"
HD = GRAPHICS / "4x"
PROMPTS = Path(__file__).parent / "prompts"
MASTERS = Path(__file__).parent / "masters" / "text"

SHEETS = ["Char", "Item", "Humanoid", "GLTerra", "OLTerra", "WTerra"]
# Sheets the engine loads as plain colour images (bitmap, not rawbitmap): no material channels,
# so drawings keep their natural colours.
PLAIN = {"WTerra"}
# Palette file indices a plain sheet's new art may use: 0-63 are left alone, since the loader's
# density rescaling treats them as material ramps.
PLAIN_FIRST_INDEX = 64
OUTLINED = {"Item", "Char", "Humanoid"}
OUTLINE_INDEX = 68  # the black the -outlined sheets use (file index)
SCALE = 4  # physical pixels per layout pixel in Graphics/4x
GEN_PX = 512  # drawing size for a 16x16 sprite
MAX_GEN_SIDE = 768  # 32x32 sprites; larger does not fit qwen_image.py's VRAM budget
SEED = 7
NOTHING_TO_DRAW = 10  # exit code of `generate --once` when the sheet is done (for run scripts)

STYLE = (
    "Friendly storybook fantasy game art: a charming hand-drawn cartoon style with clean rounded shapes, "
    "bold clean dark outlines, soft cel shading with one shadow tone and a gentle highlight, "
    "whimsical and good-humoured"
)

# Marker colour per material channel: its name in prompts and its RGB at brightness 8.
MARKERS = {
    "A": ("light grey", (170, 170, 170)),
    "B": ("orange", (230, 130, 30)),
    "C": ("green", (60, 180, 60)),
    "D": ("blue", (60, 110, 230)),
    # Not a material channel: a part drawn in this keeps a fixed grey the engine doesn't recolour, like the
    # dark stone frame that sets the original doors off from a wall of the same material.
    "F": ("purple", (150, 60, 200)),
}
# The fixed grey an F part takes at the marker's own brightness; its darker shades take darker greys.
FIXED_GREY_LEVEL = 150

PROMPT = (
    "{subject}. A single game sprite for VALE, a light-hearted fantasy roguelike in the spirit of Tolkien. "
    "{style}. {colours}Exactly one subject, whole and centred, filling most of the image. No ground, no cast "
    "shadow, no text, no frame, no background scenery. Not pixel art, not photorealistic."
)
# The whimsical style likes to add a little character peeking from behind bars or curtains; on
# these sheets nothing should be alive unless the description says so.
NOBODY_SHEETS = {"OLTerra"}
NOBODY = "Nobody is in the picture: no people, creatures or faces"
# ... and it likes to give food and shields a smiling face; asking for "no face" only encourages it.
OBJECT = "It is a plain, lifeless object"
LIVELY_WORDS = ("face", "skull", "mask", "mummy", "baby", "statuette", "heart", "Malgorath")

# Humanoid sprites are pieces of a paper doll: each description names what the piece belongs to,
# and its role says which piece to draw.
ROLE_FRAMES = {
    "head": "Only the head and neck of {subject}, seen from the front and looking straight ahead, with no body",
    # "No arms" alone is ignored (half the torsos came with arms or sleeves, doubling the arm sprites); an
    # armless mannequin's shape is not.
    "torso": (
        "The torso alone of {subject}, seen from the front: the shoulders, chest and belly down to the waist, "
        "shaped like an armless dressmaker's mannequin, any clothing sleeveless"
    ),
    "legs": "Only the hips and legs of {subject}, seen from the front, standing with the feet a little apart, with no upper body",
    "arms": "Only one arm of {subject}, seen from the front, from the shoulder down to the hand, with no body",
    "worn": "{subject}, seen from the front, shaped as when worn but with nobody wearing it",
    "held": "{subject}, held level and pointing to the right, seen from the side",
    "shield": "{subject}, held up and seen from the front",
    "tile": "{subject}, filling the whole square image edge to edge",
}
# What each material channel usually is on a humanoid piece, for descriptions that do not say.
ROLE_PARTS = {
    "head": {"A": "the skin of the face", "B": "the hat or hood", "C": "the hair", "D": "the eyes"},
    "torso": {"A": "the bare skin", "B": "the clothing", "C": "the belt and trim", "D": "the collar and decorations"},
    "arms": {"A": "the bare skin and the hand", "B": "the sleeve", "C": "the glove or cuff", "D": "the decoration"},
    "legs": {"A": "the bare skin", "B": "the trousers or skirt", "C": "the boots or shoes", "D": "the decoration"},
    "held": {"A": "the head or blade", "B": "the handle", "C": "the grip", "D": "the decoration"},
    "worn": {"A": "the main material", "B": "the straps and trim", "C": "the fittings", "D": "the decoration"},
    "shield": {"A": "the shield", "B": "the rim", "C": "the boss", "D": "the emblem"},
    "tile": {"A": "the main material", "B": "the second material", "C": "the details", "D": "the decorations"},
}

TEXTURE_PROMPT = (
    "A seamless, tileable, top-down texture of {subject}, filling the whole square image edge to edge, "
    "evenly lit, with no border, no vignette and no single object in the middle. Game ground texture for VALE, "
    "a light-hearted fantasy roguelike. {style}, kept calm and low in contrast so creatures stand out on it. "
    "{colours}Not pixel art, not photorealistic."
)
# Ground textures sit under everything, so they stay close to the originals' quiet brightness:
# their spread of brightness levels is the original's times this, but at least TEXTURE_MIN_SPREAD.
TEXTURE_CONTRAST = 1.1
# Share of each side of a texture drawing cut away, and how much a tiled texture is enlarged (a
# tile shows 1/TEXTURE_ZOOM of the drawing's width; see texture_crop).
TEXTURE_MARGIN = 0.05
TEXTURE_ZOOM = 2
# In a texture whose original had fixed-colour details, a pixel whose colour points this far away
# from every marker (cosine similarity below it) is such a detail.
TEXTURE_FIXED_SIMILARITY = 0.97
TEXTURE_MIN_SPREAD = 0.9

FRAME_PROMPT = (
    "This is a finished game sprite of {subject}. Draw exactly the same subject again, identical in design, "
    "style, colours, size and position in the image, but {pose}. No ground, no cast shadow, no background."
)

# Humanoid body parts and worn gear are stretched over the original silhouette (the engine lays
# them over each other at fixed places), and kept within this many 4x pixels of it.
STRETCHED_ROLES = {"torso", "legs", "worn", "tile"}
SILHOUETTE_SLACK = 2
# The body itself, which must fill its silhouette exactly so the pieces meet (see fill_rows); arms too, and
# worn pieces marked "body" (clothing that covers a body part's whole silhouette, like the tunic).
BODY_ROLES = {"torso", "legs"}

# Mirrorings assembly may apply to match the original's facing (see best_flip): creatures only
# mirror, items may also turn over.
FLIPS = {
    "Char": ("none", "mirror"),
    "Item": ("none", "mirror", "flip", "both"),
    "Humanoid": ("none",),
    "OLTerra": ("none", "mirror"),
}
# Sheets whose sprites stand on the ground: a drawing sits on the bottom of the original's bounds.
STANDING = {"Char", "OLTerra"}

# Animation frames derived from their base sprite rather than drawn: the base names the channels
# to animate ("animate": {"B": "wave"}), and each frame shifts their brightness by up to this many
# levels, as a wave rising through the sprite or as twinkling spots.
SHIMMER_AMPLITUDE = 2

# Lamps ("glow": true) are drawn without their light; its rings (see add_glow) take the originals' brightness.
GLOW_BRIGHTNESS = 8

# Assigning pixels to channels: below this luminance a pixel's hue is unreliable (outlines, deep
# shadow), so it joins the channel of the nearest confidently coloured pixel.
DARK_LUMINANCE = 45
LUMA = np.array([0.299, 0.587, 0.114])
# Paper-doll body pieces are stretched to fill their silhouettes, which widens the drawing's outline and
# shadow into dark bands (the player's legs looked bruised). Their shading is pulled this far toward the
# middle brightness, near the originals' gentle 5-8 range.
BODY_SHADING = 0.5
# Extra cost for a fixed palette colour over a material channel, so shading on a material part
# does not flicker into fixed colours.
FIXED_PENALTY = 25.0


def load_prompts(sheet_name):
    entries = json.loads((PROMPTS / f"{sheet_name}.json").read_text())
    return {key: entry for key, entry in entries.items()}


def rect(key):
    return tuple(int(v) for v in key.split(","))


def master_path(sheet_name, key):
    x, y, w, h = rect(key)
    return MASTERS / sheet_name / f"{x}_{y}_{w}x{h}.png"


def gen_size(key):
    _, _, w, h = rect(key)
    return (min(GEN_PX * w // 16, MAX_GEN_SIDE), min(GEN_PX * h // 16, MAX_GEN_SIDE))


def colour_sentence(parts):
    if not parts:
        return ""
    listed = "; ".join(f"{part} plain {MARKERS[ch][0]}" for ch, part in parts.items())
    return f"Colours: {listed}; any other small details in their natural colours. "


def is_object(sheet_name, entry):
    """Items and the gear humanoids hold or wear: lifeless, unless the description is about something with a face."""
    if sheet_name == "Item" or entry.get("role") in ("held", "shield", "worn"):
        return not any(word in entry.get("subject", "") for word in LIVELY_WORDS)
    return False


def sheet_name_of(sheet):
    return Path(sheet.path).stem


def subject_of(entry):
    role = entry.get("role")
    if not role or entry.get("verbatim"):
        return entry["subject"]
    return ROLE_FRAMES[role].format(subject=entry["subject"])


def parts_of(entry, channels):
    """The entry's parts per channel: its own, or its role's usual ones for the channels the original used."""
    if "parts" in entry:
        return entry["parts"]
    defaults = ROLE_PARTS.get(entry.get("role"), {})
    return {ch: defaults[ch] for ch in "ABCD" if ch in channels and ch in defaults}


def original_channels(sheet, key):
    kind, channel, _, _ = sheet.decode(rect(key))
    return {"ABCD"[c] for c in set(channel[kind == MATERIAL].tolist())}


def prompt_for(entries, key, sheet, plain=False):
    entry = entries[key]
    if entry.get("role") in ("texture", "patch", "strip"):
        parts = {} if plain else parts_of(entry, original_channels(sheet, key)) or {"A": "all of it"}
        return TEXTURE_PROMPT.format(subject=entry["subject"], style=STYLE, colours=colour_sentence(parts))
    if "frame_of" in entry:
        base = entries[entry["frame_of"]]
        return FRAME_PROMPT.format(subject=subject_of(base), pose=entry["pose"])
    parts = {} if plain else parts_of(entry, original_channels(sheet, key))
    subject = subject_of(entry)
    if sheet_name_of(sheet) in NOBODY_SHEETS and "poster" not in subject:
        subject += ". " + NOBODY
    elif is_object(sheet_name_of(sheet), entry):
        subject += ". " + OBJECT
    return PROMPT.format(subject=subject, style=STYLE, colours=colour_sentence(parts))


def job_for(sheet_name, entries, key, sheet):
    from qwen_image import Job

    entry = entries[key]
    width, height = gen_size(key)
    refs = [Image.open(master_path(sheet_name, entry["frame_of"]))] if "frame_of" in entry else []
    return Job(
        prompt_for(entries, key, sheet, plain=sheet_name in PLAIN), master_path(sheet_name, key), width, height,
        entry.get("seed", SEED),
        refs, transparent=entry.get("role") not in ("texture", "patch", "strip"),
    )


def pending(sheet_name, entries):
    """Sprites still to draw that can be drawn now: frames wait for their base sprite's drawing."""
    todo = []
    for key, entry in entries.items():
        if "skip" in entry or "shimmer_of" in entry or "lean" in entry or master_path(sheet_name, key).exists():
            continue
        if "frame_of" in entry and not master_path(sheet_name, entry["frame_of"]).exists():
            continue
        todo.append(key)
    # Base sprites first, so their frames can join a later chunk.
    return sorted(todo, key=lambda k: "frame_of" in entries[k])


def generate(sheet_name, limit, steps, only=None):
    from qwen_image import run_jobs

    entries = load_prompts(sheet_name)
    todo = [k for k in pending(sheet_name, entries) if only is None or k in only][:limit]
    if not todo:
        print(f"{sheet_name}: nothing to draw now")
        return False
    (MASTERS / sheet_name).mkdir(parents=True, exist_ok=True)
    print(f"{sheet_name}: drawing {len(todo)} sprites", flush=True)
    sheet = Sheet.load(GRAPHICS / f"{sheet_name}.png")
    run_jobs([job_for(sheet_name, entries, key, sheet) for key in todo], steps=steps, precision="fp16")
    return True


def opaque_bounds(mask):
    ys, xs = np.nonzero(mask)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def fit(drawing, box, bottom):
    """
    Scale the drawing's opaque part (aspect kept) to fit `box` (x0, y0, x1, y1, in sprite pixels at
    4x), centred horizontally and either centred or standing on the box's bottom. Returns (RGBA
    float array, x, y) of the placed drawing.
    """
    rgba = np.asarray(drawing.convert("RGBA"))
    if not (rgba[..., 3] >= 128).any():
        return None
    x0, y0, x1, y1 = opaque_bounds(rgba[..., 3] >= 128)
    crop = drawing.convert("RGBA").crop((x0, y0, x1, y1))
    bw, bh = box[2] - box[0], box[3] - box[1]
    scale = min(bw / crop.width, bh / crop.height)
    w, h = max(1, round(crop.width * scale)), max(1, round(crop.height * scale))
    # Resize premultiplied, so transparent pixels' colours do not bleed into the edges.
    small = crop.convert("RGBa").resize((w, h), Image.LANCZOS, reducing_gap=3.0).convert("RGBA")
    x = box[0] + (bw - w) // 2
    y = box[3] - h if bottom else box[1] + (bh - h) // 2
    return np.asarray(small).astype(float), x, y


def stretch(drawing, box):
    """The drawing's opaque part resized to exactly fill `box` (x0, y0, x1, y1): body parts must
    cover the silhouette the engine composites them into."""
    rgba = np.asarray(drawing.convert("RGBA"))
    if not (rgba[..., 3] >= 128).any():
        return None
    crop = drawing.convert("RGBA").crop(opaque_bounds(rgba[..., 3] >= 128))
    w, h = box[2] - box[0], box[3] - box[1]
    return np.asarray(crop.convert("RGBa").resize((w, h), Image.LANCZOS, reducing_gap=3.0).convert("RGBA")).astype(float)


def confine(canvas, mask, slack=SILHOUETTE_SLACK):
    """
    Keep a body part within `slack` pixels of the original silhouette and fill the silhouette's
    interior, so parts drawn separately still meet where the engine lays them over each other.
    """
    alpha = canvas[..., 3] >= 128
    if not alpha.any():
        return canvas
    keep = (alpha & ndimage.binary_dilation(mask, iterations=slack)) | ndimage.binary_erosion(mask, iterations=slack)
    _, (iy, ix) = ndimage.distance_transform_edt(~alpha, return_indices=True)
    out = np.where(alpha[..., None], canvas, canvas[iy, ix])
    out[..., 3] = np.where(keep, 255, 0)
    out[~keep] = 0
    return out


def runs(row):
    """(start, end) of each run of True in a boolean row."""
    edges = np.flatnonzero(np.diff(np.concatenate(([0], row.astype(np.int8), [0]))))
    return list(zip(edges[::2], edges[1::2]))


def fill_rows(layer, mask, trim_sides=False):
    """
    Widen each row of a placed body piece to cover the original's silhouette exactly. The engine's
    torso, arms and legs were made to meet edge to edge, so a drawing narrower than its silhouette
    (arms hang beside a narrower waist) leaves a gap between the pieces. Each run of the silhouette
    in a row takes the drawing's pixels across that run, resampled to its width; a run the drawing
    misses copies the nearest row that has some. With trim_sides (torsos, whose sides meet the
    arms), the drawing's dark outline at either end of a run gives way to the colour inside it, so
    no seam shows between torso and arm.
    """
    out = np.zeros_like(layer)
    opaque = layer[..., 3] > 0
    drawn_rows = np.flatnonzero(opaque.any(axis=1))
    if not len(drawn_rows):
        return layer
    for y in range(mask.shape[0]):
        for a, b in runs(mask[y]):
            for src_y in sorted(drawn_rows, key=lambda r: abs(r - y)):
                cols = np.flatnonzero(opaque[src_y, a:b])
                if len(cols):
                    break
            else:
                continue
            lo, hi = a + cols[0], a + cols[-1] + 1
            pick = lo + ((np.arange(b - a) + 0.5) * (hi - lo) / (b - a)).astype(int)
            out[y, a:b] = layer[src_y, pick]
            if trim_sides:
                run = out[y, a:b]
                lit = np.flatnonzero(run[:, :3] @ LUMA >= DARK_LUMINANCE)
                if len(lit):
                    run[: lit[0]] = run[lit[0]]
                    run[lit[-1] + 1 :] = run[lit[-1]]
    return out


def place(sheet_name, role, drawing, kind, body=False):
    """The drawing laid out on a transparent canvas the size of the sprite at 4x."""
    h, w = kind.shape
    mask = np.kron(kind != TRANSPARENT, np.ones((SCALE, SCALE), bool))
    canvas = np.zeros((h * SCALE, w * SCALE, 4))
    if role == "arms":
        # The engine draws the right arm from the sprite's left half and the left arm from its right
        # half; the drawing is one arm, mirrored for the other side.
        half = w * SCALE // 2
        for side, img in ((slice(0, half), drawing), (slice(half, None), drawing.transpose(Image.FLIP_LEFT_RIGHT))):
            part = np.zeros_like(mask)
            part[:, side] = mask[:, side]
            if not part.any():
                continue
            x0, y0, x1, y1 = opaque_bounds(part)
            piece = stretch(img, (x0, y0, x1, y1))
            if piece is not None:
                layer = np.zeros_like(canvas)
                layer[y0:y1, x0:x1] = piece
                layer = fill_rows(confine(layer, part), part)
                canvas = np.where(layer[..., 3:] > 0, layer, canvas)
        return canvas
    box = tuple(v * SCALE for v in opaque_bounds(kind != TRANSPARENT))
    if role in STRETCHED_ROLES:
        piece = stretch(drawing, box)
        if piece is not None:
            canvas[box[1] : box[3], box[0] : box[2]] = piece
            canvas = confine(canvas, mask)
            if role in BODY_ROLES or body:
                canvas = fill_rows(canvas, mask, trim_sides=role == "torso" or body)
        return canvas
    placed = fit(drawing, box, bottom=sheet_name in STANDING)
    if placed is None:
        return canvas
    small, px, py = placed
    flips = FLIPS["Item"] if role in ("held", "shield") else FLIPS[sheet_name]
    canvas[py : py + small.shape[0], px : px + small.shape[1]] = best_flip(small, px, py, mask, flips)
    return confine(canvas, mask) if role == "head" else canvas


def make_seamless(rgb):
    """Blend the image with a copy shifted by half its size, so its edges come from the copy's
    middle and it tiles without seams."""
    h, w, _ = rgb.shape
    shifted = np.roll(rgb, (h // 2, w // 2), axis=(0, 1))
    ramp_y = np.abs(np.arange(h) - (h - 1) / 2) / (h / 2)
    ramp_x = np.abs(np.arange(w) - (w - 1) / 2) / (w / 2)
    weight = np.clip(np.maximum(ramp_y[:, None], ramp_x[None, :]) * 2 - 1, 0, 1)[..., None]
    return rgb * (1 - weight) + shifted * weight


def dither(levels):
    """Floyd-Steinberg rounding of fractional brightness levels, so gentle shading does not band."""
    out = levels.copy()
    h, w = out.shape
    for y in range(h):
        for x in range(w):
            old = out[y, x]
            new = np.rint(old)
            out[y, x] = new
            err = old - new
            if x + 1 < w:
                out[y, x + 1] += err * 7 / 16
            if y + 1 < h:
                if x > 0:
                    out[y + 1, x - 1] += err * 3 / 16
                out[y + 1, x] += err * 5 / 16
                if x + 1 < w:
                    out[y + 1, x + 1] += err / 16
    return out


def texture_indices(drawing, original, key, channels, entry):
    x, y, w, h = rect(key)
    return texture_tile(
        drawing, original, (x, y, w, h), channels, (w * SCALE, h * SCALE),
        zoom=entry.get("zoom"), seamless=entry.get("seamless", True),
    )


def texture_crop(rgb, zoom, seamless):
    """
    The part of a texture drawing a tile is made from. The model tends to frame a texture with a
    thin line (the seamless blend would carry it inside), and its decoder can leave a faint seam
    through the image's centre, so a tiled texture comes from inside one quarter; its details come
    out small, so that part is enlarged (a tile shows 1/zoom of the drawing's width). A texture
    that is not tiled (a single emblem) keeps the whole drawing inside the margin.
    """
    h, w = rgb.shape[:2]
    if not seamless:
        y0, x0 = int(h * TEXTURE_MARGIN), int(w * TEXTURE_MARGIN)
        return rgb[y0 : h - y0, x0 : w - x0]
    keep = min((1 - 2 * TEXTURE_MARGIN) / (zoom or TEXTURE_ZOOM), 0.5 - TEXTURE_MARGIN - 0.01)
    y0, x0 = int(h * TEXTURE_MARGIN), int(w * TEXTURE_MARGIN)
    return rgb[y0 : y0 + int(h * keep), x0 : x0 + int(w * keep)]


def texture_tile(drawing, original, stats_rect, channels, size, zoom=None, seamless=True):
    """A ground texture `size` pixels wide: seamless, each pixel on its marker's channel, and its
    brightness matched to the level and (a little more than) the spread of the original's
    `stats_rect`."""
    rgb = texture_crop(np.asarray(drawing.convert("RGB"), float), zoom, seamless)
    if seamless:
        rgb = make_seamless(rgb)
    rgb = np.asarray(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize(size, Image.LANCZOS), float)
    markers = np.array([MARKERS[ch][1] for ch in channels], float)
    direction = rgb / np.maximum(np.linalg.norm(rgb, axis=-1, keepdims=True), 1)
    similarity = direction @ (markers / np.linalg.norm(markers, axis=-1, keepdims=True)).T
    choice = np.argmax(similarity, axis=-1)
    luminance = rgb @ np.array([0.299, 0.587, 0.114])
    kind, channel, intensity, _ = original.decode(stats_rect)
    out = np.zeros(luminance.shape, np.uint8)
    if (kind == FIXED).any():
        # Details the original drew in fixed colours (a carpet's golden edging) keep their colour.
        fixed = (similarity.max(axis=-1) < TEXTURE_FIXED_SIMILARITY) & (luminance >= DARK_LUMINANCE)
        palette_idx = original.fixed_indices()
        d = np.linalg.norm(rgb[fixed][:, None] - original.palette[palette_idx][None].astype(float), axis=-1)
        out[fixed] = palette_idx[d.argmin(axis=-1)]
        choice[fixed] = -1
    for i, ch in enumerate(channels):
        here = choice == i
        if not here.any():
            continue
        was = (kind == MATERIAL) & (channel == "ABCD".index(ch))
        target = intensity[was] if was.any() else intensity[kind == MATERIAL]
        spread = max(target.std() * TEXTURE_CONTRAST, TEXTURE_MIN_SPREAD)
        lum = luminance[here]
        levels = np.zeros(luminance.shape)
        levels[here] = (lum - lum.mean()) / max(lum.std(), 1e-6) * spread + target.mean()
        levels = np.clip(dither(levels), 1, 15).astype(int)
        out[here] = material_file_index("ABCD".index(ch), levels[here])
    return out


def lean(canvas, amount):
    """A placed sprite sheared sideways with its foot kept in place: each row moves by `amount`
    times its height above the foot (negative: to the left). Sways a standing sprite without
    drawing each frame, at the base sprite's size."""
    opaque = canvas[..., 3] >= 128
    if not opaque.any():
        return canvas
    foot = np.nonzero(opaque.any(axis=1))[0].max()
    out = np.zeros_like(canvas)
    for y in range(canvas.shape[0]):
        shift = int(round(amount * (foot - y)))
        if shift > 0:
            out[y, shift:] = canvas[y, :-shift]
        elif shift < 0:
            out[y, :shift] = canvas[y, -shift:]
        else:
            out[y] = canvas[y]
    return out


def paint_patches(result, base, original, entry, drawing):
    """
    Terrain drawn as blobs over a 3x3 block of tiles (liquids, cave earth; see
    glterrain::GetBorderBitmapPos): each listed block is filled with the seamless texture, tiled and
    shifted by `scroll` 4x pixels per block, within the Scale2x outline of the original blob.
    """
    channels = sorted(entry.get("parts") or {"A": ""})
    tile = SCALE * 16
    for i, block in enumerate(entry["blocks"]):
        cx, cy = (int(v) for v in block.split(","))
        texture = texture_tile(drawing, original, (cx - 16, cy - 16, 48, 48), channels, (tile, tile), zoom=entry.get("zoom"))
        sx, sy = (i * v for v in entry.get("scroll", (0, 0)))
        big = np.roll(np.tile(texture, (3, 3)), (sy, sx), axis=(0, 1))
        bx, by = (cx - 16) * SCALE, (cy - 16) * SCALE
        mask = base.decode((bx, by, 3 * tile, 3 * tile))[0] != TRANSPARENT
        region = result.pixels[by : by + 3 * tile, bx : bx + 3 * tile]
        region[mask] = big[mask]


def glow_core(kind, channel):
    """The original's lamp without its glow rings (channels B-D), for fitting the drawing of the lamp alone."""
    return np.where((kind == MATERIAL) & (channel > 0), TRANSPARENT, kind)


def add_glow(indices, opaque):
    """
    Lamps (see lantern::GetAlphaB) draw channels B, C and D as translucent light that pulses: the
    originals ring the lamp with one pixel of each, B innermost. The same rings, SCALE pixels wide,
    around the placed lamp. Returns the new indices and opaque mask.
    """
    indices, grown = indices.copy(), opaque.copy()
    for c in (1, 2, 3):
        ring = ndimage.binary_dilation(grown, iterations=SCALE) & ~grown
        indices[ring] = material_file_index(c, GLOW_BRIGHTNESS)
        grown |= ring
    return indices, grown


def soften(indices, amount=BODY_SHADING):
    """Material pixels' brightness pulled toward the middle (8) by `amount`, keeping their channels."""
    e = 255 - indices.astype(int)
    material = e >= 192
    channel = (e - 192) >> 4
    level = np.rint(8 + ((e & 15) - 8) * (1 - amount)).astype(int)
    out = indices.copy()
    out[material] = material_file_index(channel[material], np.clip(level, 1, 15)[material])
    return out


def shimmer(indices, animate, phase):
    """A frame derived from a base sprite's file indices: the animated channels' brightness moves
    by up to SHIMMER_AMPLITUDE, as a wave rising through the sprite or as twinkling spots."""
    out = indices.copy()
    e = 255 - indices.astype(int)
    material = e >= 192
    channel = (e - 192) >> 4
    level = e & 15
    h, w = indices.shape
    yy, xx = np.mgrid[0:h, 0:w]
    spots = np.random.default_rng(1).random(((h + 3) // 4, (w + 3) // 4))[yy // 4, xx // 4]
    for ch, kind in animate.items():
        c = "ABCD".index(ch)
        here = material & (channel == c)
        offset = (1 - yy / h) if kind == "wave" else spots
        delta = np.rint(SHIMMER_AMPLITUDE * np.sin(2 * np.pi * (phase + offset)))
        out[here] = material_file_index(c, np.clip(level + delta, 1, 15)[here].astype(int))
    return out


def best_flip(small, px, py, original_mask, flips):
    """
    The drawing mirrored or flipped (within `flips`) to best overlap the original sprite's
    silhouette: the model does not reliably follow "facing left" or "tip to the upper right".
    """
    region = original_mask[py : py + small.shape[0], px : px + small.shape[1]]

    def overlap(img):
        mask = img[..., 3] >= 128
        return (mask & region).sum() / max((mask | region).sum(), 1)

    candidates = [small, small[:, ::-1], small[::-1], small[::-1, ::-1]][: len(flips)]
    return max(candidates, key=overlap)


def nearest_grey(levels, palette_rgb, palette_idx):
    """File indices of the palette's fixed greys nearest to each grey level."""
    grey = np.ptp(palette_rgb, axis=1) <= 12
    values, indices = palette_rgb[grey].mean(axis=1), palette_idx[grey]
    return indices[np.abs(levels[..., None] - values).argmin(axis=-1)]


def classify(rgb, opaque, channels, allow_fixed, palette_rgb, palette_idx):
    """
    File indices for opaque pixels: each goes to the marker channel whose colour, at the best-fitting
    brightness, reproduces it most closely (or to the nearest fixed colour, when allowed; the F
    marker gives a fixed grey of that brightness). Dark pixels take the channel of the nearest
    clearly coloured pixel.
    """
    h, w, _ = rgb.shape
    costs, results = [], []
    for ch in channels:
        base = np.array(MARKERS[ch][1], float)
        t = np.clip(np.rint(8 * (rgb @ base) / (base @ base)), 0, 15)
        costs.append(np.linalg.norm(rgb - t[..., None] * base / 8, axis=-1))
        if ch == "F":
            results.append(nearest_grey(t * FIXED_GREY_LEVEL / 8, palette_rgb, palette_idx))
        else:
            results.append(material_file_index("ABCD".index(ch), t.astype(int)))
    if allow_fixed or not channels:
        d = np.linalg.norm(rgb[..., None, :] - palette_rgb[None, None], axis=-1)
        costs.append(d.min(axis=-1) + (FIXED_PENALTY if channels else 0))
        results.append(palette_idx[d.argmin(axis=-1)])
    choice = np.argmin(np.stack(costs), axis=0)

    if channels:
        luminance = rgb @ LUMA
        confident = opaque & (luminance >= DARK_LUMINANCE)
        if confident.any():
            _, (iy, ix) = ndimage.distance_transform_edt(~confident, return_indices=True)
            dark = opaque & ~confident
            # A dark pixel keeps its own best class only if that is a fixed colour (e.g. black eyes).
            fixed_class = len(channels)
            keep = choice == fixed_class
            choice = np.where(dark & ~keep, choice[iy, ix], choice)
    out = np.choose(choice, results).astype(np.uint8)
    return out


def assemble(sheet_name):
    entries = load_prompts(sheet_name)
    original = Sheet.load(GRAPHICS / f"{sheet_name}.png")
    base = upscale_sheet(original, SCALE)
    result = Sheet(str(HD / f"{sheet_name}.png"), base.pixels.copy(), base.palette)
    palette_idx = original.fixed_indices()
    palette_rgb = original.palette[palette_idx].astype(float)
    done = 0
    # Odd-sized or misaligned rectangles last, so they win where they overlap a neighbour.
    for key in sorted(entries, key=lambda k: (rect(k)[0] % 16 or rect(k)[1] % 16, rect(k)[1], rect(k)[0])):
        # A leaning frame is its base sprite's drawing, sheared (see lean).
        path = master_path(sheet_name, entries[key]["frame_of"] if "lean" in entries[key] else key)
        if "skip" in entries[key] or "shimmer_of" in entries[key] or not path.exists():
            continue
        x, y, w, h = rect(key)
        kind = original.decode((x, y, w, h))[0]
        if not (kind != TRANSPARENT).any():
            continue
        base_entry = entries[entries[key].get("frame_of", key)]
        if base_entry.get("role") == "patch":
            paint_patches(result, base, original, base_entry, Image.open(path))
            done += 1
            continue
        if base_entry.get("role") == "texture":
            channels = sorted(parts_of(base_entry, original_channels(original, key)) or {"A": ""})
            result.pixels[y * SCALE : (y + h) * SCALE, x * SCALE : (x + w) * SCALE] = texture_indices(
                Image.open(path), original, key, channels, base_entry
            )
            done += 1
            continue
        if base_entry.get("glow"):
            kind = glow_core(*original.decode((x, y, w, h))[:2])
        if "lean" in entries[key]:
            base_kind = original.decode(rect(entries[key]["frame_of"]))[0]
            canvas = lean(place(sheet_name, base_entry.get("role"), Image.open(path), base_kind, base_entry.get("body")), entries[key]["lean"])
        else:
            canvas = place(sheet_name, base_entry.get("role"), Image.open(path), kind, base_entry.get("body"))
        opaque = canvas[..., 3] >= 128
        if not opaque.any():
            continue
        base_key = entries[key].get("frame_of", key)
        channels = sorted(parts_of(base_entry, original_channels(original, base_key)))
        allow_fixed = (kind == FIXED).any()
        indices = classify(canvas[..., :3], opaque, channels, allow_fixed, palette_rgb, palette_idx)
        if base_entry.get("role") in BODY_ROLES | {"arms"} or base_entry.get("body"):
            indices = soften(indices)
        indices[~opaque] = result.transparent_index
        if base_entry.get("glow"):
            indices, opaque = add_glow(indices, opaque)
        result.pixels[y * SCALE : (y + h) * SCALE, x * SCALE : (x + w) * SCALE] = indices
        done += 1
    for key, entry in entries.items():
        if "shimmer_of" not in entry:
            continue
        bx, by, bw, bh = (v * SCALE for v in rect(entry["shimmer_of"]))
        if not master_path(sheet_name, entry["shimmer_of"]).exists():
            continue
        base_indices = result.pixels[by : by + bh, bx : bx + bw]
        x, y, w, h = (v * SCALE for v in rect(key))
        result.pixels[y : y + h, x : x + w] = shimmer(base_indices, entries[entry["shimmer_of"]]["animate"], entry["phase"])
        done += 1
    HD.mkdir(parents=True, exist_ok=True)
    result.save()
    print(f"wrote {Path(result.path).relative_to(REPO)} ({done} new sprites)")
    if sheet_name in OUTLINED:
        outlined = Sheet(str(HD / f"{sheet_name}-outlined.png"), result.pixels.copy(), result.palette)
        kind = outlined.decode()[0]
        ring = ndimage.binary_dilation(kind != TRANSPARENT, structure=np.ones((3, 3)), iterations=SCALE)
        outlined.pixels[ring & (kind == TRANSPARENT)] = OUTLINE_INDEX
        outlined.save()
        print(f"wrote {Path(outlined.path).relative_to(REPO)}")


def texture_rgb(drawing, size, zoom=None):
    """A seamless colour texture `size` pixels wide from a texture drawing (see texture_tile)."""
    rgb = make_seamless(texture_crop(np.asarray(drawing.convert("RGB"), float), zoom, True))
    return np.asarray(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize(size, Image.LANCZOS), float)


def assemble_plain(sheet_name):
    """
    A plain colour sheet (the world map): the Scale2x base in its own colours, with new sprites,
    ground patches and animated strips pasted in, then reduced to one palette. A 2x version is
    written as well, so the engine never has to rescale it.
    """
    entries = load_prompts(sheet_name)
    original = Sheet.load(GRAPHICS / f"{sheet_name}.png")
    base = upscale_sheet(original, SCALE)
    canvas = original.palette[base.pixels].astype(float)
    # The sheet may hold magenta in more than one palette entry; any of them is see-through.
    transparent = (canvas == (255, 0, 255)).all(axis=-1)
    tile = SCALE * 16
    done = 0
    for key, entry in entries.items():
        path = master_path(sheet_name, key)
        if "skip" in entry or not path.exists():
            continue
        drawing = Image.open(path)
        x, y, w, h = rect(key)
        role = entry.get("role")
        if role == "patch":
            texture = np.tile(texture_rgb(drawing, (tile, tile), entry.get("zoom")), (3, 3, 1))
            for block in entry["blocks"]:
                cx, cy = (int(v) for v in block.split(","))
                bx, by = (cx - 16) * SCALE, (cy - 16) * SCALE
                mask = ~transparent[by : by + 3 * tile, bx : bx + 3 * tile]
                canvas[by : by + 3 * tile, bx : bx + 3 * tile][mask] = texture[mask]
        elif role == "strip":
            texture = texture_rgb(drawing, (tile, tile), entry.get("zoom"))
            dx, dy = entry.get("scroll", (0, 0))
            for i in range(entry["frames"]):
                fx = (x + i * entry["step"]) * SCALE
                canvas[y * SCALE : y * SCALE + tile, fx : fx + tile] = np.roll(texture, (i * dy, i * dx), axis=(0, 1))
                transparent[y * SCALE : y * SCALE + tile, fx : fx + tile] = False
        else:
            kind = original.decode((x, y, w, h))[0]
            box = tuple(v * SCALE for v in opaque_bounds(kind != TRANSPARENT))
            placed = fit(drawing, box, bottom=True)
            if placed is None:
                continue
            small, px, py = placed
            region = (slice(y * SCALE, (y + h) * SCALE), slice(x * SCALE, (x + w) * SCALE))
            layer = np.zeros((h * SCALE, w * SCALE, 4))
            layer[py : py + small.shape[0], px : px + small.shape[1]] = small
            opaque = layer[..., 3] >= 128
            transparent[region] = ~opaque
            canvas[region][opaque] = layer[..., :3][opaque]
        done += 1
    for scale in (SCALE, 2):
        rgb, clear = canvas, transparent
        if scale != SCALE:
            f = SCALE // scale
            rgb = canvas.reshape(canvas.shape[0] // f, f, canvas.shape[1] // f, f, 3).mean(axis=(1, 3))
            clear = transparent.reshape(transparent.shape[0] // f, f, transparent.shape[1] // f, f).mean(axis=(1, 3)) > 0.5
        write_plain(GRAPHICS / f"{scale}x" / f"{sheet_name}.png", rgb, clear, original)
    print(f"wrote Graphics/4x and Graphics/2x/{sheet_name}.png ({done} new drawings)")
    if write_new_blocks(sheet_name, entries, original, canvas, transparent):
        print(f"wrote new blocks into Graphics/{sheet_name}.png")


def write_new_blocks(sheet_name, entries, original, canvas, transparent):
    """
    The 1x sheet is the classic art and otherwise left alone, but a ground patch marked "new" has no
    classic art (it took over an unused block), so its drawing goes there too: its opaque pixels
    averaged down to 1x (the see-through ones are magenta, which would tint the edges) within the
    block's original shape, in the nearest of the sheet's own colours.
    """
    blocks = [b for e in entries.values() if e.get("new") and e.get("role") == "patch" for b in e["blocks"]]
    if not blocks:
        return False
    pixels = original.pixels.copy()
    palette = original.palette.astype(float)
    usable = np.flatnonzero((original.palette != (255, 0, 255)).any(axis=1))
    for block in blocks:
        cx, cy = (int(v) for v in block.split(","))
        x0, y0 = cx - 16, cy - 16
        rows, cols = slice(y0 * SCALE, (y0 + 48) * SCALE), slice(x0 * SCALE, (x0 + 48) * SCALE)
        weight = (~transparent[rows, cols]).astype(float).reshape(48, SCALE, 48, SCALE, 1)
        region = canvas[rows, cols].reshape(48, SCALE, 48, SCALE, 3)
        small = (region * weight).sum(axis=(1, 3)) / np.maximum(weight.sum(axis=(1, 3)), 1)
        shape = (original.palette[pixels[y0 : y0 + 48, x0 : x0 + 48]] != (255, 0, 255)).any(axis=-1)
        nearest = usable[np.linalg.norm(small[..., None, :] - palette[usable][None, None], axis=-1).argmin(axis=-1)]
        pixels[y0 : y0 + 48, x0 : x0 + 48][shape] = nearest[shape]
    Sheet(str(GRAPHICS / f"{sheet_name}.png"), pixels, original.palette).save()
    return True


def write_plain(path, rgb, clear, original):
    """Save colour art as the engine's 8-bit PNG: opaque pixels quantized into palette entries
    PLAIN_FIRST_INDEX and up (entries below keep the original's), clear ones magenta."""
    count = 256 - PLAIN_FIRST_INDEX - 1  # one entry stays magenta
    opaque = rgb[~clear].astype(np.uint8)
    strip = Image.fromarray(opaque.reshape(1, -1, 3))
    quantized = strip.quantize(colors=count, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    colours = np.array(quantized.getpalette()[: 3 * count], np.uint8).reshape(-1, 3)
    palette = original.palette.copy()
    palette[PLAIN_FIRST_INDEX : PLAIN_FIRST_INDEX + len(colours)] = colours
    magenta = PLAIN_FIRST_INDEX + count
    palette[magenta] = (255, 0, 255)
    pixels = np.full(clear.shape, magenta, np.uint8)
    pixels[~clear] = PLAIN_FIRST_INDEX + np.asarray(quantized)[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    Sheet(str(path), pixels, palette).save()


def status():
    for sheet_name in SHEETS:
        if not (PROMPTS / f"{sheet_name}.json").exists():
            continue
        entries = load_prompts(sheet_name)
        wanted = [k for k, e in entries.items() if not {"skip", "shimmer_of", "lean"} & e.keys()]
        drawn = sum(master_path(sheet_name, k).exists() for k in wanted)
        print(f"{sheet_name}: {drawn}/{len(wanted)} drawn, {len(entries) - len(wanted)} skipped")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["generate", "assemble", "status"])
    parser.add_argument("--sheet", choices=SHEETS)
    parser.add_argument("--chunk", type=int, default=12, help="Sprites per model load")
    parser.add_argument("--once", action="store_true", help="Draw a single chunk, then exit")
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--only", help="Draw just these sprites: rectangles 'x,y,w,h' separated by ';'")
    args = parser.parse_args()
    only = set(args.only.split(";")) if args.only else None
    if args.command == "status":
        status()
    elif args.command == "generate":
        drew = generate(args.sheet, args.chunk, args.steps, only)
        while drew and not args.once:
            drew = generate(args.sheet, args.chunk, args.steps, only)
        if not drew:
            sys.exit(NOTHING_TO_DRAW)
    elif args.sheet in PLAIN:
        assemble_plain(args.sheet)
    else:
        assemble(args.sheet)


if __name__ == "__main__":
    from qwen_image import run_then_exit

    run_then_exit(main)
