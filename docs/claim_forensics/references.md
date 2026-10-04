# CLAIMFORGE — Verified References & Literature Landscape

Consolidated so nothing depends on ephemeral `/tmp` caches. Compiled 2026-06-20 from two
literature sweeps (2026-06-15/16) + a paper-verification pass that fetched arXiv pages.

> ⚠️ Most ids below are 2025–2026 preprints, **past the assistant's training cutoff** — they were
> surfaced and verified by live web search this session. Confidence is annotated. Re-open the URL
> before formal citation. Raw verification cache: `_sweeps/frauddive_raw.json` (first sweep cache
> `litsweep.json` was lost to /tmp cleanup; its content survives in §2/§5 of `experiment_plan.md`
> and in the auto-memory project note).

---

## A. "Small localized edits collapse detectors" — the core phenomenon (VERIFIED)

### A1. INP-X — the headline collapse paper
- **Title:** *AI-Generated Image Detectors Overrely on Global Artifacts: Evidence from Inpainting Exchange (INP-X)*
- **arXiv:** 2602.00192 — https://arxiv.org/abs/2602.00192
- **Code:** https://github.com/emirhanbilgic/INP-X
- **Authors / date:** Elif Nebioglu, Emirhan Bilgic, Adrian Popescu; submitted 30 Jan 2026; preprint (21 pp).
- **Mechanism:** detectors key on a VAE-induced **global spectral shift** across the *whole* image,
  not the locally synthesized content. The "Inpainting Exchange" op keeps the AI region but restores
  the real pixels outside the mask → collapse:
  - Hive 91.4 → 54.8 · Sightengine 92.6 → 55.0 · Corvi2023 94.2 → 55.4 · SPAI 66.1 → 54.2 · DNF 71.0 → 60.4
- **Data:** 90K benchmark (30k each real / inpainted / exchanged) over CelebA-HQ, CityScapes,
  OpenImages, SUN-RGBD; generators Kandinsky2.2 / OpenJourney / SDv1.4.
- **Did NOT do:** fraud domain; size×blending sweep with numbers; >2 commercial APIs; laundering.
- **Confidence:** HIGH (abs+HTML+HF+GitHub all cross-checked; all four collapse pairs verbatim).
- **This is the direct source for the "91% → 55%" / "small edit collapses detector" claim.**

### A2. Detecting Localized Deepfakes — the edit-size curve
- **Title:** *Detecting Localized Deepfakes: How Well Do Synthetic Image Detectors Handle Inpainting?*
- **arXiv:** 2512.16688 — https://arxiv.org/abs/2512.16688
- **Authors:** S. Pandolfini, L. Pellegrini, M. Ferrara, D. Maltoni (University of Bologna); Dec 2025.
- **Finding (QUALITATIVE, Fig 4 — no per-bin table):** <5% mask area ≈ chance; recovery >20%;
  DINOv3 matches full-synthesis detection at ~65% mask, DINOv2 needs >80%.
- **Backbones:** ResNet-50 CLIP, DINOv2 ViT-L/14, DINOv3 ViT-L/16. **Datasets:** BR-Gen, TGIF, TGIF2.
- **Did NOT do:** fraud; commercial APIs; deliberate laundering; clean numeric size bins.
- **Confidence:** HIGH on existence/datasets/backbones/qualitative trend; LOW on specific AUROC points.

### A3. AIForge-Doc — the document-fraud analogue
- **Title:** *AIForge-Doc: A Benchmark for Detecting AI-Forged Tampering in Financial and Form Documents*
- **arXiv:** 2602.20569 — https://arxiv.org/abs/2602.20569 ; submitted 24 Feb 2026.
- **Finding:** median tampered area **0.92%** → DocTamper AUC **0.98 → 0.563**, TruFor 0.751, GPT-4o 0.509.
- **Data:** 4,061 forged from CORD/WildReceipt/SROIE/XFUND via Gemini 2.5 Flash Image (89.6%) + Ideogram v2 (10.4%).
- **Scope:** documents only — no damage photos, no size/blend sweep, no commercial APIs, no laundering.
- **Confidence:** HIGH.

---

## B. Closest localized-edit benchmarks on real photos (VERIFIED ids)

