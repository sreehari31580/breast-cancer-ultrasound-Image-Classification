"""
Prediction Page - Upload and Analyze Ultrasound Images
"""
import streamlit as st
from pathlib import Path
import sys
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import io
from PIL import Image
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as T

from src.utils.db_utils import log_prediction, update_prediction_report_path, log_user_activity
from src.utils.reporting.pdf_report import generate_pdf_report
from src.utils.grad_cam import GradCAM, overlay_heatmap
from src.config.settings import settings
from src.utils.logging.logger import get_logger

# Page config
st.set_page_config(
    page_title="Prediction | Cancer Detection AI",
    page_icon="🔬",
    layout="wide"
)

# Load CSS
def load_css():
    css_file = Path(__file__).parent.parent / "assets" / "style.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Check authentication
if not st.session_state.get('authenticated'):
    st.warning("⚠️ Please login first")
    if st.button("🔐 Go to Login"):
        st.switch_page("app.py")
    st.stop()

username = st.session_state.username

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

# Header
st.markdown("""
    <h1>🔬 AI-Powered Image Analysis</h1>
    <p style="font-size: 1.1rem; color: var(--text-secondary); margin-bottom: 2rem;">
        Upload a breast ultrasound image for instant AI analysis with explainable Grad-CAM visualization
    </p>
""", unsafe_allow_html=True)

# Navigation
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("⬅️ Back to Home"):
        st.switch_page("pages/Home.py")
with col2:
    if st.button("📊 View Analytics"):
        st.switch_page("pages/User_Analytics.py")

st.markdown("<br>", unsafe_allow_html=True)

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
        <div class="glass-card">
            <h3>📤 Upload Image</h3>
            <p style="color: var(--text-muted); margin-bottom: 1rem;">
                Supported formats: PNG, JPG, JPEG
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "Choose an ultrasound image",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed"
    )
    
    if uploaded:
        image = Image.open(uploaded).convert("RGB")
        st.image(image, caption="📸 Uploaded Image")
        
        # Patient ID
        patient_id = st.text_input("🏥 Patient ID (optional)", placeholder="Enter patient identifier")

