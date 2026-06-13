from __future__ import annotations

import base64
import io
import json
import os
import random
import re
from dataclasses import replace
from typing import Any, Protocol

from PIL import Image

from .concept_library import COLORS, MATERIALS, PATTERNS, distractors_for, infer_question_attribute
from .env import load_dotenv
from .geometry import crop_image, crop_spec_for_slot, draw_guide_crop
from .sampling import stable_seed
from .schemas import (
    AnnotationRow,
    PlanSpec,
    PlannedEdit,
    SampleSpec,
    SampledEdit,
    Slot,
    to_jsonable,
)


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_SITE_URL = "https://github.com/dynamic-vstar"
OPENROUTER_APP_TITLE = "dynamic-vstar-planner"

ATTRIBUTE_QUESTION_WORDS = {
    "color": "What color is",
    "material": "What material is",
    "pattern": "What pattern is on",
}
ANSWERED_QUESTION_TYPES = {"color", "material", "pattern"}
POSITION_QUESTION_TYPES = {"position_left_right"}
VALID_QUESTION_TYPES = ANSWERED_QUESTION_TYPES | POSITION_QUESTION_TYPES
JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.I | re.S)
OMIT_ADD_MATERIALS = {"food"}
PLACEMENT_HINTS = {
    "ground_surface": "place it on the visible ground, floor, or path surface",
    "countertop_or_table": "place it on the visible tabletop or counter surface; if only a thin support edge is visible, use that edge instead of the wall or background",
    "shelf_or_display": "place it on the visible shelf or display surface",
    "water_surface": "place it on the visible water surface",
    "vertical_surface": "attach it to the visible vertical surface",
    "vehicle_surface": "attach it to the visible vehicle surface",
    "body_or_clothing_surface": "attach it to the visible body or clothing surface",
    "container_inside": "place it inside the visible container opening",
    "hanging_or_overhead_area": "place it in the visible upper area with a natural pose (flying for birds, hanging for objects, draped for fabric)",
}


class Planner(Protocol):
    def build(self, row: AnnotationRow, sample: SampleSpec, source_image: Image.Image | None = None) -> PlanSpec:
        ...


class PlanValidationError(ValueError):
    pass


def find_slot(row: AnnotationRow, slot_id: str) -> Slot:
    for slot in row.slots:
        if slot.slot_id == slot_id:
            return slot
    raise KeyError(f"slot {slot_id!r} not found")


def source_question(row: AnnotationRow) -> str:
    for key in ("relabel_question", "original_question", "question", "source_question"):
        if row.source.get(key):
            return str(row.source[key])
    return ""


def source_options(row: AnnotationRow) -> dict[str, str]:
    raw = row.source.get("options")
    if not isinstance(raw, dict):
        return {}
    return {str(key): str(value) for key, value in raw.items()}


def source_answer(row: AnnotationRow) -> str | None:
    for key in ("answer_text", "answer", "source_answer"):
        if row.source.get(key):
            return str(row.source[key])
    label = row.source.get("label")
    options = source_options(row)
    if label is not None and str(label) in options:
        return options[str(label)]
    return None


def option_map(answer: str, distractors: list[str], rng: random.Random) -> tuple[dict[str, str], str]:
    values = [answer] + [d for d in distractors if d != answer]
    values = values[:4]
    rng.shuffle(values)
    letters = ["A", "B", "C", "D"][: len(values)]
    options = dict(zip(letters, values))
    correct = next(letter for letter, value in options.items() if value == answer)
    return options, correct


def context_anchor(slot: Slot) -> str:
    """Extract a short spatial anchor from context_ref for use in target_phrase."""
    ref = (slot.context_region.ref or "").strip()
    if not ref:
        return ""
    return f"near {ref}"


def target_phrase(sampled: SampledEdit, slot: Slot) -> str:
    anchor = context_anchor(slot)
    if sampled.operation == "add":
        attrs = sampled.attributes
        visible_descriptors = []
        if sampled.answer_attribute != "pattern" and attrs.get("pattern") != "plain":
            visible_descriptors.append(attrs.get("pattern", ""))
        if sampled.answer_attribute != "color":
            visible_descriptors.append(attrs.get("color", ""))
        if sampled.answer_attribute != "material":
            material = attrs.get("material", "")
            if material not in OMIT_ADD_MATERIALS:
                visible_descriptors.append(material)
        descriptor = " ".join(
            part
            for part in [*visible_descriptors, sampled.object_name]
            if part
        )
        if anchor:
            return f"the {descriptor} {anchor}"
        return f"the {descriptor}"
    base = sampled.target_name
    if anchor:
        return f"the {base} {anchor}" if not base.startswith("the ") else f"{base} {anchor}"
    return f"the {base}" if not base.startswith("the ") else base


