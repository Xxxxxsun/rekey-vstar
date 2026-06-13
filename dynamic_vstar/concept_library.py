from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Any


P_GROUND = "ground_surface"
P_TABLE = "countertop_or_table"
P_SHELF = "shelf_or_display"
P_WATER = "water_surface"
P_VERT = "vertical_surface"
P_VEHICLE = "vehicle_surface"
P_BODY = "body_or_clothing_surface"
P_INSIDE = "container_inside"
P_AIR = "hanging_or_overhead_area"

SURFACE_PLACEMENTS = (P_GROUND, P_TABLE, P_SHELF)
STICK_PLACEMENTS = (P_VERT, P_VEHICLE, P_BODY)

COLORS = ["red", "blue", "yellow", "green", "black", "white", "orange", "purple", "pink", "brown", "gray"]
MATERIALS = [
    "plastic",
    "metal",
    "glass",
    "rubber",
    "fabric",
    "paper",
    "wood",
    "ceramic",
    "leather",
    "denim",
    "cotton",
    "wool",
]
PATTERNS = ["striped", "spotted", "checked", "plain", "dotted"]

ATTRIBUTE_SCOPES: dict[str, dict[str, tuple[str, ...]]] = {
    "wearable": {"material": ("fabric", "leather", "denim", "cotton", "wool", "rubber")},
    "rigid": {"material": ("metal", "plastic", "glass", "wood", "ceramic", "rubber")},
    "paper": {"material": ("paper", "plastic", "fabric")},
}

ATTRIBUTE_SCOPE_ALIASES = {
    "container": "rigid",
    "hard_object": "rigid",
    "surface": "rigid",
    "paper_label": "paper",
    "vehicle_part": "rigid",
    "tool_device": "rigid",
    "wearable_material": "wearable",
    "container_material": "rigid",
    "hard_object_material": "rigid",
    "surface_material": "rigid",
    "paper_label_material": "paper",
    "vehicle_part_material": "rigid",
    "tool_device_material": "rigid",
}

TARGET_KEYWORD_ATTRIBUTE_SCOPES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("glove", "hat", "shoe", "bag", "shirt", "apron", "clothing", "dress", "coat", "scarf", "pants", "jacket", "vest", "tie",
      "手套", "帽", "鞋", "包", "衣", "围裙", "裤", "裙", "外套"), "wearable"),
    (("sign", "label", "poster", "price card", "tag", "标牌", "标签", "海报", "价目牌"), "paper"),
    (("bottle", "cup", "jar", "box", "bucket", "camera", "phone", "clock", "utensil", "tool",
      "wheel", "light", "mirror", "handlebar", "vehicle", "wall", "table", "surface", "glasses",
      "瓶", "杯", "罐", "盒", "桶", "相机", "手机", "钟", "工具", "车", "轮", "灯", "镜", "墙", "桌", "眼镜"), "rigid"),
)


@dataclass(frozen=True)
class AddConcept:
    objects: dict[str, tuple[str, ...]]
    colors: tuple[str, ...]
    materials: tuple[str, ...]
    patterns: tuple[str, ...] = ("plain",)
    default_attribute: str = "color"
    sub_items: tuple[str, ...] | None = None


@dataclass(frozen=True)
class ReplaceConcept:
    targets: tuple[str, ...]
    colors: tuple[str, ...] = tuple(COLORS)
    materials: tuple[str, ...] = tuple(MATERIALS)
    patterns: tuple[str, ...] = tuple(PATTERNS)
    default_attribute_scope: str | None = None


