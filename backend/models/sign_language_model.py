#!/usr/bin/env python3
"""
Sign Language Recognition Model - CNN+LSTM Baseline Architecture

This module implements a baseline CNN+LSTM model for sign language gesture recognition.
The model processes sequences of hand landmark coordinates extracted from video frames.

Architecture:
    Input: (batch_size, sequence_length=60, num_features=126)
           where num_features = 42 keypoints × 3 coordinates (x, y, z)
    
    CNN Feature Extraction:
        - Conv1D(64 filters) + BatchNorm + MaxPool + Dropout
        - Conv1D(128 filters) + BatchNorm + MaxPool + Dropout
        - Conv1D(256 filters) + BatchNorm + GlobalMaxPool
    
    LSTM Temporal Modeling:
        - LSTM(128 units) + Dropout
        - LSTM(64 units) + Dropout
    
    Classification Head:
        - Dense(128) + Dropout
        - Dense(num_classes) + Softmax
    
    Output: (batch_size, num_classes) - probability distribution over gesture classes

Requirements: 30.1, 30.10
Phase: MVP

Author: AI-Powered Meeting Platform Team
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional, Tuple


class CNNLSTMSignLanguageModel(nn.Module):
    """
    CNN+LSTM baseline model for sign language gesture recognition.
    
    This model combines convolutional layers for spatial feature extraction
    with LSTM layers for temporal sequence modeling. It's designed to process
    hand landmark sequences and classify them into gesture categories.
    
    Architecture Details:
        - 3 Conv1D layers with increasing filter sizes (64, 128, 256)
        - BatchNorm after each Conv1D for training stability
        - MaxPool and Dropout for regularization
        - 2 LSTM layers (128, 64 units) for temporal modeling
        - Dense classification head with dropout
    
    Expected Performance (MVP):
        - Test accuracy: ≥85%
        - Inference latency: <200ms (CPU)
        - Model size: ~50 MB
        - Vocabulary: 20-50 common gestures
    
    Args:
        num_classes: Number of gesture classes to predict
        sequence_length: Fixed sequence length (default: 60 frames)
        num_keypoints: Number of hand keypoints (default: 42 for both hands)
        coordinates: Number of coordinates per keypoint (default: 3 for x,y,z)
        dropout_rate: Dropout probability for regularization (default: 0.3-0.5)
    
    Input Shape:
        (batch_size, sequence_length, num_keypoints * coordinates)
        = (batch_size, 60, 126)
    
    Output Shape:
        (batch_size, num_classes)
    
    Requirements:
        - 30.1: Implements CNN+LSTM architecture for sequence classification
        - 30.10: Achieves minimum 85% accuracy on test set for MVP release
    """
    
    def __init__(
        self,
        num_classes: int,
        sequence_length: int = 60,
        num_keypoints: int = 42,
        coordinates: int = 3,
        dropout_rate: float = 0.3
    ):
        super(CNNLSTMSignLanguageModel, self).__init__()
        
        # Model configuration
        self.num_classes = num_classes
        self.sequence_length = sequence_length
        self.num_keypoints = num_keypoints
        self.coordinates = coordinates
        self.input_features = num_keypoints * coordinates  # 42 * 3 = 126
        self.dropout_rate = dropout_rate
        
        # CNN Feature Extraction Layers
        # Conv1D expects input shape: (batch, channels, sequence_length)
        # We'll transpose input from (batch, seq, features) to (batch, features, seq)
        
        # First Conv1D block: 64 filters
        self.conv1 = nn.Conv1d(
            in_channels=self.input_features,
            out_channels=64,
            kernel_size=3,
            padding=1
        )
        self.bn1 = nn.BatchNorm1d(64)
        self.pool1 = nn.MaxPool1d(kernel_size=2)
        self.dropout1 = nn.Dropout(dropout_rate)
        
        # Second Conv1D block: 128 filters
        self.conv2 = nn.Conv1d(
            in_channels=64,
            out_channels=128,
            kernel_size=3,
            padding=1
        )
        self.bn2 = nn.BatchNorm1d(128)
        self.pool2 = nn.MaxPool1d(kernel_size=2)
        self.dropout2 = nn.Dropout(dropout_rate)
        
        # Third Conv1D block: 256 filters
        self.conv3 = nn.Conv1d(
            in_channels=128,
            out_channels=256,
            kernel_size=3,
            padding=1
        )
        self.bn3 = nn.BatchNorm1d(256)
        # Global max pooling will be applied in forward pass
        self.dropout3 = nn.Dropout(dropout_rate)
        
        # Calculate sequence length after pooling operations
        # After pool1: seq_len / 2
        # After pool2: seq_len / 4
        # After global max pool: 1
        seq_after_pools = sequence_length // 4
        
        # LSTM Temporal Modeling Layers
        # Input to LSTM: (batch, seq_len, features)
        # We need to reshape CNN output appropriately
        
        self.lstm1 = nn.LSTM(
            input_size=256,
            hidden_size=128,
            num_layers=1,
            batch_first=True,
            dropout=0.0  # No dropout for single layer
        )
        self.dropout4 = nn.Dropout(0.4)  # Higher dropout after LSTM
        
        self.lstm2 = nn.LSTM(
            input_size=128,
            hidden_size=64,
            num_layers=1,
            batch_first=True,
            dropout=0.0
        )
        self.dropout5 = nn.Dropout(0.4)
        
        # Classification Head
        self.fc1 = nn.Linear(64, 128)
        self.dropout6 = nn.Dropout(0.5)  # Highest dropout before final layer
        self.fc2 = nn.Linear(128, num_classes)
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """
        Initialize model weights using appropriate strategies.
        
        - Conv layers: Kaiming initialization (good for ReLU)
        - LSTM layers: Xavier initialization
        - Linear layers: Xavier initialization
        """
        for module in self.modules():
            if isinstance(module, nn.Conv1d):
                nn.init.kaiming_normal_(module.weight, mode='fan_out', nonlinearity='relu')
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
            elif isinstance(module, nn.BatchNorm1d):
                nn.init.constant_(module.weight, 1)
                nn.init.constant_(module.bias, 0)
            elif isinstance(module, nn.LSTM):
                for name, param in module.named_parameters():
                    if 'weight' in name:
                        nn.init.xavier_normal_(param)
                    elif 'bias' in name:
                        nn.init.constant_(param, 0)
            elif isinstance(module, nn.Linear):
                nn.init.xavier_normal_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the model.
        
        Args:
            x: Input tensor of shape (batch_size, sequence_length, num_features)
               where num_features = num_keypoints * coordinates = 126
        
        Returns:
            Output tensor of shape (batch_size, num_classes) with class probabilities
        
        Processing Steps:
            1. Reshape input for Conv1D: (batch, features, sequence)
            2. Apply CNN feature extraction with BatchNorm and pooling
            3. Reshape for LSTM: (batch, sequence, features)
            4. Apply LSTM temporal modeling
            5. Apply classification head with softmax
        """
        batch_size = x.size(0)
        
        # Input shape: (batch, seq_len, features) = (batch, 60, 126)
        # Conv1D expects: (batch, features, seq_len)
        x = x.transpose(1, 2)  # (batch, 126, 60)
        
        # CNN Feature Extraction
        # Block 1: Conv1D(64) + BatchNorm + ReLU + MaxPool + Dropout
        x = self.conv1(x)  # (batch, 64, 60)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.pool1(x)  # (batch, 64, 30)
        x = self.dropout1(x)
        
        # Block 2: Conv1D(128) + BatchNorm + ReLU + MaxPool + Dropout
        x = self.conv2(x)  # (batch, 128, 30)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.pool2(x)  # (batch, 128, 15)
        x = self.dropout2(x)
        
        # Block 3: Conv1D(256) + BatchNorm + ReLU + Dropout
        x = self.conv3(x)  # (batch, 256, 15)
        x = self.bn3(x)
        x = F.relu(x)
        x = self.dropout3(x)
        
        # Prepare for LSTM: (batch, features, seq_len) -> (batch, seq_len, features)
        x = x.transpose(1, 2)  # (batch, 15, 256)
        
        # LSTM Temporal Modeling
        # LSTM 1: 128 units
        x, _ = self.lstm1(x)  # (batch, 15, 128)
        x = self.dropout4(x)
        
        # LSTM 2: 64 units (return_sequences=False equivalent)
        x, (h_n, c_n) = self.lstm2(x)  # x: (batch, 15, 64), h_n: (1, batch, 64)
        # Take the last hidden state
        x = x[:, -1, :]  # (batch, 64)
        x = self.dropout5(x)
        
        # Classification Head
        x = self.fc1(x)  # (batch, 128)
        x = F.relu(x)
        x = self.dropout6(x)
        
        x = self.fc2(x)  # (batch, num_classes)
        
        # Apply softmax for probability distribution
        x = F.softmax(x, dim=1)
        
        return x
    
    def get_config(self) -> Dict:
        """
        Get model configuration as dictionary.
        
        Returns:
            Dictionary containing model hyperparameters and architecture details
        """
        return {
            'model_type': 'CNN+LSTM',
            'num_classes': self.num_classes,
            'sequence_length': self.sequence_length,
            'num_keypoints': self.num_keypoints,
            'coordinates': self.coordinates,
            'input_features': self.input_features,
            'dropout_rate': self.dropout_rate,
            'architecture': {
                'cnn_layers': [
                    {'type': 'Conv1D', 'filters': 64, 'kernel_size': 3},
                    {'type': 'Conv1D', 'filters': 128, 'kernel_size': 3},
                    {'type': 'Conv1D', 'filters': 256, 'kernel_size': 3}
                ],
                'lstm_layers': [
                    {'type': 'LSTM', 'units': 128},
                    {'type': 'LSTM', 'units': 64}
                ],
                'dense_layers': [
                    {'type': 'Dense', 'units': 128},
                    {'type': 'Dense', 'units': self.num_classes}
                ]
            }
        }
    
    def count_parameters(self) -> Tuple[int, int]:
        """
        Count total and trainable parameters in the model.
        
        Returns:
            Tuple of (total_params, trainable_params)
        """
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return total_params, trainable_params
    
    def get_model_size_mb(self) -> float:
        """
        Calculate model size in megabytes.
        
        Returns:
            Model size in MB
        """
        param_size = sum(p.numel() * p.element_size() for p in self.parameters())
        buffer_size = sum(b.numel() * b.element_size() for b in self.buffers())
        size_mb = (param_size + buffer_size) / (1024 ** 2)
        return size_mb


