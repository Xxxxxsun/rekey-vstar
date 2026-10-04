# CLAIMFORGE — External Review (Round 1)

Reviewer: gpt-5.4 (xhigh reasoning) via Codex CLI. Date: 2026-06-16.
Target reviewed: docs/claim_forensics/experiment_plan.md (design draft v0).

---

**A. Most Likely Rejection Reasons, Ranked**

1. **Thin novelty / wrong headline.**
This is **not** novel if sold as “small localized edits break detectors”; that is already established by INP-X, Bologna, and AIForge-Doc. The four-axis package is enough for **WIFS / IH&MMSec / forensics workshop** only if the paper is framed as: **an operational low-FPR stress test of claim-photo defender stacks on localized damage edits, plus a mitigation that recovers performance**. The axes with real weight are: **fixed-base size sweep at deployment FPR**, **defender-stack evaluation**, and **E7 defense**. The weakest axes are: **“damage domain” by itself** and **broad commercial/API breadth or long laundering menus**.
**Preempt it by:** making E7 mandatory, shrinking the editor/API leaderboard, and rewriting the title/abstract around **vehicle-claim fraud triage at low FPR**, not detector collapse.

2. **The factorization is not yet clean; several core variables are entangled.**
Right now, **size, SP/FR mode, and blending are partially confounded**. “100% = FR” is not a valid size point; FR changes the synthesis regime, not just the edited area. Likewise, “editor-native FR” is not just another blending level. More seriously, **CarDD images are already damaged**; unless you separate **damage inflation** (edit overlaps real damage) from **damage injection** (edit on an intact but plausible nearby panel), the threat model is muddy. The proposed non-diffusion copy-paste control is **necessary but not sufficient**; it does not isolate compositing artifacts, donor mismatch, or damage semantics.
**Preempt it by:** redesigning the factors as `edited-area fraction` × `SP/FR regime` × `compositing method`; adding a **no-op/sham edit control** that runs the full crop/composite/launder pipeline without semantic change; stratifying **on-damage vs off-damage** edits; and running a **human/VLM realism audit** per condition.

3. **The operational metric story is under-specified.**
`precision@{1%,0.1%}FPR on a majority-real stream` is directionally right, but **“majority-real” is too vague** and precision is meaningless without an explicit prior. Also, **MDEF defined by AUROC >= 0.7 is the wrong primary operational definition**; AUROC will hide low-FPR collapse.
**Preempt it by:** locking thresholds on a held-out **authentic + benign-transformed** validation set, then reporting **TPR/recall at fixed FPR**, plus **expected precision under explicit prevalences** such as 0.5%, 1%, and 5%. Redefine MDEF as **the smallest edited-area fraction achieving a target recall at 1% FPR**. Add **pAUC over [0,1% FPR]** and bootstrap CIs.

4. **Scope is still too broad relative to the available data.**
`auto + receipts` is defensible. `property/hotel` is not. If you keep promising “claim photos” broadly, reviewers will notice that the only solid public visual base is auto, and the receipt branch is a separate document-forensics mini-paper. “Car dents only” is acceptable if you are honest and call it **vehicle-damage claim forensics**.
**Preempt it by:** dropping property/hotel from the headline entirely, making **auto the primary benchmark**, and using receipts only as **one transfer slice** or appendix-level generalization check.

5. **Dual-use / ethics reviewers will still worry this reads like a fraud-enabling benchmark.**
The current framing is better than most, but **E8 is a liability**, and a large public table of `detector x editor x laundering` miss-rates is close to an evasion recipe. Gated release helps, but not if the paper still exposes operationally useful cells.
**Preempt it by:** removing **E8** from the public paper, reporting results at the level of **detector families** and **coarse condition bins**, not per-product best-miss recipes, and **not releasing edited images, masks, prompts, or laundering scripts**. If anything is released, use a **gated evaluation server / enclave**, not downloadable artifacts.

---

**B. Mock Review**

**Summary**
This is a timely and practically relevant measurement plan. The authors are unusually honest that the core phenomenon is already known and try to recover novelty through domain specificity, controlled factor sweeps, deployed-stack evaluation, and a defensive recovery baseline. That is the correct instinct.

In its current form, however, the plan still overreaches. The strongest paper here is **not** “detectors fail on small edits,” but rather **“existing vehicle-claim screening pipelines remain brittle at low FPR to localized damage inflation/injection, and a simple localization-first defense partially recovers performance.”** Without cleaner factorization, a tighter scope, and a real E7 result, I would lean reject.

**Strengths**
- The threat model is important and economically credible.
- The plan is unusually aware of prior work and novelty risk.
- The intended emphasis on **low-FPR operating points** is correct for this venue.
- Using authentic base imagery and mask-controlled edits is the right experimental backbone.
- Including a **positive defense contribution** is essential and, if it works, materially improves publishability.

**Weaknesses**
- The core novelty is still modest; domain transfer alone is a re-skin.
- The current parameterization entangles **area**, **SP/FR regime**, and **blending**.
- CarDD creates a threat-model ambiguity: are you measuring **severity inflation on already damaged cars** or **new damage fabrication on intact surfaces**?
- The copy-paste control is insufficient on its own; pipeline/compositing artifacts could dominate.
- The defender-stack claim overreaches given that the proposed base data do not support strong EXIF/PRNU/provenance conclusions.
- The metric protocol is not yet operationally rigorous enough for black-box detector comparison.
- The ethics story is improved but still exposed by E8 and overly detailed laundering/editor sweeps.

