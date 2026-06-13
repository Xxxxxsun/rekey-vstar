#!/usr/bin/env python3
"""Compute all tables from raw experiment data files.

Produces every table that appears in EXPERIMENT_RESULTS.md, computed
entirely from the data files — no hardcoded numbers.

Usage:
    python scripts/compute_tables.py
"""

import json
import os
import re
import sys
from pathlib import Path

import numpy as np

# ── paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
CONTAM_DIR = ROOT / "results" / "contamination_audit" / "original_vs_relabel"
DYNEVAL_DIR = ROOT / "results" / "dynamic_eval"
VLM_EVAL_DIR = ROOT / "results" / "vlm_annotator" / "bench_vlm_add"

# ── parsing helpers ────────────────────────────────────────────────────

_WORD_BOUNDARY_RE = re.compile(r"(?<![a-zA-Z])\(?([A-Da-d])\)?(?![a-zA-Z])")
_COT_ANSWER_RE = re.compile(
    r"(?:answer|final answer)\s*[:：]\s*\(?([A-D])\)?", re.I
)


def parse_choice_wb(text: str) -> str | None:
    """Word-boundary parse: return the *last* match (upper-cased)."""
    if not text:
        return None
    matches = _WORD_BOUNDARY_RE.findall(text)
    if matches:
        return matches[-1].upper()
    return None


def parse_choice_cot(text: str) -> str | None:
    """CoT parse: try answer-line regex first, then fallback to word-boundary."""
    if not text:
        return None
    m = _COT_ANSWER_RE.findall(text)
    if m:
        return m[-1].upper()
    return parse_choice_wb(text)


# ── data loading ───────────────────────────────────────────────────────