with col2:
    if uploaded:
        st.markdown("""
            <div class="glass-card">
                <h3>🤖 AI Analysis</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Load model and make prediction
        with st.spinner("🔄 Analyzing image..."):
            model = load_model()
            transforms = get_transforms()
            
            # Prepare input and time the inference
            img_tensor = transforms(image).unsqueeze(0)
            start_time = time.time()
            with torch.no_grad():
                logits = model(img_tensor)
                probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
            end_time = time.time()
            processing_time_ms = int((end_time - start_time) * 1000)
            
            pred_idx = int(np.argmax(probs))
            pred_label = CLASS_LABELS[pred_idx]
            confidence = float(probs[pred_idx])
        
        # Display results with animation
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Prediction result
        label_config = {
            'Normal': {'emoji': '🟢', 'color': '#43e97b'},
            'Benign': {'emoji': '🟡', 'color': '#ffa726'},
            'Malignant': {'emoji': '🔴', 'color': '#ef5350'}
        }
        
        config = label_config.get(pred_label, {'emoji': '⚪', 'color': '#666'})
        
        st.markdown(f"""
            <div class="glass-card animated-pulse" style="border-left: 4px solid {config['color']};">
                <h2 style="margin: 0;">{config['emoji']} {pred_label}</h2>
                <p style="font-size: 1.5rem; color: var(--text-secondary); margin: 0.5rem 0;">
                    Confidence: <strong>{confidence:.1%}</strong>
                </p>
                <p style="color: var(--text-muted); font-size: 0.9rem;">
                    ⚡ Processed in {processing_time_ms}ms
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Probabilities
        with st.expander("📊 View All Probabilities", expanded=True):
            prob_dict = {CLASS_LABELS[i]: float(probs[i]) for i in range(len(CLASS_LABELS))}
            
            for label, prob in prob_dict.items():
                label_cfg = label_config.get(label, {'emoji': '⚪', 'color': '#666'})
                st.markdown(f"""
                    <div style="margin: 0.75rem 0;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span>{label_cfg['emoji']} <strong>{label}</strong></span>
                            <span style="color: {label_cfg['color']}; font-weight: 600;">{prob:.1%}</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {prob*100}%; background: linear-gradient(90deg, {label_cfg['color']}, {label_cfg['color']}AA);"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Grad-CAM
        st.markdown("""
            <div class="glass-card">
                <h3>🔍 Explainable AI - Grad-CAM Heatmap</h3>
                <p style="color: var(--text-muted); margin-bottom: 1rem;">
                    Visualizing which regions influenced the AI's decision
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.spinner("🎨 Generating Grad-CAM visualization..."):
            cam = GradCAM(model, target_layer_name="layer4")
            heatmap = cam(img_tensor, class_idx=pred_idx)
            overlay = overlay_heatmap(np.array(image), heatmap, alpha=0.4)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.image(image, caption="Original Image")
        with col_b:
            st.image(overlay, caption="Grad-CAM Overlay")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Log prediction
        prediction_id = None
        try:
            prob_map = {CLASS_LABELS[i]: float(probs[i]) for i in range(len(CLASS_LABELS))}
            prediction_id = log_prediction(
                uploaded.name,
                pred_label,
                confidence,
                user=username,
                model_version=settings.model_version,
                probabilities=prob_map,
                patient_id=patient_id or None,
                processing_time_ms=processing_time_ms,
            )
            log_user_activity(username, "prediction")
        except Exception as e:
            LOGGER.exception("Log prediction failed")
            st.warning(f"⚠️ Could not log prediction: {e}")
        
        # Save temporary files
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
        
        # PDF Report
        st.markdown("""
            <div class="glass-card">
                <h3>📄 Clinical Report</h3>
                <p style="color: var(--text-muted);">
                    Download a comprehensive PDF report for medical records
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("📥 Download PDF Report", width="stretch", type="primary"):
                try:
                    pdf_path = generate_pdf_report(
                        output_dir=reports_dir,
                        original_image_path=orig_tmp_path,
                        gradcam_image_path=cam_tmp_path,
                        filename=uploaded.name,
                        predicted_label=pred_label,
                        probabilities=prob_dict,
                        model_version=settings.model_version,
                        username=username,
                        patient_id=patient_id or None,
                    )
                    if prediction_id is not None:
                        update_prediction_report_path(prediction_id, str(pdf_path))
                    
                    # Log PDF download
                    try:
                        log_user_activity(username, "pdf_download")
                    except Exception:
                        pass
                    
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Report PDF",
                            data=f,
                            file_name=pdf_path.name,
                            mime="application/pdf",
                            width="stretch"
                        )
                    st.success("✅ Report generated successfully!")
                except Exception as e:
                    LOGGER.exception("PDF generation failed")
                    st.error(f"❌ Failed to generate report: {e}")
        
        # Feedback Section
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div class="glass-card">
                <h3>💬 Prediction Feedback</h3>
                <p style="color: var(--text-muted); margin-bottom: 1rem;">
                    Your feedback helps us improve the model's accuracy!
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Check if feedback already submitted
        from src.utils.db_utils import get_prediction_feedback, submit_prediction_feedback
        
        existing_feedback = None
        if prediction_id:
            existing_feedback = get_prediction_feedback(prediction_id)
        
        if existing_feedback:
            # Show existing feedback
            feedback_type = existing_feedback['feedback_type']
            emoji_map = {'correct': '✅', 'incorrect': '❌', 'uncertain': '❓'}
            st.success(f"{emoji_map.get(feedback_type, '💬')} You marked this prediction as **{feedback_type.upper()}** on {existing_feedback['created_at'][:19]}")
            
            if existing_feedback['actual_label']:
                st.info(f"📋 You indicated the actual class was: **{existing_feedback['actual_label']}**")
            
            if existing_feedback['notes']:
                st.text_area("Your Notes:", value=existing_feedback['notes'], disabled=True, height=80)
        else:
            # Feedback form
            st.markdown("**Was this prediction correct?**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                correct_btn = st.button("✅ Correct", width="stretch", use_container_width=True)
            with col2:
                incorrect_btn = st.button("❌ Incorrect", width="stretch", use_container_width=True)
            with col3:
                uncertain_btn = st.button("❓ Uncertain", width="stretch", use_container_width=True)
            
            # Handle feedback submission
            feedback_submitted = False
            feedback_type = None
            
            if correct_btn:
                feedback_type = 'correct'
                feedback_submitted = True
            elif incorrect_btn:
                feedback_type = 'incorrect'
                feedback_submitted = True
            elif uncertain_btn:
                feedback_type = 'uncertain'
                feedback_submitted = True
            
            if feedback_submitted and prediction_id:
                # Show additional options for incorrect/uncertain
                if feedback_type in ['incorrect', 'uncertain']:
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    actual_label = st.selectbox(
                        "What is the actual class? (Optional)",
                        options=["", "Normal", "Benign", "Malignant"],
                        key=f"actual_label_{prediction_id}"
                    )
                    
                    notes = st.text_area(
                        "Additional notes (Optional):",
                        placeholder="Describe why you think the prediction was incorrect or uncertain...",
                        height=100,
                        key=f"notes_{prediction_id}"
                    )
                    
                    if st.button("Submit Feedback", type="primary", use_container_width=True):
                        try:
                            submit_prediction_feedback(
                                prediction_id=prediction_id,
                                user=username,
                                feedback_type=feedback_type,
                                actual_label=actual_label if actual_label else None,
                                notes=notes if notes else None
                            )
                            st.success("✅ Thank you for your feedback! It will help improve the model.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to submit feedback: {e}")
                else:
                    # For 'correct', submit immediately
                    try:
                        submit_prediction_feedback(
                            prediction_id=prediction_id,
                            user=username,
                            feedback_type=feedback_type,
                            actual_label=None,
                            notes=None
                        )
                        st.success("✅ Thank you for confirming! Your feedback has been recorded.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to submit feedback: {e}")
    
    else:
        st.markdown("""
            <div class="glass-card" style="text-align: center; padding: 4rem 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">📤</div>
                <h3>Upload an Image to Begin</h3>
                <p style="color: var(--text-muted);">
                    Select an ultrasound image from the left panel
                </p>
            </div>
        """, unsafe_allow_html=True)

# Info section
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
    <div class="glass-card">
        <h3>ℹ️ About the Analysis</h3>
        <p style="color: var(--text-secondary); line-height: 1.6;">
            This AI model uses <strong>ResNet-18</strong> architecture trained on breast ultrasound images to classify into three categories:
        </p>
        <ul style="color: var(--text-secondary); line-height: 1.8;">
            <li><strong>🟢 Normal:</strong> Healthy tissue with no abnormalities detected</li>
            <li><strong>🟡 Benign:</strong> Non-cancerous tumor or abnormality</li>
            <li><strong>🔴 Malignant:</strong> Cancerous tumor requiring further clinical evaluation</li>
        </ul>
        <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 1rem;">
            ⚠️ <strong>Disclaimer:</strong> This tool is for research and clinical decision support only. 
            Always consult with qualified healthcare professionals for diagnosis and treatment.
        </p>
    </div>
""", unsafe_allow_html=True)
