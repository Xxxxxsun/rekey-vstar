# meta-llama/llama-4-maverick — original vs relabel V*

original V*: `results/llama4mav_original.jsonl` (n=191)
relabel V*: `results/llama4mav_relabel.jsonl` (n=191)

## Single-Condition Metrics

| metric | original V* | relabel V* |
|---|---:|---:|
| overall accuracy | 116/189 (61.4%) | 94/187 (50.3%) |
| acc · `direct_attributes` | 69/113 (61.1%) | 44/111 (39.6%) |
| acc · `relative_position` | 47/76 (61.8%) | 50/76 (65.8%) |
| acc · 2-choice | 54/84 (64.3%) | 55/84 (65.5%) |
| acc · 4-choice | 62/105 (59.0%) | 39/103 (37.9%) |
| acc · first 32 | 20/31 (64.5%) | 11/30 (36.7%) |
| acc · remaining 159 | 96/158 (60.8%) | 83/157 (52.9%) |
| parse rate | 189/191 (99.0%) | 187/191 (97.9%) |
| total cost (USD) | $0.0951 | $0.0983 |

## Output Choice Distribution

| condition | A | B | C | D |
|---|---:|---:|---:|---:|
| original V* | 37 | 94 | 34 | 24 |
| relabel V* | 65 | 69 | 33 | 20 |

## Paired Comparison

| metric | value |
|---|---:|
| paired n (both parsed) | 185 |
| both correct | 59 |
| both wrong | 36 |
| original correct only | 56 |
| relabel correct only | 34 |
| choice agreement | 36.2% |
| McNemar exact p-value | 0.0263 |
