# Quickstart

## 1. Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## 2. Run an offline smoke generation

This uses the deterministic fake image generator and does not need API keys:

```bash
python scripts/run_dynamic_vstar_pipeline.py \
  --annotations data/annotations/dynamic_vstar_slots_latest.jsonl \
  --out outputs/dynamic_vstar \
  --run-id smoke \
  --limit 3 \
  --fake-generator
```

## 3. Run real image regeneration

Set `OPENAI_API_KEY` in your shell or `.env` first.

```bash
python scripts/run_dynamic_vstar_pipeline.py \
  --annotations data/annotations/dynamic_vstar_slots_latest.jsonl \
  --out outputs/dynamic_vstar \
  --run-id rekey_seed_1 \
  --limit 10
```

## 4. Build the evaluation file

```bash
python scripts/build_eval_dataset.py \
  --bench-dir outputs/dynamic_vstar \
  --out outputs/dynamic_vstar/eval_dataset.jsonl
```

## 5. Evaluate a model

Set `OPENROUTER_API_KEY` in your shell or `.env` first.

```bash
python scripts/run_dynamic_eval.py \
  --eval-dataset outputs/dynamic_vstar/eval_dataset.jsonl \
  --out results/qwen36plus_smoke.jsonl \
  --model qwen/qwen3.6-plus \
  --limit 3
```
