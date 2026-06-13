#!/usr/bin/env python3
"""Build a compact object-attribute plausibility table from VAW data.

Reads raw VAW annotations, maps VAW's fine-grained attributes to the
simplified attribute set used by concept_library.py, and outputs a JSON
filter table at data/processed/vaw_object_attributes.json.

Usage:
    python scripts/build_vaw_filter.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAW_DIR = ROOT / "data" / "external" / "vaw" / "data"
OUT_PATH = ROOT / "data" / "processed" / "vaw_object_attributes.json"

# ── VAW → concept_library attribute mapping ─────────────────────────

COLOR_MAP: dict[str, str] = {
    "red": "red", "bright red": "red", "dark red": "red", "light red": "red",
    "reddish": "red", "rust colored": "red", "maroon": "red", "burgundy": "red",
    "blue": "blue", "bluish": "blue", "bright blue": "blue", "dark blue": "blue",
    "light blue": "blue", "navy blue": "blue", "pale blue": "blue", "teal": "blue",
    "yellow": "yellow", "bright yellow": "yellow", "light yellow": "yellow",
    "golden": "yellow", "amber": "yellow",
    "green": "green", "bright green": "green", "dark green": "green",
    "light green": "green", "lime green": "green", "neon green": "green",
    "olive green": "green", "pale green": "green", "green tinted": "green",
    "black": "black",
    "white": "white", "off white": "white", "ivory": "white", "cream colored": "white",
    "orange": "orange", "terracotta": "orange",
    "purple": "purple", "purplish": "purple", "dark purple": "purple",
    "violet": "purple", "fuchsia": "purple",
    "pink": "pink", "dark pink": "pink",
    "brown": "brown", "dark brown": "brown", "light brown": "brown",
    "golden brown": "brown", "tan": "brown", "taupe": "brown",
    "beige": "brown", "sand colored": "brown", "bronze": "brown",
    "gray": "gray", "dark gray": "gray", "light gray": "gray", "silver": "gray",
}

MATERIAL_MAP: dict[str, str] = {
    "plastic": "plastic", "styrofoam": "plastic",
    "metal": "metal", "aluminum": "metal", "brass": "metal", "chrome": "metal",
    "iron": "metal", "stainless steel": "metal", "steel": "metal",
    "glass": "glass",
    "rubber": "rubber",
    "fabric": "fabric", "cloth": "fabric", "silk": "fabric",
    "paper": "paper", "cardboard": "paper",
    "wooden": "wood", "bamboo": "wood", "hardwood": "wood",
    "ceramic": "ceramic", "porcelain": "ceramic", "clay": "ceramic",
    "leather": "leather",
    "denim": "denim", "jean": "denim",
    "straw": "straw",
    "wool": "wool", "plush": "wool", "fluffy": "wool",
    "furry": "fur",
}

PATTERN_MAP: dict[str, str] = {
    "striped": "striped", "blue striped": "striped", "red striped": "striped",
    "pinstriped": "striped", "lined": "striped",
    "spotted": "spotted", "speckled": "spotted", "polka dotted": "spotted",
    "checkered": "checked", "plaid": "checked", "blue plaid": "checked",
    "dotted": "dotted",
    "floral": "patterned", "patterned": "patterned",
}

ATTR_MAPS = {"color": COLOR_MAP, "material": MATERIAL_MAP, "pattern": PATTERN_MAP}

# ── Objects to extract (union of all concept_library object pools) ───

TARGET_OBJECTS: dict[str, list[str]] = {
    "human": ["passerby", "child", "person", "man", "woman", "boy", "girl"],
    "human_clothing": [
        "shirt", "t-shirt", "jacket", "pants", "hat", "cap", "dress", "coat",
        "scarf", "glove", "shoe", "shorts", "jeans", "sweater", "hoodie",
        "vest", "tie", "helmet", "skirt", "apron", "boots", "socks",
    ],
    "human_features": ["hair", "glasses", "sunglasses", "beard", "backpack", "bag"],
    "animal": ["dog", "cat", "bird", "horse", "duck"],
    "animal_parts": ["collar", "leash", "tail", "wing", "paw"],
    "ground_vehicle": ["bicycle", "scooter", "cart", "stroller", "bike", "motorcycle"],
    "water_vehicle": ["boat", "buoy", "kayak"],
    "tiny_object": ["key", "clip", "cap", "button", "rubber band", "coin", "ring"],
    "sticker_or_tag": ["sticker", "label", "tag", "tape", "poster", "sign"],
    "small_container": ["cup", "bottle", "jar", "tin", "mug", "can", "box", "bucket", "basket"],
    "food_item": ["candy", "fruit", "bun", "bread", "cake", "apple", "banana", "orange"],
    "plant_or_flower": ["plant", "flower", "leaf", "pot", "vase"],
    "tool_or_device": ["flashlight", "camera", "phone", "utensil", "knife", "fork", "clock", "watch", "umbrella"],
    "wearable_accessory": ["badge", "bracelet", "scarf", "hat", "glove", "shoe", "bag", "glasses", "belt", "necklace"],
    "surface_mark": ["patch", "mark", "stripe", "dot", "graffiti"],
}

# Flatten: VAW object name → our object name(s)
# Some VAW names match directly; for others we search substrings
OBJECT_ALIASES: dict[str, str] = {
    "bike": "bicycle",
    "mug": "cup",
    "can": "tin",
    "person": "passerby",
    "man": "passerby",
    "woman": "passerby",
    "boy": "child",
    "girl": "child",
    "t-shirt": "shirt",
    "hoodie": "sweater",
    "boots": "shoe",
    "socks": "shoe",
    "sunglasses": "glasses",
    "knife": "utensil",
    "fork": "utensil",
    "horse": "dog",
    "duck": "bird",
    "kayak": "boat",
    "motorcycle": "bicycle",
    "apple": "fruit",
    "banana": "fruit",
    "bread": "bun",
    "cake": "bun",
}

MIN_POSITIVE = 2
MIN_POSITIVE_RATE = 0.005


def all_target_names() -> set[str]:
    names: set[str] = set()
    for group in TARGET_OBJECTS.values():
        names.update(group)
    return names


def canonical_object(vaw_name: str) -> str | None:
    name = vaw_name.lower().strip()
    targets = all_target_names()
    if name in targets:
        return OBJECT_ALIASES.get(name, name)
    return None


def load_vaw_annotations() -> list[dict]:
    annotations = []
    for fname in ["train_part1.json", "train_part2.json", "val.json", "test.json"]:
        fpath = VAW_DIR / fname
        if not fpath.exists():
            continue
        with open(fpath) as f:
            annotations.extend(json.load(f))
    return annotations


def load_attr_type_index() -> dict[str, str]:
    with open(VAW_DIR / "attribute_types.json") as f:
        attr_types = json.load(f)
    index: dict[str, str] = {}
    for type_name, attrs in attr_types.items():
        for attr in attrs:
            index[attr] = type_name
    return index


def build_stats(annotations: list[dict], type_index: dict[str, str]) -> dict:
    stats: dict[str, dict] = {}

    for ann in annotations:
        obj = canonical_object(ann["object_name"])
        if obj is None:
            continue

        if obj not in stats:
            stats[obj] = {"count": 0, "positive": {}, "negative": {}}
        stats[obj]["count"] += 1

        for attr in ann.get("positive_attributes", []):
            vaw_type = type_index.get(attr)
            if vaw_type not in ATTR_MAPS:
                continue
            mapped = ATTR_MAPS[vaw_type].get(attr)
            if mapped is None:
                continue
            key = f"{vaw_type}:{mapped}"
            stats[obj]["positive"][key] = stats[obj]["positive"].get(key, 0) + 1

        for attr in ann.get("negative_attributes", []):
            vaw_type = type_index.get(attr)
            if vaw_type not in ATTR_MAPS:
                continue
            mapped = ATTR_MAPS[vaw_type].get(attr)
            if mapped is None:
                continue
            key = f"{vaw_type}:{mapped}"
            stats[obj]["negative"][key] = stats[obj]["negative"].get(key, 0) + 1

    return stats


def compute_plausible(stats: dict) -> dict[str, dict[str, list[str]]]:
    table: dict[str, dict[str, list[str]]] = {}

    for obj, obj_stats in stats.items():
        count = obj_stats["count"]
        if count < 5:
            continue

        entry: dict[str, list[str]] = {}
        for attr_type in ("color", "material", "pattern"):
            plausible: list[str] = []
            seen_values: set[str] = set()

            for key, pos_count in obj_stats["positive"].items():
                parts = key.split(":", 1)
                if parts[0] != attr_type:
                    continue
                value = parts[1]
                seen_values.add(value)
                neg_count = obj_stats["negative"].get(key, 0)
                rate = pos_count / count
                if pos_count >= MIN_POSITIVE and rate >= MIN_POSITIVE_RATE and pos_count > neg_count:
                    plausible.append(value)

            if plausible:
                entry[attr_type] = sorted(plausible)

        if entry:
            table[obj] = entry

    return table


def main() -> None:
    print("Loading VAW annotations...")
    annotations = load_vaw_annotations()
    print(f"  {len(annotations)} instances")

    type_index = load_attr_type_index()
    print(f"  {len(type_index)} attributes indexed")

    print("Building per-object stats...")
    stats = build_stats(annotations, type_index)
    print(f"  {len(stats)} objects matched")

    print("Computing plausible attribute sets...")
    table = compute_plausible(stats)
    print(f"  {len(table)} objects with plausible data")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(table, f, indent=2, sort_keys=True, ensure_ascii=False)
    print(f"  Written to {OUT_PATH}")

    print("\nSample entries:")
    for obj in ["leaf", "bottle", "hat", "dog", "flower", "key", "phone"]:
        if obj in table:
            entry = table[obj]
            print(f"  {obj}: colors={entry.get('color', [])}, materials={entry.get('material', [])}")
        else:
            print(f"  {obj}: (no data)")


if __name__ == "__main__":
    main()
