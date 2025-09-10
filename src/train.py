from __future__ import annotations
import os, sys
from pathlib import Path
import json
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, transforms, models
# Make script runnable via `python src/train.py` by adding project root to sys.path
_here = os.path.dirname(__file__)
_root = os.path.abspath(os.path.join(_here, '..'))
if _root not in sys.path:
	sys.path.insert(0, _root)

from src.config.settings import settings
from src.utils.logging.logger import get_logger

DATA_DIR = settings.data_processed
MODEL_PATH = settings.model_path()
IMG_SIZE = settings.img_size
BATCH_SIZE = settings.batch_size
EPOCHS = settings.epochs
LR = settings.lr
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
LOGGER = get_logger("train", level=settings.log_level)


def get_loaders():
	if not DATA_DIR.exists():
		raise SystemExit("Processed data not found. Run src/preprocess.py or place images under data/processed.")
	tfms = {
		"train": transforms.Compose([
			transforms.Resize((IMG_SIZE, IMG_SIZE)),
			transforms.RandomHorizontalFlip(p=0.5),
			transforms.ColorJitter(brightness=0.1, contrast=0.1),
			transforms.ToTensor(),
			transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
		]),
		"val": transforms.Compose([
			transforms.Resize((IMG_SIZE, IMG_SIZE)),
			transforms.ToTensor(),
			transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
		]),
	}

	full = datasets.ImageFolder(DATA_DIR, transform=tfms["train"])
	n = len(full)
	n_val = max(1, int(0.2 * n))
	n_train = n - n_val
	gen = torch.Generator().manual_seed(settings.seed)
	train_set, val_set = torch.utils.data.random_split(full, [n_train, n_val], generator=gen)
	# Ensure val uses val transforms
	val_set.dataset.transform = tfms["val"]

	sampler = None
	if settings.use_balanced_sampler:
		# Build class-balanced sampler to combat class imbalance
		counts = [0] * len(full.classes)
		for idx in train_set.indices:
			_, y = full.samples[idx]
			counts[y] += 1
		class_weights = [1.0 / (c if c > 0 else 1.0) for c in counts]
		sample_weights = [class_weights[full.samples[idx][1]] for idx in train_set.indices]
		sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)

	train_loader = DataLoader(
		train_set,
		batch_size=BATCH_SIZE,
		sampler=sampler,
		shuffle=(sampler is None),
		num_workers=0,
	)
	val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
	return train_loader, val_loader, full.classes


def compute_class_weights(dataset: datasets.ImageFolder, num_classes: int):
	# Count samples per class
	counts = [0] * num_classes
	for _, y in dataset.samples:
		counts[y] += 1
	total = sum(counts)
	# Inverse frequency weights
	inv = [total / (c if c > 0 else 1) for c in counts]
	# Smooth towards uniform using alpha
	alpha = settings.class_weight_alpha
	uniform = [1.0] * num_classes
	weights = [alpha * v + (1 - alpha) * u for v, u in zip(inv, uniform)]
	# Normalize to sum= num_classes (optional)
	s = sum(weights)
	weights = [w * (num_classes / s) for w in weights]
	return torch.tensor(weights, dtype=torch.float32).to(DEVICE)


def build_model(num_classes: int) -> nn.Module:
	m = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
	# Fine-tuning options from settings
	if settings.freeze_backbone:
		for p in m.parameters():
			p.requires_grad = False
		if settings.unfreeze_last_block:
			for p in m.layer4.parameters():
				p.requires_grad = True
	m.fc = nn.Linear(m.fc.in_features, num_classes)
	for p in m.fc.parameters():
		p.requires_grad = True
	return m.to(DEVICE)


def train_one_epoch(model, loader, criterion, optimizer):
	model.train()
	running = 0.0
	for x, y in loader:
		x, y = x.to(DEVICE), y.to(DEVICE)
		optimizer.zero_grad()
		logits = model(x)
		loss = criterion(logits, y)
		loss.backward()
		optimizer.step()
		running += loss.item() * x.size(0)
	return running / len(loader.dataset)


def evaluate(model, loader, criterion):
	model.eval()
	running = 0.0
	correct = 0
	with torch.no_grad():
		for x, y in loader:
			x, y = x.to(DEVICE), y.to(DEVICE)
			logits = model(x)
			loss = criterion(logits, y)
			running += loss.item() * x.size(0)
			pred = torch.argmax(logits, dim=1)
			correct += (pred == y).sum().item()
	return running / len(loader.dataset), correct / len(loader.dataset)


def main():
	# Reproducibility
	torch.manual_seed(settings.seed)
	random.seed(settings.seed)
	np.random.seed(settings.seed)

	train_loader, val_loader, class_names = get_loaders()
	model = build_model(num_classes=len(class_names))

	# Choose imbalance strategy: either balanced sampler or class-weighted loss
	if settings.use_class_weights and not settings.use_balanced_sampler:
		full_ds = datasets.ImageFolder(DATA_DIR)
		class_weights = compute_class_weights(full_ds, num_classes=len(class_names))
		LOGGER.info(f"Using class-weighted loss with weights={class_weights.tolist()}")
		criterion = nn.CrossEntropyLoss(weight=class_weights)
	else:
		if settings.use_balanced_sampler:
			LOGGER.info("Using balanced sampler (no class weights in loss)")
		criterion = nn.CrossEntropyLoss()
	optimizer = optim.Adam((p for p in model.parameters() if p.requires_grad), lr=LR)
	scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

	best_acc = 0.0
	for epoch in range(1, EPOCHS + 1):
		tr_loss = train_one_epoch(model, train_loader, criterion, optimizer)
		val_loss, val_acc = evaluate(model, val_loader, criterion)
		LOGGER.info(f"Epoch {epoch}/{EPOCHS} | train_loss={tr_loss:.4f} val_loss={val_loss:.4f} val_acc={val_acc:.4f}")
		scheduler.step()
		if val_acc > best_acc:
			best_acc = val_acc
			MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
			torch.save(model.state_dict(), MODEL_PATH)
			LOGGER.info(f"Saved best model to {MODEL_PATH}")
			# Save class names alongside the model
			with open(MODEL_PATH.with_name("class_names.json"), "w", encoding="utf-8") as f:
				json.dump(class_names, f)


if __name__ == "__main__":
	main()
