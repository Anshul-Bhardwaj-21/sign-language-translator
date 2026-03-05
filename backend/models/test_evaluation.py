#!/usr/bin/env python3
"""
Test script for model evaluation functionality.

This script tests the evaluation pipeline with a mock model and dataset
to ensure all metrics are calculated correctly.

Usage:
    python test_evaluation.py
"""

import sys
import tempfile
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from models.sign_language_model import CNNLSTMSignLanguageModel
from models.evaluate_model import ModelEvaluator


class MockDataset(Dataset):
    """Mock dataset for testing."""
    
    def __init__(self, num_samples=100, num_classes=10, sequence_length=60):
        self.num_samples = num_samples
        self.num_classes = num_classes
        self.sequence_length = sequence_length
        
        # Generate random data
        self.features = torch.randn(num_samples, sequence_length, 126)
        self.labels = torch.randint(0, num_classes, (num_samples,))
    
    def __len__(self):
        return self.num_samples
    
    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


def test_evaluation():
    """Test evaluation pipeline."""
    print("="*60)
    print("Testing Model Evaluation Pipeline")
    print("="*60)
    
    # Configuration
    num_classes = 10
    num_samples = 100
    batch_size = 16
    device = 'cpu'
    
    # Create mock model
    print("\n1. Creating mock model...")
    model = CNNLSTMSignLanguageModel(
        num_classes=num_classes,
        sequence_length=60,
        dropout_rate=0.3
    )
    model = model.to(device)
    model.eval()
    print("✓ Model created")
    
    # Create mock dataset
    print("\n2. Creating mock dataset...")
    test_dataset = MockDataset(
        num_samples=num_samples,
        num_classes=num_classes
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False
    )
    print(f"✓ Dataset created: {num_samples} samples, {num_classes} classes")
    
    # Create class names
    class_names = [f"gesture_{i}" for i in range(num_classes)]
    
    # Create evaluator
    print("\n3. Creating evaluator...")
    evaluator = ModelEvaluator(
        model=model,
        test_loader=test_loader,
        device=device,
        class_names=class_names
    )
    print("✓ Evaluator created")
    
    # Run evaluation
    print("\n4. Running evaluation...")
    metrics = evaluator.evaluate()
    print("✓ Evaluation complete")
    
    # Verify metrics
    print("\n5. Verifying metrics...")
    
    # Check overall accuracy
    assert 'overall_accuracy' in metrics, "Missing overall_accuracy"
    assert 0.0 <= metrics['overall_accuracy'] <= 1.0, "Invalid accuracy range"
    print(f"✓ Overall accuracy: {metrics['overall_accuracy'] * 100:.2f}%")
    
    # Check per-class metrics
    assert 'per_class_metrics' in metrics, "Missing per_class_metrics"
    assert len(metrics['per_class_metrics']) == num_classes, "Wrong number of classes"
    for class_name in class_names:
        assert class_name in metrics['per_class_metrics'], f"Missing class {class_name}"
        class_metrics = metrics['per_class_metrics'][class_name]
        assert 'precision' in class_metrics, f"Missing precision for {class_name}"
        assert 'recall' in class_metrics, f"Missing recall for {class_name}"
        assert 'f1_score' in class_metrics, f"Missing f1_score for {class_name}"
        assert 'support' in class_metrics, f"Missing support for {class_name}"
    print(f"✓ Per-class metrics calculated for {num_classes} classes")
    
    # Check macro and weighted averages
    assert 'macro_avg' in metrics, "Missing macro_avg"
    assert 'weighted_avg' in metrics, "Missing weighted_avg"
    print(f"✓ Macro F1: {metrics['macro_avg']['f1_score']:.4f}")
    print(f"✓ Weighted F1: {metrics['weighted_avg']['f1_score']:.4f}")
    
    # Check inference latency
    assert 'inference_latency_ms' in metrics, "Missing inference_latency_ms"
    latency = metrics['inference_latency_ms']
    assert 'mean' in latency, "Missing mean latency"
    assert 'p95' in latency, "Missing p95 latency"
    assert 'p99' in latency, "Missing p99 latency"
    assert latency['mean'] > 0, "Invalid mean latency"
    print(f"✓ Inference latency: {latency['mean']:.2f} ms (P95: {latency['p95']:.2f} ms)")
    
    # Check model size
    assert 'model_size' in metrics, "Missing model_size"
    assert 'size_mb' in metrics['model_size'], "Missing size_mb"
    assert metrics['model_size']['size_mb'] > 0, "Invalid model size"
    print(f"✓ Model size: {metrics['model_size']['size_mb']:.2f} MB")
    
    # Check confusion matrix
    assert 'confusion_matrix' in metrics, "Missing confusion_matrix"
    assert 'confusion_matrix_normalized' in metrics, "Missing confusion_matrix_normalized"
    cm = np.array(metrics['confusion_matrix'])
    assert cm.shape == (num_classes, num_classes), "Invalid confusion matrix shape"
    print(f"✓ Confusion matrix: {cm.shape}")
    
    # Check top confused pairs
    assert 'top_5_confused_pairs' in metrics, "Missing top_5_confused_pairs"
    confused_pairs = metrics['top_5_confused_pairs']
    assert len(confused_pairs) <= 5, "Too many confused pairs"
    print(f"✓ Top confused pairs: {len(confused_pairs)} pairs identified")
    
    # Test saving functionality
    print("\n6. Testing save functionality...")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save metrics JSON
        metrics_path = Path(tmpdir) / 'test_metrics.json'
        evaluator.save_metrics_json(str(metrics_path))
        assert metrics_path.exists(), "Metrics JSON not saved"
        print(f"✓ Metrics JSON saved: {metrics_path}")
        
        # Save confusion matrix plot
        cm_path = Path(tmpdir) / 'test_confusion_matrix.png'
        evaluator.save_confusion_matrix_plot(str(cm_path))
        assert cm_path.exists(), "Confusion matrix plot not saved"
        print(f"✓ Confusion matrix plot saved: {cm_path}")
    
    # Print summary
    print("\n7. Testing summary output...")
    evaluator.print_summary()
    print("✓ Summary printed")
    
    print("\n" + "="*60)
    print("All tests passed! ✓")
    print("="*60)


if __name__ == '__main__':
    test_evaluation()
