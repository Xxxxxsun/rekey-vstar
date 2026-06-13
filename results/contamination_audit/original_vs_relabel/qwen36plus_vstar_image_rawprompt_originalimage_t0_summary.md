# V* Image Evaluation

model: `qwen/qwen3.6-plus`
source: `results/qwen36plus_vstar_image_rawprompt_originalimage_t0.jsonl`

## Overall

| requests | ok | parsed | correct | accuracy over parsed |
|---:|---:|---:|---:|---:|
| 191 | 191 | 191 | 173 | 90.6% |

## By Category

| category | n | parsed | correct | accuracy |
|---|---:|---:|---:|---:|
| `direct_attributes` | 115 | 115 | 104 | 90.4% |
| `relative_position` | 76 | 76 | 69 | 90.8% |

## By Option Count

| option count | n | parsed | correct | accuracy |
|---:|---:|---:|---:|---:|
| 2 | 84 | 84 | 77 | 91.7% |
| 4 | 107 | 107 | 96 | 89.7% |

## Errors

| qid | category | label | parsed | content |
|---:|---|---|---|---|
| 4 | `direct_attributes` | C | D | `D` |
| 15 | `direct_attributes` | D | C | `C` |
| 23 | `direct_attributes` | B | A | `A` |
| 25 | `direct_attributes` | D | A | `A` |
| 34 | `direct_attributes` | A | C | `C` |
| 37 | `direct_attributes` | C | D | `(D)` |
| 51 | `direct_attributes` | A | C | `(C)` |
| 69 | `direct_attributes` | C | D | `D` |
| 72 | `direct_attributes` | C | D | `D` |
| 75 | `direct_attributes` | A | D | `(D)` |
| 83 | `direct_attributes` | D | A | `A` |
| 116 | `relative_position` | A | B | `B` |
| 126 | `relative_position` | A | B | `(B)` |
| 151 | `relative_position` | B | A | `A` |
| 159 | `relative_position` | A | B | `B` |
| 167 | `relative_position` | B | A | `(A)` |
| 178 | `relative_position` | B | A | `A` |
| 189 | `relative_position` | B | A | `The red stool is visible near the pillar of the building on the left side (specifically, near the entrance archway). The` |
