#!/usr/bin/env python3
"""Export latest V* relabel annotations and validate label/answer consistency."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def latest_by_qid(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        latest[str(row["question_id"])] = row
    return [latest[qid] for qid in sorted(latest, key=lambda x: int(x))]


def validate(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for row in rows:
        qid = row.get("question_id")
        label = row.get("correct_label")
        options = row.get("corrected_options") or {}
        answer = (row.get("correct_answer_text") or "").strip()
        option_text = (options.get(label) or "").strip() if label else ""
        missing = [
            key
            for key in ["corrected_question", "corrected_options", "correct_label", "correct_answer_text"]
            if not row.get(key)
        ]
        if missing:
            issues.append(f"qid={qid}: missing {', '.join(missing)}")
        if label and option_text != answer:
            issues.append(
                f"qid={qid}: correct_label={label} option_text={option_text!r} "
                f"does not match correct_answer_text={answer!r}"
            )
    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/annotations/vstar_relabel.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("data/annotations/vstar_relabel_latest.jsonl"))
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    latest = latest_by_qid(rows)
    write_jsonl(args.out, latest)

    issues = validate(latest)
    print(f"input_rows={len(rows)}")
    print(f"latest_rows={len(latest)}")
    print(f"wrote={args.out}")
    if issues:
        print("validation_issues:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("validation_issues=0")


if __name__ == "__main__":
    main()
