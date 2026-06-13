#!/usr/bin/env python3
"""NoThink Direct vs CoT bar chart (tab:cot in paper).

Reads data from result files automatically.
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
CONTAM_DIR = ROOT / "results" / "contamination_audit" / "original_vs_relabel"
DYNEVAL_DIR = ROOT / "results" / "dynamic_eval"

FINAL_RE = re.compile(r"(?<![a-zA-Z])\(?([A-Da-d])\)?(?![a-zA-Z])")


def load_acc(path: Path) -> float:
    rows = [json.loads(l) for l in path.open() if l.strip()]
    by_id = {}
    for r in rows:
        k = r.get("question_id", r.get("image_id"))
        raw = r.get("content", "") or r.get("raw_response", "")
        if raw or r.get("correct") is not None:
            by_id[k] = r
    correct = sum(1 for r in by_id.values() if r.get("correct"))
    return correct / len(by_id) * 100 if by_id else 0.0


def rekey_mean_std(key: str, suffix: str) -> tuple[float, float]:
    accs = []
    for b in [1, 2, 3]:
        f = DYNEVAL_DIR / f"{key}{suffix}_bench{b}.jsonl"
        if f.exists():
            accs.append(load_acc(f))
    return float(np.mean(accs)), float(np.std(accs, ddof=1)) if len(accs) > 1 else 0.0


MODELS = [
    ("seed20lite", "Seed-2.0\nLite"),
    ("kimi", "Kimi\nK2.6"),
    ("mimo25", "MiMo\nv2.5"),
    ("qwen36plus", "Qwen3.6\nPlus"),
]

orig_direct, orig_cot = [], []
rekey_direct_m, rekey_direct_e = [], []
rekey_cot_m, rekey_cot_e = [], []

for key, _ in MODELS:
    orig_direct.append(load_acc(CONTAM_DIR / f"{key}_noreason_original.jsonl"))
    orig_cot.append(load_acc(CONTAM_DIR / f"{key}_noreason_cot_original.jsonl"))
    m, s = rekey_mean_std(key, "_noreason")
    rekey_direct_m.append(m)
    rekey_direct_e.append(s)
    m, s = rekey_mean_std(key, "_noreason_cot")
    rekey_cot_m.append(m)
    rekey_cot_e.append(s)

orig_direct = np.array(orig_direct)
orig_cot = np.array(orig_cot)
rekey_direct_m = np.array(rekey_direct_m)
rekey_direct_e = np.array(rekey_direct_e)
rekey_cot_m = np.array(rekey_cot_m)
rekey_cot_e = np.array(rekey_cot_e)

model_labels = [m[1] for m in MODELS]

plt.rcParams.update({
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.family": "DejaVu Serif",
    "axes.linewidth": 1.0,
})

x = np.arange(len(model_labels))
width = 0.19
fig, ax = plt.subplots(figsize=(7.5, 3.6))

colors = ["#c7dcf0", "#7ba3d4", "#f0d0d0", "#d47b7b"]
edges  = ["#5f83d4", "#2c5aa0", "#d45f5f", "#a02c2c"]
labels = ["Original (Direct)", "Original (CoT)",
          "ReKey (Direct)", "ReKey (CoT)"]
vals = [orig_direct, orig_cot, rekey_direct_m, rekey_cot_m]
errs = [None, None, rekey_direct_e, rekey_cot_e]

for i, (y, err, label) in enumerate(zip(vals, errs, labels)):
    offset = (i - 1.5) * width
    kw = dict(
        width=width, label=label,
        color=colors[i], edgecolor=edges[i],
        linewidth=1.2, alpha=0.9,
    )
    if err is not None:
        kw.update(yerr=err, capsize=3,
                  error_kw=dict(linewidth=1.0, capthick=1.0, ecolor=edges[i]))
    bars = ax.bar(x + offset, y, **kw)
    for bar, val in zip(bars, y):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.6,
                f"{val:.1f}", ha="center", va="bottom",
                fontsize=7, fontweight="bold", color=edges[i])

ax.set_ylabel("Accuracy (%)", fontsize=12, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(model_labels, fontsize=10)
ax.set_ylim(55, 100)
ax.tick_params(axis="y", labelsize=9)
ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.3)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.legend(frameon=True, fontsize=8, loc="upper right",
          ncol=2, handlelength=1.0, columnspacing=1.0)

plt.tight_layout()
out = Path(__file__).parent
fig.savefig(out / "nothink_cot.pdf", bbox_inches="tight")
fig.savefig(out / "nothink_cot.png", dpi=300, bbox_inches="tight")
print(f"Saved to {out}/nothink_cot.{{pdf,png}}")
plt.close()
