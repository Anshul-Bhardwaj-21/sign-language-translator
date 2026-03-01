"""Evaluation script for trained models."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

from model import create_model
from dataset_loader import LandmarkDataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def evaluate_model(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    classes: list
) -> dict:
    """Evaluate model and return metrics."""
    model.eval()
    
    all_predictions = []
    all_labels = []
    all_latencies = []
    
    with torch.no_grad():
        for sequences, labels in dataloader:
            sequences = sequences.to(device)
            labels = labels.to(device)
            
            # Measure inference latency
            start_time = time.perf_counter()
            outputs = model(sequences)
            latency = (time.perf_counter() - start_time) * 1000  # ms
            
            _, predicted = outputs.max(1)
            
            all_predictions.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_latencies.append(latency / len(sequences))  # Per-sample latency
    
    # Calculate metrics
    accuracy = 100.0 * np.mean(np.array(all_predictions) == np.array(all_labels))
    avg_latency = np.mean(all_latencies)
    
    # Confusion matrix
    cm = confusion_matrix(all_labels, all_predictions)
    
    # Classification report
    report = classification_report(
        all_labels,
        all_predictions,
        target_names=classes,
        output_dict=True
    )
    
    return {
        'accuracy': accuracy,
        'avg_latency_ms': avg_latency,
        'confusion_matrix': cm,
        'classification_report': report,
        'predictions': all_predictions,
        'labels': all_labels
    }


def plot_confusion_matrix(cm: np.ndarray, classes: list, output_path: str):
    """Plot and save confusion matrix."""
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        cm,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=classes,
        yticklabels=classes
    )
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Confusion matrix saved to {output_path}")


def save_metrics_report(metrics: dict, classes: list, output_path: str):
    """Save detailed metrics report."""
    with open(output_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("MODEL EVALUATION REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Overall Accuracy: {metrics['accuracy']:.2f}%\n")
        f.write(f"Average Latency: {metrics['avg_latency_ms']:.2f} ms\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("PER-CLASS METRICS\n")
        f.write("=" * 80 + "\n\n")
        
        report = metrics['classification_report']
        
        f.write(f"{'Class':<15} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}\n")
        f.write("-" * 80 + "\n")
        
        for class_name in classes:
            if class_name in report:
                class_metrics = report[class_name]
                f.write(
                    f"{class_name:<15} "
                    f"{class_metrics['precision']:<12.3f} "
                    f"{class_metrics['recall']:<12.3f} "
                    f"{class_metrics['f1-score']:<12.3f} "
                    f"{int(class_metrics['support']):<10}\n"
                )
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("AGGREGATE METRICS\n")
        f.write("=" * 80 + "\n\n")
        
        for avg_type in ['macro avg', 'weighted avg']:
            if avg_type in report:
                avg_metrics = report[avg_type]
                f.write(f"{avg_type}:\n")
                f.write(f"  Precision: {avg_metrics['precision']:.3f}\n")
                f.write(f"  Recall: {avg_metrics['recall']:.3f}\n")
                f.write(f"  F1-Score: {avg_metrics['f1-score']:.3f}\n\n")
    
    logger.info(f"Metrics report saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate trained model")
    parser.add_argument("--model-path", type=str, required=True,
                        help="Path to trained model checkpoint")
    parser.add_argument("--data-dir", type=str, required=True,
                        help="Path to test dataset")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--output-dir", type=str, default="ml/evaluation",
                        help="Directory to save evaluation results")
    parser.add_argument("--device", type=str, default="auto")
    
    args = parser.parse_args()
    
    # Device selection
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    
    logger.info(f"Using device: {device}")
    
    # Load model
    logger.info(f"Loading model from {args.model_path}")
    checkpoint = torch.load(args.model_path, map_location=device)
    
    classes = checkpoint['classes']
    sequence_length = checkpoint['sequence_length']
    model_type = checkpoint.get('model_type', 'conv_lstm')
    hidden_dim = checkpoint.get('hidden_dim', 128)
    
    model = create_model(
        model_type=model_type,
        input_features=63,
        num_classes=len(classes),
        hidden_dim=hidden_dim
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()
    
    logger.info(f"Model loaded: {len(classes)} classes")
    
    # Load test dataset
    logger.info(f"Loading test dataset from {args.data_dir}")
    test_dataset = LandmarkDataset(
        data_dir=args.data_dir,
        sequence_length=sequence_length,
        augment=False,
        normalize=True
    )
    
    if len(test_dataset) == 0:
        logger.error("No test data found")
        return
    
    logger.info(f"Test dataset size: {len(test_dataset)}")
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0
    )
    
    # Evaluate
    logger.info("Evaluating model...")
    metrics = evaluate_model(model, test_loader, device, classes)
    
    # Print results
    logger.info(f"\nAccuracy: {metrics['accuracy']:.2f}%")
    logger.info(f"Average Latency: {metrics['avg_latency_ms']:.2f} ms")
    
    # Save results
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Save confusion matrix
    cm_path = os.path.join(args.output_dir, "confusion_matrix.png")
    plot_confusion_matrix(metrics['confusion_matrix'], classes, cm_path)
    
    # Save metrics report
    report_path = os.path.join(args.output_dir, "evaluation_report.txt")
    save_metrics_report(metrics, classes, report_path)
    
    logger.info(f"\n✓ Evaluation complete! Results saved to {args.output_dir}")


if __name__ == "__main__":
    main()
