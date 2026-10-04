# CLAIMFORGE / REKEY Detector Smoke Test and Literature Notes

Date: 2026-06-22

This is an internal working note. It consolidates the current literature landscape,
the detector/API smoke tests we ran on REKEY outputs, and the immediate implication
for the CLAIMFORGE benchmark direction.

No API keys or secrets are recorded here.

---

## 0. 中文结论

这轮结果是有价值的，但结论要摆正：

- 不能声称“我们首次发现局部编辑会让检测器失效”。这个现象已有 benchmark 和论文支持。
- 可以声称“已有工作主要覆盖通用图像、通用 inpainting 或文档/票据；真实理赔损伤照片上的小面积 AI 损伤注入/扩大，还没有被系统 benchmark 化。”
- 我们现在的 REKEY smoke test 给了一个很好的先验信号：在同一张图的 paired source/composite 设置下，商业 whole-image AI detector 和 Illuminarty localized output 都没有对极小局部编辑产生可靠响应。

当前最重要的下一步不是继续在 V* 图上扩很多张，而是把流程迁移到真正的 CLAIMFORGE pilot：

1. 选 20-50 张真实车损/车体照片。
2. 用前沿编辑器生成 damage injection / damage inflation。
3. 保存 source、composite、pixel edit mask。
4. 跑 Sightengine、Illuminarty localized、Copyleaks、Hive/Reality Defender。
5. 报 paired score delta、localized hit rate、低 FPR 下的 recall。

---

## 1. Prior Benchmarks We Should Not Overclaim Against

There are already benchmarks/papers showing that localized AI edits and inpainting
are hard for standard detectors. The opening for CLAIMFORGE is not the generic
phenomenon; it is the insurance/damage-domain operational stress test.

| Work | What it shows | What it does not cover for us |
|---|---|---|
| INP-X, arXiv:2602.00192 | Restoring real pixels outside the inpaint mask collapses whole-image detectors. Reported drops include Hive 91.4 -> 54.8, Sightengine 92.6 -> 55.0, Corvi2023 94.2 -> 55.4, SPAI 66.1 -> 54.2. | Generic faces/scenes. No fraud domain, no damage photos, no operational claim-photo defender stack. |
| Detecting Localized Deepfakes, arXiv:2512.16688 | Detector performance is near chance for very small masks; performance recovers as mask area grows. | General inpainting detection. Not insurance/fraud, not damage photos, no commercial API deployment framing. |
| AIForge-Doc, arXiv:2602.20569 | Document/financial-form fraud analogue. AI tampering of receipt/form fields causes strong detector degradation. | Documents only. It is close in fraud framing, but not physical damage photos. |
| DiQuID / SAGI-D, arXiv:2502.06593 | Large-scale inpainted-image benchmark with original images, masks, SP/FR split, human deceptiveness. | COCO/RAISE/OpenImages; no insurance/damage semantics. |
| COCO-Inpaint, arXiv:2504.18361 | COCO inpainting benchmark with multiple inpainters including Flux.1-Fill / BrushNet / PowerPaint; cross-model localization drops. | Generic COCO objects. Not damage fraud. |
| TGIF / TGIF2, arXiv:2407.11566 / 2603.28613 | Text-guided edits, SP vs FR, FLUX hardness, generative-SR laundering in TGIF2. | Generic images/web images. No claim-photo damage domain. |
| DiffSeg30k, arXiv:2511.19111 | 30k diffusion-edited COCO images, pixel masks, multiple editors, multi-turn edits. | General image edits. No auto/property damage fraud setting. |

Working positioning:

> Prior work establishes that localized AI edits are a detector weakness. CLAIMFORGE
> asks whether this weakness persists in the high-risk claim-photo setting, where the
> base image is authentic, the edit is a tiny physical-damage injection/inflation, and
> the defender cares about low-FPR operation and localization, not just AUROC.

---

## 2. What We Tested So Far

This was a demo/smoke test, not a full benchmark. Inputs were 5 existing REKEY
composites generated with `gpt-image-2` from `results/benchmark/bench2`.

Each test was paired: matched original source image vs REKEY composite.

