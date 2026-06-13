# Post-Change ReAct V* 3-Seed Benchmark Merge

Date: 2026-05-25

This report merges the old full-benchmark ReAct rows with the three-seed rerun on changed bench1/bench2/bench3 questions. The primary tables keep dataset and seed separate.

- Old sweep root: `outputs/react_vstar/tool_loop_zoom_sweep_20260519`
- Changed-question root: `outputs/react_vstar/tool_loop_zoom_sweep_20260519/changed_questions_seeded_20260524`
- Changed-question data: `data/annotations/dynamic_vstar_changed_questions_latest`
- Generated tables: `outputs/react_vstar/tool_loop_zoom_sweep_20260519/post_change_merged_3seed_20260525/tables`

Seed pairing used for the merged post-change rows:

| Merged seed | Old unchanged source | Changed-question source |
| --- | --- | --- |
| `merged_seed_1` | `old_main` for standard models; `claude_opus_4_7` for Opus | `changed_seed_41` |
| `merged_seed_2` | `old_seed_2026052201` for standard models; `claude_opus_4_7_adaptive_only` for Opus | `changed_seed_42` |
| `merged_seed_3` | `old_seed_2026052202` for standard models; `seed_2026052201/claude_opus_4_7_adaptive` for Opus | `changed_seed_43` |

Important provenance note: Opus 4.7 did not have three old runs with identical seed semantics. The merged Opus old side uses `claude_opus_4_7` (adaptive thinking with `effort=low`, no seed), `claude_opus_4_7_adaptive_only` (adaptive-only, no seed), and `seed_2026052201/claude_opus_4_7_adaptive` (seed label used for output isolation; backend seed not sent).

Scores use `correct / target`; missing or failed rows remain in the denominator and therefore count as incorrect. The present-only accuracy column is diagnostic only for incomplete models.

## Gap Explanation

All old-side source rows are present; no targeted rerun gap remains.

## Five-Condition 3-Seed Summary

Each cell is mean accuracy plus/minus sample standard deviation across three seed pairings. `original` and `relabeled` use the old full-benchmark sources; `bench1`/`bench2`/`bench3` use the post-change merged seeds.

| Model | Original | Relabeled | Bench 1 | Bench 2 | Bench 3 |
| --- | --- | --- | --- | --- | --- |
| `doubao-seed-2.0-lite` | 94.94% ± 1.09 | 81.68% ± 1.81 | 80.80% ± 0.60 | 75.39% ± 1.89 | 81.68% ± 3.27 |
| `gemini-3.1-pro-preview` | 93.54% ± 1.09 | 82.02% ± 1.21 | 79.23% ± 1.09 | 76.44% ± 3.18 | 80.28% ± 2.47 |
| `qwen3.6-plus` | 91.97% ± 0.80 | 81.50% ± 1.68 | 79.93% ± 0.60 | 73.12% ± 2.47 | 80.10% ± 1.81 |
| `gpt-5.5-0424-global` | 87.09% ± 1.84 | 76.09% ± 1.60 | 74.87% ± 0.91 | 71.03% ± 2.18 | 73.47% ± 1.98 |
| `claude-opus-4-7` | 87.96% ± 0.52 | 70.51% ± 2.42 | 71.38% ± 1.68 | 66.49% ± 1.89 | 70.16% ± 0.52 |
| `kimi-k2.6` | 74.87% ± 4.29 | 62.13% ± 3.56 | 65.79% ± 1.84 | 62.13% ± 3.33 | 65.10% ± 3.49 |

## Per-Dataset, Per-Seed Scores