ADD_CONCEPTS: dict[str, AddConcept] = {
    "human": AddConcept(
        objects={
            "passerby": (P_GROUND,),
            "child": (P_GROUND,),
        },
        colors=("blue", "red", "yellow", "green", "white", "black", "gray", "brown", "pink", "orange", "purple"),
        materials=("fabric", "denim", "leather"),
        patterns=("plain", "striped", "checked"),
        sub_items=(
            "shirt", "jacket", "pants", "hat", "dress", "coat", "scarf",
            "glove", "shoe", "shorts", "vest", "tie", "helmet", "skirt", "apron", "backpack",
        ),
    ),
    "animal": AddConcept(
        objects={
            "dog": (P_GROUND,),
            "cat": (P_GROUND,),
            "bird": (P_GROUND, P_WATER, P_AIR),
        },
        colors=("brown", "black", "white", "gray", "orange"),
        materials=("fur", "feather"),
        patterns=("plain", "spotted"),
    ),
    "vehicle": AddConcept(
        objects={
            "bicycle": (P_GROUND,),
            "kick scooter": (P_GROUND,),
            "cart": (P_GROUND,),
            "stroller": (P_GROUND,),
            "boat": (P_WATER,),
            "buoy": (P_WATER,),
        },
        colors=("red", "blue", "yellow", "black", "white", "green"),
        materials=("metal", "plastic", "wood"),
        patterns=("plain", "striped"),
    ),
    "tiny_object": AddConcept(
        objects={
            "clip": (*SURFACE_PLACEMENTS, P_INSIDE),
            "cap": (*SURFACE_PLACEMENTS, P_INSIDE),
        },
        colors=("red", "blue", "yellow", "green", "orange", "black", "white", "gray"),
        materials=("plastic", "rubber", "metal"),
        patterns=("plain", "striped", "dotted"),
    ),
    "sticker_or_tag": AddConcept(
        objects={
            "sticker": (P_TABLE, P_VERT, P_VEHICLE, P_BODY),
            "label": (P_TABLE, P_VERT, P_VEHICLE, P_BODY),
            "tape strip": (P_TABLE, P_VERT),
            "tag": (P_TABLE, P_VERT, P_VEHICLE, P_BODY),
            "sign": (P_TABLE, P_VERT),
            "poster": (P_TABLE, P_VERT),
        },
        colors=("red", "blue", "yellow", "green", "white", "black", "orange"),
        materials=("paper", "plastic", "metal"),
        patterns=("plain", "striped", "checked"),
    ),
    "small_container": AddConcept(
        objects={
            "cup": SURFACE_PLACEMENTS,
            "bottle": SURFACE_PLACEMENTS,
            "jar": SURFACE_PLACEMENTS,
            "tin": (*SURFACE_PLACEMENTS, P_INSIDE),
            "bucket": SURFACE_PLACEMENTS,
            "box": SURFACE_PLACEMENTS,
            "vase": SURFACE_PLACEMENTS,
        },
        colors=("red", "blue", "yellow", "green", "white", "black", "gray", "brown"),
        materials=("plastic", "glass", "metal", "ceramic", "wood"),
        patterns=("plain", "striped"),
        default_attribute="material",
    ),
    "food_item": AddConcept(
        objects={
            "candy": (*SURFACE_PLACEMENTS, P_INSIDE),
            "fruit slice": (*SURFACE_PLACEMENTS, P_INSIDE),
            "bun": (*SURFACE_PLACEMENTS, P_INSIDE),
            "snack packet": (*SURFACE_PLACEMENTS, P_INSIDE),
        },
        colors=("red", "yellow", "green", "orange", "brown", "white"),
        materials=("food", "paper"),
        patterns=("plain", "striped"),
    ),
    "plant_or_flower": AddConcept(
        objects={
            "potted plant": SURFACE_PLACEMENTS,
            "flower": (*SURFACE_PLACEMENTS, P_INSIDE, P_AIR),
            "leaf": (*SURFACE_PLACEMENTS, P_INSIDE, P_AIR),
        },
        colors=("green", "yellow", "red", "pink", "purple", "white", "orange"),
        materials=("plant",),
        patterns=("plain",),
        default_attribute="color",
    ),
    "tool_or_device": AddConcept(
        objects={
            "flashlight": SURFACE_PLACEMENTS,
            "camera": SURFACE_PLACEMENTS,
            "phone": SURFACE_PLACEMENTS,
            "utensil": SURFACE_PLACEMENTS,
            "umbrella": SURFACE_PLACEMENTS,
            "clock": SURFACE_PLACEMENTS,
        },
        colors=("black", "white", "gray", "red", "blue", "yellow", "brown", "orange"),
        materials=("metal", "plastic", "wood"),
        patterns=("plain",),
        default_attribute="material",
    ),
    "wearable_accessory": AddConcept(
        objects={
            "badge": (*SURFACE_PLACEMENTS, P_BODY, P_INSIDE),
            "hair clip": (*SURFACE_PLACEMENTS, P_BODY, P_INSIDE),
            "scarf": (*SURFACE_PLACEMENTS, P_BODY, P_AIR),
            "bracelet": (*SURFACE_PLACEMENTS, P_BODY, P_INSIDE),
            "belt": (*SURFACE_PLACEMENTS, P_BODY),
            "necklace": (*SURFACE_PLACEMENTS, P_BODY, P_INSIDE),
        },
        colors=("red", "blue", "yellow", "green", "white", "black", "pink", "brown"),
        materials=("fabric", "plastic", "metal", "leather"),
        patterns=("plain", "striped", "spotted"),
    ),
    "surface_mark": AddConcept(
        objects={
            "stripe": (P_TABLE, *STICK_PLACEMENTS),
            "patch": (P_TABLE, *STICK_PLACEMENTS),
        },
        colors=("red", "blue", "yellow", "green", "black", "white", "orange"),
        materials=("paint",),
        patterns=("plain", "striped", "dotted"),
    ),
}


