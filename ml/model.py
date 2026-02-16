"""PyTorch model architectures for sign language recognition."""

from __future__ import annotations

import torch
import torch.nn as nn
from typing import Tuple


class Conv1DLSTMClassifier(nn.Module):
    """
    Temporal Convolutional + BiLSTM architecture for gesture classification.
    
    Architecture:
    - Conv1D layers for local temporal feature extraction
    - BiLSTM for sequence modeling
    - Fully connected layers for classification
    
    Input: (batch, sequence_length, features)
    Output: (batch, num_classes)
    """
    
    def __init__(
        self,
        input_features: int = 63,  # 21 landmarks * 3 coordinates
        num_classes: int = 10,
        hidden_dim: int = 128,
        num_lstm_layers: int = 2,
        dropout: float = 0.3
    ):
        super().__init__()
        
        self.input_features = input_features
        self.num_classes = num_classes
        
        # Temporal convolution layers
        self.conv1 = nn.Conv1d(input_features, 64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(64)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(128)
        
        # BiLSTM layers
        self.lstm = nn.LSTM(
            input_size=128,
            hidden_size=hidden_dim,
            num_layers=num_lstm_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_lstm_layers > 1 else 0
        )
        
        # Fully connected layers
        self.fc1 = nn.Linear(hidden_dim * 2, 128)  # *2 for bidirectional
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(128, num_classes)
        
        self.relu = nn.ReLU()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch, sequence_length, features)
        
        Returns:
            Logits of shape (batch, num_classes)
        """
        # x: (batch, seq_len, features)
        
        # Conv1D expects (batch, features, seq_len)
        x = x.transpose(1, 2)
        
        # Convolutional layers
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        
        # Back to (batch, seq_len, features) for LSTM
        x = x.transpose(1, 2)
        
        # LSTM
        lstm_out, _ = self.lstm(x)
        
        # Use last timestep output
        x = lstm_out[:, -1, :]
        
        # Fully connected layers
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        
        return x


class TCNClassifier(nn.Module):
    """
    Temporal Convolutional Network for gesture classification.
    
    Lightweight alternative to LSTM with better parallelization.
    """
    
    def __init__(
        self,
        input_features: int = 63,
        num_classes: int = 10,
        num_channels: list = None,
        kernel_size: int = 3,
        dropout: float = 0.2
    ):
        super().__init__()
        
        if num_channels is None:
            num_channels = [64, 128, 128, 256]
        
        self.input_features = input_features
        self.num_classes = num_classes
        
        layers = []
        num_levels = len(num_channels)
        
        for i in range(num_levels):
            dilation_size = 2 ** i
            in_channels = input_features if i == 0 else num_channels[i-1]
            out_channels = num_channels[i]
            
            layers.append(
                TemporalBlock(
                    in_channels,
                    out_channels,
                    kernel_size,
                    stride=1,
                    dilation=dilation_size,
                    padding=(kernel_size-1) * dilation_size,
                    dropout=dropout
                )
            )
        
        self.network = nn.Sequential(*layers)
        self.fc = nn.Linear(num_channels[-1], num_classes)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch, sequence_length, features)
        
        Returns:
            Logits of shape (batch, num_classes)
        """
        # x: (batch, seq_len, features)
        # TCN expects (batch, features, seq_len)
        x = x.transpose(1, 2)
        
        # TCN layers
        x = self.network(x)
        
        # Global average pooling
        x = x.mean(dim=2)
        
        # Classification
        x = self.fc(x)
        
        return x


class TemporalBlock(nn.Module):
    """Building block for TCN."""
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        stride: int,
        dilation: int,
        padding: int,
        dropout: float = 0.2
    ):
        super().__init__()
        
        self.conv1 = nn.Conv1d(
            in_channels, out_channels, kernel_size,
            stride=stride, padding=padding, dilation=dilation
        )
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout)
        
        self.conv2 = nn.Conv1d(
            out_channels, out_channels, kernel_size,
            stride=stride, padding=padding, dilation=dilation
        )
        self.bn2 = nn.BatchNorm1d(out_channels)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(dropout)
        
        # Residual connection
        self.downsample = nn.Conv1d(in_channels, out_channels, 1) if in_channels != out_channels else None
        self.relu = nn.ReLU()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu1(out)
        out = self.dropout1(out)
        
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu2(out)
        out = self.dropout2(out)
        
        # Trim to match residual size (causal padding)
        out = out[:, :, :residual.size(2)]
        
        if self.downsample is not None:
            residual = self.downsample(residual)
        
        out = out + residual
        out = self.relu(out)
        
        return out


def create_model(
    model_type: str = "conv_lstm",
    input_features: int = 63,
    num_classes: int = 10,
    **kwargs
) -> nn.Module:
    """
    Factory function for creating models.
    
    Args:
        model_type: "conv_lstm" or "tcn"
        input_features: Number of input features (21 landmarks * 3 = 63)
        num_classes: Number of gesture classes
        **kwargs: Additional model-specific parameters
    
    Returns:
        PyTorch model
    """
    if model_type == "conv_lstm":
        return Conv1DLSTMClassifier(
            input_features=input_features,
            num_classes=num_classes,
            **kwargs
        )
    elif model_type == "tcn":
        return TCNClassifier(
            input_features=input_features,
            num_classes=num_classes,
            **kwargs
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def count_parameters(model: nn.Module) -> int:
    """Count trainable parameters in model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Test model creation
    print("Testing Conv1D+LSTM model:")
    model_lstm = create_model("conv_lstm", num_classes=10)
    print(f"Parameters: {count_parameters(model_lstm):,}")
    
    # Test forward pass
    batch_size = 4
    seq_len = 24
    features = 63
    x = torch.randn(batch_size, seq_len, features)
    output = model_lstm(x)
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    
    print("\nTesting TCN model:")
    model_tcn = create_model("tcn", num_classes=10)
    print(f"Parameters: {count_parameters(model_tcn):,}")
    output = model_tcn(x)
    print(f"Output shape: {output.shape}")
