#!/usr/bin/env python3
"""Strip color from position questions in plan.json and regenerate overview.

Usage:
    python scripts/update_position_questions.py
    python scripts/update_position_questions.py --bench-dir results/benchmark/bench1
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image

_POS_COLOR_RE = re.compile(
    r"\bthe ("
    + "|".join(["red", "blue", "yellow", "green", "black", "white",
                 "orange", "purple", "pink", "brown", "gray"])
    + r") "
)


def strip_position_colors(question: str) -> str:
    return _POS_COLOR_RE.sub("the ", question)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bench-dir", type=Path, nargs="+",
                        default=[Path(f"results/benchmark/{b}") for b in ("bench1", "bench2", "bench3")])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Lazy import pipeline for overview regeneration
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from dynamic_vstar.pipeline import write_overview_image
    from dynamic_vstar.schemas import PlanSpec, PlannedEdit

    updated = 0
    for bench_dir in args.bench_dir:
        for item_dir in sorted(bench_dir.iterdir()):
            if not item_dir.is_dir():
                continue
            plan_path = item_dir / "artifacts" / "plan.json"
            if not plan_path.exists():
                continue

            plan_data = json.loads(plan_path.read_text())
            qt = plan_data.get("question_type", "")
            if "position" not in qt:
                continue

            old_q = plan_data["question"]
            new_q = strip_position_colors(old_q)
            if old_q == new_q:
                continue

            if args.dry_run:
                print(f"  {item_dir.name}: {old_q} → {new_q}")
                updated += 1
                continue

            # Update plan.json
            plan_data["question"] = new_q
            plan_path.write_text(json.dumps(plan_data, ensure_ascii=False, indent=2))

            # Regenerate overview
            source_boxed_path = item_dir / "artifacts" / "source_boxed.png"
            composite_path = item_dir / "artifacts" / "composite.jpg"
            if not composite_path.exists():
                composite_path = item_dir / "artifacts" / "composite.png"
            overview_path = item_dir / "overview.png"

            if source_boxed_path.exists() and composite_path.exists():
                boxed = Image.open(source_boxed_path)
                composite = Image.open(composite_path)

                edits = [
                    PlannedEdit(**{k: (v if not isinstance(v, list) else v) for k, v in e.items()})
                    for e in plan_data.get("edits", [])
                ]
                plan_spec = PlanSpec(
                    image_id=plan_data["image_id"],
                    question_id=plan_data.get("question_id"),
                    source_question=plan_data.get("source_question", ""),
                    source_category=plan_data.get("source_category"),
                    edits=edits,
                    question_type=plan_data["question_type"],
                    question=new_q,
                    answer=plan_data["answer"],
                    options=plan_data["options"],
                    correct_label=plan_data["correct_label"],
                    planner_metadata=plan_data.get("planner_metadata", {}),
                )

                # Collect slot images (guide + restored context)
                slot_images = []
                for edit in edits:
                    guide_path = item_dir / "artifacts" / f"guide_context_{edit.slot_id}.png"
                    restored_path = item_dir / "artifacts" / f"restored_context_{edit.slot_id}.png"
                    if guide_path.exists() and restored_path.exists():
                        slot_images.append((edit, Image.open(guide_path), Image.open(restored_path)))

                write_overview_image(overview_path, boxed, composite, plan_spec, slot_images)

            updated += 1

    print(f"{'Would update' if args.dry_run else 'Updated'} {updated} position plans")


if __name__ == "__main__":
    main()
