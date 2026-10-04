#!/usr/bin/env python3
"""
Deterministic stratified sampler for the ReKey human edit-success audit (ARR rebuttal).

Draws N=200 items from the 573 generated ReKey composites (191 x 3 seeds), stratified by
  question_type (color / position)  x  edit-mode composition (add-only / has-replace),
balanced across the 3 seeds (bench1/2/3), proportional-within-seed by largest-remainder.

Outputs (into paper/emnlp2026/rebuttal/audit/):
  - audit_sample.json  : full per-item + per-slot detail + image paths (repo-root-relative)
  - audit_data.js      : `window.AUDIT_ITEMS = [...]` for the offline HTML scoring tool
  - audit_sample.csv   : flat frozen list (one row per item) for reproducibility

The sample list is frozen by a fixed RNG seed so it is reproducible and cannot be re-drawn
after inspection. Run once; do not re-run after annotation begins.
"""
import json, glob, csv, os, random
from collections import defaultdict, Counter
from math import floor

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "paper/emnlp2026/rebuttal/audit")
SEEDS = ["bench1", "bench2", "bench3"]
SEED_QUOTA = {"bench1": 67, "bench2": 67, "bench3": 66}  # sums to 200
STRATA = ["color__add_only", "color__has_replace",
          "position__add_only", "position__has_replace"]
RNG_SEED = 20260708


def coarse(qt):
    return "color" if qt == "color" else "position"


def load_items():
    items = []
    for seed in SEEDS:
        for pf in sorted(glob.glob(os.path.join(REPO, f"results/benchmark/{seed}/*/artifacts/plan.json"))):
            plan = json.load(open(pf))
            adir = os.path.dirname(pf)
            man_path = os.path.join(adir, "manifest.json")
            man = json.load(open(man_path)) if os.path.exists(man_path) else {}
            edits = plan.get("edits", [])
            modes = [e.get("mode", "?") for e in edits]
            has_rep = "replace" in modes
            qt = plan.get("question_type", "?")
            ck = coarse(qt)
            stratum = f"{ck}__{'has_replace' if has_rep else 'add_only'}"
            rel = lambda p: os.path.relpath(os.path.join(adir, p), REPO)
            items.append({
                "item_id": f"{plan['image_id']}__{seed}",
                "seed": seed,
                "image_id": plan["image_id"],
                "question_id": str(plan.get("question_id", "")),
                "question_type": qt,
                "qtype_coarse": ck,
                "stratum": stratum,
                "n_edits": len(edits),
                "modes": modes,
                "has_replace": has_rep,
                "question": plan.get("question", ""),
                "options": plan.get("options", {}),
                "answer": plan.get("answer", ""),
                "correct_label": plan.get("correct_label", ""),
                "edits": [{
                    "slot_id": e.get("slot_id", ""),
                    "mode": e.get("mode", ""),
                    "target_phrase": e.get("target_phrase", ""),
                    "edit_instruction": e.get("edit_instruction", ""),
                    "attr_answer": e.get("answer", ""),
                } for e in edits],
                "img_source": rel("source.png"),
                "img_source_boxed": rel("source_boxed.png"),
                "img_composite": rel("composite.jpg"),
            })
    return items


def largest_remainder(quota, sizes):
    """Allocate `quota` across keys proportional to sizes, exact integer sum, capped by sizes."""
    total = sum(sizes.values())
    raw = {k: (quota * sizes[k] / total if total else 0) for k in sizes}
    alloc = {k: min(floor(raw[k]), sizes[k]) for k in sizes}
    rem = quota - sum(alloc.values())
    # distribute leftover to largest fractional remainders, respecting caps
    order = sorted(sizes, key=lambda k: (raw[k] - floor(raw[k])), reverse=True)
    i = 0
    while rem > 0:
        k = order[i % len(order)]
        if alloc[k] < sizes[k]:
            alloc[k] += 1
            rem -= 1
        i += 1
        if i > 10000:
            break
    return alloc


def main():
    os.makedirs(OUT, exist_ok=True)
    items = load_items()
    print(f"Loaded {len(items)} items (population).")
    pop = Counter(it["stratum"] for it in items)
    print("Population strata:", dict(pop))

    rng = random.Random(RNG_SEED)
    chosen = []
    realized = defaultdict(Counter)  # seed -> stratum -> n
    for seed in SEEDS:
        pool = defaultdict(list)
        for it in items:
            if it["seed"] == seed:
                pool[it["stratum"]].append(it)
        sizes = {s: len(pool[s]) for s in STRATA}
        alloc = largest_remainder(SEED_QUOTA[seed], sizes)
        for s in STRATA:
            cand = sorted(pool[s], key=lambda x: (x["image_id"], x["question_id"]))
            pick = rng.sample(cand, alloc[s]) if alloc[s] <= len(cand) else cand
            chosen.extend(pick)
            realized[seed][s] = len(pick)

    chosen.sort(key=lambda x: (x["seed"], x["image_id"]))
    assert len(chosen) == sum(SEED_QUOTA.values()), f"got {len(chosen)}"

    # ---- report realized breakdown ----
    print(f"\nSampled {len(chosen)} items. Realized (seed x stratum):")
    tot = Counter()
    for seed in SEEDS:
        row = ", ".join(f"{s.split('__')[0][:3]}/{s.split('__')[1][:3]}={realized[seed][s]}" for s in STRATA)
        print(f"  {seed}: {row}  (sum {sum(realized[seed].values())})")
        for s in STRATA:
            tot[s] += realized[seed][s]
    print("  POOLED:", dict(tot))
    edit_modes = Counter(m for it in chosen for m in it["modes"])
    n_items_with_rep = sum(1 for it in chosen if it["has_replace"])
    print(f"  edit-level: {dict(edit_modes)}  (replace edits = {edit_modes['replace']})")
    print(f"  items containing >=1 replace: {n_items_with_rep}")
    print(f"  slot-level judgments = {sum(it['n_edits'] for it in chosen)}, item-level = {len(chosen)}")

    # ---- write outputs ----
    with open(os.path.join(OUT, "audit_sample.json"), "w") as f:
        json.dump(chosen, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "audit_data.js"), "w") as f:
        f.write("window.AUDIT_ITEMS = ")
        json.dump(chosen, f, ensure_ascii=False)
        f.write(";\n")
    with open(os.path.join(OUT, "audit_sample.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "seed", "image_id", "question_id", "question_type",
                    "stratum", "n_edits", "modes", "has_replace", "question", "answer",
                    "composite_path"])
        for it in chosen:
            w.writerow([it["item_id"], it["seed"], it["image_id"], it["question_id"],
                        it["question_type"], it["stratum"], it["n_edits"],
                        "+".join(it["modes"]), it["has_replace"], it["question"],
                        it["answer"], it["img_composite"]])
    print(f"\nWrote audit_sample.json / audit_data.js / audit_sample.csv to {OUT}")


if __name__ == "__main__":
    main()
