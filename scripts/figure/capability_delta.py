#!/usr/bin/env python3
"""Combined capability delta chart: (a) CoT effect, (b) Agentic effect."""

import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
CONTAM_DIR = ROOT / "results" / "contamination_audit" / "original_vs_relabel"
DYNEVAL_DIR = ROOT / "results" / "dynamic_eval"
AGENTIC = json.load(open(ROOT / "results" / "agentic_eval" / "agentic_summary.json"))


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


def rekey_mean(key: str, suffix: str) -> float:
    accs = []
    for b in [1, 2, 3]:
        f = DYNEVAL_DIR / f"{key}{suffix}_bench{b}.jsonl"
        if f.exists():
            accs.append(load_acc(f))
    return float(np.mean(accs)) if accs else 0.0


# ── (a) CoT data (nothink: CoT − Direct) ──
COT_MODELS = [
    ("seed20lite", "Seed-2.0\nLite"),
    ("mimo25", "MiMo\nv2.5"),
    ("qwen36plus", "Qwen3.6\nPlus"),
]

cot_orig, cot_relab, cot_rekey = [], [], []
for key, _ in COT_MODELS:
    orig_d = load_acc(CONTAM_DIR / f"{key}_noreason_original.jsonl")
    orig_c = load_acc(CONTAM_DIR / f"{key}_noreason_cot_original.jsonl")
    rel_d = load_acc(CONTAM_DIR / f"{key}_noreason_relabel.jsonl")
    rel_c = load_acc(CONTAM_DIR / f"{key}_noreason_cot_relabel.jsonl")
    rekey_d = rekey_mean(key, "_noreason")
    rekey_c = rekey_mean(key, "_noreason_cot")
    cot_orig.append(orig_c - orig_d)
    cot_relab.append(rel_c - rel_d)
    cot_rekey.append(rekey_c - rekey_d)

# ── (b) Agentic data (Agent − Standard) ──
AGENT_MODELS = [
    ("Seed-2.0-Lite",   "Seed-2.0\nLite"),
    ("Gemini 3.1 Pro",  "Gemini\n3.1 Pro"),
    ("Qwen3.6-Plus",    "Qwen3.6\nPlus"),
    ("GPT-5.5",         "GPT\n5.5"),
    ("Claude Opus 4.7", "Claude\nOpus 4.7"),
    ("Kimi K2.6",       "Kimi\nK2.6"),
]

ag_orig, ag_relab, ag_rekey = [], [], []
for key, _ in AGENT_MODELS:
    a = AGENTIC["models"][key]
    s = AGENTIC["standard_comparison"][key]
    ag_orig.append(a["original"] - s["original"])
    ag_relab.append(a["relabel"] - s["relabel"])
    ag_rekey.append(a["rekey_mean"] - s["rekey_mean"])

# ── Palette ──
ORIG_FILL, ORIG_EDGE = "#c0daf0", "#6182cc"
REL_FILL, REL_EDGE = "#9dabd0", "#424d95"
REKEY_FILL, REKEY_EDGE = "#e8b4b4", "#b05050"

# ── Style ──
plt.style.use(["science", "no-latex"])
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial"],
    "font.size": 9,
    "pdf.fonttype": 42,
    "savefig.facecolor": "white",
})

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5.6, 5.0), dpi=600,
                                gridspec_kw={"height_ratios": [3, 6]})
fig.subplots_adjust(hspace=0.35)

w = 0.24
ylim = (-12, 16)


def draw_panel(ax, deltas_o, deltas_r, deltas_k, labels, title):
    x = np.arange(len(labels))
    b1 = ax.bar(x - w, deltas_o, w,
                color=ORIG_FILL, edgecolor=ORIG_EDGE, linewidth=0.7,
                alpha=0.92, label="Original V*", zorder=3)
    b2 = ax.bar(x, deltas_r, w,
                color=REL_FILL, edgecolor=REL_EDGE, linewidth=0.7,
                alpha=0.92, label="Relabel V*", zorder=3)
    b3 = ax.bar(x + w, deltas_k, w,
                color=REKEY_FILL, edgecolor=REKEY_EDGE, linewidth=0.7,
                alpha=0.92, label="ReKey", zorder=3)

    for bars, ec in [(b1, ORIG_EDGE), (b2, REL_EDGE), (b3, REKEY_EDGE)]:
        for bar in bars:
            val = bar.get_height()
            va = "bottom" if val >= 0 else "top"
            ypos = val + 0.3 if val >= 0 else val - 0.3
            ax.text(bar.get_x() + bar.get_width() / 2, ypos,
                    f"{val:+.1f}", ha="center", va=va,
                    fontsize=5.5, color=ec, fontweight="600")

    ax.axhline(y=0, color="#444444", linewidth=0.6, linestyle="-", zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylim(ylim)
    ax.set_xlim(-0.5, len(labels) - 0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.4)
    ax.spines["bottom"].set_linewidth(0.4)
    ax.tick_params(axis="y", labelsize=7.5)
    ax.tick_params(axis="x", length=0)
    ax.yaxis.grid(True, alpha=0.2, linestyle="--", linewidth=0.4, zorder=0)
    ax.set_title(title, fontsize=9, fontweight="bold", loc="left", pad=6)


draw_panel(ax1, cot_orig, cot_relab, cot_rekey,
           [m[1] for m in COT_MODELS],
           "(a) CoT effect: CoT − Direct")
draw_panel(ax2, ag_orig, ag_relab, ag_rekey,
           [m[1] for m in AGENT_MODELS],
           "(b) Agentic effect: Agent − Standard")

handles, labels = ax1.get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.0),
           ncol=3, frameon=True, framealpha=0.9, edgecolor="#e0e0e0",
           fontsize=7.5, handlelength=1.0, borderpad=0.4, handletextpad=0.4)

plt.tight_layout(pad=0.4, rect=[0, 0, 1, 0.95])
out = Path(__file__).parent
fig.savefig(out / "capability_delta.pdf", bbox_inches="tight", dpi=600)
fig.savefig(out / "capability_delta.png", bbox_inches="tight", dpi=600)
print(f"Saved to {out}/capability_delta.{{pdf,png}}")
plt.close()
