#!/usr/bin/env python3
"""Generate sub-images for the pipeline figure.

Standalone script — does NOT modify pipeline.py or geometry.py.
Generates annotated source, crops, and color sampling visualizations.

Usage:
    python scripts/gen_figure_subimages.py --image-id vstar_0129 --out results/figure_parts
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynamic_vstar.schemas import annotation_row_from_dict
from dynamic_vstar.planning import find_slot
from dynamic_vstar.geometry import crop_spec_for_slot, crop_image


# ── Color palette per slot ──────────────────────────────────────────

SLOT_COLORS: dict[str, dict[str, tuple[int, int, int, int]]] = {
    "A1": {"ctx": (255, 255, 255, 255), "edit": (255, 255, 255, 255), "badge": (200, 200, 200, 230), "type_label": "Replace"},  # white (sampled white)
    "B1": {"ctx": (230, 126, 34, 255),  "edit": (230, 126, 34, 255),  "badge": (230, 126, 34, 210),  "type_label": "Replace"},  # orange (sampled orange)
    "C1": {"ctx": (231, 76, 60, 255),   "edit": (231, 76, 60, 255),   "badge": (231, 76, 60, 210),   "type_label": "Add"},      # red (sampled red)
    "D1": {"ctx": (52, 152, 219, 255),  "edit": (52, 152, 219, 255),  "badge": (52, 152, 219, 210),  "type_label": "Add"},      # blue (sampled blue)
}

# Fallback for unknown slot IDs
_REPLACE_DEFAULT = {"ctx": (230, 126, 34, 255), "edit": (230, 126, 34, 255), "badge": (230, 126, 34, 210), "type_label": "Replace"}
_ADD_DEFAULT = {"ctx": (21, 101, 192, 255), "edit": (21, 101, 192, 255), "badge": (21, 101, 192, 210), "type_label": "Add"}


def slot_color(slot) -> dict:
    if slot.slot_id in SLOT_COLORS:
        return SLOT_COLORS[slot.slot_id]
    return _REPLACE_DEFAULT if slot.replace is not None else _ADD_DEFAULT


# ── Font loading ────────────────────────────────────────────────────

def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    for path, idx in [("/System/Library/Fonts/Avenir Next.ttc", 0 if bold else 5),
                       ("/System/Library/Fonts/Avenir.ttc", 4 if bold else 8)]:
        try:
            return ImageFont.truetype(path, size=size, index=idx)
        except OSError:
            continue
    for path in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


# ── Drawing helpers ─────────────────────────────────────────────────

def _text_size(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def _dashed_rect(draw, box, color, width, dash_on=16, dash_off=10):
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
                draw.line([(int(sx + ux * pos), int(sy + uy * pos)),
                           (int(sx + ux * (pos + seg)), int(sy + uy * (pos + seg)))],
                          fill=color, width=width)
            pos += seg
            drawing = not drawing


# ── Source image with all slots ─────────────────────────────────────

def draw_source_all_slots(
    source: Image.Image,
    row,
    selected_ids: set[str] | None = None,
) -> Image.Image:
    """Draw all slots on source. Selected slots get full opacity; others dimmed."""
    guide = source.convert("RGBA").copy()
    draw = ImageDraw.Draw(guide)
    font = load_font(max(16, min(32, guide.width // 50)), bold=True)

    for slot in row.slots:
        sc = slot_color(slot)
        active = selected_ids is None or slot.slot_id in selected_ids
        alpha = 255 if active else 100

        cx1, cy1, cx2, cy2 = slot.context_region.xyxy
        ex1, ey1, ex2, ey2 = slot.edit_region.xyxy
        ctx_c = (*sc["ctx"][:3], alpha)
        edit_c = (*sc["edit"][:3], alpha)

        # Adaptive line width and dash based on context box size
        ctx_size = min(cx2 - cx1, cy2 - cy1)
        ctx_lw = max(2, min(5, round(ctx_size / 30)))
        ctx_dash_on = max(6, ctx_lw * 3)
        ctx_dash_off = max(4, ctx_lw * 2)

        edit_size = min(ex2 - ex1, ey2 - ey1)
        edit_lw = max(2, min(4, round(edit_size / 15)))

        if not active:
            ctx_lw = max(1, ctx_lw // 2)
            edit_lw = max(1, edit_lw // 2)

        _dashed_rect(draw, (cx1, cy1, cx2, cy2), ctx_c, ctx_lw, ctx_dash_on, ctx_dash_off)
        draw.rectangle((ex1, ey1, ex2, ey2), outline=edit_c, width=edit_lw)

        # Badge — sized to fit within context box, on top-left corner edge
        label = slot.slot_id[0]
        ctx_w, ctx_h = cx2 - cx1, cy2 - cy1
        badge_font_size = max(10, min(int(min(ctx_w, ctx_h) * 0.35), 32))
        badge_font = load_font(badge_font_size, bold=True)
        tw, th = _text_size(draw, label, badge_font)
        badge_c = (*sc["badge"][:3], 220 if active else 90)
        badge_w, badge_h = tw + 8, th + 4
        lbx = cx1
        lby = cy1
        lbx = max(0, min(lbx, guide.width - badge_w))
        lby = max(0, min(lby, guide.height - badge_h))
        draw.rectangle((lbx, lby, lbx + badge_w, lby + badge_h), fill=badge_c)
        draw.text((lbx + 4, lby), label, font=badge_font, fill=(255, 255, 255, 255))

    return guide


# ── Crop with slot-colored edit box ─────────────────────────────────

def draw_crop_guide(
    source: Image.Image,
    slot,
) -> Image.Image:
    """Crop the context region with edit box only."""
    sc = slot_color(slot)
    cs = crop_spec_for_slot(slot, source.size)
    crop = crop_image(source, cs.crop_xyxy).convert("RGBA")
    draw = ImageDraw.Draw(crop)
    lw = max(2, min(6, round(min(crop.size) / 40)))
    ex1, ey1, ex2, ey2 = cs.edit_xyxy_in_crop
    draw.rectangle((ex1, ey1, ex2, ey2), outline=sc["edit"], width=lw)
    return crop


# ── Main generation ─────────────────────────────────────────────────

def load_source_image(question_id: str):
    from scripts.run_dynamic_vstar_pipeline import load_vstar_sources, image_from_record
    sources = load_vstar_sources()
    record = sources[question_id]
    return image_from_record(record)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-id", default="vstar_0129")
    parser.add_argument("--out", type=Path, default=ROOT / "results/figure_parts")
    args = parser.parse_args()

    qid = args.image_id.replace("vstar_", "").lstrip("0") or "0"
    out = args.out / f"{args.image_id}_subimages"
    out.mkdir(parents=True, exist_ok=True)

    # Load annotation
    with open(ROOT / "data/annotations/dynamic_vstar_slots_latest.jsonl") as f:
        row = None
        for line in f:
            r = json.loads(line)
            if r["image_id"] == args.image_id:
                row = annotation_row_from_dict(r)
                break
    if not row:
        raise SystemExit(f"Image {args.image_id} not found in annotations")

    # Load source image
    source = load_source_image(qid)

    # 1. Source clean
    source.convert("RGB").save(out / "source_clean.png")
    print(f"source_clean: {source.size}")

    # 2. Source with ALL slots (all active)
    all_slots = draw_source_all_slots(source, row)
    all_slots.convert("RGB").save(out / "source_all_slots.png")
    print(f"source_all_slots: all {len(row.slots)} slots drawn")

    # 3. Per-slot crops (with context dashed border + edit solid box in slot color)
    for slot in row.slots:
        crop = draw_crop_guide(source, slot)
        letter = slot.slot_id[0]
        crop.convert("RGB").save(out / f"crop_{letter}.png")
        sc = slot_color(slot)
        print(f"crop_{letter}: {crop.size}, color=rgb{sc['edit'][:3]}")

    # 6. Full image with magnifier zoom on each slot's edit region
    import math as _math
    for slot in row.slots:
        sc = slot_color(slot)
        letter = slot.slot_id[0]
        vis = source.convert("RGBA").copy()
        draw = ImageDraw.Draw(vis)
        ex1, ey1, ex2, ey2 = slot.edit_region.xyxy
        cx_c = (ex1 + ex2) // 2
        cy_c = (ey1 + ey2) // 2
        edit_diag = max(ex2 - ex1, ey2 - ey1)
        circle_r = max(edit_diag, min(vis.width, vis.height) // 18)
        # Dashed circle
        lw_c = max(4, min(10, round(min(vis.size) / 250)))
        n_segs = 48
        for si in range(0, n_segs, 2):
            a1 = 2 * _math.pi * si / n_segs
            a2 = 2 * _math.pi * (si + 1) / n_segs
            draw.line([
                (cx_c + int(circle_r * _math.cos(a1)), cy_c + int(circle_r * _math.sin(a1))),
                (cx_c + int(circle_r * _math.cos(a2)), cy_c + int(circle_r * _math.sin(a2))),
            ], fill=sc["edit"], width=lw_c)
        # Zoomed inset (4x)
        zoom = 4
        pad = circle_r + edit_diag // 2
        zx1, zy1 = max(0, cx_c - pad), max(0, cy_c - pad)
        zx2, zy2 = min(vis.width, cx_c + pad), min(vis.height, cy_c + pad)
        zoomed = source.crop((zx1, zy1, zx2, zy2))
        zw = min(vis.width // 3, int((zx2 - zx1) * zoom))
        zh = min(vis.height // 3, int((zy2 - zy1) * zoom))
        zoomed = zoomed.resize((zw, zh), Image.Resampling.LANCZOS)
        # Place in top-right
        ix, iy = vis.width - zw - 30, 30
        draw.rectangle((ix - 4, iy - 4, ix + zw + 4, iy + zh + 4), outline=sc["edit"], width=4)
        vis.paste(zoomed.convert("RGBA"), (ix, iy))
        # Connecting line
        draw.line([(cx_c + circle_r, cy_c), (ix, iy + zh // 2)],
                  fill=(*sc["edit"][:3], 160), width=max(2, lw_c // 2))
        vis.convert("RGB").save(out / f"source_magnify_{letter}.png")
        print(f"source_magnify_{letter}: full image + {zoom}x zoom inset")

    # 7. Soft masks per slot (black bg, white edit region with gaussian blur)
    from PIL import ImageFilter
    for slot in row.slots:
        letter = slot.slot_id[0]
        cs = crop_spec_for_slot(slot, source.size)
        cw, ch = cs.output_size
        mask = Image.new("L", (cw, ch), 0)
        d = ImageDraw.Draw(mask)
        ex1, ey1, ex2, ey2 = cs.edit_xyxy_in_crop
        d.rectangle((ex1, ey1, ex2, ey2), fill=255)
        blur_r = max(3, min(ex2 - ex1, ey2 - ey1) // 3)
        mask = mask.filter(ImageFilter.GaussianBlur(radius=blur_r))
        rgb = Image.new("RGB", (cw, ch), (0, 0, 0))
        white = Image.new("RGB", (cw, ch), (255, 255, 255))
        rgb = Image.composite(white, rgb, mask)
        rgb.save(out / f"mask_{letter}.png")
        print(f"mask_{letter}: {cw}x{ch}, blur_r={blur_r}")

    # 7. Slot metadata summary
    meta = []
    for slot in row.slots:
        sc = slot_color(slot)
        entry = {
            "slot_id": slot.slot_id,
            "type": sc["type_label"],
            "color_rgb": list(sc["edit"][:3]),
            "context_xyxy": list(slot.context_region.xyxy),
            "edit_xyxy": list(slot.edit_region.xyxy),
        }
        if slot.replace:
            targets = slot.replace if isinstance(slot.replace, dict) else vars(slot.replace)
            entry["targets"] = targets.get("targets", [])
        if slot.add:
            add_data = slot.add if isinstance(slot.add, dict) else vars(slot.add)
            entry["candidates"] = add_data.get("objects", [])
        meta.append(entry)

    (out / "slots_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"\nslots_meta.json: {len(meta)} slots")
    for m in meta:
        print(f"  {m['slot_id']} ({m['type']}): color=rgb{tuple(m['color_rgb'])}")

    print(f"\nAll saved to {out}")


if __name__ == "__main__":
    main()
