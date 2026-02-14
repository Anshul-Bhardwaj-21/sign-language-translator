"""Preprocessing and augmentation utilities for landmark data."""

from __future__ import annotations

import numpy as np
from typing import Tuple


def normalize_landmarks(landmarks: np.ndarray) -> np.ndarray:
    """
    Normalize hand landmarks to be scale and translation invariant.
    
    Steps:
    1. Center landmarks around wrist (landmark 0)
    2. Scale by hand size (max distance from wrist)
    
    Args:
        landmarks: (T, 21, 3) array of hand landmarks
    
    Returns:
        Normalized landmarks of same shape
    """
    landmarks = landmarks.copy()
    
    for t in range(landmarks.shape[0]):
        frame = landmarks[t]  # (21, 3)
        
        # Center around wrist
        wrist = frame[0]
        frame = frame - wrist
        
        # Scale by hand size
        distances = np.linalg.norm(frame, axis=1)
        max_distance = np.max(distances)
        
        if max_distance > 1e-6:  # Avoid division by zero
            frame = frame / max_distance
        
        landmarks[t] = frame
    
    return landmarks


def augment_sequence(
    landmarks: np.ndarray,
    rotation_range: float = 15.0,
    scale_range: Tuple[float, float] = (0.9, 1.1),
    noise_std: float = 0.01
) -> np.ndarray:
    """
    Apply data augmentation to landmark sequence.
    
    Augmentations:
    - Random rotation around Z-axis
    - Random scaling
    - Gaussian noise
    
    Args:
        landmarks: (T, 21, 3) array
        rotation_range: Max rotation in degrees
        scale_range: (min_scale, max_scale)
        noise_std: Standard deviation of Gaussian noise
    
    Returns:
        Augmented landmarks
    """
    landmarks = landmarks.copy()
    
    # Random rotation around Z-axis
    angle = np.random.uniform(-rotation_range, rotation_range)
    angle_rad = np.deg2rad(angle)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    
    rotation_matrix = np.array([
        [cos_a, -sin_a, 0],
        [sin_a, cos_a, 0],
        [0, 0, 1]
    ])
    
    # Apply rotation to all frames
    for t in range(landmarks.shape[0]):
        landmarks[t] = landmarks[t] @ rotation_matrix.T
    
    # Random scaling
    scale = np.random.uniform(*scale_range)
    landmarks = landmarks * scale
    
    # Gaussian noise
    noise = np.random.normal(0, noise_std, landmarks.shape)
    landmarks = landmarks + noise
    
    return landmarks


def temporal_smooth(
    landmarks: np.ndarray,
    window_size: int = 3
) -> np.ndarray:
    """
    Apply temporal smoothing using moving average.
    
    Args:
        landmarks: (T, 21, 3) array
        window_size: Size of smoothing window
    
    Returns:
        Smoothed landmarks
    """
    if window_size <= 1:
        return landmarks
    
    smoothed = landmarks.copy()
    half_window = window_size // 2
    
    for t in range(landmarks.shape[0]):
        start = max(0, t - half_window)
        end = min(landmarks.shape[0], t + half_window + 1)
        smoothed[t] = np.mean(landmarks[start:end], axis=0)
    
    return smoothed


def extract_velocity_features(landmarks: np.ndarray) -> np.ndarray:
    """
    Extract velocity features from landmark sequence.
    
    Args:
        landmarks: (T, 21, 3) array
    
    Returns:
        Velocity features of shape (T-1, 21, 3)
    """
    if landmarks.shape[0] < 2:
        return np.zeros((1, 21, 3))
    
    velocities = np.diff(landmarks, axis=0)
    return velocities


def extract_acceleration_features(landmarks: np.ndarray) -> np.ndarray:
    """
    Extract acceleration features from landmark sequence.
    
    Args:
        landmarks: (T, 21, 3) array
    
    Returns:
        Acceleration features of shape (T-2, 21, 3)
    """
    if landmarks.shape[0] < 3:
        return np.zeros((1, 21, 3))
    
    velocities = extract_velocity_features(landmarks)
    accelerations = np.diff(velocities, axis=0)
    return accelerations


def compute_hand_angles(landmarks: np.ndarray) -> np.ndarray:
    """
    Compute angles between finger segments.
    
    Args:
        landmarks: (T, 21, 3) array
    
    Returns:
        Angles array of shape (T, num_angles)
    """
    # Finger landmark indices
    fingers = {
        'thumb': [0, 1, 2, 3, 4],
        'index': [0, 5, 6, 7, 8],
        'middle': [0, 9, 10, 11, 12],
        'ring': [0, 13, 14, 15, 16],
        'pinky': [0, 17, 18, 19, 20]
    }
    
    angles_list = []
    
    for t in range(landmarks.shape[0]):
        frame_angles = []
        
        for finger_name, indices in fingers.items():
            # Compute angles between consecutive segments
            for i in range(len(indices) - 2):
                p1 = landmarks[t, indices[i]]
                p2 = landmarks[t, indices[i+1]]
                p3 = landmarks[t, indices[i+2]]
                
                # Vectors
                v1 = p1 - p2
                v2 = p3 - p2
                
                # Angle
                cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                angle = np.arccos(cos_angle)
                
                frame_angles.append(angle)
        
        angles_list.append(frame_angles)
    
    return np.array(angles_list)


def pad_or_trim_sequence(
    landmarks: np.ndarray,
    target_length: int,
    pad_value: float = 0.0
) -> np.ndarray:
    """
    Pad or trim sequence to target length.
    
    Args:
        landmarks: (T, 21, 3) array
        target_length: Desired sequence length
        pad_value: Value to use for padding
    
    Returns:
        Sequence of shape (target_length, 21, 3)
    """
    current_length = landmarks.shape[0]
    
    if current_length == target_length:
        return landmarks
    
    if current_length > target_length:
        # Trim from the end
        return landmarks[:target_length]
    
    # Pad at the end
    pad_length = target_length - current_length
    padding = np.full((pad_length, 21, 3), pad_value)
    return np.concatenate([landmarks, padding], axis=0)


if __name__ == "__main__":
    # Test preprocessing functions
    print("Testing preprocessing functions...")
    
    # Create dummy landmarks
    T, num_landmarks, coords = 24, 21, 3
    landmarks = np.random.randn(T, num_landmarks, coords)
    
    print(f"Original shape: {landmarks.shape}")
    print(f"Original range: [{landmarks.min():.3f}, {landmarks.max():.3f}]")
    
    # Test normalization
    normalized = normalize_landmarks(landmarks)
    print(f"\nNormalized range: [{normalized.min():.3f}, {normalized.max():.3f}]")
    
    # Test augmentation
    augmented = augment_sequence(landmarks)
    print(f"Augmented shape: {augmented.shape}")
    
    # Test smoothing
    smoothed = temporal_smooth(landmarks, window_size=5)
    print(f"Smoothed shape: {smoothed.shape}")
    
    # Test velocity features
    velocities = extract_velocity_features(landmarks)
    print(f"Velocity features shape: {velocities.shape}")
    
    # Test angles
    angles = compute_hand_angles(landmarks)
    print(f"Angles shape: {angles.shape}")
    
    # Test padding
    padded = pad_or_trim_sequence(landmarks, target_length=30)
    print(f"Padded shape: {padded.shape}")
    
    trimmed = pad_or_trim_sequence(landmarks, target_length=10)
    print(f"Trimmed shape: {trimmed.shape}")
    
    print("\n✓ All preprocessing functions working correctly")