REPLACE_CONCEPTS: dict[str, ReplaceConcept] = {
    "human_wearable": ReplaceConcept(("glove", "apron", "hat", "shoe", "bag", "shirt", "jacket", "pants", "dress", "coat", "scarf", "vest"), default_attribute_scope="wearable"),
    "human_detail": ReplaceConcept(("hair", "glasses", "helmet"), default_attribute_scope="rigid"),
    "animal_marking": ReplaceConcept(("collar",), default_attribute_scope="wearable"),
    "vehicle_part": ReplaceConcept(("wheel", "light", "mirror", "handlebar"), default_attribute_scope="rigid"),
    "sign_or_label": ReplaceConcept(("sign", "label", "poster", "price card"), default_attribute_scope="paper"),
    "container_or_bottle": ReplaceConcept(("bottle", "cup", "jar", "box", "bucket", "vase"), default_attribute_scope="rigid"),
    "tool_or_device": ReplaceConcept(("camera", "phone", "clock", "utensil", "umbrella"), default_attribute_scope="rigid"),
    "small_existing_object": ReplaceConcept(("cap", "clip", "key", "ornament"), default_attribute_scope="rigid"),
}


ADD_OBJECT_POOL: dict[str, list[str]] = {
    P_GROUND: ["bag", "bucket", "umbrella", "bottle", "box", "bicycle", "kick scooter", "stroller", "dog", "cat"],
    P_TABLE: ["cup", "bottle", "box", "bowl", "bag", "umbrella", "phone", "flower"],
    P_VERT: ["poster", "sign", "clock", "flag"],
    P_WATER: ["boat", "duck", "kayak", "float"],
    P_AIR: ["bird", "balloon", "kite", "flag"],
}


def infer_question_attribute(question: str | None) -> str | None:
    text = (question or "").lower()
    if re.search(r"\bcolor|colour\b", text):
        return "color"
    if re.search(r"\bmaterial|made of\b", text):
        return "material"
    if re.search(r"\bpattern|striped|spotted|checked\b", text):
        return "pattern"
    if re.search(r"\bleft|right|above|below|position|where\b", text):
        return "position"
    return None


def objects_for_placement(family: str, placement: str) -> list[str]:
    concept = ADD_CONCEPTS.get(family)
    if concept is None:
        return []
    return [obj for obj, placements in concept.objects.items() if placement in placements]


