from __future__ import annotations

import argparse
from pathlib import Path

from backend.training.pipeline import TrainingConfig, train_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a local sign-language classifier.")
    parser.add_argument(
        "--dataset-root",
        default="backend/datasets/sign_language_images",
        help="Dataset root with train/val/test folders.",
    )
    parser.add_argument(
        "--artifact-dir",
        default="backend/artifacts/models/local_sign_model",
        help="Directory where model artifacts will be saved.",
    )
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    args = parser.parse_args()

    result = train_model(
        TrainingConfig(
            dataset_root=Path(args.dataset_root),
            artifact_dir=Path(args.artifact_dir),
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
        )
    )
    print(result)


if __name__ == "__main__":
    main()

