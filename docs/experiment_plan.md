# V* Leakage and Dynamic V* Experiment Plan

Date: 2026-05-04

This document is the forward-looking experiment plan. Completed results are recorded in `docs/experiment_results.md`.

## 中文执行摘要

当前我们已经有一个可以支撑第一版 arXiv 的基本事实：在同一个 official-like full-resolution V* setting 下，Qwen3.6-Plus 在原始 V* label 上是 90.6%，但在我们完整人工重标后的 V* split 上降到 75.4%。这说明新标注集已经能作为一个有效的静态 stress test。

下一步分两条线推进：

1. 用当前完整人工重标 split 横向测试更多模型，形成主结果表。模型应覆盖 Qwen、OpenAI、Gemini/Claude、Kimi、Doubao/Seed、MiMo 和至少一个 open-weight VLM。每个模型都跑 original V*、human relabeled V*，并配套 no-image prior/control。
2. 提出 Dynamic V* 方法，解决“静态重标数据集未来也会泄漏”的问题。核心做法是在 V* 图像上先标注大量可编辑区域和坐标框，再用局部生成/修图模型在这些区域中按语义插入小物体，最后根据生成元数据自动构造 V*-style question/answer。这样每次评测都能生成新的目标对象和答案，避免固定题目被训练或记忆。

第一版论文可以把人工重标 split 作为实验证据，把 Dynamic V* 作为方法贡献；如果时间允许，再做 100 道左右的 Dynamic V* pilot 来展示方法可行性。

## Current Starting Point

We now have a complete human relabeled V* split:

- raw append-only annotations: `data/annotations/vstar_relabel.jsonl`
- latest-per-question annotations: `data/annotations/vstar_relabel_latest.jsonl`
- total latest items: 191
- validation issues: 0

Current Qwen3.6-Plus official-like result on this split:

| split | model | correct / total | accuracy |
|---|---|---:|---:|
| original V* labels | `qwen/qwen3.6-plus` | 173 / 191 | 90.6% |
| final human relabeled V* | `qwen/qwen3.6-plus` | 144 / 191 | 75.4% |

The relabeled split gives us a concrete, reproducible signal:

- The same images and same official-like evaluation path produce a large drop after the question/answer targets are changed.
- `direct_attributes` remains hard: 80 / 115 = 69.6%.
- `relative_position` is no longer trivial after rewriting: 64 / 76 = 84.2%.
- This is a usable first artifact for a short arXiv version.

## Core Claim For The First Version

We should avoid overclaiming that any single model has definitively memorized V*. The cleaner claim is:

1. Some models show no-image answer concentration on repeated/conflicting V* stems.
2. Qwen3.6-Plus reproduces the official V* score under an official-like setting.
3. When the same images are paired with human relabeled questions and answers, Qwen3.6-Plus drops from 90.6% to 75.4%.
4. Static relabeling is only a temporary defense because the relabeled split can itself leak once released or evaluated repeatedly.
5. Therefore, we propose Dynamic V*: a benchmark generation procedure that creates fresh V*-style visual questions from image-region annotations and localized generative edits.

## Next Experiment: Cross-Model Evaluation On The New Relabeled Split

### Model Matrix

Run the final relabeled split on multiple model families. Use OpenRouter model IDs when available, but verify the exact IDs before running.

Priority groups:

| group | purpose | examples |
|---|---|---|
| Qwen | main target and family ablation | Qwen3.6-Plus, strongest Qwen VL available, smaller Qwen VL if available |
| OpenAI | strong closed-model control | GPT-5.5, GPT-5.4-mini, GPT-4.1-mini or current equivalents |
| Gemini | strong closed-model control | Gemini Pro / Flash current equivalents |
| Claude | strong closed-model control | Claude Sonnet / Haiku current equivalents |
| Kimi | model family that showed motorcycle concentration | Kimi latest / K2.x current equivalents |
| Doubao / Seed | Chinese model family control | current ByteDance Seed / Doubao multimodal model |
| MiMo | model family that showed motorcycle concentration | latest MiMo multimodal model if available |
| open VLMs | open-weight controls | InternVL, LLaVA, Qwen-VL open variants, MiniCPM-V, Phi-Vision if available |

The minimum viable table for arXiv should include:

- Qwen3.6-Plus
- one strong OpenAI model
- one strong Gemini or Claude model
- Kimi
- Doubao / Seed
- MiMo
- one open-weight VLM

### Evaluation Conditions

Use a single primary setting for all models:

- original image bytes from V*
- no resizing
- no JPEG re-encoding
- no system prompt unless the provider requires one
- dataset-native answer suffix: `Answer with the option's letter from the given choices directly.`
- temperature 0
- one run per item
- max tokens 16 first, then rerun unparsed items with 512 or 1024
- parse only explicit option letters, with existing parser rules

For models that frequently reason before answering, allow longer completion budgets but keep the prompt unchanged. Record this as an output-budget accommodation, not a different task.

### Metrics

For every model, report:

