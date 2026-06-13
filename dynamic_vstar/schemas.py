from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


Box = tuple[int, int, int, int]


@dataclass(frozen=True)
class ContextRegion:
    xyxy: Box
    ref: str


@dataclass(frozen=True)
class EditRegion:
    xyxy: Box
    mode: str


@dataclass(frozen=True)
class Slot:
    slot_id: str
    context_region: ContextRegion
    edit_region: EditRegion
    add: dict[str, Any] | None = None
    replace: dict[str, Any] | None = None


@dataclass(frozen=True)
class AnnotationRow:
    image_id: str
    question_id: str | None
    category: str | None
    slots: list[Slot]
    source: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SampledEdit:
    slot_id: str
    operation: str
    placement: str | None
    entity_family: str | None
    target_family: str | None
    edit_type: str
    object_name: str
    target_name: str
    answer_attribute: str
    answer: str
    attributes: dict[str, str]


@dataclass(frozen=True)
class SampleSpec:
    image_id: str
    question_id: str | None
    run_id: str
    seed: int
    slot_count: int
    edits: list[SampledEdit]
    probability_trace: dict[str, Any]


@dataclass(frozen=True)
class PlannedEdit:
    slot_id: str
    mode: str
    target_phrase: str
    edit_instruction: str
    image_prompt: str
    question_type: str
    question: str
    answer: str
    distractors: list[str]
    options: dict[str, str]
    correct_label: str


@dataclass(frozen=True)
class PlanSpec:
    image_id: str
    question_id: str | None
    source_question: str
    source_category: str | None
    edits: list[PlannedEdit]
    question_type: str
    question: str
    answer: str
    options: dict[str, str]
    correct_label: str
    planner_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CropSpec:
    slot_id: str
    context_xyxy: Box
    crop_xyxy: Box
    edit_xyxy: Box
    edit_xyxy_in_crop: Box
    output_size: tuple[int, int]


@dataclass(frozen=True)
class CanvasSpec:
    size: tuple[int, int]
    source_size: tuple[int, int]
    content_xyxy: Box
    edit_xyxy_in_canvas: Box
    scale: float


@dataclass(frozen=True)
class GenerationResult:
    slot_id: str
    context_crop_path: str
    clean_canvas_path: str
    guide_crop_path: str
    generated_canvas_path: str
    restored_context_path: str
    api_metadata: dict[str, Any]
    crop: CropSpec
    canvas: CanvasSpec


@dataclass(frozen=True)
class DynamicItem:
    image_id: str
    question_id: str | None
    run_id: str
    source_image_path: str
    composite_image_path: str
    overview_image_path: str
    sample: SampleSpec
    plan: PlanSpec
    generations: list[GenerationResult]
    qc: dict[str, Any]


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    return value


def box_from_list(value: Any, field_name: str) -> Box:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError(f"{field_name} must be a 4-number xyxy list")
    x1, y1, x2, y2 = (int(round(float(v))) for v in value)
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"{field_name} has invalid extent: {value!r}")
    return (x1, y1, x2, y2)


def annotation_row_from_dict(row: dict[str, Any]) -> AnnotationRow:
    slots: list[Slot] = []
    for raw in row.get("slots") or []:
        context = raw.get("context_region") or {}
        edit = raw.get("edit_region") or {}
        slots.append(
            Slot(
                slot_id=str(raw["slot_id"]),
                context_region=ContextRegion(
                    xyxy=box_from_list(context.get("xyxy"), "context_region.xyxy"),
                    ref=str(context.get("ref") or "").strip(),
                ),
                edit_region=EditRegion(
                    xyxy=box_from_list(edit.get("xyxy"), "edit_region.xyxy"),
                    mode=str(edit.get("mode") or "").strip(),
                ),
                add=raw.get("add") if isinstance(raw.get("add"), dict) else None,
                replace=raw.get("replace") if isinstance(raw.get("replace"), dict) else None,
            )
        )
    return AnnotationRow(
        image_id=str(row["image_id"]),
        question_id=str(row["question_id"]) if row.get("question_id") is not None else None,
        category=str(row["category"]) if row.get("category") is not None else None,
        slots=slots,
        source=row,
    )
