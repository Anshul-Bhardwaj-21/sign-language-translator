"""Dataset loader for sign language landmark sequences."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple, Optional
import logging

import numpy as np
import torch
from torch.utils.data import Dataset

from preprocess import normalize_landmarks, augment_sequence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LandmarkDataset(Dataset):
    """
    Dataset for hand landmark sequences.
    
    Expected directory structure:
        data_dir/
        ├── CLASS1/
        │   ├── sample_001.npz
        │   ├── sample_002.npz
        │   └── ...
        ├── CLASS2/
        │   └── ...
        └── ...
    
    Each .npz file should contain:
        - 'landmarks': (T, 21, 3) array of hand landmarks
        - 'label': str (optional, inferred from directory)
        - 'signer_id': str (optional)
    """
    
    def __init__(
        self,
        data_dir: str,
        sequence_length: int = 24,
        augment: bool = False,
        normalize: bool = True
    ):
        self.data_dir = Path(data_dir)
        self.sequence_length = sequence_length
        self.augment = augment
        self.normalize = normalize
        
        self.samples: List[Tuple[Path, int]] = []
        self.classes: List[str] = []
        self.class_to_idx: dict = {}
        
        self._load_dataset()
    
    def _load_dataset(self):
        """Scan directory and build sample list."""
        if not self.data_dir.exists():
            logger.error(f"Dataset directory not found: {self.data_dir}")
            return
        
        # Find all class directories
        class_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]
        
        if not class_dirs:
            logger.warning(f"No class directories found in {self.data_dir}")
            return
        
        # Sort for consistent ordering
        class_dirs = sorted(class_dirs, key=lambda x: x.name)
        
        for class_idx, class_dir in enumerate(class_dirs):
            class_name = class_dir.name
            self.classes.append(class_name)
            self.class_to_idx[class_name] = class_idx
            
            # Find all .npz files in class directory
            npz_files = list(class_dir.glob("*.npz"))
            
            for npz_file in npz_files:
                self.samples.append((npz_file, class_idx))
            
            logger.info(f"Class '{class_name}': {len(npz_files)} samples")
        
        logger.info(f"Total samples: {len(self.samples)}")
        logger.info(f"Classes: {self.classes}")
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """
        Get a sample.
        
        Returns:
            sequence: (sequence_length, 63) tensor of flattened landmarks
            label: int class index
        """
        file_path, label = self.samples[idx]
        
        try:
            # Load landmarks
            data = np.load(file_path)
            landmarks = data['landmarks']  # (T, 21, 3)
            
            # Ensure correct shape
            if landmarks.ndim != 3 or landmarks.shape[1] != 21 or landmarks.shape[2] != 3:
                logger.warning(f"Invalid landmark shape in {file_path}: {landmarks.shape}")
                # Return zero tensor as fallback
                return torch.zeros(self.sequence_length, 63), label
            
            # Normalize landmarks
            if self.normalize:
                landmarks = normalize_landmarks(landmarks)
            
            # Temporal resampling to target sequence length
            landmarks = self._resample_sequence(landmarks, self.sequence_length)
            
            # Data augmentation
            if self.augment:
                landmarks = augment_sequence(landmarks)
            
            # Flatten landmarks: (T, 21, 3) -> (T, 63)
            landmarks = landmarks.reshape(self.sequence_length, -1)
            
            # Convert to tensor
            sequence = torch.from_numpy(landmarks).float()
            
            return sequence, label
        
        except Exception as exc:
            logger.error(f"Error loading {file_path}: {exc}")
            # Return zero tensor as fallback
            return torch.zeros(self.sequence_length, 63), label
    
    def _resample_sequence(
        self,
        sequence: np.ndarray,
        target_length: int
    ) -> np.ndarray:
        """
        Resample sequence to target length using linear interpolation.
        
        Args:
            sequence: (T, 21, 3) array
            target_length: Desired sequence length
        
        Returns:
            Resampled sequence of shape (target_length, 21, 3)
        """
        current_length = sequence.shape[0]
        
        if current_length == target_length:
            return sequence
        
        # Create interpolation indices
        old_indices = np.linspace(0, current_length - 1, current_length)
        new_indices = np.linspace(0, current_length - 1, target_length)
        
        # Interpolate each landmark coordinate
        resampled = np.zeros((target_length, 21, 3))
        
        for landmark_idx in range(21):
            for coord_idx in range(3):
                resampled[:, landmark_idx, coord_idx] = np.interp(
                    new_indices,
                    old_indices,
                    sequence[:, landmark_idx, coord_idx]
                )
        
        return resampled
    
    @property
    def num_classes(self) -> int:
        return len(self.classes)


def collate_fn(batch: List[Tuple[torch.Tensor, int]]) -> Tuple[torch.Tensor, torch.Tensor]:
    """Custom collate function for DataLoader."""
    sequences, labels = zip(*batch)
    sequences = torch.stack(sequences)
    labels = torch.tensor(labels, dtype=torch.long)
    return sequences, labels


if __name__ == "__main__":
    # Test dataset loading
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python dataset_loader.py <data_dir>")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    
    print(f"Loading dataset from: {data_dir}")
    dataset = LandmarkDataset(data_dir, sequence_length=24, augment=False)
    
    print(f"\nDataset size: {len(dataset)}")
    print(f"Number of classes: {dataset.num_classes}")
    print(f"Classes: {dataset.classes}")
    
    if len(dataset) > 0:
        print("\nTesting sample loading...")
        sequence, label = dataset[0]
        print(f"Sequence shape: {sequence.shape}")
        print(f"Label: {label} ({dataset.classes[label]})")
        print(f"Sequence range: [{sequence.min():.3f}, {sequence.max():.3f}]")