def compatible_pairs(placements: list[str], entity_families: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for placement in placements:
        for family in entity_families:
            if objects_for_placement(family, placement):
                pairs.append((placement, family))
    return pairs


def choose_answer_attribute(
    preferred: str | None,
    available: set[str],
    default_attribute: str = "color",
) -> str:
    if preferred in available:
        return str(preferred)
    if default_attribute in available:
        return default_attribute
    for fallback in ("color", "material", "pattern"):
        if fallback in available:
            return fallback
    return sorted(available)[0]


def sample_add_detail(
    rng: random.Random,
    entity_family: str,
    preferred_attribute: str | None,
    placement: str | None = None,
) -> dict[str, Any]:
    from .vaw_filter import filter_pool

    concept = ADD_CONCEPTS[entity_family]
    eligible = objects_for_placement(entity_family, placement) if placement else list(concept.objects.keys())
    if not eligible:
        eligible = list(concept.objects.keys())
    object_name = rng.choice(eligible)
    sub_item = rng.choice(concept.sub_items) if concept.sub_items else None
    filter_key = sub_item or object_name
    colors = filter_pool(filter_key, "color", concept.colors)
    materials = filter_pool(filter_key, "material", concept.materials)
    patterns = filter_pool(filter_key, "pattern", concept.patterns)
    attrs = {
        "color": rng.choice(colors),
        "material": rng.choice(materials),
        "pattern": rng.choice(patterns),
    }
    if sub_item:
        attrs["sub_item"] = sub_item
    answer_attribute = choose_answer_attribute(
        preferred_attribute,
        {"color", "material", "pattern"},
        default_attribute=concept.default_attribute,
    )
    return {
        "object_name": object_name,
        "target_name": "",
        "answer_attribute": answer_attribute,
        "answer": attrs[answer_attribute],
        "attributes": attrs,
    }


def forced_replace_edit_type(preferred_attribute: str | None, edit_types: list[str]) -> str | None:
    if preferred_attribute == "color" and "color_change" in edit_types:
        return "color_change"
    if preferred_attribute == "material" and "material_change" in edit_types:
        return "material_change"
    if preferred_attribute == "pattern" and "pattern_change" in edit_types:
        return "pattern_change"
    return None


def edit_type_to_attribute(edit_type: str) -> str:
    if edit_type == "material_change":
        return "material"
    if edit_type == "pattern_change":
        return "pattern"
    return "color"


def canonical_attribute_scope(scope: str | None) -> str | None:
    if not scope:
        return None
    return ATTRIBUTE_SCOPE_ALIASES.get(scope, scope)


def infer_attribute_scope(target_name: str, target_family: str | None = None) -> str | None:
    text = target_name.lower()
    for keywords, scope in TARGET_KEYWORD_ATTRIBUTE_SCOPES:
        if any(keyword in text for keyword in keywords):
            return scope
    if target_family and target_family in REPLACE_CONCEPTS:
        return REPLACE_CONCEPTS[target_family].default_attribute_scope
    return None


def materials_for_scope(scope: str | None) -> tuple[str, ...]:
    canonical = canonical_attribute_scope(scope)
    if canonical and canonical in ATTRIBUTE_SCOPES:
        return ATTRIBUTE_SCOPES[canonical].get("material", tuple(MATERIALS))
    return tuple(MATERIALS)


def sample_replace_detail(
    rng: random.Random,
    target_family: str | None,
    edit_type: str,
    target_ref: str = "",
    attribute_scope: str | None = None,
) -> dict[str, Any]:
    concept = REPLACE_CONCEPTS.get(target_family or "")
    target_name = target_ref.strip() or (rng.choice(concept.targets) if concept else "target")
    resolved_attribute_scope = canonical_attribute_scope(attribute_scope) or infer_attribute_scope(target_name, target_family)
    material_pool = materials_for_scope(resolved_attribute_scope)
    attrs = {
        "color": rng.choice(concept.colors if concept else COLORS),
        "material": rng.choice(material_pool),
        "pattern": rng.choice(concept.patterns if concept else PATTERNS),
    }
    answer_attribute = edit_type_to_attribute(edit_type)
    return {
        "object_name": "",
        "target_name": target_name,
        "answer_attribute": answer_attribute,
        "answer": attrs[answer_attribute],
        "attributes": {**attrs, "attribute_scope": resolved_attribute_scope or "general"},
    }


def distractors_for(
    attribute: str,
    answer: str,
    rng: random.Random,
    count: int = 3,
    attribute_scope: str | None = None,
) -> list[str]:
    pools = {
        "color": COLORS,
        "material": list(materials_for_scope(attribute_scope)),
        "pattern": PATTERNS,
    }
    pool = [value for value in pools.get(attribute, COLORS) if value != answer]
    rng.shuffle(pool)
    return pool[:count]
