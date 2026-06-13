#!/usr/bin/env python3
"""Run the Dynamic V* crop-generation-paste pipeline."""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from huggingface_hub import hf_hub_download
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dynamic_vstar.image_api import ApiImageGenerator, FakeImageGenerator
from dynamic_vstar.planning import OpenRouterPlanner, RuleBasedPlanner
from dynamic_vstar.pipeline import run_dynamic_item
from dynamic_vstar.schemas import AnnotationRow, annotation_row_from_dict


REPO_ID = "lmms-lab/vstar-bench"
FILENAME = "data/test-00000-of-00001.parquet"
REVISION = "b44023b4dca749ed8a76b85eb576627d05a1c174"
LOCAL_PARQUET = Path("data/raw/test-00000-of-00001.parquet")
ANSWER_SUFFIX_RE = re.compile(r"\s*Answer with the option's letter.*$", re.I | re.S)
OPTION_BLOCK_RE = re.compile(r"\(([A-D])\)\s*(.*?)(?=\s+\([A-D]\)|$)", re.S)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_stem(text: str) -> str:
    no_suffix = ANSWER_SUFFIX_RE.sub("", text)
    return normalize_space(re.split(r"\s+\(A\)\s+", no_suffix, maxsplit=1)[0])


def extract_options(text: str) -> dict[str, str]:
    no_suffix = ANSWER_SUFFIX_RE.sub("", text)
    return {
        letter: normalize_space(value)
        for letter, value in OPTION_BLOCK_RE.findall(normalize_space(no_suffix))
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def parquet_path(path: Path | None = None) -> Path:
    if path:
        return path
    if LOCAL_PARQUET.exists():
        return LOCAL_PARQUET
    return Path(
        hf_hub_download(
            repo_id=REPO_ID,
            repo_type="dataset",
            filename=FILENAME,
            revision=REVISION,
        )
    )


def load_vstar_sources(path: Path | None = None) -> dict[str, dict[str, Any]]:
    df = pd.read_parquet(parquet_path(path))
    out: dict[str, dict[str, Any]] = {}
    for _, row in df.iterrows():
        qid = str(row["question_id"])
        image_id = f"vstar_{int(qid):04d}"
        text = str(row["text"])
        options = extract_options(text)
        label = str(row["label"]).strip()
        record = {
            "question_id": qid,
            "image_id": image_id,
            "category": str(row["category"]),
            "label": label,
            "answer_text": options.get(label),
            "original_question": extract_stem(text),
            "source_text": normalize_space(text),
            "options": options,
            "image_bytes": row["image"]["bytes"],
        }
        out[qid] = record
        out[image_id] = record
    return out


def image_from_record(record: dict[str, Any]) -> Image.Image:
    return Image.open(io.BytesIO(record["image_bytes"])).convert("RGBA")


def merge_source(row: dict[str, Any], sources: dict[str, dict[str, Any]]) -> tuple[AnnotationRow, Image.Image]:
    key = str(row.get("question_id") or row.get("image_id"))
    image_id = str(row.get("image_id"))
    source = sources.get(key) or sources.get(image_id)
    merged = dict(row)
    if source:
        for field in ("original_question", "source_text", "options", "label", "answer_text"):
            if field not in merged and field in source:
                merged[field] = source[field]
        if "category" not in merged and source.get("category"):
            merged["category"] = source["category"]
    annotation = annotation_row_from_dict(merged)
    if not source:
        raise KeyError(f"no source image found for {row.get('image_id')} / qid={row.get('question_id')}")
    return annotation, image_from_record(source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--parquet", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--question-ids", help="Comma-separated question IDs")
    parser.add_argument("--allow-multislot", action="store_true")
    parser.add_argument("--fake-generator", action="store_true")
    parser.add_argument(
        "--planner",
        choices=["rule", "openrouter"],
        default="rule",
        help="Planner backend. 'rule' is deterministic/offline; 'openrouter' uses the OpenRouter Python SDK.",
    )
    parser.add_argument("--planner-model", help="OpenRouter model ID, or DYNAMIC_VSTAR_PLANNER_MODEL")
    parser.add_argument("--planner-temperature", type=float, default=0.2)
    parser.add_argument("--planner-max-tokens", type=int, default=1800)
    parser.add_argument("--planner-timeout", type=float, default=60.0)
    parser.add_argument("--planner-reasoning-effort", help="Optional OpenRouter reasoning effort")
    parser.add_argument("--planner-include-reasoning", action="store_true")
    parser.add_argument("--planner-max-retries", type=int, default=1)
    parser.add_argument(
        "--planner-fallback",
        action="store_true",
        help="Fall back to rule-based planner on LLM errors (off by default; errors are retried then raised).",
    )
    parser.add_argument("--api-url", help="Override DYNAMIC_VSTAR_IMAGE_API_URL")
    parser.add_argument("--api-model", help="Override DYNAMIC_VSTAR_IMAGE_MODEL")
    parser.add_argument(
        "--size",
        default="match",
        help="'match' chooses the closest standard canvas: 1024x1024, 1536x1024, or 1024x1536",
    )
    parser.add_argument("--quality", default="high")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--use-vaw", action="store_true", help="Enable VAW color filtering (default: off)")
    parser.add_argument("--use-mask", action="store_true", help="Enable soft mask compositing (default: off, pastes full crop)")
    args = parser.parse_args()

    rows = read_jsonl(args.annotations)
    if args.question_ids:
        qids = {part.strip() for part in args.question_ids.split(",") if part.strip()}
        rows = [row for row in rows if str(row.get("question_id")) in qids]
    if args.limit is not None:
        rows = rows[: args.limit]

    if not rows:
        raise SystemExit("no annotation rows selected")

    sources = load_vstar_sources(args.parquet)
    generator = (
        FakeImageGenerator()
        if args.fake_generator
        else ApiImageGenerator(api_url=args.api_url, model=args.api_model, timeout=args.timeout)
    )
    planner_backend = (
        RuleBasedPlanner(use_vaw=args.use_vaw, use_mask=args.use_mask)
        if args.planner == "rule"
        else OpenRouterPlanner(
            model=args.planner_model,
            temperature=args.planner_temperature,
            max_tokens=args.planner_max_tokens,
            timeout=args.planner_timeout,
            reasoning_effort=args.planner_reasoning_effort,
            exclude_reasoning=not args.planner_include_reasoning,
            max_retries=args.planner_max_retries,
            fallback_to_rule=args.planner_fallback,
        )
    )
    args.out.mkdir(parents=True, exist_ok=True)

    completed = 0
    for row in rows:
        annotation, source_image = merge_source(row, sources)
        item = run_dynamic_item(
            annotation,
            source_image,
            out_root=args.out,
            run_id=args.run_id,
            generator=generator,
            planner=planner_backend,
            allow_multislot=args.allow_multislot,
            size=args.size,
            quality=args.quality,
        )
        completed += 1
        print(
            f"[{completed}/{len(rows)}] {item.image_id} -> {item.overview_image_path}",
            flush=True,
        )


if __name__ == "__main__":
    main()
