"""Smoke tests for ML pipeline components."""

import pytest
import numpy as np
import torch
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.model import create_model, count_parameters, Conv1DLSTMClassifier, TCNClassifier
from ml.preprocess import (
    normalize_landmarks,
    augment_sequence,
    temporal_smooth,
    extract_velocity_features,
    pad_or_trim_sequence
)


def test_model_creation_conv_lstm():
    """Test Conv1D+LSTM model creation."""
    model = create_model("conv_lstm", num_classes=10)
    assert model is not None
    assert isinstance(model, Conv1DLSTMClassifier)
    
    # Test forward pass
    batch_size = 4
    seq_len = 24
    features = 63
    x = torch.randn(batch_size, seq_len, features)
    output = model(x)
    
    assert output.shape == (batch_size, 10)


def test_model_creation_tcn():
    """Test TCN model creation."""
    model = create_model("tcn", num_classes=10)
    assert model is not None
    assert isinstance(model, TCNClassifier)
    
    # Test forward pass
    batch_size = 4
    seq_len = 24
    features = 63
    x = torch.randn(batch_size, seq_len, features)
    output = model(x)
    
    assert output.shape == (batch_size, 10)


def test_model_parameter_count():
    """Test parameter counting."""
    model = create_model("conv_lstm", num_classes=10)
    param_count = count_parameters(model)
    assert param_count > 0
    assert isinstance(param_count, int)


def test_normalize_landmarks():
    """Test landmark normalization."""
    # Create dummy landmarks
    T, num_landmarks, coords = 24, 21, 3
    landmarks = np.random.randn(T, num_landmarks, coords)
    
    normalized = normalize_landmarks(landmarks)
    
    assert normalized.shape == landmarks.shape
    assert not np.array_equal(normalized, landmarks)  # Should be different


def test_augment_sequence():
    """Test sequence augmentation."""
    T, num_landmarks, coords = 24, 21, 3
    landmarks = np.random.randn(T, num_landmarks, coords)
    
    augmented = augment_sequence(landmarks)
    
    assert augmented.shape == landmarks.shape
    assert not np.array_equal(augmented, landmarks)  # Should be different


def test_temporal_smooth():
    """Test temporal smoothing."""
    T, num_landmarks, coords = 24, 21, 3
    landmarks = np.random.randn(T, num_landmarks, coords)
    
    smoothed = temporal_smooth(landmarks, window_size=3)
    
    assert smoothed.shape == landmarks.shape


def test_extract_velocity_features():
    """Test velocity feature extraction."""
    T, num_landmarks, coords = 24, 21, 3
    landmarks = np.random.randn(T, num_landmarks, coords)
    
    velocities = extract_velocity_features(landmarks)
    
    assert velocities.shape == (T-1, num_landmarks, coords)


def test_pad_or_trim_sequence():
    """Test sequence padding and trimming."""
    T, num_landmarks, coords = 20, 21, 3
    landmarks = np.random.randn(T, num_landmarks, coords)
    
    # Test padding
    padded = pad_or_trim_sequence(landmarks, target_length=30)
    assert padded.shape == (30, num_landmarks, coords)
    
    # Test trimming
    trimmed = pad_or_trim_sequence(landmarks, target_length=10)
    assert trimmed.shape == (10, num_landmarks, coords)
    
    # Test no change
    same = pad_or_trim_sequence(landmarks, target_length=20)
    assert same.shape == (20, num_landmarks, coords)


def test_model_inference_speed():
    """Test model inference latency."""
    import time
    
    model = create_model("conv_lstm", num_classes=10)
    model.eval()
    
    batch_size = 1
    seq_len = 24
    features = 63
    x = torch.randn(batch_size, seq_len, features)
    
    # Warmup
    with torch.no_grad():
        _ = model(x)
    
    # Measure
    latencies = []
    with torch.no_grad():
        for _ in range(100):
            start = time.perf_counter()
            _ = model(x)
            latency = (time.perf_counter() - start) * 1000  # ms
            latencies.append(latency)
    
    avg_latency = np.mean(latencies)
    assert avg_latency < 10.0  # Should be < 10ms for real-time


def test_model_output_range():
    """Test model output is valid logits."""
    model = create_model("conv_lstm", num_classes=10)
    model.eval()
    
    batch_size = 4
    seq_len = 24
    features = 63
    x = torch.randn(batch_size, seq_len, features)
    
    with torch.no_grad():
        output = model(x)
    
    # Check output shape
    assert output.shape == (batch_size, 10)
    
    # Check no NaN or Inf
    assert not torch.isnan(output).any()
    assert not torch.isinf(output).any()
    
    # Check softmax sums to 1
    probs = torch.softmax(output, dim=1)
    sums = probs.sum(dim=1)
    assert torch.allclose(sums, torch.ones_like(sums), atol=1e-6)


def test_model_gradient_flow():
    """Test gradients flow through model."""
    model = create_model("conv_lstm", num_classes=10)
    model.train()
    
    batch_size = 4
    seq_len = 24
    features = 63
    x = torch.randn(batch_size, seq_len, features)
    labels = torch.randint(0, 10, (batch_size,))
    
    # Forward pass
    output = model(x)
    loss = torch.nn.functional.cross_entropy(output, labels)
    
    # Backward pass
    loss.backward()
    
    # Check gradients exist
    for name, param in model.named_parameters():
        if param.requires_grad:
            assert param.grad is not None, f"No gradient for {name}"
            assert not torch.isnan(param.grad).any(), f"NaN gradient for {name}"


def test_preprocessing_pipeline():
    """Test complete preprocessing pipeline."""
    # Create dummy landmarks
    T, num_landmarks, coords = 30, 21, 3
    landmarks = np.random.randn(T, num_landmarks, coords)
    
    # Apply preprocessing steps
    normalized = normalize_landmarks(landmarks)
    smoothed = temporal_smooth(normalized, window_size=3)
    trimmed = pad_or_trim_sequence(smoothed, target_length=24)
    augmented = augment_sequence(trimmed)
    
    # Check final shape
    assert augmented.shape == (24, 21, 3)
    
    # Flatten for model input
    flattened = augmented.reshape(24, -1)
    assert flattened.shape == (24, 63)


def test_batch_processing():
    """Test model handles batches correctly."""
    model = create_model("conv_lstm", num_classes=10)
    model.eval()
    
    # Test different batch sizes
    for batch_size in [1, 4, 8, 16]:
        x = torch.randn(batch_size, 24, 63)
        with torch.no_grad():
            output = model(x)
        assert output.shape == (batch_size, 10)


def test_model_deterministic():
    """Test model produces same output for same input."""
    model = create_model("conv_lstm", num_classes=10)
    model.eval()
    
    torch.manual_seed(42)
    x = torch.randn(1, 24, 63)
    
    with torch.no_grad():
        output1 = model(x)
        output2 = model(x)
    
    assert torch.allclose(output1, output2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
