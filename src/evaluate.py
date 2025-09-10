from __future__ import annotations
import os, sys
from pathlib import Path
import json

# Make script runnable via `python src/evaluate.py` by adding project root to sys.path
_here = os.path.dirname(__file__)
_root = os.path.abspath(os.path.join(_here, '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

from src.config.settings import settings


def get_loader():
    tfm = transforms.Compose([
        transforms.Resize((settings.img_size, settings.img_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    ds = datasets.ImageFolder(settings.data_processed, transform=tfm)
    return DataLoader(ds, batch_size=32, shuffle=False), ds.classes


def build_model(num_classes: int) -> nn.Module:
    m = models.resnet18(weights=None)
    m.fc = nn.Linear(m.fc.in_features, num_classes)
    return m


def main():
    loader, classes = get_loader()
    model = build_model(len(classes))
    state = torch.load(settings.model_path(), map_location="cpu")
    model.load_state_dict(state)
    model.eval()

    y_true, y_pred = [], []
    with torch.no_grad():
        for x, y in loader:
            logits = model(x)
            pred = torch.argmax(logits, dim=1)
            y_true.extend(y.tolist())
            y_pred.extend(pred.tolist())

    print(classification_report(y_true, y_pred, target_names=classes))

    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes, ax=ax)
    ax.set_xlabel('Predicted')
    ax.set_ylabel('True')
    out = Path('reports/confusion_matrix.png')
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out)
    print(f"Saved confusion matrix to {out}")


if __name__ == "__main__":
    main()
