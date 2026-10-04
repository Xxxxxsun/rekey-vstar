# CLAIMFORGE — Experiment Plan

Fabricated-damage claim-photo forensics: a domain stress-test of localized
AI-edit detection on authentic insurance-claim photographs.

- Status: design draft **v1** (claim-driven; incorporates external review round 1)
- Date: 2026-06-16
- External review: `docs/claim_forensics/review_round1.md` (gpt-5.4 xhigh; scored v0 at
  **3/6 Weak Reject**, clear path to accept). v1 below folds in its must-fix items.
- Working benchmark name: **CLAIMFORGE** (provisional)
- Builds on: the REKEY / Dynamic V* local-edit + soft-mask compositing pipeline
  (`dynamic_vstar/pipeline.py`, `compositing.py`, `image_api.py`).
- Framing: **defensive / red-team measurement.** We expose where detectors and the
  deployed claim-photo defender stack fail on small localized AI edits, so detection
  can be improved and this fraud caught. This is not an evasion toolkit; see §13.

---

## 0. 中文执行摘要

我们要回答一个有现实威胁背景的问题:**在一张真机拍摄、绝大多数像素是真实相机像素、只有一小块被前沿编辑器“加了假损伤”(凹陷/裂纹/划痕/水渍/霉斑/火烧)的理赔照片上,当前最强的 AI 生图检测器、篡改定位器、以及保险理赔实际部署的分层鉴伪流水线,能不能识别出来?**

文献已经反复证明“整图检测器依赖全局伪影、对小局部编辑会塌到接近随机”(INP-X 2602.00192: 91%→55%;Detecting Localized Deepfakes 2512.16688: <5% 面积≈随机;AIForge-Doc 2602.20569: 文档 0.98→0.563)。**因此“检测器会失败”本身不是新发现。** 我们的贡献只能立在四个别人没做过的轴上,缺一不可:

1. **损伤域(domain):** 真实车损/票据照片 + 前沿编辑器加的假损伤,带逐像素 GT mask。这个交集是空的(只有文档侧 AIForge-Doc 占了一半)。
2. **编辑面积 × 融合质量 的二维参数化扫描**(固定基底去混淆),报告“最小可检测编辑比例”。
3. **洗图鲁棒性扫描**(JPEG/缩放/截图/微信重传/生成式超分),以及它与小编辑的**交互**。
4. **更宽的检测器面板 + 真实分层防守方**:开源 + ≥1 个商用 API + 去重/EXIF/ELA/溯源,报告**低 FPR 下的 precision**(不是平衡 AUROC)。

外加一个**防御贡献**(§9),把论文从“攻击”变成“贡献”。第一版 MVP **锁车损 + 票据**(房产/酒店没有公开标注基底,延后)。目标会场:取证方向(WIFS / IH&MMSec / workshop),**不是顶会方法论文**,不要吹过头。判定:**有条件 GO**——前提是我们真的拥有上面 4 个轴 + 防御,否则就是已有基准的换皮。

---

## 1. Problem and threat model

A claimant submits a single, freshly captured smartphone photo as evidence of physical
damage (vehicle dent, hotel-room/property damage, a receipt total). The base capture is a
**genuine camera image**; an instruction editor inpaints one small region to add or alter
damage. Because >95% of pixels are authentic sensor pixels, the global generation
fingerprint that whole-image detectors rely on is largely absent.

Field-attested: an AI-added cracked-bumper claim (>£1,000) reported via Allianz/LV= shows
the capability already exists in the wild (industry press; treat the figure as
directional, not audited).

**Defensive goal.** Measure the detectability of this manipulation across the realistic
defender stack and the strongest available detectors, identify the failure surface as a
function of edit size / blending / laundering / editor, and propose a detector change that
recovers detection. We model the defender; we do not optimize an evader.

**Out of scope (and withheld):** any tuned recipe that uniquely strengthens a fraudster
(per-detector evasion parameters, metadata-washing how-to, adaptive-attack configs against
named products). See §13.

### 1.1 Headline framing (post-review)

