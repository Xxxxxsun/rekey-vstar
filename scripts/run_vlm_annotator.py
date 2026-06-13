#!/usr/bin/env python3
"""Use a VLM (via OpenRouter) to annotate V* images with replace/add slots.

This mimics the human annotation process to test whether VLM annotation
introduces selection bias (picks easier/more salient objects).
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from PIL import Image

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

REPO_ID = "lmms-lab/vstar-bench"
PARQUET_FILENAME = "data/test-00000-of-00001.parquet"
PARQUET_REVISION = "b44023b4dca749ed8a76b85eb576627d05a1c174"
LOCAL_PARQUET = Path("data/raw/test-00000-of-00001.parquet")

MAX_IMAGE_SIZE = 2048

ANNOTATION_PROMPT_TEMPLATE = """\
You are annotating images for a visual search benchmark. The benchmark tests whether VLMs can find small, hidden objects in cluttered scenes.

For reference, the original benchmark question for this image is: "{original_question}"

Your task: annotate this image with 2 REPLACE targets and 2 ADD regions.

## REPLACE targets (2 required)
Find 2 existing objects in the image that:
- Are SMALL or partially hidden (NOT the most prominent objects)
- Are the ONLY one of their kind in the image (uniquely identifiable)
- Have a clear, nameable color
- Would require careful visual search to locate

For each, provide:
- target_ref: MUST follow one of these exact formats:
  - Simple object: "COLOR OBJECT" (e.g., "red bicycle", "white car")
  - Sub-item on person/animal/object: "COLOR ITEM on the OWNER" (e.g., "blue jacket on the cyclist", "orange life vest on the dog")
  - Multi-color: "COLOR1-and-COLOR2 OBJECT" (e.g., "orange-and-white lifebuoy")
  Color MUST be the first word(s). Do NOT use "in a", "with a", "wearing" — always use "on the".
- edit_bbox: tight bounding box around the object [x1, y1, x2, y2] as fractions of image width/height (0.0 to 1.0)
- context_bbox: larger crop area containing the object and its surroundings [x1, y1, x2, y2] (0.0 to 1.0)

## ADD regions (2 required)
Find 2 empty/open areas where a new object could be naturally inserted:
- The area should be relatively small and peripheral (not center-stage)
- Visually plausible for placing everyday objects
- A location that would require visual search to find the added object

For each, provide:
- edit_bbox: the target insertion area [x1, y1, x2, y2] (0.0 to 1.0)
- context_bbox: larger crop area for context [x1, y1, x2, y2] (0.0 to 1.0)
- candidate_objects: 3-5 objects from the allowed list that DO NOT already exist anywhere in this image

Allowed object pool: bag, bucket, umbrella, bottle, box, bicycle, kick scooter, stroller, dog, cat, cup, bowl, phone, flower, poster, sign, clock, flag, boat, duck, kayak, float, balloon

## Output format (strict JSON, no other text):
{
  "replace_slots": [
    {
      "target_ref": "red bicycle",
      "edit_bbox": [0.1, 0.2, 0.15, 0.3],
      "context_bbox": [0.05, 0.1, 0.25, 0.4]
    },
    {
      "target_ref": "white hat on the man",
      "edit_bbox": [0.6, 0.3, 0.65, 0.35],
      "context_bbox": [0.5, 0.2, 0.75, 0.5]
    }
  ],
  "add_slots": [
    {
      "edit_bbox": [0.3, 0.7, 0.38, 0.78],
      "context_bbox": [0.2, 0.6, 0.5, 0.85],
      "candidate_objects": ["dog", "bottle", "bag"]
    },
    {
      "edit_bbox": [0.8, 0.5, 0.88, 0.6],
      "context_bbox": [0.7, 0.4, 0.95, 0.7],
      "candidate_objects": ["clock", "sign", "poster"]
    }
  ]
}"""

JSON_RETRY_SUFFIX = (
    "\n\nIMPORTANT: Your previous response was not valid JSON. "
    "Output ONLY a single JSON object with keys 'replace_slots' and 'add_slots'. "
    "No markdown fences, no explanation, no text outside the JSON."
)

REPLACE_SLOT_IDS = ["A1", "B1"]
ADD_SLOT_IDS = ["C1", "D1"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_parquet() -> pd.DataFrame:
    """Load V* parquet, preferring local cache."""
    if LOCAL_PARQUET.exists():
        return pd.read_parquet(LOCAL_PARQUET)
    from huggingface_hub import hf_hub_download
    path = hf_hub_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        filename=PARQUET_FILENAME,
        revision=PARQUET_REVISION,
    )
    return pd.read_parquet(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def existing_image_ids(path: Path) -> set[str]:
    """Return image_ids already present in the output JSONL for resumption."""
    if not path.exists():
        return set()
    ids: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                ids.add(json.loads(line)["image_id"])
            except (json.JSONDecodeError, KeyError):
                pass
    return ids


# ---------------------------------------------------------------------------
# Image encoding
# ---------------------------------------------------------------------------

def resize_image(img: Image.Image, max_side: int = MAX_IMAGE_SIZE) -> Image.Image:
    """Resize so the longest side is at most max_side pixels."""
    w, h = img.size
    if max(w, h) <= max_side:
        return img
    scale = max_side / max(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    return img.resize((new_w, new_h), Image.LANCZOS)


def encode_image_base64(image_bytes: bytes) -> tuple[str, int, int]:
    """Load image bytes, resize, encode as base64 PNG. Returns (data_uri, width, height)."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    original_w, original_h = img.size
    img = resize_image(img)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    data_uri = f"data:image/png;base64,{b64}"
    return data_uri, original_w, original_h


