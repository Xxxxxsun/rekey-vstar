from __future__ import annotations

from PIL import Image, ImageChops, ImageFilter

from .schemas import Box, CropSpec


def fit_patch(patch: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    return patch.convert("RGBA").resize(target_size, Image.Resampling.LANCZOS)


def composite_context_crop(
    base_image: Image.Image,
    generated_context_crop: Image.Image,
    crop_spec: CropSpec,
) -> Image.Image:
    base = base_image.convert("RGBA")
    patch = fit_patch(generated_context_crop, crop_spec.output_size)
    out = base.copy()
    out.alpha_composite(patch, (crop_spec.crop_xyxy[0], crop_spec.crop_xyxy[1]))
    return out


def soft_edit_mask(
    crop_size: tuple[int, int],
    edit_xyxy_in_crop: Box,
    expand_px: int = 12,
    blur_px: int = 8,
) -> Image.Image:
    width, height = crop_size
    x1, y1, x2, y2 = edit_xyxy_in_crop
    x1 = max(0, x1 - expand_px)
    y1 = max(0, y1 - expand_px)
    x2 = min(width, x2 + expand_px)
    y2 = min(height, y2 + expand_px)
    mask = Image.new("L", crop_size, 0)
    mask.paste(255, (x1, y1, x2, y2))
    if blur_px > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(blur_px))
    return mask


def composite_generated_crop(
    base_image: Image.Image,
    generated_crop: Image.Image,
    crop_spec: CropSpec,
    mask_expand_px: int = 12,
    mask_blur_px: int = 8,
) -> tuple[Image.Image, Image.Image]:
    base = base_image.convert("RGBA")
    original_crop = base.crop(crop_spec.crop_xyxy)
    patch = fit_patch(generated_crop, crop_spec.output_size)
    mask = soft_edit_mask(
        crop_spec.output_size,
        crop_spec.edit_xyxy_in_crop,
        expand_px=mask_expand_px,
        blur_px=mask_blur_px,
    )
    blended_crop = Image.composite(patch, original_crop, mask)
    out = base.copy()
    out.alpha_composite(blended_crop, (crop_spec.crop_xyxy[0], crop_spec.crop_xyxy[1]))
    return out, mask


def outside_mask_changed(
    original: Image.Image,
    composite: Image.Image,
    crop_spec: CropSpec,
    mask: Image.Image,
) -> bool:
    """Lightweight invariant check used by tests."""
    orig_crop = original.convert("RGBA").crop(crop_spec.crop_xyxy)
    comp_crop = composite.convert("RGBA").crop(crop_spec.crop_xyxy)
    diff = ImageChops.difference(orig_crop, comp_crop).convert("L")
    outside = Image.eval(mask, lambda px: 255 - px)
    outside_diff = Image.composite(diff, Image.new("L", diff.size, 0), outside)
    return outside_diff.getbbox() is not None
