# Release Checklist

Use this checklist before switching the GitHub repository to public.

1. Run tests:

```bash
pytest
```

2. Run a local smoke generation:

```bash
python scripts/run_dynamic_vstar_pipeline.py \
  --annotations data/annotations/dynamic_vstar_slots_latest.jsonl \
  --out outputs/dynamic_vstar \
  --run-id release_smoke \
  --limit 2 \
  --fake-generator
```

3. Check for secrets in tracked files:

```bash
git grep -n -I -E 'sk-|OPENAI_API_KEY[=]|OPENROUTER_API_KEY[=]|HF_TOKEN[=]|Bearer [A-Za-z0-9_-]+' -- .
```

4. Confirm large/generated artifacts are not tracked:

```bash
git ls-files results/benchmark data/raw outputs
```

5. Publish the benchmark dataset to Hugging Face:

```bash
git lfs pull -I "results/benchmark/**" -I "results/vlm_annotator/**"
python scripts/upload_rekey_benchmark.py \
  --repo-id Xfgll/rekey-vstar-benchmark \
  --multi-commits \
  --dry-run
```

6. Update `README.md`, `.env.example`, and `CITATION.cff` with the final GitHub
and Hugging Face URLs.

7. Make the GitHub repository public.