The paper is **NOT** "detectors fail on small localized edits" (already published). The two
load-bearing pillars are:

- **P1 — Operational stress test.** Existing vehicle-claim screening (the layered defender of §6
  + off-the-shelf detectors) remains brittle **at deployment-style low FPR** to localized damage
  **inflation** and **injection** on authentic auto photos. Headline = operating-point recall, not
  detector collapse.
- **P2 — A defense that recovers (mandatory).** A simple localization-first / content-aware
  detector materially recovers low-FPR detection on **held-out editors** (E7). Without a real P2
  result the paper is a thin re-skin; with it, it is a measurement+mitigation contribution.

Axes that carry weight: **fixed-base edited-area sweep at low FPR**, **defender-stack eval**, **E7
defense**. Filler to minimize: "damage domain" as a standalone claim, long editor/commercial-API
leaderboards, exhaustive laundering menus. Working title direction: *"Brittle at low FPR:
stress-testing vehicle-claim photo screening against localized AI damage edits — and a localization
-first fix."* Primary domain = **auto**; receipts = transfer slice/appendix; property/hotel dropped
from the headline (no public base).

---

## 2. Positioning vs. verified prior work

All ids below were fetched and verified from arXiv during a 2026-06 deep-dive
(`/tmp/litsweep.json`, `/tmp/frauddive.json`). Two corrections are baked in.

