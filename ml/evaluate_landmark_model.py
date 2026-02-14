"""Evaluate trained landmark classifier on labeled JSON samples."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import pickle
from typing import Dict, List, Sequence, Tuple

import numpy as np

from landmark_features import cosine_similarity_matrix, sequence_to_feature_vector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate landmark classifier.")
    parser.add_argument(
        "--model-path",
        default=str(Path(__file__).resolve().parents[1] / "ml" / "models" / "landmark_classifier.pkl"),
    )
    parser.add_argument(
        "--data-dir",
        default=str(Path(__file__).resolve().parents[1] / "ml" / "datasets" / "raw"),
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parents[1] / "ml" / "models" / "evaluation_report.txt"),
    )
    return parser.parse_args()


def load_model(path: Path) -> dict:
    with path.open("rb") as handle:
        artifact = pickle.load(handle)
    return artifact


def load_dataset(data_dir: Path, sequence_length: int) -> Tuple[np.ndarray, np.ndarray, int]:
    features: List[np.ndarray] = []
    labels: List[str] = []
    skipped = 0

    for file_path in sorted(data_dir.rglob("*.json")):
        try:
            sample = json.loads(file_path.read_text(encoding="utf-8"))
            label = str(sample.get("label", "")).strip()
            sequence = sample.get("landmarks")
            if not label or sequence is None:
                skipped += 1
                continue
            feature = sequence_to_feature_vector(sequence, target_length=sequence_length)
            features.append(feature)
            labels.append(label)
        except Exception:
            skipped += 1

    if not features:
        return np.zeros((0, 0), dtype=np.float32), np.array([], dtype=object), skipped

    return np.vstack(features).astype(np.float32), np.asarray(labels, dtype=object), skipped


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=1, keepdims=True)


def predict(features: np.ndarray, labels: Sequence[str], centroids: np.ndarray, confidence_scale: float) -> Tuple[np.ndarray, np.ndarray]:
    similarities = cosine_similarity_matrix(features, centroids)
    probabilities = softmax(similarities * confidence_scale)
    indices = np.argmax(probabilities, axis=1)
    pred_labels = np.asarray([labels[idx] for idx in indices], dtype=object)
    confidences = probabilities[np.arange(len(probabilities)), indices]
    return pred_labels, confidences


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, label_list: Sequence[str]) -> dict:
    accuracy = float(np.mean(y_true == y_pred)) if len(y_true) else 0.0

    per_class = {}
    f1_scores: List[float] = []

    for label in label_list:
        tp = int(np.sum((y_true == label) & (y_pred == label)))
        fp = int(np.sum((y_true != label) & (y_pred == label)))
        fn = int(np.sum((y_true == label) & (y_pred != label)))

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0

        per_class[label] = {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "support": int(np.sum(y_true == label)),
        }
        f1_scores.append(float(f1))

    macro_f1 = float(np.mean(f1_scores)) if f1_scores else 0.0

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "per_class": per_class,
        "samples": int(len(y_true)),
    }


def write_report(path: Path, payload: dict) -> None:
    lines = []
    lines.append("Landmark Classifier Evaluation")
    lines.append("=" * 36)
    lines.append(f"Model path: {payload['model_path']}")
    lines.append(f"Data dir: {payload['data_dir']}")
    lines.append(f"Samples evaluated: {payload['metrics']['samples']}")
    lines.append(f"Samples skipped: {payload['skipped']}")
    lines.append("")
    lines.append(f"Accuracy: {payload['metrics']['accuracy']:.4f}")
    lines.append(f"Macro F1: {payload['metrics']['macro_f1']:.4f}")
    lines.append("")

    lines.append("Per-class metrics")
    lines.append("-" * 36)
    for label, row in payload["metrics"]["per_class"].items():
        lines.append(
            f"{label}: precision={row['precision']:.3f}, recall={row['recall']:.3f}, "
            f"f1={row['f1']:.3f}, support={row['support']}"
        )

    lines.append("")
    lines.append("Prediction counts")
    lines.append("-" * 36)
    for label, count in payload["prediction_counts"].items():
        lines.append(f"{label}: {count}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.with_suffix(".json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()

    model_path = Path(args.model_path)
    data_dir = Path(args.data_dir)
    out_path = Path(args.output)

    if not model_path.exists():
        print(f"ERROR: Model not found: {model_path}")
        return 1

    artifact = load_model(model_path)
    sequence_length = int(artifact.get("sequence_length", 24))
    label_list = artifact.get("labels", [])
    centroids = np.asarray(artifact.get("centroids", []), dtype=np.float32)
    confidence_scale = float(artifact.get("confidence_scale", 6.0))

    if centroids.size == 0 or not label_list:
        print("ERROR: Invalid model artifact (missing centroids/labels).")
        return 1

    features, labels, skipped = load_dataset(data_dir, sequence_length=sequence_length)
    if len(labels) == 0:
        print("ERROR: No valid evaluation samples found.")
        return 1

    preds, conf = predict(features, labels=label_list, centroids=centroids, confidence_scale=confidence_scale)
    metrics = compute_metrics(labels, preds, label_list)

    payload = {
        "model_path": str(model_path),
        "data_dir": str(data_dir),
        "sequence_length": sequence_length,
        "skipped": skipped,
        "metrics": metrics,
        "prediction_counts": dict(Counter(preds.tolist())),
        "average_confidence": float(np.mean(conf)) if len(conf) else 0.0,
    }

    write_report(out_path, payload)

    print(f"Evaluation report written to: {out_path}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Macro F1: {metrics['macro_f1']:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
