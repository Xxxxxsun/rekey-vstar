from __future__ import annotations

import base64
import io
import os
import re
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageChops, ImageDraw

from .env import load_dotenv


DEFAULT_IMAGE_API_URL = "https://api.openai.com/v1/images/edits"
DEFAULT_IMAGE_MODEL = "gpt-image-2"
DEFAULT_IMAGE_FIELD = "image[]"
EDIT_REGION_RE = re.compile(r"\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]")


class ImageGenerator:
    def generate_edit(
        self,
        prompt: str,
        image_path: Path,
        output_path: Path,
        size: str,
        quality: str,
        n: int = 1,
        reference_image_paths: list[Path] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


class ApiImageGenerator(ImageGenerator):
    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        model: str | None = None,
        timeout: float = 180.0,
    ) -> None:
        load_dotenv()
        self.api_key = api_key or os.environ.get("DYNAMIC_VSTAR_IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.api_url = api_url or os.environ.get("DYNAMIC_VSTAR_IMAGE_API_URL") or DEFAULT_IMAGE_API_URL
        self.model = model or os.environ.get("DYNAMIC_VSTAR_IMAGE_MODEL") or DEFAULT_IMAGE_MODEL
        self.image_field = os.environ.get("DYNAMIC_VSTAR_IMAGE_FIELD") or DEFAULT_IMAGE_FIELD
        self.timeout = timeout
        if not self.api_key:
            raise RuntimeError("Set OPENAI_API_KEY or DYNAMIC_VSTAR_IMAGE_API_KEY to run image edits")

    def generate_edit(
        self,
        prompt: str,
        image_path: Path,
        output_path: Path,
        size: str,
        quality: str,
        n: int = 1,
        reference_image_paths: list[Path] | None = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": str(n),
        }
        image_paths = [image_path, *(reference_image_paths or [])]
        files = []
        handles = []
        for path in image_paths:
            handle = path.open("rb")
            handles.append(handle)
            files.append((self.image_field, (path.name, handle, "image/png")))
        import time as _time
        max_retries = 3
        response = None
        last_error: Exception | None = None
        for attempt in range(max_retries):
            for handle in handles:
                handle.seek(0)
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=self.timeout,
                )
                if response.status_code not in (429, 502, 503, 524):
                    break
                wait = 10 * (attempt + 1)
                print(f"  image API {response.status_code}, retry in {wait}s...")
                _time.sleep(wait)
            except requests.exceptions.Timeout as exc:
                last_error = exc
                if attempt == max_retries - 1:
                    raise
                _time.sleep(10 * (attempt + 1))
        for handle in handles:
            handle.close()
        if response is None:
            raise RuntimeError(f"image API request did not return a response: {last_error}")
        metadata: dict[str, Any] = {
            "api_url": self.api_url,
            "model": self.model,
            "http_status": response.status_code,
            "ok": response.ok,
            "input_image_count": len(image_paths),
            "image_field": self.image_field,
        }
        try:
            payload = response.json()
        except Exception:
            metadata["error_text"] = response.text[:1000]
            response.raise_for_status()
            return metadata
        if not response.ok:
            metadata["error"] = payload
            raise RuntimeError(
                f"image API request failed with HTTP {response.status_code}: "
                f"{str(payload)[:1000]}"
            )

        image_bytes = image_bytes_from_payload(payload)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_bytes)
        metadata["response_id"] = payload.get("id")
        metadata["response_keys"] = sorted(payload.keys())
        return metadata


def image_bytes_from_payload(payload: dict[str, Any]) -> bytes:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise ValueError("image API response missing data[0]")
    first = data[0]
    if not isinstance(first, dict):
        raise ValueError("image API response data[0] is not an object")
    if first.get("b64_json"):
        return base64.b64decode(str(first["b64_json"]))
    if first.get("url"):
        response = requests.get(str(first["url"]), timeout=180.0)
        response.raise_for_status()
        return response.content
    raise ValueError("image API response has neither b64_json nor url")



class FakeImageGenerator(ImageGenerator):
    """Deterministic local generator for dry runs and tests."""

    def generate_edit(
        self,
        prompt: str,
        image_path: Path,
        output_path: Path,
        size: str,
        quality: str,
        n: int = 1,
        reference_image_paths: list[Path] | None = None,
    ) -> dict[str, Any]:
        base_path = reference_image_paths[0] if reference_image_paths else image_path
        with Image.open(base_path) as img:
            patch = img.convert("RGBA")
        guide_img = Image.open(image_path).convert("RGBA")
        diff = ImageChops.difference(patch, guide_img).convert("L")
        bbox = diff.getbbox()
        draw = ImageDraw.Draw(patch, "RGBA")
        w, h = patch.size
        box = bbox or orange_box_from_guide(image_path) or (max(0, w // 3), max(0, h // 3), max(1, 2 * w // 3), max(1, 2 * h // 3))
        draw.ellipse(box, fill=(255, 64, 32, 190), outline=(255, 255, 255, 230), width=2)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        patch.save(output_path)
        return {
            "fake": True,
            "model": "fake-image-generator",
            "size": size,
            "quality": quality,
            "prompt_prefix": prompt[:160],
        }


def orange_box_from_guide(path: Path) -> tuple[int, int, int, int] | None:
    with Image.open(path) as img:
        rgba = img.convert("RGBA")
    pixels = rgba.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            if a > 180 and r > 220 and 80 <= g <= 180 and b < 80:
                xs.append(x)
                ys.append(y)
    if not xs or not ys:
        return None
    return (max(0, min(xs)), max(0, min(ys)), min(rgba.width, max(xs) + 1), min(rgba.height, max(ys) + 1))
