from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import torch
    from torchvision import models, transforms
except Exception:  # pragma: no cover
    torch = None  # type: ignore[assignment]
    models = None  # type: ignore[assignment]
    transforms = None  # type: ignore[assignment]


@dataclass
class LocalModelBundle:
    model_dir: Path
    model: object
    labels: list[str]
    transform: object

    @classmethod
    def load_if_available(cls, model_dir: Path) -> "LocalModelBundle | None":
        if torch is None or models is None or transforms is None:
            return None

        model_path = model_dir / "model.pt"
        labels_path = model_dir / "labels.json"
        metadata_path = model_dir / "metadata.json"

        if not model_path.exists() or not labels_path.exists() or not metadata_path.exists():
            return None

        labels = json.loads(labels_path.read_text(encoding="utf-8"))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        model = models.mobilenet_v3_small(weights=None)
        model.classifier[3] = torch.nn.Linear(
            model.classifier[3].in_features,
            int(metadata["num_classes"]),
        )
        state_dict = torch.load(model_path, map_location="cpu")
        model.load_state_dict(state_dict)
        model.eval()

        return cls(
            model_dir=model_dir,
            model=model,
            labels=labels,
            transform=transforms.Compose(
                [
                    transforms.ToPILImage(),
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225],
                    ),
                ]
            ),
        )

    def predict(self, frame_rgb: np.ndarray) -> tuple[str, float]:
        tensor = self.transform(frame_rgb).unsqueeze(0)
        with torch.no_grad():
            logits = self.model(tensor)
            probabilities = torch.softmax(logits, dim=1)[0]
        index = int(torch.argmax(probabilities).item())
        confidence = float(probabilities[index].item())
        return self.labels[index], confidence