def edit_instruction(sampled: SampledEdit, slot: Slot) -> str:
    attrs = sampled.attributes
    context = slot.context_region.ref
    if sampled.operation == "add":
        descriptor = add_descriptor(sampled)
        return (
            f"Add a {descriptor} inside the edit region. "
            f"Context: {context}. It should be visible but not dominant."
        )
    target = sampled.target_name
    if sampled.answer_attribute == "material":
        change = f"Change the visible material of {target} to {sampled.answer}."
    elif sampled.answer_attribute == "pattern":
        change = f"Add a {sampled.answer} pattern to {target}."
    else:
        change = f"Change the visible color of {target} to {sampled.answer}."
    return (
        f"{change} Edit only inside the edit region, preserving identity and surroundings. "
        f"Context: {context}."
    )


def image_prompt(sampled: SampledEdit, slot: Slot) -> str:
    return (
        "Use the input image as a local context crop from a real photograph. "
        "Edit only the specified small edit region and preserve everything else. "
        f"{edit_instruction(sampled, slot)} "
        "Match the original lighting, perspective, texture, blur, and camera noise. "
        "Do not add guide boxes, labels, text overlays, borders, logos, or extra objects."
    )


def question_for(sampled: SampledEdit, phrase: str, preferred: str | None) -> tuple[str, str]:
    phrase = natural_phrase(phrase)
    attribute = sampled.answer_attribute
    if preferred in ANSWERED_QUESTION_TYPES:
        attribute = preferred if preferred == sampled.answer_attribute else sampled.answer_attribute
    sub_item = sampled.attributes.get("sub_item")
    if sub_item:
        if attribute == "material":
            return "material", f"What is the {sub_item} of {phrase} made of?"
        if attribute == "pattern":
            return "pattern", f"What pattern does the {sub_item} of {phrase} have?"
        return "color", f"What color is the {sub_item} of {phrase}?"
    if attribute == "material":
        return "material", f"What material is {phrase}?"
    if attribute == "pattern":
        return "pattern", f"What pattern is on {phrase}?"
    return "color", f"What color is {phrase}?"


def center_xy(slot: Slot) -> tuple[float, float]:
    x1, y1, x2, y2 = slot.edit_region.xyxy
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def position_question(row: AnnotationRow, planned: list[PlannedEdit]) -> tuple[str, str, dict[str, str], str] | None:
    if len(planned) < 2:
        return None
    a = planned[0]
    b = planned[1]
    phrase_a = natural_phrase(a.target_phrase)
    phrase_b = natural_phrase(b.target_phrase)
    slot_a = find_slot(row, a.slot_id)
    slot_b = find_slot(row, b.slot_id)
    ax, ay = center_xy(slot_a)
    bx, by = center_xy(slot_b)
    dx = ax - bx
    if abs(dx) >= 20:
        answer = "left" if dx < 0 else "right"
        return (
            "position_left_right",
            f"Is {phrase_a} to the left or right of {phrase_b}?",
            {"A": "left", "B": "right"},
            "A" if answer == "left" else "B",
        )
    return None


