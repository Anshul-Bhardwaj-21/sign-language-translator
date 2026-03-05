#!/usr/bin/env python3
"""
Sign Language Model Evaluation Script

This script implements comprehensive model evaluation with the following metrics:

1. Overall test accuracy
2. Per-class precision, recall, F1 scores
3. Confusion matrix visualization
4. Top 5 most confused gesture pairs
5. Inference latency measurement
6. Model size calculation
7. Evaluation metrics saved to JSON

Requirements: 30.9, 31.1, 31.2, 31.3, 31.4, 31.5, 31.8
Phase: MVP

Usage:
    # Evaluate best model checkpoint
    python evaluate_model.py
    
    # Evaluate specific checkpoint
    python evaluate_model.py --checkpoint checkpoints/checkpoint_epoch_50.pth
    
    # Save results to custom directory
    python evaluate_model.py --output-dir evaluation_results

Author: AI-Powered Meeting Platform Team
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)
from torch.utils.data import DataLoader

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from models.sign_language_model import CNNLSTMSignLanguageModel
from models.train_model import SignLanguageDataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Comprehensive model evaluation class.
    
    Calculates various metrics and generates visualizations for model performance
    assessment.
    
    Args:
        model: Trained PyTorch model
        test_loader: DataLoader for test data
        device: Device to run evaluation on ('cuda' or 'cpu')
        class_names: List of class names for visualization
    
    Requirements:
        - 31.1: Calculates overall accuracy on held-out test set
        - 31.2: Calculates per-class F1 scores to handle class imbalance
        - 31.3: Generates confusion matrix visualization
        - 31.4: Identifies top 5 most confused gesture pairs
        - 31.5: Calculates average inference latency
        - 31.8: Saves all evaluation metrics in JSON format
    """
    
    def __init__(
        self,
        model: nn.Module,
        test_loader: DataLoader,
        device: str,
        class_names: List[str]
    ):
        self.model = model
        self.test_loader = test_loader
        self.device = device
        self.class_names = class_names
        self.num_classes = len(class_names)
        
        # Results storage
        self.predictions = []
        self.ground_truth = []
        self.inference_times = []
        self.metrics = {}
    
    def evaluate(self) -> Dict:
        """
        Run complete evaluation pipeline.
        
        Returns:
            Dictionary containing all evaluation metrics
        
        Requirements:
            - 31.1: Overall test accuracy
            - 31.2: Per-class precision, recall, F1 scores
            - 31.5: Average inference latency
        """
        logger.info("="*60)
        logger.info("Starting Model Evaluation")
        logger.info("="*60)
        
        # Set model to evaluation mode
        self.model.eval()
        
        # Run inference on test set
        logger.info("Running inference on test set...")
        self._run_inference()
        
        # Calculate metrics
        logger.info("Calculating metrics...")
        self._calculate_overall_accuracy()
        self._calculate_per_class_metrics()
        self._calculate_inference_latency()
        self._calculate_model_size()
        
        # Generate confusion matrix
        logger.info("Generating confusion matrix...")
        self._generate_confusion_matrix()
        
        # Identify confused pairs
        logger.info("Identifying most confused gesture pairs...")
        self._identify_confused_pairs()
        
        logger.info("="*60)
        logger.info("Evaluation Complete!")
        logger.info("="*60)
        
        return self.metrics
    
    def _run_inference(self):
        """
        Run inference on test set and collect predictions.
        
        Measures inference time for each batch to calculate latency metrics.
        """
        self.predictions = []
        self.ground_truth = []
        self.inference_times = []
        
        with torch.no_grad():
            for batch_idx, (features, labels) in enumerate(self.test_loader):
                # Move data to device
                features = features.to(self.device)
                labels = labels.to(self.device)
                
                # Measure inference time
                start_time = time.time()
                outputs = self.model(features)
                inference_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Get predictions
                _, predicted = outputs.max(1)
                
                # Store results
                self.predictions.extend(predicted.cpu().numpy())
                self.ground_truth.extend(labels.cpu().numpy())
                self.inference_times.append(inference_time / features.size(0))  # Per sample
                
                if (batch_idx + 1) % 10 == 0:
                    logger.info(f"Processed {batch_idx + 1}/{len(self.test_loader)} batches")
        
        self.predictions = np.array(self.predictions)
        self.ground_truth = np.array(self.ground_truth)
        
        logger.info(f"Inference complete: {len(self.predictions)} samples processed")
    
    def _calculate_overall_accuracy(self):
        """
        Calculate overall test accuracy.
        
        Requirements:
            - 31.1: Calculates overall accuracy on held-out test set
        """
        accuracy = accuracy_score(self.ground_truth, self.predictions)
        self.metrics['overall_accuracy'] = float(accuracy)
        
        logger.info(f"Overall Accuracy: {accuracy * 100:.2f}%")
    
    def _calculate_per_class_metrics(self):
        """
        Calculate per-class precision, recall, and F1 scores.
        
        Requirements:
            - 31.2: Calculates per-class F1 scores to handle class imbalance
            - 30.9: Reports per-class precision, recall, and F1 scores
        """
        # Calculate metrics for each class
        precision, recall, f1, support = precision_recall_fscore_support(
            self.ground_truth,
            self.predictions,
            labels=list(range(self.num_classes)),
            average=None,
            zero_division=0
        )
        
        # Store per-class metrics
        self.metrics['per_class_metrics'] = {}
        for idx, class_name in enumerate(self.class_names):
            self.metrics['per_class_metrics'][class_name] = {
                'precision': float(precision[idx]),
                'recall': float(recall[idx]),
                'f1_score': float(f1[idx]),
                'support': int(support[idx])
            }
        
        # Calculate macro and weighted averages
        precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
            self.ground_truth,
            self.predictions,
            average='macro',
            zero_division=0
        )
        
        precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
            self.ground_truth,
            self.predictions,
            average='weighted',
            zero_division=0
        )
        
        self.metrics['macro_avg'] = {
            'precision': float(precision_macro),
            'recall': float(recall_macro),
            'f1_score': float(f1_macro)
        }
        
        self.metrics['weighted_avg'] = {
            'precision': float(precision_weighted),
            'recall': float(recall_weighted),
            'f1_score': float(f1_weighted)
        }
        
        logger.info(f"Macro F1 Score: {f1_macro:.4f}")
        logger.info(f"Weighted F1 Score: {f1_weighted:.4f}")
    
    def _calculate_inference_latency(self):
        """
        Calculate average inference latency.
        
        Requirements:
            - 31.5: Calculates average inference latency on test samples
        """
        avg_latency = np.mean(self.inference_times)
        std_latency = np.std(self.inference_times)
        min_latency = np.min(self.inference_times)
        max_latency = np.max(self.inference_times)
        p50_latency = np.percentile(self.inference_times, 50)
        p95_latency = np.percentile(self.inference_times, 95)
        p99_latency = np.percentile(self.inference_times, 99)
        
        self.metrics['inference_latency_ms'] = {
            'mean': float(avg_latency),
            'std': float(std_latency),
            'min': float(min_latency),
            'max': float(max_latency),
            'p50': float(p50_latency),
            'p95': float(p95_latency),
            'p99': float(p99_latency)
        }
        
        logger.info(f"Average Inference Latency: {avg_latency:.2f} ms")
        logger.info(f"P95 Inference Latency: {p95_latency:.2f} ms")
        logger.info(f"P99 Inference Latency: {p99_latency:.2f} ms")
    
    def _calculate_model_size(self):
        """
        Calculate model size in megabytes.
        
        Requirements:
            - 31.6: Measures model size in megabytes
        """
        if hasattr(self.model, 'get_model_size_mb'):
            model_size_mb = self.model.get_model_size_mb()
        else:
            # Calculate manually
            param_size = sum(p.numel() * p.element_size() for p in self.model.parameters())
            buffer_size = sum(b.numel() * b.element_size() for b in self.model.buffers())
            model_size_mb = (param_size + buffer_size) / (1024 ** 2)
        
        total_params, trainable_params = self._count_parameters()
        
        self.metrics['model_size'] = {
            'size_mb': float(model_size_mb),
            'total_parameters': int(total_params),
            'trainable_parameters': int(trainable_params)
        }
        
        logger.info(f"Model Size: {model_size_mb:.2f} MB")
        logger.info(f"Total Parameters: {total_params:,}")
    
    def _count_parameters(self) -> Tuple[int, int]:
        """Count total and trainable parameters."""
        if hasattr(self.model, 'count_parameters'):
            return self.model.count_parameters()
        else:
            total_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            return total_params, trainable_params
    
    def _generate_confusion_matrix(self):
        """
        Generate and save confusion matrix visualization.
        
        Requirements:
            - 31.3: Generates confusion matrix visualization showing prediction patterns
            - 30.8: Generates confusion matrices for validation and test sets
        """
        # Calculate confusion matrix
        cm = confusion_matrix(self.ground_truth, self.predictions)
        
        # Normalize confusion matrix
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        
        # Store confusion matrix
        self.metrics['confusion_matrix'] = cm.tolist()
        self.metrics['confusion_matrix_normalized'] = cm_normalized.tolist()
        
        # Store for later visualization
        self.confusion_matrix = cm
        self.confusion_matrix_normalized = cm_normalized
    
    def _identify_confused_pairs(self):
        """
        Identify top 5 most confused gesture pairs.
        
        Requirements:
            - 31.4: Identifies the top 5 most confused gesture pairs
        """
        cm = self.confusion_matrix
        
        # Find off-diagonal elements (misclassifications)
        confused_pairs = []
        for i in range(self.num_classes):
            for j in range(self.num_classes):
                if i != j and cm[i, j] > 0:
                    confused_pairs.append({
                        'true_class': self.class_names[i],
                        'predicted_class': self.class_names[j],
                        'count': int(cm[i, j]),
                        'percentage': float(cm[i, j] / cm[i].sum() * 100)
                    })
        
        # Sort by count and get top 5
        confused_pairs.sort(key=lambda x: x['count'], reverse=True)
        top_5_confused = confused_pairs[:5]
        
        self.metrics['top_5_confused_pairs'] = top_5_confused
        
        logger.info("Top 5 Most Confused Gesture Pairs:")
        for idx, pair in enumerate(top_5_confused, 1):
            logger.info(
                f"  {idx}. {pair['true_class']} -> {pair['predicted_class']}: "
                f"{pair['count']} samples ({pair['percentage']:.1f}%)"
            )
    
    def save_confusion_matrix_plot(self, output_path: str):
        """
        Save confusion matrix visualization as image.
        
        Args:
            output_path: Path to save the plot
        
        Requirements:
            - 31.3: Generates confusion matrix visualization
        """
        plt.figure(figsize=(12, 10))
        
        # Plot normalized confusion matrix
        sns.heatmap(
            self.confusion_matrix_normalized,
            annot=True,
            fmt='.2f',
            cmap='Blues',
            xticklabels=self.class_names,
            yticklabels=self.class_names,
            cbar_kws={'label': 'Normalized Frequency'}
        )
        
        plt.title('Confusion Matrix (Normalized)', fontsize=16, pad=20)
        plt.xlabel('Predicted Class', fontsize=12)
        plt.ylabel('True Class', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        # Save plot
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved confusion matrix plot: {output_path}")
    
    def save_metrics_json(self, output_path: str):
        """
        Save all evaluation metrics to JSON file.
        
        Args:
            output_path: Path to save the JSON file
        
        Requirements:
            - 31.8: Saves all evaluation metrics in JSON format alongside trained models
        """
        # Add metadata
        self.metrics['metadata'] = {
            'evaluation_date': datetime.now().isoformat(),
            'num_test_samples': len(self.ground_truth),
            'num_classes': self.num_classes,
            'class_names': self.class_names,
            'device': self.device
        }
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        logger.info(f"Saved evaluation metrics: {output_path}")
    
    def print_summary(self):
        """Print evaluation summary to console."""
        logger.info("="*60)
        logger.info("EVALUATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Overall Accuracy: {self.metrics['overall_accuracy'] * 100:.2f}%")
        logger.info(f"Macro F1 Score: {self.metrics['macro_avg']['f1_score']:.4f}")
        logger.info(f"Weighted F1 Score: {self.metrics['weighted_avg']['f1_score']:.4f}")
        logger.info(f"Average Inference Latency: {self.metrics['inference_latency_ms']['mean']:.2f} ms")
        logger.info(f"P95 Inference Latency: {self.metrics['inference_latency_ms']['p95']:.2f} ms")
        logger.info(f"Model Size: {self.metrics['model_size']['size_mb']:.2f} MB")
        logger.info("="*60)


def load_checkpoint(checkpoint_path: str, device: str) -> Tuple[nn.Module, Dict]:
    """
    Load model from checkpoint.
    
    Args:
        checkpoint_path: Path to checkpoint file
        device: Device to load model on
    
    Returns:
        Tuple of (model, checkpoint_dict)
    """
    logger.info(f"Loading checkpoint: {checkpoint_path}")
    
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    # Get model configuration
    model_config = checkpoint.get('model_config', {})
    num_classes = model_config.get('num_classes', 50)
    
    # Create model
    model = CNNLSTMSignLanguageModel(
        num_classes=num_classes,
        sequence_length=model_config.get('sequence_length', 60),
        dropout_rate=model_config.get('dropout_rate', 0.3)
    )
    
    # Load state dict
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()
    
    logger.info(f"Loaded model from epoch {checkpoint.get('epoch', 'unknown')}")
    logger.info(f"Best validation accuracy: {checkpoint.get('best_val_acc', 0.0):.2f}%")
    
    return model, checkpoint


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Evaluate sign language recognition model',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Model arguments
    parser.add_argument(
        '--checkpoint',
        type=str,
        default='backend/models/checkpoints/best_model.pth',
        help='Path to model checkpoint'
    )
    
    # Data arguments
    parser.add_argument(
        '--data-dir',
        type=str,
        default='backend/storage/datasets/v1.0.0/processed',
        help='Path to processed dataset directory'
    )
    parser.add_argument(
        '--test-split',
        type=str,
        default='backend/storage/datasets/v1.0.0/splits/test.txt',
        help='Path to test split file'
    )
    
    # Output arguments
    parser.add_argument(
        '--output-dir',
        type=str,
        default='backend/models/evaluation',
        help='Directory to save evaluation results'
    )
    
    # Hardware arguments
    parser.add_argument(
        '--device',
        type=str,
        default='auto',
        choices=['auto', 'cuda', 'cpu'],
        help='Device to run evaluation on'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for evaluation'
    )
    parser.add_argument(
        '--num-workers',
        type=int,
        default=4,
        help='Number of data loading workers'
    )
    
    return parser.parse_args()


def main():
    """Main evaluation function."""
    # Parse arguments
    args = parse_args()
    
    # Determine device
    if args.device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    else:
        device = args.device
    logger.info(f"Using device: {device}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if checkpoint exists
    if not os.path.exists(args.checkpoint):
        logger.error(f"Checkpoint not found: {args.checkpoint}")
        logger.error("Please train a model first using train_model.py")
        sys.exit(1)
    
    # Load model
    model, checkpoint = load_checkpoint(args.checkpoint, device)
    
    # Load test dataset
    logger.info("Loading test dataset...")
    test_dataset = SignLanguageDataset(
        data_dir=args.data_dir,
        split_file=args.test_split,
        sequence_length=60
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(device == 'cuda')
    )
    
    logger.info(f"Test dataset: {len(test_dataset)} samples")
    logger.info(f"Number of classes: {len(test_dataset.classes)}")
    
    # Create evaluator
    evaluator = ModelEvaluator(
        model=model,
        test_loader=test_loader,
        device=device,
        class_names=test_dataset.classes
    )
    
    # Run evaluation
    metrics = evaluator.evaluate()
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save metrics JSON
    metrics_path = output_dir / f'evaluation_metrics_{timestamp}.json'
    evaluator.save_metrics_json(str(metrics_path))
    
    # Save confusion matrix plot
    cm_plot_path = output_dir / f'confusion_matrix_{timestamp}.png'
    evaluator.save_confusion_matrix_plot(str(cm_plot_path))
    
    # Print summary
    evaluator.print_summary()
    
    # Check if model meets MVP requirements
    mvp_accuracy_threshold = 0.85  # Requirement 30.10
    if metrics['overall_accuracy'] >= mvp_accuracy_threshold:
        logger.info(f"✓ Model meets MVP accuracy requirement (≥{mvp_accuracy_threshold * 100}%)")
    else:
        logger.warning(
            f"✗ Model does not meet MVP accuracy requirement "
            f"(≥{mvp_accuracy_threshold * 100}%, got {metrics['overall_accuracy'] * 100:.2f}%)"
        )
    
    # Check inference latency requirement
    max_latency_ms = 200  # Requirement 33.4
    if metrics['inference_latency_ms']['p95'] <= max_latency_ms:
        logger.info(f"✓ Model meets inference latency requirement (P95 ≤{max_latency_ms}ms)")
    else:
        logger.warning(
            f"✗ Model does not meet inference latency requirement "
            f"(P95 ≤{max_latency_ms}ms, got {metrics['inference_latency_ms']['p95']:.2f}ms)"
        )
    
    logger.info("="*60)
    logger.info("Evaluation completed successfully!")
    logger.info(f"Results saved to: {output_dir}")
    logger.info("="*60)


if __name__ == '__main__':
    main()
