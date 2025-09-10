# Cancer Detection App (PyTorch + Grad‑CAM)

An end‑to‑end breast ultrasound classification app. Train a PyTorch CNN (ResNet‑18), run predictions in a Streamlit UI with Grad‑CAM explainability, generate clinical‑style PDF reports, and keep an auditable SQLite history with user accounts.

## Features
- Three‑class classification: Normal, Benign, Malignant
- Streamlit UI with login/registration (bcrypt + SQLite)
- Grad‑CAM heatmaps (targeting ResNet layer4) with overlay
- One‑click PDF report: image, Grad‑CAM, probabilities, model version, timestamp, disclaimer
- CLI for preprocess/train/evaluate (Typer)
- Evaluation with classification report and confusion matrix
- Config via Pydantic Settings; structured logging

## Tech stack
- Python 3.13, Windows‑friendly
- PyTorch + torchvision (ResNet‑18)
- Streamlit, Pillow, OpenCV‑headless
- scikit‑learn, numpy, pandas, matplotlib/seaborn
- SQLite + bcrypt
- pydantic/pydantic‑settings, typer
- fpdf2 (PDF generation)

## Repository layout
```
cancer_detection_app/
├─ app.py                  # Streamlit UI
├─ cli.py                  # CLI: preprocess/train/evaluate
├─ requirements.txt        # Runtime deps
├─ pyproject.toml          # Tooling (ruff/black/pytest)
├─ src/
│  ├─ config/settings.py   # Centralized settings
│  ├─ preprocess.py        # Center‑crop + resize to 224x224
│  ├─ train.py             # Train ResNet‑18, save model.pt & class_names.json
│  ├─ evaluate.py          # Metrics + confusion matrix
│  └─ utils/
│     ├─ grad_cam.py       # Grad‑CAM hooks & heatmap overlay
│     ├─ db_utils.py       # SQLite users + predictions
│     └─ reporting/pdf_report.py  # PDF generator
├─ data/
│  ├─ raw/                 # Put Normal/, Benign/, Malignant/ here
│  └─ processed/           # Auto‑generated
├─ models/                 # model.pt, class_names.json
├─ reports/                # PDFs, Grad‑CAM images, confusion_matrix.png
└─ tests/
	 └─ test_grad_cam.py     # Smoke test
```

## Quickstart (Windows PowerShell)
1) Create a virtual environment and install deps:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

2) Prepare your data:
- Place images under:
	- `data/raw/Normal/`
	- `data/raw/Benign/`
	- `data/raw/Malignant/`

3) (Optional) Preprocess to square+resize:
```powershell
python .\src\preprocess.py
```

4) Train the model:
```powershell
python -m src.train   # or: python .\src\train.py
```
Artifacts are saved to `models/model.pt` and `models/class_names.json`.

5) Evaluate (saves confusion matrix to `reports/`):
```powershell
python -m src.evaluate
```

6) Run the app:
```powershell
streamlit run .\app.py
```
Register a user, log in, upload an image, see prediction + Grad‑CAM, and click “Download PDF Report”.

## Configuration
Tunables live in `src/config/settings.py` or via `.env`:
- Paths: `data_raw`, `data_processed`, `models_dir`, `reports_dir`
- Training: `img_size`, `batch_size`, `epochs`, `lr`, `seed`
- Fine‑tuning: `freeze_backbone`, `unfreeze_last_block`
- Imbalance: `use_balanced_sampler` | `use_class_weights`, `class_weight_alpha`
- App: `db_path`, `model_version`
- Logging: `log_level`

## Development
- Code style: black; Lint: ruff; Tests: pytest.
- Run tests:
```powershell
pytest -q
```

## Troubleshooting
- ModuleNotFoundError: Prefer module mode: `python -m src.train` / `python -m src.evaluate`.
- Torch/vision install issues: ensure versions from `requirements.txt` (Windows + Python 3.13).
- Streamlit DB errors: if schema changed, restart the app (we auto‑migrate columns).

## Security & disclaimers
- Authentication is basic (SQLite + bcrypt); for production, add roles, rate limiting, HTTPS, and secret management.
- Reports include a disclaimer and are for decision support only.

## License
Specify a license (e.g., MIT). See `LICENSE` file if included.
