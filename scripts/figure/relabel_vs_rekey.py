#!/usr/bin/env python3
"""Relabel V* vs ReKey comparison figure, matching pipeline overview style."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw
from dynamic_vstar.pipeline import (
    SCALE, OVERVIEW_WIDTH, OVERVIEW_MARGIN, OVERVIEW_GAP, OVERVIEW_BG,
    TEXT_FILL, MUTED_FILL, BORDER_FILL, ACCENT_FILL, COLOR_RGB, LEGEND_HEIGHT,
    load_font, draw_dashed_rect, text_bbox, draw_wrapped_text,
    draw_image_panel, fit_on_canvas, slot_comparison_image,
    _draw_dashed_rectangle,
)

S = SCALE
OUT = Path(__file__).parent
BENCH = ROOT / "results/benchmark/bench1/vstar_0101__bench1/artifacts"

SOURCE = BENCH / "source.png"
EDITED = BENCH / "composite.jpg"
CROP_IN = BENCH / "guide_context_B1.png"
CROP_OUT = BENCH / "restored_context_B1.png"

# Slot B1 coordinates (from bench1 manifest.json → generations[0].crop)
CONTEXT_XYXY = (2683, 1034, 2842, 1150)
EDIT_XYXY = (2740, 1099, 2771, 1118)

GREEN_FILL = (46, 139, 87, 255)
RED_FILL = (196, 78, 82, 255)
CONTEXT_COLOR = (52, 152, 219, 255)
EDIT_COLOR = (230, 126, 34, 255)

title_font = load_font(22 * S, bold=True)
section_font = load_font(15 * S, bold=True)
body_font = load_font(13 * S)
label_font = load_font(13 * S, bold=True)
small_font = load_font(11 * S)
desc_font = load_font(12 * S)
desc_bold = load_font(12 * S, bold=True)
detail_label_font = load_font(15 * S, bold=True)
detail_body_font = load_font(14 * S)
legend_font = load_font(11 * S, bold=True)

import json
plan_data = json.load(open(BENCH / "plan.json"))

src_img = Image.open(SOURCE).convert("RGBA")
edited_img = Image.open(EDITED).convert("RGBA")
crop_in_img = Image.open(CROP_IN).convert("RGBA")
crop_out_img = Image.open(CROP_OUT).convert("RGBA")


def make_source_with_guides():
    img = src_img.copy()
    d = ImageDraw.Draw(img)
    lw = max(4, min(10, round(min(img.size) / 180)))
    dash_on = max(14, lw * 4)
    dash_off = max(10, lw * 3)
    _draw_dashed_rectangle(d, CONTEXT_XYXY, CONTEXT_COLOR, lw, dash_on, dash_off)
    d.rectangle(EDIT_XYXY, outline=EDIT_COLOR, width=lw)
    return img


src_guided = make_source_with_guides()

content_w = OVERVIEW_WIDTH - 2 * OVERVIEW_MARGIN
x = OVERVIEW_MARGIN

measure = Image.new("RGBA", (OVERVIEW_WIDTH, 100), OVERVIEW_BG)
mdraw = ImageDraw.Draw(measure)

top_image_h = 340 * S
top_panel_w = (content_w - OVERVIEW_GAP) // 2
img_panel_h = top_image_h + 40 * S
qa_line_h = text_bbox(mdraw, "Q", body_font)[1] + 8 * S
opt_line_h = text_bbox(mdraw, "O", small_font)[1] + 6 * S
label_line_h = text_bbox(mdraw, "X", label_font)[1] + 6 * S
desc_line_h = text_bbox(mdraw, "X", desc_font)[1] + 4 * S
slot_panel_h = 350 * S

from dynamic_vstar.schemas import (
    AnnotationRow, Slot, ContextRegion, EditRegion, PlanSpec, PlannedEdit,
)

total_h = (
    OVERVIEW_MARGIN + 35 * S + OVERVIEW_GAP
    + 28 * S + desc_line_h
    + img_panel_h + OVERVIEW_GAP
    + (label_line_h + qa_line_h + opt_line_h + qa_line_h + 10 * S) * 2
    + OVERVIEW_GAP + 4 * S + OVERVIEW_GAP * 2
    + 28 * S + desc_line_h
    + (qa_line_h + opt_line_h + qa_line_h + 10 * S)
    + img_panel_h + LEGEND_HEIGHT + OVERVIEW_GAP
    + slot_panel_h + OVERVIEW_MARGIN
)

canvas = Image.new("RGBA", (OVERVIEW_WIDTH, total_h), OVERVIEW_BG)
draw = ImageDraw.Draw(canvas)

y = OVERVIEW_MARGIN

draw_wrapped_text(draw, (x, y), "vstar_0101", title_font, content_w, fill=ACCENT_FILL)
y += text_bbox(draw, "vstar_0101", title_font)[1] + 9 * S
draw.line([(x, y), (OVERVIEW_WIDTH - x, y)], fill=BORDER_FILL, width=S)
y += OVERVIEW_GAP

# SECTION 1: Relabel V*
draw_wrapped_text(draw, (x, y), "Relabel V*", title_font, content_w, fill=GREEN_FILL)
y += text_bbox(draw, "Relabel V*", title_font)[1] + 6 * S

desc_parts = [
    ("Static benchmark, ", False),
    ("fresh human-written questions", True),
    (" on ", False),
    ("different visual keys", True),
]
dx = x
for txt, bold in desc_parts:
    f = desc_bold if bold else desc_font
    draw.text((dx, y), txt, font=f, fill=MUTED_FILL)
    dx += text_bbox(draw, txt, f)[0]
y += desc_line_h + 4 * S

draw_image_panel(canvas, draw, (x, y), (content_w, img_panel_h),
                 "Source image (unchanged for both conditions)", src_img, top_image_h, "", section_font, small_font)
y += img_panel_h + OVERVIEW_GAP

draw.text((x, y), "Original V*", font=label_font, fill=ACCENT_FILL)
y += label_line_h
draw.text((x, y), "Q:", font=label_font, fill=TEXT_FILL)
draw.text((x + 25 * S, y), "What is the color of the life buoy?", font=body_font, fill=TEXT_FILL)
y += qa_line_h
draw.text((x + 25 * S, y), "(A) green/white   (B) red/white   (C) yellow/red   (D) blue/white",
          font=small_font, fill=MUTED_FILL)
y += opt_line_h
draw.text((x, y), "A:", font=label_font, fill=TEXT_FILL)
draw.text((x + 25 * S, y), "(B) red/white", font=label_font, fill=GREEN_FILL)
acc_text = "8/8 models correct"
draw.text((OVERVIEW_WIDTH - OVERVIEW_MARGIN - text_bbox(draw, acc_text, label_font)[0], y),
          acc_text, font=label_font, fill=GREEN_FILL)
y += qa_line_h + 10 * S

draw.text((x, y), "Relabel V*", font=label_font, fill=GREEN_FILL)
y += label_line_h
draw.text((x, y), "Q:", font=label_font, fill=TEXT_FILL)
draw.text((x + 25 * S, y), "What color is the direction sign?", font=body_font, fill=TEXT_FILL)
y += qa_line_h
draw.text((x + 25 * S, y), "(A) blue   (B) white   (C) yellow   (D) black",
          font=small_font, fill=MUTED_FILL)
y += opt_line_h
draw.text((x, y), "A:", font=label_font, fill=TEXT_FILL)
draw.text((x + 25 * S, y), "(C) yellow", font=label_font, fill=RED_FILL)
acc_text = "0/8 models correct"
draw.text((OVERVIEW_WIDTH - OVERVIEW_MARGIN - text_bbox(draw, acc_text, label_font)[0], y),
          acc_text, font=label_font, fill=RED_FILL)
y += qa_line_h + OVERVIEW_GAP

draw.line([(x, y), (OVERVIEW_WIDTH - x, y)], fill=BORDER_FILL, width=2 * S)
y += OVERVIEW_GAP * 2

# SECTION 2: ReKey
draw_wrapped_text(draw, (x, y), "ReKey", title_font, content_w, fill=RED_FILL)
y += text_bbox(draw, "ReKey", title_font)[1] + 6 * S

desc_parts2 = [
    ("Dynamic benchmark, ", False),
    ("fresh visual key", True),
    (" via ", False),
    ("localized image editing", True),
]
dx = x
for txt, bold in desc_parts2:
    f = desc_bold if bold else desc_font
    draw.text((dx, y), txt, font=f, fill=MUTED_FILL)
    dx += text_bbox(draw, txt, f)[0]
y += desc_line_h + 4 * S

draw.text((x, y), "Q:", font=label_font, fill=TEXT_FILL)
draw.text((x + 25 * S, y), "What color is the dog?", font=body_font, fill=TEXT_FILL)
y += qa_line_h
draw.text((x + 25 * S, y), "(A) brown   (B) purple   (C) yellow   (D) black",
          font=small_font, fill=MUTED_FILL)
y += opt_line_h
draw.text((x, y), "A:", font=label_font, fill=TEXT_FILL)
draw.text((x + 25 * S, y), "(B) purple", font=label_font, fill=RED_FILL)
acc_text = "0/8 models correct"
draw.text((OVERVIEW_WIDTH - OVERVIEW_MARGIN - text_bbox(draw, acc_text, label_font)[0], y),
          acc_text, font=label_font, fill=RED_FILL)
y += qa_line_h + 10 * S

panel_h_no_legend = img_panel_h
draw_image_panel(canvas, draw, (x, y), (top_panel_w, panel_h_no_legend),
                 "Source", src_guided, top_image_h, "", section_font, small_font)
draw_image_panel(canvas, draw, (x + top_panel_w + OVERVIEW_GAP, y), (top_panel_w, panel_h_no_legend),
                 "Edited", edited_img, top_image_h, "", section_font, small_font)

legend_y = y + panel_h_no_legend + 4 * S
lx = x + 10 * S
box_w, box_h = 14 * S, 9 * S
_draw_dashed_rectangle(draw, (lx, legend_y + 2 * S, lx + box_w, legend_y + 2 * S + box_h),
                       CONTEXT_COLOR, S + 1, 4 * S, 3 * S)
draw.text((lx + box_w + 5 * S, legend_y), "Context region", font=legend_font,
          fill=(*CONTEXT_COLOR[:3], 255))
ctx_tw = text_bbox(draw, "Context region", legend_font)[0]
lx2 = lx + box_w + 5 * S + ctx_tw + 15 * S
draw.rectangle((lx2, legend_y + 2 * S, lx2 + box_w, legend_y + 2 * S + box_h),
               outline=EDIT_COLOR, width=S + 1)
draw.text((lx2 + box_w + 5 * S, legend_y), "Edit region", font=legend_font,
          fill=(*EDIT_COLOR[:3], 255))

y += panel_h_no_legend + LEGEND_HEIGHT + OVERVIEW_GAP

pad = 12 * S
draw_dashed_rect(draw, (x, y, x + content_w, y + slot_panel_h), radius=7 * S)
cursor_y = y + pad
cursor_y += draw_wrapped_text(draw, (x + pad, cursor_y), "Add: the dog",
                              section_font, content_w - 2 * pad)
cursor_y += 8 * S

slot_image_h = 195 * S
comparison = slot_comparison_image(crop_in_img, crop_out_img)
image_box = (x + pad, cursor_y, x + content_w - pad, cursor_y + slot_image_h)
fitted = fit_on_canvas(comparison, (image_box[2] - image_box[0], image_box[3] - image_box[1]),
                       fill=OVERVIEW_BG)
canvas.alpha_composite(fitted, image_box[:2])
cursor_y = image_box[3] + 9 * S

draw.line([(x + pad, cursor_y), (x + content_w - pad, cursor_y)], fill=BORDER_FILL, width=S)
cursor_y += 7 * S

detail_lines = [
    ("candidates:", "cat, dog", "dog"),
    ("sampled:", "purple dog", "purple"),
    ("prompt:", "Add a purple dog in the marked area", None),
]
line_h = text_bbox(draw, "Ag", detail_label_font)[1]
line_gap = 8 * S
for label_text, value_text, highlight in detail_lines:
    lw = text_bbox(draw, label_text, detail_label_font)[0] + 8
    draw.text((x + pad, cursor_y), label_text, font=detail_label_font, fill=TEXT_FILL)
    if highlight and highlight in COLOR_RGB:
        color = COLOR_RGB[highlight]
        parts = value_text.split(highlight, 1)
        vx = x + pad + lw
        if parts[0]:
            pw = text_bbox(draw, parts[0], detail_body_font)[0]
            draw.text((vx, cursor_y), parts[0], font=detail_body_font, fill=MUTED_FILL)
            vx += pw
        draw.text((vx, cursor_y), highlight, font=detail_label_font, fill=(*color, 255))
        hw = text_bbox(draw, highlight, detail_label_font)[0]
        vx += hw
        if len(parts) > 1 and parts[1]:
            draw.text((vx, cursor_y), parts[1], font=detail_body_font, fill=MUTED_FILL)
    else:
        draw_wrapped_text(draw, (x + pad + lw, cursor_y), value_text, detail_body_font,
                          content_w - 2 * pad - lw, fill=MUTED_FILL)
    cursor_y += line_h + line_gap

canvas.convert("RGB").save(OUT / "relabel_vs_rekey.png")
canvas.convert("RGB").save(OUT / "relabel_vs_rekey.pdf")
print(f"Saved to {OUT}/relabel_vs_rekey.{{png,pdf}}")
