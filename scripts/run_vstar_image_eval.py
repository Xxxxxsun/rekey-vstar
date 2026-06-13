#!/usr/bin/env python3
"""Run V* with images through an OpenRouter multimodal model."""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from huggingface_hub import hf_hub_download
from PIL import Image


API_URL = "https://openrouter.ai/api/v1/chat/completions"
REPO_ID = "lmms-lab/vstar-bench"
FILENAME = "data/test-00000-of-00001.parquet"
REVISION = "b44023b4dca749ed8a76b85eb576627d05a1c174"
DIRECT_SYSTEM = (
    "You answer visual multiple-choice questions using the provided image. "
    "Output exactly one uppercase option letter and nothing else. "
    "If the choices are A-D, output one of A, B, C, or D. "
    "If the choices are only A-B, output A or B."
)
VERBOSE_SYSTEM = (
    "You answer visual multiple-choice questions using the provided image. "
    "You may explain your reasoning, but you must end with a separate line in the exact format "
    "'Final answer: X', where X is one allowed option letter."
)
BRIEF_REASONING_SYSTEM = (
    "You answer visual multiple-choice questions using the provided image. "
    "Give one short sentence of visible reasoning, then end with a separate line in the exact format "
    "'Final answer: X', where X is one allowed option letter."
)
FINAL_RE = re.compile(r"(?<![a-zA-Z])\(?([A-Da-d])\)?(?![a-zA-Z])")
COT_ANSWER_RE = re.compile(r"(?:answer|final answer)\s*[:：]\s*\(?([A-D])\)?", re.I)
OPTION_RE = re.compile(r"\(([A-D])\)")
OPTION_BLOCK_RE = re.compile(r"\(([A-D])\)\s*(.*?)(?=\s+\([A-D]\)|$)", re.S)
ANSWER_SUFFIX_RE = re.compile(r"\s*Answer with the option's letter.*$", re.I | re.S)
ANSWER_SUFFIX = "Answer with the option's letter from the given choices directly."
COT_SUFFIX = "Think step by step, then answer with the option's letter from the given choices."


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_options(text: str) -> str:
    no_suffix = ANSWER_SUFFIX_RE.sub("", text)
    options = OPTION_BLOCK_RE.findall(normalize_space(no_suffix))
    return " ".join(f"({letter}) {normalize_space(value)}" for letter, value in options)


def extract_stem(text: str) -> str:
    no_suffix = ANSWER_SUFFIX_RE.sub("", text)
    return normalize_space(re.split(r"\s+\(A\)\s+", no_suffix, maxsplit=1)[0])


def format_options(options: dict[str, str]) -> str:
    letters = [letter for letter in ["A", "B", "C", "D"] if letter in options]
    return " ".join(f"({letter}) {normalize_space(str(options[letter]))}" for letter in letters)


def build_raw_prompt(question: str, options: dict[str, str], suffix: str | None = None) -> str:
    return f"{normalize_space(question)} {format_options(options)} {suffix or ANSWER_SUFFIX}"


def build_prompt(text: str, option_count: int, prompt_mode: str, response_mode: str, suffix: str | None = None) -> str:
    if prompt_mode == "options_only":
        question = extract_options(text)
    elif prompt_mode == "question_options":
        question = normalize_space(ANSWER_SUFFIX_RE.sub("", text))
    elif prompt_mode == "raw_text":
        if suffix:
            return ANSWER_SUFFIX_RE.sub(f" {suffix}", normalize_space(text))
        return normalize_space(text)
    elif prompt_mode == "relabeled_raw_text":
        if suffix:
            return ANSWER_SUFFIX_RE.sub(f" {suffix}", normalize_space(text))
        return normalize_space(text)
    elif prompt_mode == "rephrased_question_options":
        raise ValueError("rephrased_question_options requires build_prompt_from_parts")
    else:
        raise ValueError(f"Unknown prompt_mode: {prompt_mode}")

    if option_count <= 2:
        if response_mode in {"verbose", "brief_reasoning"}:
            if response_mode == "brief_reasoning":
                instruction = "Use the image and choose from A or B. Give one short sentence of reasoning, then end with 'Final answer: A' or 'Final answer: B'. You must answer now."
            else:
                instruction = "Use the image and choose from A or B. You may explain. End with 'Final answer: A' or 'Final answer: B'. You must answer now."
        else:
            instruction = "Use the image. Answer with exactly one option letter: A or B. You must answer now."
    else:
        if response_mode in {"verbose", "brief_reasoning"}:
            if response_mode == "brief_reasoning":
                instruction = "Use the image and choose from A, B, C, or D. Give one short sentence of reasoning, then end with 'Final answer: A', 'Final answer: B', 'Final answer: C', or 'Final answer: D'. You must answer now."
            else:
                instruction = "Use the image and choose from A, B, C, or D. You may explain. End with 'Final answer: A', 'Final answer: B', 'Final answer: C', or 'Final answer: D'. You must answer now."
        else:
            instruction = "Use the image. Answer with exactly one option letter: A, B, C, or D. You must answer now."
    return f"{question}\n\n{instruction}"


