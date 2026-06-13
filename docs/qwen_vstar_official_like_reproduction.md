# Qwen3.6-Plus V* Official-Like Reproduction

Date: 2026-04-29

Purpose: explain why the earlier image + question reproduction was around 75%, and test a configuration closer to the official V* evaluation setup.

## Official Reference

In the Qwen3.6-Plus blog, the V* row is reported as `96.9 / 90.5` for Qwen3.6-Plus.

The table footnote says V* scores are reported as `with CI / without CI`.

Therefore, the relevant non-CI target for our API-only run is about `90.5%`.

## Previous Low-Resolution Run

File: `results/qwen36plus_vstar_image_original_direct_t0.jsonl`

Summary: `results/qwen36plus_vstar_image_original_direct_t0_summary.md`

Setting:
- image + original question + options
- image resized to max side 1536
- JPEG quality 85
- custom direct-answer system prompt
- `reasoning.effort=none`
- `temperature=0`
- direct letter-only output

Result:

| condition | parsed | correct | accuracy |
|---|---:|---:|---:|
| resized image, custom direct prompt | 191/191 | 144 | 75.4% |

This is much lower than the official non-CI score.

## Official-Like Run

File: `results/qwen36plus_vstar_image_rawprompt_originalimage_t0.jsonl`

Summary: `results/qwen36plus_vstar_image_rawprompt_originalimage_t0_summary.md`

Setting:
- original image bytes from the V* parquet
- no resizing
- no JPEG re-encoding
- original HF prompt text, including `Answer with the option's letter from the given choices directly.`
- no system prompt
- OpenRouter `reasoning` field omitted
- `temperature=0`
- initial `max_tokens=16`
- 13 truncated/unparsed rows rerun with `max_tokens=512`
- 2 remaining unparsed rows rerun with `max_tokens=2048`

Image size examples:

| qid | original size | original bytes |
|---:|---:|---:|
| 62 | 5759 x 1440 | 2,636,684 |
| 153 | 4755 x 1500 | 3,004,418 |
| 43 | 4031 x 1500 | 2,830,607 |
| 184 | 3976 x 1500 | 2,907,573 |

Result:

| condition | parsed | correct | accuracy |
|---|---:|---:|---:|
| original image + raw prompt | 191/191 | 173 | 90.6% |

By category:

| category | n | correct | accuracy |
|---|---:|---:|---:|
| `direct_attributes` | 115 | 104 | 90.4% |
| `relative_position` | 76 | 69 | 90.8% |

By option count:

| option count | n | correct | accuracy |
|---:|---:|---:|---:|
| 2 | 84 | 77 | 91.7% |
| 4 | 107 | 96 | 89.7% |

Recorded OpenRouter usage:
- cost: about `$0.77`
- prompt tokens: 487,569
- completion tokens: 312,641

## Comparison

| run | correct | accuracy |
|---|---:|---:|
| resized image, custom direct prompt | 144/191 | 75.4% |
| original image + raw prompt | 173/191 | 90.6% |
| official Qwen3.6-Plus without CI | -- | 90.5% |

Paired comparison against the earlier resized direct run:
- new run fixes 31 previous errors
- old run was correct but new run is wrong on 2 items
- net gain: +29 correct items

## Interpretation

The earlier 75% reproduction was primarily an evaluation-configuration artifact.

The largest difference is image handling: resizing to max side 1536 removes detail needed by V*, especially small objects, colors, and relative-position cues. Using original image bytes restores the score to 90.6%, essentially matching the official Qwen3.6-Plus non-CI score of 90.5%.

Prompt and reasoning settings also matter:
- using the original HF prompt avoids prompt drift
- omitting the forced `reasoning.effort=none` setting lets the API behave closer to the default evaluation path
- no system prompt is closer to the dataset-native prompt

Conclusion: for leakage/bias experiments that compare against the official V* score, use the official-like configuration as the normal VQA baseline. The low-resolution resized runs should only be treated as ablations.
