#!/usr/bin/env python3
"""Attr vs Pos breakdown chart for appendix (fig:dynamic_breakdown)."""

import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
DYNEVAL_DIR = ROOT / "results" / "dynamic_eval"


def load_by_type(path: Path):
    rows = [json.loads(l) for l in path.open() if l.strip()]
    by_id = {}
    for r in rows:
        k = r.get("question_id", r.get("image_id"))
        by_id[k] = r
    attr_c, attr_t, pos_c, pos_t = 0, 0, 0, 0
    for r in by_id.values():
        cat = r.get("category", "")
        if "attribute" in cat:
            attr_t += 1
            if r.get("correct"):
                attr_c += 1
        elif "position" in cat:
            pos_t += 1
            if r.get("correct"):
                pos_c += 1
    attr_acc = attr_c / attr_t * 100 if attr_t else 0
    pos_acc = pos_c / pos_t * 100 if pos_t else 0
    return attr_acc, pos_acc


MODELS = [
    ("qwen36plus", "Qwen3.6\nPlus"),
    ("gpt55", "GPT\n5.5"),
    ("opus47", "Opus\n4.7"),
    ("gemini31pro", "Gemini\n3.1 Pro"),
    ("seed20lite", "Seed-2.0\nLite"),
    ("kimi", "Kimi\nK2.6"),
    ("mimo25", "MiMo\nv2.5"),
    ("llama4mav", "Llama 4\nMaverick"),
]

attr_means, attr_stds = [], []
pos_means, pos_stds = [], []

for key, _ in MODELS:
    a_seeds, p_seeds = [], []
    for b in [1, 2, 3]:
        f = DYNEVAL_DIR / f"{key}_bench{b}.jsonl"
        if f.exists():
            a, p = load_by_type(f)
            a_seeds.append(a)
            p_seeds.append(p)
    attr_means.append(np.mean(a_seeds))
    attr_stds.append(np.std(a_seeds))
    pos_means.append(np.mean(p_seeds))
    pos_stds.append(np.std(p_seeds))

attr_means = np.array(attr_means)
attr_stds = np.array(attr_stds)
pos_means = np.array(pos_means)
pos_stds = np.array(pos_stds)
gaps = pos_means - attr_means
model_labels = [m[1] for m in MODELS]

ATTR_FILL, ATTR_EDGE = "#f0c8a0", "#c07830"
POS_FILL, POS_EDGE = "#a0d0cc", "#308078"
GAP_COLOR = "#555555"

plt.style.use(["science", "no-latex"])
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial"],
    "font.size": 9,
    "pdf.fonttype": 42,
    "savefig.facecolor": "white",
})

fig, ax = plt.subplots(figsize=(5.6, 3.0), dpi=600)

x = np.arange(len(model_labels))
w = 0.33

bars1 = ax.bar(x - w/2, attr_means, w, yerr=attr_stds,
               color=ATTR_FILL, edgecolor=ATTR_EDGE, linewidth=0.7,
               alpha=0.92, label="Attribute", zorder=3,
               error_kw=dict(lw=0.6, capsize=2, capthick=0.6, color=ATTR_EDGE))
bars2 = ax.bar(x + w/2, pos_means, w, yerr=pos_stds,
               color=POS_FILL, edgecolor=POS_EDGE, linewidth=0.7,
               alpha=0.92, label="Position", zorder=3,
               error_kw=dict(lw=0.6, capsize=2, capthick=0.6, color=POS_EDGE))

for i in range(len(model_labels)):
    a, p = attr_means[i], pos_means[i]
    mid_y = (a + p) / 2
    sign = "+" if gaps[i] >= 0 else ""
    ax.text(x[i], mid_y, f"{sign}{gaps[i]:.1f}",
            ha="center", va="center", fontsize=5.5,
            color="white", fontweight="bold", zorder=6,
            bbox=dict(boxstyle="round,pad=0.22", facecolor=GAP_COLOR,
                      edgecolor="none", alpha=0.82))

ax.set_ylabel("ReKey Accuracy (%)", fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(model_labels, fontsize=7.5)
ax.set_ylim(38, 103)
ax.set_xlim(-0.55, len(model_labels) - 0.35)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.4)
ax.spines["bottom"].set_linewidth(0.4)
ax.tick_params(axis="y", labelsize=7.5)
ax.tick_params(axis="x", length=0)
ax.yaxis.grid(True, alpha=0.2, linestyle="--", linewidth=0.4, zorder=0)

leg = ax.legend(loc="upper right", frameon=True, framealpha=0.9,
                edgecolor="#e0e0e0", fontsize=7.5, handlelength=1.0,
                borderpad=0.4, handletextpad=0.4)
leg.get_frame().set_linewidth(0.4)

plt.tight_layout(pad=0.4)
out = Path(__file__).parent
fig.savefig(out / "attr_pos_breakdown.pdf", bbox_inches="tight", dpi=600)
fig.savefig(out / "attr_pos_breakdown.png", bbox_inches="tight", dpi=600)
print(f"Saved to {out}/attr_pos_breakdown.{{pdf,png}}")
plt.close()
