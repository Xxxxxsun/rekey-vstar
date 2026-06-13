# V* Image Evaluation

model: `qwen/qwen3.6-plus`
source: `results/qwen36plus_vstar_relabel_current_rawprompt_originalimage_t0.jsonl`

## Overall

| requests | ok | parsed | correct | accuracy over parsed |
|---:|---:|---:|---:|---:|
| 191 | 191 | 191 | 144 | 75.4% |

## By Category

| category | n | parsed | correct | accuracy |
|---|---:|---:|---:|---:|
| `direct_attributes` | 115 | 115 | 80 | 69.6% |
| `relative_position` | 76 | 76 | 64 | 84.2% |

## By Option Count

| option count | n | parsed | correct | accuracy |
|---:|---:|---:|---:|---:|
| 2 | 84 | 84 | 69 | 82.1% |
| 4 | 107 | 107 | 75 | 70.1% |

## Errors

| qid | category | label | parsed | content |
|---:|---|---|---|---|
| 3 | `direct_attributes` | B | A | `A` |
| 4 | `direct_attributes` | D | C | `C` |
| 5 | `direct_attributes` | A | B | `B` |
| 6 | `direct_attributes` | B | D | `D` |
| 11 | `direct_attributes` | C | B | `B` |
| 13 | `direct_attributes` | C | A | `A` |
| 15 | `direct_attributes` | B | C | `C` |
| 16 | `direct_attributes` | D | B | `The person wearing a yellow dress is likely the woman on the right (although her clothing appears dark/black in the shad` |
| 20 | `direct_attributes` | B | A | `A` |
| 23 | `direct_attributes` | D | A | `A` |
| 26 | `direct_attributes` | A | B | `B` |
| 30 | `direct_attributes` | B | A | `A` |
| 33 | `direct_attributes` | D | C | `C` |
| 37 | `direct_attributes` | C | B | `B` |
| 46 | `direct_attributes` | D | A | `A` |
| 48 | `direct_attributes` | D | B | `B` |
| 50 | `direct_attributes` | B | C | `C` |
| 51 | `direct_attributes` | A | D | `D` |
| 53 | `direct_attributes` | C | D | `The person carrying a blue bag is walking in the middle-left area of the image. To their right, there is a green trash c` |
| 59 | `direct_attributes` | C | B | `B` |
| 61 | `direct_attributes` | B | C | `C` |
| 62 | `direct_attributes` | C | A | `A` |
| 64 | `direct_attributes` | A | B | `B` |
| 66 | `direct_attributes` | A | C | `The scooter visible on the far right side of the image is primarily **black**. It appears to be an electric rental scoot` |
| 67 | `direct_attributes` | D | C | `C` |
| 68 | `direct_attributes` | A | B | `B` |
| 69 | `direct_attributes` | C | A | `A` |
| 72 | `direct_attributes` | D | C | `C` |
| 83 | `direct_attributes` | C | D | `D` |
| 84 | `direct_attributes` | C | B | `B` |
| 96 | `direct_attributes` | D | B | `B` |
| 98 | `direct_attributes` | B | A | `A` |
| 101 | `direct_attributes` | C | A | `A` |
| 102 | `direct_attributes` | C | A | `A` |
| 104 | `direct_attributes` | B | C | `C` |
| 120 | `relative_position` | B | A | `A` |
| 121 | `relative_position` | A | B | `B` |
| 128 | `relative_position` | B | A | `A` |
| 141 | `relative_position` | A | B | `The "window on the full shutter" likely refers to the tall, white, rectangular window (covered by a shutter or blind) lo` |
| 152 | `relative_position` | B | A | `A` |
| 156 | `relative_position` | A | B | `B` |
| 158 | `relative_position` | B | A | `A` |
| 160 | `relative_position` | A | B | `(B)` |
| 161 | `relative_position` | B | A | `A` |
| 170 | `relative_position` | B | A | `A` |
| 188 | `relative_position` | A | B | `B` |
| 189 | `relative_position` | A | B | `The motorcycle is located on the far right side of the image, moving away from the camera. The most prominent pedestrian` |
