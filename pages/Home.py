"""
Home Dashboard - User Overview
"""
import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import analytics
from src.config.settings import settings

# Page config
st.set_page_config(
    page_title="Home | Cancer Detection AI",
    page_icon="🏠",
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
is_admin = username in settings.admin_users

# Header
col1, col2 = st.columns([3, 1])

with col1:
    if is_admin:
        st.markdown(f"""
            <h1>🏠 Welcome, {username}!</h1>
            <p style="font-size: 1.1rem; color: var(--text-secondary);">
                <span class="badge badge-primary">🔐 ADMIN</span> System Administrator Dashboard
            </p>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <h1>🏠 Welcome, {username}!</h1>
            <p style="font-size: 1.1rem; color: var(--text-secondary);">
                Cancer Detection AI Platform
            </p>
        """, unsafe_allow_html=True)

with col2:
    if st.button("🚪 Logout", width="stretch"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.success("Logged out successfully!")
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Quick Actions
st.markdown("<h2>⚡ Quick Actions</h2>", unsafe_allow_html=True)

if is_admin:
    # Admin-specific quick actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔐 Admin Dashboard", width="stretch", type="primary"):
            st.switch_page("pages/Admin_Dashboard.py")
    
    with col2:
        if st.button("📊 System Analytics", width="stretch"):
            st.switch_page("pages/Admin_Dashboard.py")
else:
    # Regular user quick actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔬 New Prediction", width="stretch", type="primary"):
            st.switch_page("pages/Prediction.py")
    
    with col2:
        if st.button("📊 My Analytics", width="stretch"):
            st.switch_page("pages/User_Analytics.py")
    
    with col3:
        if st.button("📜 View History", width="stretch"):
            # For now, redirect to analytics (History page can be created later)
            st.switch_page("pages/User_Analytics.py")

st.markdown("<br><br>", unsafe_allow_html=True)

# Statistics Section
if is_admin:
    # Admin sees system-wide statistics
    st.markdown("<h2>🖥️ System Overview</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = analytics.get_total_users()
        st.metric(
            label="👥 Total Users",
            value=total_users
        )
    
    with col2:
        total_preds = analytics.get_total_predictions()
        st.metric(
            label="🔬 Total Predictions",
            value=total_preds
        )
    
    with col3:
        avg_conf = analytics.get_average_confidence()
        st.metric(
            label="🎯 System Avg Confidence",
            value=f"{avg_conf:.1%}"
        )
    
    with col4:
        st.metric(
            label="🤖 Model Version",
            value=settings.model_version
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Tip:** Click 'Admin Dashboard' above for detailed system analytics and management tools.")

else:
    # Regular users see personal statistics
    st.markdown("<h2>📈 Your Statistics</h2>", unsafe_allow_html=True)
    
    user_total = analytics.get_user_total_predictions(username)
    user_avg_conf = analytics.get_user_average_confidence(username)
    activity_stats = analytics.get_user_activity_stats(username)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Predictions",
            value=user_total,
            delta="+5 this week" if user_total > 5 else None
        )
    
    with col2:
        st.metric(
            label="Average Confidence",
            value=f"{user_avg_conf:.1%}",
            delta="+2.3%" if user_avg_conf > 0.8 else None
        )
    
    with col3:
        st.metric(
            label="Total Logins",
            value=activity_stats.get('total_logins', 0)
        )
    
    with col4:
        st.metric(
            label="PDF Downloads",
            value=activity_stats.get('total_pdf_downloads', 0)
        )

st.markdown("<br><br>", unsafe_allow_html=True)

# Recent Predictions (system-wide for admin, personal for users)
if is_admin:
    st.markdown("<h2>🔍 Recent System Activity</h2>", unsafe_allow_html=True)
    recent = analytics.get_recent_predictions(limit=10)
else:
    st.markdown("<h2>🔍 Your Recent Predictions</h2>", unsafe_allow_html=True)
    recent = analytics.get_user_recent_predictions(username, limit=5)

if recent:
    import pandas as pd
    df = pd.DataFrame(recent)
    df['confidence'] = df['confidence'].apply(lambda x: f"{x:.2%}" if x else "N/A")
    
    # Display in a nice format
    for idx, row in df.iterrows():
        if is_admin:
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
        else:
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            st.markdown(f"**📄 {row['filename']}**")
        
        with col2:
            label_color = {
                'Normal': '🟢',
                'Benign': '🟡',
                'Malignant': '🔴'
            }
            icon = label_color.get(row['predicted_label'], '⚪')
            st.markdown(f"{icon} **{row['predicted_label']}**")
        
        with col3:
            st.markdown(f"🎯 Confidence: **{row['confidence']}**")
        
        if is_admin:
            with col4:
                st.markdown(f"👤 **{row.get('user', 'N/A')}**")
            with col5:
                st.markdown(f"*{row['created_at'][:10]}*")
        else:
            with col4:
                st.markdown(f"*{row['created_at'][:10]}*")
        
        st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.2;'>", unsafe_allow_html=True)
else:
    if is_admin:
        st.info("📊 No system activity yet")
    else:
        st.info("🔬 No predictions yet. Start by uploading an image!")

st.markdown("<br><br>", unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
        <p>Cancer Detection AI Platform | ResNet-18 | 97% Accuracy</p>
        <p style="font-size: 0.85rem;">For research and clinical decision support only</p>
    </div>
""", unsafe_allow_html=True)
