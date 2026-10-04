#!/usr/bin/env python3
"""
Analyze the two-stage ReKey human edit audit -> rebuttal-ready numbers.

Usage:
  python scripts/analyze_edit_audit.py A.csv [B.csv]

Each CSV is the export from score.html, one row per item, columns:
  annotator,item_id,seed,image_id,question_id,question_type,stratum,modes,
  correct_label,stage1_answer,label_match,instruction_compliance,side_effect,side_types,note

Metrics (per plan / [AUDIT: ...]):
  - 标签—图像一致率  = mean(label_match)           (stage-1 blind answer == construction label)
  - 指令符合率       = P(instruction_compliance=符合)  (overall + add/replace)
  - 任务相关副作用率 = P(side_effect!=无)  &  P(side_effect=有·影响作答)
  - 有效编辑率       = label_match & 符合 & side_effect!=有·影响作答
  - Cohen's κ (pre-adjudication) for: stage1_answer, instruction_compliance, side_effect
  - Wilson 95% CI for each rate.
"""
import csv, sys, math, argparse
from collections import Counter, defaultdict

COMPLY_OK = "符合"
SIDE_NONE = "无"
SIDE_BREAK = "有·影响作答"


def read_csv(p):
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (100 * (c - m), 100 * (c + m))


def rate(rows, pred):
    n = len(rows); k = sum(1 for r in rows if pred(r))
    lo, hi = wilson(k, n)
    return f"{100*k/n:5.1f}%  [{lo:.1f}, {hi:.1f}]  ({k}/{n})" if n else "  n/a"


def cohen_kappa(pairs):
    pairs = [(a, b) for a, b in pairs if a != "" and b != ""]
    n = len(pairs)
    if n == 0:
        return None, 0
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    return ((po - pe) / (1 - pe) if pe < 1 else 1.0), po


def is_valid(r):
    return r.get("label_match") in ("1", 1, "True", "true") \
        and r.get("instruction_compliance") == COMPLY_OK \
        and r.get("side_effect") != SIDE_BREAK


def mode_of(r):
    m = r.get("modes", "")
    if "replace" in m and "add" in m: return "mixed"
    if "replace" in m: return "replace"
    if "add" in m: return "add"
    return "?"


def report(rows, tag):
    n = len(rows)
    lm = lambda r: r.get("label_match") in ("1", 1, "True", "true")
    print(f"\n=== [{tag}]  n={n} ===")
    print(f"  标签—图像一致率      : {rate(rows, lm)}")
    print(f"  指令符合率           : {rate(rows, lambda r: r.get('instruction_compliance')==COMPLY_OK)}")
    for md in ("add", "replace"):
        sub = [r for r in rows if mode_of(r) == md]
        if sub:
            print(f"      · {md:8}        : {rate(sub, lambda r: r.get('instruction_compliance')==COMPLY_OK)}")
    print(f"  任务相关副作用率(有) : {rate(rows, lambda r: r.get('side_effect', SIDE_NONE) != SIDE_NONE)}")
    print(f"     其中·影响作答     : {rate(rows, lambda r: r.get('side_effect')==SIDE_BREAK)}")
    print(f"  有效编辑率           : {rate(rows, is_valid)}")
    # side-effect type breakdown
    types = Counter(t for r in rows for t in (r.get("side_types") or "").split("|") if t)
    if types:
        print(f"  副作用类型分布       : " + ", ".join(f"{t} {c}" for t, c in types.most_common()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csvs", nargs="+")
    args = ap.parse_args()
    annots = [read_csv(p) for p in args.csvs]
    names = [(rows[0]["annotator"] if rows and rows[0].get("annotator") else p) for p, rows in zip(args.csvs, annots)]

    for nm, rows in zip(names, annots):
        report(rows, nm)

    if len(annots) >= 2:
        A = {r["item_id"]: r for r in annots[0]}
        B = {r["item_id"]: r for r in annots[1]}
        common = sorted(set(A) & set(B))
        print(f"\n=== 两标注者一致性 κ（裁决前, {names[0]} vs {names[1]}）, {len(common)} 条 ===")
        for field, lbl in [("stage1_answer", "标签—图像(盲答)"),
                            ("instruction_compliance", "指令符合性  "),
                            ("side_effect", "任务相关副作用")]:
            k, po = cohen_kappa([(A[i].get(field, ""), B[i].get(field, "")) for i in common])
            print(f"  {lbl}: κ={k:.3f}  原始一致率={100*po:.1f}%" if k is not None else f"  {lbl}: n/a")
        agree_valid = sum(1 for i in common if is_valid(A[i]) and is_valid(B[i]))
        print(f"  双方均判有效编辑: {agree_valid}/{len(common)}")

    print("\n— [AUDIT: …] 填充模板 —")
    print("  指令符合率 X%（add A%/replace B%）；标签—图像一致率 Y%；任务相关副作用率 Z%；")
    print("  有效编辑率 U%；κ=K1/K2/K3，原始一致率=R1/R2/R3（各率附 95% CI）")
    print("  注：报告采用两人裁决后的比例，κ/原始一致率用裁决前标注。")


if __name__ == "__main__":
    main()
