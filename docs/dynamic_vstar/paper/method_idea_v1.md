# Dynamic V* Method Idea v1

## 1. Core thesis

V* is valuable because each image contains a small number of scarce visual
keys: details that are uniquely identifiable, hard to notice in a cluttered
high-resolution scene, and sufficient to answer a question. Once such a visual
key and its answer leak, the static item loses much of its evaluation value.

Dynamic V* refreshes those scarce visual keys instead of only rewriting the
question. For each source image, humans annotate local edit slots where a new
visual key can be inserted or an existing visual key can be replaced. At
evaluation time, the system samples slots and edit concepts, generates an
edited image, and constructs V*-style questions whose answers are grounded in
sampled edit metadata and final box geometry.

The method is not "let a generator make a new benchmark from scratch." The
human role is to identify local visual opportunities that VLMs and generic
image generators are unlikely to find reliably on their own. The system role is
to instantiate those opportunities with controlled, sampled visual details.

## 2. Human annotation unit: visual-key edit slot

The v1 annotation unit is a context group plus one or more `visual_key_slot`s,
not an anchor/object graph. Annotators give each blue context group a letter id
such as `A` or `B`; orange edit boxes inside that context use ids such as `A1`,
`A2`, or `B1`. The parser emits each orange edit box as an independent
downstream slot and copies the shared context crop into it.

Each slot has:

```json
{
  "slot_id": "A1",
  "context_region": {
    "xyxy": [x1, y1, x2, y2],
    "ref": "back counter area with a water bottle, beige blank patch, and pink price sign"
  },
  "edit_region": {
    "xyxy": [x1, y1, x2, y2],
    "mode": "add"
  },
  "add": {
    "placements": ["countertop_or_table"],
    "entity_families": ["tiny_object", "sticker_or_tag", "small_container"]
  }
}
```

Field meanings:

- `context_region`: a larger local crop used for scene understanding and
  image-generation context. It should contain the edit region plus nearby
  visual context that helps generation look natural.
- `context_region.ref`: the only free-text reference field. It should briefly
  describe what is inside the context crop. It should say what the annotator
  sees, not why the region is hard.
- `edit_region`: the smaller region that may actually be changed.
- `mode`: `add`, `replace`, or `either`.
- `add`: optional, present when `mode` is `add` or `either`.
- `replace`: optional, present when `mode` is `replace` or `either`.

The previous `anchor` concept is not mandatory in v1. Local references such as
"near the price sign" live inside `context_region.ref`. For v0, position
questions primarily use generated object boxes and edit-region geometry rather
than a full pre-annotated object graph.

## 3. Why simplify the annotation

The annotation should encode the information only humans can provide cheaply:

1. Where is a local region that can support a new or refreshed visual key?
2. What is inside that local region, in ordinary language?
3. For this region, which add or replace concepts are plausible?
4. If replacing, what exact object or surface is the orange box meant to edit?

It should not force annotators to pre-write prompts, enumerate every possible
object, label global scene semantics, or define all possible relations. Those
choices are better handled by a sampler and a planner prompt conditioned on the
source V* question.

This keeps the human task scalable and protects diversity: the same context
can host multiple independent edit slots, and each slot can generate many
different visual keys across seeds.

## 4. Add vs replace

Dynamic V* has two edit modes.

### Add

Insert a new visual key into a semantically plausible region.

Example:

- Source slot: small blank patch on the back counter.
- Add placement: `countertop_or_table`.
- Sampled entity: `tiny_object`.
- Sampled concrete edit: tiny blue plastic clip.
- Possible question: "What color is the tiny clip on the back counter?"

### Replace

Modify an existing unique visual key while preserving its local identity and
scene role.

Example:

- Source slot: vendor's blue glove.
- Replace target reference: `blue plastic glove`.
- Sampled edit: change the glove to yellow, or add a small striped patch.
- Possible question: "What color is the glove on the vendor's hand?"

Replace mode is especially important because it directly addresses the V*
failure mode: if a static unique visual key has leaked, the benchmark can keep
the hard location but refresh the answer-bearing appearance.

## 5. Edit concept library

Dynamic V* should use a controlled edit concept library, not a fixed
image-asset library and not fully open-ended LLM invention.

The library has two parts:

1. Add concepts: what kind of new entity can be placed in the edit region.
2. Replace concepts: what kind of existing target can be modified, and which
   visual attributes may change.

This split is important. Adding a new object is constrained by the physical
surface or local scene; replacing an existing object is constrained by the
target's identity and editable visual attributes.

### 5.1 Add concepts

