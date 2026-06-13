# Related Work and Differentiation — Dynamic V*

This note distills the VLB literature read into the positioning we will
write in the paper, and updates the methodological story to match the
implementation shift we now plan: **instruction-based image editing
(gpt-image-1)** in place of mask-based inpainting (FLUX.1 Fill). The
deeper analyses live in `../vlb_deep_dive.md` and `../literature_review.md`.

## 1. VLB — the only directly overlapping prior work

### 1.1 Motivation (VLB's framing, in their words)

Static multimodal benchmarks have two coupled defects:

- **Fixed complexity.** A fixed test set cannot follow models up the
  difficulty curve; once the strongest models saturate it, the benchmark
  stops discriminating.
- **Data contamination.** Static items leak into pretraining corpora; the
  reported score may reflect memorization, not capability.

VLB proposes a **dynamic** evaluation where every original item
`(I, Q, A)` can be re-instantiated into a new
`(𝒱(I), ℒ(Q), A)` whose answer must remain `A`. Re-running the
benchmark with fresh perturbations yields a moving target that resists
contamination and supports controllable difficulty by stacking
perturbations.

### 1.2 Method — 7 atomic operators plus a judge gate

| family | op | difficulty | mechanism |
|---|---|---|---|
| visual | 𝒱₁ Add Object | hard | GPT-4V picks `(object, bbox)` at gen time → bbox→mask → PowerPaint inpaints |
| visual | 𝒱₂ Remove Object | easy | SAM segments the image → Set-of-Mark prompts GPT-4V to pick a removable mask → PowerPaint erases |
| visual | 𝒱₃ Outpaint / expand FoV | hard | extend canvas with PowerPaint at ratio r=1.5 by default |
| language | ℒ₁ Word substitution | hard | synonym swap |
| language | ℒ₂ Sentence rephrase | hard | GPT-4V rewrites Q in chosen voice |
| language | ℒ₃ Add relevant context | easy | GPT-4V adds a caption-like preface that does not contain the answer |
| language | ℒ₄ Add irrelevant context | hard | GPT-4V adds a topical but answer-irrelevant preface |

Operators compose freely: 12 dyadic 𝒱×ℒ pairs, plus same-modality
stacking like `𝒱₃(𝒱₁(I))`, give a smooth difficulty axis.

The **judge** is a single InternVL-2 instance: it receives the original
`(I, Q, A)`, the perturbed `(𝒱(I), ℒ(Q))`, and a description of the
perturbation, and answers a binary "is `A` still correct?" Up to five
retries; if the judge says "No" five times, **VLB silently substitutes
the original vanilla item back**.

The ground-truth answer is **never re-derived**; it is whatever the
seed benchmark already labelled. The judge is a consistency gate, not
an oracle.

### 1.3 Three critical weaknesses we will exploit

1. **Silent vanilla fallback.** A "dynamic" item is not always
   transformed; if the judge rejects 5 times, the score for that
   slot is computed on the unchanged original. The reported delta
   between vanilla and dynamic understates the dynamic difficulty
   because hard-to-perturb items don't move.
2. **Judge ≡ evaluatee.** InternVL-2 sits in the judge role *and* in
   the evaluation table. Reviewers (OpenReview thread on
   `X1OfiRYCLn`) raised the circularity; the paper still shipped Oral
   without ablating it out.
3. **Tautological "contamination reduction".** Their headline
   contamination-reduction figure (Figure 8) re-runs their own
   CLIPScore≥0.9 detector against LAION/CC3M/COCO-Cap and observes
   that perturbed images no longer match. This proves the perturbation
   shifted pixels, not that any LVLM training pipeline contained those
   originals to begin with.

The 𝒱₁ failure mode in Appendix A.14 is independently informative:
GPT-4V's bbox prediction has a saliency bias toward centred, prominent
positions, producing pathological insertions like a laptop blocking a
cat or a balloon obscuring a face. **This is empirical evidence that a
generator-time GPT-4V loop cannot fill the role of pre-annotated
difficulty-controlled regions.**

## 2. Dynamic V* — methodological choices (revised)

### 2.1 Generation backend: gpt-image-1, not FLUX.1 Fill

