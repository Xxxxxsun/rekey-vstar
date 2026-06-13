#!/usr/bin/env python3
"""Human vs VLM annotation radar chart (tab:vlm-annotator in paper).

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


def rekey_mean(key: str) -> float:
    accs = []
    for b in [1, 2, 3]:
        f = DYNEVAL_DIR / f"{key}_bench{b}.jsonl"
        if f.exists():
            accs.append(load_acc(f))
    return float(np.mean(accs)) if accs else 0.0


MODELS = [
    ("qwen36plus", "Qwen3.6\nPlus"),
    ("gpt55", "GPT\n5.5"),
    ("opus47", "Claude\nOpus 4.7"),
    ("gemini31pro", "Gemini\n3.1 Pro"),
    ("seed20lite", "Seed-2.0\nLite"),
    ("kimi", "Kimi\nK2.6"),
    ("mimo25", "MiMo\nv2.5"),
    ("llama4mav", "Llama 4\nMaverick"),
]

human_vals = []
vlm_vals = []
for key, _ in MODELS:
    human_vals.append(rekey_mean(key))
    vlm_vals.append(load_acc(DYNEVAL_DIR / f"{key}_vlm_add.jsonl"))

human = np.array(human_vals)
vlm = np.array(vlm_vals)
delta = vlm - human
model_labels = [m[1] for m in MODELS]

plt.rcParams.update({
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.family": "Times New Roman",
    "axes.linewidth": 1.0,
})

num_vars = len(model_labels)
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)
angles_closed = np.concatenate([angles, angles[:1]])
human_closed = np.concatenate([human, human[:1]])
vlm_closed = np.concatenate([vlm, vlm[:1]])

fig = plt.figure(figsize=(5.8, 5.4))
ax = plt.subplot(111, polar=True)
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)

ax.set_ylim(50, 95)
ax.set_yticks([50, 60, 70, 80, 90])
ax.set_yticklabels(["50", "60", "70", "80", "90"], fontsize=11, color="gray")
ax.set_rlabel_position(90)
ax.yaxis.grid(True, linestyle="--", linewidth=1.0, alpha=0.35)
ax.xaxis.grid(True, linestyle="--", linewidth=1.0, alpha=0.28)
ax.spines["polar"].set_linestyle("--")
ax.spines["polar"].set_linewidth(1.2)
ax.spines["polar"].set_color("gray")
ax.spines["polar"].set_alpha(0.8)

ax.set_xticks(angles)
ax.set_xticklabels([])

label_r_list = [98, 100, 100, 100, 98, 101, 99, 100]
ha_list = ["center", "left", "left", "left", "center", "right", "right", "right"]
va_list = ["bottom", "center", "center", "center", "top", "center", "center", "center"]

for angle, label, label_r, ha, va in zip(
    angles, model_labels, label_r_list, ha_list, va_list
):
    ax.text(angle, label_r, label, ha=ha, va=va, fontsize=13,
            fontfamily="Times New Roman", clip_on=False)

human_color = "#4C72B0"
vlm_color = "#DD8452"

ax.plot(angles_closed, human_closed, color=human_color, linewidth=2.5,
        marker="o", markersize=5.5, label="Human")
ax.fill(angles_closed, human_closed, color=human_color, alpha=0.12)

ax.plot(angles_closed, vlm_closed, color=vlm_color, linewidth=2.5,
        marker="s", markersize=5.5, label="VLM")
ax.fill(angles_closed, vlm_closed, color=vlm_color, alpha=0.12)

for i, (angle, h, v, d) in enumerate(zip(angles, human, vlm, delta)):
    r = min(max(h, v) + 3.0, 94.0)
    if i == 0:
        r = 92.0
    elif i == 1:
        r = 91.5
    elif i == 2:
        r = 88.0
    elif i == 7:
        r = 73.5
    ax.text(angle, r, f"+{d:.1f}", ha="center", va="center",
            fontsize=10, fontweight="bold", color="#555555",
            bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                      edgecolor="none", alpha=0.78))

ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2,
          frameon=False, fontsize=13, handlelength=2.4, columnspacing=2.0)

plt.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.18)

out = Path(__file__).parent
fig.savefig(out / "human_vlm_radar.pdf", bbox_inches="tight", pad_inches=0.22)
fig.savefig(out / "human_vlm_radar.png", dpi=300, bbox_inches="tight", pad_inches=0.22)
print(f"Saved to {out}/human_vlm_radar.{{pdf,png}}")
plt.close()
