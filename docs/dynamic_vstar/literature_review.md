# Dynamic V*: External Literature Review and Feasibility Check

Date: 2026-05-04
Scope: 30-45 minute external review of academic and industry sources
relevant to (a) the contamination motivation for Dynamic V* and (b) the
inpainting-based regenerative benchmark proposal in
`docs/experiment_plan.md` and `docs/dynamic_vstar/generation_design.md`.

This document deliberately does not cite our own internal docs as
evidence. Every URL below is external work.

---

## Section 1 — Is benchmark contamination in VLMs a recognized problem?

**Short answer: yes, and it is now a mainstream research subfield.**
Multimodal contamination is recognized at the survey, methodology, and
diagnostic-paper levels in 2024-2026.

### Survey-level recognition

- **"Recent Advances in Large Language Model Benchmarks against Data
  Contamination: From Static to Dynamic Evaluation"** (Yu et al.,
  arXiv 2502.17521, 2025; later EMNLP 2025) is the canonical survey of
  the static-to-dynamic transition. It explicitly motivates the field
  by noting that public benchmarks "may have leaked into LLM/VLM
  training sets, leading to inflated and misleading performance
  metrics." It taxonomizes encryption, post-hoc detection,
  timestamp-based updating, and full regeneration as the four families
  of mitigation.
  https://arxiv.org/html/2502.17521v2 ; ACL: https://aclanthology.org/2025.emnlp-main.511.pdf
- **EMNLP-Findings 2025: "A Systematic Analysis of Data Contamination
  in Multimodal LLMs"** ("Both Text and Images Leaked!"). Across
  ScienceQA, MMStar, COCO-Caption, NoCaps, and Vintage they find
  contamination in 12 MLLMs ranging from minor to severe leakage,
  arising from both the unimodal pretraining and the multimodal
  fine-tuning stage. Method: option-order shuffling and slot-guess on
  back-translated paraphrases.
  https://arxiv.org/html/2411.03823 ; https://aclanthology.org/2025.findings-emnlp.556.pdf

### Detection methodology

- **MM-Detect** (the framework behind the EMNLP-Findings paper above).
  Pioneers the "perform a semantic-irrelevant perturbation, observe
  unusual discrepancy" recipe specifically for multimodal models.
- **"Contamination Detection for VLMs Using Multi-Modal Semantic
  Perturbations"** (arXiv 2511.03774, NeurIPS-track 2025) is the
  closest *methodological* neighbor to Dynamic V*. They use
  Flux-with-ControlNet plus GPT-4o captions to **regenerate
  semantically perturbed images** for RealWorldQA, MMStar, and
  NaturalBench, and measure performance drops as a contamination
  signal. They explicitly use diffusion-based image perturbation (not
  inpainting) as the contamination probe.
  https://arxiv.org/html/2511.03774
- **"Benchmark Designers Should 'Train on the Test Set' to Expose
  Exploitable Non-Visual Shortcuts"** (arXiv 2511.04655, 2025). They
  fine-tune a *blind* (no-image) LLM on the test set itself and find
  blind models gain +33.3 points on CV-Bench and +31.4 on VSI-Bench
  through pattern learning, exposing benchmark fragility to non-visual
  shortcuts. They make explicit the no-image probing methodology.
  https://arxiv.org/html/2511.04655
- **MMStar** (Chen et al., NeurIPS 2024, arXiv 2403.20330). Defines
  "Multi-modal Leakage" (ML) and "Multi-modal Gain" (MG) metrics. They
  use 8 LLMs as no-image inspectors to filter out questions that any
  three could answer, demonstrating that the no-image-as-leakage-probe
  pattern is established practice.
  https://arxiv.org/html/2403.20330.pdf ; https://mmstar-benchmark.github.io/
- **"Benchmarking Benchmark Leakage in Large Language Models"**
  (arXiv 2404.18824, 2024). Background reference for the same idea on
  LLM-only benchmarks.
  https://arxiv.org/html/2404.18824v1
