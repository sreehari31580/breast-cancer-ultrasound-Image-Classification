from __future__ import annotations
import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights
from src.utils.grad_cam import GradCAM


def test_grad_cam_runs():
    model = resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 3)
    cam = GradCAM(model, target_layer_name="layer4")
    x = torch.randn(1, 3, 224, 224)
    out = cam(x, class_idx=0)
    assert out.shape == (7, 7) or len(out.shape) == 2
