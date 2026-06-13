# ~moonshotai/kimi-latest — original vs relabel V*

original V*: `results/kimi_original.jsonl` (n=191)
relabel V*: `results/kimi_relabel.jsonl` (n=191)

## Single-Condition Metrics

| metric | original V* | relabel V* |
|---|---:|---:|
| overall accuracy | 155/181 (85.6%) | 110/173 (63.6%) |
| acc · `direct_attributes` | 92/110 (83.6%) | 62/107 (57.9%) |
| acc · `relative_position` | 63/71 (88.7%) | 48/66 (72.7%) |
| acc · 2-choice | 71/79 (89.9%) | 53/72 (73.6%) |
| acc · 4-choice | 84/102 (82.4%) | 57/101 (56.4%) |
| acc · first 32 | 28/31 (90.3%) | 17/29 (58.6%) |
| acc · remaining 159 | 127/150 (84.7%) | 93/144 (64.6%) |
| parse rate | 181/191 (94.8%) | 173/191 (90.6%) |
| total cost (USD) | $1.3048 | $1.6763 |

## Output Choice Distribution

| condition | A | B | C | D |
|---|---:|---:|---:|---:|
| original V* | 67 | 70 | 25 | 19 |
| relabel V* | 73 | 59 | 23 | 18 |

## Paired Comparison

| metric | value |
|---|---:|
| paired n (both parsed) | 166 |
| both correct | 90 |
| both wrong | 9 |
| original correct only | 51 |
| relabel correct only | 16 |
| choice agreement | 41.0% |
| McNemar exact p-value | 2.169e-05 |
