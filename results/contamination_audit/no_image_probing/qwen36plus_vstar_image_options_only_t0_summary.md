# V* Image Evaluation

model: `qwen/qwen3.6-plus`
source: `results/qwen36plus_vstar_image_options_only_t0.jsonl`

## Overall

| requests | ok | parsed | correct | accuracy over parsed |
|---:|---:|---:|---:|---:|
| 191 | 191 | 191 | 74 | 38.7% |

## By Category

| category | n | parsed | correct | accuracy |
|---|---:|---:|---:|---:|
| `direct_attributes` | 115 | 115 | 36 | 31.3% |
| `relative_position` | 76 | 76 | 38 | 50.0% |

## By Option Count

| option count | n | parsed | correct | accuracy |
|---:|---:|---:|---:|---:|
| 2 | 84 | 84 | 42 | 50.0% |
| 4 | 107 | 107 | 32 | 29.9% |

## Errors

| qid | category | label | parsed | content |
|---:|---|---|---|---|
| 0 | `direct_attributes` | A | B | `B` |
| 1 | `direct_attributes` | C | D | `D` |
| 3 | `direct_attributes` | B | A | `A` |
| 4 | `direct_attributes` | C | A | `A` |
| 6 | `direct_attributes` | B | C | `C` |
| 8 | `direct_attributes` | B | D | `D` |
| 9 | `direct_attributes` | D | B | `B` |
| 12 | `direct_attributes` | C | D | `D` |
| 13 | `direct_attributes` | A | B | `B` |
| 15 | `direct_attributes` | D | B | `B` |
| 16 | `direct_attributes` | B | C | `C` |
| 18 | `direct_attributes` | C | D | `D` |
| 19 | `direct_attributes` | A | C | `C` |
| 21 | `direct_attributes` | A | C | `C` |
| 22 | `direct_attributes` | C | D | `D` |
| 24 | `direct_attributes` | B | A | `A` |
| 25 | `direct_attributes` | D | C | `C` |
| 26 | `direct_attributes` | B | A | `A` |
| 28 | `direct_attributes` | C | B | `B` |
| 29 | `direct_attributes` | B | D | `D` |
| 31 | `direct_attributes` | C | D | `D` |
| 33 | `direct_attributes` | C | D | `D` |
| 35 | `direct_attributes` | C | A | `A` |
| 39 | `direct_attributes` | C | A | `A` |
| 40 | `direct_attributes` | B | A | `A` |
| 42 | `direct_attributes` | A | B | `B` |
| 44 | `direct_attributes` | D | A | `A` |
| 46 | `direct_attributes` | A | B | `B` |
| 47 | `direct_attributes` | A | B | `B` |
| 48 | `direct_attributes` | B | A | `A` |
| 49 | `direct_attributes` | C | D | `D` |
| 50 | `direct_attributes` | A | C | `C` |
| 51 | `direct_attributes` | A | D | `D` |
| 53 | `direct_attributes` | C | D | `D` |
| 54 | `direct_attributes` | A | B | `B` |
| 55 | `direct_attributes` | D | A | `A` |
| 56 | `direct_attributes` | A | D | `D` |
| 58 | `direct_attributes` | B | A | `A` |
| 59 | `direct_attributes` | A | D | `D` |
| 61 | `direct_attributes` | A | C | `C` |
| 62 | `direct_attributes` | D | B | `B` |
| 63 | `direct_attributes` | D | C | `C` |
| 64 | `direct_attributes` | A | B | `B` |
| 65 | `direct_attributes` | A | D | `D` |
| 67 | `direct_attributes` | B | D | `D` |
| 68 | `direct_attributes` | A | B | `B` |
| 69 | `direct_attributes` | C | B | `B` |
| 70 | `direct_attributes` | B | D | `D` |
| 71 | `direct_attributes` | B | D | `D` |
| 72 | `direct_attributes` | C | D | `D` |
| 73 | `direct_attributes` | B | A | `A` |
| 74 | `direct_attributes` | A | C | `C` |
| 75 | `direct_attributes` | A | B | `B` |
| 76 | `direct_attributes` | D | B | `B` |
| 77 | `direct_attributes` | C | B | `B` |
| 78 | `direct_attributes` | C | D | `D` |
| 80 | `direct_attributes` | A | C | `C` |
| 81 | `direct_attributes` | A | D | `D` |
| 83 | `direct_attributes` | D | A | `A` |
| 84 | `direct_attributes` | A | B | `B` |
| 86 | `direct_attributes` | A | C | `C` |
| 87 | `direct_attributes` | B | A | `A` |
| 89 | `direct_attributes` | D | B | `B` |
| 90 | `direct_attributes` | C | A | `A` |
| 93 | `direct_attributes` | A | D | `D` |
| 95 | `direct_attributes` | A | B | `B` |
| 96 | `direct_attributes` | C | B | `B` |
| 99 | `direct_attributes` | D | C | `C` |
| 100 | `direct_attributes` | C | B | `B` |
| 101 | `direct_attributes` | B | A | `A` |
| 102 | `direct_attributes` | C | B | `B` |
| 103 | `direct_attributes` | B | D | `D` |
| 104 | `direct_attributes` | B | C | `C` |
| 105 | `direct_attributes` | D | A | `A` |
| 106 | `direct_attributes` | A | D | `D` |
| 107 | `direct_attributes` | A | C | `C` |
| 108 | `direct_attributes` | D | C | `C` |
| 112 | `direct_attributes` | D | A | `A` |
| 113 | `direct_attributes` | A | B | `B` |
| 115 | `relative_position` | A | B | `B` |
| 119 | `relative_position` | A | B | `B` |
| 120 | `relative_position` | B | A | `A` |
| 121 | `relative_position` | A | B | `B` |
| 122 | `relative_position` | B | A | `A` |
| 126 | `relative_position` | A | B | `B` |
| 127 | `relative_position` | A | B | `B` |
| 128 | `relative_position` | B | A | `A` |
| 129 | `relative_position` | B | A | `A` |
| 131 | `relative_position` | B | A | `A` |
| 132 | `relative_position` | B | A | `A` |
| 136 | `relative_position` | B | A | `A` |
| 137 | `relative_position` | A | B | `B` |
| 138 | `relative_position` | A | B | `B` |
| 139 | `relative_position` | A | B | `B` |
| 140 | `relative_position` | A | B | `B` |
| 144 | `relative_position` | B | A | `A` |
| 146 | `relative_position` | B | A | `A` |
| 148 | `relative_position` | B | A | `A` |
| 149 | `relative_position` | B | A | `A` |
| 151 | `relative_position` | B | A | `A` |
| 153 | `relative_position` | B | A | `A` |
| 154 | `relative_position` | A | B | `B` |
| 155 | `relative_position` | A | B | `B` |
| 156 | `relative_position` | A | B | `B` |
| 157 | `relative_position` | B | A | `A` |
| 158 | `relative_position` | B | A | `A` |
| 160 | `relative_position` | A | B | `B` |
| 161 | `relative_position` | A | B | `B` |
| 162 | `relative_position` | B | A | `A` |
| 163 | `relative_position` | B | A | `A` |
| 167 | `relative_position` | B | A | `A` |
| 170 | `relative_position` | A | B | `B` |
| 174 | `relative_position` | B | A | `A` |
| 177 | `relative_position` | B | A | `A` |
| 179 | `relative_position` | A | B | `B` |
| 180 | `relative_position` | A | B | `B` |
| 181 | `relative_position` | A | B | `B` |