Add concepts use two fields:

```json
{
  "placements": ["countertop_or_table"],
  "entity_families": ["tiny_object", "sticker_or_tag", "small_container"]
}
```

`placements` describe what the edit region can physically support.

Initial placement set:

| placement | meaning |
|---|---|
| `walkable_ground` | sidewalk, floor, path, plaza, beach, grass where a person/animal/object can stand |
| `road_or_path` | road, lane, driveway, bike path; suitable for vehicles or road objects |
| `countertop_or_table` | counter, table, stall surface, desk, tray edge |
| `shelf_or_display` | shelf, rack, display case, market stand, product display |
| `water_surface` | sea, lake, river, pool, puddle large enough for floating objects |
| `vertical_surface` | wall, signboard, door, window, poster, flat vertical panel |
| `vehicle_surface` | car/bus/bicycle/motorcycle surface where stickers or parts can appear |
| `body_or_clothing_surface` | clothing, glove, hat, shoe, bag, apron; mostly for small accessories or markings |
| `container_inside` | basket, bowl, box, bucket, bag opening, tray compartment |
| `hanging_or_overhead_area` | rail, rope, awning edge, branch, ceiling area where a small item could hang |

`entity_families` are broad families that can be sampled after placement
filtering.

Initial add entity families:

| entity family | compatible placements | sampled details |
|---|---|---|
| `human` | `walkable_ground`, `road_or_path` | hat, hair, shirt/top color, pants color, shoe color, carried bag |
| `animal` | `walkable_ground`, `water_surface` | species, body color, collar color, marking |
| `ground_vehicle` | `road_or_path`, `walkable_ground` | stroller, bicycle, scooter, cart, toy vehicle; color, wheel color, cargo |
| `water_vehicle` | `water_surface` | tiny boat, toy boat, buoy-like float; color, stripe pattern |
| `tiny_object` | `countertop_or_table`, `shelf_or_display`, `walkable_ground`, `container_inside` | clip, cap, rubber band, toy block, small tag; color, material, pattern |
| `sticker_or_tag` | `vertical_surface`, `vehicle_surface`, `body_or_clothing_surface`, `countertop_or_table` | sticker, label, tape strip, tag; color, border, simple pattern |
| `small_container` | `countertop_or_table`, `shelf_or_display`, `walkable_ground`, `container_inside` | cup, small bottle, jar, tin; color, material |
| `food_item` | `countertop_or_table`, `shelf_or_display`, `container_inside` | fruit slice, bun, candy, packet; color, shape |
| `plant_or_flower` | `walkable_ground`, `countertop_or_table`, `shelf_or_display`, `container_inside` | small potted plant, flower, leaf; flower color, pot color |
| `tool_or_device` | `countertop_or_table`, `shelf_or_display`, `walkable_ground` | small flashlight, camera, phone, utensil, key; color, material |
| `wearable_accessory` | `body_or_clothing_surface`, `countertop_or_table`, `walkable_ground` | badge, pin, bracelet, hair clip, scarf, small bag; color, pattern |
| `surface_mark` | `vertical_surface`, `vehicle_surface`, `body_or_clothing_surface`, `countertop_or_table` | dot, stripe, patch, stain-like mark; color, shape |

The sampler must apply compatibility checks before choosing a concrete entity.
For example, `water_vehicle` requires `water_surface`, while `ground_vehicle`
requires `road_or_path` or `walkable_ground`. This prevents invalid samples
such as a stroller on the sea or a boat on a table.

### 5.2 Replace concepts

Replace concepts use:

```json
{
  "targets": [
    {
      "target_ref": "blue plastic glove",
      "attribute_scope": "wearable",
      "edit_types": ["color_change", "pattern_change", "accessory_addition"]
    },
    {
      "target_ref": "white phone",
      "attribute_scope": "tool_device",
      "edit_types": ["sticker_addition", "marking_addition"]
    }
  ]
}
```

Each replace target has its own `target_ref`, `attribute_scope`, and
`edit_types`. If the orange edit box contains multiple plausible targets, the
annotator lists them as separate target entries rather than choosing a broad
target family.

Initial attribute scopes:

| attribute scope | intended targets | initially constrained attributes |
|---|---|---|
| `wearable` | glove, hat, shoe, bag, apron, shirt | wearable materials such as fabric, leather, rubber, denim |
| `container` | bottle, cup, jar, box, bucket | container materials such as plastic, glass, metal, ceramic |
| `hard_object` | rigid small objects and durable parts | hard materials such as metal, plastic, wood, glass |
| `surface` | wall/table/object-surface patches | surface materials such as metal, wood, plastic, fabric |
| `paper_label` | sign, label, tag, poster, price card | paper/label materials such as paper, plastic, fabric |
| `vehicle_part` | wheel, light, mirror, handlebar, body patch | vehicle-part materials such as metal, plastic, rubber, glass |
| `tool_device` | camera, phone, clock, utensil, small tool | tool/device materials such as metal, plastic, rubber, glass |

