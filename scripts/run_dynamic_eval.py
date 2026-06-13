#!/usr/bin/env python3
"""Evaluate VLMs on Dynamic V* benchmark using the same format as run_vstar_image_eval.py.

Prompt format matches original V* exactly:
  {question} (A) xxx (B) xxx (C) xxx (D) xxx Answer with the option's letter from the given choices directly.

No system prompt. Full-resolution composite images. Temperature 0.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests
from PIL import Image

API_URL = "https://openrouter.ai/api/v1/chat/completions"
ANSWER_SUFFIX = "Answer with the option's letter from the given choices directly."
COT_SUFFIX = "Think step by step, then answer with the option's letter from the given choices."
FINAL_RE = re.compile(r"(?<![a-zA-Z])\(?([A-Da-d])\)?(?![a-zA-Z])")
COT_ANSWER_RE = re.compile(r"(?:answer|final answer)\s*[:：]\s*\(?([A-D])\)?", re.I)

LOCK = threading.Lock()


def format_prompt(question: str, options: dict[str, str], mode: str = "direct") -> str:
    opts = " ".join(f"({k}) {v}" for k, v in sorted(options.items()))
    suffix = COT_SUFFIX if mode == "cot" else ANSWER_SUFFIX
    return f"{question} {opts} {suffix}"


def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def parse_choice(text: str, mode: str = "direct") -> str:
    if mode == "cot":
        matches = list(COT_ANSWER_RE.finditer(text))
        if matches:
            return matches[-1].group(1).upper()
    matches = list(FINAL_RE.finditer(text))
    return matches[-1].group(1).upper() if matches else ""


def call_model(
    api_key: str,
    model: str,
    prompt: str,
    image_b64: str,
    temperature: float,
    max_tokens: int,
    timeout: float,
    reasoning: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                {"type": "text", "text": prompt},
            ]},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if reasoning is not None:
        payload["reasoning"] = reasoning
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    for attempt in range(3):
        try:
            r = requests.post(API_URL, json=payload, headers=headers, timeout=timeout)
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            resp = r.json()
            content = (resp["choices"][0]["message"].get("content") or "").strip()
            if not content and payload["max_tokens"] < max_tokens * 4:
                payload["max_tokens"] = min(payload["max_tokens"] * 2, max_tokens * 4)
                continue
            return {
                "ok": True,
                "content": content,
                "usage": resp.get("usage", {}),
            }
        except Exception as e:
            if attempt == 2:
                return {"ok": False, "error": str(e)}
            time.sleep(3)
    return {"ok": False, "error": "max retries"}


def append_row(path: Path, row: dict[str, Any]) -> None:
    with LOCK:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def existing_ids(path: Path) -> set[str]:
    ids = set()
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    ids.add(json.loads(line).get("image_id", ""))
    return ids


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate VLMs on Dynamic V* benchmark.")
    parser.add_argument("--eval-dataset", type=Path, required=True, help="eval_dataset.jsonl from full_run")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default="qwen/qwen3.6-plus")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--prompt-mode", choices=["direct", "cot"], default="direct")
    parser.add_argument("--reasoning", choices=["default", "none"], default="default",
                        help="'none' disables reasoning/thinking tokens")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        raise SystemExit(2)

    with args.eval_dataset.open("r") as f:
        items = [json.loads(line) for line in f if line.strip()]

    if args.limit:
        items = items[:args.limit]

    done = existing_ids(args.out)
    items = [i for i in items if i["image_id"] not in done]

    if not items:
        print("All done.")
        return

    print(f"Running {args.model} on {len(items)} items (concurrency={args.concurrency})", flush=True)

    completed = 0
    correct = 0

    bench_dir = args.eval_dataset.parent

    def eval_item(item: dict[str, Any]) -> dict[str, Any]:
        prompt = format_prompt(item["question"], item["options_dict"], mode=args.prompt_mode)
        image_path = item["image_path"]
        if not Path(image_path).is_absolute():
            image_path = str(bench_dir / image_path)
        image_b64 = encode_image(image_path)

        reasoning_param = {"effort": "none"} if args.reasoning == "none" else None
        result = call_model(
            api_key=api_key,
            model=args.model,
            prompt=prompt,
            image_b64=image_b64,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
            reasoning=reasoning_param,
        )
        prediction = parse_choice(result.get("content", ""), mode=args.prompt_mode) if result["ok"] else "ERROR"
        is_correct = prediction == item["correct_label"]

        return {
            "image_id": item["image_id"],
            "question_id": item["question_id"],
            "category": item.get("category", ""),
            "question_type": item["question_type"],
            "question": item["question"],
            "options": item["options"],
            "correct_label": item["correct_label"],
            "answer": item["answer"],
            "model": args.model,
            "prompt": prompt,
            "prompt_mode": args.prompt_mode,
            "response_mode": "direct",
            "system_mode": "none",
            "prediction": prediction,
            "raw_response": result.get("content", ""),
            "correct": is_correct,
            "usage": result.get("usage", {}),
        }

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(eval_item, item): item for item in items}
        for future in as_completed(futures):
            completed += 1
            row = future.result()
            append_row(args.out, row)
            if row["correct"]:
                correct += 1
            if completed % 20 == 0:
                print(f"  {completed}/{len(items)}: {correct}/{completed} ({100*correct/completed:.1f}%)", flush=True)

    # Final summary
    total = completed
    print(f"\n=== {args.model} on Dynamic V* ===")
    print(f"Overall: {correct}/{total} ({100*correct/total:.1f}%)")

    # Category breakdown
    with args.out.open("r") as f:
        all_rows = [json.loads(line) for line in f if line.strip()]
    for qtype in ["color", "position_left_right", "position_above_below"]:
        rows = [r for r in all_rows if r["question_type"] == qtype]
        if rows:
            c = sum(1 for r in rows if r["correct"])
            print(f"  {qtype}: {c}/{len(rows)} ({100*c/len(rows):.1f}%)")


if __name__ == "__main__":
    main()