def build_prompt_from_parts(question: str, options: str, option_count: int, response_mode: str) -> str:
    base = f"{normalize_space(question)} {normalize_space(options)}"
    if option_count <= 2:
        if response_mode == "direct":
            instruction = "Use the image. Answer with exactly one option letter: A or B. You must answer now."
        else:
            instruction = "Use the image and choose from A or B. Give one short sentence of reasoning, then end with 'Final answer: A' or 'Final answer: B'. You must answer now."
    else:
        if response_mode == "direct":
            instruction = "Use the image. Answer with exactly one option letter: A, B, C, or D. You must answer now."
        else:
            instruction = "Use the image and choose from A, B, C, or D. Give one short sentence of reasoning, then end with 'Final answer: A', 'Final answer: B', 'Final answer: C', or 'Final answer: D'. You must answer now."
    return f"{base}\n\n{instruction}"


def build_rephrased_raw_prompt(question: str, options: str) -> str:
    return f"{normalize_space(question)} {normalize_space(options)} {ANSWER_SUFFIX}"


def parse_choice(text: str | None, mode: str = "direct") -> str | None:
    text = (text or "").strip()
    if mode == "cot":
        matches = list(COT_ANSWER_RE.finditer(text))
        if matches:
            return matches[-1].group(1).upper()
    matches = list(FINAL_RE.finditer(text))
    return matches[-1].group(1).upper() if matches else None


def image_data_url(image_bytes: bytes, max_side: int, quality: int) -> tuple[str, dict[str, Any]]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    original_size = image.size
    if max(image.size) > max_side:
        image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=quality, optimize=True)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    metadata = {
        "original_size": original_size,
        "sent_size": image.size,
        "original_bytes": len(image_bytes),
        "sent_bytes": len(output.getvalue()),
    }
    return f"data:image/jpeg;base64,{encoded}", metadata


def original_image_data_url(image_bytes: bytes) -> tuple[str, dict[str, Any]]:
    image = Image.open(io.BytesIO(image_bytes))
    image_format = (image.format or "jpeg").lower()
    if image_format == "jpg":
        image_format = "jpeg"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    metadata = {
        "original_size": image.size,
        "sent_size": image.size,
        "original_bytes": len(image_bytes),
        "sent_bytes": len(image_bytes),
        "image_format": image_format,
        "reencoded": False,
    }
    return f"data:image/{image_format};base64,{encoded}", metadata


def load_rows(limit: int | None = None) -> list[dict[str, Any]]:
    parquet_path = hf_hub_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        filename=FILENAME,
        revision=REVISION,
    )
    df = pd.read_parquet(parquet_path)
    if limit:
        df = df.head(limit)

    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        text = str(row["text"])
        option_count = len(set(OPTION_RE.findall(text)))
        rows.append(
            {
                "question_id": str(row["question_id"]),
                "category": str(row["category"]),
                "label": str(row["label"]).strip(),
                "text": text,
                "original_question": extract_stem(text),
                "options_text": extract_options(text),
                "option_count": option_count,
                "image_bytes": row["image"]["bytes"],
            }
        )
    return rows