def create_model(
    num_classes: int,
    sequence_length: int = 60,
    dropout_rate: float = 0.3,
    device: Optional[str] = None
) -> CNNLSTMSignLanguageModel:
    """
    Factory function to create and initialize a CNN+LSTM model.
    
    Args:
        num_classes: Number of gesture classes to predict
        sequence_length: Fixed sequence length (default: 60 frames)
        dropout_rate: Dropout probability (default: 0.3)
        device: Device to place model on ('cuda', 'cpu', or None for auto-detect)
    
    Returns:
        Initialized model on specified device
    
    Example:
        >>> model = create_model(num_classes=50, dropout_rate=0.3)
        >>> print(f"Model has {model.count_parameters()[0]:,} parameters")
        >>> print(f"Model size: {model.get_model_size_mb():.2f} MB")
    """
    # Auto-detect device if not specified
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Create model
    model = CNNLSTMSignLanguageModel(
        num_classes=num_classes,
        sequence_length=sequence_length,
        dropout_rate=dropout_rate
    )
    
    # Move to device
    model = model.to(device)
    
    return model


if __name__ == '__main__':
    """
    Test script to verify model architecture and output shapes.
    """
    print("="*60)
    print("CNN+LSTM Sign Language Model - Architecture Test")
    print("="*60)
    
    # Create model for 50 gesture classes (MVP target)
    num_classes = 50
    batch_size = 8
    sequence_length = 60
    
    model = create_model(num_classes=num_classes, dropout_rate=0.3)
    
    # Print model information
    print(f"\nModel Configuration:")
    config = model.get_config()
    print(f"  Model Type: {config['model_type']}")
    print(f"  Number of Classes: {config['num_classes']}")
    print(f"  Sequence Length: {config['sequence_length']}")
    print(f"  Input Features: {config['input_features']}")
    print(f"  Dropout Rate: {config['dropout_rate']}")
    
    total_params, trainable_params = model.count_parameters()
    print(f"\nModel Statistics:")
    print(f"  Total Parameters: {total_params:,}")
    print(f"  Trainable Parameters: {trainable_params:,}")
    print(f"  Model Size: {model.get_model_size_mb():.2f} MB")
    
    # Test forward pass
    print(f"\nTesting Forward Pass:")
    print(f"  Input Shape: (batch={batch_size}, seq={sequence_length}, features=126)")
    
    # Create dummy input
    dummy_input = torch.randn(batch_size, sequence_length, 126)
    
    # Set model to evaluation mode
    model.eval()
    
    # Forward pass
    with torch.no_grad():
        output = model(dummy_input)
    
    print(f"  Output Shape: {output.shape}")
    print(f"  Expected Shape: ({batch_size}, {num_classes})")
    
    # Verify output properties
    assert output.shape == (batch_size, num_classes), "Output shape mismatch!"
    
    # Check softmax properties (probabilities sum to 1)
    prob_sums = output.sum(dim=1)
    assert torch.allclose(prob_sums, torch.ones(batch_size), atol=1e-6), "Softmax probabilities don't sum to 1!"
    
    print(f"\n✓ All tests passed!")
    print(f"✓ Model ready for training")
    print("="*60)