The original `generation_design.md` selected FLUX.1 Fill for
mask-based inpainting. We now plan to use **gpt-image-1 / gpt-image-2**
through an instruction-based edit endpoint, accessed via a proxied
OpenAI-compatible API (no separate inference stack to host). The trade
is honest:

- **Pro** — single endpoint, single key, no diffusers / GPU
  orchestration; the same API is already wired into our cross-model
  evaluation pipeline.
- **Pro** — modern instruction-tuned editing handles "natural
  language placement" cues like "next to the red flowerpot" well; we
  do not need to construct binary masks.
- **Con** — instruction-based edits do not strictly preserve pixels
  outside the intended region; we cannot promise "only the marked
  region changed." We will report drift as part of QC.
- **Con** — with no mask, structural depth control via mask shape
  (the anchor-overlap zeroing we had planned) is no longer available.
  Position relations must be honoured purely through language.

### 2.2 Pipeline in four stages

1. **Annotation** (Label Studio, self-hosted) produces a JSONL row per
   image with anchors, insertables, and pairwise position relations.
   Spec is `../annotation_spec.md`.
2. **Sampling** picks one insertable region, samples a category and
   attributes from the schema's allowed lists, and records seed and
   metadata.
3. **Prompt construction** assembles a single instruction string from
   the schema:
   - bbox centre → `"in the upper-right area"`-style spatial qualifier
   - `semantic_region` → scene context phrase
   - sampled `category, color, scale, material` → object phrase
   - `position_relation` `(rel, target)` → natural-language clause
     such as `"next to the red flowerpot"` or `"partially behind the
     blue umbrella"`
   - explicit "do not change anything else" directive
4. **Image edit** posts the original V* image plus the instruction
   prompt to the gpt-image-1 edits endpoint; the result is stored
   alongside the metadata used to compute ground-truth answers.
5. **Question generation** is the schema-driven template engine
   (deterministic; no judge): `(category, color)` →
   direct-attribute Q; `(insertable bbox, anchor bbox)` → left/right
   or above/below; `position_relation` graph → closer/farther under
   transitive closure.

The loss of mask construction means failure cases will be more visible
than under FLUX.1 Fill; the upside is that the entire pipeline is
text-only and reproducible from one API.

## 3. Differentiation against VLB (revised for gpt-image-1)

The earlier four-point differentiation collapses to three, and one of
them weakens. We restate them honestly:

### 3.1 Pre-annotated insertable + anchor inventory with V* difficulty criteria

VLB has no equivalent. Their region selection is a one-shot GPT-4V
call at generation time, with no human curation, no V*-style
small-peripheral-cluttered constraint, and no reuse across runs. The
A.14 fail cases show the natural failure mode of that loop. Our
inventory is reusable, satisfies V* difficulty criteria by
construction, and is auditable.

**Strength:** unambiguously novel relative to VLB. A reviewer cannot
collapse "human-curated metadata-driven generator" into "VLB with a
better prompt."

### 3.2 Programmatic, judge-free question generation from bbox geometry + sampled metadata

VLB's pipeline preserves the seed answer and perturbs around it; ours
constructs a new question whose ground truth comes from the sampled
attribute (for direct-attribute) or from bbox arithmetic (for
relative position) or from the position-relation DAG (for
closer/farther). No language model is required to verify the answer.

This is **orthogonal to VLB's philosophy**, and it eliminates the
silent vanilla-fallback failure mode: there is no "did the perturbation
break the answer?" question to fail; the answer is constructed by the
schema.

**Strength:** unambiguously novel; the strongest of our three remaining
differentiators.

### 3.3 V* high-resolution small-target regime

VLB ran on SEEDBench, MMBench, MME — moderate-resolution multi-task
VQA. They do not address the V* setting at all. V* is the canonical
benchmark for small-target search in cluttered high-resolution images;
nobody has yet shown how to regenerate items in that regime.

**Strength:** clean positional novelty, but only as long as we
demonstrate the V*-specific value (e.g., that VLB-style 𝒱₁ on V*
fails by inserting in centre-large regions). We will reproduce a
VLB-𝒱₁ baseline on V* as the "without our anchor-aware annotation"
control.

