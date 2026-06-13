# REKEY

Metadata-grounded visual-key regeneration for contamination-resistant VQA evaluation.

REKEY refreshes a VQA benchmark by regenerating the small answer-bearing visual detail
instead of replacing the whole image-question pair. Human annotations mark where a
new visual key can remain natural and non-obvious; the pipeline samples new visual
content, edits the local region, and derives the answer from the same construction
record.

This is the code release for:

> REKEY: Metadata-Grounded Visual-Key Regeneration for Contamination-Resistant VQA Evaluation

## What is included

- `dynamic_vstar/`: REKEY generation library.
- `scripts/run_dynamic_vstar_pipeline.py`: generate refreshed V*Bench-style items.
- `scripts/build_eval_dataset.py`: build `eval_dataset.jsonl` from generated items.
- `scripts/run_dynamic_eval.py`: run VLM evaluation through OpenRouter.
- `scripts/compute_tables.py`: recompute paper tables from released result logs.
- `data/annotations/dynamic_vstar_slots_latest.jsonl`: human-curated edit slots.
- `data/annotations/vstar_relabel_latest_fixed.jsonl`: fixed human relabel snapshot.

Generated benchmark images are released through Hugging Face, not stored directly in
the GitHub code repository.

## Install

```bash
git clone https://github.com/Xxxxxsun/rekey-vstar.git
cd rekey-vstar

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Copy the example environment file if you plan to call APIs, then fill in only
the keys you need:

```bash
cp .env.example .env
```

`OPENAI_API_KEY` enables image regeneration, and `OPENROUTER_API_KEY` enables
model evaluation through OpenRouter.

## Use the released benchmark

Download the released Hugging Face dataset:

```bash
python scripts/download_rekey_benchmark.py \
  --repo-id Xfgll/rekey-vstar-benchmark \
  --out data/rekey_benchmark
```

Run a VLM through OpenRouter:

```bash
python scripts/run_dynamic_eval.py \
  --eval-dataset data/rekey_benchmark/benchmark/bench1/eval_dataset.jsonl \
  --out results/my_model_bench1.jsonl \
  --model qwen/qwen3.6-plus \
  --concurrency 4
```

## Generate fresh benchmark instances

Dry run without external image generation:

```bash
python scripts/run_dynamic_vstar_pipeline.py \
  --annotations data/annotations/dynamic_vstar_slots_latest.jsonl \
  --out outputs/dynamic_vstar \
  --run-id smoke \
  --limit 3 \
  --fake-generator
```

Generate with OpenAI image edits:

```bash
python scripts/run_dynamic_vstar_pipeline.py \
  --annotations data/annotations/dynamic_vstar_slots_latest.jsonl \
  --out outputs/dynamic_vstar \
  --run-id rekey_seed_1 \
  --limit 10
```

Build an evaluation JSONL from a generated run:

```bash
python scripts/build_eval_dataset.py \
  --bench-dir outputs/dynamic_vstar \
  --out outputs/dynamic_vstar/eval_dataset.jsonl
```

The pipeline fetches the V*Bench parquet from `lmms-lab/vstar-bench` if
`data/raw/test-00000-of-00001.parquet` is not present locally.

## Reproduce paper tables

```bash
python scripts/compute_tables.py
```

The checked-in result logs under `results/` are enough to recompute the reported
tables. Regenerated benchmark image artifacts should be downloaded from Hugging
Face when needed.

## Publish the benchmark to Hugging Face

The upload helper refuses to upload Git LFS pointer files. Fetch the real image
files before publishing:

```bash
git lfs pull -I "results/benchmark/**" -I "results/vlm_annotator/**"

python scripts/upload_rekey_benchmark.py \
  --repo-id Xfgll/rekey-vstar-benchmark \
  --multi-commits
```

Use `--dry-run` first to inspect the export manifest.

## Documentation

- [Quickstart](docs/QUICKSTART.md)
- [API keys and providers](docs/API_KEYS.md)
- [Dataset release notes](docs/DATASET.md)
- [Release checklist](docs/RELEASE.md)

## License

Code is released under the MIT license. Dataset artifacts include derived
V*Bench/source-image content and should be used under the applicable upstream
dataset terms.
