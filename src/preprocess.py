from __future__ import annotations
from pathlib import Path
from PIL import Image

RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")


def center_crop_resize(img: Image.Image, size: int = 224) -> Image.Image:
	w, h = img.size
	m = min(w, h)
	left = (w - m) // 2
	top = (h - m) // 2
	img = img.crop((left, top, left + m, top + m))
	return img.resize((size, size))


def preprocess():
	PROC_DIR.mkdir(parents=True, exist_ok=True)
	for cls in ["Normal", "Benign", "Malignant"]:
		src = RAW_DIR / cls
		dst = PROC_DIR / cls
		dst.mkdir(parents=True, exist_ok=True)
		if not src.exists():
			print(f"Missing: {src}")
			continue
		files = []
		for ext in ("*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"):
			files += list(src.glob(ext))
		for fp in files:
			try:
				img = Image.open(fp).convert("RGB")
				img = center_crop_resize(img)
				img.save(dst / fp.name)
			except Exception as e:
				print(f"Failed {fp}: {e}")


if __name__ == "__main__":
	preprocess()