- **MicroVQA** (Burgess et al., 2025). Documented case where GPT-4o
  scored ~90% on questions *with no image*, motivating their
  redesign. Cited often as a "smoking gun" for image-unnecessary
  benchmark questions. https://jmhb0.github.io/microvqa/

### V* specifically — has anyone audited it?

- We did not find a paper *dedicated* to auditing V*Bench. V*Bench (Wu
  & Xie, CVPR 2024) is referenced as the canonical 191-image
  high-resolution attribute/spatial benchmark on arxiv and the project
  page (https://arxiv.org/abs/2312.14135 ; https://vstar-seal.github.io/)
  but **no dedicated leakage audit, replication, or relabel paper for
  V* turned up in 30-45 minutes of search.** This is a real gap.
- V*Bench appears as a sub-benchmark in `inspect_evals` and
  `VLMEvalKit`, both of which treat it as a black-box accuracy number.
  https://ukgovernmentbeis.github.io/inspect_evals/evals/multimodal/vstar_bench/
- The "saturation evidence" we have collected is consistent with the
  general phenomenon flagged by MMStar and the NeurIPS-track 2025
  contamination paper, but no public citation of V*-specific leakage
  exists as of this review's cutoff.

**Net finding for Section 1.** The contamination problem is real,
recognized, and actively studied. V* itself is not the object of a
dedicated audit paper, so a V*-focused leakage study is a defensible
contribution.

---

## Section 2 — Has anyone proposed dynamic / regenerative VLM benchmarks?

**Short answer: yes, including at least one prior work that uses
inpainting-based object addition on real images. This is the most
important finding of this review.**

### LLM-only live benchmarks (the parents)

- **LiveBench** (White et al., ICLR 2025; arXiv 2406.19314). Monthly
  refreshed LLM-only benchmark with verifiable ground-truth answers.
  18 tasks, 6 categories. Top models <70%. Defines the recurring-update
  template that LiveXiv and LiveVQA imitate.
  https://livebench.ai/livebench.pdf ; https://arxiv.org/abs/2406.19314
- **LiveCodeBench**. The code-domain twin. Time-stamped problem
  inclusion. https://livecodebench.github.io/
- **R-Bench** (arXiv 2505.02018). Olympiad-level multilingual reasoning
  benchmark; the "R" stands for reasoning, not regenerative. Not the
  same idea as ours. https://arxiv.org/abs/2505.02018
- **DARG** (NeurIPS 2024) and **DyCodeEval** (ICML 2025) and
  **BeyondBench** (ICLR 2026, arXiv 2509.24210). These adapt LLM
  benchmark questions by graph perturbation (DARG), agent rephrasing
  (DyCodeEval), or algorithmic problem generation with provable
  uniqueness (BeyondBench).
  https://arxiv.org/html/2406.17271 ; https://arxiv.org/html/2503.04149 ;
  https://arxiv.org/abs/2509.24210

### VLM live / regenerative benchmarks

- **LiveXiv** (Shabtay et al., ICLR 2025; arXiv 2410.10783). A monthly
  refreshed VLM benchmark built from new arXiv papers. Pipeline:
  Docling parses PDFs into structured documents, GPT-4o generates VQA
  pairs over charts/tables/diagrams, Claude-Sonnet filters for
  consistency. **Images are natural (extracted from arXiv papers), not
  generated.** This is the canonical "Live" VLM benchmark.
  https://arxiv.org/abs/2410.10783 ; https://research.ibm.com/blog/live-VQA-benchmark
- **LiveVQA** (Sui et al., arXiv 2504.05288, 2025). 107k samples
  across 12 categories, drawn from news, YouTube, and arXiv published
  April 2024 - May 2025. Multi-stage MLLM-in-the-loop pipeline with
  human validation. Again, **natural images** sourced from the
  internet at evaluation time. https://arxiv.org/abs/2504.05288 ;
  https://livevqa.github.io/
- **AutoBench-V** (Bao et al., arXiv 2410.21259, 2024-25). LVLMs
  benchmark themselves using **text-to-image generated** images
  (Stable Diffusion-style). GPT-4o orchestrates VQA tasks. Synthetic
  scenes throughout. https://arxiv.org/abs/2410.21259 ;
  https://autobench-v.github.io/
- **MMGenBench** (arXiv 2411.14062, 2024). Closely related; LMMs are
  evaluated by their ability to interpret and regenerate
  text-to-image-generated content. https://arxiv.org/html/2411.14062
- **Vision-Language Bootstrapping (VLB)** — Sun et al., arXiv 2410.08695,
  ICLR-track 2025. **This is the closest published prior work to our
  proposal.** See Section 3 for the full overlap analysis. They
  bootstrap MMBench/SEEDBench/MME by **adding new objects via
  PowerPaint inpainting (with BrushNet as alternative)**, removing
  existing objects, expanding images, and rephrasing questions; an
  InternVL-2 judge maintains consistency. Reported drops 4-8% on hard
  variants. https://arxiv.org/html/2410.08695v1 ;
  https://openreview.net/pdf?id=X1OfiRYCLn

### Dynamic-adversarial-collection antecedents

- **Dynabench** (Meta, NeurIPS 2021; later ML Commons). Human-and-model
  in-the-loop adversarial data collection. Different mechanism (humans
  craft adversarial examples) but the same "static benchmarks rot"
  motivation. https://dynabench.org/

**Net finding for Section 2.** The space is crowded. LiveXiv and
LiveVQA cover the "natural image" niche; AutoBench-V and MMGenBench
cover the "fully synthetic" niche; **VLB occupies the
"inpaint-real-images" niche that our proposal aims at.** The next
section examines VLB in detail.

---

## Section 3 — Closest prior work to our specific pipeline

This section ranks the closest external prior work to our specific
pipeline (anchor + insertable bbox annotation, inpaint a sampled object
into one insertable region, emit VQA from metadata) and explains the
overlap and remaining differentiation.

### 3.1 Vision-Language Bootstrapping (VLB) — the strongest overlap

- Paper: "Dynamic Multimodal Evaluation with Flexible Complexity by
  Vision-Language Bootstrapping," arXiv 2410.08695 (Oct 2024,
  ICLR-track 2025). https://arxiv.org/html/2410.08695v1 ;
  https://openreview.net/pdf?id=X1OfiRYCLn