- overall accuracy on 191 relabeled items
- accuracy by category: `direct_attributes`, `relative_position`
- accuracy by option count: 2-choice, 4-choice
- first 32 vs remaining items
- parse rate
- output choice distribution
- cost and latency when available

For key models, also report paired comparisons against:

- original V* label result on the same model
- relabeled result

Useful paired statistics:

- original-correct-only count
- relabel-correct-only count
- both-correct / both-wrong
- McNemar exact binomial test
- choice agreement

### Leakage-Oriented Controls

For each model family, run three related probes:

1. Original V* with image.
2. Human relabeled V* with image.
3. Human relabeled V* without image.

The without-image condition is not an accuracy benchmark. It measures answer priors and possible dataset exposure. For no-image runs, use repeated sampling at low temperature:

- temperature 0 or 0.1
- 20 repeats per item for the small 191-item split
- strict answer-only system prompt where supported
- report single-option concentration and true-label concentration

### Expected Interpretations

Possible outcome patterns:

- High original V*, low relabeled V*: model may rely on original benchmark familiarity, original target distribution, or brittle visual grounding.
- High original V*, high relabeled V*: strong genuine visual reasoning on this split.
- Low no-image, high image: visual evidence is doing the work.
- High no-image concentration on relabeled labels after release: relabeled split is no longer safe as a static benchmark.

We should not equate all score drops with leakage. The relabeled questions can also be intrinsically harder. The stronger argument is that static benchmark scores are fragile and need dynamic generation.

## Dynamic V*: Proposed Method

### Motivation

The human relabeled split is useful now, but it is still static. If it is released, repeatedly evaluated, or included in future training mixtures, it can leak exactly like the original V*.

Dynamic V* solves this by generating fresh benchmark instances at evaluation time. The model cannot memorize the exact answer because the queried object or relation does not exist until the benchmark is instantiated.

### High-Level Idea

Start from V* images or similar high-resolution scene images. Annotators mark many semantically meaningful regions:

- beaches, shorelines, sidewalks, road edges
- park paths, benches, lawns, plazas
- tables, counters, shelves
- empty wall areas, signs, vehicles, windows
- foreground/background objects suitable for relative-position questions

Each region is annotated with:

- coordinates or polygon/mask
- semantic region label
- plausible object categories that can be inserted there
- scale constraints
- occlusion/depth constraints
- allowed question types

At evaluation time, a generator inserts small plausible objects into selected regions. Then the system creates V*-style questions about those inserted objects and their relations to existing scene objects.

Examples:

- Insert a red bucket near the edge of a beach.
- Insert a blue water bottle on a park path.
- Insert a small yellow sign beside a scooter.
- Insert a toy boat above/below an existing object in the image plane.

This creates a fresh visual target and answer for each evaluation run.

## Dynamic V* Data Construction

### Stage 1: Region Annotation

For each source image, create many candidate edit regions.

Annotation fields:

```json
{
  "image_id": "vstar_00123",
  "region_id": "r07",
  "geometry": {
    "type": "box",
    "xyxy": [x1, y1, x2, y2]
  },
  "semantic_region": "beach_shoreline",
  "depth": "middle_ground",
  "surface": "sand",
  "occlusion_risk": "low",
  "allowed_insertions": ["bucket", "towel", "bottle", "small sign"],
  "forbidden_insertions": ["car", "large furniture"],
  "question_types": ["direct_attribute", "relative_position"],
  "anchor_objects": [
    {
      "name": "blue umbrella",
      "xyxy": [x1, y1, x2, y2]
    }
  ],
  "notes": ""
}
```

Start with boxes. Add polygons/masks only where boxes are too coarse.

Minimum target for a first dynamic prototype:

- 50 source images
- 10 regions per image
- 500 editable regions
- at least 3 allowed object categories per region

### Stage 2: Object and Attribute Library

Create a controlled object library with visual attributes.

Object schema:

```json
{
  "object": "bucket",
  "allowed_regions": ["beach_shoreline", "park_path", "sidewalk"],
  "attributes": {
    "color": ["red", "blue", "yellow", "green"],
    "material": ["plastic", "metal"],
    "size": ["small", "medium"]
  },
  "negative_options": {
    "color": ["black", "white", "orange"],
    "material": ["wood", "cloth"]
  }
}
```

The library should avoid ambiguous fine-grained labels at first. Use objects and attributes that humans can verify quickly.

### Stage 3: Localized Image Generation

Use an image generation or inpainting model to edit only the annotated region.

Generation inputs:

- original image
- mask or box
- semantic prompt
- negative prompt
- size/depth instruction
- optional reference object style

Example generation prompt:

```text
Insert a small red plastic bucket naturally sitting on the sand near the beach shoreline.
Keep the rest of the image unchanged. Match lighting, perspective, and shadows.
```

Quality requirements:

- inserted object is visible
- object is inside the annotated region
- object is semantically plausible for the region
- no major changes outside the mask
- no duplicate or distorted object artifacts
- target attribute is unambiguous

### Stage 4: Automatic Question Generation

Generate questions from the inserted object and region metadata rather than asking a language model to infer the answer.

Question templates:

