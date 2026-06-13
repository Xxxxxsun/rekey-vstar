#!/usr/bin/env python3
"""Convert a Dynamic V* Label Studio export into visual-key slot JSONL.

The current Label Studio config is
``docs/dynamic_vstar/labelstudio_config.xml``. Annotators draw paired regions:

  * ``context_region``: large crop region with ``context_slot_id`` and
    ``context_ref``. New annotations use context ids like ``A`` / ``B``.
  * ``edit_region``: small editable region with ``edit_slot_id``, mode, and
    add/replace concept choices. New annotations use edit ids like ``A1`` /
    ``A2`` / ``B1``.

The parser pairs edits to contexts by exact id first, then by the alphabetic
prefix of the edit id. This keeps legacy ``S1``/``S1`` exports valid while
allowing one context box ``A`` to own multiple edit boxes ``A1``, ``A2``.

    {
      "image_id": "vstar_0004",
      "question_id": "4",
      "category": "direct_attributes",
      "slots": [
        {
          "slot_id": "A1",
          "context_region": {"xyxy": [...], "ref": "..."},
          "edit_region": {"xyxy": [...], "mode": "add"},
          "add": {"placements": [...], "entity_families": [...]}
        }
      ]
    }

Validation is intentionally conservative: incomplete slots are skipped with a
warning printed to stderr, while other valid slots in the same image are still
emitted.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

VALID_LABELS = {"context_region", "edit_region"}
VALID_MODES = {"add", "replace", "either"}
VALID_PLACEMENTS = {
    "ground_surface",
    "countertop_or_table",
    "shelf_or_display",
    "water_surface",
    "vertical_surface",
    "vehicle_surface",
    "body_or_clothing_surface",
    "container_inside",
    "hanging_or_overhead_area",
}
VALID_ENTITY_FAMILIES = {
    "human",
    "animal",
    "vehicle",
    "tiny_object",
    "sticker_or_tag",
    "small_container",
    "food_item",
    "plant_or_flower",
    "tool_or_device",
    "wearable_accessory",
    "surface_mark",
}
VALID_REPLACE_EDIT_TYPES = {
    "color_change",
}

CANONICAL_VALUES = {
    "新增物体": "add",
    "新增物体 add": "add",
    "替换已有物体": "replace",
    "替换已有物体 replace": "replace",
    "新增或替换都可以": "either",
    "都可以 either": "either",
    "可站立地面": "ground_surface",
    "草坪/草地": "ground_surface",
    "道路/小路": "ground_surface",
    "地面（草坪/道路/地板/广场）": "ground_surface",
    "柜台/桌面": "countertop_or_table",
    "平面（桌椅/台面/窗台）": "countertop_or_table",
    "货架/展示台": "shelf_or_display",
    "货架/展柜（有层板的）": "shelf_or_display",
    "水面": "water_surface",
    "墙面/牌面/窗面": "vertical_surface",
    "墙面/物体表面": "vertical_surface",
    "竖面（墙壁/门板/靠背）": "vertical_surface",
    "车辆表面": "vehicle_surface",
    "身体/衣物表面": "body_or_clothing_surface",
    "容器内部": "container_inside",
    "容器里（篮子/碗/桶内）": "container_inside",
    "悬挂/上方区域": "hanging_or_overhead_area",
    "悬挂处（晾绳/栏杆/树枝）": "hanging_or_overhead_area",
    "空中/上方区域": "hanging_or_overhead_area",
    "空中/上方（天空/树枝/晾绳）": "hanging_or_overhead_area",
    "人": "human",
    "动物": "animal",
    "地面交通工具": "vehicle",
    "水面交通工具": "vehicle",
    "交通工具": "vehicle",
    "小物件": "tiny_object",
    "小杂物（钥匙/夹子/纽扣）": "tiny_object",
    "贴纸/标签": "sticker_or_tag",
    "贴纸/标签/标牌": "sticker_or_tag",
    "小容器": "small_container",
    "瓶罐杯桶": "small_container",
    "食物": "food_item",
    "植物/花": "plant_or_flower",
    "工具/设备": "tool_or_device",
    "工具/电子设备": "tool_or_device",
    "穿戴配件": "wearable_accessory",
    "表面标记": "surface_mark",
    "人的穿戴物": "human_wearable",
    "人的局部细节": "human_detail",
    "动物标记/项圈": "animal_marking",
    "车辆部件": "vehicle_part",
    "标牌/标签": "sign_or_label",
    "容器/瓶子": "container_or_bottle",
    "食物/展示物": "food_or_display_item",
    "表面细节": "surface_detail",
    "已有小物体": "small_existing_object",
    "wearable_material": "wearable",
    "container_material": "container",
    "hard_object_material": "hard_object",
    "surface_material": "surface",
    "paper_label_material": "paper_label",
    "vehicle_part_material": "vehicle_part",
    "tool_device_material": "tool_device",
    "衣物/穿戴材质": "wearable",
    "容器/瓶子材质": "container",
    "硬物材质": "hard_object",
    "表面材质": "surface",
    "纸张/标签材质": "paper_label",
    "车辆部件材质": "vehicle_part",
    "工具/设备材质": "tool_device",
    "穿戴类范围": "wearable",
    "穿戴类（布/皮/棉/毛/橡胶）": "wearable",
    "容器/瓶子范围": "rigid",
    "硬物范围": "rigid",
    "硬物（金属/塑料/玻璃/木/陶瓷）": "rigid",
    "表面范围": "rigid",
    "纸张/标签范围": "paper",
    "纸质（纸/塑料/布）": "paper",
    "车辆部件范围": "rigid",
    "工具/设备范围": "rigid",
    "container": "rigid",
    "hard_object": "rigid",
    "surface": "rigid",
    "paper_label": "paper",
    "vehicle_part": "rigid",
    "tool_device": "rigid",
    "改颜色": "color_change",
    "改材质": "material_change",
    "改图案": "pattern_change",
    "改纹样（条纹/格子/圆点）": "pattern_change",
    "替换小部件": "color_change",
    "加小配件": "color_change",
    "加贴纸/标签": "color_change",
    "加标记/斑点/条纹": "color_change",
    # add_objects value normalization
    "wall_flag": "flag",
    "air_flag": "flag",
    "water_bird": "bird",
    "air_bird": "bird",
    "bucket_float": "bucket",
    # add_objects Chinese labels → English values
    "包/袋": "bag",
    "桶": "bucket",
    "雨伞": "umbrella",
    "瓶子": "bottle",
    "箱子/盒子": "box",
    "自行车": "bicycle",
    "滑板车": "kick scooter",
    "婴儿车": "stroller",
    "狗": "dog",
    "猫": "cat",
    "杯子": "cup",
    "碗": "bowl",
    "手机": "phone",
    "花": "flower",
    "海报": "poster",
    "标牌": "sign",
    "时钟": "clock",
    "旗子": "flag",
    "小船": "boat",
    "浮标": "duck",
    "鸭子": "duck",
    "皮划艇": "kayak",
    "游泳圈": "float",
    "鸟": "bird",
    "鸟/鸭": "bird",
    "桶/漂浮物": "bucket",
    "气球": "balloon",
    "风筝": "kite",
}


def warn(message: str) -> None:
    print(f"  warn: {message}", file=sys.stderr)


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, list):
                out.extend(as_list(item))
            else:
                text = str(item).strip()
                if text:
                    out.append(text)
        return out
    text = str(value).strip()
    return [text] if text else []


def canonical_value(value: str) -> str:
    return CANONICAL_VALUES.get(value, value)


def canonical_list(value: Any) -> list[str]:
    return [canonical_value(item) for item in as_list(value)]


def first(value: Any) -> str:
    values = as_list(value)
    return values[0] if values else ""


def first_canonical(value: Any) -> str:
    values = canonical_list(value)
    return values[0] if values else ""


def clean_slot_id(value: Any) -> str:
    return first(value).strip().upper().replace(" ", "")


def context_id_for_edit(slot_id: str) -> str:
    prefix = []
    for char in slot_id:
        if char.isalpha():
            prefix.append(char)
        elif prefix:
            break
    return "".join(prefix)


def entry_value(entry: dict[str, Any]) -> Any:
    value = entry.get("value")
    if not isinstance(value, dict):
        return value
    if "choices" in value:
        return value.get("choices")
    if "text" in value:
        return value.get("text")
    if "rectanglelabels" in value:
        return value.get("rectanglelabels")
    return value


def to_xyxy_from_entry(entry: dict[str, Any]) -> list[int] | None:
    import math
    value = entry.get("value") or {}
    if not isinstance(value, dict):
        return None
    try:
        ow = float(entry.get("original_width") or value["original_width"])
        oh = float(entry.get("original_height") or value["original_height"])
        x = float(value["x"])
        y = float(value["y"])
        w = float(value["width"])
        h = float(value["height"])
    except (KeyError, TypeError, ValueError):
        return None
    rotation = float(value.get("rotation", 0))
    px = x / 100.0 * ow
    py = y / 100.0 * oh
    pw = w / 100.0 * ow
    ph = h / 100.0 * oh
    if abs(rotation) < 0.5:
        return [int(round(px)), int(round(py)), int(round(px + pw)), int(round(py + ph))]
    rad = math.radians(rotation)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)
    corners = [(0, 0), (pw, 0), (pw, ph), (0, ph)]
    xs = [px + dx * cos_r - dy * sin_r for dx, dy in corners]
    ys = [py + dx * sin_r + dy * cos_r for dx, dy in corners]
    x1 = max(0, int(min(xs)))
    y1 = max(0, int(min(ys)))
    x2 = min(int(ow), int(max(xs)) + 1)
    y2 = min(int(oh), int(max(ys)) + 1)
    return [x1, y1, x2, y2]


def task_data(task: dict[str, Any]) -> dict[str, Any]:
    data = task.get("data")
    return data if isinstance(data, dict) else task


def image_id_of(task: dict[str, Any]) -> str:
    data = task_data(task)
    if data.get("image_id"):
        return str(data["image_id"])
    qid = data.get("question_id") or task.get("question_id")
    if qid is not None:
        try:
            return f"vstar_{int(qid):04d}"
        except (TypeError, ValueError):
            return f"vstar_{qid}"
    return f"task_{task.get('id', 'unknown')}"


def question_id_of(task: dict[str, Any]) -> str | None:
    data = task_data(task)
    qid = data.get("question_id") or task.get("question_id")
    return str(qid) if qid is not None else None


def category_of(task: dict[str, Any]) -> str | None:
    data = task_data(task)
    category = data.get("category") or task.get("category")
    return str(category) if category is not None else None


def latest_annotation(task: dict[str, Any]) -> dict[str, Any] | None:
    annotations = [
        ann
        for ann in task.get("annotations", [])
        if isinstance(ann, dict) and not ann.get("was_cancelled")
    ]
    if not annotations:
        return None
    return max(annotations, key=lambda ann: str(ann.get("updated_at") or ann.get("created_at") or ""))


def grouped_standard_results(task: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Group standard LS annotation result entries by region id."""
    ann = latest_annotation(task)
    if not ann:
        return {}
    grouped: dict[str, dict[str, Any]] = {}
    for entry in ann.get("result") or []:
        if not isinstance(entry, dict):
            continue
        region_id = entry.get("id")
        from_name = entry.get("from_name")
        if not region_id or not from_name:
            continue
        group = grouped.setdefault(str(region_id), {"fields": {}})
        if from_name == "slot_box":
            labels = as_list(entry_value(entry))
            label = labels[0] if labels else ""
            xyxy = to_xyxy_from_entry(entry)
            group.update({"label": label, "xyxy": xyxy})
        else:
            group["fields"][from_name] = entry_value(entry)
    return grouped


