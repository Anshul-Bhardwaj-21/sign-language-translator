from __future__ import annotations

import argparse
from pathlib import Path

from backend.training.pipeline import evaluate_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a local sign-language classifier.")
    parser.add_argument(
        "--dataset-root",
        default="backend/datasets/sign_language_images",
        help="Dataset root with train/val/test folders.",
    )
    parser.add_argument(
        "--artifact-dir",
        default="backend/artifacts/models/local_sign_model",
        help="Directory containing model.pt, labels.json, and metadata.json.",
    )
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    result = evaluate_model(
        dataset_root=Path(args.dataset_root),
        artifact_dir=Path(args.artifact_dir),
        batch_size=args.batch_size,
    )
    print(result)


if __name__ == "__main__":
    main()

