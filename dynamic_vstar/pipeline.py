from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from . import PIPELINE_VERSION
from .compositing import composite_context_crop, composite_generated_crop
from .geometry import (
    canvas_spec_for_crop,
    crop_image,
    crop_spec_for_slot,
    draw_guide_crop,
    draw_guide_canvas,
    letterbox_crop,
    restore_letterboxed_content,
)
from .image_api import ImageGenerator
from .planning import Planner, RuleBasedPlanner, find_slot
from .sampling import sample_image_edits
from .schemas import (
    AnnotationRow,
    DynamicItem,
    GenerationResult,
    PlanSpec,
    PlannedEdit,
    SampleSpec,
    to_jsonable,
)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(to_jsonable(value), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def item_dir_name(image_id: str, run_id: str, seed: int) -> str:
    return f"{image_id}__{run_id}"


STANDARD_IMAGE_SIZES = {
    "1024x1024": (1024, 1024),
    "1536x1024": (1536, 1024),
    "1024x1536": (1024, 1536),
}
SCALE = 4
OVERVIEW_WIDTH = 1100 * SCALE
OVERVIEW_MARGIN = 24 * SCALE
OVERVIEW_GAP = 16 * SCALE
OVERVIEW_BG = (255, 255, 255, 255)
PANEL_BG = (252, 253, 255, 255)
TEXT_FILL = (40, 40, 45, 255)
MUTED_FILL = (110, 110, 120, 255)
BORDER_FILL = (160, 165, 175, 255)
ACCENT_FILL = (52, 120, 198, 255)
LABEL_BG = (52, 120, 198, 240)
DASHED_BORDER_COLOR = (140, 145, 155, 255)
DASHED_BORDER_WIDTH = 2 * SCALE
DASHED_ON = 7 * SCALE
DASHED_OFF = 4 * SCALE


def prompt_for_crop(plan_edit: PlannedEdit) -> str:
    return (
        f"{plan_edit.image_prompt}\n\n"
        "You receive two input images with the same standard canvas size. "
        "The first image contains the local crop and an orange box marking the exact edit region. "
        "The second image contains the same local crop without any guide markings and must be used as the clean visual reference. "
        "Return one edited image at the same canvas size. "
        "Make the requested change in the orange-boxed region of the local crop. "
        "Remove the orange box and leave no labels or guide markings in the output. "
        "Preserve the crop's lighting, perspective, boundaries, and all unrelated content."
    )


def choose_image_size(crop_size: tuple[int, int], requested: str) -> str:
    if requested != "match":
        return requested
    width, height = crop_size
    ratio = width / max(1, height)
    candidates = {key: size[0] / size[1] for key, size in STANDARD_IMAGE_SIZES.items()}
    return min(candidates, key=lambda key: abs(candidates[key] - ratio))


def parse_image_size(size: str) -> tuple[int, int]:
    if size not in STANDARD_IMAGE_SIZES:
        raise ValueError(
            f"size must be one of {sorted(STANDARD_IMAGE_SIZES)} or 'match' before resolution; got {size!r}"
        )
    return STANDARD_IMAGE_SIZES[size]


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    ttc_candidates: list[tuple[str, int]] = [
        ("/System/Library/Fonts/Avenir Next.ttc", 0 if bold else 5),  # Bold / Medium
        ("/System/Library/Fonts/Avenir.ttc", 4 if bold else 8),  # Heavy / Medium
    ]
    for path, index in ttc_candidates:
        try:
            return ImageFont.truetype(path, size=size, index=index)
        except OSError:
            continue
    ttf_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in ttf_candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_dashed_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    color: tuple[int, int, int, int] = DASHED_BORDER_COLOR,
    width: int = DASHED_BORDER_WIDTH,
    dash_on: int = DASHED_ON,
    dash_off: int = DASHED_OFF,
    radius: int = 6 * SCALE,
) -> None:
    x1, y1, x2, y2 = box
    r = min(radius, (x2 - x1) // 4, (y2 - y1) // 4)

    def _dashed_line(sx: int, sy: int, ex: int, ey: int) -> None:
        import math
        dx, dy = ex - sx, ey - sy
        length = math.hypot(dx, dy)
        if length < 1:
            return
        ux, uy = dx / length, dy / length
        pos = 0.0
        drawing = True
        while pos < length:
            seg = dash_on if drawing else dash_off
            seg = min(seg, length - pos)
            if drawing:
                lx1 = int(sx + ux * pos)
                ly1 = int(sy + uy * pos)
                lx2 = int(sx + ux * (pos + seg))
                ly2 = int(sy + uy * (pos + seg))
                draw.line([(lx1, ly1), (lx2, ly2)], fill=color, width=width)
            pos += seg
            drawing = not drawing

    _dashed_line(x1 + r, y1, x2 - r, y1)
    _dashed_line(x2, y1 + r, x2, y2 - r)
    _dashed_line(x2 - r, y2, x1 + r, y2)
    _dashed_line(x1, y2 - r, x1, y1 + r)
    if r > 0:
        draw.arc((x1, y1, x1 + 2 * r, y1 + 2 * r), 180, 270, fill=color, width=width)
        draw.arc((x2 - 2 * r, y1, x2, y1 + 2 * r), 270, 360, fill=color, width=width)
        draw.arc((x2 - 2 * r, y2 - 2 * r, x2, y2), 0, 90, fill=color, width=width)
        draw.arc((x1, y2 - 2 * r, x1 + 2 * r, y2), 90, 180, fill=color, width=width)


def text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    if not text:
        return (0, 0)
    x1, y1, x2, y2 = draw.textbbox((0, 0), text, font=font)
    return (x2 - x1, y2 - y1)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        words = list(text)
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if text_bbox(draw, candidate, font)[0] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = word
        else:
            chunk = ""
            for char in word:
                candidate_chunk = f"{chunk}{char}"
                if text_bbox(draw, candidate_chunk, font)[0] <= max_width:
                    chunk = candidate_chunk
                else:
                    if chunk:
                        lines.append(chunk)
                    chunk = char
            current = chunk
    if current:
        lines.append(current)
    return lines


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    fill: tuple[int, int, int, int] = TEXT_FILL,
    line_gap: int = 6,
) -> int:
    x, y = xy
    total = 0
    for line in wrap_text(draw, text, font, max_width):
        draw.text((x, y + total), line, font=font, fill=fill)
        total += text_bbox(draw, line, font)[1] + line_gap
    return max(0, total - line_gap)