| image | edit | source | composite |
|---|---|---|---|
| `vstar_0024` | add yellow flag | `ls-data/media/upload/1/145845ad-vstar_0024.jpg` | `results/benchmark/bench2/vstar_0024__bench2/artifacts/composite.jpg` |
| `vstar_0034` | add brown umbrella | `ls-data/media/upload/1/c1f16e5e-vstar_0034.jpg` | `results/benchmark/bench2/vstar_0034__bench2/artifacts/composite.jpg` |
| `vstar_0046` | add brown bench | `ls-data/media/upload/1/50b48f52-vstar_0046.jpg` | `results/benchmark/bench2/vstar_0046__bench2/artifacts/composite.jpg` |
| `vstar_0101` | replace buoy to purple | `ls-data/media/upload/1/88bd035f-vstar_0101.jpg` | `results/benchmark/bench2/vstar_0101__bench2/artifacts/composite.jpg` |
| `vstar_0187` | replace street lamp to red and van to orange | `ls-data/media/upload/1/9ff0fc13-vstar_0187.jpg` | `results/benchmark/bench2/vstar_0187__bench2/artifacts/composite.jpg` |

The edits are extremely small in pixel terms:

| image | pixels changed >20 RGB levels | pixels changed >50 RGB levels |
|---|---:|---:|
| `vstar_0024` | 0.018% | 0.001% |
| `vstar_0034` | 0.012% | 0.001% |
| `vstar_0046` | 0.304% | 0.102% |
| `vstar_0101` | 0.054% | 0.017% |
| `vstar_0187` | 0.066% | 0.024% |

Result files:

- `results/claim_forensics_smoke/summary.md`
- `results/claim_forensics_smoke/source_composite_diff_stats.jsonl`
- `results/claim_forensics_smoke/sightengine_genai.jsonl`
- `results/claim_forensics_smoke/illuminarty_classify.jsonl`
- `results/claim_forensics_smoke/illuminarty_internal_localization.jsonl`
- `results/claim_forensics_smoke/illuminarty_localization_eval.jsonl`

---

## 3. Detector/API Results

### 3.1 Strong VLM Black-Box Forensics

Models were asked to classify the image as real, locally edited, fully AI-generated,
or unsure, without seeing the source image or edit mask.

| model | valid outputs | verdicts |
|---|---:|---|
| `openai/gpt-4.1` | 5/5 | real, real, real, real, real |
| `anthropic/claude-sonnet-4.6` | 5/5 | real, real, real, real, real |
| `qwen/qwen3.7-plus` | 5/5 | real, real, real, real, real |
| `google/gemini-2.5-flash` one-word | 5/5 | REAL, REAL, REAL, REAL, REAL |
| `google/gemini-2.5-pro` | unstable | several invalid/empty outputs |

Interpretation:

- Strong general VLMs did not spontaneously identify these REKEY images as locally edited.
- This is not a detector benchmark, but it is useful as a sanity check: semantic visual inspection alone is not enough.

### 3.2 Hugging Face Whole-Image Detector

Model: `capcheck/ai-image-detection`.

| image | composite top label | composite score | matched source top label | matched source score |
|---|---:|---:|---:|---:|
| `vstar_0024` | FAKE | 0.848 | FAKE | 0.848 |
| `vstar_0034` | FAKE | 0.718 | FAKE | 0.723 |
| `vstar_0046` | FAKE | 0.739 | FAKE | 0.731 |
| `vstar_0101` | FAKE | 0.769 | FAKE | 0.779 |
| `vstar_0187` | FAKE | 0.780 | FAKE | 0.792 |

Interpretation:

- This detector fires on both originals and composites with near-identical scores.
- It is not detecting the REKEY edit. It is a domain/format false-positive baseline on these V* images.
- This supports the need for paired source/composite evaluation and low-FPR calibration.

### 3.3 Sightengine `genai`

Endpoint used:

```bash
POST https://api.sightengine.com/1.0/check.json
models=genai
media=@image.jpg
```

Credentials were supplied via environment variables and are not recorded.

| image | source `ai_generated` | REKEY composite `ai_generated` | delta |
|---|---:|---:|---:|
| `vstar_0024` | 0.001 | 0.001 | 0.000 |
| `vstar_0034` | 0.001 | 0.001 | 0.000 |
| `vstar_0046` | 0.001 | 0.001 | 0.000 |
| `vstar_0101` | 0.001 | 0.001 | 0.000 |
| `vstar_0187` | 0.001 | 0.001 | 0.000 |

