"""Sampling logic for Dynamic V* (ReKey).

Deterministic given (image_id, question_id, run_id, PIPELINE_VERSION).

Uniqueness guarantees:
  - Add objects are never duplicates of scene replace targets (exact + last-word match).
  - Position pairs always have different object categories.
  - Position pairs never use a replace slot whose category has >1 instance in the scene.
  - Position pairs have sufficient spatial separation (dx >= 20px).

Flow:
  1. Sample slots and edits via weighted selection (deterministic RNG).
  2. Validate constraints; repair only the items that violate them.
"""

from __future__ import annotations

import hashlib
import random
from collections import Counter
from typing import Any

from . import PIPELINE_VERSION
from .concept_library import (
    COLORS,
    compatible_pairs,
    infer_question_attribute,
    sample_add_detail,
)
from .schemas import AnnotationRow, SampleSpec, SampledEdit, Slot


SLOT_COUNT_DISTRIBUTION = [(1, 0.80), (2, 0.18), (3, 0.02)]
MIN_POSITION_DX = 20


# ── Primitives ────────────────────────────────────────────────────────────

def stable_seed(*parts: object) -> int:
    text = "||".join(str(part) for part in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def weighted_choice(rng: random.Random, weighted: list[tuple[Any, float]]) -> Any:
    if not weighted:
        raise ValueError("cannot sample from an empty weighted list")
    total = sum(max(0.0, w) for _, w in weighted)
    if total <= 0:
        return rng.choice([item for item, _ in weighted])
    target = rng.random() * total
    cursor = 0.0
    for item, w in weighted:
        cursor += max(0.0, w)
        if cursor >= target:
            return item
    return weighted[-1][0]


def weighted_sample_without_replacement(
    rng: random.Random, weighted: list[tuple[Any, float]], count: int,
) -> list[Any]:
    pool = list(weighted)
    out: list[Any] = []
    for _ in range(min(count, len(pool))):
        picked = weighted_choice(rng, pool)
        out.append(picked)
        pool = [(item, w) for item, w in pool if item is not picked]
    return out


def sample_slot_count(
    rng: random.Random, max_count: int, allow_multislot: bool,
    preferred_attribute: str | None = None,
) -> int:
    if max_count <= 0:
        return 0
    if preferred_attribute == "position":
        return min(2, max_count)
    if preferred_attribute in {"color", "material", "pattern"}:
        return 1
    if not allow_multislot:
        return 1
    return min(int(weighted_choice(rng, SLOT_COUNT_DISTRIBUTION)), max_count)


# ── Slot analysis ─────────────────────────────────────────────────────────

def slot_area(slot: Slot) -> int:
    x1, y1, x2, y2 = slot.edit_region.xyxy
    return max(1, x2 - x1) * max(1, y2 - y1)


def _slot_center_x(slot: Slot) -> float:
    x1, _, x2, _ = slot.edit_region.xyxy
    return (x1 + x2) / 2.0


def _slots_far_enough(a: Slot, b: Slot) -> bool:
    return abs(_slot_center_x(a) - _slot_center_x(b)) >= MIN_POSITION_DX


def valid_operations(slot: Slot) -> list[str]:
    mode = slot.edit_region.mode
    ops: list[str] = []
    if mode in {"add", "either"} and slot.add:
        if slot.add.get("objects"):
            ops.append("add")
        else:
            placements = [str(v) for v in slot.add.get("placements", [])]
            families = [str(v) for v in slot.add.get("entity_families", [])]
            if compatible_pairs(placements, families):
                ops.append("add")
    if mode in {"replace", "either"} and slot.replace:
        if valid_replace_targets(slot.replace):
            ops.append("replace")
    return ops


def slot_weight(slot: Slot, median_area: float) -> float:
    ops = valid_operations(slot)
    if not ops:
        return 0.0
    area = slot_area(slot)
    area_weight = max(0.7, min(1.5, (median_area / area) ** 0.5))
    return area_weight * (1.2 if "replace" in ops else 1.0)


def choose_operation(rng: random.Random, slot: Slot) -> str:
    ops = valid_operations(slot)
    if not ops:
        raise ValueError(f"slot {slot.slot_id} has no valid operation")
    if len(ops) == 1:
        return ops[0]
    return weighted_choice(rng, [("add", 0.55), ("replace", 0.45)])


def source_question(row: AnnotationRow) -> str:
    for key in ("relabel_question", "original_question", "question", "source_question"):
        if row.source.get(key):
            return str(row.source[key])
    return ""


def valid_replace_targets(replace: dict[str, Any]) -> list[dict[str, Any]]:
    raw = replace.get("targets")
    if not isinstance(raw, list):
        return []
    return [
        {"target_ref": str(t.get("target_ref") or "").strip(),
         "edit_types": [str(v) for v in t.get("edit_types", []) if str(v).strip()]}
        for t in raw
        if isinstance(t, dict) and str(t.get("target_ref") or "").strip()
        and any(str(v).strip() for v in t.get("edit_types", []))
    ]


# ── Category helpers ──────────────────────────────────────────────────────

def _parse_base_category(target_ref: str, parse_color_fn: Any) -> str:
    _, obj = parse_color_fn(target_ref)
    return obj.split(" on the ")[0].strip().lower()


def _edit_base_category(edit: SampledEdit, parse_color_fn: Any) -> str:
    if edit.object_name:
        return edit.object_name.lower()
    return _parse_base_category(edit.target_name, parse_color_fn)


def _collect_scene_objects(slots: list[Slot], parse_color_fn: Any) -> set[str]:
    """Object categories from all replace targets.

    Stores both full base ("baby stroller") and last word ("stroller")
    so add candidates using either form are excluded.
    """
    cats: set[str] = set()
    for slot in slots:
        if slot.replace:
            for t in valid_replace_targets(slot.replace):
                base = _parse_base_category(t["target_ref"], parse_color_fn)
                if base:
                    cats.add(base)
                    last = base.split()[-1]
                    if last != base:
                        cats.add(last)
    return cats


def _slot_categories(
    slot: Slot, scene_objects: set[str], parse_color_fn: Any,
) -> set[str]:
    """All categories this slot can produce (add filtered by scene)."""
    cats: set[str] = set()
    if slot.replace:
        for t in valid_replace_targets(slot.replace):
            base = _parse_base_category(t["target_ref"], parse_color_fn)
            if base:
                cats.add(base)
    if slot.add:
        for obj in slot.add.get("objects", []):
            o = str(obj).lower()
            if o and o not in scene_objects:
                cats.add(o)
    return cats


def _dup_replace_cats(slots: list[Slot], parse_color_fn: Any) -> set[str]:
    """Replace-target categories that appear more than once across all slots."""
    counts: Counter[str] = Counter()
    for slot in slots:
        if slot.replace:
            for t in valid_replace_targets(slot.replace):
                counts[_parse_base_category(t["target_ref"], parse_color_fn)] += 1
    return {c for c, n in counts.items() if n > 1}


# ── Edit sampling ─────────────────────────────────────────────────────────

def sample_slot_edit(
    row: AnnotationRow, slot: Slot, operation: str, run_id: str,
    exclude_objects: set[str] | None = None,
) -> tuple[SampledEdit, dict[str, Any]]:
    """Sample a single edit for *slot*. Uses its own stable RNG."""
    seed = stable_seed(row.image_id, run_id, PIPELINE_VERSION, slot.slot_id, operation)
    rng = random.Random(seed)
    preferred = infer_question_attribute(source_question(row))
    trace: dict[str, Any] = {"slot_seed": seed, "preferred_attribute": preferred, "operation": operation}

    if operation == "add":
        add = slot.add or {}
        objects = [str(v) for v in add.get("objects", [])]
        if exclude_objects:
            objects = [o for o in objects if o not in exclude_objects]
        if objects:
            obj = rng.choice(objects)
            color = rng.choice(COLORS)
            trace.update(candidate_objects=objects, sampled_object=obj)
            return SampledEdit(
                slot_id=slot.slot_id, operation="add", placement=None,
                entity_family=None, target_family=None, edit_type="add_object",
                object_name=obj, target_name=f"{color} {obj}",
                answer_attribute="color", answer=color, attributes={"color": color},
            ), trace
        placements = [str(v) for v in add.get("placements", [])]
        families = [str(v) for v in add.get("entity_families", [])]
        pairs = compatible_pairs(placements, families)
        placement, family = rng.choice(pairs)
        detail = sample_add_detail(rng, family, preferred, placement=placement)
        trace["compatible_pairs"] = pairs
        return SampledEdit(
            slot_id=slot.slot_id, operation="add", placement=placement,
            entity_family=family, target_family=None, edit_type="add_object",
            object_name=detail["object_name"], target_name="",
            answer_attribute=detail["answer_attribute"], answer=detail["answer"],
            attributes=detail["attributes"],
        ), trace

    targets = valid_replace_targets(slot.replace or {})
    target = rng.choice(targets)
    target_ref = target["target_ref"]
    from .rule_planner import parse_color, sample_new_color
    old_color, _ = parse_color(target_ref)
    new_color = sample_new_color(old_color, rng, target_ref=target_ref)
    trace.update(target_ref=target_ref, old_color=old_color)
    return SampledEdit(
        slot_id=slot.slot_id, operation="replace", placement=None,
        entity_family=None, target_family=None, edit_type="color_change",
        object_name="", target_name=target_ref,
        answer_attribute="color", answer=new_color, attributes={"color": new_color},
    ), trace


# ── Position pair repair ──────────────────────────────────────────────────

def _find_valid_pair(
    row: AnnotationRow, run_id: str, rng: random.Random,
    first_slot: Slot | None, first_cat: str,
    valid_slots: list[Slot], weighted_slots: list[tuple[Slot, float]],
    scene_objects: set[str], dup_cats: set[str],
    parse_color_fn: Any,
    full_reselect: bool = False,
) -> tuple[SampledEdit, dict, Slot, SampledEdit | None, dict | None, Slot | None] | None:
    """Find a valid position pair or second slot.

    If *full_reselect*: pick an entirely new pair (both slots), avoiding dup-category replace.
    Otherwise: keep first_slot/first_cat fixed, find a compatible second.
    """
    rng_repair = random.Random(rng.randint(0, 2**32))

    if full_reselect:
        def safe_cats(slot: Slot) -> set[str]:
            cats: set[str] = set()
            if slot.replace:
                for t in valid_replace_targets(slot.replace):
                    base = _parse_base_category(t["target_ref"], parse_color_fn)
                    if base and base not in dup_cats:
                        cats.add(base)
            if slot.add:
                for obj in slot.add.get("objects", []):
                    o = str(obj).lower()
                    if o and o not in scene_objects:
                        cats.add(o)
            return cats

        pairs = [
            (sa, sb) for i, sa in enumerate(valid_slots)
            for j, sb in enumerate(valid_slots)
            if j > i and _slots_far_enough(sa, sb)
            and (lambda ca, cb: ca and cb and len(ca | cb) > 1)(safe_cats(sa), safe_cats(sb))
        ]
        if not pairs:
            return None
        slot_a, slot_b = pairs[rng_repair.randint(0, len(pairs) - 1)]
        if rng_repair.random() < 0.5:
            slot_a, slot_b = slot_b, slot_a

        exclude_a = scene_objects.copy()
        op_a = "add" if "add" in valid_operations(slot_a) else "replace"
        try:
            edit_a, trace_a = sample_slot_edit(row, slot_a, op_a, run_id, exclude_objects=exclude_a)
        except (ValueError, IndexError):
            return None
        cat_a = _edit_base_category(edit_a, parse_color_fn)
        if cat_a in dup_cats and edit_a.operation == "replace":
            return None

        exclude_b = scene_objects | {cat_a}
        op_b = "add" if "add" in valid_operations(slot_b) else "replace"
        try:
            edit_b, trace_b = sample_slot_edit(row, slot_b, op_b, run_id, exclude_objects=exclude_b)
        except (ValueError, IndexError):
            return None
        cat_b = _edit_base_category(edit_b, parse_color_fn)
        if cat_b == cat_a or (cat_b in dup_cats and edit_b.operation == "replace"):
            return None
        return edit_a, trace_a, slot_a, edit_b, trace_b, slot_b

    # Find compatible second slot for fixed first
    assert first_slot is not None
    candidates = [
        (s, w) for s, w in weighted_slots
        if s.slot_id != first_slot.slot_id and _slots_far_enough(first_slot, s)
    ]
    rng_repair.shuffle(candidates)
    exclude = scene_objects | {first_cat}

    for slot, _ in candidates:
        if not (_slot_categories(slot, scene_objects, parse_color_fn) - {first_cat}):
            continue
        for op in ["replace", "add"]:
            if op not in valid_operations(slot):
                continue
            if op == "replace":
                rep_cats = {
                    _parse_base_category(t["target_ref"], parse_color_fn)
                    for t in valid_replace_targets(slot.replace)
                }
                if not (rep_cats - {first_cat}) or (rep_cats & dup_cats):
                    continue
            try:
                edit, trace = sample_slot_edit(row, slot, op, run_id, exclude_objects=exclude)
            except (ValueError, IndexError):
                continue
            if _edit_base_category(edit, parse_color_fn) != first_cat:
                return edit, trace, slot, None, None, None
    return None


# ── Entry point ───────────────────────────────────────────────────────────

def sample_image_edits(
    row: AnnotationRow, run_id: str, allow_multislot: bool = False,
) -> SampleSpec:
    seed = stable_seed(row.image_id, row.question_id or "", run_id, PIPELINE_VERSION)
    rng = random.Random(seed)
    preferred = (
        "position" if row.category == "relative_position"
        else infer_question_attribute(source_question(row))
    )
    valid_slots = [s for s in row.slots if valid_operations(s)]
    if not valid_slots:
        raise ValueError(f"{row.image_id} has no valid slots")

    from .rule_planner import parse_color

    areas = sorted(slot_area(s) for s in valid_slots)
    median_area = float(areas[len(areas) // 2])
    weighted_slots = [(s, slot_weight(s, median_area)) for s in valid_slots]

    # ── 1. Sample slots and edits ─────────────────────────────────────
    count = sample_slot_count(
        rng, len(weighted_slots), allow_multislot=allow_multislot,
        preferred_attribute=preferred,
    )
    selected = weighted_sample_without_replacement(rng, weighted_slots, count)
    if len(selected) >= 2 and not _slots_far_enough(selected[0], selected[1]):
        selected = [selected[0]]

    edits: list[SampledEdit] = []
    slot_traces: dict[str, Any] = {}
    used_objects: set[str] = set()
    for slot in selected:
        op = choose_operation(rng, slot)
        edit, trace = sample_slot_edit(row, slot, op, run_id, exclude_objects=used_objects)
        edits.append(edit)
        if edit.object_name:
            used_objects.add(edit.object_name)
        else:
            _, obj = parse_color(edit.target_name)
            used_objects.add(obj.split(" on the ")[0].split()[-1] if obj else "")
        slot_traces[slot.slot_id] = {
            **trace, "valid_operations": valid_operations(slot),
            "slot_weight": slot_weight(slot, median_area),
        }

    # ── 2. Validate and repair ────────────────────────────────────────
    scene_objects = _collect_scene_objects(row.slots, parse_color)
    is_position = preferred == "position"

    # 2a. Fix add-scene collisions
    for i, edit in enumerate(edits):
        if edit.operation == "add" and edit.object_name.lower() in scene_objects:
            slot = next(s for s in selected if s.slot_id == edit.slot_id)
            try:
                new_edit, new_trace = sample_slot_edit(
                    row, slot, "add", run_id, exclude_objects=scene_objects,
                )
                edits[i] = new_edit
                slot_traces[slot.slot_id] = {
                    **new_trace, "valid_operations": valid_operations(slot),
                    "slot_weight": slot_weight(slot, median_area),
                }
            except (ValueError, IndexError):
                pass

    # 2b. Fix position constraints
    if is_position:
        has_same_cat = (
            len(edits) >= 2
            and _edit_base_category(edits[0], parse_color)
            == _edit_base_category(edits[1], parse_color)
            and not (edits[0].operation == "replace" and edits[1].operation == "replace")
        )
        has_add_collision = any(
            e.operation == "add" and e.object_name.lower() in scene_objects
            for e in edits
        )
        needs_second = len(edits) == 1 and len(valid_slots) >= 2

        if has_add_collision:
            result = _find_valid_pair(
                row, run_id, rng, None, "", valid_slots, weighted_slots,
                scene_objects, set(), parse_color, full_reselect=True,
            )
            if result:
                ea, ta, sa, eb, tb, sb = result
                edits = [ea, eb]
                slot_traces = {
                    sa.slot_id: {**ta, "valid_operations": valid_operations(sa),
                                 "slot_weight": slot_weight(sa, median_area)},
                    sb.slot_id: {**tb, "valid_operations": valid_operations(sb),
                                 "slot_weight": slot_weight(sb, median_area)},
                }
            else:
                edits = edits[:1]

        elif has_same_cat or needs_second:
            first_cat = _edit_base_category(edits[0], parse_color)
            result = _find_valid_pair(
                row, run_id, rng, selected[0], first_cat,
                valid_slots, weighted_slots, scene_objects, set(),
                parse_color, full_reselect=False,
            )
            if result:
                new_edit, new_trace, new_slot = result[0], result[1], result[2]
                if has_same_cat:
                    slot_traces.pop(selected[1].slot_id, None)
                    edits[1] = new_edit
                else:
                    edits.append(new_edit)
                slot_traces[new_slot.slot_id] = {
                    **new_trace, "valid_operations": valid_operations(new_slot),
                    "slot_weight": slot_weight(new_slot, median_area),
                }
            elif has_same_cat:
                edits = edits[:1]

    return SampleSpec(
        image_id=row.image_id, question_id=row.question_id,
        run_id=run_id, seed=seed, slot_count=len(edits), edits=edits,
        probability_trace={
            "pipeline_version": PIPELINE_VERSION,
            "allow_multislot": allow_multislot,
            "preferred_attribute": preferred,
            "slot_count_distribution": SLOT_COUNT_DISTRIBUTION,
            "valid_slot_ids": [s.slot_id for s in valid_slots],
            "selected_slot_ids": [e.slot_id for e in edits],
            "slot_traces": slot_traces,
        },
    )
