# Dynamic V* Visual-Key Slot Annotation Spec

Status: v1, aligned with `docs/dynamic_vstar/paper/method_idea_v1.md`
and `docs/dynamic_vstar/labelstudio_config.xml`.

## Goal

For each V* image, annotators mark local visual-key edit slots. A slot is a
local opportunity where the benchmark can either add a new answer-bearing
visual key or replace an existing one. The output drives later stages:

1. crop/context construction for image editing,
2. sampled add/replace concept generation,
3. dynamic V*-style question generation,
4. ground-truth construction from sampled metadata and final geometry.

The human annotation task should stay minimal. Annotators identify useful local
regions and choose broad add/replace concepts; they do not write generation
prompts, enumerate every object, or annotate a full object graph.

## Region Types

Each image has context groups and edit slots. A context group is one blue
`context_region` with a letter id such as `A`, `B`, or `C`. Each orange
`edit_region` under that context gets an id with the context letter plus an
index, such as `A1`, `A2`, `B1`, or `B2`.

The parser emits each orange edit region as an independent downstream slot and
copies the paired blue context region into it. This lets one large context crop
support multiple fine-grained editable details without changing the sampler or
generation pipeline.

### context_region

A larger crop region used for local scene understanding and image-generation
context.

Fields:

- `slot_id`: stable context id within the image, e.g. `A`.
- `xyxy`: absolute pixel coordinates.
- `ref`: short free-text description of what is inside this context crop.

`ref` should describe what the annotator sees:

- good: `back counter area with a water bottle, beige blank patch, and pink price sign`
- good: `vendor's upper body and hands with blue gloves`
- avoid: `this region is hard and useful for VQA`

### edit_region

A smaller region where an add or replace edit may happen.

Fields:

- `slot_id`: edit id prefixed by its paired context id, e.g. `A1` or `A2` for
  context `A`.
- `xyxy`: absolute pixel coordinates.
- `mode`: `add`, `replace`, or `either`.
- `add`: optional add concepts, present for `add` or `either`.
- `replace`: optional replace concepts, present for `replace` or `either`.

The edit region should usually lie inside the context region or be tightly
covered by it.

## Add Concepts

Add concepts describe what kind of new entity can be placed in the edit region.

Schema:

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
| `vertical_surface` | wall or object surface that can support a visible local edit |
| `vehicle_surface` | car/bus/bicycle/motorcycle surface where stickers or parts can appear |
| `body_or_clothing_surface` | clothing, glove, hat, shoe, bag, apron |
| `container_inside` | basket, bowl, box, bucket, bag opening, tray compartment |
| `hanging_or_overhead_area` | rail, rope, awning edge, branch, ceiling area where a small item could hang |

Initial add entity families:

| entity family | examples |
|---|---|
| `human` | small person, passerby, vendor-like figure; answer-bearing details should be clothes/accessories |
| `animal` | small animal; answer-bearing details should be body color, collar, or marking |
| `ground_vehicle` | stroller, bicycle, scooter, cart, toy vehicle |
| `water_vehicle` | tiny boat, toy boat, buoy-like float |
| `tiny_object` | clip, cap, rubber band, toy block, small tag |
| `sticker_or_tag` | sticker, label, tape strip, tag |
| `small_container` | cup, small bottle, jar, tin |
| `food_item` | fruit slice, bun, candy, packet |
| `plant_or_flower` | small potted plant, flower, leaf |
| `tool_or_device` | small flashlight, camera, phone, utensil, key |
| `wearable_accessory` | badge, pin, bracelet, hair clip, scarf, small bag |
| `surface_mark` | dot, stripe, patch, stain-like mark |

The downstream sampler must apply compatibility checks. For example,
`water_vehicle` should only be sampled for `water_surface`; `ground_vehicle`
should require `road_or_path` or `walkable_ground`.

## Replace Concepts

Replace concepts describe the existing target that can be modified and which
visual attributes may change. The orange edit box is the primary target
binding. If the edit box contains several plausible replace targets, annotators
list them separately; each target has its own attribute scope and edit types.

Schema:

```json
{
  "targets": [
    {
      "target_ref": "blue plastic glove",
      "attribute_scope": "wearable",
      "edit_types": ["color_change", "material_change", "pattern_change"]
    },
    {
      "target_ref": "white phone",
      "attribute_scope": "tool_device",
      "edit_types": ["sticker_addition", "marking_addition"]
    }
  ]
}
```

Fields:

| field | required | meaning |
|---|---:|---|
| `targets` | required | list of candidate targets inside the edit box |
| `targets[].target_ref` | required | short description of the exact object or surface to edit |
| `targets[].attribute_scope` | optional | extra constraint over the sampled attribute pools for this target type |
| `targets[].edit_types` | required | allowed replace operations for this specific target |

Initial attribute scopes:

| attribute scope | examples |
|---|---|
| `wearable` | glove, hat, shoe, bag, apron, shirt |
| `container` | bottle, cup, jar, box, bucket |
| `hard_object` | rigid small objects and durable parts |
| `surface` | wall, table, vehicle, clothing, or object-surface patches |
| `paper_label` | signs, labels, tags, posters, price cards |
| `vehicle_part` | wheel, light, mirror, handlebar, body patch |
| `tool_device` | camera, phone, clock, utensil, small tool |

Initial edit types:

| edit type | meaning |
|---|---|
| `color_change` | change the dominant color of the target or target part |
| `material_change` | change the visible material or texture of the target or target part |
| `pattern_change` | add or change a simple pattern |
| `small_part_replace` | change a localized part such as cap, wheel, handle, label edge |
| `accessory_addition` | add a small accessory on or attached to the target |
| `sticker_addition` | add a small sticker/tag/label to target surface |
| `marking_addition` | add a simple mark, dot, stripe, or patch |

The safest v0 replace edits preserve target identity: color changes, simple
patterns, small stickers, small patches, cap/handle/label color, local
markings, or material changes constrained by an appropriate attribute scope.

Examples:

```json
{
  "targets": [
    {
      "target_ref": "blue plastic glove",
      "attribute_scope": "wearable",
      "edit_types": ["color_change", "pattern_change", "marking_addition"]
    }
  ]
}
```

```json
{
  "targets": [
    {
      "target_ref": "white refrigerator door surface",
      "attribute_scope": "surface",
      "edit_types": ["sticker_addition", "marking_addition"]
    },
    {
      "target_ref": "small blue bottle cap",
      "attribute_scope": "container",
      "edit_types": ["color_change", "small_part_replace"]
    }
  ]
}
```

## Drawing Rules

- Draw a `context_region` first, then one or more paired `edit_region` boxes.
- Use letter ids for context boxes, e.g. `A`, `B`, `C`.
- Use numbered ids for edit boxes under each context, e.g. `A1`, `A2`, `B1`.
- Aim for 3-6 slots per image for the first pilot.
- The context region should include enough surrounding visual context for the
  image editor to make a natural local edit.
- The edit region should be tight around the area to change.
- For `add`, choose at least one placement and one entity family.
- For `replace`, fill one or more target groups. Each target group needs a
  concrete `target_ref` and at least one edit type. Use separate groups when
  one orange box contains multiple plausible targets.
- For `either`, fill at least one valid add or replace concept set; filling
  both is preferred.

## Output Format

One JSONL row per image:

```json
{
  "image_id": "vstar_0004",
  "question_id": "4",
  "category": "direct_attributes",
  "slots": [
    {
      "slot_id": "A1",
      "context_region": {
        "xyxy": [1040, 40, 1530, 250],
        "ref": "back counter area with a water bottle, beige blank patch, and pink price sign"
      },
      "edit_region": {
        "xyxy": [1204, 112, 1268, 177],
        "mode": "add"
      },
      "add": {
        "placements": ["countertop_or_table"],
        "entity_families": ["tiny_object", "sticker_or_tag", "small_container"]
      }
    },
    {
      "slot_id": "A2",
      "context_region": {
        "xyxy": [1040, 40, 1530, 250],
        "ref": "back counter area with a water bottle, beige blank patch, and pink price sign"
      },
      "edit_region": {
        "xyxy": [1360, 70, 1420, 130],
        "mode": "add"
      },
      "add": {
        "placements": ["vertical_surface"],
        "entity_families": ["sticker_or_tag", "surface_mark"]
      }
    }
  ]
}
```

## Tool: Label Studio

The labeling interface XML lives in:

```text
docs/dynamic_vstar/labelstudio_config.xml
```

The parser lives in:

```text
scripts/parse_labelstudio_export.py
```

After annotation, export from Label Studio and run:

```bash
python scripts/parse_labelstudio_export.py \
  --export path/to/labelstudio-export.json \
  --out data/annotations/dynamic_vstar_slots_v1.jsonl
```

Validation warnings are printed to stderr. Incomplete slots are skipped while
other valid slots in the same image are still emitted.
