"""Train a landmark sequence classifier (nearest-centroid cosine baseline)."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import pickle
from typing import Dict, List, Sequence, Tuple

import numpy as np

from landmark_features import (
    DEFAULT_SEQUENCE_LENGTH,
    cosine_similarity_matrix,
    mirror_sequence,
    sequence_to_feature_vector,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train landmark sequence classifier.")
    parser.add_argument(
        "--data-dir",
        default=str(Path(__file__).resolve().parents[1] / "ml" / "datasets" / "raw"),
        help="Directory containing raw JSON samples",
    )
    parser.add_argument(
        "--out-model",
        default=str(Path(__file__).resolve().parents[1] / "ml" / "models" / "landmark_classifier.pkl"),
        help="Output model artifact path",
    )
    parser.add_argument(
        "--out-report",
        default=str(Path(__file__).resolve().parents[1] / "ml" / "models" / "training_report.txt"),
        help="Output text report path",
    )
    parser.add_argument("--sequence-length", type=int, default=DEFAULT_SEQUENCE_LENGTH)
    parser.add_argument("--min-samples-per-class", type=int, default=8)
    parser.add_argument("--validation-split", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-augment", action="store_true", help="Disable mirror augmentation")
    parser.add_argument("--confidence-scale", type=float, default=6.0)
    return parser.parse_args()


def load_samples(data_dir: Path) -> List[dict]:
    samples: List[dict] = []
    if not data_dir.exists():
        return samples

    for path in sorted(data_dir.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["_file"] = str(path)
            samples.append(payload)
        except Exception:
            continue

    return samples


def build_feature_table(
    raw_samples: Sequence[dict],
    sequence_length: int,
    augment: bool,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, int], int]:
    features: List[np.ndarray] = []
    labels: List[str] = []
    class_counts: Dict[str, int] = defaultdict(int)
    skipped = 0

    for sample in raw_samples:
        label = str(sample.get("label", "")).strip()
        sequence = sample.get("landmarks")
        if not label or sequence is None:
            skipped += 1
            continue

        try:
            feat = sequence_to_feature_vector(sequence, target_length=sequence_length)
        except Exception:
            skipped += 1
            continue

        features.append(feat)
        labels.append(label)
        class_counts[label] += 1

        if augment:
            try:
                mirrored = mirror_sequence(sequence)
                mirrored_feat = sequence_to_feature_vector(mirrored, target_length=sequence_length)
                features.append(mirrored_feat)
                labels.append(label)
                class_counts[label] += 1
            except Exception:
                pass

    if not features:
        return np.zeros((0, 0), dtype=np.float32), np.array([], dtype=object), {}, skipped

    return np.vstack(features).astype(np.float32), np.asarray(labels, dtype=object), dict(class_counts), skipped


def filter_classes(
    features: np.ndarray,
    labels: np.ndarray,
    min_samples_per_class: int,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, int]]:
    counts = Counter(labels.tolist())
    keep_labels = {label for label, count in counts.items() if count >= min_samples_per_class}

    keep_mask = np.asarray([label in keep_labels for label in labels], dtype=bool)
    filtered_features = features[keep_mask]
    filtered_labels = labels[keep_mask]

    filtered_counts = Counter(filtered_labels.tolist())
    return filtered_features, filtered_labels, dict(filtered_counts)


def stratified_split(
    labels: np.ndarray,
    validation_split: float,
    seed: int,
) -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_idx: List[int] = []
    val_idx: List[int] = []

    unique_labels = sorted(set(labels.tolist()))
    for label in unique_labels:
        label_indices = np.where(labels == label)[0]
        rng.shuffle(label_indices)

        if len(label_indices) <= 1:
            train_idx.extend(label_indices.tolist())
            continue

        val_count = int(round(len(label_indices) * validation_split))
        val_count = max(1, val_count)
        val_count = min(val_count, len(label_indices) - 1)

        val_idx.extend(label_indices[:val_count].tolist())
        train_idx.extend(label_indices[val_count:].tolist())

    return np.asarray(train_idx, dtype=np.int64), np.asarray(val_idx, dtype=np.int64)


def train_centroids(features: np.ndarray, labels: np.ndarray) -> Tuple[List[str], np.ndarray]:
    class_names = sorted(set(labels.tolist()))
    centroids = []
    for class_name in class_names:
        class_features = features[labels == class_name]
        centroids.append(np.mean(class_features, axis=0))
    return class_names, np.vstack(centroids).astype(np.float32)


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=1, keepdims=True)


def predict(
    features: np.ndarray,
    class_names: Sequence[str],
    centroids: np.ndarray,
    confidence_scale: float,
) -> Tuple[np.ndarray, np.ndarray]:
    similarities = cosine_similarity_matrix(features, centroids)
    probabilities = softmax(similarities * confidence_scale)
    pred_indices = np.argmax(probabilities, axis=1)
    pred_labels = np.asarray([class_names[idx] for idx in pred_indices], dtype=object)
    pred_conf = probabilities[np.arange(len(probabilities)), pred_indices]
    return pred_labels, pred_conf


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, class_names: Sequence[str]) -> dict:
    total = len(y_true)
    correct = int(np.sum(y_true == y_pred))
    accuracy = float(correct / total) if total else 0.0

    per_class = {}
    f1_values = []

    for class_name in class_names:
        tp = int(np.sum((y_true == class_name) & (y_pred == class_name)))
        fp = int(np.sum((y_true != class_name) & (y_pred == class_name)))
        fn = int(np.sum((y_true == class_name) & (y_pred != class_name)))

        precision = float(tp / (tp + fp)) if (tp + fp) else 0.0
        recall = float(tp / (tp + fn)) if (tp + fn) else 0.0
        f1 = float((2 * precision * recall) / (precision + recall)) if (precision + recall) else 0.0

        per_class[class_name] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": int(np.sum(y_true == class_name)),
        }
        f1_values.append(f1)

    macro_f1 = float(np.mean(f1_values)) if f1_values else 0.0

    matrix = []
    for true_label in class_names:
        row = []
        for pred_label in class_names:
            row.append(int(np.sum((y_true == true_label) & (y_pred == pred_label))))
        matrix.append(row)

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "per_class": per_class,
        "confusion_matrix": {
            "labels": list(class_names),
            "matrix": matrix,
        },
        "samples": int(total),
    }


def write_report(path: Path, report_payload: dict) -> None:
    lines = []
    lines.append("Landmark Classifier Training Report")
    lines.append("=" * 40)
    lines.append(f"Created: {report_payload['created_at_utc']}")
    lines.append(f"Data dir: {report_payload['data_dir']}")
    lines.append(f"Sequence length: {report_payload['sequence_length']}")
    lines.append(f"Augmentation: {report_payload['augmentation']}")
    lines.append("")

    lines.append("Dataset")
    lines.append("-" * 40)
    lines.append(f"Raw samples loaded: {report_payload['raw_samples_loaded']}")
    lines.append(f"Invalid/skipped samples: {report_payload['skipped_samples']}")
    lines.append(f"Samples after filtering: {report_payload['filtered_samples']}")
    lines.append("Class counts:")
    for class_name, count in sorted(report_payload["class_counts"].items()):
        lines.append(f"  - {class_name}: {count}")
    lines.append("")

    train_metrics = report_payload["train_metrics"]
    val_metrics = report_payload["val_metrics"]

    lines.append("Train Metrics")
    lines.append("-" * 40)
    lines.append(f"Accuracy: {train_metrics['accuracy']:.4f}")
    lines.append(f"Macro F1: {train_metrics['macro_f1']:.4f}")
    lines.append("")

    lines.append("Validation Metrics")
    lines.append("-" * 40)
    lines.append(f"Accuracy: {val_metrics['accuracy']:.4f}")
    lines.append(f"Macro F1: {val_metrics['macro_f1']:.4f}")
    lines.append("")

    lines.append("Per-Class Validation Metrics")
    lines.append("-" * 40)
    for class_name, metrics in val_metrics["per_class"].items():
        lines.append(
            f"{class_name}: precision={metrics['precision']:.3f}, recall={metrics['recall']:.3f}, "
            f"f1={metrics['f1']:.3f}, support={metrics['support']}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    data_dir = Path(args.data_dir)
    model_path = Path(args.out_model)
    report_path = Path(args.out_report)
    sequence_length = args.sequence_length

    raw_samples = load_samples(data_dir)
    if not raw_samples:
        print(f"ERROR: No samples found in {data_dir}")
        return 1

    features, labels, class_counts, skipped = build_feature_table(
        raw_samples,
        sequence_length=sequence_length,
        augment=not args.no_augment,
    )

    if len(labels) == 0:
        print("ERROR: No valid samples after preprocessing.")
        return 1

    features, labels, filtered_counts = filter_classes(
        features,
        labels,
        min_samples_per_class=args.min_samples_per_class,
    )

    if len(set(labels.tolist())) < 2:
        print("ERROR: Need at least two classes after filtering to train classifier.")
        return 1

    train_idx, val_idx = stratified_split(
        labels,
        validation_split=args.validation_split,
        seed=args.seed,
    )

    train_x = features[train_idx]
    train_y = labels[train_idx]
    val_x = features[val_idx]
    val_y = labels[val_idx]

    class_names, centroids = train_centroids(train_x, train_y)

    train_pred, train_conf = predict(
        train_x,
        class_names=class_names,
        centroids=centroids,
        confidence_scale=args.confidence_scale,
    )
    val_pred, val_conf = predict(
        val_x,
        class_names=class_names,
        centroids=centroids,
        confidence_scale=args.confidence_scale,
    )

    train_metrics = compute_metrics(train_y, train_pred, class_names)
    val_metrics = compute_metrics(val_y, val_pred, class_names)

    artifact = {
        "version": "1.0.0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "sequence_length": int(sequence_length),
        "feature_dim": int(train_x.shape[1]),
        "labels": class_names,
        "centroids": centroids.astype(np.float32),
        "confidence_scale": float(args.confidence_scale),
        "min_confidence": 0.58,
        "class_counts": filtered_counts,
        "train_metrics": train_metrics,
        "val_metrics": val_metrics,
        "pipeline": "wrist_center + palm_scale + temporal_resample + velocity + nearest_centroid_cosine",
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as handle:
        pickle.dump(artifact, handle)

    report_payload = {
        "created_at_utc": artifact["created_at_utc"],
        "data_dir": str(data_dir),
        "sequence_length": sequence_length,
        "augmentation": not args.no_augment,
        "raw_samples_loaded": len(raw_samples),
        "skipped_samples": skipped,
        "filtered_samples": int(len(labels)),
        "class_counts": filtered_counts,
        "train_metrics": train_metrics,
        "val_metrics": val_metrics,
    }

    write_report(report_path, report_payload)

    metrics_json_path = report_path.with_suffix(".json")
    metrics_json_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

    print(f"Model saved to: {model_path}")
    print(f"Report saved to: {report_path}")
    print(f"Validation accuracy: {val_metrics['accuracy']:.4f}")
    print(f"Validation macro F1: {val_metrics['macro_f1']:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
