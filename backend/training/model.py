from __future__ import annotations

import torch
from torchvision import models


def create_sign_model(num_classes: int):
    model = models.mobilenet_v3_small(weights=None)
    model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, num_classes)
    return model

