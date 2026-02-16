"""Shared feature engineering for landmark-sequence training and inference."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np


NUM_LANDMARKS = 21
NUM_COORDS = 3
DEFAULT_SEQUENCE_LENGTH = 24
EPSILON = 1e-6


def to_numpy_sequence(sequence: Sequence) -> np.ndarray:
    """Convert raw nested list/array input to validated numpy tensor [T, 21, 3]."""
    array = np.asarray(sequence, dtype=np.float32)
    if array.ndim != 3 or array.shape[1:] != (NUM_LANDMARKS, NUM_COORDS):
        raise ValueError(
            f"Expected sequence shape [T, {NUM_LANDMARKS}, {NUM_COORDS}], got {array.shape}"
        )
    return array


def normalize_sequence(sequence: Sequence) -> np.ndarray:
    """
    Normalize landmarks by wrist-centered coordinates and palm-size scaling.

    This reduces sensitivity to camera distance and user hand size.
    """
    array = to_numpy_sequence(sequence)

    # Center every frame on wrist.
    centered = array - array[:, 0:1, :]

    # Scale using palm width (index_mcp to pinky_mcp) with fallback.
    index_mcp = centered[:, 5, :]
    pinky_mcp = centered[:, 17, :]
    palm_scale = np.linalg.norm(index_mcp - pinky_mcp, axis=1)

    if np.all(palm_scale < EPSILON):
        palm_scale = np.ones_like(palm_scale)
    else:
        reference = np.median(palm_scale[palm_scale > EPSILON]) if np.any(palm_scale > EPSILON) else 1.0
        palm_scale = np.where(palm_scale > EPSILON, palm_scale, reference)

    normalized = centered / palm_scale[:, None, None]
    normalized = np.clip(normalized, -3.0, 3.0)
    return normalized


def mirror_sequence(sequence: Sequence) -> np.ndarray:
    """Mirror sequence on x-axis for simple left/right augmentation."""
    normalized = normalize_sequence(sequence)
    mirrored = normalized.copy()
    mirrored[:, :, 0] *= -1.0
    return mirrored


def resample_sequence(sequence: np.ndarray, target_length: int = DEFAULT_SEQUENCE_LENGTH) -> np.ndarray:
    """Temporally resample sequence to fixed length via linear interpolation."""
    if target_length <= 1:
        raise ValueError("target_length must be greater than 1")

    if sequence.shape[0] == target_length:
        return sequence.copy()

    src_steps = np.linspace(0.0, 1.0, num=sequence.shape[0], dtype=np.float32)
    dst_steps = np.linspace(0.0, 1.0, num=target_length, dtype=np.float32)

    flat = sequence.reshape(sequence.shape[0], -1)
    resampled_flat = np.zeros((target_length, flat.shape[1]), dtype=np.float32)

    for feature_idx in range(flat.shape[1]):
        resampled_flat[:, feature_idx] = np.interp(dst_steps, src_steps, flat[:, feature_idx])

    return resampled_flat.reshape(target_length, NUM_LANDMARKS, NUM_COORDS)


def sequence_to_feature_vector(
    sequence: Sequence,
    target_length: int = DEFAULT_SEQUENCE_LENGTH,
) -> np.ndarray:
    """
    Build feature vector from landmark sequence.

    Features:
    - Position stream [T, 21, 3]
    - Velocity stream [T, 21, 3]
    - Per-landmark trajectory std [21, 3]
    """
    normalized = normalize_sequence(sequence)
    sampled = resample_sequence(normalized, target_length=target_length)

    velocity = np.diff(sampled, axis=0, prepend=sampled[0:1])
    trajectory_std = np.std(sampled, axis=0)

    feature = np.concatenate(
        [
            sampled.reshape(-1),
            velocity.reshape(-1),
            trajectory_std.reshape(-1),
        ],
        axis=0,
    ).astype(np.float32)

    return feature


def cosine_similarity_matrix(vectors: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between each vector and class centroid."""
    vectors = np.asarray(vectors, dtype=np.float32)
    centroids = np.asarray(centroids, dtype=np.float32)

    vectors_norm = np.linalg.norm(vectors, axis=1, keepdims=True)
    centroids_norm = np.linalg.norm(centroids, axis=1, keepdims=True)

    vectors_safe = vectors / np.maximum(vectors_norm, EPSILON)
    centroids_safe = centroids / np.maximum(centroids_norm, EPSILON)

    return vectors_safe @ centroids_safe.T
