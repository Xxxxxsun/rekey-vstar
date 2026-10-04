#!/usr/bin/env python3
"""
Build the Phase-2 difficulty-comparison sample (blind 2AFC: ReKey vs its V* original).

- Fresh, stratified, seed-balanced 200 items, DISJOINT from the Phase-1 edit-quality sample
  (so annotators have not seen these ReKey images in Phase 1 -> preserves blindness).
- Each item paired with its own V* original (same image); random L/R side per pair.
- Bundles composite (ReKey) + plain source.png (original, NO box) into audit/imgs/ as __c/__o.
- Writes diff_sample.json + diff_data.js (window.DIFF_PAIRS) for score_diff.html.
"""
import json, glob, os, random
from math import floor
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(REPO, "paper/emnlp2026/rebuttal/audit")
IMGS = os.path.join(AUDIT, "imgs")
SEEDS = ["bench1", "bench2", "bench3"]
QUOTA = {"bench1": 67, "bench2": 67, "bench3": 66}
STRATA = ["color__add_only", "color__has_replace", "position__add_only", "position__has_replace"]
RNG_SEED = 20260711


def shrink(src, dst, long=1500, q=82):
    im = Image.open(src).convert("RGB"); w, h = im.size; s = long / max(w, h)
    if s < 1: im = im.resize((int(w * s), int(h * s)))
    im.save(dst, "JPEG", quality=q)


def largest_remainder(quota, sizes):
    total = sum(sizes.values())
    raw = {k: (quota * sizes[k] / total if total else 0) for k in sizes}
    alloc = {k: min(floor(raw[k]), sizes[k]) for k in sizes}
    rem = quota - sum(alloc.values())
    order = sorted(sizes, key=lambda k: raw[k] - floor(raw[k]), reverse=True)
    i = 0
    while rem > 0:
        k = order[i % len(order)]
        if alloc[k] < sizes[k]: alloc[k] += 1; rem -= 1
        i += 1
        if i > 10000: break
    return alloc


def main():
    p1 = set(it["item_id"] for it in json.load(open(f"{AUDIT}/audit_sample.json")))
    pool = {s: {st: [] for st in STRATA} for s in SEEDS}
    for pf in sorted(glob.glob(os.path.join(REPO, "results/benchmark/*/*/artifacts/plan.json"))):
        d = json.load(open(pf)); seed = pf.split("/")[-4]
        iid = f"{d['image_id']}__{seed}"
        if iid in p1: continue
        qt = "color" if d.get("question_type") == "color" else "position"
        hr = "has_replace" if any(e["mode"] == "replace" for e in d["edits"]) else "add_only"
        adir = os.path.dirname(pf)
        pool[seed][f"{qt}__{hr}"].append(dict(
            item_id=iid, seed=seed, image_id=d["image_id"], question_type=d.get("question_type"),
            qtype_coarse=qt, stratum=f"{qt}__{hr}",
            rekey_q=d.get("question", ""), orig_q=d.get("source_question", ""),
            comp=os.path.join(adir, "composite.jpg"), src=os.path.join(adir, "source.png")))

    rng = random.Random(RNG_SEED)
    chosen = []
    for seed in SEEDS:
        sizes = {st: len(pool[seed][st]) for st in STRATA}
        alloc = largest_remainder(QUOTA[seed], sizes)
        for st in STRATA:
            cand = sorted(pool[seed][st], key=lambda x: x["item_id"])
            chosen += rng.sample(cand, alloc[st])
    chosen.sort(key=lambda x: (x["seed"], x["image_id"]))
    rng.shuffle(chosen)                       # present in random order

    os.makedirs(IMGS, exist_ok=True)
    pairs = []
    for i, it in enumerate(chosen, 1):
        iid = it["item_id"]
        shrink(it["comp"], f"{IMGS}/{iid}__c.jpg")
        shrink(it["src"],  f"{IMGS}/{iid}__o.jpg")
        side = rng.choice(["L", "R"])          # which side shows the ReKey version
        pairs.append(dict(pair_id=f"D{i:03d}", item_id=iid, seed=it["seed"],
                          question_type=it["question_type"], stratum=it["stratum"],
                          rekey_side=side,
                          rekey_img=f"imgs/{iid}__c.jpg", rekey_q=it["rekey_q"],
                          orig_img=f"imgs/{iid}__o.jpg", orig_q=it["orig_q"]))

    json.dump(pairs, open(f"{AUDIT}/diff_sample.json", "w"), ensure_ascii=False, indent=1)
    open(f"{AUDIT}/diff_data.js", "w").write("window.DIFF_PAIRS = " + json.dumps(pairs, ensure_ascii=False) + ";\n")

    import collections
    print(f"Phase-2 difficulty sample: {len(pairs)} pairs (disjoint from Phase-1)")
    print("  strata:", dict(collections.Counter(p["stratum"] for p in pairs)))
    print("  seeds :", dict(collections.Counter(p["seed"] for p in pairs)))
    print("  rekey side L/R:", dict(collections.Counter(p["rekey_side"] for p in pairs)))
    print(f"  overlap with Phase-1: {len(set(p['item_id'] for p in pairs) & p1)} (should be 0)")


if __name__ == "__main__":
    main()
