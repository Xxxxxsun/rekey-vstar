#!/usr/bin/env python3
"""Publish the REKEY benchmark artifacts to a Hugging Face dataset repo."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi


ROOT = Path(__file__).resolve().parents[1]
LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"


def is_lfs_pointer(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        return path.read_bytes()[: len(LFS_POINTER_PREFIX)] == LFS_POINTER_PREFIX
    except OSError:
        return False


def iter_files(path: Path):
    if path.is_file():
        yield path
        return
    for child in path.rglob("*"):
        if child.is_file():
            yield child


def copy_path(src: Path, dst: Path) -> None:
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def write_dataset_card(path: Path, repo_id: str, license_name: str, manifest: dict) -> None:
    benchmark_list = "\n".join(
        f"- `benchmark/{name}`: {manifest['eval_rows'].get(name, 0)} evaluation rows."
        for name in manifest["benchmark_seeds"]
    )
    card = f"""---
license: {license_name}
task_categories:
- visual-question-answering
language:
- en
pretty_name: REKEY V* benchmark
---

# REKEY V* Benchmark

This dataset contains regenerated V*Bench-style evaluation instances produced by
REKEY, a metadata-grounded visual-key regeneration protocol for
contamination-resistant VQA evaluation.

## Contents

{benchmark_list}

Each benchmark split contains `eval_dataset.jsonl`, optional
`eval_dataset_pos_nocolor.jsonl`, generated images, plans, samples, and
manifests.
- `annotations/dynamic_vstar_slots_latest.jsonl`: human-curated edit slots used
  by the regeneration pipeline.
- `annotations/vstar_relabel_latest_fixed.jsonl`: fixed human relabel snapshot
  used for contamination controls.
- `dataset_manifest.json`: counts and release metadata.

## Dataset Schema

Each `eval_dataset.jsonl` row contains:

- `image_id`, `question_id`, `category`, `question_type`
- `question`
- `options` and `options_dict`
- `correct_label`, `answer`
- `image_path`, relative to the benchmark seed directory

## License and Source Data

The code in the GitHub repository is released under MIT. This dataset includes
derived images and metadata based on V*Bench source items; users are responsible
for complying with the original V*Bench and source-image terms.

## Citation

If you use this dataset, cite the REKEY paper:

```bibtex
@misc{{rekey2026,
  title={{REKEY: Metadata-Grounded Visual-Key Regeneration for Contamination-Resistant VQA Evaluation}},
  year={{2026}}
}}
```

## Release Manifest