Notes:

- All 10 requests returned `status=success`.
- Each request consumed 5 operations.
- Sightengine assigns the floor score to both matched originals and REKEY composites.

Interpretation:

- Sightengine `genai` did not detect these local edits.
- This is expected for a whole-image AI-generated detector, but it is important because Sightengine is a mature commercial baseline.

### 3.4 Illuminarty `image/classify`

Public API endpoint:

```bash
POST https://api.illuminarty.ai/v1/image/classify
Header: X-API-Key: ...
Form: file=@image.jpg
```

| image | source probability | REKEY composite probability | delta |
|---|---:|---:|---:|
| `vstar_0024` | 0.003 | 0.003 | +0.000 |
| `vstar_0034` | 0.306 | 0.319 | +0.013 |
| `vstar_0046` | 0.039 | 0.039 | +0.000 |
| `vstar_0101` | 0.029 | 0.029 | +0.000 |
| `vstar_0187` | 0.047 | 0.048 | +0.001 |

Interpretation:

- Illuminarty classify gives low AI probabilities to all REKEY composites.
- The source-to-composite deltas are zero or tiny.
- It does not produce a reliable detection signal for the local edit.

### 3.5 Illuminarty Localized Output

The public API docs only expose `image/classify`, but the web app uses an internal
analysis endpoint that returns localization points:

```bash
POST https://app.illuminarty.ai/api/analysis/image?apiKey=...
Form: file=@image.jpg
```

This returns:

```json
{
  "data": {
    "probability": 0.003,
    "details": {
      "breakdown": {"human": 0.997, "...": 0.0},
      "localization": [[152, 176], [256, 352], [424, 152]]
    }
  }
}
```

The web app renders these localization points as large translucent circles. We mapped
the points back to original image coordinates and compared them with the REKEY edit boxes.

| image | source p | composite p | delta | loc identical | point inside edit box | circle intersects edit box | min point-edit distance |
|---|---:|---:|---:|---|---|---|---:|
| `vstar_0024` | 0.003 | 0.003 | +0.000 | True | False | False | 350.9 px |
| `vstar_0034` | 0.306 | 0.319 | +0.013 | True | False | False | 606.6 px |
| `vstar_0046` | 0.039 | 0.039 | +0.000 | True | False | False | 479.3 px |
| `vstar_0101` | 0.029 | 0.029 | +0.000 | True | False | False | 712.6 px |
| `vstar_0187` | 0.047 | 0.048 | +0.001 | True | False | True | 124.3 px |

Overlay images:

- `results/claim_forensics_smoke/illuminarty_localization_overlays/`
- Green = REKEY edit box.
- Red = Illuminarty localized circles.

Interpretation:

- For every matched pair, source and composite localization points are identical.
- The localization does not move toward the REKEY edit.
- No localization point lands inside the edit box.
- In one case (`vstar_0187`) a large displayed circle intersects an edit box, but the same circle is present on the source image and the point itself remains outside the edit boxes. This is not evidence of detecting the edit.

### 3.6 Metadata / ELA Sanity Check

Basic metadata and JPEG recompression residuals were computed with Pillow.

Observation:

- REKEY composites have no EXIF, only JFIF metadata.
- Matched original V* source images also have no useful EXIF.
- ELA-style residual statistics are effectively the same for source and composite.

Interpretation:

- Cheap metadata/ELA checks do not separate these small local edits.
- This is expected for the V* setup and should not be overinterpreted for real phone claim photos, where EXIF/provenance may matter.

---

## 4. What This Demonstrates

The smoke test supports three useful statements:

1. Whole-image AI-generated detectors can miss tiny local edits when most pixels are authentic.
2. Commercial detector scores should be evaluated in a paired source/composite design; raw high or low scores alone are not meaningful.
3. A product having localized output does not mean it localizes the actual AI-edited region. In this test, Illuminarty localized points were unchanged between source and composite.

This does not yet prove CLAIMFORGE. It only validates the experiment direction.

