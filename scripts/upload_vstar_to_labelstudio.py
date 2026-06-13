#!/usr/bin/env python3
"""Upload V* benchmark images from the HF parquet into a Label Studio project.

Mirrors scripts/run_vstar_image_eval.py:load_rows for the data side. For each
image: write the bytes to a temp .jpg, POST it to the project's import
endpoint to create a task, then PATCH the task to attach question_id,
category, original_question (V* parquet stem with options + answer suffix
stripped) and relabel_question (corrected_question from
data/annotations/vstar_relabel_latest.jsonl) onto its `data` so annotators
see both the source and the relabeled prompt above the image.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import tempfile
from pathlib import Path

# Reuse the existing loader rather than duplicating the parquet plumbing.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_vstar_image_eval import load_rows  # noqa: E402

import requests  # noqa: E402
from PIL import Image  # noqa: E402

DEFAULT_RELABEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "annotations"
    / "vstar_relabel_latest.jsonl"
)


def image_id_for(question_id: str) -> str:
    return f"vstar_{int(question_id):04d}"


def load_relabel_questions(path: Path) -> dict[str, str]:
    """Index corrected_question by question_id; returns {} when file missing."""
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            qid = str(row.get("question_id"))
            corrected = row.get("corrected_question")
            if qid and corrected:
                out[qid] = str(corrected).strip()
    return out


def to_jpeg_path(image_bytes: bytes, tmpdir: Path, image_id: str) -> Path:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    out = tmpdir / f"{image_id}.jpg"
    image.save(out, format="JPEG", quality=95, optimize=True)
    return out


def upload_one(
    session: requests.Session,
    base_url: str,
    project_id: int,
    image_path: Path,
    extra_data: dict,
    timeout: float,
) -> int:
    # POST as multipart; ?return_task_ids=true so we can PATCH metadata onto it.
    with image_path.open("rb") as f:
        resp = session.post(
            f"{base_url}/api/projects/{project_id}/import",
            params={"return_task_ids": "true"},
            files={"file": (image_path.name, f, "image/jpeg")},
            timeout=timeout,
        )
    resp.raise_for_status()
    payload = resp.json()
    task_ids = payload.get("task_ids") or payload.get("annotations") or []
    if not task_ids:
        raise RuntimeError(f"Import returned no task IDs: {payload}")
    task_id = int(task_ids[0])

    # Fetch the auto-created task data (which has the image URL), merge extras,
    # and PATCH back. PATCHing only `data` would otherwise replace the image.
    get_resp = session.get(f"{base_url}/api/tasks/{task_id}/", timeout=timeout)
    get_resp.raise_for_status()
    task_data = get_resp.json().get("data") or {}
    task_data.update(extra_data)

    patch_resp = session.patch(
        f"{base_url}/api/tasks/{task_id}/",
        json={"data": task_data},
        timeout=timeout,
    )
    patch_resp.raise_for_status()
    return task_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ls-url", required=True, help="e.g. https://label.example.com")
    parser.add_argument("--ls-token", required=True, help="Label Studio API token")
    parser.add_argument("--project-id", type=int, required=True)
    parser.add_argument("--limit", type=int, default=5, help="1..191; default 5 demo images")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument(
        "--relabel-jsonl",
        type=Path,
        default=DEFAULT_RELABEL_PATH,
        help="V* relabel jsonl with corrected_question per question_id",
    )
    args = parser.parse_args()

    if not (1 <= args.limit <= 191):
        raise SystemExit(f"--limit must be in [1, 191], got {args.limit}")
    if args.start_index < 0:
        raise SystemExit("--start-index must be >= 0")

    base_url = args.ls_url.rstrip("/")
    session = requests.Session()
    if args.ls_token.startswith("eyJ"):
        refresh = session.post(
            f"{base_url}/api/token/refresh/",
            json={"refresh": args.ls_token},
            timeout=args.timeout,
        )
        refresh.raise_for_status()
        session.headers.update({"Authorization": f"Bearer {refresh.json()['access']}"})
    else:
        session.headers.update({"Authorization": f"Token {args.ls_token}"})

    end = args.start_index + args.limit
    rows = load_rows(limit=end)[args.start_index : end]
    print(f"loaded {len(rows)} rows (start={args.start_index}, limit={args.limit})", flush=True)
    relabel_questions = load_relabel_questions(args.relabel_jsonl)
    if not relabel_questions:
        print(
            f"  warn: no relabel questions loaded from {args.relabel_jsonl}",
            flush=True,
        )

    created: list[tuple[str, int]] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        for i, row in enumerate(rows):
            image_id = image_id_for(row["question_id"])
            image_path = to_jpeg_path(row["image_bytes"], tmpdir, image_id)
            extra = {
                "image_id": image_id,
                "question_id": row["question_id"],
                "category": row["category"],
                "original_question": row["original_question"],
                "relabel_question": relabel_questions.get(row["question_id"], ""),
            }
            task_id = upload_one(
                session, base_url, args.project_id, image_path, extra, args.timeout
            )
            created.append((image_id, task_id))
            print(f"  [{i + 1}/{len(rows)}] {image_id} -> task {task_id}", flush=True)

    print("\ndone")
    print("image_id,task_id")
    for image_id, task_id in created:
        print(f"{image_id},{task_id}")


if __name__ == "__main__":
    main()