Direct attribute:

```text
What is the color of the small bucket near the beach shoreline?
(A) red (B) blue (C) yellow (D) green
```

Relative position:

```text
Is the small red bucket to the left or right of the blue umbrella?
(A) left (B) right
```

Above/below:

```text
Is the small sign above or below the bicycle basket?
(A) above (B) below
```

Closer/farther:

```text
Which is closer to the camera, the red bucket or the blue umbrella?
(A) red bucket (B) blue umbrella
```

The answer should be computed from coordinates and metadata, not manually guessed.

### Stage 5: Human Verification

Every generated item needs a lightweight human check:

- Is the inserted object visible?
- Is the target object uniquely identifiable?
- Is the attribute answer correct?
- Are distractor options plausible but wrong?
- For relative-position questions, is the relation unambiguous?
- Did generation modify unrelated parts of the image?

Use a three-way label:

- accept
- fix prompt / regenerate
- reject region

For paper numbers, report acceptance rate and common rejection reasons.

## Dynamic V* Evaluation Protocol

### Static Seeded Split

For reproducibility, create a fixed seeded dynamic split:

- fixed source images
- fixed region annotations
- fixed generation seed list
- fixed generated images
- released only after the paper submission or kept private for evaluation

This allows reviewers to reproduce reported numbers.

### Live Dynamic Split

For leakage resistance, create fresh instances at evaluation time:

- sample source image
- sample region
- sample object and attributes
- generate localized edit
- generate question from metadata
- verify automatically and optionally with human spot checks
- evaluate model

The live split is the benchmark contribution. The static seeded split is for reproducibility.

### Anti-Leakage Argument

Dynamic V* is leakage-resistant because:

- the exact target object is generated after benchmark construction
- answer labels are determined by fresh edits and coordinates
- the same source image can produce many distinct target questions
- released region annotations do not reveal future generated objects or attributes

Important caveat:

- If generated images and questions are released as a static set, that specific set can leak. The leakage-resistant object is the generation procedure plus private seeds, not any one frozen output file.

## Experiments For Dynamic V*

### Experiment A: Generation Quality

Measure:

- object visibility rate
- region containment rate
- semantic plausibility
- attribute clarity
- human acceptance rate
- outside-mask change rate

Target for a first version:

- at least 70% generation acceptance after one generation attempt
- at least 90% after up to three attempts

### Experiment B: Model Performance On Static Relabel vs Dynamic V*

Run the same model matrix on:

- original V*
- human relabeled V*
- static seeded Dynamic V*
- live Dynamic V*

Report whether dynamic generated items further reduce scores, especially for models with high original V* performance.

### Experiment C: No-Image Prior Control

Run no-image repeated sampling on Dynamic V* questions.

Expected result:

- no-image accuracy should be close to random
- no-image true-label concentration should be low
- if a model performs well only with image, the benchmark is measuring visual grounding

### Experiment D: Region and Object Ablations

Ablate:

- direct attribute vs relative position
- small objects vs medium objects
- foreground vs background regions
- left/right vs above/below vs closer/farther
- natural object insertion vs deliberately unusual insertion

### Experiment E: Generator Leakage / Artifact Control

Check whether models exploit generator artifacts:

- compare multiple generators if possible
- include real unedited V* questions mixed with generated questions
- randomize object categories and colors
- test whether a model can detect generated patches
- evaluate with crop-only and full-image variants

## Paper Structure

Proposed arXiv structure:

1. Introduction
   - Static multimodal benchmarks can leak.
   - V* is a useful case study because official scores are high and repeated stems expose suspicious no-image behavior.

2. Empirical Evidence On V*
   - no-image repeated-stem answer concentration
   - motorcycle case as an illustrative example
   - cross-model no-image controls

3. Human Relabeled V*
   - annotation procedure
   - validation
   - Qwen3.6-Plus drop from 90.6% to 75.4%
   - cross-model evaluation table

4. Why Static Relabeling Is Not Enough
   - the new split can itself leak over time
   - repeated public evaluation creates benchmark exposure

5. Dynamic V*
   - region annotation
   - localized generation
   - metadata-grounded question generation
   - human verification

6. Experiments
   - generation quality
   - model results
   - no-image controls
   - ablations

7. Limitations
   - generator artifacts
   - human verification cost
   - possible distribution shift from generated objects
   - need for private seeds or live evaluation server

8. Conclusion
   - static benchmark relabeling is a short-term patch
   - dynamic visual benchmark generation is the long-term defense

## Immediate To-Do List

1. Run cross-model official-like evaluation on the final human relabeled split.
2. Add paired original-vs-relabel summaries for each model.
3. Build a small region annotation format for Dynamic V*.
4. Annotate 50 images with boxes and semantic region tags.
5. Prototype localized generation on 20 image-region pairs.
6. Create template-based question generation from metadata.
7. Human-verify the first 100 dynamic items.
8. Run Qwen3.6-Plus and two controls on the 100-item dynamic pilot.
9. Decide whether to present Dynamic V* as a pilot method or as a full benchmark in the first arXiv version.