def build_rule_based_plan(
    row: AnnotationRow,
    sample: SampleSpec,
    use_vaw: bool = False,
    use_mask: bool = False,
) -> PlanSpec:
    from .rule_planner import (
        parse_color, build_attr_question, build_position_question,
        build_edit_prompt as rule_edit_prompt, build_add_edit_prompt,
        sample_new_color,
    )

    src_question = source_question(row)
    edits: list[PlannedEdit] = []
    used_colors: set[str] = set()

    for sampled in sample.edits:
        slot = find_slot(row, sampled.slot_id)
        rng = random.Random(stable_seed(sample.image_id, sample.run_id, sampled.slot_id, "plan"))
        target_ref = sampled.target_name
        old_color, obj_phrase = parse_color(target_ref)
        new_color = sampled.answer
        if new_color in used_colors or new_color == old_color:
            new_color = sample_new_color(old_color, rng, also_exclude=used_colors, target_ref=target_ref, use_vaw=use_vaw)
        used_colors.add(new_color)

        if sampled.operation == "add":
            target_ref = f"{new_color} {sampled.object_name}"
            qa = build_attr_question(target_ref, new_color, rng)
            ep = build_add_edit_prompt(sampled.object_name, new_color)
        else:
            qa = build_attr_question(target_ref, new_color, rng)
            ep = rule_edit_prompt(target_ref, new_color)

        edits.append(
            PlannedEdit(
                slot_id=sampled.slot_id,
                mode=sampled.operation,
                target_phrase=qa["question"].replace("What color is ", "").rstrip("?"),
                edit_instruction=ep,
                image_prompt=ep,
                question_type=qa["question_type"],
                question=qa["question"],
                answer=qa["answer"],
                distractors=qa["distractors"],
                options=qa["options"],
                correct_label=qa["correct_label"],
            )
        )

    # Position question if 2+ slots
    if len(edits) >= 2:
        slot_a = find_slot(row, edits[0].slot_id)
        slot_b = find_slot(row, edits[1].slot_id)
        ax = sum(slot_a.edit_region.xyxy[::2]) / 2
        ay = sum(slot_a.edit_region.xyxy[1::2]) / 2
        bx = sum(slot_b.edit_region.xyxy[::2]) / 2
        by = sum(slot_b.edit_region.xyxy[1::2]) / 2
        if abs(ax - bx) >= 20 or abs(ay - by) >= 20:
            ref_a = sample.edits[0].target_name
            ref_b = sample.edits[1].target_name
            pq = build_position_question(
                ref_a, edits[0].answer,
                ref_b, edits[1].answer,
                ax, ay, bx, by,
            )
            return PlanSpec(
                image_id=row.image_id,
                question_id=row.question_id,
                source_question=src_question,
                source_category=row.category,
                edits=edits,
                question_type=pq["question_type"],
                question=pq["question"],
                answer=pq["answer"],
                options=pq["options"],
                correct_label=pq["correct_label"],
                planner_metadata={"backend": "rule", "use_vaw": use_vaw, "use_mask": use_mask},
            )

    first = edits[0]
    return PlanSpec(
        image_id=row.image_id,
        question_id=row.question_id,
        source_question=src_question,
        source_category=row.category,
        edits=edits,
        question_type=first.question_type,
        question=first.question,
        answer=first.answer,
        options=first.options,
        correct_label=first.correct_label,
        planner_metadata={"backend": "rule", "use_vaw": use_vaw, "use_mask": use_mask},
    )


class RuleBasedPlanner:
    backend = "rule"

    def __init__(self, use_vaw: bool = False, use_mask: bool = False):
        self.use_vaw = use_vaw
        self.use_mask = use_mask

    def build(self, row: AnnotationRow, sample: SampleSpec, source_image: Image.Image | None = None) -> PlanSpec:
        return build_rule_based_plan(row, sample, use_vaw=self.use_vaw, use_mask=self.use_mask)


def clean_text(value: Any, max_chars: int = 1200) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text[:max_chars].strip()


def natural_phrase(phrase: str) -> str:
    text = clean_text(phrase, max_chars=240)
    if not text:
        return text
    if re.match(r"^(the|a|an|this|that|these|those)\b", text, re.I):
        return text
    return f"the {text}"


def contains_answer(text: str, answer: str) -> bool:
    if not text or not answer:
        return False
    return re.search(rf"\b{re.escape(answer.lower())}\b", text.lower()) is not None


def extract_json_object(content: str) -> dict[str, Any]:
    text = content.strip()
    fence = JSON_FENCE_RE.search(text)
    if fence:
        text = fence.group(1).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise PlanValidationError("planner response must be a JSON object")
    return parsed


PLANNER_SYSTEM_PROMPT = """You are creating visual quiz questions for a VQA benchmark. Return JSON only."""


def sampled_payload(sampled: SampledEdit, slot: Slot) -> dict[str, Any]:
    payload = {
        "slot_id": sampled.slot_id,
        "context": slot.context_region.ref,
        "operation": sampled.operation,
        "edit_type": sampled.edit_type,
        "answer_attribute": sampled.answer_attribute,
        "answer": sampled.answer,
        "required_edit": edit_request(sampled),
    }
    if sampled.operation == "replace":
        payload["target"] = sampled.target_name
    else:
        payload["object"] = sampled.object_name
        payload["placement"] = sampled.placement
        payload["placement_hint"] = placement_hint(sampled)
    return payload


