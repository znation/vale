#!/usr/bin/env python3
"""
sprite_catalog.py — Which sprite lives where, read from the game's own data.

Walks Script/*.dat (classes and their Config blocks, with class-level values inherited by
configs) and the CHARACTER()/ITEM()/... declarations in Main/Include/*.h (to know which
characters are humanoids or large creatures), and maps every sprite rectangle to the things
that use it:

  * char.dat TorsoBitmapPos: the Char sheet for non-humanoids (32x32 for large creatures),
    the Humanoid sheet for humanoids, together with Head/Arm/LegBitmapPos
  * item.dat BitmapPos: the Item sheet; WieldedBitmapPos and the worn-gear positions
    (Helmet, Cloak, TorsoArmor, ...): the Humanoid sheet
  * glterra.dat / olterra.dat BitmapPos: GLTerra / OLTerra; gwterra.dat / owterra.dat: WTerra

Usage:
    python tools/asset_gen/sprite_catalog.py              # writes tools/asset_gen/sprite_catalog.json
    python tools/asset_gen/sprite_catalog.py --show Char   # prints one sheet's entries
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
SCRIPT = REPO / "Script"
OUT = Path(__file__).parent / "sprite_catalog.json"

GEAR_FIELDS = {
    "WieldedBitmapPos": "held in hand",
    "HelmetBitmapPos": "helmet, worn",
    "CloakBitmapPos": "cloak, worn",
    "TorsoArmorBitmapPos": "body armour, worn on the torso",
    "LegArmorBitmapPos": "leg armour, worn",
    "ArmArmorBitmapPos": "arm armour, worn",
    "AthleteArmArmorBitmapPos": "arm armour, worn by a muscular arm",
    "BeltBitmapPos": "belt, worn",
    "BootBitmapPos": "boots, worn",
    "GauntletBitmapPos": "gauntlets, worn",
}
BODY_FIELDS = {"HeadBitmapPos": "head", "TorsoBitmapPos": "torso", "ArmBitmapPos": "arms", "LegBitmapPos": "legs"}


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", " ", text)


def tokenize(text):
    return re.findall(r'"(?:[^"\\]|\\.)*"|==|[{}=;,()]|[^\s{}=;,()"]+', text)


def parse_block(tokens, i):
    """Parse statements until the matching '}'. Returns (fields, configs, next_index)."""
    fields, configs = {}, []
    while i < len(tokens) and tokens[i] != "}":
        if tokens[i] == "Config":
            name = tokens[i + 1]
            i += 2
            if tokens[i] == ";":
                i += 1
            if tokens[i] == "{":
                sub, _, i = parse_block(tokens, i + 1)
                configs.append((name, sub))
            continue
        if i + 1 < len(tokens) and tokens[i + 1] in ("=", "=="):
            key = tokens[i]
            i += 2
            value, depth = [], 0
            while i < len(tokens):
                t = tokens[i]
                if t == "{":
                    depth += 1
                elif t == "}":
                    if depth == 0:
                        break
                    depth -= 1
                elif t == ";" and depth == 0:
                    i += 1
                    break
                value.append(t)
                i += 1
            fields[key] = value
            continue
        if tokens[i] == "{":  # stray nested block
            _, _, i = parse_block(tokens, i + 1)
            continue
        i += 1
    return fields, configs, i + 1


def parse_dat_classes(path):
    """Top-level 'name { ... }' class blocks -> {name: (fields, [(config, fields)])}."""
    tokens = tokenize(strip_comments(path.read_text(encoding="utf-8-sig", errors="replace")))
    classes, i = {}, 0
    while i < len(tokens):
        if i + 1 < len(tokens) and tokens[i + 1] == "{" and re.match(r"^[A-Za-z_]\w*$", tokens[i]):
            name = tokens[i]
            fields, configs, i = parse_block(tokens, i + 2)
            if name in classes:  # a class can be continued in another block
                classes[name][0].update(fields)
                classes[name][1].extend(configs)
            else:
                classes[name] = (fields, configs)
            continue
        i += 1
    return classes


def class_parents():
    parents = {}
    for header in (REPO / "Main" / "Include").glob("*.h"):
        for m in re.finditer(r"^\s*[A-Z]+\((\w+),\s*(\w+)\)", header.read_text(errors="replace"), re.M):
            parents[m.group(1)] = m.group(2)
    return parents


def descends(cls, ancestor, parents):
    seen = set()
    while cls and cls not in seen:
        if cls == ancestor:
            return True
        seen.add(cls)
        cls = parents.get(cls)
    return False


def pos(value):
    nums = [int(t) for t in value if re.match(r"^-?\d+$", t)]
    return tuple(nums[:2]) if len(nums) >= 2 else None


def text(value):
    joined = " ".join(value)
    m = re.search(r'"((?:[^"\\]|\\.)*)"', joined)
    return m.group(1) if m else None


def display_name(fields):
    name = text(fields.get("NameSingular", [])) or ""
    adj = text(fields.get("Adjective", [])) or ""
    post = text(fields.get("PostFix", [])) or ""
    return " ".join(p for p in (adj, name, post) if p).strip()


def variants(classes):
    """Yield (class, config, effective fields) for each class and each of its configs."""
    for cls, (base, configs) in classes.items():
        yield cls, None, base
        for config, fields in configs:
            merged = dict(base)
            merged.update(fields)
            yield cls, config, merged


def build():
    parents = class_parents()
    catalog = defaultdict(lambda: {"names": set(), "uses": set()})

    def add(sheet, xy, size, name, use):
        if not xy or not name:
            return
        entry = catalog[f"{sheet}:{xy[0]},{xy[1]},{size[0]},{size[1]}"]
        entry["names"].add(name)
        entry["uses"].add(use)

    for cls, config, f in variants(parse_dat_classes(SCRIPT / "char.dat")):
        name = display_name(f)
        humanoid = descends(cls, "humanoid", parents)
        large = descends(cls, "largecreature", parents)
        if "TorsoBitmapPos" in f:
            if humanoid:
                add("Humanoid", pos(f["TorsoBitmapPos"]), (16, 16), name, "torso")
            else:
                add("Char", pos(f["TorsoBitmapPos"]), (32, 32) if large else (16, 16), name, "creature")
        if humanoid:
            for field, part in BODY_FIELDS.items():
                if field != "TorsoBitmapPos" and field in f:
                    add("Humanoid", pos(f[field]), (16, 16), name, part)

    for cls, config, f in variants(parse_dat_classes(SCRIPT / "item.dat")):
        name = display_name(f)
        if "BitmapPos" in f:
            add("Item", pos(f["BitmapPos"]), (16, 16), name, "item")
        for field, use in GEAR_FIELDS.items():
            if field in f:
                add("Humanoid", pos(f[field]), (16, 16), name, use)

    for dat, sheet in (("glterra.dat", "GLTerra"), ("olterra.dat", "OLTerra"),
                       ("gwterra.dat", "WTerra"), ("owterra.dat", "WTerra")):
        for cls, config, f in variants(parse_dat_classes(SCRIPT / dat)):
            name = display_name(f) or (config or cls).lower().replace("_", " ")
            for field in ("BitmapPos", "WallBitmapPos"):
                if field in f:
                    add(sheet, pos(f[field]), (16, 16), name, "terrain" if field == "BitmapPos" else "wall")

    return {k: {"names": sorted(v["names"]), "uses": sorted(v["uses"])} for k, v in sorted(catalog.items())}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--show", help="Print the entries for one sheet")
    args = parser.parse_args()
    catalog = build()
    OUT.write_text(json.dumps(catalog, indent=1))
    counts = defaultdict(int)
    for key in catalog:
        counts[key.split(":")[0]] += 1
    print(f"wrote {OUT.relative_to(REPO)}: " + ", ".join(f"{s} {n}" for s, n in sorted(counts.items())))
    if args.show:
        for key, entry in catalog.items():
            if key.startswith(args.show + ":"):
                print(f"{key:28s} {entry['uses']} {entry['names'][:4]}")


if __name__ == "__main__":
    main()
