#!/usr/bin/env python3
"""Prepare text-only V* probes for leakage experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
from huggingface_hub import hf_hub_download


REPO_ID = "lmms-lab/vstar-bench"
FILENAME = "data/test-00000-of-00001.parquet"
REVISION = "b44023b4dca749ed8a76b85eb576627d05a1c174"
OPTION_RE = re.compile(r"\(([A-D])\)\s*(.*?)(?=\s+\([A-D]\)|\s+Answer with|$)", re.S)
ANSWER_SUFFIX_RE = re.compile(r"\s*Answer with the option's letter.*$", re.I | re.S)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_item(text: str, label: str) -> dict[str, Any]:
    stem = normalize_space(re.split(r"\s+\(A\)\s+", text, maxsplit=1)[0])
    options = {m.group(1): normalize_space(m.group(2)) for m in OPTION_RE.finditer(text)}
    if label not in options:
        raise ValueError(f"Label {label!r} is missing from options in: {text!r}")
    canonical_stem = normalize_space(stem.lower().rstrip(".?"))
    return {
        "stem": stem,
        "canonical_stem": canonical_stem,
        "options": options,
        "answer": options[label],
    }


def format_prompt(stem: str, options: dict[str, str], suffix: str) -> str:
    choices = " ".join(f"({letter}) {options[letter]}" for letter in sorted(options))
    return f"{stem} {choices} {suffix}"


def shuffled_options(
    options: dict[str, str], answer: str, seed: int, question_id: str
) -> tuple[dict[str, str], str]:
    letters = sorted(options)
    values = [options[letter] for letter in letters]
    rnd = random.Random(f"{seed}:{question_id}")
    rnd.shuffle(values)
    shuffled = dict(zip(letters, values))
    target_label = next(letter for letter, value in shuffled.items() if value == answer)
    return shuffled, target_label


def row_record(row: pd.Series) -> dict[str, Any]:
    label = str(row["label"]).strip()
    parsed = parse_item(str(row["text"]), label)
    return {
        "question_id": str(row["question_id"]),
        "category": str(row["category"]),
        "label": label,
        **parsed,
        "source_text": normalize_space(str(row["text"])),
    }


def build_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    records = [row_record(row) for _, row in df.iterrows()]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        groups[rec["canonical_stem"]].append(rec)

    for rec in records:
        group = groups[rec["canonical_stem"]]
        rec["stem_group_size"] = len(group)
        rec["stem_group_labels"] = sorted({item["label"] for item in group})
        rec["stem_group_answers"] = sorted({item["answer"] for item in group})
        rec["is_conflict_group"] = len({item["answer"] for item in group}) > 1
    return records


def make_probe_records(records: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    exact_suffix = "Answer with the option's letter from the given choices directly."
    urgent_suffix = "Answer with the option's letter from the given choices. You must answer now."

    for rec in records:
        base = {
            "source": "vstar-bench",
            "question_id": rec["question_id"],
            "category": rec["category"],
            "stem": rec["stem"],
            "canonical_stem": rec["canonical_stem"],
            "original_label": rec["label"],
            "original_answer": rec["answer"],
            "stem_group_size": rec["stem_group_size"],
            "stem_group_labels": rec["stem_group_labels"],
            "stem_group_answers": rec["stem_group_answers"],
            "is_conflict_group": rec["is_conflict_group"],
        }

        for variant, suffix in (("exact", exact_suffix), ("urgent", urgent_suffix)):
            prompt = format_prompt(rec["stem"], rec["options"], suffix)
            probes.append(
                {
                    **base,
                    "probe_id": stable_probe_id(rec["question_id"], variant, prompt),
                    "variant": variant,
                    "options": rec["options"],
                    "target_label": rec["label"],
                    "target_answer": rec["answer"],
                    "prompt": prompt,
                }
            )

        options, target_label = shuffled_options(
            rec["options"], rec["answer"], seed, rec["question_id"]
        )
        prompt = format_prompt(rec["stem"], options, urgent_suffix)
        probes.append(
            {
                **base,
                "probe_id": stable_probe_id(rec["question_id"], "shuffle", prompt),
                "variant": "shuffle",
                "options": options,
                "target_label": target_label,
                "target_answer": rec["answer"],
                "prompt": prompt,
            }
        )
    return probes


def stable_probe_id(question_id: str, variant: str, prompt: str) -> str:
    digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:10]
    return f"vstar-{question_id}-{variant}-{digest}"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_conflict_groups(path: Path, records: list[dict[str, Any]]) -> None:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        groups[rec["canonical_stem"]].append(rec)

    rows = []
    for stem, items in sorted(groups.items()):
        answers = sorted({item["answer"] for item in items})
        if len(items) <= 1 and len(answers) <= 1:
            continue
        rows.append(
            {
                "canonical_stem": stem,
                "size": len(items),
                "answers": answers,
                "labels": sorted({item["label"] for item in items}),
                "question_ids": [item["question_id"] for item in items],
                "items": [
                    {
                        "question_id": item["question_id"],
                        "label": item["label"],
                        "answer": item["answer"],
                        "options": item["options"],
                    }
                    for item in items
                ],
            }
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data/processed/vstar_probes.jsonl"))
    parser.add_argument(
        "--metadata-out", type=Path, default=Path("data/processed/vstar_metadata.jsonl")
    )
    parser.add_argument(
        "--conflicts-out", type=Path, default=Path("data/processed/vstar_conflicts.json")
    )
    parser.add_argument("--seed", type=int, default=20260428)
    args = parser.parse_args()

    parquet_path = args.input
    if parquet_path is None:
        parquet_path = Path(
            hf_hub_download(
                repo_id=REPO_ID,
                repo_type="dataset",
                filename=FILENAME,
                revision=REVISION,
            )
        )

    df = pd.read_parquet(parquet_path)
    records = build_records(df)
    probes = make_probe_records(records, seed=args.seed)

    write_jsonl(args.metadata_out, records)
    write_jsonl(args.out, probes)
    write_conflict_groups(args.conflicts_out, records)

    n_conflict_items = sum(1 for rec in records if rec["is_conflict_group"])
    n_conflict_groups = len({rec["canonical_stem"] for rec in records if rec["is_conflict_group"]})
    print(f"loaded_rows={len(records)}")
    print(f"probe_rows={len(probes)}")
    print(f"conflict_groups={n_conflict_groups}")
    print(f"conflict_items={n_conflict_items}")
    print(f"wrote={args.out}")
    print(f"wrote={args.metadata_out}")
    print(f"wrote={args.conflicts_out}")


if __name__ == "__main__":
    main()