- **What it does that we also do.** Bootstraps an existing
  multiple-choice VQA benchmark by:
  1. Adding objects via inpainting (PowerPaint, with BrushNet as
     alternative; **the same family of model we plan to use**).
  2. Removing objects and expanding images as additional image-side
     transformations.
  3. Rephrasing questions and adding context as language-side
     transformations.
  4. Filtering with a VLM judge (InternVL-2) that the new
     image+question still has the same answer (or revises the
     answer). Up to 5 retries before falling back to the original.
- **What it does that we do not.** Modifies *existing* benchmark
  samples (so the new image is treated as a counterfactual variant of
  an existing question), targets MMBench / SEEDBench / MME (not V*),
  and reports modest drops (4-8% on the hardest composition setting).
- **What we do that it does not.** (Possible differentiators we have
  to defend.)
  1. Pre-annotated "insertable" empty-region inventory plus an
     "anchor" inventory with metadata. VLB selects insertion regions
     dynamically; we annotate them up front for difficulty control.
     (Open question: is "manually marked insertable region" a
     defensible methodological contribution, or just a more
     labor-intensive variant of VLB's automatic region selection?)
  2. Metadata-grounded ground-truth answer for the new question (we
     compute the answer from sampled object attributes plus bbox
     coordinates; VLB uses a VLM judge to *re-derive* the answer).
     This is genuinely different and should be highlighted: ours is
     "automated programmatic question generation" in the CLEVR sense,
     applied to inpainted real photos; VLB's is "VLM judge in the
     loop."
  3. V*-specific difficulty preservation rules (small-object,
     peripheral, cluttered). VLB does not target high-resolution
     small-target benchmarks.
- **Concrete recommendation:** Treat VLB as the must-cite primary
  related work. If we proceed with Dynamic V*, the framing must call
  out and contrast VLB explicitly. If we cannot articulate what is
  better than VLB beyond "we target a different source benchmark," the
  contribution is weak.

### 3.2 Contamination Detection via Multi-Modal Semantic Perturbations
(arXiv 2511.03774, 2025).

- Closest *methodologically* on the contamination-detection axis.
  Uses Flux + ControlNet + GPT-4o captions to perturb whole images
  (not localized inpainting). Differs from our pipeline because they
  regenerate the whole image with a Canny/edge constraint, not insert
  a single sampled object into an annotated empty region.
  https://arxiv.org/html/2511.03774
- **Implication.** We can cite this as evidence that "image-side
  perturbation as a contamination probe" is publishable, while
  positioning Dynamic V* as the localized, metadata-grounded version
  of the same idea.

### 3.3 Programmatic VQA on real photos

- **CLEVR** (Johnson et al., CVPR 2017). The progenitor of programmatic
  VQA. Synthetic 3D scenes + scene graph + functional programs.
  https://cs.stanford.edu/people/jcjohns/clevr/
- **GQA** (Hudson & Manning, 2019). Programmatic VQA on real photos
  (Visual Genome). Scene graphs are real-image annotations, questions
  are templated. The closest existing precedent for programmatic VQA
  on real images. We are not the first to combine "templated questions
  + scene metadata + real images" — GQA is. Our novelty is the
  *inpainting + metadata-grounded answer* angle, not "template VQA on
  real photos."
- **Generate Any Scene** (arXiv 2412.08221, 2024). Scene-graph-driven
  VQA pair generation, but for text-to-image *training* data, not for
  real-photo benchmarks. https://arxiv.org/html/2412.08221v2

### 3.4 Inpainting-based augmentation for evaluation (not training)

- **VLB** (already covered). Uses PowerPaint for object addition.
- **The Counterfactual VQA Dataset** (XAITK / SRI). 484 GAN-edited
  VQA-v2 images with 4 inpaint types, but explicitly for *explanation*
  research, not contamination defense.
  https://xaitk.org/capabilities/SRI-counterfactual
- **Visual Jenga** (arXiv 2503.21770, 2025). Counterfactual inpainting
  to *remove* objects to study object dependency. Not a benchmark; a
  scene understanding task. https://arxiv.org/html/2503.21770

### 3.5 Object insertion methods (not benchmarks)

- **Paint by Inpaint (PIPE)** — Wasserman et al., CVPR 2025. ~1M
  pairs, 1400+ object classes. **A training dataset and method, not a
  benchmark.** Ours uses a different control surface (we have masks
  from annotation) and a different objective (eval, not training).
  https://arxiv.org/abs/2404.18212 ; https://rotsteinnoam.github.io/Paint-by-Inpaint/
- **AnyDoor** (CVPR 2024). https://arxiv.org/abs/2307.09481
- **Paint by Example** (CVPR 2023). https://arxiv.org/abs/2211.13227
- **ObjectStitch** (CVPR 2023). https://arxiv.org/abs/2212.00932
- **ObjectDrop** (ECCV 2024, arXiv 2403.18818). Counterfactual
  removal/insertion fine-tuning. https://arxiv.org/html/2403.18818
- **PowerPaint** (ECCV 2024). The model VLB uses.
  https://github.com/open-mmlab/PowerPaint
- **FLUX.1 Fill** (BFL, Nov 2024). The model we plan to use.
  https://bfl.ai/flux-1-tools/

None of the above are *benchmarks*; they are insertion/removal
*methods*. They appear in our related-work as "inpainting backbones"
not as competing benchmarks.

### 3.6 Set-of-Mark and grounding probes

- **Set-of-Mark Prompting** (Yang et al., arXiv 2310.11441). Visual
  grounding via SAM/SEEM-driven mark overlays. Not a benchmark
  generator; orthogonal to our pipeline.
  https://arxiv.org/abs/2310.11441 ; https://github.com/microsoft/SoM

---

## Section 4 — Risks and limitations the literature has surfaced

These are the literature-documented risks Dynamic V* will face. We
list them in priority order.

### 4.1 Inpainting artifacts as a shortcut (highest priority)

- **"Can VLMs Detect and Localize Fine-Grained AI-Edited Images?"**
  (arXiv 2505.15644, 2025). Constructs FragFake, a 98k-image
  benchmark of AI-edited images including FLUX outputs. Pretrained
  GPT-4o has ~45-46% Object Precision detecting edited objects;
  fine-tuned Qwen2.5-VL reaches 72-86% depending on dataset. **Subtle
  edits remain hard; salient ones trivial.** This is concerning
  evidence that VLMs *can* recognize inpainting once they have any
  cue. https://arxiv.org/html/2505.15644
- **SAGI** (arXiv 2502.06593, 2025) and **DiQuID**. A 95k inpainted-
  image detection benchmark using 8 inpainting models across 5
  pipelines; contains FLUX-Fill outputs. Provides evidence that
  inpaint-detection is an active research area with high accuracy in
  some settings. https://arxiv.org/html/2502.06593v1
- **Implication for us.** The risk that a VLM "answers correctly"
  because it spots the inpainted region (effectively localizing an
  edit and reading off the edit content) is real. Our `generation_design.md`
  Sections 2.3, 2.4, and 5 already enumerate this risk; the
  literature confirms it is not theoretical. Mitigation paths:
  (i) Use multiple generators and randomize, exactly as in our
  Experiment E; (ii) Insert real objects via copy-paste from a paired
  real image as a control (this is a common trick in the
  edit-detection literature); (iii) Include a baseline of "ask the
  model to localize the inpainting region" and check whether that
  correlates with answer correctness.

### 4.2 Generator-style giveaway and oversaturation

- **"AI-Generated Image Detectors Overrely on Global Artifacts"**
  (linked from our generation_design.md as 2602.00192). Modern
  detectors latch onto global VAE-induced spectral shift. We avoid
  the *crop-and-paste* failure mode but still have a residual
  full-image spectral signature. The literature confirms that this
  signature is detectable in principle.
- **Implication.** The benchmark requires a genuine "real images
  among inpainted images" mixing strategy; otherwise a model that
  simply detects "this image has been processed by FLUX" would
  ace the benchmark.

### 4.3 Stochasticity / reproducibility of dynamic benchmarks

- **VLB**'s judge module retries up to 5 times on rejection, which
  introduces reproducibility cost. The paper notes this as a
  limitation but does not provide a scoring-stability quantification
  across run_ids. This is a documented gap in the regenerative-VLM
  literature and an opportunity for our static-seeded split.
- **LiveBench** and **LiveCodeBench** address this by version-tagging
  each monthly cohort, which we should mirror for the static seeded
  split.
- **The contamination survey** (arXiv 2502.17521) explicitly flags
  reproducibility as the #1 weakness of regenerative benchmarks.
- **Implication.** Our seeded run_id design with `pipeline_version`
  in the seed (already in `generation_design.md` Section 4) is on
  the right track but must be empirically validated by reporting
  inter-run accuracy variance for at least 3 distinct run_ids on a
  held set of models.

### 4.4 Closed-library / fixed-vocabulary generalization concerns

- **MMStar** (NeurIPS 2024) sets the precedent for "small curated
  benchmark with strong vision-dependence guarantees" but does not
  use generation. The literature on closed-vocabulary benchmarks
  flags two failure modes:
  1. **Vocabulary leakage to training time.** If our `OBJECT_LIBRARY`
     is published, future training data will include those object
     categories preferentially, exactly the same leakage problem
     applied one level up (object-library leakage instead of
     question leakage).
  2. **Reduced generalization claim.** Models that score well on a
     20-30 object library cannot be claimed to "generalize to all
     objects." This is a known limitation of CLEVR-style benchmarks
     (https://cs.stanford.edu/people/jcjohns/clevr/).
- **Implication.** We need to either keep the library private and
  expand it over time (operationally hard) or scale it past the
  20-30 size in `generation_design.md` Section 1.4 and acknowledge
  the limitation in the paper.

### 4.5 Synthetic patches deflate or inflate scores in misleading ways

- **"Measuring Robustness to Natural Distribution Shifts in Image
  Classification"** (NeurIPS 2020;
  https://proceedings.neurips.cc/paper/2020/file/d8330f857a17c53d217014ee776bfd50-Paper.pdf).
  Foundational result: *synthetic robustness measures do not imply
  natural robustness.* A model that does badly on synthetic
  perturbations is not necessarily a model that does badly on real
  novel data. This is the most cited prior work on the
  synthetic-vs-real gap.
- **Implication.** A lower Dynamic V* score does not unambiguously
  imply "the model has memorized V* less well"; it could mean "the
  model is brittle to FLUX inpainting style." We need (i) a control
  with a different generator (Experiment E in our plan), and (ii) a
  paired real-image control where the inserted object is a true
  cropped object from another photo.

### 4.6 Cross-editor transfer drops

- **FragFake transfer experiments** (arXiv 2505.15644, again).
  Localization performance drops sharply across editor styles. This
  is good news for benchmark robustness (a model trained on FLUX
  cannot trivially detect SDXL-Fill outputs) but it cuts both ways:
  if we use a single generator, a model fine-tuned to recognize that
  generator's quirks could ace our benchmark.
- **Implication.** The "use multiple generators" recommendation in
  Experiment E is not optional. It is required for the benchmark
  claim to be defensible.

### 4.7 V* questions specifically about high-resolution small targets

- V* targets are <2% of the image (Wu & Xie, CVPR 2024,
  https://arxiv.org/abs/2312.14135). Inserting a small object into a
  cluttered region is exactly what FLUX-Fill is *not* benchmarked
  most strongly on; small-mask FLUX runs are known to produce
  duplicate objects or oversize inserts (referenced in our
  `generation_design.md` Section 5). The literature does not have a
  clean small-mask FLUX benchmark.
- **Implication.** Our 70%-on-first-try / 90%-after-three retry
  budget may be optimistic. A cheap pre-experiment that measures
  small-mask success rate on 100 V* regions before committing is
  prudent.

### 4.8 Question-side leakage via VLM judges

- **VLB**'s use of an InternVL-2 judge to verify answer consistency
  is a closed-loop concern. If the same judge family is in the
  evaluated model pool, the benchmark measures judge-agreement, not
  ground truth.
- Our `generation_design.md` Section 7 already calls this out and
  proposes using a different family for QC than the family being
  benchmarked. This is the same issue VLB has and our explicit
  resolution would be a citable methodological improvement.

---

## Section 5 — Verdict

### 5.1 Is the idea novel?

**Partially novel.** It is *not* fully novel: the core mechanism
(inpaint a new object into a real benchmark image, then automatically
update the VQA answer, then evaluate VLMs on the modified
samples) is published as VLB (arXiv 2410.08695, ICLR-track 2025;
PowerPaint inpainting + InternVL-2 judge on
MMBench/SEEDBench/MME). Two further closely related groups exist:

1. **LiveXiv** (ICLR 2025) and **LiveVQA** (2025) cover the
   "natural-image refresh" niche. Different mechanism (no
   generation), same motivation.
2. **AutoBench-V** (2024) and **MMGenBench** (2024) cover the
   "fully synthetic image generation" niche. Different image source
   (text-to-image, not inpaint), same motivation.

The remaining defensible novelty surface for "Dynamic V*" is:

- **(a)** First inpainting-based regenerative benchmark targeted at
  high-resolution **small-target / fine-detail** evaluation (V* as
  the source). VLB does not target this regime; LiveXiv and LiveVQA
  use natural images and do not control object scale; AutoBench-V is
  fully synthetic. This is the strongest claim and the one we should
  build the paper around.
- **(b)** Pre-annotated insertable-region inventory with anchor
  metadata and explicit difficulty constraints. VLB picks regions
  programmatically; ours uses human annotation to control difficulty.
  Whether this is methodologically interesting or merely
  labor-intensive is a defendable but contestable claim.
- **(c)** Metadata-grounded answers (computed from coordinates and
  sampled attributes) instead of VLM-judge re-derived answers.
  This is genuinely different from VLB and arguably more rigorous,
  because it removes the judge-circularity concern.
- **(d)** First V*-specific contamination audit + fix. The audit
  side (relabel + no-image probe) is its own contribution and does
  not appear to be published elsewhere.

### 5.2 Are there fatal flaws documented in adjacent literature?

**No fatal flaws, but two near-fatal risks.** Specifically:

1. **Inpainting artifacts as a shortcut** (Section 4.1). FragFake and
   SAGI demonstrate that VLMs can be fine-tuned to detect FLUX-style
   inpainting with high accuracy. We need a hard control proving
   that *our* benchmark scores do not just track inpaint-detection
   ability. Without this control, reviewers will reject. The Section
   2.4 trivial-findability probe and Experiment E in our plan are
   in the right direction but not sufficient — we additionally need
   a "real-image control" where the inserted object is copy-pasted
   from another photo without any diffusion involved, to give us a
   non-FLUX baseline.

2. **Closed-library generalization framing** (Section 4.4). A paper
   claiming "Dynamic V*" should not claim "open-set difficulty"; we
   are using a 20-30 object library that will itself become
   memorizable. The honest framing is "controllable, fine-grained,
   regenerable" *not* "open-set."

Both risks are addressable with the experiments already sketched in
the plan plus one or two additions.

### 5.3 Strongest paper-level positioning

Three positioning options, ranked:

1. **Audit + methodology paper.** Lead with the V*-specific
   contamination audit (no-image probing, relabel split with the
   90.6% to 75.4% drop) as the empirical motivation; present
   Dynamic V* as the methodological response. Cite VLB as concurrent
   prior art and articulate the four differentiators above
   (high-resolution small-target focus, anchor-aware difficulty
   control, metadata-grounded answers, V*-specific). **This is the
   strongest framing.** It is honest about VLB and gives the reader
   a clear reason to publish: V* is *the* canonical hard
   high-resolution benchmark and no one has audited or
   regeneratively-fixed it.

2. **Methods paper only.** Drop the audit, focus on Dynamic V* as a
   benchmark-construction methodology. Risks being subsumed by VLB
   reviewer-side. Not recommended.

3. **Audit-only paper.** Drop Dynamic V*, ship the relabel split
   plus cross-model evaluation as a stress test of V*. Cite the
   contamination survey as motivation. **This is the safest minimum
   viable paper** and is what the experiment plan's "Core Claim For
   The First Version" already articulates. It can be extended into
   a fuller Dynamic V* paper later.

### 5.4 Concrete recommendation

**Proceed, with framing pivots and two added experiments.**

Pivots:

- Frame Dynamic V* as **"the first inpainting-regenerative benchmark
  for high-resolution fine-detail VLM evaluation"** specifically.
  Stop using "leakage-resistant generation" as the headline framing —
  VLB owns that.
- Cite VLB upfront (introduction and related work) and articulate
  the four differentiators (high-resolution / small target;
  anchor-difficulty annotation; metadata-grounded answers; V*-specific
  audit).
- Honest framing on object library: it is *closed-vocabulary,
  controlled-difficulty,* not *open-set.*

Required additional experiments:

- **Inpaint-detection control.** Mix in real images and inpainted
  images at known proportions; show the model's accuracy on the
  inserted-object question is independent of whether the model can
  detect inpainting. (Sanity check that we are not measuring
  inpaint-detection.)
- **Cross-generator robustness control.** Run the benchmark with
  FLUX.1 Fill *and* SDXL-Inpainting *and* a copy-paste control;
  show the relative model ranking is stable. (Already in
  Experiment E of our plan; needs to be elevated to a headline
  experiment, not an ablation.)
- **Reproducibility variance.** Report accuracy across 3 distinct
  run_ids on a fixed model set to quantify regeneration noise.

If the inpaint-detection control fails (model accuracy correlates
strongly with detection ability), we *do* have to stop and rethink.
But the literature does not predict that outcome unambiguously, so
running the control is an honest gating experiment, not a death
warrant.

### 5.5 Must-cite related work

Critical:

- VLB (arXiv 2410.08695). Inpainting-based dynamic VQA. **Treat as
  primary related work; differentiate explicitly.**
- LiveXiv (arXiv 2410.10783, ICLR 2025). Live VLM benchmark from
  arXiv papers.
- LiveVQA (arXiv 2504.05288, 2025). Live VLM benchmark from web
  content.
- AutoBench-V (arXiv 2410.21259, 2024). LVLMs benchmarking themselves
  on text-to-image-generated scenes.
- Static-to-Dynamic Survey (arXiv 2502.17521, EMNLP 2025).
- "Both Text and Images Leaked" / MM-Detect (arXiv 2411.03823,
  EMNLP-Findings 2025).
- Contamination via Multi-Modal Semantic Perturbations (arXiv
  2511.03774, 2025). Closest perturbation-based detection method.
- MMStar (arXiv 2403.20330, NeurIPS 2024). Defines ML/MG metrics.
- "Train on the Test Set" (arXiv 2511.04655, 2025). Blind-LLM
  exploit-detection.
- LiveBench (arXiv 2406.19314, ICLR 2025). LLM-only template parent.
- V* / V*Bench (arXiv 2312.14135, CVPR 2024). The source benchmark.

Important:

- FragFake (arXiv 2505.15644, 2025). VLM detection of AI-edited
  images.
- SAGI / DiQuID (arXiv 2502.06593, 2025). Inpainted-image detection
  benchmark.
- CLEVR (CVPR 2017). Programmatic VQA precedent.
- GQA (CVPR 2019). Programmatic VQA on real photos.
- DARG (NeurIPS 2024). Graph-perturbation dynamic LLM benchmark.
- BeyondBench (ICLR 2026, arXiv 2509.24210). Algorithmic LLM benchmark.
- Dynabench (NeurIPS 2021). Adversarial collection ancestor.
- Paint by Inpaint / PIPE (CVPR 2025). Object-addition method we may
  switch to.
- AnyDoor / Paint-by-Example / ObjectStitch / ObjectDrop. Inpainting
  backbones; cite as background.

---

## Executive summary (60 seconds)

- **Contamination in VLMs is a recognized problem with a mature
  research base in 2024-2026.** Surveys, detection frameworks
  (MM-Detect), perturbation methods (arXiv 2511.03774), and
  vision-indispensable benchmarks (MMStar) all establish the
  motivation; no dedicated V*-specific audit has been published, so
  that part of our work is genuinely under-covered.

- **Our pipeline is partially novel, not fully novel.** Vision-Language
  Bootstrapping (VLB, arXiv 2410.08695, ICLR-track 2025) already does
  inpainting-based regenerative VQA with PowerPaint on
  MMBench/SEEDBench/MME with an InternVL-2 judge. Our contributions
  must be repositioned around (a) high-resolution small-target focus,
  (b) anchor-aware difficulty annotation, (c) metadata-grounded
  answers (no judge circularity), (d) V*-specific audit.

- **The biggest unaddressed risk is "VLMs detect FLUX inpainting and
  short-circuit the question."** FragFake (arXiv 2505.15644) and
  SAGI (arXiv 2502.06593) prove VLMs *can* learn to detect
  inpainting. We must add a real-image / copy-paste control plus a
  cross-generator control before publishing, otherwise reviewers will
  conclude we measured inpaint-detection rather than visual
  understanding.

- **Recommendation: proceed with two framing pivots and two added
  experiments.** Lead with the V*-specific audit; differentiate
  Dynamic V* explicitly from VLB; do not claim open-set
  generalization; add an inpaint-detection control and a
  cross-generator control as headline experiments, not ablations.

- **Safest fallback if reviewers push back: ship just the audit +
  relabel split as the first arXiv version.** That is already a
  novel, defensible contribution given no V*-specific audit exists,
  and the Dynamic V* methodology can be expanded in a follow-up.