def wrapped_text_height(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int, line_gap: int = 6) -> int:
    lines = wrap_text(draw, text, font, max_width)
    if not lines:
        return 0
    line_heights = [text_bbox(draw, line, font)[1] for line in lines]
    return sum(line_heights) + line_gap * (len(lines) - 1)


def fit_on_canvas(image: Image.Image, size: tuple[int, int], fill: tuple[int, int, int, int] = PANEL_BG) -> Image.Image:
    width, height = size
    canvas = Image.new("RGBA", size, fill)
    if image.width <= 0 or image.height <= 0:
        return canvas
    scale = min(width / image.width, height / image.height)
    fitted_size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    fitted = image.convert("RGBA").resize(fitted_size, Image.Resampling.LANCZOS)
    canvas.alpha_composite(fitted, ((width - fitted_size[0]) // 2, (height - fitted_size[1]) // 2))
    return canvas


def _draw_dashed_rectangle(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    outline: tuple[int, int, int, int],
    width: int,
    dash_on: int = 16,
    dash_off: int = 10,
) -> None:
    import math
    x1, y1, x2, y2 = box
    edges = [(x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)]
    for sx, sy, ex, ey in edges:
        dx, dy = ex - sx, ey - sy
        length = math.hypot(dx, dy)
        if length < 1:
            continue
        ux, uy = dx / length, dy / length
        pos, drawing = 0.0, True
        while pos < length:
            seg = min(dash_on if drawing else dash_off, length - pos)
            if drawing:
                draw.line(
                    [(int(sx + ux * pos), int(sy + uy * pos)),
                     (int(sx + ux * (pos + seg)), int(sy + uy * (pos + seg)))],
                    fill=outline, width=width,
                )
            pos += seg
            drawing = not drawing


def draw_source_guides(source: Image.Image, row: AnnotationRow, plan: PlanSpec) -> Image.Image:
    selected = {edit.slot_id for edit in plan.edits}
    guide = source.convert("RGBA").copy()
    draw = ImageDraw.Draw(guide)
    line_width = max(4, min(10, round(min(guide.size) / 180)))
    context_color = (52, 152, 219, 255)
    edit_color = (230, 126, 34, 255)
    dash_on = max(14, line_width * 4)
    dash_off = max(10, line_width * 3)
    for slot in row.slots:
        if slot.slot_id not in selected:
            continue
        cx1, cy1, cx2, cy2 = slot.context_region.xyxy
        ex1, ey1, ex2, ey2 = slot.edit_region.xyxy
        _draw_dashed_rectangle(draw, (cx1, cy1, cx2, cy2), context_color, line_width, dash_on, dash_off)
        draw.rectangle((ex1, ey1, ex2, ey2), outline=edit_color, width=line_width)
    return guide


def options_line(plan: PlanSpec) -> str:
    return "  ".join(f"({key}) {value}" for key, value in sorted(plan.options.items()))


def answer_line(plan: PlanSpec) -> str:
    return f"Answer: ({plan.correct_label}) {plan.answer}"


def panel_height(
    draw: ImageDraw.ImageDraw,
    image_height: int,
    title: str,
    caption: str,
    width: int,
    title_font: ImageFont.ImageFont,
    caption_font: ImageFont.ImageFont,
) -> int:
    S = SCALE
    text_width = width - 20 * S
    return (
        10 * S
        + wrapped_text_height(draw, title, title_font, text_width)
        + 7 * S
        + image_height
        + 7 * S
        + wrapped_text_height(draw, caption, caption_font, text_width)
        + 10 * S
    )


def draw_image_panel(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    size: tuple[int, int],
    title: str,
    image: Image.Image,
    image_height: int,
    caption: str,
    title_font: ImageFont.ImageFont,
    caption_font: ImageFont.ImageFont,
) -> int:
    x, y = xy
    width, height = size
    S = SCALE
    pad = 10 * S
    draw_dashed_rect(draw, (x, y, x + width, y + height), radius=7 * S)
    cursor = y + pad
    cursor += draw_wrapped_text(draw, (x + pad, cursor), title, title_font, width - 2 * pad)
    cursor += 7 * S
    image_box = (x + pad, cursor, x + width - pad, cursor + image_height)
    fitted = fit_on_canvas(image, (image_box[2] - image_box[0], image_box[3] - image_box[1]), fill=OVERVIEW_BG)
    canvas.alpha_composite(fitted, image_box[:2])
    cursor = image_box[3] + 7 * S
    if caption:
        draw_wrapped_text(draw, (x + pad, cursor), caption, caption_font, width - 2 * pad, fill=MUTED_FILL)
    return height


def slot_comparison_image(before: Image.Image, after: Image.Image) -> Image.Image:
    S = SCALE
    label_font = load_font(22 * S, bold=True)
    label_h = 33 * S
    panel_w = 420 * S
    panel_h = 285 * S
    arrow_w = 40 * S
    canvas = Image.new("RGBA", (panel_w * 2 + arrow_w, panel_h), OVERVIEW_BG)
    draw = ImageDraw.Draw(canvas)
    draw.text((7 * S, 4 * S), "Input crop", font=label_font, fill=TEXT_FILL)
    draw.text((panel_w + arrow_w + 7 * S, 4 * S), "Edited result", font=label_font, fill=TEXT_FILL)
    before_fit = fit_on_canvas(before, (panel_w, panel_h - label_h), fill=OVERVIEW_BG)
    after_fit = fit_on_canvas(after, (panel_w, panel_h - label_h), fill=OVERVIEW_BG)
    canvas.alpha_composite(before_fit, (0, label_h))
    canvas.alpha_composite(after_fit, (panel_w + arrow_w, label_h))
    arrow_cy = label_h + (panel_h - label_h) // 2
    ax = panel_w + 3 * S
    draw.line([(ax, arrow_cy), (ax + arrow_w - 9 * S, arrow_cy)], fill=ACCENT_FILL, width=2 * S)
    tip = ax + arrow_w - 4 * S
    draw.polygon([(tip, arrow_cy), (tip - 7 * S, arrow_cy - 5 * S), (tip - 7 * S, arrow_cy + 5 * S)], fill=ACCENT_FILL)
    return canvas


def _format_slot_title(edit: PlannedEdit) -> str:
    mode_label = "Replace" if edit.mode == "replace" else "Add"
    target = edit.target_phrase or ""
    return f"{mode_label}: {target}" if target else mode_label


def _build_slot_detail_lines(
    edit: PlannedEdit,
    row: AnnotationRow | None = None,
) -> list[tuple[str, str, str | None]]:
    """Return list of (label, value, highlight_value_or_None) for the slot detail area."""
    lines: list[tuple[str, str, str | None]] = []
    if edit.mode == "replace":
        lines.append(("target_ref:", f'"{edit.target_phrase or "?"}"', None))
        lines.append(("new color:", edit.answer, edit.answer))
    else:
        if row:
            slot = next((s for s in row.slots if s.slot_id == edit.slot_id), None)
            if slot and slot.add:
                add_data = slot.add if isinstance(slot.add, dict) else vars(slot.add) if hasattr(slot.add, '__dict__') else {}
                candidates = add_data.get("objects", []) if isinstance(add_data, dict) else getattr(slot.add, "objects", [])
                sampled = (edit.target_phrase or "").replace("the ", "")
                cand_str = ", ".join(candidates)
                lines.append(("candidates:", cand_str, sampled))
        lines.append(("sampled:", f"{edit.answer} {(edit.target_phrase or '').replace('the ', '')}", edit.answer))
    raw_prompt = edit.image_prompt.split(". ")[0]
    for trim in [", sized naturally for the scene context", ", sized naturally"]:
        raw_prompt = raw_prompt.replace(trim, "")
    lines.append(("prompt:", raw_prompt, None))
    return lines


COLOR_RGB = {
    "red": (231, 76, 60), "orange": (230, 126, 34), "yellow": (200, 170, 15),
    "green": (39, 174, 96), "blue": (52, 152, 219), "purple": (155, 89, 182),
    "pink": (233, 30, 99), "brown": (121, 85, 72), "black": (33, 33, 33),
    "white": (160, 160, 160), "gray": (130, 130, 130),
}


def _draw_slot_details(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    width: int,
    lines: list[tuple[str, str, str | None]],
    label_font: ImageFont.ImageFont,
    body_font: ImageFont.ImageFont,
) -> int:
    x, y = xy
    cursor = 0
    line_h = text_bbox(draw, "Ag", label_font)[1]
    line_gap = 8 * SCALE
    for label_text, value_text, highlight in lines:
        lw = text_bbox(draw, label_text, label_font)[0] + 8
        draw.text((x, y + cursor), label_text, font=label_font, fill=TEXT_FILL)
        if highlight and highlight in COLOR_RGB:
            color = COLOR_RGB[highlight]
            parts = value_text.split(highlight, 1)
            vx = x + lw
            if parts[0]:
                pw = text_bbox(draw, parts[0], body_font)[0]
                draw.text((vx, y + cursor), parts[0], font=body_font, fill=MUTED_FILL)
                vx += pw
            draw.text((vx, y + cursor), highlight, font=label_font, fill=(*color, 255))
            hw = text_bbox(draw, highlight, label_font)[0]
            vx += hw
            if len(parts) > 1 and parts[1]:
                draw.text((vx, y + cursor), parts[1], font=body_font, fill=MUTED_FILL)
        else:
            draw_wrapped_text(draw, (x + lw, y + cursor), value_text, body_font, width - lw, fill=MUTED_FILL)
        cursor += line_h + line_gap
    return cursor


LEGEND_HEIGHT = 25 * SCALE


def write_overview_image(
    path: Path,
    boxed_source: Image.Image,
    final_composite: Image.Image,
    plan: PlanSpec,
    slot_images: list[tuple[PlannedEdit, Image.Image, Image.Image]],
    row: AnnotationRow | None = None,
) -> None:
    S = SCALE
    title_font = load_font(22 * S, bold=True)
    section_font = load_font(15 * S, bold=True)
    body_font = load_font(12 * S)
    small_font = load_font(11 * S)
    label_font = load_font(12 * S, bold=True)
    detail_label_font = load_font(15 * S, bold=True)
    detail_body_font = load_font(14 * S)
    legend_font = load_font(11 * S, bold=True)

    measure = Image.new("RGBA", (OVERVIEW_WIDTH, 100), OVERVIEW_BG)
    measure_draw = ImageDraw.Draw(measure)
    content_w = OVERVIEW_WIDTH - 2 * OVERVIEW_MARGIN

    header_lines = [
        ("Original:", plan.source_question or "-"),
        ("Generated:", plan.question),
        ("Options:", options_line(plan)),
        ("Answer:", f"({plan.correct_label}) {plan.answer}"),
    ]
    header_h = 12 * S
    for _, text in header_lines:
        header_h += wrapped_text_height(measure_draw, text, body_font, content_w - 85 * S) + 7 * S
    header_h += 12 * S

    top_w = (content_w - OVERVIEW_GAP) // 2
    top_image_h = 340 * S
    top_h = panel_height(measure_draw, top_image_h, "Source", "", top_w, section_font, small_font)
    top_h += LEGEND_HEIGHT

    slot_cols = min(3, max(1, len(slot_images)))
    slot_w = (content_w - OVERVIEW_GAP * (slot_cols - 1)) // slot_cols
    slot_image_h = 195 * S
    detail_h_per_slot = 105 * S
    slot_panel_heights: list[int] = []
    for edit, _, _ in slot_images:
        base_h = panel_height(measure_draw, slot_image_h, _format_slot_title(edit), "", slot_w, section_font, small_font)
        slot_panel_heights.append(base_h + detail_h_per_slot)
    slot_rows: list[int] = []
    for start in range(0, len(slot_panel_heights), slot_cols):
        slot_rows.append(max(slot_panel_heights[start : start + slot_cols]))
    slots_h = sum(slot_rows) + OVERVIEW_GAP * max(0, len(slot_rows) - 1)

    total_h = OVERVIEW_MARGIN + header_h + OVERVIEW_GAP + top_h + (OVERVIEW_GAP + slots_h if slot_images else 0) + OVERVIEW_MARGIN
    canvas = Image.new("RGBA", (OVERVIEW_WIDTH, total_h), OVERVIEW_BG)
    draw = ImageDraw.Draw(canvas)

    # Header
    y = OVERVIEW_MARGIN
    qid = plan.question_id or plan.image_id or "-"
    title_text = f"vstar_{int(qid):04d}" if qid.isdigit() else qid
    draw_wrapped_text(draw, (OVERVIEW_MARGIN, y), title_text, title_font, content_w, fill=ACCENT_FILL)
    y += text_bbox(draw, title_text, title_font)[1] + 9 * S

    draw.line([(OVERVIEW_MARGIN, y), (OVERVIEW_WIDTH - OVERVIEW_MARGIN, y)], fill=BORDER_FILL, width=S)
    y += 7 * S

    for bold_label, text in header_lines:
        label_w = text_bbox(draw, bold_label, label_font)[0] + 8
        draw.text((OVERVIEW_MARGIN, y), bold_label, font=label_font, fill=ACCENT_FILL)
        y += draw_wrapped_text(draw, (OVERVIEW_MARGIN + label_w, y), text, body_font, content_w - label_w)
        y += 10
    y += 8

    # Top panels (Source + Edited)
    panel_h_no_legend = top_h - LEGEND_HEIGHT
    draw_image_panel(canvas, draw, (OVERVIEW_MARGIN, y), (top_w, panel_h_no_legend), "Source", boxed_source, top_image_h, "", section_font, small_font)
    draw_image_panel(canvas, draw, (OVERVIEW_MARGIN + top_w + OVERVIEW_GAP, y), (top_w, panel_h_no_legend), "Edited", final_composite, top_image_h, "", section_font, small_font)

    # Legend below Source panel
    legend_y = y + panel_h_no_legend + 4 * S
    lx = OVERVIEW_MARGIN + 10 * S
    context_color = (52, 152, 219, 255)
    edit_color = (230, 126, 34, 255)
    box_w, box_h = 14 * S, 9 * S
    _draw_dashed_rectangle(draw, (lx, legend_y + 2 * S, lx + box_w, legend_y + 2 * S + box_h), context_color, S + 1, 4 * S, 3 * S)
    draw.text((lx + box_w + 5 * S, legend_y), "Context region", font=legend_font, fill=(*context_color[:3], 255))
    ctx_tw = text_bbox(draw, "Context region", legend_font)[0]
    lx2 = lx + box_w + 5 * S + ctx_tw + 15 * S
    draw.rectangle((lx2, legend_y + 2 * S, lx2 + box_w, legend_y + 2 * S + box_h), outline=edit_color, width=S + 1)
    draw.text((lx2 + box_w + 5 * S, legend_y), "Edit region", font=legend_font, fill=(*edit_color[:3], 255))

    y += top_h + OVERVIEW_GAP

    # Slot panels with rich details inside the panel
    panel_index = 0
    for row_h in slot_rows:
        for col in range(slot_cols):
            if panel_index >= len(slot_images):
                break
            edit, before_image, after_image = slot_images[panel_index]
            px = OVERVIEW_MARGIN + col * (slot_w + OVERVIEW_GAP)
            pad = 12 * S
            draw_dashed_rect(draw, (px, y, px + slot_w, y + row_h), radius=7 * S)
            cursor_y = y + pad
            cursor_y += draw_wrapped_text(draw, (px + pad, cursor_y), _format_slot_title(edit), section_font, slot_w - 2 * pad)
            cursor_y += 8 * S
            comparison = slot_comparison_image(before_image, after_image)
            image_box = (px + pad, cursor_y, px + slot_w - pad, cursor_y + slot_image_h)
            fitted = fit_on_canvas(comparison, (image_box[2] - image_box[0], image_box[3] - image_box[1]), fill=OVERVIEW_BG)
            canvas.alpha_composite(fitted, image_box[:2])
            cursor_y = image_box[3] + 9 * S
            draw.line([(px + pad, cursor_y), (px + slot_w - pad, cursor_y)], fill=BORDER_FILL, width=S)
            cursor_y += 7 * S
            detail_lines = _build_slot_detail_lines(edit, row)
            _draw_slot_details(draw, (px + pad, cursor_y), slot_w - 2 * pad, detail_lines, detail_label_font, detail_body_font)
            panel_index += 1
        y += row_h + OVERVIEW_GAP

    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(path)


def run_dynamic_item(
    row: AnnotationRow,
    source_image: Image.Image,
    out_root: Path,
    run_id: str,
    generator: ImageGenerator,
    planner: Planner | None = None,
    allow_multislot: bool = False,
    size: str = "match",
    quality: str = "high",
) -> DynamicItem:
    sample = sample_image_edits(row, run_id=run_id, allow_multislot=allow_multislot)
    planner = planner or RuleBasedPlanner()
    plan = planner.build(row, sample, source_image=source_image)
    run_dir = out_root / item_dir_name(row.image_id, run_id, sample.seed)
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    current = source_image.convert("RGBA")
    source_path = artifacts_dir / "source.png"
    current.save(source_path)
    boxed_source = draw_source_guides(current, row, plan)
    source_boxed_path = artifacts_dir / "source_boxed.png"
    boxed_source.save(source_boxed_path)

    sample_path = artifacts_dir / "sample.json"
    plan_path = artifacts_dir / "plan.json"
    write_json(sample_path, sample)
    write_json(plan_path, plan)

    generations: list[GenerationResult] = []
    slot_overview_images: list[tuple[PlannedEdit, Image.Image, Image.Image]] = []
    for plan_edit in plan.edits:
        slot = find_slot(row, plan_edit.slot_id)
        crop_spec = crop_spec_for_slot(slot, current.size)
        context_crop = crop_image(current, crop_spec.crop_xyxy)
        api_size = choose_image_size(crop_spec.output_size, size)
        canvas_spec = canvas_spec_for_crop(crop_spec, parse_image_size(api_size))
        clean_canvas = letterbox_crop(context_crop, canvas_spec)
        guide_context = draw_guide_crop(context_crop, crop_spec)
        guide_canvas = draw_guide_canvas(clean_canvas, canvas_spec)

        context_path = artifacts_dir / f"context_{plan_edit.slot_id}.png"
        guide_context_path = artifacts_dir / f"guide_context_{plan_edit.slot_id}.png"
        clean_canvas_path = artifacts_dir / f"clean_canvas_{plan_edit.slot_id}.png"
        guide_canvas_path = artifacts_dir / f"guide_canvas_{plan_edit.slot_id}.png"
        generated_canvas_path = artifacts_dir / f"generated_canvas_{plan_edit.slot_id}.png"
        restored_context_path = artifacts_dir / f"restored_context_{plan_edit.slot_id}.png"
        context_crop.save(context_path)
        guide_context.save(guide_context_path)
        clean_canvas.save(clean_canvas_path)
        guide_canvas.save(guide_canvas_path)

        api_prompt = prompt_for_crop(plan_edit)
        api_metadata = generator.generate_edit(
            prompt=api_prompt,
            image_path=guide_canvas_path,
            output_path=generated_canvas_path,
            size=api_size,
            quality=quality,
            n=1,
            reference_image_paths=[clean_canvas_path],
        )
        with Image.open(generated_canvas_path) as generated_img:
            restored_context = restore_letterboxed_content(generated_img, canvas_spec)
        restored_context.save(restored_context_path)
        slot_overview_images.append((plan_edit, guide_context.copy(), restored_context.copy()))
        use_mask = plan.planner_metadata.get("use_mask", False)
        if use_mask:
            current, _ = composite_generated_crop(current, restored_context, crop_spec)
        else:
            current = composite_context_crop(current, restored_context, crop_spec)

        generations.append(
            GenerationResult(
                slot_id=plan_edit.slot_id,
                context_crop_path=str(context_path),
                clean_canvas_path=str(clean_canvas_path),
                guide_crop_path=str(guide_canvas_path),
                generated_canvas_path=str(generated_canvas_path),
                restored_context_path=str(restored_context_path),
                api_metadata=api_metadata,
                crop=crop_spec,
                canvas=canvas_spec,
            )
        )

    composite_path = artifacts_dir / "composite.png"
    current.save(composite_path)
    overview_path = run_dir / "overview.png"
    write_overview_image(
        overview_path,
        boxed_source,
        current,
        plan,
        slot_overview_images,
        row=row,
    )
    item = DynamicItem(
        image_id=row.image_id,
        question_id=row.question_id,
        run_id=run_id,
        source_image_path=str(source_path),
        composite_image_path=str(composite_path),
        overview_image_path=str(overview_path),
        sample=sample,
        plan=plan,
        generations=generations,
        qc={
            "qc_pass": None,
            "qc_reasons": [],
            "qc_stage": "not_run",
        },
    )
    manifest = {
        **to_jsonable(item),
        "pipeline_version": PIPELINE_VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "files": {
            "artifacts_dir": str(artifacts_dir),
            "source": str(source_path),
            "source_boxed": str(source_boxed_path),
            "sample": str(sample_path),
            "plan": str(plan_path),
            "composite": str(composite_path),
            "overview": str(overview_path),
            "manifest": str(artifacts_dir / "manifest.json"),
        },
    }
    write_json(artifacts_dir / "manifest.json", manifest)
    return item