def planner_input_payload(row: AnnotationRow, sample: SampleSpec, base_plan: PlanSpec | None = None) -> dict[str, Any]:
    return {
        "source_question": source_question(row),
        "preferred_question_attribute": infer_question_attribute(source_question(row)),
        "slots": [
            sampled_payload(sampled, find_slot(row, sampled.slot_id))
            for sampled in sample.edits
        ],
        "planner_outputs": [
            "edit_prompt",
            "target_phrase",
        ],
        "ground_truth_note": "The code builds question, answer, options, and correct_label from sampled metadata and box geometry.",
    }


def add_descriptor(sampled: SampledEdit) -> str:
    attrs = sampled.attributes
    sub_item = attrs.get("sub_item")
    if sub_item:
        item_parts = []
        pattern = attrs.get("pattern", "")
        if pattern and pattern != "plain":
            item_parts.append(pattern)
        item_parts.append(attrs.get("color", ""))
        material = attrs.get("material", "")
        if material not in OMIT_ADD_MATERIALS:
            item_parts.append(material)
        item_parts.append(sub_item)
        item_desc = " ".join(p for p in item_parts if p)
        return f"{sampled.object_name} wearing a {item_desc}"

    material = attrs.get("material", "")
    if material in OMIT_ADD_MATERIALS or sampled.entity_family == "food_item":
        material = ""
    object_name = sampled.object_name
    size = "small"
    size_match = re.match(r"^(small|tiny)\s+(.+)$", object_name, re.I)
    if size_match:
        size = size_match.group(1).lower()
        object_name = size_match.group(2)
    name_lower = object_name.lower()
    color = attrs.get("color", "")
    if color and color.lower() in name_lower:
        color = ""
    if material and material.lower() in name_lower:
        material = ""
    parts = [
        size,
        attrs.get("pattern") if attrs.get("pattern") and attrs.get("pattern") != "plain" else "",
        color,
        material,
        object_name,
    ]
    return " ".join(part for part in parts if part)


def edit_request(sampled: SampledEdit) -> str:
    if sampled.operation == "add":
        descriptor = add_descriptor(sampled)
        article = "an" if descriptor[:1].lower() in {"a", "e", "i", "o", "u"} else "a"
        return f"add {article} {descriptor}"
    target = sampled.target_name
    if sampled.edit_type == "color_change":
        return f"change only {target}'s color to {sampled.answer}; keep its material, pattern, shape, and position unchanged"
    if sampled.edit_type == "material_change":
        return f"change only {target}'s material to {sampled.answer}; keep its color, pattern, shape, and position unchanged"
    if sampled.edit_type == "pattern_change":
        return f"add a {sampled.answer} pattern to {target}; keep its color, material, shape, and position unchanged"
    return f"change {target}'s {sampled.answer_attribute} to {sampled.answer}"


def placement_hint(sampled: SampledEdit) -> str:
    if sampled.operation != "add" or not sampled.placement:
        return ""
    return PLACEMENT_HINTS.get(sampled.placement, sampled.placement.replace("_", " "))


QUESTION_TEMPLATES = {
    "color": "What color is {phrase}?",
    "material": "What is {phrase} made of?",
    "pattern": "What pattern does {phrase} have?",
}


def question_template_display(sampled: SampledEdit) -> str:
    sub_item = sampled.attributes.get("sub_item")
    if sub_item:
        templates = {
            "color": f"What color is the {sub_item} of {{phrase}}?",
            "material": f"What is the {sub_item} of {{phrase}} made of?",
            "pattern": f"What pattern does the {sub_item} of {{phrase}} have?",
        }
        template = templates.get(sampled.answer_attribute, f"What color is the {sub_item} of {{phrase}}?")
    else:
        template = QUESTION_TEMPLATES.get(sampled.answer_attribute, "What color is {phrase}?")
    return template.replace("{phrase}", "___")


def slot_planner_text(row: AnnotationRow, sampled: SampledEdit, slot: Slot) -> str:
    q_display = question_template_display(sampled)
    hint = placement_hint(sampled)
    lines = [
        "The attached image is a local crop from a high-res photo. The orange box marks the edit area.",
        "",
        "## Task",
        f"Scene context: {slot.context_region.ref}",
        f"Required edit: {edit_request(sampled)}",
    ]
    if hint:
        lines.append(f"Placement: {hint}.")
    lines.extend([
        "",
        "## Quiz question that will be shown with the FULL edited image",
        f"Template: \"{q_display}\"",
        f"Answer: \"{sampled.answer}\"",
        "",
        "## Your outputs",
        "1. edit_prompt — instruction for the image model to execute the edit on this crop.",
        f"2. target_phrase — fills the blank in \"{q_display}\". Requirements:",
        f"   - MUST incorporate the scene context above to anchor the target (e.g. 'near the two men talking', 'on the red box', 'next to the lifebuoy')",
        f"   - Must NOT reveal the answer",
        "",
        '{"edit_prompt": "...", "target_phrase": "..."}',
    ])
    return "\n".join(lines)