### 3.4 What we *lost* by switching to gpt-image-1

The original "anchor-aware mask preserves occlusion at the pixel
level" point dissolves. Position relations now live in the prompt as
language (`"partially behind the blue umbrella"`), and gpt-image-1
honours them only as well as it honours instructions in general. This
is **not a stronger differentiator than VLB's language-side ℒ
operators**, because both are language conditioning of a generator.

We should not advertise occlusion fidelity as a contribution; we
should report empirically how often gpt-image-1 honours occlusion and
treat it as a measurable property of the dataset rather than a method
claim.

## 4. Required controls (gating experiments)

These are not optional ablations; reviewers will ask, and the absence
of any single one will reset the paper to "speculative."

### 4.1 Cross-generator transfer

Run the benchmark with at least two generators of different family —
gpt-image-1 (instruction-based, OpenAI lineage) and FLUX.1 Fill
(diffusion inpainting, BFL lineage) — and report whether model
ranking is preserved across them. Item-level disagreement is an
expected confound to quantify. Rank-stability across generators is
the strongest single sentence we can write to defend "we measured
visual understanding, not generator artefacts."

### 4.2 Detection-shortcut probe

Train a small classifier (or query a held-out VLM) to discriminate
vanilla V* images from gpt-image-1-edited ones. If AUC ≥ 0.7, we
cannot publish the headline accuracy table without ablating
detection ability; reviewers will (correctly) read the score as
edit-detection, not understanding. Target: AUC ≤ 0.6.

### 4.3 Reproducibility variance

Run the full benchmark generation pipeline at three independent seeds
on the same model set; report the per-model standard deviation. If
σ exceeds the gap between any two models in our headline table, that
gap is not significant.

### 4.4 (Specific to gpt-image-1) Mask-out-of-region drift

Pixel-diff each output image against the original V*. Report the
fraction of bbox-outside pixels that change by more than ε. This
quantifies our concession in §2.1: with no mask, drift is real; we
need to know how much.

## 5. Paper framing

### 5.1 Minimum survivable claim

> "Dynamic V* is the first regenerative VLM benchmark targeted at the
> high-resolution fine-detail (small-target search) regime, with
> human-curated insertable+anchor inventories satisfying V* difficulty
> criteria, and a judge-free programmatic question generator that
> constructs ground truth from sampled attributes and bbox geometry."

Three differentiators, no more. The instruction-based generation
backend is an implementation choice; we will report it but not lead
on it.

### 5.2 What we explicitly do not claim

- Not "leakage-resistant generation in general." VLB owns that.
- Not "first dynamic VLM benchmark." LiveXiv / LiveVQA / VLB
  predate us.
- Not "perfect occlusion preservation." gpt-image-1 makes no such
  guarantee, and the paper will not pretend otherwise.
- Not "open-set object insertion." Our object library is closed and
  controlled by design; that is a feature for difficulty calibration,
  not a generality claim.

### 5.3 Must-cite list (final)

VLB (2410.08695), LiveXiv (2410.10783), LiveVQA (2504.05288),
AutoBench-V (2410.21259), MMStar (2403.20330), MM-Detect (2411.03823),
Multi-Modal Semantic Perturbations (2511.03774), V*Bench
(2312.14135), CLEVR (CVPR 2017), GQA (CVPR 2019), FragFake
(2505.15644), SAGI (2502.06593), Paint-by-Inpaint (CVPR 2025),
PowerPaint (Zhuang et al. 2023, VLB's backbone).

### 5.4 Audit-only fallback paper

If at any point the differentiators above stop adding up — e.g., the
detection-shortcut probe reveals a high AUC and we cannot recover —
we still have a smaller paper consisting of:

- the V* contamination audit (no-image probing,
  stem-seen-label concentration, motorcycle case),
- the cross-model relabel evaluation
  (Qwen3.6-Plus 90.6% → 75.4%, plus the 7 other MVP models),
- a discussion section describing Dynamic V* as planned future work.

This is the safest minimum-viable paper; it does not require
generation to succeed and stands alone as a stress test of V*.
