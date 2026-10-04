# REKEY handoff branch

This branch is a collaboration handoff built from the latest remote
`origin/dynamic-vstar-pipeline` commit:

- base commit: `d7cd6608d62cd75aef95ed9b23262b931e4049f8`
- handoff date: 2026-09-30

It adds the internal project guides, the latest local analysis scripts, small
annotation and contamination-audit records, and the curated showcase example.
It intentionally does not re-add the large generated benchmark, raw/external
datasets, experiment output trees, paper workspace, Label Studio runtime
database, credentials, caches, or local screenshots.

## Access and clone

The GitHub repository is private. Add the recipient's GitHub account as a
collaborator before cloning.

```bash
git clone --branch handoff-20260930 --single-branch \
  https://github.com/Xxxxxsun/vstar_pro.git
cd vstar_pro
```

For the benchmark download only, create a minimal environment with
`huggingface_hub`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip huggingface_hub
```

Install the complete project requirements separately when running the project:

```bash
python -m pip install -r requirements.txt
```

## Download the released benchmark

The released benchmark is hosted separately on Hugging Face:

`https://huggingface.co/datasets/Xfgll/rekey-vstar-benchmark`

Download the exact handoff release with:

```bash
python scripts/download_rekey_benchmark.py \
  --repo-id Xfgll/rekey-vstar-benchmark \
  --revision b08d1a8e4085dec60973a46670ba0e947e990c7c \
  --out data/rekey_benchmark
```

Expected layout:

```text
data/rekey_benchmark/
├── annotations/
├── benchmark/
│   ├── bench1/
│   ├── bench2/
│   ├── bench3/
│   └── bench_vlm_add/
├── README.md
└── dataset_manifest.json
```

The Hugging Face repository is about 12 GB. Reserve additional working space
for caches and downstream outputs.

Historical commits before the public-release cleanup referenced benchmark
images through Git LFS. Those paths are not part of this branch's current tree;
the Hugging Face release is the supported distribution source.

## Scope boundary

Cloning this branch and downloading the Hugging Face release provides the
handoff code, released annotations, and four released benchmark splits. It does
not provide the local paper workspace, raw/external source snapshots, complete
experiment output trees, Label Studio runtime database, credentials, caches, or
local screenshots. Those internal artifacts are not distributed by this
handoff.
