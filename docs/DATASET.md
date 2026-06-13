# Dataset Release Notes

The generated REKEY benchmark is intended to be released as a Hugging Face
dataset. The GitHub repository contains code, annotations, evaluation scripts,
and result logs; generated benchmark image artifacts are downloaded separately.

## Structure

Expected Hugging Face layout:

```text
benchmark/
  bench1/
    eval_dataset.jsonl
    eval_dataset_pos_nocolor.jsonl
    vstar_0000__bench1/
      artifacts/
        composite.jpg
        composite.png
        manifest.json
        plan.json
        sample.json
      overview.png
  bench2/
  bench3/
annotations/
  dynamic_vstar_slots_latest.jsonl
  vstar_relabel_latest_fixed.jsonl
dataset_manifest.json
README.md
```

Each `eval_dataset.jsonl` row includes the relative `image_path` for the item.
Use the row's benchmark directory as the base path.

## Download

```bash
python scripts/download_rekey_benchmark.py \
  --repo-id Xfgll/rekey-vstar-benchmark \
  --out data/rekey_benchmark
```

## Upload

The upload script checks for Git LFS pointer files before uploading:

```bash
git lfs pull -I "results/benchmark/**" -I "results/vlm_annotator/**"

python scripts/upload_rekey_benchmark.py \
  --repo-id Xfgll/rekey-vstar-benchmark \
  --multi-commits \
  --dry-run
```

Remove `--dry-run` to publish.

## License note

The code license is MIT. The benchmark dataset includes derived V*Bench/source
image content, so the dataset card uses `license: other` by default and points
users to the applicable upstream terms.