def load_rephrases(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    mapping = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                mapping[str(row["question_id"])] = str(row["rephrased_question"])
    return mapping


def load_relabels(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    latest: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                latest[str(row["question_id"])] = row
    return latest


def apply_relabels(rows: list[dict[str, Any]], relabels: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    missing = [row["question_id"] for row in rows if row["question_id"] not in relabels]
    if missing:
        raise SystemExit(f"Missing relabel annotations for question_ids: {missing[:10]}")

    out: list[dict[str, Any]] = []
    for row in rows:
        annotation = relabels[row["question_id"]]
        question = normalize_space(str(annotation["corrected_question"]))
        options = {
            letter: normalize_space(str(value))
            for letter, value in (annotation.get("corrected_options") or {}).items()
            if letter in {"A", "B", "C", "D"}
        }
        label = str(annotation["correct_label"]).strip().upper()
        if label not in options:
            raise SystemExit(f"Relabel for qid={row['question_id']} has label {label} outside options")
        new_row = dict(row)
        new_row.update(
            {
                "label": label,
                "text": build_raw_prompt(question, options),
                "original_question": question,
                "options_text": format_options(options),
                "option_count": len(options),
                "relabel": {
                    "dataset_label": annotation.get("dataset_label"),
                    "dataset_answer_text": annotation.get("dataset_answer_text"),
                    "correct_answer_text": annotation.get("correct_answer_text"),
                },
            }
        )
        out.append(new_row)
    return out


def existing_keys(path: Path) -> set[tuple[str, str, int]]:
    """Tasks already completed successfully. Failed rows (ok=false) are not
    counted, so re-running the same command will retry network/provider errors
    while keeping every successful row intact."""
    if not path.exists():
        return set()
    keys = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if not row.get("ok"):
                continue
            keys.add((row["model"], row["question_id"], int(row["repeat"])))
    return keys


def _call_at_max_tokens(
    api_key: str,
    model: str,
    row: dict[str, Any],
    repeat: int,
    temperature: float,
    max_tokens: int,
    max_side: int,
    quality: int,
    prompt_mode: str,
    response_mode: str,
    image_mode: str,
    system_mode: str,
    reasoning_mode: str,
    rephrases: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    if image_mode == "original":
        data_url, image_meta = original_image_data_url(row["image_bytes"])
    else:
        data_url, image_meta = image_data_url(row["image_bytes"], max_side=max_side, quality=quality)
    if prompt_mode == "rephrased_question_options":
        prompt = build_prompt_from_parts(
            rephrases[row["question_id"]],
            row["options_text"],
            row["option_count"],
            response_mode,
        )
    elif prompt_mode == "rephrased_raw_text":
        prompt = build_rephrased_raw_prompt(
            rephrases[row["question_id"]],
            row["options_text"],
        )
    else:
        prompt = build_prompt(row["text"], row["option_count"], prompt_mode, response_mode,
                              suffix=row.get("_prompt_suffix"))
    system = None
    if system_mode != "none":
        if response_mode == "verbose":
            system = VERBOSE_SYSTEM
        elif response_mode == "brief_reasoning":
            system = BRIEF_REASONING_SYSTEM
        else:
            system = DIRECT_SYSTEM
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/qwen-leak-probe",
        "X-Title": "qwen-leak-probe",
    }
    messages: list[dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    )
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "usage": {"include": True},
    }
    if reasoning_mode == "none":
        body["reasoning"] = {"effort": "none", "exclude": True}

    last_error = None
    for attempt in range(5):
        started = time.time()
        try:
            response = requests.post(API_URL, headers=headers, json=body, timeout=timeout)
            result: dict[str, Any] = {
                "model": model,
                "question_id": row["question_id"],
                "category": row["category"],
                "label": row["label"],
                "option_count": row["option_count"],
                "repeat": repeat,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "max_side": max_side,
                "jpeg_quality": quality,
                "prompt_mode": prompt_mode,
                "response_mode": response_mode,
                "image_mode": image_mode,
                "system_mode": system_mode,
                "reasoning_mode": reasoning_mode,
                "original_question": row["original_question"],
                "rephrased_question": rephrases.get(row["question_id"]),
                "image_meta": image_meta,
                "prompt": prompt,
                "http_status": response.status_code,
                "ok": response.ok,
                "elapsed_s": round(time.time() - started, 3),
            }
            try:
                payload = response.json()
            except Exception:
                payload = {"raw": response.text[:1000]}

            if response.ok:
                content = (
                    payload.get("choices", [{}])[0].get("message", {}).get("content")
                    or ""
                ).strip()
                parse_mode = "cot" if row.get("_prompt_suffix") == COT_SUFFIX else "direct"
                parsed = parse_choice(content, mode=parse_mode)
                result.update(
                    {
                        "content": content,
                        "parsed_choice": parsed,
                        "correct": parsed == row["label"],
                        "usage": payload.get("usage"),
                        "id": payload.get("id"),
                        "provider": payload.get("provider"),
                    }
                )
            else:
                result["error"] = payload
            return result
        except Exception as exc:
            last_error = repr(exc)
            time.sleep(1.5 * (attempt + 1))

    return {
        "model": model,
        "question_id": row["question_id"],
        "category": row["category"],
        "label": row["label"],
        "option_count": row["option_count"],
        "repeat": repeat,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "max_side": max_side,
        "jpeg_quality": quality,
        "prompt_mode": prompt_mode,
        "response_mode": response_mode,
        "image_mode": image_mode,
        "system_mode": system_mode,
        "reasoning_mode": reasoning_mode,
        "original_question": row.get("original_question"),
        "rephrased_question": rephrases.get(row["question_id"]),
        "http_status": None,
        "ok": False,
        "elapsed_s": None,
        "error_text": last_error,
    }


def call_model(
    api_key: str,
    model: str,
    row: dict[str, Any],
    repeat: int,
    temperature: float,
    max_tokens_schedule: list[int],
    max_side: int,
    quality: int,
    prompt_mode: str,
    response_mode: str,
    image_mode: str,
    system_mode: str,
    reasoning_mode: str,
    rephrases: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    """Try each max_tokens tier in order; escalate when HTTP 200 but unparsed.

    Stops at the first parsed choice (returning that attempt's row) or at the
    first HTTP failure (returning the error row). The returned row's
    ``usage.cost`` reflects only the final attempt that was kept.
    """
    last: dict[str, Any] = {}
    for tier_index, max_tokens in enumerate(max_tokens_schedule, start=1):
        result = _call_at_max_tokens(
            api_key, model, row, repeat, temperature, max_tokens,
            max_side, quality, prompt_mode, response_mode, image_mode,
            system_mode, reasoning_mode, rephrases, timeout,
        )
        result["tier_attempts"] = tier_index
        last = result
        if not result.get("ok"):
            return result
        if result.get("parsed_choice"):
            return result
    return last


def append_row(path: Path, lock: threading.Lock, row: dict[str, Any]) -> None:
    with lock:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default="qwen/qwen3.6-plus")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument(
        "--max-tokens",
        type=int,
        nargs="+",
        default=[2048],
        help="One or more max_tokens tiers; tries each in order if response is unparsed.",
    )
    parser.add_argument("--max-side", type=int, default=1536)
    parser.add_argument("--jpeg-quality", type=int, default=85)
    parser.add_argument(
        "--prompt-mode",
        choices=[
            "question_options",
            "options_only",
            "rephrased_question_options",
            "raw_text",
            "rephrased_raw_text",
            "relabeled_raw_text",
        ],
        default="question_options",
    )
    parser.add_argument(
        "--response-mode",
        choices=["direct", "verbose", "brief_reasoning"],
        default="direct",
    )
    parser.add_argument("--image-mode", choices=["processed", "original"], default="processed")
    parser.add_argument("--system-mode", choices=["default", "none"], default="default")
    parser.add_argument("--reasoning-mode", choices=["none", "omit"], default="none")
    parser.add_argument("--prompt-suffix", choices=["direct", "cot"], default="direct")
    parser.add_argument("--rephrases", type=Path)
    parser.add_argument("--annotations", type=Path, default=Path("data/annotations/vstar_relabel_latest.jsonl"))
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is not set")

    rows = load_rows(limit=args.limit)
    prompt_suffix = COT_SUFFIX if args.prompt_suffix == "cot" else None
    for row in rows:
        row["_prompt_suffix"] = prompt_suffix
    rephrases = load_rephrases(args.rephrases)
    if args.prompt_mode == "relabeled_raw_text":
        rows = apply_relabels(rows, load_relabels(args.annotations))
    if args.prompt_mode in {"rephrased_question_options", "rephrased_raw_text"}:
        missing = [row["question_id"] for row in rows if row["question_id"] not in rephrases]
        if missing:
            raise SystemExit(f"Missing rephrases for question_ids: {missing[:10]}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    done = existing_keys(args.out)
    tasks = []
    for row in rows:
        for repeat in range(args.repeats):
            key = (args.model, row["question_id"], repeat)
            if key not in done:
                tasks.append((row, repeat))

    print(f"pending={len(tasks)} rows={len(rows)} repeats={args.repeats}", flush=True)
    lock = threading.Lock()
    completed = 0
    correct = 0
    parsed = 0

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(
                call_model,
                api_key,
                args.model,
                row,
                repeat,
                args.temperature,
                args.max_tokens,
                args.max_side,
                args.jpeg_quality,
                args.prompt_mode,
                args.response_mode,
                args.image_mode,
                args.system_mode,
                args.reasoning_mode,
                rephrases,
                args.timeout,
            )
            for row, repeat in tasks
        ]
        for future in as_completed(futures):
            result = future.result()
            append_row(args.out, lock, result)
            completed += 1
            if result.get("parsed_choice"):
                parsed += 1
            if result.get("correct"):
                correct += 1
            if completed % 20 == 0 or completed == len(tasks):
                print(
                    f"completed={completed}/{len(tasks)} parsed={parsed} correct={correct}",
                    flush=True,
                )


if __name__ == "__main__":
    main()