Initial edit types:

| edit type | meaning | typical answers |
|---|---|---|
| `color_change` | change the dominant color of the target or target part | red, blue, yellow, green, black, white |
| `material_change` | change visible material within an appropriate attribute scope | fabric, rubber, metal, glass |
| `pattern_change` | add or change a simple pattern | striped, spotted, plain, checked |
| `small_part_replace` | change a localized part such as cap, wheel, handle, label edge | part color, part shape |
| `accessory_addition` | add a small accessory on or attached to the target | badge color, pin color, clip color |
| `sticker_addition` | add a small sticker/tag/label to target surface | sticker color, sticker position |
| `marking_addition` | add a simple mark, dot, stripe, or patch | mark color, mark shape |

The safest v0 replace edits are visual-attribute edits that preserve object
identity: color, simple pattern, small sticker, small patch, cap/handle/label
color, and material change when the attribute scope is compatible with the
target. Replacing whole objects should be avoided unless the edit region is
large and the target identity remains unambiguous.

### 5.3 Human and animal concepts

Human, animal, and vehicle concepts are allowed in v1, but the benchmark should
prefer answer-bearing local details over broad identity attributes.

For a generated human, questions should usually target:

- hat color
- shirt/top color
- pants color
- shoe color
- bag color
- hair color or hairstyle only when visually clear

For a generated animal, questions should usually target:

- body color
- collar color
- visible marking color or pattern
- species only when unambiguous

For a generated vehicle, questions should usually target:

- body color
- wheel color
- cargo or basket color
- sticker/stripe color

This keeps the task visually grounded while avoiding unstable attributes such
as age, gender, emotion, brand, breed, or fine-grained identity.

## 6. Sampling

For each dynamic run:

1. Sample a source image.
2. Infer the source question type.
3. Sample visual-key slots from that image:
   - direct attribute source question: sample one slot;
   - relative-position source question: sample two slots when possible.
4. For each sampled slot, sample an add or replace path according to
   `edit_region.mode`.
5. For add mode, sample a compatible entity family from the slot's
   `placements` and `entity_families`.
6. For replace mode, sample one entry from `replace.targets`, then sample an
   edit type from that target's own `edit_types`. A replace target must have a
   concrete human-written `target_ref`; broad target families alone are not
   enough for sampling.
7. Sample concrete answer-bearing attributes from the concept library.
8. Condition the planner on the original V* question type and the sampled edit
   metadata.

Recommended v0 slot-count distribution:

- 80%: edit one slot.
- 18%: edit two slots.
- 2%: edit three slots.

Most direct-attribute v0 examples edit only one slot. Multi-slot edits are used
mainly for relative-position questions between generated visual keys.

## 7. Source-question-conditioned planning

The source V* question should be an input to the planner. It tells the system
what kind of visual reasoning the original item was designed to probe.

If the source question is a color question, the dynamic item should usually
produce a color or appearance question over the new or replaced visual key.

If the source question is a relative-position question, the dynamic item should
sample two slots and produce a left/right question between the two generated or
replaced visual keys.

For v0, the position relation set is intentionally limited to:

- left of
- right of

These are computable from box coordinates. Above/below, depth, occlusion,
closer/farther, inside/outside, and support relations should be left for later
versions unless they are explicitly verified after generation.

## 8. Planner prompt

The planner is a VLM. It receives:

- the local context crop for each sampled slot,
- an orange edit box drawn on the crop,
- the source V* question,
- `context_region.ref`,
- sampled concrete edit metadata,
- for add edits, a natural-language placement hint derived from the sampled
  affordance.

The planner does not choose arbitrary objects. The prompt already includes the
sampled object or replace target and answer-bearing attributes. The planner's
job is only to turn them into:

```json
{"edit_prompt": "...", "target_phrase": "..."}
```

It does not generate the question type, answer, options, or correct label.
Those are constructed by code from sampled metadata and box geometry.

Example single-slot planner prompt:

