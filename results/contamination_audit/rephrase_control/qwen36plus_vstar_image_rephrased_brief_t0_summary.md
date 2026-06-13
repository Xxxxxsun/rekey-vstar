# V* Image Evaluation

model: `qwen/qwen3.6-plus`
source: `results/qwen36plus_vstar_image_rephrased_brief_t0.jsonl`

## Overall

| requests | ok | parsed | correct | accuracy over parsed |
|---:|---:|---:|---:|---:|
| 191 | 191 | 191 | 150 | 78.5% |

## By Category

| category | n | parsed | correct | accuracy |
|---|---:|---:|---:|---:|
| `direct_attributes` | 115 | 115 | 87 | 75.7% |
| `relative_position` | 76 | 76 | 63 | 82.9% |

## By Option Count

| option count | n | parsed | correct | accuracy |
|---:|---:|---:|---:|---:|
| 2 | 84 | 84 | 70 | 83.3% |
| 4 | 107 | 107 | 80 | 74.8% |

## Errors

| qid | category | label | parsed | content |
|---:|---|---|---|---|
| 9 | `direct_attributes` | D | B | `The image shows a white truck, and there is no tissue box visible in the scene.  Final answer: B` |
| 15 | `direct_attributes` | D | B | `The image shows the exterior of The Trump World Tower building and does not contain a suitcase, making the question unan` |
| 23 | `direct_attributes` | B | A | `The image does not contain a woman with pink hair or any visible handbag matching the description, making the question u` |
| 24 | `direct_attributes` | B | A | `The image shows a large white boat docked at a pier, and since "car" is likely a misnomer for the vessel, its dominant c` |
| 31 | `direct_attributes` | C | B | `The image shows a street scene with buildings, cars, and utility poles, but there is no visible telephone in the frame —` |
| 34 | `direct_attributes` | A | D | `The image shows a street scene with buildings and trees, but there is no helmet visible anywhere in the frame.  Final an` |
| 37 | `direct_attributes` | C | D | `The clock visible in the shop window has a distinct red casing.  Final answer: D` |
| 42 | `direct_attributes` | A | B | `The image shows a cityscape with boats on a river and historic buildings, but there is no van visible in the scene.  Fin` |
| 44 | `direct_attributes` | D | A | `The image shows a dental office with green cabinets and accents, but no toothbrush is visibly present in the scene.  Fin` |
| 45 | `direct_attributes` | D | B | `The image shows a park scene with benches, trees, and a building in the background; there is no visible handbag in the i` |
| 51 | `direct_attributes` | A | C | `The image shows a boat on a river with a white arched structure and churches in the background, but there is no helmet v` |
| 58 | `direct_attributes` | B | C | `The image displays a large floral clock and figures on a grassy hill, but there is no flag visible in the scene to deter` |
| 60 | `direct_attributes` | D | A | `The image shows a statue of Dante in a plaza and does not contain a dog, making it impossible to determine a breed from ` |
| 67 | `direct_attributes` | B | D | `The person in the vehicle ahead is wearing a bright yellow scarf or hooded garment, which stands out against the snowy b` |
| 68 | `direct_attributes` | A | B | `The prominent floating structure in the foreground, which functions as a flag or marker, is distinctly colored red.  Fin` |
| 69 | `direct_attributes` | C | B | `The image shows a playroom with cartoon rabbit decals on the wall and a small framed picture, but no actual oil painting` |
| 72 | `direct_attributes` | C | D | `The woman visible in the lower right background is wearing a light-colored, sleeveless dress that appears white.  Final ` |
| 75 | `direct_attributes` | A | D | `The image shows a park scene with people, but no one is clearly wearing a backpack that is visible and identifiable in c` |
| 76 | `direct_attributes` | D | C | `The image shows a grand palace with ornate architecture and manicured gardens, but there is no umbrella visible anywhere` |
| 78 | `direct_attributes` | C | D | `The watch is not clearly visible in the image; however, among the people shown, no one is wearing a prominently visible ` |
| 80 | `direct_attributes` | A | D | `The image shows a street performer holding a wind instrument that appears to be made of metal with a shiny, reflective s` |
| 81 | `direct_attributes` | A | D | `The large, domed structure in the background is made of blue-tinted glass panels, giving it a distinct blue appearance. ` |
| 82 | `direct_attributes` | D | A | `The image shows a public square with a monument, flags, and historic buildings, but there is no soda can visible anywher` |
| 83 | `direct_attributes` | D | C | `The image shows a courtyard of a historic building with stone walls, red-tiled roofs, and green trees — there is no hand` |
| 84 | `direct_attributes` | A | D | `The image shows a street scene with various shops and signs, but there is no visible straw in the image to determine its` |
| 87 | `direct_attributes` | B | A | `The image shows a war memorial with bronze statues of soldiers, not a live guard wearing gloves; however, if referring t` |
| 109 | `direct_attributes` | A | C | `The image shows the exterior of a grand building (Teatr im. Juliusza Słowackiego) with no tablecloth visible anywhere in` |
| 110 | `direct_attributes` | D | A | `The image shows a large building and does not contain any visible hats, making the question unanswerable based on the pr` |
| 120 | `relative_position` | B | A | `The person wearing orange is on the small bridge over the pond, and the baby stroller is visible on the path behind and ` |
| 134 | `relative_position` | B | A | `In the background on the right side of the image, a green trash can is visible next to white chairs and a black bench or` |
| 135 | `relative_position` | B | A | `The question appears to misidentify boats as people; however, interpreting the "individual wearing white trousers" as th` |
| 136 | `relative_position` | B | A | `Upon close inspection of the image, there is no dog visible on either side of the river or in the boats.  Final answer: ` |
| 139 | `relative_position` | A | B | `The image displays a townscape with buildings and greenery, but there are no visible trucks or vehicles to determine the` |
| 140 | `relative_position` | A | B | `The image does not contain a plunger, so the relative position of the bucket to a non-existent object cannot be determin` |
| 151 | `relative_position` | B | A | `The red chair is visible on the sidewalk next to the decorative structure on the left side of the road from the viewer's` |
| 152 | `relative_position` | A | B | `The faucet is attached to the right side of the cart near the man, while the bowl sits on the counter further to the lef` |
| 153 | `relative_position` | B | A | `The image shows a wide cityscape with no clearly visible white truck or red truck in the foreground or midground that ca` |
| 159 | `relative_position` | A | B | `The motorcycle is visible in the distance, parked along the right-hand side of the cobblestone street.  Final answer: B` |
| 162 | `relative_position` | B | A | `The image is a landscape view of a castle and bridge with no clearly visible individuals wearing a beanie or carrying a ` |
| 164 | `relative_position` | A | B | `The image shows a cityscape with a blue pool in the lower center, surrounded by palm trees. To the right of the pool, al` |
| 168 | `relative_position` | B | A | `The image does not contain a blue bicycle or a dog, so the question cannot be answered based on visible content.  Final ` |
