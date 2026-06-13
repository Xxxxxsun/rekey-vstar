from __future__ import annotations

from PIL import Image, ImageDraw

from .schemas import Box, CanvasSpec, CropSpec, Slot


def clamp_xyxy(box: Box, image_size: tuple[int, int]) -> Box:
    width, height = image_size
    x1, y1, x2, y2 = box
    x1 = max(0, min(x1, width - 1))
    y1 = max(0, min(y1, height - 1))
    x2 = max(x1 + 1, min(x2, width))
    y2 = max(y1 + 1, min(y2, height))
    return (x1, y1, x2, y2)


def expand_xyxy(box: Box, image_size: tuple[int, int], fraction: float = 0.08, min_pad: int = 16) -> Box:
    x1, y1, x2, y2 = box
    w = x2 - x1
    h = y2 - y1
    pad_x = max(min_pad, round(w * fraction))
    pad_y = max(min_pad, round(h * fraction))
    return clamp_xyxy((x1 - pad_x, y1 - pad_y, x2 + pad_x, y2 + pad_y), image_size)


def box_to_local(box: Box, crop_xyxy: Box) -> Box:
    cx1, cy1, _, _ = crop_xyxy
    x1, y1, x2, y2 = box
    return (x1 - cx1, y1 - cy1, x2 - cx1, y2 - cy1)


def crop_spec_for_slot(
    slot: Slot,
    image_size: tuple[int, int],
    padding_fraction: float = 0.0,
    min_pad: int = 0,
) -> CropSpec:
    context = clamp_xyxy(slot.context_region.xyxy, image_size)
    crop = expand_xyxy(context, image_size, fraction=padding_fraction, min_pad=min_pad)
    edit = clamp_xyxy(slot.edit_region.xyxy, image_size)
    return CropSpec(
        slot_id=slot.slot_id,
        context_xyxy=context,
        crop_xyxy=crop,
        edit_xyxy=edit,
        edit_xyxy_in_crop=box_to_local(edit, crop),
        output_size=(crop[2] - crop[0], crop[3] - crop[1]),
    )


def crop_image(image: Image.Image, box: Box) -> Image.Image:
    return image.crop(box).convert("RGBA")


def scale_box(box: Box, scale: float, offset: tuple[int, int], image_size: tuple[int, int]) -> Box:
    ox, oy = offset
    x1, y1, x2, y2 = box
    scaled = (
        ox + round(x1 * scale),
        oy + round(y1 * scale),
        ox + round(x2 * scale),
        oy + round(y2 * scale),
    )
    return clamp_xyxy(scaled, image_size)


def canvas_spec_for_crop(crop_spec: CropSpec, canvas_size: tuple[int, int]) -> CanvasSpec:
    source_w, source_h = crop_spec.output_size
    canvas_w, canvas_h = canvas_size
    if source_w <= 0 or source_h <= 0:
        raise ValueError(f"invalid crop size: {crop_spec.output_size}")
    if canvas_w <= 0 or canvas_h <= 0:
        raise ValueError(f"invalid canvas size: {canvas_size}")
    scale = min(canvas_w / source_w, canvas_h / source_h)
    content_w = max(1, round(source_w * scale))
    content_h = max(1, round(source_h * scale))
    left = (canvas_w - content_w) // 2
    top = (canvas_h - content_h) // 2
    content_xyxy = (left, top, left + content_w, top + content_h)
    edit_xyxy_in_canvas = scale_box(
        crop_spec.edit_xyxy_in_crop,
        scale,
        (left, top),
        canvas_size,
    )
    return CanvasSpec(
        size=canvas_size,
        source_size=crop_spec.output_size,
        content_xyxy=content_xyxy,
        edit_xyxy_in_canvas=edit_xyxy_in_canvas,
        scale=scale,
    )


def letterbox_crop(crop: Image.Image, canvas_spec: CanvasSpec, fill: tuple[int, int, int, int] = (0, 0, 0, 255)) -> Image.Image:
    canvas = Image.new("RGBA", canvas_spec.size, fill)
    x1, y1, x2, y2 = canvas_spec.content_xyxy
    fitted = crop.convert("RGBA").resize((x2 - x1, y2 - y1), Image.Resampling.LANCZOS)
    canvas.alpha_composite(fitted, (x1, y1))
    return canvas


def restore_letterboxed_content(canvas: Image.Image, canvas_spec: CanvasSpec) -> Image.Image:
    x1, y1, x2, y2 = canvas_spec.content_xyxy
    content = canvas.convert("RGBA").crop((x1, y1, x2, y2))
    if content.size != canvas_spec.source_size:
        content = content.resize(canvas_spec.source_size, Image.Resampling.LANCZOS)
    return content


def draw_guide_crop(crop: Image.Image, crop_spec: CropSpec, label: str | None = None) -> Image.Image:
    guide = crop.convert("RGBA").copy()
    draw = ImageDraw.Draw(guide)
    x1, y1, x2, y2 = crop_spec.edit_xyxy_in_crop
    line_w = max(2, min(5, round(min(guide.size) / 60)))
    draw.rectangle((x1, y1, x2, y2), outline=(230, 126, 34, 255), width=line_w)
    return guide


def draw_guide_canvas(clean_canvas: Image.Image, canvas_spec: CanvasSpec) -> Image.Image:
    guide = clean_canvas.convert("RGBA").copy()
    draw = ImageDraw.Draw(guide)
    x1, y1, x2, y2 = canvas_spec.edit_xyxy_in_canvas
    draw.rectangle((x1, y1, x2, y2), outline=(255, 127, 14, 255), width=4)
    return guide
