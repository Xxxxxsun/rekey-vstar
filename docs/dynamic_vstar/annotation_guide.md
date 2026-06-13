# Dynamic V* Annotation Guide

## Goal

Mark objects in V* images for dynamic benchmark generation. The pipeline
edits images (replace colors / add new objects) and generates VQA questions.

## Annotation Steps

### Blue box (context_region)

Draw a crop area covering the target and its surroundings. Write a letter
ID (A, B, C). Description is optional.

### Orange box (edit_region)

Draw tightly around the target area. Write ID as letter + number (A1, B1).

**Replace mode**: for existing objects whose color will be changed.
Write `target_ref` describing the object (in Chinese, will be translated later).

**Add mode**: for empty regions where a new object will be inserted.
Check candidate objects from the list that DON'T exist in the image.

## target_ref Format (Replace)

**Always start with the color, then describe the object.**

### Type 1: Simple object — `{color} {object}`

```
red bicycle
white car
blue plastic glove
```

### Type 2: Sub-item — `{color} {item} on the {owner}`

```
blue jacket on the cyclist
green shorts on the man
orange life vest on the dog
```

### Type 3: Multi-color — `{color1}-and-{color2} {object}`

```
orange-and-white lifebuoy
black-and-white dog
```

## Add Mode Candidate Objects

Grouped by typical placement (visual grouping only, not a constraint):

| Group | Objects |
|-------|---------|
| Ground | bag, bucket, umbrella, bottle, box, bicycle, scooter, stroller, dog, cat |
| Table | cup, bowl, phone, flower |
| Wall | poster, sign, clock, flag |
| Water | boat, buoy, bird |
| Air | bird, balloon, kite, flag |

Check all objects that **do not already exist** in the image.

## Rules

1. **Color must be the first word(s)** in target_ref
2. **Use `on the`** for sub-items (not under/beside/with/in)
3. **One target per orange box**
4. **Add objects must not exist** in the original image
5. **Use V\* vocabulary**: cyclist, van, baby stroller, scooter, etc.

## How Questions Are Generated

| Type | Input | Question |
|------|-------|----------|
| Color | `red bicycle` | What color is the bicycle? |
| Color | `blue jacket on the cyclist` | What color is the jacket on the cyclist? |
| Position | 2 slots | Is the bicycle to the left or right of the car? |
| Position (fallback) | 2 slots, vertical | Is the bicycle above or below the car? |

- **Color**: strips color prefix, asks about the rest
- **Position**: uses object name only (no color), prefers left/right, falls back to above/below