---

## 5. What This Does Not Yet Prove

Current limitations:

- The tested images are REKEY V* images, not claim-photo damage images.
- The edits are object/color edits, not damage injection/inflation.
- We tested only 5 pairs.
- No detector threshold was calibrated against a large negative set.
- No low-FPR recall is reported yet.
- No commercial fraud stack was fully modeled.
- We have not run Copyleaks, Hive, Reality Defender, TruFor, CAT-Net, AEROBLADE, or PRNU-based methods.

Therefore this result should be used as:

- a pilot signal,
- an API integration check,
- a motivation for a damage-domain benchmark,

not as a final paper result.

---

## 6. API Status and What To Get Next

Already tested:

| API / method | Status | Result |
|---|---|---|
| OpenRouter VLMs | ran | strong VLMs call images real |
| Sightengine `genai` | ran | all source/composite scores 0.001 |
| Illuminarty `image/classify` | ran | low probabilities, no meaningful delta |
| Illuminarty internal localized analysis | ran | localized points identical between source/composite |
| HF `capcheck/ai-image-detection` | ran | false-positive on both source and composite |
| metadata / ELA sanity | ran | no separation |

Next APIs to arrange:

| Priority | API | Why |
|---|---|---|
| 1 | Copyleaks AI Image Detection | Claims partial AI detection and mask/RLE-style output. Most directly relevant after Illuminarty localized failed. |
| 2 | Hive AI-generated image detection | Used in INP-X; useful for literature alignment. Can use direct Hive API or NVIDIA NIM route if available. |
| 3 | Reality Defender | Enterprise/fraud-oriented detector; useful for defender-stack framing. |
| 4 | Google AI Content Detection | Worth applying for, but private preview and should not block work. |

Do not put keys in tracked files. Use environment variables or a local `.env`.

---

## 7. Recommended Next Experiment

Minimum CLAIMFORGE pilot:

1. Select 20-50 real auto/claim-style images.
2. Split edit types:
   - damage injection: add a dent/scratch/crack to an otherwise plausible intact area.
   - damage inflation: enlarge or intensify an existing damage region.
3. Generate each edit with one or two frontier editors.
4. Store:
   - source image,
   - composite image,
   - pixel edit mask,
   - edit type,
   - edited-area percentage,
   - editor/model,
   - prompt family,
   - accept/reject QA label.
5. Run:
   - Sightengine,
   - Illuminarty classify + localized,
   - Copyleaks,
   - Hive,
   - one or two open localization models if setup cost is acceptable.
6. Report:
   - paired source/composite score delta,
   - recall at fixed FPR using source negatives,
   - localized hit rate against edit mask,
   - false positives on authentic damage photos,
   - failure examples.

First claim to test:

> On authentic claim-style photos with tiny AI-added or AI-inflated damage, mature
> commercial AI-image detectors and localized outputs show little or no paired
> response to the manipulated region.

If the claim holds on the damage pilot, CLAIMFORGE has a defensible benchmark story.

---

## 8. Links and Local References

Local docs:

- `docs/claim_forensics/experiment_plan.md`
- `docs/claim_forensics/references.md`
- `docs/claim_forensics/review_round1.md`

Smoke test outputs:

- `results/claim_forensics_smoke/summary.md`
- `results/claim_forensics_smoke/sightengine_summary.md`
- `results/claim_forensics_smoke/illuminarty_summary.md`
- `results/claim_forensics_smoke/illuminarty_localization_summary.md`

External references:

- INP-X: https://arxiv.org/abs/2602.00192
- Detecting Localized Deepfakes: https://arxiv.org/abs/2512.16688
- AIForge-Doc: https://arxiv.org/abs/2602.20569
- DiQuID / SAGI-D: https://arxiv.org/abs/2502.06593
- COCO-Inpaint: https://arxiv.org/abs/2504.18361
- TGIF: https://arxiv.org/abs/2407.11566
- TGIF2: https://arxiv.org/abs/2603.28613
- DiffSeg30k: https://arxiv.org/abs/2511.19111
- Sightengine genAI docs: https://sightengine.com/docs/ai-generated-image-detection
- Illuminarty image API docs: https://app.illuminarty.ai/docs/analysis