| Name | arXiv / venue | Key fact |
|---|---|---|
| DiQuID / SAGI-D | **2502.06593** | 95,839 inpaints from 78,684 originals (MS-COCO/RAISE-RAW/OpenImages); UGDA deceptiveness; SP vs FR split; human acc 74→35%. v2 renamed SAGI-D. **FLUX-Fill is NOT in it** (was conflated w/ TGIF2). MeVer/CERTH-ITI. |
| COCO-Inpaint | **2504.18361** | 6 inpainters incl Flux.1-Fill/BrushNet/PowerPaint; cross-model Pixel-F1 **86.4→24.6**; mask-ratio stratified. |
| TGIF | **2407.11566** (IEEE WIFS 2024) | text-guided edits on real photos; SP vs FR. |
| TGIF2 | **2603.28613** (Springer, DOI 10.1186/s13635-026-00235-9) | adds random masks; FLUX hardest; studies generative-SR laundering only. |
| DiffSeg30k | **2511.19111** | 30k COCO, 8 diffusion editors, multi-turn edits, editor attribution. |
| Chameleon / AIDE | **2406.19435** (ICLR 2025) | difficulty floor: on FULL fakes ~9 detectors still call AI "real" (~0% fake recall). |

---

## C. Detector panel (open weights unless noted)

- **Whole-image passive:** UnivFD/UniversalFakeDetect **2302.10174** (CVPR'23, frozen CLIP) ·
  Corvi2023 **2312.00195** · SPAI **2411.19417** (CVPR'25) · DIRE 2303.09295 (ICCV'23) ·
  AEROBLADE **2401.17879** (CVPR'24, training-free, per-pixel map) · NPR 2312.10461 (CVPR'24) ·
  DINOv2/v3 ViT-L linear probe · INP-X content-aware (2602.00192).
- **Forgery localization (via IMDL-BenCo / ForensicHub):** TruFor (CVPR'23) · CAT-Net · IML-ViT ·
  Mesorch (AAAI'25) · SAFIRE (AAAI'25) · DocTamper/DTD (CVPR'23) · DinoLizer *(id unverified)*.
- **Commercial APIs (paid):** Hive Moderation · Sightengine · Illuminarty (offers localization).
- **VLM path:** GPT-4o, Qwen2.5-VL (zero-shot + fine-tune).
- **Confound control ref:** Fake-or-JPEG corrected GenImage **2403.17608** (real=JPEG/fake=PNG bias).
- **Adversarial/laundering:** RAID **2506.03988**.

---

## D. Fraud-domain: bases, defenders, scale

### D1. Real authentic base datasets (never AI)
- **CarDD** — 4,000 real car-damage photos, 6 classes (dent/scratch/crack/glass/lamp/tire), pixel
  instance masks, Ping-An claim standards. Signed form; non-commercial; no real consumer EXIF; no redistribution.
- **VehiDE** — 13,945 insurance-framed damaged-car photos, ~8 categories, pricing-rule annotations (Kaggle).
- Roboflow/Kaggle auto-damage sets (CAPSTONE, Car Damage Assessment 3,772, etc.) — licenses vary.
- **Receipts/forms:** CORD, WildReceipt, SROIE, XFUND (same bases as AIForge-Doc).
- **Provenance-bearing (for EXIF/PRNU claims):** RAISE-RAW, SIDD, VISION, Dresden, Forchheim, MIT-Adobe FiveK.
- **GAP:** no public mask-annotated **property/hotel/water-mold-fire** damage base (only a ~116-img
  Roboflow furniture set; xBD is satellite, MVTec is studio). → binding constraint; MVP = auto+receipts.

### D2. Defender stack actually deployed (model these as the target)
- **Reuse/dedup (highest-yield):** Verisk ClaimSearch Image Matching (>95% industry), VAARHAFT
  cross-insurer dedup, Shift/FRISS; reverse-image search (TinEye/Yandex/Google).
- **Metadata/EXIF consistency** · **classic pixel forensics** (ELA, clone, double-JPEG, PRNU multi-signature).
- **GenAI/deepfake classifier** (Verisk module beta; VAARHAFT, TruthScan, UVeye, Inaza).
- **Capture-time provenance** (strongest, usually absent on inbound claimant JPEGs): Truepic, Serelay,
  C2PA / Content Credentials; SynthID.
- Field-attested threat: Allianz/LV= AI-added cracked-bumper claim (>£1,000). *(vendor/scale figures are self-reported marketing — directional only.)*

---

## E. ⚠️ VERIFY-BEFORE-CITE (could NOT be confirmed this session — do not cite until resolved)
FragFake **2505.15644** · X-Edit **2505.11753** · LocateEdit-Bench **2602.05577** ·
"Editing Away the Evidence" **2603.12949** · C2PA-shortcomings **2604.24890** · and other 2603/2604 ids.
All vendor accuracy/scale numbers (Verisk, AppZen, Allianz, Veryfi) are self-reported, not audited.

---

## F. Provenance
- Sweep 1 (general detector-robustness landscape): 2026-06-15, 9 agents — cache `litsweep.json` **lost to /tmp cleanup**;
  content survives in `experiment_plan.md` §2/§5 and the project memory note.
- Sweep 2 (fraud-domain deep-dive + paper verification): 2026-06-16, 12 agents — raw cache archived at
  `_sweeps/frauddive_raw.json`.
- External review (round 1): `review_round1.md`.
