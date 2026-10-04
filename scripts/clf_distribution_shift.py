#!/usr/bin/env python3
"""
Distribution-shift test (rebuttal, LqQL B4): can a SHALLOW classifier separate
original V* images from ReKey-regenerated images? If it is at chance, the two sets are
not distributionally separable, so the model accuracy drop cannot be a distribution shift.

Design (controls the confounds):
  - original = source.png (lossless), ReKey = composite.png (lossless); BOTH re-encoded to the
    same JPEG q90 + same size  -> no format/compression cheat.
  - split TRAIN/TEST BY IMAGE (an image's original + ReKey on the same side) -> no leakage;
    forces a generalizable "edit signature", not scene memorization.
  - shallow classifier = logistic regression on ~42 low-level image features.
  - positive control: same classifier on original vs a mild Gaussian blur -> must be ~100%,
    proving the classifier CAN detect a real global shift (so a chance result is meaningful).
  - run per regeneration seed (bench1/2/3) to show robustness.
No GPU / torch / sklearn needed. CPU, ~2-3 min.  Run from repo root: python scripts/clf_distribution_shift.py
"""
import glob, io, json, numpy as np
from PIL import Image, ImageFilter
Image.MAX_IMAGE_PIXELS = None
SZ = 256
rng = np.random.RandomState(0)


def norm_load(path):
    im = Image.open(path).convert("RGB").resize((SZ, SZ))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=90); buf.seek(0)
    return np.asarray(Image.open(buf).convert("RGB"), dtype=np.float64)


def rgb2lab(rgb):
    r = rgb / 255.0; lin = np.where(r <= 0.04045, r / 12.92, ((r + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883]); d = 6 / 29
    f = np.where(xyz > d ** 3, np.cbrt(xyz), xyz / (3 * d ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def feats(img):
    F = []
    for c in range(3):
        x = img[..., c].ravel(); m = x.mean(); s = x.std() + 1e-6
        F += [m, s, (((x - m) / s) ** 3).mean()]
        F += list(np.histogram(x, bins=8, range=(0, 255))[0] / x.size)
    g = img.mean(2); gy, gx = np.gradient(g); F.append(np.sqrt(gx * gx + gy * gy).mean())
    lap = (np.roll(g, 1, 0) + np.roll(g, -1, 0) + np.roll(g, 1, 1) + np.roll(g, -1, 1) - 4 * g); F.append(lap.std())
    Ff = np.abs(np.fft.fftshift(np.fft.fft2(g - g.mean()))); tot = Ff.sum() + 1e-6
    yy, xx = np.ogrid[:SZ, :SZ]; hi = ((yy - SZ // 2) ** 2 + (xx - SZ // 2) ** 2) > (SZ * 0.25) ** 2
    F.append(Ff[hi].sum() / tot)
    lab = rgb2lab(img)
    for c in range(3): F += [lab[..., c].mean(), lab[..., c].std()]
    return np.array(F)


def logreg(Xtr, ytr, Xte, l2=1.0, lr=0.1, ep=800):
    mu = Xtr.mean(0); sd = Xtr.std(0) + 1e-6; Xtr = (Xtr - mu) / sd; Xte = (Xte - mu) / sd
    n, d = Xtr.shape; w = np.zeros(d); b = 0.0
    for _ in range(ep):
        p = 1 / (1 + np.exp(-(Xtr @ w + b))); w -= lr * (Xtr.T @ (p - ytr) / n + l2 * w / n); b -= lr * (p - ytr).mean()
    return 1 / (1 + np.exp(-(Xte @ w + b)))


def auc(y, s):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1)
    npos = y.sum(); nneg = len(y) - npos
    return (r[y == 1].sum() - npos * (npos + 1) / 2) / (npos * nneg)


def run(imgs0, imgs1, ids, tag):
    X = np.array([feats(a) for a in imgs0 + imgs1]); y = np.array([0] * len(imgs0) + [1] * len(imgs1))
    idsa = np.array(ids + ids); uids = sorted(set(ids)); rng.shuffle(uids); tr_ids = set(uids[:len(uids) // 2])
    tr = np.array([i in tr_ids for i in idsa]); te = ~tr
    s = logreg(X[tr], y[tr].astype(float), X[te]); acc = ((s > 0.5).astype(int) == y[te]).mean()
    a = auc(y[te], s); n = te.sum()
    print(f"  [{tag:16}] test n={n}  acc={acc*100:5.1f}% ±{1.96*np.sqrt(acc*(1-acc)/n)*100:.1f}  AUC={a:.3f}")


def main():
    b1 = sorted(glob.glob("results/benchmark/bench1/*/artifacts/plan.json"))
    ids = [json.load(open(pf))["image_id"] for pf in b1]
    orig = [norm_load(pf.rsplit("/", 1)[0] + "/source.png") for pf in b1]
    print(f"{len(orig)} original images loaded\n=== original V* vs ReKey (per seed) ===")
    for seed in ("bench1", "bench2", "bench3"):
        comp = [norm_load(f"results/benchmark/{seed}/{i}__{seed}/artifacts/composite.png") for i in ids]
        run(orig, comp, ids, f"orig vs {seed}")
    print("=== positive control: original vs mild Gaussian blur (classifier sanity) ===")
    blur = [np.asarray(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), float) for a in orig]
    run(orig, blur, ids, "orig vs blur")
    print("\n判读：原vsReKey ≈ 50% / AUC≈0.5（不可分→无分布偏移）；模糊对照 ≈100%（分类器有效）。")


if __name__ == "__main__":
    main()