```text
Look at this local crop. The orange box marks the exact area to edit.

Original question: What is the color of the motorcycle?
Local context: back counter area with a water bottle and price sign
Required edit: add a small blue plastic clip
Placement hint: place it on the visible tabletop or counter surface.

Write one short image-edit prompt for this crop and one short phrase that
uniquely names the edited visual detail.
The target phrase must not include the new answer value "blue".

Return JSON only: {"edit_prompt": "...", "target_phrase": "..."}
```

Expected output:

```json
{
  "edit_prompt": "add a small blue plastic clip on the counter near the water bottle",
  "target_phrase": "the small plastic clip near the water bottle"
}
```

## 9. Image generation prompt

The image editor receives:

- a local context crop with the orange edit box,
- the same local context crop without guide markings as clean reference,
- the planner's `edit_prompt`.

Each slot is edited independently, then pasted back sequentially into the
current image. The guide image is only a localization aid; the output must
remove all colored boxes and preserve unrelated crop content.

Example edit prompt:

```text
You receive two input images with the same standard canvas size. The first image
contains the local crop and an orange box marking the exact edit region. The
second image contains the same local crop without guide markings and must be
used as the clean visual reference.

add a small blue plastic clip on the counter near the water bottle

Return one edited image at the same canvas size. Make the requested change in
the orange-boxed region, remove the orange box, and preserve unrelated content.
```

The current v0 paste path restores the generated crop content to the original
context-region size and directly composites that context crop back into the
source image. Soft masks can be tested later as an ablation.

## 10. Ground truth construction

Dynamic V* ground truth comes from sampled metadata and final geometry.

For direct-attribute questions:

- The answer is the sampled and verified attribute, e.g. `blue`.
- Distractors are sampled from the same attribute family and should avoid
  ambiguity with nearby scene colors when possible.

For position questions:

- The answer is computed from the sampled edit boxes.
- v0 asks only left/right between the two sampled slots.

For v0, position ground truth should use center coordinates:

```text
center_x = (x1 + x2) / 2
left/right: compare center_x
```

Items with small margins should be rejected:

```text
abs(center_x_a - center_x_b) < margin_x -> reject left/right question
```

The margin should be a fraction of image size or context crop size, not a fixed
global pixel threshold only.

## 11. Verification

Sampling and generation do not guarantee uniqueness. Uniqueness is a
post-generation property.

Each generated item needs verification:

1. Is the edited visual key visible?
2. Is it inside or tightly near the edit region?
3. Is the sampled attribute clear?
4. Is there exactly one object matching the target phrase?
5. If the question is positional, is the relation unambiguous under the margin
   rule?
6. Did the editor avoid changing unrelated parts of the image?
7. Is the question hard to answer without the image?

Verification can combine automatic checks, VLM readback, and lightweight human
review. The paper should report acceptance rate and common failure modes.

## 12. Question generation

Questions are generated after the edit is accepted.

The source V* question controls style and type, not the answer. The new answer
comes from the sampled and verified visual key.

Direct-attribute template:

```text
What {attribute} is the {target_phrase}?
(A) sampled answer (B/C/D) same-family distractors
Answer with the option's letter from the given choices directly.
```

Position template:

```text
Is the {target_phrase_1} to the left or right of the {target_phrase_2}?
(A) left (B) right
Answer with the option's letter from the given choices directly.
```

For v0, the safest target phrases are based on the generated visual key and the
context `ref`, for example:

- "tiny blue plastic clip on the back counter near the price sign"
- "yellow patch on the vendor's glove"
- "small red tag on the blank wall area"

## 13. Difference from VLB

VLB perturbs an existing VQA sample while trying to preserve the original
answer. Its judge checks whether the old answer still holds.

Dynamic V* regenerates the answer-bearing visual key itself. The answer is not
preserved; it is newly constructed from sampled attributes and final geometry.

This gives the paper three clean differentiators:

1. Human-scouted local visual-key slots for high-resolution V* images.
2. Add-or-replace regeneration of scarce answer-bearing visual keys.
3. Constructive ground truth from sampled metadata and geometry rather than a
   VLM judge preserving the old answer.

## 14. Minimal v0 experiment

For a first pilot:

- Annotate 50 V* images.
- Mark 3-6 visual-key slots per image.
- Use the v1 add/replace concept library above.
- Generate 100 accepted dynamic items.
- Keep 70 direct-attribute questions and 30 position questions.
- Run Qwen3.6-Plus plus two non-Qwen controls.
- Run no-image controls.
- Run an edit-detection shortcut probe.
- Report acceptance rate, verification failures, and model accuracy.

The goal of v0 is not to prove a full production benchmark. It is to show that
the visual-key slot abstraction can regenerate V*-style hard questions whose
answers are fresh, controlled, and grounded.