def position_planner_text(row: AnnotationRow, items: list[tuple[SampledEdit, Slot]]) -> str:
    lines = [
        "The attached images are local crops from the same high-res photo. Each orange box marks one edit area.",
        "",
        "## Task",
    ]
    for index, (sampled, slot) in enumerate(items, start=1):
        lines.append(f"Slot {sampled.slot_id} (image {index}): context={slot.context_region.ref}")
        lines.append(f"  Edit: {edit_request(sampled)}")
        hint = placement_hint(sampled)
        if hint:
            lines.append(f"  Placement: {hint}.")
    lines.extend([
        "",
        "## Quiz question that will be shown with the FULL edited image",
        "Template: \"Is _A_ to the left or right of _B_?\"",
        "The left/right answer is computed by code from coordinates — do not decide it.",
        "",
        "## Your outputs",
        "For each slot:",
        "1. edit_prompt — instruction for the image model.",
        "2. target_phrase — fills one blank. Include visible attributes (color, material) since the question asks about position. Use scene context as anchor.",
        "",
        '{"edits": [{"slot_id": "...", "edit_prompt": "...", "target_phrase": "..."}]}',
    ])
    return "\n".join(lines)


def contains_attribute_term(text: str, term: str) -> bool:
    return re.search(rf"(?<![A-Za-z]){re.escape(term.lower())}(?![A-Za-z])", text.lower()) is not None


def has_unsampled_attribute_conflict(text: str, sampled: SampledEdit) -> bool:
    if sampled.operation != "replace":
        return False
    target_text = sampled.target_name.lower()
    answer = sampled.answer.lower()
    pools: dict[str, list[str]] = {
        "color": COLORS,
        "material": MATERIALS,
        "pattern": PATTERNS,
    }
    for attribute, terms in pools.items():
        for term in terms:
            normalized = term.lower()
            if normalized == answer or contains_attribute_term(target_text, normalized):
                continue
            if attribute == sampled.answer_attribute:
                continue
            if contains_attribute_term(text, normalized):
                return True
    if sampled.answer_attribute in pools:
        for term in pools[sampled.answer_attribute]:
            normalized = term.lower()
            if normalized == answer or contains_attribute_term(target_text, normalized):
                continue
            if contains_attribute_term(text, normalized):
                return True
    return False


