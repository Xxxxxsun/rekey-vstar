# Dynamic V* — Method Overview

Date: 2026-05-12
Status: implemented, tested on 191 images

## Core Idea

Static visual benchmarks leak — once a (image, question, answer) triple is
in training data, models memorize it. Dynamic V* makes the answer space
non-enumerable by editing images at evaluation time:

1. **Replace** existing objects' colors (red bicycle → green bicycle)
2. **Add** new objects that don't exist in the original image

Both operations preserve V*'s visual search difficulty (small, hidden targets
in cluttered scenes) while making the answer unpredictable.

## Pipeline Architecture

```
Annotated JSONL (human-labeled regions + target_refs)
        │
        ├── Sampler: pick slot(s), sample color
        │     • Replace: parse old color from target_ref, sample new color (VAW-filtered)
        │     • Add: pick object from annotator's candidate list, sample random color
        │     • Dedup: exclude objects already used by other slots in same image
        │
        ├── Rule Planner: generate QA + edit prompts (no LLM)
        │     • Color Q: "What color is the {object}?" (strip color from target_ref)
        │     • Position Q: "Is the {A} to the left or right of {B}?" (no color)
        │     • Position fallback: above/below when left/right indistinguishable
        │     • Edit prompt: "Change ONLY the color of X to Y" / "Add a {color} {object}"
        │
        ├── Image Generator: crop → edit API → restore
        │     • Context crop (blue box) provides scene context
        │     • Edit region (orange box) guides placement
        │     • Soft mask compositing: only paste edit region, blur edges
        │
        └── Output: composite image + QA metadata
```

## Annotation Schema

Two box types per image:

- **Blue box** (context_region): crop area for the image model, letter ID (A/B/C)
- **Orange box** (edit_region): target area, ID = letter+number (A1/B1/C1)

### Replace Mode

Annotator writes `target_ref` in format `{color} {object}`:

```
red bicycle                        → Q: What color is the bicycle?
blue jacket on the cyclist         → Q: What color is the jacket on the cyclist?
orange-and-white lifebuoy          → Q: What color is the lifebuoy?
```

### Add Mode

Annotator checks candidate objects (grouped by placement) that DON'T exist
in the image. Pipeline randomly selects one + random color.

```
Candidate pool per placement:
  Ground:  bag, bucket, umbrella, bottle, box, bicycle, scooter, stroller, dog, cat
  Table:   cup, bowl, phone, flower
  Wall:    poster, sign, clock, flag
  Water:   boat, buoy, bird
  Air:     bird, balloon, kite, flag
```

## Question Types

### Color (direct_attributes, 1 slot)

```
target_ref: "red bicycle"
sample: new_color = "green"
→ Q: "What color is the bicycle?"
→ A: "green"
→ Options: (A) green (B) purple (C) black (D) yellow
→ Edit: "Change ONLY the color of the red bicycle to green."
```

- Distractors exclude old color + new color + multi-color components
- VAW filter prevents implausible colors (e.g., green dog)
- Distractors drawn from full COLORS pool (wrong options don't need to be plausible)

### Position (relative_position, 2 slots)

```
slot A: "red bicycle" (center_x=100)
slot B: "white car" (center_x=500)
→ Q: "Is the bicycle to the left or right of the car?"
→ A: "left"
```

- Questions use object name only, no color
- Sub-items inverted: "blue jacket on the cyclist" → "the cyclist"
- Fallback to above/below when dx < dy
- Two slots guaranteed different objects (dedup)
- Two slots guaranteed different new colors (also_exclude)

## Image Generation

### Edit Prompts

```
Replace: "Change ONLY the color of the {old} {object} to {new}.
          Do NOT modify any surrounding pixels.
          Keep shape, material, texture, and background exactly the same."

Add:     "Add a {color} {object} in the marked area,
          sized naturally for the scene context.
          Do NOT modify any pixels outside the marked area.
          Keep the background exactly the same."
```

### Compositing

Uses soft mask to prevent background bleed:

1. Crop context region from source image
2. Send to image editing API with guide overlay
3. Restore generated content to crop coordinates
4. **Soft mask**: only paste within edit region (orange box) + 12px expand + 8px Gaussian blur
5. Outside mask: original pixels preserved exactly

## Data

- 191 V* images annotated
- 267 replace slots (115 attr + 152 position)
- 145 add slots (position images)
- 23 unique add object types across 5 placements
- 11 colors in sampling pool

## Results (Qwen3.6-Plus, first run)

|              | Original V* | Relabel V* | Dynamic V* |
|--------------|-------------|------------|------------|
| Overall      | 90.6%       | 75.4%      | 80.7%      |
| Attr         | 90.4%       | 69.6%      | 76.7%      |
| Position     | 90.8%       | 84.2%      | 87.3%      |

Dynamic V* with color-only attr is easier than relabel (multi-type).
Cross-model ranking comparison pending.

---

## VLM Annotator Experiment (Ablation)

### Purpose

Prove that using a VLM as annotator (instead of human) introduces selection bias,
validating our design choice of human-in-the-loop annotation.

### Experimental Setup

**VLM Annotator**: GPT-5.5 via OpenRouter, given the same instructions as human annotators.

For each of the 191 V* images, GPT-5.5 outputs:
- 2 replace targets (existing objects to recolor)
- 2 add regions (empty areas + candidate objects)

Same constraints as human annotators:
- Objects should be small, hidden, hard-to-find
- Must be uniquely identifiable
- Add candidates must not exist in the image
- Same allowed object pool

**Pipeline**: Both benchmarks use identical pipeline:
rule planner → image edit API → soft mask compositing

### Comparison Metrics

| Metric | Human bench | VLM bench | What it proves |
|--------|-----------|-----------|---------------|
| Target object area (avg px) | Expected: small | Expected: larger | VLM picks salient objects |
| Invalid question rate | ~16% | Expected: >25% | VLM misses uniqueness |
| Qwen3.6-Plus accuracy | 75.8% | Expected: >80% | VLM bench is easier |
| Uniqueness error rate | 2.7% | Expected: >10% | VLM can't verify uniqueness |
| Object size distribution | Skewed small | Skewed large | Selection bias |

### Key Figure

Scatter plot: X = target object area, Y = VLM accuracy
- Human annotations: spread across small sizes
- VLM annotations: clustered at large sizes with high accuracy
→ Visual proof of selection bias

### Expected Conclusion

> "Using a VLM as annotation oracle conditions the benchmark on the 
> annotator model's visual attention. Objects selected by the VLM are
> systematically larger and more salient, resulting in a benchmark that
> overestimates model capabilities. Human annotation provides an 
> independent oracle that preserves V*'s visual search difficulty."

### Status

- [ ] Script: `scripts/run_vlm_annotator.py`
- [ ] Run GPT-5.5 annotation on 191 images
- [ ] Convert to pipeline JSONL format
- [ ] Generate VLM-annotated benchmark (image editing)
- [ ] Quality review (10 subagents)
- [ ] Evaluate Qwen3.6-Plus on VLM bench
- [ ] Compute comparison metrics
- [ ] Generate comparison figure
