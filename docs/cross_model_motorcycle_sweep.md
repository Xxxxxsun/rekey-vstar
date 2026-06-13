# Cross-Model Motorcycle Prompt Sweep

Date: 2026-04-28

Prompt:

```text
What is the color of the motorcycle? (A) orange (B) red (C) white (D) black Answer with the option's letter from the given choices. You must answer now.
```

Condition:
- strict system prompt: `Output exactly one uppercase option letter from A, B, C, or D. Do not explain.`
- `reasoning.effort=none`
- `max_tokens=16`
- 20 repeats per temperature

Model selection from OpenRouter `/models` at run time:
- Doubao requested: no `doubao` model ID was listed; used latest ByteDance Seed available, `bytedance-seed/seed-2.0-lite`
- Kimi: `~moonshotai/kimi-latest` and stable named `moonshotai/kimi-k2.6`
- MiMo: `xiaomi/mimo-v2.5-pro`
- Qwen baseline: previous `qwen/qwen3.6-plus` strict sweep

## B+D Concentration

| model | t=0 | t=0.05 | t=0.1 | t=0.2 | t=0.3 | t=0.5 | t=0.7 | t=1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen/qwen3.6-plus` | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 18/20 (90%) | 19/20 (95%) | 15/20 (75%) | 14/20 (70%) | 16/20 (80%) |
| `bytedance-seed/seed-2.0-lite` | 15/20 (75%) | 18/20 (90%) | 17/20 (85%) | 16/20 (80%) | 15/20 (75%) | 19/20 (95%) | 16/20 (80%) | 16/20 (80%) |
| `~moonshotai/kimi-latest` | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 16/20 (80%) | 19/20 (95%) | 14/20 (70%) |
| `moonshotai/kimi-k2.6` | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 17/20 (85%) | 15/20 (75%) | 11/20 (55%) |
| `xiaomi/mimo-v2.5-pro` | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 19/20 (95%) | 17/20 (85%) |

## Full Counts

### `bytedance-seed/seed-2.0-lite`

| temp | A | B | C | D | unparsed | B+D |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 2 | 14 | 3 | 1 | 0 | 15/20 (75%) |
| 0.05 | 2 | 13 | 0 | 5 | 0 | 18/20 (90%) |
| 0.1 | 2 | 12 | 1 | 5 | 0 | 17/20 (85%) |
| 0.2 | 2 | 11 | 2 | 5 | 0 | 16/20 (80%) |
| 0.3 | 3 | 15 | 2 | 0 | 0 | 15/20 (75%) |
| 0.5 | 1 | 18 | 0 | 1 | 0 | 19/20 (95%) |
| 0.7 | 2 | 13 | 2 | 3 | 0 | 16/20 (80%) |
| 1 | 2 | 13 | 2 | 3 | 0 | 16/20 (80%) |

### `~moonshotai/kimi-latest`

| temp | A | B | C | D | unparsed | B+D |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 20 | 0 | 0 | 0 | 20/20 (100%) |
| 0.05 | 0 | 20 | 0 | 0 | 0 | 20/20 (100%) |
| 0.1 | 0 | 20 | 0 | 0 | 0 | 20/20 (100%) |
| 0.2 | 0 | 20 | 0 | 0 | 0 | 20/20 (100%) |
| 0.3 | 0 | 19 | 0 | 1 | 0 | 20/20 (100%) |
| 0.5 | 0 | 16 | 4 | 0 | 0 | 16/20 (80%) |
| 0.7 | 0 | 17 | 1 | 2 | 0 | 19/20 (95%) |
| 1 | 1 | 11 | 3 | 3 | 2 | 14/20 (70%) |

### `moonshotai/kimi-k2.6`

| temp | A | B | C | D | unparsed | B+D |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 20 | 0 | 0 | 0 | 20/20 (100%) |
| 0.05 | 0 | 20 | 0 | 0 | 0 | 20/20 (100%) |
| 0.1 | 0 | 20 | 0 | 0 | 0 | 20/20 (100%) |
| 0.2 | 0 | 20 | 0 | 0 | 0 | 20/20 (100%) |
| 0.3 | 0 | 19 | 0 | 1 | 0 | 20/20 (100%) |
| 0.5 | 1 | 17 | 2 | 0 | 0 | 17/20 (85%) |
| 0.7 | 1 | 12 | 3 | 3 | 1 | 15/20 (75%) |
| 1 | 1 | 10 | 6 | 1 | 2 | 11/20 (55%) |

### `xiaomi/mimo-v2.5-pro`

| temp | A | B | C | D | unparsed | B+D |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 20 | 0 | 20/20 (100%) |
| 0.05 | 0 | 0 | 0 | 20 | 0 | 20/20 (100%) |
| 0.1 | 0 | 0 | 0 | 20 | 0 | 20/20 (100%) |
| 0.2 | 0 | 0 | 0 | 20 | 0 | 20/20 (100%) |
| 0.3 | 0 | 0 | 0 | 20 | 0 | 20/20 (100%) |
| 0.5 | 0 | 2 | 0 | 18 | 0 | 20/20 (100%) |
| 0.7 | 1 | 2 | 0 | 17 | 0 | 19/20 (95%) |
| 1 | 2 | 7 | 1 | 10 | 0 | 17/20 (85%) |

## Interpretation

The B/D concentration is not Qwen-specific. Under a strict letter-only prompt, Kimi and MiMo show equal or stronger concentration on the same `{B,D}` label set. This weakens a single-model leakage interpretation for this specific motorcycle prompt.

For the current dataset, this result should be interpreted as evidence that the motorcycle prompt is not Qwen-specific.
