# Qwen V* Strict No-Image Bias Sweep

model: `qwen/qwen3.6-plus`
temperature: `0.1`
system: `Output exactly one uppercase option letter from A, B, C, or D. Do not explain.`

## Summary

| subset | items | strong top-choice bias | strong target-label bias | strong stem-seen-label bias |
|---|---:|---:|---:|---:|
| all | 191 | 150 (78.5%) | 50 (26.2%) | 61 (31.9%) |
| conflict/repeated-answer stems | 33 | 30 (90.9%) | 12 (36.4%) | 22 (66.7%) |
| non-conflict stems | 158 | 120 (75.9%) | 38 (24.1%) | 39 (24.7%) |

Definitions: strong top-choice bias means one parsed option has >=90% of repeats. Strong target-label bias means the V* label has >=90% of repeats. Strong stem-seen-label bias means labels appearing for the same stem in V* have >=90% of repeats; for unique stems this is equivalent to target-label bias.

## Conflict Stem Items

| qid | stem | target | seen labels | counts | top | target rate | seen-label rate |
|---:|---|---|---|---|---|---:|---:|
| 8 | what is the color of the plastic stool | B=blue | B,C | `{'C': 20}` | C (1.00) | 0.00 | 1.00 |
| 17 | what is the color of the bicycle | D=red | C,D | `{'D': 20}` | D (1.00) | 1.00 | 1.00 |
| 24 | what is the color of the car | B=black | B,D | `{'A': 20}` | A (1.00) | 0.00 | 0.00 |
| 25 | what is the color of the bicycle | D=yellow | C,D | `{'A': 20}` | A (1.00) | 0.00 | 0.00 |
| 27 | what is the color of the motorcycle | B=orange | B,D | `{'D': 19, 'A': 1}` | D (0.95) | 0.00 | 0.95 |
| 29 | what is the color of the man's cap | B=red | A,B,C | `{'B': 20}` | B (1.00) | 1.00 | 1.00 |
| 33 | what is the color of the man's cap | C=gray | A,B,C | `{'B': 20}` | B (1.00) | 0.00 | 1.00 |
| 34 | what is the color of the helmet | A=green | A | `{'D': 20}` | D (1.00) | 0.00 | 0.00 |
| 41 | what is the color of the man's cap | C=black | A,B,C | `{'C': 20}` | C (1.00) | 1.00 | 1.00 |
| 43 | what is the color of the car | B=white | B,D | `{'A': 20}` | A (1.00) | 0.00 | 0.00 |
| 45 | what is the color of the handbag | D=white | D | `{'B': 20}` | B (1.00) | 0.00 | 0.00 |
| 46 | what is the color of the man's cap | A=white | A,B,C | `{'C': 20}` | C (1.00) | 0.00 | 1.00 |
| 49 | what is the color of the plastic stool | C=white | B,C | `{'C': 20}` | C (1.00) | 1.00 | 1.00 |
| 51 | what is the color of the helmet | A=red | A | `{'C': 20}` | C (1.00) | 0.00 | 0.00 |
| 53 | what is the color of the trash can | C=green | A,C | `{'A': 20}` | A (1.00) | 0.00 | 1.00 |
| 57 | what is the color of the bicycle | C=red | C,D | `{'C': 20}` | C (1.00) | 1.00 | 1.00 |
| 58 | what is the color of the flag | B=blue and yellow | A,B | `{'A': 20}` | A (1.00) | 0.00 | 1.00 |
| 61 | what is the color of the dog | A=white | A,B,D | `{'A': 20}` | A (1.00) | 1.00 | 1.00 |
| 62 | what is the color of the motorcycle | D=black | B,D | `{'D': 19, 'A': 1}` | D (0.95) | 0.95 | 0.95 |
| 63 | what is the color of the car | D=silver | B,D | `{'A': 13, 'C': 7}` | A (0.65) | 0.00 | 0.00 |
| 70 | what is the color of the dog | B=black | A,B,D | `{'C': 3, 'D': 10, 'B': 7}` | D (0.50) | 0.35 | 0.85 |
| 74 | what is the color of the umbrella | A=purple | A,B,D | `{'D': 20}` | D (1.00) | 0.00 | 1.00 |
| 75 | what is the color of the backpack | A=gray | A | `{'A': 20}` | A (1.00) | 1.00 | 1.00 |
| 76 | what is the color of the umbrella | D=purple | A,B,D | `{'A': 20}` | A (1.00) | 0.00 | 1.00 |
| 81 | what is the color of the flag | A=red | A,B | `{'A': 20}` | A (1.00) | 1.00 | 1.00 |
| 83 | what is the color of the handbag | D=yellow | D | `{'C': 20}` | C (1.00) | 0.00 | 0.00 |
| 86 | what is the color of the trash can | A=black | A,C | `{'D': 17, 'A': 3}` | D (0.85) | 0.15 | 0.15 |
| 93 | what is the color of the helmet | A=white | A | `{'A': 20}` | A (1.00) | 1.00 | 1.00 |
| 94 | what is the color of the backpack | A=red | A | `{'B': 20}` | B (1.00) | 0.00 | 0.00 |
| 96 | what is the color of the bottle cap | C=red | C,D | `{'C': 20}` | C (1.00) | 1.00 | 1.00 |
| 97 | what is the color of the umbrella | B=blue | A,B,D | `{'A': 20}` | A (1.00) | 0.00 | 1.00 |
| 99 | what is the color of the dog | D=black and white | A,B,D | `{'D': 20}` | D (1.00) | 1.00 | 1.00 |
| 105 | what is the color of the bottle cap | D=blue | C,D | `{'C': 18, 'A': 2}` | C (0.90) | 0.00 | 0.90 |

