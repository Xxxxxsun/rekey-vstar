"""Rule-based planner for Dynamic V*.

All target_refs follow one of two formats:
  1. "{color} {object}"                    — "red bicycle"
  2. "{color} {item} on the {owner}"       — "blue jacket on the cyclist"

This module provides:
  - parse_color: strip color prefix from target_ref
  - for_question: prepare target_ref for color question (strip color)
  - for_position: prepare target_ref for position question (replace color, invert sub-item)
  - build_attr_question: full color QA
  - build_position_question: full left/right QA
  - build_edit_prompt: image editing instruction
"""

from __future__ import annotations

import random
import re
from typing import Any

from .concept_library import COLORS

# Recognized color prefixes, longest first for greedy matching.
COLOR_PREFIXES = sorted(
    [
        "rose-pink", "silver-gray", "gray-blue", "brown-red", "brown-yellow",
        "light pink", "light blue", "dark blue", "dark green", "dark red",
        "colorful", "golden",
        "white", "black", "red", "blue", "green", "yellow", "orange",
        "purple", "pink", "gray", "brown", "silver", "gold", "magenta",
    ],
    key=len,
    reverse=True,
)

# Multi-color: "orange-and-white", "red-and-yellow striped", "blue-white-and-yellow"
MULTI_COLOR_RE = re.compile(r"^([\w]+-(?:and-)?[\w]+(?:-and-[\w]+)*(?:\s+striped)?)\s+", re.I)

# Sub-item pattern: "{item} on the {owner}"
SUB_ITEM_RE = re.compile(r"^(.+?)\s+on the\s+(.+)$")


def parse_color(target_ref: str) -> tuple[str | None, str]:
    """Extract (color, rest) from target_ref. Color is always the prefix."""
    ref = target_ref.strip()

    m = MULTI_COLOR_RE.match(ref)
    if m:
        return m.group(1).lower(), ref[m.end():]

    ref_lower = ref.lower()
    for color in COLOR_PREFIXES:
        if ref_lower.startswith(color + " "):
            return color, ref[len(color) + 1:]

    return None, ref


def for_question(target_ref: str) -> str:
    """Strip color from target_ref for use in color questions.

    "red bicycle" → "the bicycle"
    "blue jacket on the cyclist" → "the jacket on the cyclist"
    """
    _, rest = parse_color(target_ref)
    return f"the {rest}"


def for_position(target_ref: str, new_color: str) -> str:
    """Prepare target_ref for position questions with new color.

    Simple: "red bicycle" + green → "the green bicycle"
    Sub-item: "blue jacket on the cyclist" + red → "the cyclist with the red jacket"
    Add object: "bottle" + red → "the red bottle"
    """
    _, rest = parse_color(target_ref)
    m = SUB_ITEM_RE.match(rest)
    if m:
        item, owner = m.group(1), m.group(2)
        return f"the {owner} with the {new_color} {item}"
    return f"the {new_color} {rest}"


def _color_exclusion_set(color: str | None) -> set[str]:
    """Build the set of colors to exclude given a (possibly multi-) color."""
    excluded: set[str] = set()
    if not color:
        return excluded
    excluded.add(color)
    for part in re.split(r"[-\s]+(?:and[-\s]+)?", color):
        if part and part != "striped":
            excluded.add(part)
    return excluded


def sample_new_color(
    old_color: str | None,
    rng: random.Random,
    pool: list[str] | None = None,
    also_exclude: set[str] | None = None,
    target_ref: str | None = None,
    use_vaw: bool = False,
) -> str:
    if pool is None:
        pool = list(COLORS)
    if use_vaw and target_ref:
        from .vaw_filter import filter_pool as vaw_filter
        _, obj = parse_color(target_ref)
        obj_key = obj.split(" on the ")[0].split()[-1] if obj else ""
        if obj_key:
            filtered = list(vaw_filter(obj_key, "color", tuple(pool)))
            if len(filtered) >= 3:
                pool = filtered
    excluded = _color_exclusion_set(old_color)
    if also_exclude:
        excluded |= also_exclude
    candidates = [c for c in pool if c not in excluded]
    return rng.choice(candidates) if candidates else rng.choice(pool)


def build_attr_question(
    target_ref: str,
    new_color: str,
    rng: random.Random,
) -> dict[str, Any]:
    """Build a color question."""
    old_color, _ = parse_color(target_ref)
    phrase = for_question(target_ref)

    excluded = _color_exclusion_set(old_color) | {new_color}
    distractors = [c for c in COLORS if c not in excluded]
    rng.shuffle(distractors)
    distractors = distractors[:3]

    values = [new_color] + distractors
    rng.shuffle(values)
    letters = ["A", "B", "C", "D"]
    options = dict(zip(letters, values))
    correct_label = next(l for l, v in options.items() if v == new_color)

    return {
        "question_type": "color",
        "question": f"What color is {phrase}?",
        "answer": new_color,
        "old_color": old_color,
        "distractors": distractors,
        "options": options,
        "correct_label": correct_label,
    }


def build_position_question(
    target_ref_a: str,
    new_color_a: str,
    target_ref_b: str,
    new_color_b: str,
    center_x_a: float,
    center_y_a: float,
    center_x_b: float,
    center_y_b: float,
    min_separation: float = 20.0,
    operation_a: str = "replace",
    operation_b: str = "replace",
) -> dict[str, Any]:
    """Build a position question. Prefers left/right; falls back to above/below.

    Replace objects include their new color for identification (the recolored
    object needs color to distinguish it from its original appearance).
    Add objects use category only (unique in scene by construction).
    """
    phrase_a = for_position(target_ref_a, new_color_a) if operation_a == "replace" else for_question(target_ref_a)
    phrase_b = for_position(target_ref_b, new_color_b) if operation_b == "replace" else for_question(target_ref_b)
    dx = abs(center_x_a - center_x_b)
    dy = abs(center_y_a - center_y_b)

    if dx >= min_separation and dx >= dy:
        answer = "left" if center_x_a < center_x_b else "right"
        return {
            "question_type": "position_left_right",
            "question": f"Is {phrase_a} to the left or right of {phrase_b}?",
            "answer": answer,
            "options": {"A": "left", "B": "right"},
            "correct_label": "A" if answer == "left" else "B",
        }

    answer = "above" if center_y_a < center_y_b else "below"
    return {
        "question_type": "position_above_below",
        "question": f"Is {phrase_a} above or below {phrase_b}?",
        "answer": answer,
        "options": {"A": "above", "B": "below"},
        "correct_label": "A" if answer == "above" else "B",
    }


def build_edit_prompt(target_ref: str, new_color: str) -> str:
    """Build image edit instruction for replace."""
    old_color, rest = parse_color(target_ref)
    if old_color:
        return (
            f"Change ONLY the color of the {old_color} {rest} to {new_color}. "
            f"Do NOT modify any surrounding pixels. "
            f"Keep shape, material, texture, and background exactly the same."
        )
    return (
        f"Change ONLY the color of the {target_ref} to {new_color}. "
        f"Do NOT modify any other pixels."
    )


def build_add_edit_prompt(object_name: str, color: str) -> str:
    """Build image edit instruction for add."""
    return (
        f"Add a {color} {object_name} in the marked area, "
        f"sized naturally for the scene context. "
        f"Do NOT modify any pixels outside the marked area. "
        f"Keep the background exactly the same."
    )