def load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file, returning list of dicts."""
    rows = []
    if not path.exists():
        return rows
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _dedup_key(row: dict) -> str:
    """Return the best dedup key for a row."""
    return row.get("image_id") or row.get("question_id", "")


def dedup_rows(rows: list[dict]) -> list[dict]:
    """Deduplicate by image_id (or question_id), keeping last occurrence."""
    seen = {}
    for i, r in enumerate(rows):
        seen[_dedup_key(r)] = i
    return [rows[i] for i in sorted(seen.values())]


# ── contamination accuracy ────────────────────────────────────────────

def contam_accuracy(path: Path, is_cot: bool = False) -> float | None:
    """Compute accuracy for a contamination audit file.

    Correctness: use `correct` field if present, else parsed_choice == label.
    """
    rows = load_jsonl(path)
    if not rows:
        return None
    rows = dedup_rows(rows)
    correct = 0
    total = 0
    for r in rows:
        content = r.get("content") or r.get("raw_response") or ""
        # skip empty responses
        if not content and "correct" not in r:
            continue
        total += 1
        if "correct" in r:
            if r["correct"]:
                correct += 1
        else:
            label = r.get("label", "").upper()
            if is_cot:
                pred = parse_choice_cot(content)
            else:
                pred = parse_choice_wb(content)
            if pred == label:
                correct += 1
    if total == 0:
        return None
    return 100.0 * correct / total


# ── dynamic eval accuracy ─────────────────────────────────────────────

def dyneval_accuracy(paths: list[Path], category: str | None = None,
                     is_cot: bool = False) -> list[float]:
    """Compute accuracy for each bench seed.

    Returns list of per-seed accuracies.
    """
    accs = []
    for p in paths:
        rows = load_jsonl(p)
        if not rows:
            continue
        rows = dedup_rows(rows)
        correct = 0
        total = 0
        for r in rows:
            if category and r.get("category") != category:
                continue
            raw = r.get("raw_response") or r.get("content") or ""
            if not raw and "correct" not in r:
                continue
            total += 1
            if "correct" in r:
                if r["correct"]:
                    correct += 1
            else:
                label = (r.get("correct_label") or r.get("label", "")).upper()
                if is_cot:
                    pred = parse_choice_cot(raw)
                else:
                    pred = parse_choice_wb(raw)
                if pred == label:
                    correct += 1
        if total > 0:
            accs.append(100.0 * correct / total)
    return accs


def R1(x: float) -> float:
    """Round to 1 decimal place.

    All deltas must be computed as R1(a) - R1(b) so that readers can
    verify by subtracting the displayed table values."""
    return round(x, 1)


def mean_std(vals: list[float]) -> tuple[float, float]:
    """Mean and population std."""
    if not vals:
        return (float("nan"), float("nan"))
    return float(np.mean(vals)), float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0


def fmt_ms(vals: list[float]) -> str:
    """Format mean+-std."""
    m, s = mean_std(vals)
    return f"{m:.1f}+-{s:.1f}"


# ── model display names ───────────────────────────────────────────────

DISPLAY_NAMES = {
    "qwen36plus": "Qwen3.6-Plus",
    "gpt55": "GPT-5.5",
    "opus47": "Claude Opus 4.7",
    "gemini31pro": "Gemini 3.1 Pro",
    "seed20lite": "Seed-2.0-Lite",
    "kimi": "Kimi K2.6",
    "mimo25": "MiMo v2.5",
    "llama4mav": "Llama 4 Maverick",
    "llava15": "LLaVA-1.5-13B",
    "qwen3vl8b": "Qwen3-VL-8B",
    "qwen3vl32b": "Qwen3-VL-32B",
    "qwen3vl235b": "Qwen3-VL-235B",
}


# ══════════════════════════════════════════════════════════════════════
# TABLE 1: Contamination Audit (11 models)
# ══════════════════════════════════════════════════════════════════════

def table_contamination():
    print("=" * 72)
    print("TABLE 1: Contamination Audit")
    print("=" * 72)

    models = [
        "qwen36plus", "gpt55", "opus47", "gemini31pro",
        "seed20lite", "kimi", "mimo25", "llama4mav",
        "qwen3vl8b", "qwen3vl32b", "qwen3vl235b",
    ]

    rows = []
    for m in models:
        orig_path = CONTAM_DIR / f"{m}_original.jsonl"
        relab_path = CONTAM_DIR / f"{m}_relabel.jsonl"
        orig = contam_accuracy(orig_path)
        relab = contam_accuracy(relab_path)
        if orig is not None and relab is not None:
            delta = R1(relab) - R1(orig)
            rows.append((m, orig, relab, delta))
        else:
            rows.append((m, orig, relab, None))

    print()
    print("| Model | Original V* | Relabel V* | Delta |")
    print("|-------|------------|-----------|-------|")
    for m, o, r, d in rows:
        o_s = f"{o:.1f}" if o is not None else "—"
        r_s = f"{r:.1f}" if r is not None else "—"
        d_s = f"{d:+.1f}" if d is not None else "—"
        print(f"| {DISPLAY_NAMES.get(m, m)} | {o_s} | {r_s} | {d_s} |")
    print()

    # Return as dict for use in later tables
    contam = {}
    for m, o, r, d in rows:
        contam[m] = {"original": o, "relabel": r, "delta": d}
    return contam


# ══════════════════════════════════════════════════════════════════════
# TABLE 2: RQ1 Overall + Attr + Position
# ══════════════════════════════════════════════════════════════════════

def table_rq1(contam: dict):
    print("=" * 72)
    print("TABLE 2: RQ1 — Does ReKey Remove Contamination Benefit?")
    print("=" * 72)

    cloud_models = [
        "qwen36plus", "gpt55", "opus47", "gemini31pro",
        "seed20lite", "kimi", "mimo25", "llama4mav",
    ]
    all_models = cloud_models + ["llava15"]

    # LLaVA original from V* paper
    llava_paper = {
        "overall": 48.68,
        "attr": 43.47,
        "pos": 56.57,
    }

    for split_label, category, paper_key in [
        ("Overall", None, "overall"),
        ("Attribute", "direct_attributes", "attr"),
        ("Position", "relative_position", "pos"),
    ]:
        print(f"\n### {split_label}\n")
        print("| Model | Original | Relabel | ReKey (mean+-sigma) | vs Relabel |")
        print("|-------|---------|---------|---------------------|------------|")

        cloud_rekey_means = []

        for m in all_models:
            bench_paths = [
                DYNEVAL_DIR / f"{m}_bench{i}.jsonl" for i in (1, 2, 3)
            ]
            accs = dyneval_accuracy(bench_paths, category=category)
            ms = fmt_ms(accs)
            rekey_mean = mean_std(accs)[0]

            if m == "llava15":
                orig = llava_paper[paper_key]
                relab = None
            else:
                orig = contam.get(m, {}).get("original")
                relab = contam.get(m, {}).get("relabel")

            # For contamination, we need per-category if doing splits
            if category is not None and m != "llava15":
                orig = contam_accuracy_by_cat(
                    CONTAM_DIR / f"{m}_original.jsonl", category
                )
                relab = contam_accuracy_by_cat(
                    CONTAM_DIR / f"{m}_relabel.jsonl", category
                )

            orig_s = f"{orig:.1f}" if orig is not None else "—"
            relab_s = f"{relab:.1f}" if relab is not None else "—"

            if relab is not None and not np.isnan(rekey_mean):
                vs_relab = R1(rekey_mean) - R1(relab)
                vs_relab_s = f"{vs_relab:+.1f}"
            else:
                vs_relab_s = "—"

            print(f"| {DISPLAY_NAMES.get(m, m)} | {orig_s} | {relab_s} | {ms} | {vs_relab_s} |")

            if m in cloud_models and not np.isnan(rekey_mean):
                cloud_rekey_means.append(rekey_mean)

        # Average row for cloud models (overall only)
        if split_label == "Overall":
            avg_orig_vals = [
                contam.get(m, {}).get("original")
                for m in cloud_models
                if contam.get(m, {}).get("original") is not None
            ]
            avg_relab_vals = [
                contam.get(m, {}).get("relabel")
                for m in cloud_models
                if contam.get(m, {}).get("relabel") is not None
            ]
            avg_orig = np.mean(avg_orig_vals) if avg_orig_vals else float("nan")
            avg_relab = np.mean(avg_relab_vals) if avg_relab_vals else float("nan")
            avg_rekey = np.mean(cloud_rekey_means) if cloud_rekey_means else float("nan")
            avg_vs = R1(avg_rekey) - R1(avg_relab) if not np.isnan(avg_relab) else float("nan")
            print(
                f"| *Average* | *{avg_orig:.1f}* | *{avg_relab:.1f}* | "
                f"*{avg_rekey:.1f}* | *{avg_vs:+.1f}* |"
            )

    print()


def contam_accuracy_by_cat(path: Path, category: str,
                           is_cot: bool = False) -> float | None:
    """Compute contamination accuracy filtered to a specific category."""
    rows = load_jsonl(path)
    if not rows:
        return None
    rows = dedup_rows(rows)
    correct = 0
    total = 0
    for r in rows:
        if r.get("category") != category:
            continue
        content = r.get("content") or r.get("raw_response") or ""
        if not content and "correct" not in r:
            continue
        total += 1
        if "correct" in r:
            if r["correct"]:
                correct += 1
        else:
            label = r.get("label", "").upper()
            if is_cot:
                pred = parse_choice_cot(content)
            else:
                pred = parse_choice_wb(content)
            if pred == label:
                correct += 1
    if total == 0:
        return None
    return 100.0 * correct / total


# ══════════════════════════════════════════════════════════════════════
# TABLE 3: RQ2 Difficulty Preservation (LLaVA)
# ══════════════════════════════════════════════════════════════════════

def table_rq2():
    print("=" * 72)
    print("TABLE 3: RQ2 — Difficulty Preservation (LLaVA-1.5-13B)")
    print("=" * 72)

    llava_paper = {
        "overall": 48.68,
        "attr": 43.47,
        "pos": 56.57,
    }

    bench_paths = [DYNEVAL_DIR / f"llava15_bench{i}.jsonl" for i in (1, 2, 3)]

    overall_accs = dyneval_accuracy(bench_paths, category=None)
    attr_accs = dyneval_accuracy(bench_paths, category="direct_attributes")
    pos_accs = dyneval_accuracy(bench_paths, category="relative_position")

    print()
    print("| | Overall | Attr | Position |")
    print("|---|------:|-----:|---------:|")

    print(
        f"| Original V* (paper) | {llava_paper['overall']:.2f} | "
        f"{llava_paper['attr']:.2f} | {llava_paper['pos']:.2f} |"
    )

    o_ms = fmt_ms(overall_accs)
    a_ms = fmt_ms(attr_accs)
    p_ms = fmt_ms(pos_accs)
    print(f"| ReKey (mean+-sigma) | {o_ms} | {a_ms} | {p_ms} |")

    o_m, _ = mean_std(overall_accs)
    a_m, _ = mean_std(attr_accs)
    p_m, _ = mean_std(pos_accs)
    d_o = R1(o_m) - llava_paper["overall"]
    d_a = R1(a_m) - llava_paper["attr"]
    d_p = R1(p_m) - llava_paper["pos"]
    print(f"| Delta | {d_o:+.1f} | {d_a:+.1f} | {d_p:+.1f} |")
    print()


# ══════════════════════════════════════════════════════════════════════
# TABLE 4: Qwen3-VL Scaling + CoT
# ══════════════════════════════════════════════════════════════════════

def table_qwen3vl_scaling():
    print("=" * 72)
    print("TABLE 4: Qwen3-VL Scaling + CoT")
    print("=" * 72)

    models = ["qwen3vl8b", "qwen3vl32b", "qwen3vl235b"]
    modes = [("Direct", "", False), ("CoT", "_cot", True)]

    # ── Table A: Contamination + ReKey overall ──
    print("\n### Table A: Contamination + ReKey Overall\n")
    print("| Model | Mode | Original | Relabel | Delta(contam) | ReKey (mean+-sigma) |")
    print("|-------|------|---------|---------|--------------|---------------------|")

    for m in models:
        for mode_label, suffix, is_cot in modes:
            # Contamination files
            if suffix == "":
                orig_path = CONTAM_DIR / f"{m}_original.jsonl"
                relab_path = CONTAM_DIR / f"{m}_relabel.jsonl"
            else:
                # CoT contamination: {m}_cot_orig.jsonl / {m}_cot_relab.jsonl
                orig_path = CONTAM_DIR / f"{m}_cot_orig.jsonl"
                relab_path = CONTAM_DIR / f"{m}_cot_relab.jsonl"

            orig = contam_accuracy(orig_path, is_cot=is_cot)
            relab = contam_accuracy(relab_path, is_cot=is_cot)
            delta = (R1(relab) - R1(orig)) if (orig is not None and relab is not None) else None

            # Dynamic eval
            bench_paths = [
                DYNEVAL_DIR / f"{m}{suffix}_bench{i}.jsonl" for i in (1, 2, 3)
            ]
            accs = dyneval_accuracy(bench_paths, is_cot=is_cot)
            ms = fmt_ms(accs)

            orig_s = f"{orig:.1f}" if orig is not None else "—"
            relab_s = f"{relab:.1f}" if relab is not None else "—"
            delta_s = f"{delta:+.1f}" if delta is not None else "—"

            print(
                f"| {DISPLAY_NAMES.get(m, m)} | {mode_label} | "
                f"{orig_s} | {relab_s} | {delta_s} | {ms} |"
            )

    # ── Table B: ReKey by category ──
    print("\n### Table B: ReKey by Category\n")
    print("| Model | Mode | Overall | Attr | Position |")
    print("|-------|------|---------|------|----------|")

    for m in models:
        for mode_label, suffix, is_cot in modes:
            bench_paths = [
                DYNEVAL_DIR / f"{m}{suffix}_bench{i}.jsonl" for i in (1, 2, 3)
            ]
            overall = fmt_ms(dyneval_accuracy(bench_paths, category=None, is_cot=is_cot))
            attr = fmt_ms(dyneval_accuracy(bench_paths, category="direct_attributes", is_cot=is_cot))
            pos = fmt_ms(dyneval_accuracy(bench_paths, category="relative_position", is_cot=is_cot))
            print(
                f"| {DISPLAY_NAMES.get(m, m)} | {mode_label} | "
                f"{overall} | {attr} | {pos} |"
            )

    print()


# ══════════════════════════════════════════════════════════════════════
# TABLE 5: NoThink Direct vs CoT (4 models)
# ══════════════════════════════════════════════════════════════════════

def table_nothink():
    print("=" * 72)
    print("TABLE 5: NoThink Direct vs CoT")
    print("=" * 72)

    models = ["seed20lite", "kimi", "mimo25", "qwen36plus"]
    modes = [("Direct", "_noreason", False), ("CoT", "_noreason_cot", True)]

    print()
    print("| Model | Mode | Original | Relabel | Delta(contam) | ReKey (mean+-sigma) |")
    print("|-------|------|---------|---------|--------------|---------------------|")

    for m in models:
        for mode_label, suffix, is_cot in modes:
            # Contamination files
            orig_path = CONTAM_DIR / f"{m}{suffix}_original.jsonl"
            relab_path = CONTAM_DIR / f"{m}{suffix}_relabel.jsonl"

            orig = contam_accuracy(orig_path, is_cot=is_cot)
            relab = contam_accuracy(relab_path, is_cot=is_cot)
            delta = (R1(relab) - R1(orig)) if (orig is not None and relab is not None) else None

            # Dynamic eval
            bench_paths = [
                DYNEVAL_DIR / f"{m}{suffix}_bench{i}.jsonl" for i in (1, 2, 3)
            ]
            accs = dyneval_accuracy(bench_paths, is_cot=is_cot)
            ms = fmt_ms(accs)

            orig_s = f"{orig:.1f}" if orig is not None else "—"
            relab_s = f"{relab:.1f}" if relab is not None else "—"
            delta_s = f"{delta:+.1f}" if delta is not None else "—"

            print(
                f"| {DISPLAY_NAMES.get(m, m)} | {mode_label} | "
                f"{orig_s} | {relab_s} | {delta_s} | {ms} |"
            )

    print()


# ══════════════════════════════════════════════════════════════════════
# TABLE 6: RQ3 VLM Self-Annotation
# ══════════════════════════════════════════════════════════════════════

def table_vlm_annotation(contam: dict):
    print("=" * 72)
    print("TABLE 6: RQ3 — VLM Self-Annotation")
    print("=" * 72)

    models = [
        "qwen36plus", "gpt55", "opus47", "gemini31pro",
        "seed20lite", "kimi", "mimo25", "llama4mav",
    ]

    print()
    print("| Model | Original V* | Human Dynamic | VLM add-only | Delta(Human->VLM) |")
    print("|-------|------------|--------------|-------------|-------------------|")

    for m in models:
        orig = contam.get(m, {}).get("original")

        # Human dynamic = ReKey mean (bench1-3)
        bench_paths = [DYNEVAL_DIR / f"{m}_bench{i}.jsonl" for i in (1, 2, 3)]
        human_accs = dyneval_accuracy(bench_paths)
        human_mean = mean_std(human_accs)[0]

        # VLM add-only
        vlm_path = DYNEVAL_DIR / f"{m}_vlm_add.jsonl"
        vlm_accs = dyneval_accuracy([vlm_path])
        vlm_acc = vlm_accs[0] if vlm_accs else float("nan")

        delta_hv = R1(vlm_acc) - R1(human_mean) if not np.isnan(human_mean) else float("nan")

        orig_s = f"{orig:.1f}" if orig is not None else "—"
        human_s = f"{human_mean:.1f}" if not np.isnan(human_mean) else "—"
        vlm_s = f"{vlm_acc:.1f}" if not np.isnan(vlm_acc) else "—"
        delta_s = f"{delta_hv:+.1f}" if not np.isnan(delta_hv) else "—"

        print(f"| {DISPLAY_NAMES.get(m, m)} | {orig_s} | {human_s} | {vlm_s} | {delta_s} |")

    print()


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    contam = table_contamination()
    table_rq1(contam)
    table_rq2()
    table_qwen3vl_scaling()
    table_nothink()
    table_vlm_annotation(contam)


if __name__ == "__main__":
    main()
