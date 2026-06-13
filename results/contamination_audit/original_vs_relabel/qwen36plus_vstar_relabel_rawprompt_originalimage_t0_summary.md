# V* Image Evaluation

model: `qwen/qwen3.6-plus`
source: `results/qwen36plus_vstar_relabel_rawprompt_originalimage_t0.jsonl`

## Overall

| requests | ok | parsed | correct | accuracy over parsed |
|---:|---:|---:|---:|---:|
| 191 | 191 | 191 | 168 | 88.0% |

## By Category

| category | n | parsed | correct | accuracy |
|---|---:|---:|---:|---:|
| `direct_attributes` | 115 | 115 | 93 | 80.9% |
| `relative_position` | 76 | 76 | 75 | 98.7% |

## By Option Count

| option count | n | parsed | correct | accuracy |
|---:|---:|---:|---:|---:|
| 2 | 84 | 84 | 83 | 98.8% |
| 4 | 107 | 107 | 85 | 79.4% |

## Errors

| qid | category | label | parsed | content |
|---:|---|---|---|---|
| 4 | `direct_attributes` | D | C | `C` |
| 5 | `direct_attributes` | A | B | `B` |
| 6 | `direct_attributes` | B | D | `D` |
| 10 | `direct_attributes` | C | B | `B` |
| 13 | `direct_attributes` | C | A | `A` |
| 15 | `direct_attributes` | B | C | `C` |
| 16 | `direct_attributes` | D | B | `The person wearing a yellow dress is likely a misidentification of the woman in the black top (or perhaps she is wearing` |
| 20 | `direct_attributes` | B | C | `The playground slide is located in the lower left area of the image. It is part of a wooden play structure. The structur` |
| 23 | `direct_attributes` | D | A | `A` |
| 24 | `direct_attributes` | B | A | `A` |
| 26 | `direct_attributes` | A | B | `B` |
| 27 | `direct_attributes` | C | A | `A` |
| 30 | `direct_attributes` | B | A | `A` |
| 33 | `direct_attributes` | D | C | `C` |
| 57 | `direct_attributes` | A | B | `B` |
| 72 | `direct_attributes` | D | C | `(C)` |
| 77 | `direct_attributes` | A | D | `D` |
| 78 | `direct_attributes` | A | B | `(B)` |
| 93 | `direct_attributes` | B | C | `C` |
| 101 | `direct_attributes` | D | A | `A` |
| 102 | `direct_attributes` | B | A | `A` |
| 107 | `direct_attributes` | C | A | `A` |
| 188 | `relative_position` | B | A | `(A)` |