| Dataset | Merged seed | Model | Correct / target | Accuracy | Old unchanged | Changed | Missing | Failed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bench1` | `merged_seed_1` | `doubao-seed-2.0-lite` | 155/191 | 81.15% | 103/128 | 52/63 | 0 | 0 |
| `bench1` | `merged_seed_1` | `qwen3.6-plus` | 152/191 | 79.58% | 105/128 | 47/63 | 0 | 0 |
| `bench1` | `merged_seed_1` | `gemini-3.1-pro-preview` | 152/191 | 79.58% | 104/128 | 48/63 | 0 | 0 |
| `bench1` | `merged_seed_1` | `gpt-5.5-0424-global` | 142/191 | 74.35% | 99/128 | 43/63 | 0 | 0 |
| `bench1` | `merged_seed_1` | `claude-opus-4-7` | 140/191 | 73.30% | 89/128 | 51/63 | 0 | 0 |
| `bench1` | `merged_seed_1` | `kimi-k2.6` | 122/191 | 63.87% | 81/128 | 41/63 | 0 | 0 |
| `bench1` | `merged_seed_2` | `doubao-seed-2.0-lite` | 155/191 | 81.15% | 105/128 | 50/63 | 0 | 0 |
| `bench1` | `merged_seed_2` | `qwen3.6-plus` | 152/191 | 79.58% | 107/128 | 45/63 | 0 | 0 |
| `bench1` | `merged_seed_2` | `gemini-3.1-pro-preview` | 149/191 | 78.01% | 101/128 | 48/63 | 0 | 1 |
| `bench1` | `merged_seed_2` | `gpt-5.5-0424-global` | 145/191 | 75.92% | 97/128 | 48/63 | 0 | 0 |
| `bench1` | `merged_seed_2` | `claude-opus-4-7` | 135/191 | 70.68% | 86/128 | 49/63 | 0 | 0 |
| `bench1` | `merged_seed_2` | `kimi-k2.6` | 126/191 | 65.97% | 89/128 | 37/63 | 0 | 0 |
| `bench1` | `merged_seed_3` | `qwen3.6-plus` | 154/191 | 80.63% | 101/128 | 53/63 | 0 | 0 |
| `bench1` | `merged_seed_3` | `doubao-seed-2.0-lite` | 153/191 | 80.10% | 102/128 | 51/63 | 0 | 0 |
| `bench1` | `merged_seed_3` | `gemini-3.1-pro-preview` | 153/191 | 80.10% | 103/128 | 50/63 | 0 | 1 |
| `bench1` | `merged_seed_3` | `gpt-5.5-0424-global` | 142/191 | 74.35% | 97/128 | 45/63 | 0 | 0 |
| `bench1` | `merged_seed_3` | `claude-opus-4-7` | 134/191 | 70.16% | 85/128 | 49/63 | 0 | 0 |
| `bench1` | `merged_seed_3` | `kimi-k2.6` | 129/191 | 67.54% | 88/128 | 41/63 | 0 | 0 |
| `bench2` | `merged_seed_1` | `qwen3.6-plus` | 145/191 | 75.92% | 96/123 | 49/68 | 0 | 0 |
| `bench2` | `merged_seed_1` | `doubao-seed-2.0-lite` | 141/191 | 73.82% | 88/123 | 53/68 | 0 | 0 |
| `bench2` | `merged_seed_1` | `gemini-3.1-pro-preview` | 139/191 | 72.77% | 88/123 | 51/68 | 0 | 0 |
| `bench2` | `merged_seed_1` | `gpt-5.5-0424-global` | 131/191 | 68.59% | 85/123 | 46/68 | 0 | 0 |
| `bench2` | `merged_seed_1` | `claude-opus-4-7` | 126/191 | 65.97% | 77/123 | 49/68 | 0 | 0 |
| `bench2` | `merged_seed_1` | `kimi-k2.6` | 115/191 | 60.21% | 75/123 | 40/68 | 0 | 0 |
| `bench2` | `merged_seed_2` | `gemini-3.1-pro-preview` | 150/191 | 78.53% | 97/123 | 53/68 | 0 | 0 |
| `bench2` | `merged_seed_2` | `doubao-seed-2.0-lite` | 143/191 | 74.87% | 90/123 | 53/68 | 0 | 0 |
| `bench2` | `merged_seed_2` | `gpt-5.5-0424-global` | 139/191 | 72.77% | 88/123 | 51/68 | 0 | 0 |
| `bench2` | `merged_seed_2` | `qwen3.6-plus` | 138/191 | 72.25% | 91/123 | 47/68 | 0 | 0 |
| `bench2` | `merged_seed_2` | `claude-opus-4-7` | 131/191 | 68.59% | 79/123 | 52/68 | 0 | 0 |
| `bench2` | `merged_seed_2` | `kimi-k2.6` | 115/191 | 60.21% | 77/123 | 38/68 | 0 | 0 |
| `bench2` | `merged_seed_3` | `gemini-3.1-pro-preview` | 149/191 | 78.01% | 96/123 | 53/68 | 0 | 0 |
| `bench2` | `merged_seed_3` | `doubao-seed-2.0-lite` | 148/191 | 77.49% | 91/123 | 57/68 | 0 | 0 |
| `bench2` | `merged_seed_3` | `gpt-5.5-0424-global` | 137/191 | 71.73% | 88/123 | 49/68 | 0 | 0 |
| `bench2` | `merged_seed_3` | `qwen3.6-plus` | 136/191 | 71.20% | 85/123 | 51/68 | 0 | 0 |
| `bench2` | `merged_seed_3` | `kimi-k2.6` | 126/191 | 65.97% | 83/123 | 43/68 | 0 | 0 |
| `bench2` | `merged_seed_3` | `claude-opus-4-7` | 124/191 | 64.92% | 76/123 | 48/68 | 0 | 0 |
| `bench3` | `merged_seed_1` | `doubao-seed-2.0-lite` | 158/191 | 82.72% | 109/135 | 49/56 | 0 | 0 |
| `bench3` | `merged_seed_1` | `qwen3.6-plus` | 151/191 | 79.06% | 103/135 | 48/56 | 0 | 0 |
| `bench3` | `merged_seed_1` | `gemini-3.1-pro-preview` | 148/191 | 77.49% | 105/135 | 43/56 | 0 | 0 |
| `bench3` | `merged_seed_1` | `gpt-5.5-0424-global` | 136/191 | 71.20% | 97/135 | 39/56 | 0 | 0 |
| `bench3` | `merged_seed_1` | `claude-opus-4-7` | 135/191 | 70.68% | 90/135 | 45/56 | 0 | 0 |
| `bench3` | `merged_seed_1` | `kimi-k2.6` | 130/191 | 68.06% | 91/135 | 39/56 | 0 | 0 |
| `bench3` | `merged_seed_2` | `doubao-seed-2.0-lite` | 161/191 | 84.29% | 111/135 | 50/56 | 0 | 0 |
| `bench3` | `merged_seed_2` | `qwen3.6-plus` | 157/191 | 82.20% | 108/135 | 49/56 | 0 | 0 |
| `bench3` | `merged_seed_2` | `gemini-3.1-pro-preview` | 157/191 | 82.20% | 114/135 | 43/56 | 0 | 0 |
| `bench3` | `merged_seed_2` | `gpt-5.5-0424-global` | 142/191 | 74.35% | 101/135 | 41/56 | 0 | 0 |
| `bench3` | `merged_seed_2` | `claude-opus-4-7` | 133/191 | 69.63% | 92/135 | 41/56 | 0 | 0 |
| `bench3` | `merged_seed_2` | `kimi-k2.6` | 117/191 | 61.26% | 81/135 | 36/56 | 0 | 0 |
| `bench3` | `merged_seed_3` | `gemini-3.1-pro-preview` | 155/191 | 81.15% | 111/135 | 44/56 | 0 | 1 |
| `bench3` | `merged_seed_3` | `qwen3.6-plus` | 151/191 | 79.06% | 103/135 | 48/56 | 0 | 0 |
| `bench3` | `merged_seed_3` | `doubao-seed-2.0-lite` | 149/191 | 78.01% | 103/135 | 46/56 | 0 | 0 |
| `bench3` | `merged_seed_3` | `gpt-5.5-0424-global` | 143/191 | 74.87% | 100/135 | 43/56 | 0 | 0 |
| `bench3` | `merged_seed_3` | `claude-opus-4-7` | 134/191 | 70.16% | 92/135 | 42/56 | 0 | 0 |
| `bench3` | `merged_seed_3` | `kimi-k2.6` | 126/191 | 65.97% | 84/135 | 42/56 | 0 | 0 |

## Per-Seed Benchmark Summary

This summary pools bench1/bench2/bench3 within each merged seed only; the dataset-separated table above is the primary report.

| Merged seed | Model | Correct / target | Accuracy | Present-only acc. | Missing | Failed |
| --- | --- | --- | --- | --- | --- | --- |
| `merged_seed_1` | `doubao-seed-2.0-lite` | 454/573 | 79.23% | 79.23% | 0 | 0 |
| `merged_seed_1` | `qwen3.6-plus` | 448/573 | 78.18% | 78.18% | 0 | 0 |
| `merged_seed_1` | `gemini-3.1-pro-preview` | 439/573 | 76.61% | 76.61% | 0 | 0 |
| `merged_seed_1` | `gpt-5.5-0424-global` | 409/573 | 71.38% | 71.38% | 0 | 0 |
| `merged_seed_1` | `claude-opus-4-7` | 401/573 | 69.98% | 69.98% | 0 | 0 |
| `merged_seed_1` | `kimi-k2.6` | 367/573 | 64.05% | 64.05% | 0 | 0 |
| `merged_seed_2` | `doubao-seed-2.0-lite` | 459/573 | 80.10% | 80.10% | 0 | 0 |
| `merged_seed_2` | `gemini-3.1-pro-preview` | 456/573 | 79.58% | 79.58% | 0 | 1 |
| `merged_seed_2` | `qwen3.6-plus` | 447/573 | 78.01% | 78.01% | 0 | 0 |
| `merged_seed_2` | `gpt-5.5-0424-global` | 426/573 | 74.35% | 74.35% | 0 | 0 |
| `merged_seed_2` | `claude-opus-4-7` | 399/573 | 69.63% | 69.63% | 0 | 0 |
| `merged_seed_2` | `kimi-k2.6` | 358/573 | 62.48% | 62.48% | 0 | 0 |
| `merged_seed_3` | `gemini-3.1-pro-preview` | 457/573 | 79.76% | 79.76% | 0 | 2 |
| `merged_seed_3` | `doubao-seed-2.0-lite` | 450/573 | 78.53% | 78.53% | 0 | 0 |
| `merged_seed_3` | `qwen3.6-plus` | 441/573 | 76.96% | 76.96% | 0 | 0 |
| `merged_seed_3` | `gpt-5.5-0424-global` | 422/573 | 73.65% | 73.65% | 0 | 0 |
| `merged_seed_3` | `claude-opus-4-7` | 392/573 | 68.41% | 68.41% | 0 | 0 |
| `merged_seed_3` | `kimi-k2.6` | 381/573 | 66.49% | 66.49% | 0 | 0 |

## Aggregate Diagnostics

| Model | Correct / target | Accuracy | Present-only acc. | Present | Missing | Failed | Complete |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `doubao-seed-2.0-lite` | 1363/1719 | 79.29% | 79.29% | 1719 | 0 | 0 | yes |
| `gemini-3.1-pro-preview` | 1352/1719 | 78.65% | 78.65% | 1719 | 0 | 3 | no |
| `qwen3.6-plus` | 1336/1719 | 77.72% | 77.72% | 1719 | 0 | 0 | yes |
| `gpt-5.5-0424-global` | 1257/1719 | 73.12% | 73.12% | 1719 | 0 | 0 | yes |
| `claude-opus-4-7` | 1192/1719 | 69.34% | 69.34% | 1719 | 0 | 0 | yes |
| `kimi-k2.6` | 1106/1719 | 64.34% | 64.34% | 1719 | 0 | 0 | yes |

## Aggregate Per-Dataset Diagnostics

This table pools all three merged seeds within each dataset.

| Model | Dataset | Correct / target | Accuracy | Old unchanged | Changed | Missing | Failed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `doubao-seed-2.0-lite` | `bench1` | 463/573 | 80.80% | 310/384 | 153/189 | 0 | 0 |
| `qwen3.6-plus` | `bench1` | 458/573 | 79.93% | 313/384 | 145/189 | 0 | 0 |
| `gemini-3.1-pro-preview` | `bench1` | 454/573 | 79.23% | 308/384 | 146/189 | 0 | 2 |
| `gpt-5.5-0424-global` | `bench1` | 429/573 | 74.87% | 293/384 | 136/189 | 0 | 0 |
| `claude-opus-4-7` | `bench1` | 409/573 | 71.38% | 260/384 | 149/189 | 0 | 0 |
| `kimi-k2.6` | `bench1` | 377/573 | 65.79% | 258/384 | 119/189 | 0 | 0 |
| `gemini-3.1-pro-preview` | `bench2` | 438/573 | 76.44% | 281/369 | 157/204 | 0 | 0 |
| `doubao-seed-2.0-lite` | `bench2` | 432/573 | 75.39% | 269/369 | 163/204 | 0 | 0 |
| `qwen3.6-plus` | `bench2` | 419/573 | 73.12% | 272/369 | 147/204 | 0 | 0 |
| `gpt-5.5-0424-global` | `bench2` | 407/573 | 71.03% | 261/369 | 146/204 | 0 | 0 |
| `claude-opus-4-7` | `bench2` | 381/573 | 66.49% | 232/369 | 149/204 | 0 | 0 |
| `kimi-k2.6` | `bench2` | 356/573 | 62.13% | 235/369 | 121/204 | 0 | 0 |
| `doubao-seed-2.0-lite` | `bench3` | 468/573 | 81.68% | 323/405 | 145/168 | 0 | 0 |
| `gemini-3.1-pro-preview` | `bench3` | 460/573 | 80.28% | 330/405 | 130/168 | 0 | 1 |
| `qwen3.6-plus` | `bench3` | 459/573 | 80.10% | 314/405 | 145/168 | 0 | 0 |
| `gpt-5.5-0424-global` | `bench3` | 421/573 | 73.47% | 298/405 | 123/168 | 0 | 0 |
| `claude-opus-4-7` | `bench3` | 402/573 | 70.16% | 274/405 | 128/168 | 0 | 0 |
| `kimi-k2.6` | `bench3` | 373/573 | 65.10% | 256/405 | 117/168 | 0 | 0 |

## Coverage Notes

The following source components are incomplete or have latest failed rows. They are retained in the denominator.

| Model | Dataset | Part | Source | Correct / target | Accuracy | Missing | Failed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `gemini-3.1-pro-preview` | `bench1` | `old_unchanged` | `old_seed_2026052201` | 101/128 | 78.91% | 0 | 1 |
| `gemini-3.1-pro-preview` | `bench1` | `old_unchanged` | `old_seed_2026052202` | 103/128 | 80.47% | 0 | 1 |
| `gemini-3.1-pro-preview` | `bench3` | `old_unchanged` | `old_seed_2026052202` | 111/135 | 82.22% | 0 | 1 |

## Reproduction

```bash
/root/storage/miniconda3/envs/agent/bin/python scripts/merge_react_vstar_post_change_scores.py
```

Main generated files:

- `outputs/react_vstar/tool_loop_zoom_sweep_20260519/post_change_merged_3seed_20260525/tables/post_change_full_benchmark_by_model.csv`
- `outputs/react_vstar/tool_loop_zoom_sweep_20260519/post_change_merged_3seed_20260525/tables/post_change_full_benchmark_by_condition_model.csv`
- `outputs/react_vstar/tool_loop_zoom_sweep_20260519/post_change_merged_3seed_20260525/tables/post_change_full_benchmark_by_seed_model.csv`
- `outputs/react_vstar/tool_loop_zoom_sweep_20260519/post_change_merged_3seed_20260525/tables/post_change_full_benchmark_by_seed_condition_model.csv`
- `outputs/react_vstar/tool_loop_zoom_sweep_20260519/post_change_merged_3seed_20260525/tables/post_change_five_condition_mean_std.csv`
- `outputs/react_vstar/tool_loop_zoom_sweep_20260519/post_change_merged_3seed_20260525/tables/post_change_merge_components.csv`
- `outputs/react_vstar/tool_loop_zoom_sweep_20260519/post_change_merged_3seed_20260525/merge_manifest.json`
