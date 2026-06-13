# Motorcycle Prompt Temperature Sweep

Date: 2026-04-28

Prompt:

```text
What is the color of the motorcycle? (A) orange (B) red (C) white (D) black Answer with the option's letter from the given choices. You must answer now.
```

Model: `qwen/qwen3.6-plus` through OpenRouter.

## Condition 1: Exact User Prompt, No Explicit System Prompt

Settings:
- `reasoning.effort=none`
- `max_tokens=320`
- 20 repeats per temperature
- parser only accepts explicit final option-letter patterns or final explicit color choices

| temp | A | B | C | D | unparsed | B+D |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 2 | 1 | 17 | 0 | 19/20 (95%) |
| 0.05 | 0 | 2 | 0 | 16 | 2 | 18/20 (90%) |
| 0.1 | 0 | 1 | 0 | 19 | 0 | 20/20 (100%) |
| 0.2 | 1 | 1 | 0 | 18 | 0 | 19/20 (95%) |
| 0.3 | 1 | 4 | 0 | 15 | 0 | 19/20 (95%) |
| 0.5 | 4 | 3 | 3 | 10 | 0 | 13/20 (65%) |
| 0.7 | 1 | 4 | 2 | 11 | 2 | 15/20 (75%) |
| 1 | 6 | 5 | 3 | 4 | 2 | 9/20 (45%) |

## Condition 2: Strict Letter-Only System Prompt

System prompt:

```text
Output exactly one uppercase option letter from A, B, C, or D. Do not explain.
```

Settings:
- `reasoning.effort=none`
- `max_tokens=4`
- 20 repeats per temperature

| temp | A | B | C | D | unparsed | B+D |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 20 | 0 | 20/20 (100%) |
| 0.05 | 0 | 0 | 0 | 20 | 0 | 20/20 (100%) |
| 0.1 | 0 | 1 | 0 | 19 | 0 | 20/20 (100%) |
| 0.2 | 2 | 3 | 0 | 15 | 0 | 18/20 (90%) |
| 0.3 | 1 | 4 | 0 | 15 | 0 | 19/20 (95%) |
| 0.5 | 4 | 4 | 1 | 11 | 0 | 15/20 (75%) |
| 0.7 | 5 | 6 | 1 | 8 | 0 | 14/20 (70%) |
| 1 | 4 | 9 | 0 | 7 | 0 | 16/20 (80%) |

## Interpretation

This substantially reproduces the qualitative effect at low temperature: the model concentrates heavily on the benchmark-seen labels `B` and `D`. It is not strictly true across all settings, because `A` and sometimes `C` appear once temperature rises or under the no-system free-form condition.

For a paper claim, this is better framed as temperature- and prompt-dependent concentration on the duplicate-stem benchmark labels, not as an invariant "only B/D" behavior.
