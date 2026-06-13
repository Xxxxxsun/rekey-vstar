#!/usr/bin/env python3
"""Build eval_dataset.jsonl from a benchmark generation run.

Reads plan.json from each generated item directory and produces a single
JSONL file compatible with run_dynamic_eval.py.

Usage:
    python scripts/build_eval_dataset.py \
        --bench-dir outputs/dynamic_vstar \
        --out outputs/dynamic_vstar/eval_dataset.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_POS_COLOR_RE = re.compile(
    r"\bthe ("
    + "|".join(["red", "blue", "yellow", "green", "black", "white",
                 "orange", "purple", "pink", "brown", "gray"])
    + r") "
)


def _strip_position_colors(question: str) -> str:
    """Fallback: strip all colors from position question (for old plan.json without operation info)."""
    return _POS_COLOR_RE.sub("the ", question)


def _rebuild_position_question(plan: dict, sample: dict | None) -> str:
    """Rebuild position question: replace objects keep new color, add objects no color.

    Falls back to strip-all if sample.json is unavailable.
    """
    if not sample:
        return _strip_position_colors(plan["question"])

    edits = sample.get("edits", [])
    op_map = {e["slot_id"]: e["operation"] for e in edits}

    sys_path_hack()
    from dynamic_vstar.rule_planner import parse_color, for_position, for_question

    plan_edits = plan.get("edits", [])
    if len(plan_edits) < 2:
        return _strip_position_colors(plan["question"])

    phrases = []
    for pe in plan_edits[:2]:
        sid = pe["slot_id"]
        op = op_map.get(sid, "replace")
        se = next((e for e in edits if e["slot_id"] == sid), None)
        if se and op == "replace":
            phrases.append(for_position(se["target_name"], se["answer"]))
        elif se and op == "add":
            target_ref = se.get("object_name") or se.get("target_name", "")
            phrases.append(for_question(target_ref))
        else:
            phrases.append(pe.get("target_phrase", ""))

    qt = plan.get("question_type", "")
    if "left_right" in qt:
        return f"Is {phrases[0]} to the left or right of {phrases[1]}?"
    else:
        return f"Is {phrases[0]} above or below {phrases[1]}?"


_sys_path_done = False
def sys_path_hack():
    global _sys_path_done
    if not _sys_path_done:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        _sys_path_done = True


def format_options_str(options_dict: dict[str, str]) -> str:
    return " ".join(f"({k}) {v}" for k, v in sorted(options_dict.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build eval dataset from benchmark run.")
    parser.add_argument("--bench-dir", type=Path, required=True, help="Benchmark output directory")
    parser.add_argument("--out", type=Path, help="Output JSONL path (default: bench-dir/eval_dataset.jsonl)")
    args = parser.parse_args()

    out_path = args.out or args.bench_dir / "eval_dataset.jsonl"

    items = []
    for item_dir in sorted(args.bench_dir.iterdir()):
        if not item_dir.is_dir():
            continue
        plan_path = item_dir / "artifacts" / "plan.json"
        composite_path = item_dir / "artifacts" / "composite.jpg"
        if not composite_path.exists():
            composite_path = item_dir / "artifacts" / "composite.png"
        if not plan_path.exists() or not composite_path.exists():
            continue

        with plan_path.open() as f:
            plan = json.load(f)

        options_dict = plan.get("options", {})
        question_type = plan.get("question_type", "")
        category = "direct_attributes" if question_type == "color" else "relative_position"

        question = plan["question"]
        if category == "relative_position":
            sample_path = item_dir / "artifacts" / "sample.json"
            sample = json.load(sample_path.open()) if sample_path.exists() else None
            question = _rebuild_position_question(plan, sample)

        item = {
            "image_id": plan["image_id"],
            "question_id": str(plan.get("question_id", "")),
            "category": category,
            "question_type": question_type,
            "question": question,
            "options": format_options_str(options_dict),
            "options_dict": options_dict,
            "correct_label": plan["correct_label"],
            "answer": plan["answer"],
            "image_path": str(composite_path.relative_to(args.bench_dir)),
        }
        items.append(item)

    items.sort(key=lambda x: int(x["question_id"]) if x["question_id"].isdigit() else x["question_id"])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Summary
    cats = {}
    for item in items:
        c = item["category"]
        cats[c] = cats.get(c, 0) + 1

    print(f"Built {len(items)} items -> {out_path}")
    for c, n in sorted(cats.items()):
        print(f"  {c}: {n}")


if __name__ == "__main__":
    main()
