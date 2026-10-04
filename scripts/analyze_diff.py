#!/usr/bin/env python3
"""
Analyze Phase-2 difficulty 2AFC (blind: ReKey vs its V* original -> which is harder).

Usage: python scripts/analyze_diff.py A.csv [B.csv]
CSV cols: annotator,pair_id,item_id,seed,question_type,stratum,rekey_side,choice,rekey_harder,note
  choice ∈ {左更难,右更难,差不多}; rekey_harder ∈ {1,0,0.5}.

Reports P(judged ReKey harder) among non-ties + Wilson 95% CI + sign test vs 50%,
tie rate, breakdown by type, and Cohen's κ between two annotators (on choice).
Interpretation: P ≤ 50% (or n.s. > 50%) => editing did not raise human-perceived difficulty.
"""
import csv, sys, math
from collections import Counter


def read(p):
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (100 * (c - m), 100 * (c + m))


def binom_two_sided(k, n, p=0.5):
    if n == 0: return float("nan")
    from math import comb
    def pmf(i): return comb(n, i) * p**i * (1 - p)**(n - i)
    obs = pmf(k)
    return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= obs + 1e-12))


def cohen_kappa(pairs):
    pairs = [(a, b) for a, b in pairs if a and b]
    n = len(pairs)
    if n == 0: return None, 0
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    return ((po - pe) / (1 - pe) if pe < 1 else 1.0), po


def report(rows, tag):
    def block(sub, label):
        rk = sum(1 for r in sub if r["rekey_harder"] == "1")
        og = sum(1 for r in sub if r["rekey_harder"] == "0")
        tie = sum(1 for r in sub if r["rekey_harder"] == "0.5")
        nt = rk + og
        lo, hi = wilson(rk, nt)
        p = binom_two_sided(rk, nt)
        print(f"  {label:10} n={len(sub):3}  ReKey更难 {rk} / 原更难 {og} / 差不多 {tie}"
              f"  | P(ReKey更难|非平局)={100*rk/nt:5.1f}%  [{lo:.1f},{hi:.1f}]  sign-test p={p:.3f}" if nt else
              f"  {label:10} n={len(sub):3}  全为平局")
    print(f"\n=== [{tag}]  n={len(rows)} ===")
    block(rows, "总体")
    for qt in ("color", "position"):
        sub = [r for r in rows if r["question_type"] == qt]
        if sub: block(sub, qt)


def main():
    paths = sys.argv[1:]
    if not paths:
        print(__doc__); return
    data = [read(p) for p in paths]
    names = [(r[0]["annotator"] if r and r[0].get("annotator") else p) for p, r in zip(paths, data)]
    for nm, rows in zip(names, data):
        report([r for r in rows if r.get("choice")], nm)
    if len(data) >= 2:
        A = {r["pair_id"]: r for r in data[0]}; B = {r["pair_id"]: r for r in data[1]}
        common = sorted(set(A) & set(B))
        k, po = cohen_kappa([(A[i].get("choice", ""), B[i].get("choice", "")) for i in common])
        print(f"\n=== 两标注者一致性（{names[0]} vs {names[1]}），{len(common)} 对 ===")
        print(f"  choice κ={k:.3f}  原始一致率={100*po:.1f}%" if k is not None else "  n/a")
    print("\n— 结论口径 —  P(判 ReKey 更难) ≤ 50%（或不显著 > 50%）→ 编辑未提高人类可感知难度；")
    print("  与图像度量、LLaVA 行为学并列作为第三条证据。非盲的保守性见 README。")


if __name__ == "__main__":
    main()