def grouped_json_min_results(task: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Best-effort support for JSON-MIN-like exports.

    Some Label Studio exports flatten per-region fields to task-level keys. The
    current self-hosted export we have seen uses standard ``annotations`` /
    ``result`` entries, but this fallback keeps the parser tolerant.
    """
    regions = task.get("slot_box")
    if not isinstance(regions, list):
        return {}
    grouped: dict[str, dict[str, Any]] = {}
    for i, region in enumerate(regions, start=1):
        if not isinstance(region, dict):
            continue
        region_id = str(region.get("id") or f"r{i}")
        label = first(region.get("slot_box") or region.get("rectanglelabels") or region.get("label"))
        if not label and isinstance(region.get("value"), dict):
            label = first(region["value"].get("rectanglelabels"))
        # JSON-MIN variants usually keep x/y/width/height directly on region.
        value = region.get("value") if isinstance(region.get("value"), dict) else region
        entry = {
            "original_width": region.get("original_width") or value.get("original_width"),
            "original_height": region.get("original_height") or value.get("original_height"),
            "value": value,
        }
        grouped[region_id] = {
            "label": label,
            "xyxy": to_xyxy_from_entry(entry),
            "fields": {},
        }
    return grouped


def grouped_results(task: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return grouped_standard_results(task) or grouped_json_min_results(task)


def checked_values(values: list[str], valid: set[str], field: str, image_id: str, slot_id: str) -> list[str]:
    out: list[str] = []
    for value in values:
        if value not in valid:
            warn(f"unknown {field}={value!r} (image={image_id}, slot={slot_id}); keeping it")
        if value not in out:
            out.append(value)
    return out


def parse_replace_target(
    fields: dict[str, Any],
    index: int,
    image_id: str,
    slot_id: str,
) -> dict[str, Any] | None:
    target_ref = first(fields.get(f"replace_target_{index}_ref")).strip()
    if not target_ref:
        return None
    edit_types = checked_values(
        canonical_list(fields.get(f"replace_target_{index}_edit_types")),
        VALID_REPLACE_EDIT_TYPES,
        f"replace_target_{index}_edit_type",
        image_id,
        slot_id,
    )
    if not edit_types:
        edit_types = ["color_change"]
    return {"target_ref": target_ref, "edit_types": edit_types}


def parse_replace_targets(fields: dict[str, Any], image_id: str, slot_id: str) -> list[dict[str, Any]]:
    return [
        target
        for index in (1, 2, 3)
        if (target := parse_replace_target(fields, index, image_id, slot_id)) is not None
    ]


def build_slots(task: dict[str, Any]) -> list[dict[str, Any]]:
    image_id = image_id_of(task)
    grouped = grouped_results(task)
    contexts: dict[str, dict[str, Any]] = {}
    edits: dict[str, dict[str, Any]] = {}

    for region_id, region in grouped.items():
        label = region.get("label")
        fields = region.get("fields") or {}
        xyxy = region.get("xyxy")
        if label not in VALID_LABELS:
            if label:
                warn(f"unknown region label {label!r} (image={image_id}, region={region_id}); skipping")
            continue
        if xyxy is None:
            warn(f"region missing geometry (image={image_id}, region={region_id}); skipping")
            continue

        if label == "context_region":
            slot_id = clean_slot_id(fields.get("context_slot_id"))
            ref = first(fields.get("context_ref")).strip()
            if not slot_id:
                warn(f"context_region missing slot_id (image={image_id}, region={region_id}); skipping")
                continue
            contexts[slot_id] = {
                "xyxy": xyxy,
                "ref": ref,
            }
            continue

        slot_id = clean_slot_id(fields.get("edit_slot_id"))
        mode = first_canonical(fields.get("edit_mode")).strip()
        if not slot_id:
            warn(f"edit_region missing slot_id (image={image_id}, region={region_id}); skipping")
            continue
        if mode not in VALID_MODES:
            warn(f"edit_region has invalid mode {mode!r} (image={image_id}, slot={slot_id}); skipping")
            continue

        edit: dict[str, Any] = {
            "edit_region": {
                "xyxy": xyxy,
                "mode": mode,
            }
        }

        placements = checked_values(
            canonical_list(fields.get("add_placements")),
            VALID_PLACEMENTS,
            "placement",
            image_id,
            slot_id,
        )
        entity_families = checked_values(
            canonical_list(fields.get("add_entity_families")),
            VALID_ENTITY_FAMILIES,
            "entity_family",
            image_id,
            slot_id,
        )
        # New add format: direct object checkboxes
        add_objects_raw = []
        for field_name in ("add_objects", "add_objects_table", "add_objects_wall", "add_objects_water", "add_objects_air"):
            add_objects_raw.extend(canonical_list(fields.get(field_name)))
        # Free-text custom objects (comma-separated)
        custom_raw = first(fields.get("add_custom_object")).strip()
        if custom_raw:
            for part in custom_raw.split(","):
                part = part.strip()
                if part:
                    add_objects_raw.append(canonical_value(part))
        add_objects = sorted(set(add_objects_raw)) if add_objects_raw else []

        if add_objects:
            edit["add"] = {"objects": add_objects}
        elif placements or entity_families:
            edit["add"] = {
                "placements": placements,
                "entity_families": entity_families,
            }

        targets = parse_replace_targets(fields, image_id, slot_id)
        if targets:
            edit["replace"] = {"targets": targets}

        if slot_id in edits:
            warn(f"duplicate edit slot_id={slot_id!r} (image={image_id}); keeping the last one")
        edits[slot_id] = edit

    slots: list[dict[str, Any]] = []
    for slot_id, edit in edits.items():
        context_key = slot_id if slot_id in contexts else context_id_for_edit(slot_id)
        context = contexts.get(context_key)
        if context is None:
            warn(f"edit slot has no paired context_region (image={image_id}, slot={slot_id}, expected_context={context_key or slot_id}); skipping")
            continue
        mode = edit["edit_region"]["mode"]
        has_add = bool(edit.get("add", {}).get("objects")) or (bool(edit.get("add", {}).get("placements")) and bool(edit.get("add", {}).get("entity_families")))
        replace = edit.get("replace", {})
        targets = replace.get("targets") if isinstance(replace.get("targets"), list) else []
        has_replace_targets = any(target.get("target_ref") and target.get("edit_types") for target in targets if isinstance(target, dict))
        has_replace_target = bool(replace.get("target_ref")) or bool(replace.get("target_family"))
        has_replace = has_replace_targets or (has_replace_target and bool(replace.get("edit_types")))
        if mode == "add" and not has_add:
            warn(f"add slot missing add concepts (image={image_id}, slot={slot_id}); skipping")
            continue
        if mode == "replace" and not has_replace:
            warn(f"replace slot missing replace concepts (image={image_id}, slot={slot_id}); skipping")
            continue
        if mode == "either" and not (has_add or has_replace):
            warn(f"either slot has no usable add or replace concepts (image={image_id}, slot={slot_id}); skipping")
            continue
        slot = {
            "slot_id": slot_id,
            "context_region": context,
            **edit,
        }
        slots.append(slot)
    return slots


def parse(export: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in export:
        if not isinstance(task, dict):
            continue
        image_id = image_id_of(task)
        slots = build_slots(task)
        if not slots:
            warn(f"image {image_id} has 0 valid slots; skipping")
            continue
        row: dict[str, Any] = {
            "image_id": image_id,
            "slots": slots,
        }
        qid = question_id_of(task)
        category = category_of(task)
        if qid is not None:
            row["question_id"] = qid
        if category is not None:
            row["category"] = category
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", type=Path, required=True, help="Label Studio JSON/JSON-MIN export")
    parser.add_argument("--out", type=Path, required=True, help="Output JSONL path")
    args = parser.parse_args()

    with args.export.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise SystemExit(f"Expected export list, got {type(data).__name__}")

    rows = parse(data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} images to {args.out}")


if __name__ == "__main__":
    main()
