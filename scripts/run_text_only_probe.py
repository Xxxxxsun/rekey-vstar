#!/usr/bin/env python3
"""Text-only probing: send V*Bench questions WITHOUT images to test memorization.

For each question, sends only the system prompt + question text (no image).
Runs multiple repeats at low temperature to measure answer bias.

Usage:
    python scripts/run_text_only_probe.py \
        --model qwen/qwen3.6-plus \
        --out results/contamination_audit/no_image_probing/qwen36plus_text_probe.jsonl \
        --repeats 20 --temperature 0.1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests
import pandas as pd
from huggingface_hub import hf_hub_download

API_URL = "https://openrouter.ai/api/v1/chat/completions"
REPO_ID = "lmms-lab/vstar-bench"
FILENAME = "data/test-00000-of-00001.parquet"
REVISION = "b44023b4dca749ed8a76b85eb576627d05a1c174"

OPTION_RE = re.compile(r"\(([A-D])\)")
CHOICE_RE = re.compile(r"(?<![a-zA-Z])\(?([A-Da-d])\)?(?![a-zA-Z])")
LOCK = threading.Lock()


def load_questions() -> list[dict[str, Any]]:
    parquet_path = hf_hub_download(repo_id=REPO_ID, repo_type="dataset",
                                    filename=FILENAME, revision=REVISION)
    df = pd.read_parquet(parquet_path)
    items = []
    for _, row in df.iterrows():
        text = str(row["text"])
        question_id = str(row["question_id"])
        label = str(row["label"]).strip()
        category = str(row["category"])
        option_count = len(set(OPTION_RE.findall(text)))
        items.append({
            "question_id": question_id,
            "category": category,
            "label": label,
            "text": text,
            "option_count": option_count,
        })
    return items


def existing_keys(path: Path) -> set[tuple[str, int]]:
    keys = set()
    if path.exists():
        for line in path.open():
            if line.strip():
                r = json.loads(line)
                keys.add((r["question_id"], r["repeat"]))
    return keys


def call_api(api_key: str, model: str, system: str, user_text: str,
             temperature: float, max_tokens: int, timeout: float) -> dict:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    for attempt in range(3):
        try:
            r = requests.post(API_URL, json=body, headers=headers, timeout=timeout)
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            resp = r.json()
            content = (resp["choices"][0]["message"].get("content") or "").strip()
            return {"ok": True, "content": content, "usage": resp.get("usage", {})}
        except Exception as e:
            if attempt == 2:
                return {"ok": False, "error": str(e)}
            time.sleep(3)
    return {"ok": False, "error": "max retries"}


def parse_choice(text: str) -> str:
    matches = CHOICE_RE.findall(text)
    return matches[-1].upper() if matches else ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        raise SystemExit(2)

    items = load_questions()
    if args.limit:
        items = items[:args.limit]

    done = existing_keys(args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    tasks = []
    for item in items:
        for rep in range(args.repeats):
            if (item["question_id"], rep) not in done:
                tasks.append((item, rep))

    if not tasks:
        print("All done.")
        return

    print(f"Running {args.model} text-only probe: {len(tasks)} calls "
          f"({len(items)} items × {args.repeats} repeats)", flush=True)

    oc = item["option_count"]
    if oc <= 2:
        system = "Output exactly one uppercase option letter: A or B. Do not explain."
    else:
        system = "Output exactly one uppercase option letter from A, B, C, or D. Do not explain."

    completed = 0

    def run_one(item, rep):
        result = call_api(api_key, args.model, system, item["text"],
                          args.temperature, args.max_tokens, args.timeout)
        content = result.get("content", "")
        parsed = parse_choice(content)
        row = {
            "model": args.model,
            "question_id": item["question_id"],
            "category": item["category"],
            "label": item["label"],
            "option_count": item["option_count"],
            "repeat": rep,
            "temperature": args.temperature,
            "system": system,
            "variant": "text_only",
            "max_tokens": args.max_tokens,
            "ok": result.get("ok", False),
            "content": content,
            "parsed_choice": parsed,
            "correct": parsed == item["label"],
            "usage": result.get("usage", {}),
        }
        with LOCK:
            with args.out.open("a") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(run_one, item, rep): (item, rep) for item, rep in tasks}
        for future in as_completed(futures):
            completed += 1
            if completed % 200 == 0:
                print(f"  {completed}/{len(tasks)}", flush=True)

    print(f"Done: {completed} calls")

    # Summary
    rows = [json.loads(l) for l in args.out.open() if l.strip()]
    correct = sum(1 for r in rows if r.get("correct"))
    print(f"Overall: {correct}/{len(rows)} ({100*correct/len(rows):.1f}%)")


if __name__ == "__main__":
    main()
