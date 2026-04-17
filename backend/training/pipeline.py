from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn, optim

from backend.training.dataset import build_image_dataloaders
from backend.training.model import create_sign_model


@dataclass
class TrainingConfig:
    dataset_root: Path
    artifact_dir: Path
    epochs: int = 5
    batch_size: int = 16
    learning_rate: float = 1e-3


def train_model(config: TrainingConfig) -> dict[str, float | str]:
    train_loader, val_loader, _, classes = build_image_dataloaders(config.dataset_root, config.batch_size)
    model = create_sign_model(len(classes))
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=config.learning_rate)

    best_val_accuracy = 0.0
    config.artifact_dir.mkdir(parents=True, exist_ok=True)

    for _ in range(config.epochs):
        model.train()
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

        val_accuracy = evaluate_loader(model, val_loader)
        best_val_accuracy = max(best_val_accuracy, val_accuracy)

    torch.save(model.state_dict(), config.artifact_dir / "model.pt")
    (config.artifact_dir / "labels.json").write_text(json.dumps(classes, indent=2), encoding="utf-8")
    (config.artifact_dir / "metadata.json").write_text(
        json.dumps(
            {
                "num_classes": len(classes),
                "epochs": config.epochs,
                "batch_size": config.batch_size,
                "learning_rate": config.learning_rate,
                "best_val_accuracy": best_val_accuracy,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "artifact_dir": str(config.artifact_dir),
        "best_val_accuracy": round(best_val_accuracy, 4),
    }


def evaluate_model(dataset_root: Path, artifact_dir: Path, batch_size: int = 16) -> dict[str, float | str]:
    _, _, test_loader, classes = build_image_dataloaders(dataset_root, batch_size)
    model = create_sign_model(len(classes))
    state_dict = torch.load(artifact_dir / "model.pt", map_location="cpu")
    model.load_state_dict(state_dict)
    accuracy = evaluate_loader(model, test_loader)
    return {"artifact_dir": str(artifact_dir), "test_accuracy": round(accuracy, 4)}


def evaluate_loader(model, loader) -> float:
    model.eval()
    total = 0
    correct = 0
    with torch.no_grad():
        for inputs, labels in loader:
            outputs = model(inputs)
            predictions = outputs.argmax(dim=1)
            total += labels.size(0)
            correct += (predictions == labels).sum().item()
    return (correct / total) if total else 0.0