## Strong Non-Conflict Target Bias Examples

| qid | stem | target | counts | target rate |
|---:|---|---|---|---:|
| 3 | what is the color of the woman's scarf | B=red | `{'B': 20}` | 1.00 |
| 14 | what is the cartoon character on the clock | B=Mickey Mouse | `{'B': 20}` | 1.00 |
| 16 | what is the color of the little girl's shirt | B=pink | `{'B': 20}` | 1.00 |
| 19 | what is the color of the bucket | A=white | `{'A': 20}` | 1.00 |
| 35 | what is the color of the woman's bikini | C=black | `{'C': 18, 'B': 2}` | 0.90 |
| 38 | is the color of the motorcycle orange or green | B=orange | `{'B': 20}` | 1.00 |
| 50 | what is the color of the motorcycle helmet | A=white | `{'A': 19, 'D': 1}` | 0.95 |
| 59 | what is the color of the cyclist's bag | A=orange and black | `{'A': 20}` | 1.00 |
| 60 | what is the breed of the dog | D=golden retriever | `{'D': 18, 'A': 2}` | 0.90 |
| 64 | does the kid have curly hair or straight hair | A=curly hair | `{'A': 20}` | 1.00 |
| 66 | what is the color of the body of the bucket | B=white | `{'B': 20}` | 1.00 |
| 71 | what is the color of the paraglider | B=blue | `{'B': 20}` | 1.00 |
| 87 | what is the color of the guard's glove | B=white | `{'B': 20}` | 1.00 |
| 92 | what is the color of the messenger bag | D=black | `{'D': 20}` | 1.00 |
| 98 | does the flag have two or three colors | B=three colors | `{'B': 20}` | 1.00 |
| 101 | what is the color of the life buoy | B=red and white | `{'B': 20}` | 1.00 |
| 111 | is the flag blue and yellow or red and yellow | B=blue and yellow | `{'B': 20}` | 1.00 |
| 113 | is the color of the plastic bucket black or green | A=green | `{'A': 20}` | 1.00 |
| 116 | is the red car on the left or right side of the police car | A=left | `{'A': 20}` | 1.00 |
| 117 | is the drum on the left or right side of the yellow balloon | A=left | `{'A': 20}` | 1.00 |
| 124 | is the dog on the left or right side of the golden tower | A=left | `{'A': 20}` | 1.00 |
| 126 | is the trash can on the left or right side of the baby carriage | A=right | `{'A': 18, 'B': 2}` | 0.90 |
| 129 | is the cyclist on the left or right side of the woman's handbag | B=left | `{'B': 19, 'A': 1}` | 0.95 |
| 133 | is the dog on the left or right side of the scooter | B=left | `{'B': 18, 'A': 2}` | 0.90 |
| 137 | is the blue bench on the left or right side of the green door | A=left | `{'A': 20}` | 1.00 |
| 141 | is the green statue on the left or right side of the white statue | A=left | `{'A': 20}` | 1.00 |
| 143 | is the man with yellow cap on the left or right side of the lamp post | A=left | `{'A': 20}` | 1.00 |
| 155 | is the motorcyclist on the left or right side of the truck | A=left | `{'A': 20}` | 1.00 |
| 159 | is the motorcycle on the left or right side of the street | A=left | `{'A': 18, 'B': 2}` | 0.90 |
| 161 | is the small red car on the left or right side of the baby carriage | A=left | `{'A': 20}` | 1.00 |
| 164 | is the yellow car on the left or right side of the pool | A=left | `{'A': 20}` | 1.00 |
| 169 | is the keyboard on the left or right side of the guitar | A=left | `{'A': 20}` | 1.00 |
| 172 | is the steel ladder on the left or right side of the wagon | A=left | `{'A': 20}` | 1.00 |
| 176 | is the broom on the left or right side of the folded chair | B=left | `{'B': 18, 'A': 2}` | 0.90 |
| 182 | which one is closer to the camera, the black vehicle or the silver vehicle | A=black vehicle | `{'A': 19, 'B': 1}` | 0.95 |
| 183 | which one is closer to the camera, the water bottle or the vehicle | A=water bottle | `{'A': 20}` | 1.00 |
| 186 | is the blue mask on the left or right side of the black mask | B=left | `{'B': 20}` | 1.00 |
| 188 | is the yellow umbrella on the left or right side of the pink umbrella | A=left | `{'A': 20}` | 1.00 |
