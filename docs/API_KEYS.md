# API Keys and Providers

REKEY has two API-backed stages.

## Image editing

The default image-edit endpoint is OpenAI:

```text
https://api.openai.com/v1/images/edits
```

Set `OPENAI_API_KEY` in your shell or `.env`.

Optional overrides:

```bash
export DYNAMIC_VSTAR_IMAGE_API_URL="https://api.openai.com/v1/images/edits"
export DYNAMIC_VSTAR_IMAGE_MODEL="gpt-image-2"
export DYNAMIC_VSTAR_IMAGE_FIELD="image[]"
```

Use `--fake-generator` for local dry runs without an image API.

## Planner

The default planner is rule-based and offline. To use an OpenRouter-backed LLM
planner:

```bash
DYNAMIC_VSTAR_PLANNER_MODEL=openai/gpt-5.5

python scripts/run_dynamic_vstar_pipeline.py \
  --annotations data/annotations/dynamic_vstar_slots_latest.jsonl \
  --out outputs/dynamic_vstar \
  --run-id llm_planner_smoke \
  --planner openrouter \
  --planner-fallback \
  --limit 3
```

## Evaluation

`scripts/run_dynamic_eval.py` calls OpenRouter. Set `OPENROUTER_API_KEY` in
your shell or `.env`.

It writes model outputs incrementally to JSONL, so interrupted runs can be
resumed by reusing the same output path.