# ---------------------------------------------------------------------------
# OpenRouter API
# ---------------------------------------------------------------------------

def call_openrouter(
    api_key: str,
    model: str,
    prompt: str,
    image_uri: str,
    timeout: float,
    max_retries: int,
) -> dict[str, Any]:
    """Call OpenRouter with image + text prompt. Returns parsed JSON or error dict."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/dynamic-vstar",
        "X-Title": "dynamic-vstar-vlm-annotator",
    }
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_uri}},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 2000,
    }

    backoff_delays = [10, 20, 30]
    last_error: dict[str, Any] | None = None

    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                OPENROUTER_URL, headers=headers, json=body, timeout=timeout
            )
        except requests.exceptions.Timeout:
            last_error = {"error": "timeout", "attempt": attempt}
            if attempt < max_retries:
                delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                time.sleep(delay)
                continue
            return {"ok": False, **last_error}
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": f"request_exception: {e}"}

        if resp.status_code in (429, 502, 503) and attempt < max_retries:
            delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
            time.sleep(delay)
            last_error = {"error": f"http_{resp.status_code}", "attempt": attempt}
            continue

        if not resp.ok:
            try:
                err_body = resp.json()
            except Exception:
                err_body = resp.text[:500]
            return {"ok": False, "http_status": resp.status_code, "error": err_body}

        try:
            payload = resp.json()
        except Exception:
            return {"ok": False, "error": "json_decode_failed", "raw": resp.text[:500]}

        content = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        usage = payload.get("usage")
        return {"ok": True, "content": content, "usage": usage}

    return {"ok": False, **(last_error or {"error": "max_retries_exceeded"})}


def parse_vlm_json(text: str) -> dict[str, Any] | None:
    """Try to extract a JSON object from the VLM response text."""
    # Strip markdown fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (possibly with language tag)
        first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1 :]
        if cleaned.endswith("```"):
            cleaned = cleaned[: -3].strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and "replace_slots" in parsed and "add_slots" in parsed:
            return parsed
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict) and "replace_slots" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass

    return None


# ---------------------------------------------------------------------------
# Slot conversion
# ---------------------------------------------------------------------------

def norm_to_pixel(bbox_norm: list[float], width: int, height: int) -> list[int]:
    """Convert normalized [x1, y1, x2, y2] (0-1) to pixel coordinates."""
    x1, y1, x2, y2 = bbox_norm
    return [
        int(round(x1 * width)),
        int(round(y1 * height)),
        int(round(x2 * width)),
        int(round(y2 * height)),
    ]


def convert_to_standard_slots(
    vlm_response: dict[str, Any], width: int, height: int
) -> list[dict[str, Any]]:
    """Convert VLM response to our standard slot format."""
    slots: list[dict[str, Any]] = []

    replace_slots = vlm_response.get("replace_slots", [])
    for i, rs in enumerate(replace_slots[:2]):
        slot_id = REPLACE_SLOT_IDS[i]
        edit_bbox = norm_to_pixel(rs["edit_bbox"], width, height)
        context_bbox = norm_to_pixel(rs["context_bbox"], width, height)
        slots.append(
            {
                "slot_id": slot_id,
                "context_region": {"xyxy": context_bbox, "ref": ""},
                "edit_region": {"xyxy": edit_bbox, "mode": "replace"},
                "replace": {
                    "targets": [
                        {
                            "target_ref": rs["target_ref"],
                            "edit_types": ["color_change"],
                        }
                    ]
                },
            }
        )

    add_slots = vlm_response.get("add_slots", [])
    for i, ads in enumerate(add_slots[:2]):
        slot_id = ADD_SLOT_IDS[i]
        edit_bbox = norm_to_pixel(ads["edit_bbox"], width, height)
        context_bbox = norm_to_pixel(ads["context_bbox"], width, height)
        slots.append(
            {
                "slot_id": slot_id,
                "context_region": {"xyxy": context_bbox, "ref": ""},
                "edit_region": {"xyxy": edit_bbox, "mode": "add"},
                "add": {"objects": ads.get("candidate_objects", [])},
            }
        )

    return slots


# ---------------------------------------------------------------------------
# Per-image worker
# ---------------------------------------------------------------------------

def process_one_image(
    api_key: str,
    model: str,
    image_id: str,
    question_id: str,
    category: str,
    image_bytes: bytes,
    original_question: str,
    timeout: float,
    max_retries: int,
) -> dict[str, Any]:
    """Process a single image: encode, call VLM, parse, convert to slots."""
    data_uri, orig_w, orig_h = encode_image_base64(image_bytes)
    prompt = ANNOTATION_PROMPT_TEMPLATE.replace("{original_question}", original_question)

    # First attempt
    result = call_openrouter(
        api_key=api_key,
        model=model,
        prompt=prompt,
        image_uri=data_uri,
        timeout=timeout,
        max_retries=max_retries,
    )

    if not result.get("ok"):
        return {
            "image_id": image_id,
            "question_id": question_id,
            "category": category,
            "vlm_model": model,
            "error": result.get("error", "api_call_failed"),
            "vlm_response": None,
            "slots": [],
        }

    content = result["content"]
    parsed = parse_vlm_json(content)

    # If JSON parsing fails, retry once with reminder
    if parsed is None:
        retry_result = call_openrouter(
            api_key=api_key,
            model=model,
            prompt=prompt + JSON_RETRY_SUFFIX,
            image_uri=data_uri,
            timeout=timeout,
            max_retries=max_retries,
        )
        if retry_result.get("ok"):
            parsed = parse_vlm_json(retry_result["content"])
            content = retry_result["content"]

    if parsed is None:
        return {
            "image_id": image_id,
            "question_id": question_id,
            "category": category,
            "vlm_model": model,
            "error": "json_parse_failed",
            "raw_response": content[:2000],
            "vlm_response": None,
            "slots": [],
        }

    slots = convert_to_standard_slots(parsed, orig_w, orig_h)

    return {
        "image_id": image_id,
        "question_id": question_id,
        "category": category,
        "vlm_model": model,
        "vlm_response": parsed,
        "slots": slots,
    }


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

def draw_annotation_viz(
    image_bytes: bytes,
    slots: list[dict[str, Any]],
    image_id: str,
    out_path: Path,
) -> None:
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", size=22, index=5)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=22)
        except OSError:
            font = ImageFont.load_default()

    BLUE = (31, 119, 180, 200)
    ORANGE = (255, 127, 14, 230)
    GREEN = (44, 160, 44, 230)

    for slot in slots:
        mode = slot["edit_region"]["mode"]
        cx = slot["context_region"]["xyxy"]
        ex = slot["edit_region"]["xyxy"]
        sid = slot["slot_id"]

        draw.rectangle(cx, outline=BLUE, width=3)
        color = ORANGE if mode == "replace" else GREEN
        draw.rectangle(ex, outline=color, width=4)

        if mode == "replace":
            ref = slot["replace"]["targets"][0]["target_ref"]
            label = f"{sid} Replace: {ref}"
        else:
            objs = slot["add"]["objects"]
            label = f"{sid} Add: {', '.join(objs[:4])}"

        tw = draw.textlength(label, font=font)
        ly = max(0, ex[1] - 30)
        draw.rectangle([ex[0], ly, ex[0] + tw + 10, ly + 26], fill=color)
        draw.text((ex[0] + 5, ly + 1), label, font=font, fill=(255, 255, 255))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Use a VLM to annotate V* images with replace/add slots."
    )
    parser.add_argument("--out", type=Path, required=True, help="Output JSONL path")
    parser.add_argument(
        "--model",
        default="openai/gpt-5.5",
        help="OpenRouter model ID (default: openai/gpt-5.5)",
    )
    parser.add_argument(
        "--concurrency", type=int, default=3, help="Parallel requests (default: 3)"
    )
    parser.add_argument("--limit", type=int, help="Max images to process")
    parser.add_argument(
        "--question-ids", help="Comma-separated question IDs to process"
    )
    parser.add_argument(
        "--timeout", type=float, default=120.0, help="API timeout in seconds (default: 120)"
    )
    parser.add_argument(
        "--max-retries", type=int, default=3, help="Retry count for 429/502/503 (default: 3)"
    )
    parser.add_argument(
        "--viz-dir", type=Path, help="Save annotation visualizations to this directory"
    )
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable is not set", file=sys.stderr)
        raise SystemExit(2)

    # Load annotation metadata
    annotations_path = Path("data/annotations/dynamic_vstar_slots_latest.jsonl")
    if not annotations_path.exists():
        print(f"Error: annotation file not found: {annotations_path}", file=sys.stderr)
        raise SystemExit(1)
    annotations = read_jsonl(annotations_path)
    ann_by_qid = {str(a["question_id"]): a for a in annotations}

    # Load images from parquet
    print("Loading V* parquet...", flush=True)
    df = load_parquet()
    print(f"Loaded {len(df)} images from parquet", flush=True)

    # Build work items: one per annotated image
    work_items: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        qid = str(row["question_id"])
        image_id = f"vstar_{int(qid):04d}"
        ann = ann_by_qid.get(qid)
        if ann is None:
            continue
        raw_text = str(row.get("text", ""))
        original_question = raw_text.split("\n")[0].strip()
        work_items.append(
            {
                "image_id": image_id,
                "question_id": qid,
                "category": str(row["category"]),
                "image_bytes": row["image"]["bytes"],
                "original_question": original_question,
            }
        )

    # Apply filters
    if args.question_ids:
        qid_filter = set(args.question_ids.split(","))
        work_items = [w for w in work_items if w["question_id"] in qid_filter]
    if args.limit is not None:
        work_items = work_items[: args.limit]

    # Resume: skip already-processed images
    done = existing_image_ids(args.out)
    work_items = [w for w in work_items if w["image_id"] not in done]

    total = len(work_items)
    if total == 0:
        print("No images to process (all done or none matched filters).", flush=True)
        return

    skipped = len(done)
    if skipped > 0:
        print(f"Resuming: {skipped} already done, {total} remaining", flush=True)
    print(
        f"Processing {total} images with model={args.model}, concurrency={args.concurrency}",
        flush=True,
    )

    # Process images concurrently
    completed = 0
    errors = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        future_to_item = {}
        for item in work_items:
            future = executor.submit(
                process_one_image,
                api_key=api_key,
                model=args.model,
                image_id=item["image_id"],
                question_id=item["question_id"],
                category=item["category"],
                image_bytes=item["image_bytes"],
                original_question=item["original_question"],
                timeout=args.timeout,
                max_retries=args.max_retries,
            )
            future_to_item[future] = item

        for future in as_completed(future_to_item):
            item = future_to_item[future]
            completed += 1
            try:
                result = future.result()
            except Exception as e:
                result = {
                    "image_id": item["image_id"],
                    "question_id": item["question_id"],
                    "category": item["category"],
                    "vlm_model": args.model,
                    "error": f"exception: {e}",
                    "vlm_response": None,
                    "slots": [],
                }

            append_jsonl(args.out, result)

            if args.viz_dir and result.get("slots"):
                try:
                    draw_annotation_viz(
                        image_bytes=item["image_bytes"],
                        slots=result["slots"],
                        image_id=item["image_id"],
                        out_path=args.viz_dir / f"{item['image_id']}_vlm_annot.png",
                    )
                except Exception:
                    pass

            has_error = result.get("error") is not None
            if has_error:
                errors += 1
            status = "error" if has_error else "ok"
            n_slots = len(result.get("slots", []))
            print(
                f"[{completed}/{total}] {item['image_id']}: {status}"
                + (f" ({n_slots} slots)" if not has_error else f" ({result.get('error', '')})"),
                flush=True,
            )

    print(f"\nDone. {completed} processed, {errors} errors. Output: {args.out}", flush=True)


if __name__ == "__main__":
    main()
