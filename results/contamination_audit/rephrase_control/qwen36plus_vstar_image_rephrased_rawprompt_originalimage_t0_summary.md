# V* Image Evaluation

model: `qwen/qwen3.6-plus`
source: `results/qwen36plus_vstar_image_rephrased_rawprompt_originalimage_t0.jsonl`

## Overall

| requests | ok | parsed | correct | accuracy over parsed |
|---:|---:|---:|---:|---:|
| 191 | 191 | 191 | 174 | 91.1% |

## By Category

| category | n | parsed | correct | accuracy |
|---|---:|---:|---:|---:|
| `direct_attributes` | 115 | 115 | 103 | 89.6% |
| `relative_position` | 76 | 76 | 71 | 93.4% |

## By Option Count

| option count | n | parsed | correct | accuracy |
|---:|---:|---:|---:|---:|
| 2 | 84 | 84 | 79 | 94.0% |
| 4 | 107 | 107 | 95 | 88.8% |

## Errors

| qid | category | label | parsed | content |
|---:|---|---|---|---|
| 15 | `direct_attributes` | D | C | `C` |
| 25 | `direct_attributes` | D | C | `C` |
| 34 | `direct_attributes` | A | C | `C` |
| 49 | `direct_attributes` | C | B | `B` |
| 51 | `direct_attributes` | A | C | `The helmet (likely referring to the helmet-shaped dome of the church or a white hat/helmet on a person) is white. The do` |
| 60 | `direct_attributes` | D | B | `B` |
| 69 | `direct_attributes` | C | D | `The oil painting in the image is the framed icon hanging on the pillar near the window. This icon depicts a religious fi` |
| 72 | `direct_attributes` | C | D | `D` |
| 75 | `direct_attributes` | A | D | `(D)` |
| 78 | `direct_attributes` | C | D | `D` |
| 83 | `direct_attributes` | D | A | `A` |
| 86 | `direct_attributes` | A | D | `D` |
| 116 | `relative_position` | A | B | `B` |
| 151 | `relative_position` | B | A | `A` |
| 159 | `relative_position` | A | B | `B` |
| 167 | `relative_position` | B | A | `The lamp post is located on the left side of the image. The ramp, which is designed for wheelchair access, is located on` |
| 178 | `relative_position` | B | A | `A` |