```json
{json.dumps(manifest, indent=2)}
```
"""
    path.write_text(card, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload REKEY benchmark artifacts to Hugging Face.")
    parser.add_argument("--repo-id", default=os.environ.get("REKEY_DATASET_REPO"), help="HF dataset repo ID.")
    parser.add_argument("--token", default=os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN"))
    parser.add_argument("--benchmark-dir", type=Path, default=ROOT / "results" / "benchmark")
    parser.add_argument(
        "--extra-benchmark-dir",
        action="append",
        type=Path,
        default=None,
        help=(
            "Additional benchmark split directory to publish under benchmark/<dir-name>. "
            "Defaults to results/vlm_annotator/bench_vlm_add when present."
        ),
    )
    parser.add_argument("--annotations-dir", type=Path, default=ROOT / "data" / "annotations")
    parser.add_argument("--include-eval-results", action="store_true")
    parser.add_argument("--private", action="store_true", help="Create/update the dataset as private.")
    parser.add_argument("--license", default="other")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--multi-commits",
        action="store_true",
        help="Upload in multiple commits to avoid expiring large LFS upload URLs.",
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=ROOT / "hf_dataset_export",
        help="Directory used for --dry-run exports.",
    )
    parser.add_argument(
        "--allow-lfs-pointers",
        action="store_true",
        help="Allow uploading Git LFS pointer files. This is almost never what you want.",
    )
    args = parser.parse_args()

    if not args.repo_id:
        raise SystemExit("Pass --repo-id or set REKEY_DATASET_REPO.")
    if not args.dry_run and not args.token:
        raise SystemExit("Set HF_TOKEN, run `huggingface-cli login`, or pass --token.")
    if not args.benchmark_dir.exists():
        raise SystemExit(f"benchmark directory not found: {args.benchmark_dir}")

    default_extra = ROOT / "results" / "vlm_annotator" / "bench_vlm_add"
    extra_benchmark_dirs = args.extra_benchmark_dir
    if extra_benchmark_dirs is None:
        extra_benchmark_dirs = [default_extra] if default_extra.exists() else []
    else:
        extra_benchmark_dirs = [path for path in extra_benchmark_dirs if path.exists()]

    sources = [args.benchmark_dir]
    sources.extend(extra_benchmark_dirs)
    annotation_files = [
        args.annotations_dir / "dynamic_vstar_slots_latest.jsonl",
        args.annotations_dir / "vstar_relabel_latest_fixed.jsonl",
        args.annotations_dir / "vstar_relabel_latest_fixed_README.md",
        args.annotations_dir / "vstar_relabel_latest_fixed_items.jsonl",
    ]
    sources.extend(path for path in annotation_files if path.exists())
    if args.include_eval_results:
        for rel in ("results/dynamic_eval", "results/agentic_eval", "results/vlm_annotator"):
            path = ROOT / rel
            if path.exists():
                sources.append(path)

    pointer_files = [path for source in sources for path in iter_files(source) if is_lfs_pointer(path)]
    if pointer_files and not args.allow_lfs_pointers:
        examples = "\n".join(str(p.relative_to(ROOT)) for p in pointer_files[:10])
        raise SystemExit(
            "Refusing to upload Git LFS pointer files. Fetch the real files first, for example:\n"
            "  git lfs pull -I 'results/benchmark/**' -I 'results/vlm_annotator/**'\n\n"
            f"Examples:\n{examples}"
        )

    benchmark_splits = sorted(p for p in args.benchmark_dir.iterdir() if p.is_dir())
    benchmark_splits.extend(extra_benchmark_dirs)
    manifest = {
        "repo_id": args.repo_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_seeds": [path.name for path in benchmark_splits],
        "eval_rows": {
            split.name: count_jsonl(split / "eval_dataset.jsonl")
            for split in benchmark_splits
        },
        "source_files": [display_path(path) for path in sources],
    }

    def prepare_export(export_root: Path) -> None:
        if export_root.exists():
            shutil.rmtree(export_root)
        export_root.mkdir(parents=True)
        copy_path(args.benchmark_dir, export_root / "benchmark")
        for path in extra_benchmark_dirs:
            copy_path(path, export_root / "benchmark" / path.name)
        annotations_out = export_root / "annotations"
        for path in annotation_files:
            if path.exists():
                copy_path(path, annotations_out / path.name)
        if args.include_eval_results:
            eval_out = export_root / "eval_results"
            for rel in ("dynamic_eval", "agentic_eval", "vlm_annotator"):
                path = ROOT / "results" / rel
                if path.exists():
                    copy_path(path, eval_out / rel)

        (export_root / "dataset_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_dataset_card(export_root / "README.md", args.repo_id, args.license, manifest)

    if args.dry_run:
        prepare_export(args.export_dir)
        print(f"Prepared dataset export at {args.export_dir}")
        print(json.dumps(manifest, indent=2))
        return

    with tempfile.TemporaryDirectory(prefix="rekey_hf_") as tmp:
        export_root = Path(tmp)
        prepare_export(export_root)

        api = HfApi(token=args.token)
        api.create_repo(repo_id=args.repo_id, repo_type="dataset", private=args.private, exist_ok=True)
        api.upload_folder(
            repo_id=args.repo_id,
            repo_type="dataset",
            folder_path=export_root,
            commit_message="Upload REKEY benchmark release",
            multi_commits=args.multi_commits,
            multi_commits_verbose=args.multi_commits,
        )
        visibility = "private" if args.private else "public"
        print(f"Uploaded {args.repo_id} as a {visibility} Hugging Face dataset.")


if __name__ == "__main__":
    main()
