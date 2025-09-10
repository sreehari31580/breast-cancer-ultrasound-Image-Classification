import io
from pathlib import Path
import streamlit as st
from PIL import Image
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as T

from src.utils.db_utils import (
	init_db,
	ensure_user_table,
	create_user,
	authenticate_user,
	log_prediction,
	fetch_predictions,
	update_prediction_report_path,
)
from src.utils.reporting.pdf_report import generate_pdf_report
from src.utils.grad_cam import GradCAM, overlay_heatmap
from src.config.settings import settings
from src.utils.logging.logger import get_logger

MODEL_PATH = settings.model_path()
LOGGER = get_logger("app", settings.log_level)
CLASS_LABELS = ["Normal", "Benign", "Malignant"]
CLASS_NAMES_PATH = settings.class_names_path()
if CLASS_NAMES_PATH.exists():
	try:
		import json
		CLASS_LABELS = json.loads(CLASS_NAMES_PATH.read_text(encoding="utf-8"))
	except Exception:
		pass


@st.cache_resource(show_spinner=False)
def load_model():
	from torchvision.models import resnet18, ResNet18_Weights
	try:
		model = resnet18(weights=ResNet18_Weights.DEFAULT)
	except Exception:
		model = resnet18(weights=None)
	model.fc = nn.Linear(model.fc.in_features, len(CLASS_LABELS))
	if MODEL_PATH.exists():
		state = torch.load(MODEL_PATH, map_location="cpu")
		model.load_state_dict(state)
	model.eval()
	return model


class CenterCropSquare:
	def __call__(self, img: Image.Image) -> Image.Image:
		w, h = img.size
		m = min(w, h)
		left = (w - m) // 2
		top = (h - m) // 2
		return img.crop((left, top, left + m, top + m))


def get_transforms():
	return T.Compose([
		CenterCropSquare(),
		T.Resize((224, 224)),
		T.ToTensor(),
		T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
	])


def main():
	st.set_page_config(page_title="Breast Cancer Detection", layout="centered")
	st.title("Breast Cancer Detection (PyTorch + Grad-CAM)")

	# DB init
	init_db()
	ensure_user_table()

	# Auth UI
	auth_tab, register_tab = st.tabs(["Login", "Register"])
	with register_tab:
		st.subheader("Create an account")
		new_user = st.text_input("Username", key="reg_user")
		new_pass = st.text_input("Password", type="password", key="reg_pass")
		if st.button("Register"):
			if not new_user or not new_pass:
				st.warning("Please provide username and password.")
			elif create_user(new_user, new_pass):
				st.success("User created. You can log in now.")
			else:
				st.error("Username already exists.")

	with auth_tab:
		st.subheader("Login")
		user = st.text_input("Username", key="login_user")
		pwd = st.text_input("Password", type="password", key="login_pass")
		do_login = st.button("Login")

	if do_login:
		if authenticate_user(user, pwd):
			st.session_state["auth"] = True
			st.session_state["username"] = user
		else:
			st.error("Invalid credentials.")

	if not st.session_state.get("auth"):
		st.info("Please log in to continue.")
		return

	st.success(f"Logged in as {st.session_state['username']}")

	model = load_model()
	transforms = get_transforms()

	uploaded = st.file_uploader("Upload an ultrasound image", type=["png", "jpg", "jpeg"]) 
	if uploaded is None:
		return

	image = Image.open(uploaded).convert("RGB")
	st.image(image, caption="Uploaded Image", use_column_width=True)

	# Optional patient ID for report linkage
	patient_id = st.text_input("Patient ID (optional)")

	# Prepare input
	img_tensor = transforms(image).unsqueeze(0)
	with torch.no_grad():
		logits = model(img_tensor)
		probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
	pred_idx = int(np.argmax(probs))
	pred_label = CLASS_LABELS[pred_idx]
	confidence = float(probs[pred_idx])

	st.subheader(f"Prediction: {pred_label} ({confidence:.2%})")
	with st.expander("Probabilities"):
		st.write({CLASS_LABELS[i]: float(p) for i, p in enumerate(probs)})

	# Grad-CAM
	cam = GradCAM(model, target_layer_name="layer4")
	heatmap = cam(img_tensor, class_idx=pred_idx)
	overlay = overlay_heatmap(np.array(image), heatmap, alpha=0.4)
	st.image(overlay, caption="Grad-CAM", use_column_width=True)

	# Log prediction (capture id to attach report)
	prediction_id = None
	try:
		prob_map = {CLASS_LABELS[i]: float(probs[i]) for i in range(len(CLASS_LABELS))}
		prediction_id = log_prediction(
			uploaded.name,
			pred_label,
			confidence,
			user=st.session_state["username"],
			model_version=settings.model_version,
			probabilities=prob_map,
			patient_id=patient_id or None,
		)
	except Exception as e:
		LOGGER.exception("Log prediction failed")
		st.warning(f"Could not log prediction: {e}")

	# Prepare temporary files for report generation
	reports_dir = settings.reports_dir
	reports_dir.mkdir(parents=True, exist_ok=True)
	orig_tmp_path = reports_dir / f"_orig_{uploaded.name}"
	cam_tmp_path = reports_dir / f"_gradcam_{uploaded.name}"
	try:
		image.save(orig_tmp_path)
		Image.fromarray(overlay).save(cam_tmp_path)
	except Exception:
		orig_tmp_path = None
		cam_tmp_path = None

	# One-click PDF report
	if st.button("Download PDF Report"):
		try:
			pdf_path = generate_pdf_report(
				output_dir=reports_dir,
				original_image_path=orig_tmp_path,
				gradcam_image_path=cam_tmp_path,
				filename=uploaded.name,
				predicted_label=pred_label,
				probabilities={CLASS_LABELS[i]: float(probs[i]) for i in range(len(CLASS_LABELS))},
				model_version=settings.model_version,
				username=st.session_state["username"],
				patient_id=patient_id or None,
			)
			if prediction_id is not None:
				update_prediction_report_path(prediction_id, str(pdf_path))
			with open(pdf_path, "rb") as f:
				st.download_button(
					label="Download Report PDF",
					data=f,
					file_name=pdf_path.name,
					mime="application/pdf",
				)
		except Exception as e:
			LOGGER.exception("PDF generation failed")
			st.error(f"Failed to generate report: {e}")

	with st.expander("Recent predictions"):
		rows = fetch_predictions(limit=20)
		if rows:
			st.dataframe(rows)
		else:
			st.write("No predictions yet.")


if __name__ == "__main__":
	main()