def image_data_url(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def guide_crop_for_slot(source_image: Image.Image, slot: Slot) -> Image.Image:
    crop_spec = crop_spec_for_slot(slot, source_image.size)
    context_crop = crop_image(source_image, crop_spec.crop_xyxy)
    return draw_guide_crop(context_crop, crop_spec)


def image_content(image: Image.Image) -> dict[str, Any]:
    return {
        "type": "image_url",
        "image_url": {
            "url": image_data_url(image),
            "detail": "high",
        },
    }


def text_content(text: str) -> dict[str, str]:
    return {"type": "text", "text": text}


def slot_messages(row: AnnotationRow, sampled: SampledEdit, slot: Slot, source_image: Image.Image | None) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [text_content(slot_planner_text(row, sampled, slot))]
    if source_image is not None:
        content.append(image_content(guide_crop_for_slot(source_image, slot)))
    return [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]


def position_messages(row: AnnotationRow, items: list[tuple[SampledEdit, Slot]], source_image: Image.Image | None) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [text_content(position_planner_text(row, items))]
    if source_image is not None:
        for _, slot in items:
            content.append(image_content(guide_crop_for_slot(source_image, slot)))
    return [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]


def target_leaks_answer_dimension(target: str, sampled: SampledEdit) -> str | None:
    """Check if target_phrase contains ANY value from the answer's attribute dimension."""
    pools: dict[str, list[str]] = {
        "color": COLORS,
        "material": MATERIALS,
        "pattern": PATTERNS,
    }
    terms = pools.get(sampled.answer_attribute, [])
    for term in terms:
        if contains_attribute_term(target, term):
            return term
    return None


def validate_slot_json(raw: dict[str, Any], sampled: SampledEdit, allow_answer_in_target: bool = False) -> list[str]:
    errors: list[str] = []
    edit_prompt = clean_text(raw.get("edit_prompt"), max_chars=1200)
    target = clean_text(raw.get("target_phrase"), max_chars=240)
    if not edit_prompt:
        errors.append("missing non-empty edit_prompt")
    if not target:
        errors.append("missing non-empty target_phrase")
    if not allow_answer_in_target:
        leaked = target_leaks_answer_dimension(target, sampled)
        if leaked:
            errors.append(
                f"target_phrase contains {leaked!r} from the answer dimension "
                f"({sampled.answer_attribute}); it must not reveal or contradict the answer"
            )
    if re.search(r"\borange box\b|\bbox\b", target, re.I):
        errors.append("target_phrase must not mention the orange box")
    return errors


def validate_position_json(raw: dict[str, Any], sample: SampleSpec) -> list[str]:
    raw_edits = raw.get("edits")
    if not isinstance(raw_edits, list):
        return ["missing edits list"]
    sampled_by_slot = {edit.slot_id: edit for edit in sample.edits}
    seen: set[str] = set()
    errors: list[str] = []
    for item in raw_edits:
        if not isinstance(item, dict):
            errors.append("each edits item must be an object")
            continue
        slot_id = str(item.get("slot_id") or "")
        if slot_id not in sampled_by_slot:
            errors.append(f"unexpected slot_id {slot_id!r}")
            continue
        seen.add(slot_id)
        errors.extend(f"{slot_id}: {error}" for error in validate_slot_json(item, sampled_by_slot[slot_id], allow_answer_in_target=True))
    missing = set(sampled_by_slot) - seen
    if missing:
        errors.append(f"missing slot outputs: {sorted(missing)}")
    return errors


def repair_messages(messages: list[dict[str, Any]], content: str, errors: list[str]) -> list[dict[str, Any]]:
    return [
        *messages,
        {"role": "assistant", "content": content},
        {
            "role": "user",
            "content": "The JSON is invalid for these reasons:\n- "
            + "\n- ".join(errors)
            + "\nReturn corrected JSON only.",
        },
    ]


def planned_edit_from_slot_output(base_edit: PlannedEdit, sampled: SampledEdit, raw: dict[str, Any]) -> PlannedEdit:
    target = clean_text(raw.get("target_phrase"), max_chars=240)
    edit_prompt = clean_text(raw.get("edit_prompt"), max_chars=1200)
    question_type, question = question_for(sampled, target, sampled.answer_attribute)
    return replace(
        base_edit,
        target_phrase=target,
        edit_instruction=edit_prompt,
        image_prompt=edit_prompt,
        question_type=question_type,
        question=question,
    )


def finalize_plan_from_edits(row: AnnotationRow, sample: SampleSpec, base_plan: PlanSpec, edits: list[PlannedEdit]) -> PlanSpec:
    preferred = infer_question_attribute(source_question(row))
    item_question = position_question(row, edits) if preferred == "position" and len(edits) >= 2 else None
    if item_question is None:
        first = edits[0]
        return replace(
            base_plan,
            edits=edits,
            question_type=first.question_type,
            question=first.question,
            answer=first.answer,
            options=first.options,
            correct_label=first.correct_label,
        )
    question_type, question, options, correct_label = item_question
    return replace(
        base_plan,
        edits=edits,
        question_type=question_type,
        question=question,
        answer=options[correct_label],
        options=options,
        correct_label=correct_label,
    )


def get_field(value: Any, field: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(field, default)
    return getattr(value, field, default)


def has_choices(value: Any) -> bool:
    choices = get_field(value, "choices")
    return isinstance(choices, list) and bool(choices)


def content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            text = get_field(part, "text") or get_field(part, "content")
            if text:
                parts.append(str(text))
        return "\n".join(parts)
    return str(content or "")


def parse_possible_json(value: str) -> Any:
    text = value.strip()
    if not text:
        return value
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return value


def unwrap_chat_response(response: Any) -> Any:
    if has_choices(response):
        return response
    if isinstance(response, str):
        parsed = parse_possible_json(response)
        if parsed is not response:
            return unwrap_chat_response(parsed)
        return response
    for attr in ("data", "response", "body", "payload"):
        nested = get_field(response, attr)
        if nested is not None and nested is not response:
            unwrapped = unwrap_chat_response(nested)
            if has_choices(unwrapped):
                return unwrapped
    json_method = getattr(response, "json", None)
    if callable(json_method):
        try:
            unwrapped = unwrap_chat_response(json_method())
            if has_choices(unwrapped):
                return unwrapped
        except Exception:
            pass
    if hasattr(response, "__enter__"):
        last_event: Any = None
        with response as event_stream:
            for event in event_stream:
                unwrapped = unwrap_chat_response(event)
                if has_choices(unwrapped):
                    return unwrapped
                last_event = unwrapped
        if last_event is not None:
            return last_event
    return response


def response_content(response: Any) -> str:
    normalized = unwrap_chat_response(response)
    choices = get_field(normalized, "choices", [])
    if not choices:
        return ""
    choice = choices[0]
    message = get_field(choice, "message", {})
    return content_to_text(get_field(message, "content", ""))


def response_metadata(response: Any) -> dict[str, Any]:
    normalized = unwrap_chat_response(response)
    if isinstance(normalized, dict):
        return {
            "id": normalized.get("id"),
            "model": normalized.get("model"),
            "provider": normalized.get("provider"),
            "usage": normalized.get("usage"),
        }
    metadata: dict[str, Any] = {}
    for field in ("id", "model", "provider"):
        value = getattr(normalized, field, None)
        if value is not None:
            metadata[field] = value
    usage = getattr(normalized, "usage", None)
    if usage is not None:
        if hasattr(usage, "model_dump"):
            metadata["usage"] = usage.model_dump()
        elif isinstance(usage, dict):
            metadata["usage"] = usage
        else:
            metadata["usage"] = str(usage)
    return metadata


class OpenRouterPlanner:
    backend = "openrouter"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1800,
        timeout: float = 60.0,
        reasoning_effort: str | None = None,
        exclude_reasoning: bool = True,
        max_retries: int = 1,
        fallback_to_rule: bool = False,
        client: Any | None = None,
    ) -> None:
        load_dotenv()
        self.model = model or os.environ.get("DYNAMIC_VSTAR_PLANNER_MODEL")
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = base_url or os.environ.get("OPENROUTER_BASE_URL") or OPENROUTER_BASE_URL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.reasoning_effort = reasoning_effort
        self.exclude_reasoning = exclude_reasoning
        self.max_retries = max_retries
        self.fallback_to_rule = fallback_to_rule
        self._client = client
        self.last_error: str | None = None
        if not self.model:
            raise RuntimeError("DYNAMIC_VSTAR_PLANNER_MODEL or --planner-model is required for OpenRouter planner")
        if self._client is None and not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")

    def client(self) -> Any:
        if self._client is None:
            try:
                from openrouter import OpenRouter
            except ImportError as exc:
                try:
                    from openai import OpenAI
                except ImportError:
                    raise RuntimeError("Install the official OpenRouter Python SDK to use planner: pip install openrouter") from exc
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout,
                    default_headers={
                        "HTTP-Referer": OPENROUTER_SITE_URL,
                        "X-Title": OPENROUTER_APP_TITLE,
                    },
                )
                return self._client
            try:
                self._client = OpenRouter(
                    api_key=self.api_key or "",
                    http_referer=OPENROUTER_SITE_URL,
                    x_open_router_title=OPENROUTER_APP_TITLE,
                    timeout_ms=round(self.timeout * 1000),
                )
            except TypeError:
                self._client = OpenRouter(api_key=self.api_key or "")
        return self._client

    def send_chat_completion(self, messages: list[dict[str, Any]]) -> Any:
        client = self.client()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        reasoning: dict[str, Any] = {}
        if self.reasoning_effort:
            reasoning["effort"] = self.reasoning_effort
        if self.exclude_reasoning:
            reasoning["exclude"] = True
        if reasoning:
            kwargs["reasoning"] = reasoning
        if hasattr(client.chat, "send"):
            return client.chat.send(**kwargs)
        kwargs.pop("stream", None)
        return client.chat.completions.create(
            **kwargs,
        )

    def call_json_with_retries(
        self,
        messages: list[dict[str, Any]],
        validate: Any,
    ) -> tuple[dict[str, Any], Any, int]:
        active_messages = messages
        last_errors: list[str] = []
        last_content = ""
        last_response: Any = None
        for attempt in range(self.max_retries + 1):
            raw_response = self.send_chat_completion(active_messages)
            chat_response = unwrap_chat_response(raw_response)
            last_response = chat_response
            last_content = response_content(chat_response)
            try:
                raw_json = extract_json_object(last_content)
            except Exception as exc:
                last_errors = [f"response is not valid JSON: {exc}"]
            else:
                last_errors = validate(raw_json)
                if not last_errors:
                    return raw_json, chat_response, attempt
            active_messages = repair_messages(messages, last_content, last_errors)
        raise PlanValidationError("; ".join(last_errors) or "planner response failed validation")

    def build_attribute_plan(
        self,
        row: AnnotationRow,
        sample: SampleSpec,
        base_plan: PlanSpec,
        source_image: Image.Image | None,
    ) -> tuple[PlanSpec, list[dict[str, Any]], list[dict[str, Any]], int]:
        base_by_slot = {edit.slot_id: edit for edit in base_plan.edits}
        sampled_by_slot = {edit.slot_id: edit for edit in sample.edits}
        edits: list[PlannedEdit] = []
        responses: list[dict[str, Any]] = []
        attempts = 0
        for sampled in sample.edits:
            slot = find_slot(row, sampled.slot_id)
            messages = slot_messages(row, sampled, slot, source_image)
            raw, chat_response, attempt = self.call_json_with_retries(
                messages,
                lambda value, sampled=sampled: validate_slot_json(value, sampled),
            )
            attempts += attempt
            responses.append(
                {
                    "slot_id": sampled.slot_id,
                    "attempts": attempt + 1,
                    "raw": raw,
                    "response": to_jsonable(response_metadata(chat_response)),
                }
            )
            edits.append(planned_edit_from_slot_output(base_by_slot[sampled.slot_id], sampled_by_slot[sampled.slot_id], raw))
        return finalize_plan_from_edits(row, sample, base_plan, edits), responses, [], attempts

    def build_position_plan(
        self,
        row: AnnotationRow,
        sample: SampleSpec,
        base_plan: PlanSpec,
        source_image: Image.Image | None,
    ) -> tuple[PlanSpec, list[dict[str, Any]], list[dict[str, Any]], int]:
        base_by_slot = {edit.slot_id: edit for edit in base_plan.edits}
        sampled_by_slot = {edit.slot_id: edit for edit in sample.edits}
        items = [
            (sampled, find_slot(row, sampled.slot_id))
            for sampled in sample.edits[:2]
        ]
        messages = position_messages(row, items, source_image)
        raw, chat_response, attempt = self.call_json_with_retries(
            messages,
            lambda value: validate_position_json(value, sample),
        )
        raw_by_slot = {
            str(item["slot_id"]): item
            for item in raw.get("edits", [])
            if isinstance(item, dict) and item.get("slot_id") is not None
        }
        edits = [
            planned_edit_from_slot_output(base_by_slot[sampled.slot_id], sampled_by_slot[sampled.slot_id], raw_by_slot[sampled.slot_id])
            for sampled in sample.edits
        ]
        responses = [
            {
                "slot_ids": [sampled.slot_id for sampled in sample.edits],
                "attempts": attempt + 1,
                "raw": raw,
                "response": to_jsonable(response_metadata(chat_response)),
            }
        ]
        return finalize_plan_from_edits(row, sample, base_plan, edits), responses, [], attempt

    def build(self, row: AnnotationRow, sample: SampleSpec, source_image: Image.Image | None = None) -> PlanSpec:
        base_plan = build_rule_based_plan(row, sample)
        try:
            preferred = infer_question_attribute(source_question(row))
            if preferred == "position" and len(sample.edits) >= 2:
                plan, responses, warnings, retry_count = self.build_position_plan(row, sample, base_plan, source_image)
            else:
                plan, responses, warnings, retry_count = self.build_attribute_plan(row, sample, base_plan, source_image)
            metadata = {
                "backend": self.backend,
                "model": self.model,
                "base_url": self.base_url,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "reasoning_effort": self.reasoning_effort,
                "exclude_reasoning": self.exclude_reasoning,
                "max_retries": self.max_retries,
                "retry_count": retry_count,
                "vision_images": len(sample.edits) if source_image is not None else 0,
                "fallback_used": False,
                "responses": responses,
                "warnings": warnings,
            }
            return replace(plan, planner_metadata=metadata)
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            if not self.fallback_to_rule:
                raise
            metadata = {
                "backend": self.backend,
                "model": self.model,
                "base_url": self.base_url,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "reasoning_effort": self.reasoning_effort,
                "exclude_reasoning": self.exclude_reasoning,
                "max_retries": self.max_retries,
                "fallback_used": True,
                "fallback_reason": self.last_error,
            }
            return replace(base_plan, planner_metadata=metadata)


def build_plan(row: AnnotationRow, sample: SampleSpec) -> PlanSpec:
    return RuleBasedPlanner().build(row, sample)
