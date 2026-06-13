# GPT Motorcycle Prompt Sweep

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

Models:
- `openai/gpt-5.5`
- `openai/gpt-5.4-mini`
- `openai/gpt-4.1-mini`

## B+D Concentration

| model | t=0 | t=0.05 | t=0.1 | t=0.2 | t=0.3 | t=0.5 | t=0.7 | t=1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `openai/gpt-5.5` | 17/20 (85%) | 18/20 (90%) | 14/20 (70%) | 15/20 (75%) | 18/20 (90%) | 13/20 (65%) | 13/20 (65%) | 16/20 (80%) |
| `openai/gpt-5.4-mini` | 2/20 (10%) | 3/20 (15%) | 5/20 (25%) | 2/20 (10%) | 4/20 (20%) | 1/20 (5%) | 4/20 (20%) | 5/20 (25%) |
| `openai/gpt-4.1-mini` | 0/20 (0%) | 1/20 (5%) | 4/20 (20%) | 6/20 (30%) | 9/20 (45%) | 10/20 (50%) | 5/20 (25%) | 7/20 (35%) |

## Full Counts

### `openai/gpt-5.5`

| temp | A | B | C | D | unparsed | B+D |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 3 | 2 | 14 | 0 | 17/20 (85%) |
| 0.05 | 1 | 3 | 1 | 15 | 0 | 18/20 (90%) |
| 0.1 | 2 | 3 | 4 | 11 | 0 | 14/20 (70%) |
| 0.2 | 2 | 3 | 3 | 12 | 0 | 15/20 (75%) |
| 0.3 | 1 | 1 | 1 | 17 | 0 | 18/20 (90%) |
| 0.5 | 3 | 4 | 4 | 9 | 0 | 13/20 (65%) |
| 0.7 | 1 | 3 | 6 | 10 | 0 | 13/20 (65%) |
| 1 | 1 | 1 | 3 | 15 | 0 | 16/20 (80%) |

### `openai/gpt-5.4-mini`

| temp | A | B | C | D | unparsed | B+D |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 14 | 0 | 4 | 2 | 0 | 2/20 (10%) |
| 0.05 | 15 | 0 | 2 | 3 | 0 | 3/20 (15%) |
| 0.1 | 13 | 0 | 2 | 5 | 0 | 5/20 (25%) |
| 0.2 | 15 | 0 | 3 | 2 | 0 | 2/20 (10%) |
| 0.3 | 13 | 1 | 3 | 3 | 0 | 4/20 (20%) |
| 0.5 | 17 | 0 | 2 | 1 | 0 | 1/20 (5%) |
| 0.7 | 13 | 1 | 3 | 3 | 0 | 4/20 (20%) |
| 1 | 13 | 0 | 2 | 5 | 0 | 5/20 (25%) |

### `openai/gpt-4.1-mini`

| temp | A | B | C | D | unparsed | B+D |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 20 | 0 | 0 | 0 | 0 | 0/20 (0%) |
| 0.05 | 19 | 1 | 0 | 0 | 0 | 1/20 (5%) |
| 0.1 | 16 | 4 | 0 | 0 | 0 | 4/20 (20%) |
| 0.2 | 14 | 6 | 0 | 0 | 0 | 6/20 (30%) |
| 0.3 | 11 | 9 | 0 | 0 | 0 | 9/20 (45%) |
| 0.5 | 10 | 10 | 0 | 0 | 0 | 10/20 (50%) |
| 0.7 | 15 | 4 | 0 | 1 | 0 | 5/20 (25%) |
| 1 | 13 | 3 | 0 | 4 | 0 | 7/20 (35%) |

## Interpretation

GPT models are not uniform on this prompt:

- `openai/gpt-5.5` shows substantial B/D concentration, mostly through D.
- `openai/gpt-5.4-mini` is a strong negative control: it mostly selects A.
- `openai/gpt-4.1-mini` is another negative control: it heavily selects A at low temperature.

This supports treating the motorcycle prompt as a model-specific prior/memorization probe, not a universal no-image language-prior artifact. It still does not by itself prove benchmark leakage, because different models may have different priors over motorcycle colors or option positions.
