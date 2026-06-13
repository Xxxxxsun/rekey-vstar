#!/usr/bin/env python3
"""Compute API costs for benchmark generation and VLM evaluation.

Image generation: GPT-Image-2 official pricing (per image).
VLM evaluation: uses OpenRouter cost field from result files.

Usage:
    python scripts/compute_cost.py
"""

import json
import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DYNEVAL_DIR = ROOT / "results" / "dynamic_eval"
CONTAM_DIR = ROOT / "results" / "contamination_audit" / "original_vs_relabel"
BENCH_DIR = ROOT / "results" / "benchmark"

# GPT-Image-2 pricing (https://platform.openai.com/docs/pricing)
# Edit endpoint: per image output
GPT_IMAGE_2_PRICES = {
    "1024x1024": 0.08,
    "1536x1024": 0.08,
    "1024x1536": 0.08,
}
GPT_IMAGE_2_DEFAULT = 0.08  # high quality, standard size


def compute_image_gen_cost():
    """Cost to generate one benchmark instance (191 images)."""
    print("=" * 60)
    print("BENCHMARK GENERATION COST (1 seed = 191 images)")
    print("=" * 60)

    total_edits = 0
    sizes = {}

    for bench in ["bench1"]:
        bench_dir = BENCH_DIR / bench
        for manifest_path in sorted(bench_dir.glob("*/artifacts/manifest.json")):
            try:
                m = json.loads(manifest_path.read_text())
            except Exception:
                continue
            for g in m.get("generations", []):
                total_edits += 1
                canvas = g.get("canvas", {})
                w, h = canvas.get("width", 1024), canvas.get("height", 1024)
                size_key = f"{w}x{h}"
                sizes[size_key] = sizes.get(size_key, 0) + 1

    cost_per_image = GPT_IMAGE_2_DEFAULT
    total_cost = total_edits * cost_per_image

    print(f"\nModel: GPT-Image-2 (edit endpoint)")
    print(f"Total edit API calls per seed: {total_edits}")
    print(f"Size distribution: {dict(sorted(sizes.items()))}")
    print(f"Price per edit: ${cost_per_image:.2f}")
    print(f"Total per seed: ${total_cost:.2f}")
    print(f"Total for 3 seeds: ${total_cost * 3:.2f}")
    return total_cost


def compute_eval_cost():
    """Cost to evaluate all models on one seed."""
    print("\n" + "=" * 60)
    print("VLM EVALUATION COST (1 seed)")
    print("=" * 60)

    # RQ1: 8 standard models × 1 bench
    rq1_models = {
        "qwen36plus": "Qwen3.6-Plus",
        "gpt55": "GPT-5.5",
        "opus47": "Claude Opus 4.7",
        "gemini31pro": "Gemini 3.1 Pro",
        "seed20lite": "Seed-2.0-Lite",
        "kimi": "Kimi K2.6",
        "mimo25": "MiMo v2.5",
        "llama4mav": "Llama 4 Maverick",
    }

    print(f"\n{'Model':<22} {'Items':>5} {'Cost($)':>8} {'$/item':>8} "
          f"{'PromptTok':>10} {'CompTok':>8}")
    print("-" * 70)

    total_rq1 = 0.0
    for key, name in rq1_models.items():
        f = DYNEVAL_DIR / f"{key}_bench1.jsonl"
        if not f.exists():
            continue
        rows = [json.loads(l) for l in f.open() if l.strip()]
        cost = sum(r.get("usage", {}).get("cost", 0) for r in rows)
        prompt_tok = sum(r.get("usage", {}).get("prompt_tokens", 0) for r in rows)
        comp_tok = sum(r.get("usage", {}).get("completion_tokens", 0) for r in rows)
        per_item = cost / len(rows) if rows else 0
        print(f"{name:<22} {len(rows):>5} {cost:>8.3f} {per_item:>8.5f} "
              f"{prompt_tok:>10,} {comp_tok:>8,}")
        total_rq1 += cost

    print(f"{'RQ1 Total (1 seed)':<22} {'':>5} {total_rq1:>8.3f}")

    # Contamination audit: Original + Relabel per model
    print(f"\n--- Contamination Audit (Original + Relabel, one-time) ---")
    print(f"{'Model':<22} {'Orig($)':>8} {'Relab($)':>8} {'Total':>8}")
    print("-" * 50)

    total_contam = 0.0
    for key, name in rq1_models.items():
        orig_cost = 0
        relab_cost = 0
        for suffix, label in [("_original", "orig"), ("_relabel", "relab")]:
            # Try different file naming patterns
            for fname in [f"{key}{suffix}.jsonl",
                          f"{key}_vstar_image_rawprompt_originalimage_t0.jsonl" if "original" in suffix else None,
                          f"{key}_vstar_relabel_current_rawprompt_originalimage_t0.jsonl" if "relabel" in suffix else None]:
                if fname is None:
                    continue
                fp = CONTAM_DIR / fname
                if fp.exists():
                    rows = [json.loads(l) for l in fp.open() if l.strip()]
                    c = sum(r.get("usage", {}).get("cost", 0) for r in rows)
                    if "original" in suffix:
                        orig_cost = c
                    else:
                        relab_cost = c
                    break
        total = orig_cost + relab_cost
        if total > 0:
            print(f"{name:<22} {orig_cost:>8.3f} {relab_cost:>8.3f} {total:>8.3f}")
            total_contam += total

    print(f"{'Contam Total':<22} {'':>8} {'':>8} {total_contam:>8.3f}")

    # NoThink experiment
    print(f"\n--- NoThink Direct + CoT (per model, 1 seed ReKey + Orig + Relab) ---")
    nr_models = ["seed20lite", "kimi", "mimo25", "qwen36plus"]
    total_nr = 0.0
    for key in nr_models:
        cost = 0
        for suffix in ["_noreason_bench1", "_noreason_cot_bench1",
                        "_noreason_original", "_noreason_relabel",
                        "_noreason_cot_original", "_noreason_cot_relabel"]:
            fp = None
            if "bench" in suffix:
                fp = DYNEVAL_DIR / f"{key}{suffix}.jsonl"
            else:
                fp = CONTAM_DIR / f"{key}{suffix}.jsonl"
            if fp and fp.exists():
                rows = [json.loads(l) for l in fp.open() if l.strip()]
                cost += sum((r.get("usage") or {}).get("cost", 0) for r in rows)
        name = rq1_models.get(key, key)
        print(f"  {name}: ${cost:.3f}")
        total_nr += cost
    print(f"  NoThink Total: ${total_nr:.3f}")

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"RQ1 eval (8 models × 1 seed):    ${total_rq1:.2f}")
    print(f"RQ1 eval (8 models × 3 seeds):   ${total_rq1 * 3:.2f}")
    print(f"Contamination audit (one-time):   ${total_contam:.2f}")
    print(f"NoThink experiment (one-time):    ${total_nr:.2f}")
    print(f"Total eval cost:                  ${total_rq1 * 3 + total_contam + total_nr:.2f}")

    return total_rq1


if __name__ == "__main__":
    img_cost = compute_image_gen_cost()
    eval_cost = compute_eval_cost()