| Work | id (verified) | What it establishes | What it did NOT do (our room) |
|---|---|---|---|
| INP-X "Detectors Overrely on Global Artifacts" | **2602.00192** | Restore real pixels outside mask → Hive 91.4→54.8, Sightengine 92.6→55.0, Corvi2023 94.2→55.4, SPAI 66.1→54.2; mechanism = VAE global spectral shift | Faces/scenes only; no fraud; no size×blend sweep; only 2 commercial APIs; no laundering |
| Detecting Localized Deepfakes (Bologna) | **2512.16688** | Accuracy vs mask size: <5%≈chance, recovery >20%, DINOv3 ~65% mask to match full-synthesis | **Qualitative (Fig 4), no per-bin table**; COCO/ImageNet/Places; no commercial APIs; no laundering; no fraud |
| AIForge-Doc | **2602.20569** | Doc fraud: median tamper area 0.92%; DocTamper AUC 0.98→0.563, TruFor 0.751, GPT-4o 0.509; Gemini-2.5-Flash-Image edits | **Documents only**; no damage photos; no size/blend sweep; no commercial APIs; no laundering |
| DiQuID / SAGI-D | **2502.06593** | 95,839 inpaints; UGDA deceptiveness; Spliced vs Fully-Regen split; human acc 74→35% | **FLUX-Fill is NOT in it** (was conflated w/ TGIF2); COCO/RAISE; no fraud; realism graded not swept |
| COCO-Inpaint | **2504.18361** | 6 inpainters (incl Flux.1-Fill/BrushNet/PowerPaint); cross-model Pixel-F1 86.4→24.6 | COCO objects; no continuous size×blend grid; IMDL localizers only; no fraud |
| TGIF / TGIF2 | **2407.11566** (WIFS'24) / **2603.28613** (Springer DOI 10.1186/s13635-026-00235-9) | Text-guided edits on real photos; SP vs FR; TGIF2 studies generative-SR laundering, FLUX hardest | COCO/web; only generative-SR laundering; no fraud; no commercial APIs |
| DiffSeg30k | **2511.19111** | 30k COCO, 8 diffusion editors, multi-turn edits, editor attribution | COCO; no size×blend grid; no fraud |

**Verify-before-citing (unconfirmed during the dig):** `FragFake 2505.15644`,
`X-Edit 2505.11753`, `LocateEdit-Bench 2602.05577`, "Editing Away the Evidence" `2603.12949`,
C2PA-shortcomings `2604.24890`, and other 2603/2604 ids. All vendor accuracy/scale numbers
(Verisk, AppZen, Allianz, Veryfi, etc.) are self-reported marketing — directional only.

**The empty intersection we fill:**
`{authentic auto/property/hotel damage photo} × {frontier-editor ADDED damage} × {per-pixel GT mask} × {detector + defender-stack eval}`.
No public benchmark sits here. Auto is the only well-covered base sub-domain; property/hotel
has **no public mask-annotated base** → MVP scopes to **auto + receipts**.

---

## 3. Core claims (claim-driven)

Each claim has a dedicated experiment (§7) and a falsifiable prediction. **Foundational
distinction (review fix):** every edit is typed as **damage INJECTION** (new damage on an intact,
plausible panel of a real car photo) or **damage INFLATION** (worsening/extending damage that
already exists in the CarDD base). The two are different threat models and are reported separately
throughout; conflating them was a v0 confound.

- **C1 — Operational low-FPR blind spot (headline, = P1).** The layered vehicle-claim defender
  (§6) + off-the-shelf detectors fail to flag small localized AI damage injection/inflation on
  authentic auto photos **at a locked low-FPR operating point** (recall at FPR∈{1%,0.1%} set on a
  held-out authentic+benign-transformed negative set). *Prediction:* recall@1%FPR ≈ floor for
  sub-5%-area edits; expected precision is poor at realistic claim-fraud prevalences (0.5–5%).
- **C2 — Edited-area breakdown curve.** Conditioning on (editor, SP/FR regime, compositing), recall
  at fixed low FPR falls as edited-area fraction shrinks; define **MDEF = the smallest edited-area
  fraction achieving a target recall (e.g. 0.5) at 1% FPR**, reported *per condition* (not one
  global number, and not via AUROC≥0.7). *Prediction:* MDEF is conditional and often above the
  realistic damage-edit area, i.e. real edits fall below detectability.
- **C3 — Compositing-realism axis (orthogonal to size & regime).** At fixed edited-area and fixed
  SP/FR regime, higher-realism **compositing method** (raw-paste → Poisson/seamless → REKEY
  soft-mask → deep-harmonization) lowers low-FPR recall; **spliced-back + harmonized is hardest.**
  Editor-native full redraw is NOT a point on this axis — it is the FR *regime* (see C-FR).
  *Prediction:* ≥X-point recall@1%FPR spread across compositing at fixed 2% area (target X≥10).
- **C-FR — SP vs FR regime.** At matched edited-area, fully-regenerated (FR) edits are *more*
  detectable than spliced-back (SP), because FR reintroduces a global generation fingerprint;
  SP is the realistic fraud regime and the harder, headline case. *Prediction:* SP recall < FR
  recall at every area bin.
- **C4 — Laundering interaction.** JPEG/resize/screenshot/messenger re-encode/generative-SR
  compound with small size to push even the best detector below deployable precision.
  *Prediction:* the size×laundering interaction term is significant and negative.
- **C5 — Frontier-editor hardness.** gpt-image / Gemini 2.5 Flash Image / Firefly / Flux.1-Fill
  are both capable of plausible damage synthesis and harder to detect than classic SD-inpaint.
  *Prediction:* frontier editors yield the lowest detector AUROC at fixed size/blend.
- **C6 — Defense recovers (= P2, MANDATORY; second pillar).** A simple localization-first /
  content-aware / reconstruction-error / PRNU-aware detector (or a patch head fine-tuned on the
  damage corpus) recovers low-FPR detection on small damage edits, **evaluated on HELD-OUT editors
  not seen in training**. *Prediction:* ≥X-point recall@1%FPR recovery vs. the best off-the-shelf
  passive detector on sub-5% edits (target X≥20). If null, the paper degrades to a benchmark-only
  contribution defining the open problem (see §8 results-to-claims).
- **C7 — Defender-stack slip.** Even dedup+EXIF+ELA+GenAI-classifier together miss the fresh
  single small-edit case; only capture-time provenance / PRNU (usually absent) catches it.
  *Prediction:* combined passive-layer recall on fresh sub-5% edits < 0.3.

A NO-GO trigger: if off-the-shelf detectors already catch our small frontier-editor damage
edits robustly (C1 fails in the pilot), we stop and pivot (the editor may leave a strong
local fingerprint — itself a finding, but a different paper).

---

## 4. Data

### 4.1 Authentic base images (real photos — never AI)

| Base | Contents | Role | Constraints |
|---|---|---|---|
| **CarDD** | 4,000 real car-damage photos, 6 classes (dent/scratch/crack/glass/lamp/tire), pixel instance masks, Ping-An claim standards | primary auto base; damage masks double as edit-region priors | signed form; non-commercial; **no real consumer EXIF**; no redistribution |
| **VehiDE** | 13,945 insurance-framed damaged-car photos, ~8 categories, pricing-rule annotations | scale + diversity | verify live Kaggle license |
| Roboflow/Kaggle auto-damage sets | smartphone/claim-style car damage | claim-realistic diversity | per-set licenses (often CC BY 4.0) |
| **CORD / SROIE / WildReceipt / XFUND** | real receipts/forms (same bases as AIForge-Doc) | receipt sub-domain | research-only; scrub PII |
| **RAISE-RAW / SIDD / VISION / Dresden / Forchheim** | provenance-bearing real-camera images | **required** if we make any EXIF/PRNU claim (CarDD lacks real EXIF) | research licenses |

**Property/hotel/water-mold-fire:** no public mask-annotated base exists (only a ~116-image
Roboflow furniture-defect set; xBD is satellite, MVTec is studio). Deferred — would need
commissioned/licensed/re-captured imagery. Documented as the binding constraint.

**Recommended supplement (high value-per-effort, per review):** a small **50–100 image
multi-phone capture set with REAL EXIF** and realistic benign post-processing. CarDD lacks genuine
consumer EXIF, so this supplement is what makes the operational-metrics calibration (§8) and any
EXIF/PRNU/provenance claim (§6) credible. Worth more than a 4th editor or a longer laundering menu.

### 4.2 The edit pipeline (reuse REKEY)

We reuse `dynamic_vstar` directly: crop the edit region (use CarDD masks as priors), send to
an image-edit API, composite back. Two production modes:

- **Spliced-back (SP, INP-X style):** keep all real pixels outside the mask; paste only the
  generated region (REKEY soft-mask path, `compositing.composite_generated_crop`). This is the
  realistic fraud move and the hardest case.
- **Fully-regenerated (FR):** the editor redraws the whole crop / image (no pixel restoration).
  Upper bound on detectability; matches the SP/FR split in DiQuID/SAGI and TGIF2.

### 4.3 Edit taxonomy (damage concepts)

Add/alter localized physical damage: dent, scratch, crack, shattered glass, lamp damage, tire
damage (auto, aligned to CarDD classes); for receipts: numeric-field edits (reuse AIForge-Doc
recipe). Each edit carries: target class, edit-region bbox/mask, mode (SP/FR), editor, size,
blending level, laundering chain → all in the manifest for programmatic GT.

### 4.4 Orthogonal factor design (review fix: de-entangle size / regime / compositing)

v0 conflated three things. v1 makes them **orthogonal factors**, each varied with the others held
fixed on **identical base images**:

- **F1 — edited-area fraction** ∈ {0.5, 1, 2, 5, 10}% (and a 20% high-end anchor). This is the
  *area edited*, NOT a synthesis regime. CarDD masks make area controllable on a fixed base.
- **F2 — SP/FR regime** ∈ {spliced-back (real pixels preserved outside mask), fully-regenerated}.
  FR is a **separate regime, not the "100% area" point** — that v0 mistake is removed.
- **F3 — compositing method** ∈ {raw-paste, Poisson/seamless, REKEY soft-mask, deep-harmonization}
  (applies to SP; FR is editor-native). Orthogonal to F1/F2.
- **F4 — damage type** ∈ {injection (intact panel), inflation (worsen existing CarDD damage)} — §3.
- **Editor** (held fixed within a curve; varied in E5): gpt-image (already wired), Gemini 2.5 Flash
  Image, Firefly Generative Fill, Flux.1-Fill, classic SD/SDXL-inpaint control.
- **Laundering (kept SMALL in v1):** {identity, JPEG-85, screenshot}. Messenger matrices and
  generative-SR are deferred unless a specific claim-submission channel justifies them (review:
  long laundering menus are filler + dual-use exposure).

**Mandatory controls (the rebuttal to "you only measured inpaint/compositing detection"):**
1. **Non-diffusion copy-paste control** — real damaged-panel crop from a *different* CarDD photo,
   composited identically. Isolates diffusion artifacts from compositing artifacts.
2. **No-op / sham-edit control** — run the full crop → (no semantic change) → composite → launder
   pipeline with NO added damage. If a detector fires here, it keys on our pipeline, not on AI
   content. This is the single most important credibility control.
3. **Identical-base balancing** — same base images across all F1–F4 cells; fix final resolution and
   JPEG quality to avoid the Fake-or-JPEG real=JPEG/fake=PNG confound (2403.17608).
4. **Per-condition realism audit** — human/VLM deceptiveness grade (UGDA-style) per cell, so that
   "realism" is not silently confounded with area/editor/compositing.

---

## 5. Detector panel

| Family | Detectors | Access |
|---|---|---|
| Whole-image passive | UnivFD/UniversalFakeDetect (2302.10174), Corvi2023 (2312.00195), SPAI (2411.19417), DINOv2/v3 ViT-L linear probe, **INP-X content-aware** (2602.00192) | open weights |
| Forgery localization | TruFor, CAT-Net, IML-ViT, Mesorch, SAFIRE, DinoLizer(*verify id*) — via **IMDL-BenCo / ForensicHub** | open weights |
| Reconstruction / classical | AEROBLADE per-pixel map (2401.17879), Noiseprint++, double-JPEG/ELA, PRNU (when source phone available) | open / training-free |
| Commercial API (≥1 required) | Hive, Sightengine, Illuminarty (offers localization) | paid REST |
| VLM path | GPT-4o, Qwen2.5-VL — zero-shot + targeted fine-tune | API / open |
| Document branch | DocTamper, AIForge-Doc baselines | open weights |

Use **fixed (not oracle) thresholds**; report calibration. Reproduce INP-X's restore-outside-mask
intervention as a sanity probe on our own pipeline.

---

## 6. Defender-stack model (the realistic target)

Model the deployed claim-photo pipeline as layers and report per-layer + combined recall:
1. **Reuse/duplicate** — pHash + visual-embedding match vs an archive (model Verisk ClaimSearch /
   VAARHAFT cross-insurer dedup) + reverse-image search. (Highest-yield in practice.)
2. **EXIF/metadata consistency** — timestamp/GPS/device vs narrative; missing-metadata/screenshot flags.
3. **Classic pixel forensics** — ELA, clone/double-JPEG, PRNU multi-signature.
4. **GenAI classifier** — a probabilistic "manipulated?" score (the panel in §5).
5. **Capture-time provenance** — Truepic/Serelay/C2PA (present only when in-app capture is forced).

C7 tests the **fresh single small-edit** path through all five: it is not a duplicate, the base
capture is real, ELA is weak on re-harmonized noise, it sits below the classifier threshold, and
consumer JPEGs carry no provenance manifest. Only PRNU (≈100–200 reference images from the same
phone; fails in dark/saturated/textured regions where damage lives) is a durable passive catch.

---

## 7. Experiments (mapped to claims)

**v1 run order (highest acceptance-lift per GPU-week first; review recommendation):**
E0 gate → **E2 clean curve** (ONE frontier editor + the copy-paste & sham controls, SP only, area
bins {0.5,1,2,5,10}%, injection vs inflation) → **E7 defense** (second pillar, held-out editor) →
E1/E6 defender-stack → then breadth (E3 compositing, E5 editors, E4 small laundering). Add editors/
APIs/laundering only after the auto curve + defense are sound. Receipts are an appendix transfer
slice, not co-equal. **Do controls before breadth.**

- **E0 — Gating pilot (1 week).** ~50 CarDD photos → gpt-image SP damage edits at 1–2% size →
  run UnivFD/Corvi2023/SPAI/AEROBLADE + 1 commercial API. **Gate:** confirm the collapse on *our*
  generator/domain. If detectors already catch it robustly → NO-GO / pivot (§3).
- **E1 — Domain transfer (C1).** Full panel on damage SP edits vs. the same detectors' published
  generic-inpaint numbers; headline metric precision@{1%,0.1%}FPR on a majority-real stream.
- **E2 — Size curve (C2).** Sweep Axis A on fixed bases; report AUROC & localization F1 per size
  bin and the **MDEF** per detector. This is the de-confounded version of the Bologna curve.
- **E3 — Blending axis (C3).** Sweep Axis B at fixed 2% size; SP vs FR; rank blending levels.
- **E4 — Laundering interaction (C4).** Cross size × laundering; fit interaction; report worst case.
- **E5 — Editor hardness (C5).** Cross editor × size at fixed blend; include the copy-paste control.
- **E6 — Defender stack (C7).** Run the §6 layers; per-layer + combined recall on fresh sub-5% edits.
- **E7 — Defense (C6).** Train/adapt a localization-first / content-aware / recon-error / PRNU-aware
  detector (or a DinoLizer-style patch head on the damage corpus); measure precision@1%FPR recovery
  on sub-5% edits; held-out editors/datasets for generalization; cross-domain to documents.
- **E8 — Adaptive robustness (NOT in the public paper; internal red-team only).** Gradient-through
  stress of the E7 defense to learn whether it survives. Kept out of the submission and any release
  per review (a public adaptive-attack section reads as an evasion recipe); if mentioned at all,
  mechanism-level only, no configs (§13).

---

## 8. Metrics & protocol (review fix: locked low-FPR protocol)

- **Threshold locking.** Each detector's threshold is fixed on a **held-out negative set of
  authentic + benign-transformed photos** — real CarDD/phone images passed through realistic
  claimant behaviors: screenshots, chat-app re-encodes, night-mode/HDR, resize, portrait/bokeh.
  Thresholds are NOT re-tuned per test condition.
- **Primary metric:** **recall (TPR) at fixed FPR ∈ {1%, 0.1%}**, plus **pAUC over [0, 1% FPR]**,
  with **bootstrap CIs**. Plus **expected precision at explicit fraud prevalences** {0.5%, 1%, 5%}
  (no vague "majority-real"; the prior is stated).
- **MDEF (redefined):** smallest edited-area fraction reaching a target recall (e.g. 0.5) at 1% FPR,
  reported **per (editor, SP/FR, compositing, damage-type) condition** — not a single global number.
- **Localization:** IoU / pixel-F1 for localizers, at matched operating points.
- **Defender stack:** per-layer and combined recall on fresh sub-5% edits; **and the benign
  false-positive rate** on the held-out authentic+benign set (the under-measured deployment harm).
- **Secondary (comparability only):** balanced AUROC, to relate to prior generic-inpaint numbers.
- **Protocol controls:** fixed final JPEG/resolution; identical bases across F1–F4; sham + copy-paste
  controls in every figure; date-stamp commercial-API results (detectors move fast).

---

## 9. Defense contribution (turns attack → contribution)

E7 is the part reviewers reward. Candidate fixes, in order of expected payoff:
1. **Content-aware training** (INP-X recipe) on spliced-back damage edits.
2. **Reconstruction-error localization** (AEROBLADE per-pixel map) thresholded for small regions.
3. **Patch-level head** (DINOv3 + linear, DinoLizer-style) fine-tuned on the damage corpus.
4. **Forensic + provenance fusion** triage (noiseprint/double-JPEG + partial C2PA/PRNU) as a
   human-review triage signal — explicitly NOT standalone proof of fraud.

---

## 10. Ablations
- SP vs FR at matched size (isolates the spliced-back effect).
- Diffusion-inpaint vs non-diffusion copy-paste (isolates "are we just measuring inpaint detection").
- With/without harmonization (Axis B granularity).
- Reproducibility: 3 generation seeds → inter-seed metric variance.
- Cross-domain transfer: auto-trained defense → receipts (and vice versa).

---

## 11. Reproducibility, compute, cost
- Detectors are inference-only (single modern GPU; vast.ai available). Only E7 trains a light head.
- Corpus: a few k–30k edited images across 4 editors × {SP,FR} × size/blend/laundering grid.
  Dominant cost = quality filtering + mask QA (manual or VLM-assisted; expect a non-trivial reject rate).
- Editor-API spend: low-thousands USD; commercial-detector API: hundreds–low-thousands USD (partial panel realistic).
- Version every run (`pipeline_version`, seed, editor, manifest) as REKEY already does.

---

## 12. Risks, mitigations, kill criteria
- **Thin novelty (highest):** phenomenon already published. Mitigation = own all four axes + the
  defense; frame as measurement + domain transfer, never "new method." Kill if we can't add the axes.
- **Competitor pre-empts** the obvious "damage AIForge-Doc": move fast; differentiate on laundering +
  commercial-API panel + defender stack.
- **No property/hotel base:** scope MVP to auto+receipts; state explicitly.
- **CarDD non-redistribution / no EXIF:** release only gated/aggregate artifacts; use RAISE/SIDD for
  any PRNU/EXIF claim.
- **Editor reject rate** (AIForge-Doc rejected 5/7 tools): budget QA; report acceptance rate & failure modes.
- **"We measured inpaint-detection not damage understanding":** the copy-paste control + SP/FR ablation answer this.

---

## 13. Ethics & data gating (binding)
Strictly defensive red-team. Concrete gates:
- **Bases:** only licensed/public; **never** scrape real insurer claim images or claimants' social-media
  property photos; receipts de-identified/synthetic-PII; respect non-redistribution (CarDD/Shutterstock, xBD, MVTec).
- **PII:** scrub faces/plates/addresses/GPS; drop re-identifiable content.
- **Release:** report at the level of **detector families and COARSE condition bins**, never per-product
  "best-miss" cells (a `detector × editor × laundering` miss-rate table is close to an evasion recipe).
  Prefer a **gated evaluation server / enclave** over downloadable artifacts. Do **not** publicly release
  edited-image files, masks-as-templates, per-editor prompts, evasion-tuned params, or metadata-washing
  tricks. **No E8 (adaptive attack) in the public paper.** This mirrors INP-X / AIForge-Doc disclosure level.
- **Labeling:** watermark/C2PA-tag every AI-edited sample as synthetic.
- **Coordinated disclosure:** share blind-spot findings with affected vendors/insurers (Verisk, Shift,
  VAARHAFT, Truepic) before public release.
- **Legal/framing:** state plainly that fabricating claims is a crime; keep the public-interest
  (fraud-detection improvement) justification central.
- **Defenders as black boxes:** report catch/miss, never bypass instructions.

---

## 14. Milestones (relative)
1. E0 gating pilot → go/no-go (≈1 wk).
2. Build auto corpus (CarDD/VehiDE) + edit pipeline + size/blend/laundering grid (≈2–3 wks).
3. E1–E6 full detector + defender eval (≈2 wks).
4. E7 defense + ablations (≈2 wks).
5. Receipt sub-domain (reuse AIForge-Doc bases) (≈1 wk).
6. Write-up. Candidate venues: WIFS, IH&MMSec, IEEE TIFS, or a CVPR/ICCV forensics workshop
   (verify current deadlines). Coordinated disclosure window before any commercial-API numbers.

---

## 15. Must-cite (verified ids only)
INP-X 2602.00192 · Detecting Localized Deepfakes 2512.16688 · AIForge-Doc 2602.20569 ·
DiQuID/SAGI 2502.06593 · COCO-Inpaint 2504.18361 · TGIF 2407.11566 · TGIF2 2603.28613 ·
DiffSeg30k 2511.19111 · UnivFD 2302.10174 · Corvi2023 2312.00195 · SPAI 2411.19417 ·
AEROBLADE 2401.17879 · Fake-or-JPEG confound 2403.17608 · Chameleon/AIDE 2406.19435 ·
RAID 2506.03988. (Verify FragFake/X-Edit/LocateEdit-Bench/2603-2604 ids before adding.)