**Questions for Authors**
- Are your edits applied on top of existing real damage, on intact nearby regions, or both? The answer changes the threat model materially.
- How exactly is `synthetic-pixel fraction` defined for SP and FR? Right now `100% = FR` is not well-posed.
- What is the authentic negative distribution used to set the 0.1% and 1% FPR thresholds? Does it include benign screenshots, chat-app re-encodes, night mode, HDR, and other realistic claimant behaviors?
- What no-op or sham controls will you use to prove the detector is not simply keying on your compositing/harmonization pipeline?
- On what data will you support any EXIF/PRNU/provenance statements, given CarDD’s limitations?
- How will you ensure that realism is not confounded with edit size, editor, or blending level?

**Soundness / Contribution / Presentation**
- Soundness: **3/5**
- Contribution: **3/5**
- Presentation: **4/5**

**Overall Score**
**3/6 (Weak Reject)** on a WIFS/IH&MMSec-style scale where `1 = Strong Reject` and `6 = Strong Accept`.

**Confidence**
**4/5**

**What would move this toward accept**
- Separate **damage inflation** from **damage injection**, and separate **area** from **SP/FR** from **compositing**.
- Replace vague precision claims with a locked **low-FPR calibration protocol** and explicit prevalence sensitivity.
- Make **E7** real, simple, and cross-editor, with held-out evaluation.
- Cut scope and dual-use risk: auto-focused paper, no public E8, no exhaustive evasion-style breakdowns.

---

**C. Results-to-Claims Matrix**

| Experiment | Outcome | Defensible claim | Not defensible |
|---|---|---|---|
| **E1: Domain transfer** | **Strong** | Vehicle-claim screening has a real low-FPR blind spot for localized damage edits; the claim-photo domain is an operationally important stress case. | “This discovers a new phenomenon” or “all localized-edit detectors universally fail.” |
| **E1: Domain transfer** | **Weak** | Known localized-edit failure transfers to vehicle claims; the value is benchmarking at deployment-style operating points. | “Damage photos are uniquely harder than prior generic inpainting domains.” |
| **E1: Domain transfer** | **Null** | Some frontier damage edits leave detectable local artifacts; the interesting story becomes which editors/pipelines fail to erase them. | C1 as written, or a broad “defender-stack slip” headline. |
| **E2: Size curve** | **Strong** | There is an operational MDEF at low FPR, and realistic damage edits often fall below it. | A universal cross-domain law unless you test far beyond auto. |
| **E2: Size curve** | **Weak** | Size matters, but only conditionally on editor/compositing/laundering; report conditional thresholds, not one global MDEF. | A clean monotonic one-number threshold story. |
| **E2: Size curve** | **Null** | Area is not the dominant variable; other cues such as pipeline, compression, or semantics dominate detectability. | C2 as written, or “smallness” as the core explanatory mechanism. |
| **E7: Defense** | **Strong** | A simple localization-first/content-aware defense materially improves low-FPR detection on held-out editors and thus gives the paper a positive contribution. | “The problem is solved” or “the defense is robust in general” without stronger external validation. |
| **E7: Defense** | **Weak** | The benchmark reveals a promising direction, but not yet a deployable mitigation. | A strong practical-defense claim, or TIFS-level method contribution. |
| **E7: Defense** | **Null** | Current passive defenses remain inadequate; the benchmark defines an open problem. | Any positive defense claim, and likely the paper’s acceptability at stronger venues. |

---

**D. Minimal Experiment Package With Highest Acceptance-Lift per GPU-Week**

1. **Auto-only core benchmark first.**
Use CarDD only for the main paper, and explicitly split **damage inflation** and **damage injection**. If you cannot do that split, the paper is conceptually weaker.

2. **Run a clean E2 before anything broad.**
Use one strong frontier editor, one classical/generative control, SP only at first, and edited-area bins like `{0.5, 1, 2, 5, 10}%`. This gives you the most publishable curve fastest.

3. **Add mandatory controls, not more editors.**
The best extra spend is a **no-op/sham pipeline control**, the **copy-paste control**, and a small **realism audit**. These buy far more credibility than a 4th editor or 3rd commercial API.

4. **Evaluate a small but serious detector panel.**
One open whole-image detector, one localizer aggregated to image-level, one reconstruction/classical baseline, and **one** commercial API is enough for an MVP. Breadth beyond that is diminishing-return filler.

5. **Make E7 the second pillar, not an afterthought.**
Train the simplest plausible patch/content-aware defense and test it on a held-out editor. If E7 is null, you still have a benchmark paper; if E7 is strong, you move much closer to accept.

6. **Keep laundering tiny in v1.**
Do **JPEG85** and **screenshot** only. Cut messenger matrices and generative-SR from the first submission unless they are central to a real claim-submission channel you can justify.

7. **If you have one extra week of effort, spend it on a small phone-captured supplement, not on more GPU sweeps.**
A 50-100 image, multi-phone supplement with real EXIF and benign post-processing is far more valuable than another editor/laundering axis because it rescues the operational-metrics and defender-stack story.

8. **Treat receipts as optional transfer, not co-equal MVP.**
If the auto paper is strong, add a small receipt transfer slice late. Do not let a second domain dilute the main result before the auto benchmark is sound.

**Bottom line:**
There is a publishable paper here, but only as a **tight, operational, auto-focused measurement study with a real low-FPR protocol and a credible recovery baseline**. If you keep the current breadth, many reviewers will read it as a thin re-skin with confounds.
