#!/usr/bin/env python3
"""Download the released REKEY benchmark from Hugging Face."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from huggingface_hub import snapshot_download


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a REKEY benchmark dataset repository.")
    parser.add_argument(
        "--repo-id",
        default=os.environ.get("REKEY_DATASET_REPO"),
        help="Hugging Face dataset repo ID, e.g. org/rekey-vstar-benchmark.",
    )
    parser.add_argument("--revision", default=None)
    parser.add_argument("--out", type=Path, default=Path("data/rekey_benchmark"))
    parser.add_argument(
        "--include-eval-results",
        action="store_true",
        help="Also download released evaluation logs if the dataset repo contains them.",
    )
    args = parser.parse_args()

    if not args.repo_id:
        raise SystemExit("Pass --repo-id or set REKEY_DATASET_REPO.")

    allow_patterns = [
        "README.md",
        "dataset_manifest.json",
        "benchmark/**",
        "annotations/**",
    ]
    if args.include_eval_results:
        allow_patterns.append("eval_results/**")

    local_dir = snapshot_download(
        repo_id=args.repo_id,
        repo_type="dataset",
        revision=args.revision,
        local_dir=args.out,
        allow_patterns=allow_patterns,
    )
    print(f"Downloaded {args.repo_id} -> {local_dir}")


if __name__ == "__main__":
    main()

