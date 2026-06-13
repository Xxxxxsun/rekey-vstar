# Qwen3.6-Plus V* Human Relabel Evaluation

Date: 2026-05-04

Purpose: test Qwen3.6-Plus on the human relabeled V* questions using the same official-like setting that reproduced the original V* score.

## Relabel Data

Files:
- append-only annotations: `data/annotations/vstar_relabel.jsonl`
- latest snapshot: `data/annotations/vstar_relabel_latest.jsonl`

Validation:

```bash
python scripts/export_vstar_relabels.py
```

Output:
- `input_rows=505`
- `latest_rows=191`
- `validation_issues=0`

Current relabel status:
- all 191 V* items have latest human relabel annotations
- the final annotation pass includes rewritten relative-position questions through `qid=190`
- relative-position question forms: 62 left/right, 3 above/below, 2 front/behind, 10 closer/farther

## Setup

Dataset: `lmms-lab/vstar-bench`

Dataset revision: `b44023b4dca749ed8a76b85eb576627d05a1c174`

Model: `qwen/qwen3.6-plus`

Evaluation setting:
- original V* image bytes
- no image resizing
- no JPEG re-encoding
- no system prompt
- OpenRouter `reasoning` field omitted
- `temperature=0`
- one run per item
- relabeled question, relabeled options, and relabeled answer label
- dataset-native answer suffix: `Answer with the option's letter from the given choices directly.`

Runner support:
- `scripts/run_vstar_image_eval.py` now supports `--prompt-mode relabeled_raw_text`
- relabel annotations are loaded with `--annotations data/annotations/vstar_relabel_latest.jsonl`
- `scripts/review_vstar_labels.py` supports an optional access token and initial `qid` in the URL for shared annotation sessions

Command used:

```bash
python scripts/run_vstar_image_eval.py \
  --out results/qwen36plus_vstar_relabel_current_rawprompt_originalimage_t0.jsonl \
  --model qwen/qwen3.6-plus \
  --concurrency 8 \
  --temperature 0 \
  --max-tokens 16 \
  --prompt-mode relabeled_raw_text \
  --response-mode direct \
  --image-mode original \
  --system-mode none \
  --reasoning-mode omit \
  --annotations data/annotations/vstar_relabel_latest.jsonl \
  --timeout 300
```

Unparsed rows were rerun with the same image/prompt/model settings and larger output budgets (`max_tokens=512`, then `1024`) until all 191 rows were parsed. The larger budget only affects completion length for rows where Qwen started explaining instead of immediately outputting a letter. One slow tail item (`qid=189`) was retried separately after a short OpenRouter rate-limit interval.

Files:
- raw output: `results/qwen36plus_vstar_relabel_current_rawprompt_originalimage_t0.jsonl`
- summary: `results/qwen36plus_vstar_relabel_current_rawprompt_originalimage_t0_summary.md`

Recorded OpenRouter usage:
- cost: about `$1.09`
- prompt tokens: 488,189
- completion tokens: 477,613
- total tokens: 965,802

## Results

| condition | parsed | correct | accuracy |
|---|---:|---:|---:|
| original V* labels | 191/191 | 173 | 90.6% |
| interim human relabel, before final relative-position rewrite | 191/191 | 168 | 88.0% |
| final human relabel | 191/191 | 144 | 75.4% |

By category:

| category | n | correct | accuracy |
|---|---:|---:|---:|
| `direct_attributes` | 115 | 80 | 69.6% |
| `relative_position` | 76 | 64 | 84.2% |

By option count:

| option count | n | correct | accuracy |
|---:|---:|---:|---:|
| 2 | 84 | 69 | 82.1% |
| 4 | 107 | 75 | 70.1% |

By item range:

| subset | n | correct | accuracy |
|---|---:|---:|---:|
| first 32 items | 32 | 20 | 62.5% |
| remaining items | 159 | 124 | 78.0% |

Global choice distribution:

| A | B | C | D |
|---:|---:|---:|---:|
| 75 | 71 | 22 | 23 |

Gold label distribution:

| A | B | C | D |
|---:|---:|---:|---:|
| 70 | 69 | 24 | 28 |

## Interpretation

The final human relabel set is substantially harder than the original V* labels under the same official-like Qwen3.6-Plus setting: 90.6% drops to 75.4%.

Compared with the interim relabel result, the largest change is in `relative_position`. The interim relative-position subset was nearly saturated at 98.7%; after rewriting the remaining relative-position items into explicit position questions, it drops to 84.2%.

The final set is still hard in two different ways:
- direct attributes: 69.6%, mostly fine-grained visual attributes and small objects
- relative position: 84.2%, now no longer a near-trivial two-choice subset

This should be treated as a new human relabeled V* split rather than an equivalent wording rewrite of the original benchmark targets.

The older 88.0% file is kept as an intermediate annotation-pass result:
- `results/qwen36plus_vstar_relabel_rawprompt_originalimage_t0.jsonl`
- `results/qwen36plus_vstar_relabel_rawprompt_originalimage_t0_summary.md`
