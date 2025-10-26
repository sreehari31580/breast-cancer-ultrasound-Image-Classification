"""
User Analytics Page - Personal Statistics and Insights
"""
import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import analytics
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Page config
st.set_page_config(
    page_title="My Analytics | Cancer Detection AI",
    page_icon="📊",
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

# Header
st.markdown(f"""
    <h1>📊 My Analytics</h1>
    <p style="font-size: 1.1rem; color: var(--text-secondary); margin-bottom: 2rem;">
        Personal insights and statistics for <strong>{username}</strong>
    </p>
""", unsafe_allow_html=True)

# Navigation
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("⬅️ Back to Home"):
        st.switch_page("pages/Home.py")
with col2:
    if st.button("🔬 New Prediction"):
        st.switch_page("pages/Prediction.py")

st.markdown("<br>", unsafe_allow_html=True)

# KPI Cards
user_total = analytics.get_user_total_predictions(username)
user_avg_conf = analytics.get_user_average_confidence(username)
activity_stats = analytics.get_user_activity_stats(username)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("My Total Predictions", user_total)

with col2:
    st.metric("My Avg Confidence", f"{user_avg_conf:.1%}")

with col3:
    st.metric("Total Logins", activity_stats.get("total_logins", 0))

with col4:
    st.metric("PDF Downloads", activity_stats.get("total_pdf_downloads", 0))

st.markdown("<br><br>", unsafe_allow_html=True)

# Activity Breakdown
st.markdown("<h2>📈 Activity Breakdown</h2>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    activity_counts = activity_stats.get("activity_counts", {})
    
    if activity_counts:
        df_activity = pd.DataFrame(
            list(activity_counts.items()),
            columns=["Activity", "Count"]
        )
        fig_activity = px.bar(
            df_activity,
            x="Activity",
            y="Count",
            title="My Activities",
            labels={"Count": "Number of Actions"},
            color="Count",
            color_continuous_scale="Greens",
        )
        fig_activity.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#b8b8d1'),
            showlegend=False
        )
        st.plotly_chart(fig_activity, use_container_width=True)
    else:
        st.info("🔬 No activity data yet. Start making predictions!")

with col2:
    st.markdown("""
        <div class="glass-card">
            <h3>👤 Account Information</h3>
    """, unsafe_allow_html=True)
    st.info(f"**📅 Account Created:** {activity_stats.get('registered_at', 'N/A')}")
    st.info(f"**🕒 Last Activity:** {activity_stats.get('last_activity', 'N/A')}")
    st.info(f"**🔬 Total Predictions:** {activity_stats.get('total_predictions', 0)}")
    st.info(f"**📥 PDF Downloads:** {activity_stats.get('total_pdf_downloads', 0)}")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Predictions Over Time
st.markdown("<h2>📅 My Predictions Over Time</h2>", unsafe_allow_html=True)

user_daily = analytics.get_user_daily_predictions(username, days=30)

if user_daily:
    df_user_daily = pd.DataFrame(user_daily, columns=["Date", "Predictions"])
    fig_user_trend = px.line(
        df_user_daily,
        x="Date",
        y="Predictions",
        markers=True,
        title="Daily Predictions (Last 30 Days)",
        labels={"Predictions": "Number of Predictions", "Date": "Date"},
    )
    fig_user_trend.update_traces(line_color="#43e97b", line_width=3)
    fig_user_trend.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#b8b8d1')
    )
    st.plotly_chart(fig_user_trend, use_container_width=True)
else:
    st.info("📊 No prediction history yet.")

st.markdown("<br><br>", unsafe_allow_html=True)

# Class Distribution
st.markdown("<h2>🎯 My Prediction Distribution</h2>", unsafe_allow_html=True)

user_classes = analytics.get_user_predictions_by_class(username)

if user_classes:
    df_user_classes = pd.DataFrame(
        list(user_classes.items()),
        columns=["Class", "Count"]
    )
    
    colors = {
        'Normal': '#43e97b',
        'Benign': '#ffa726',
        'Malignant': '#ef5350'
    }
    df_user_classes['Color'] = df_user_classes['Class'].map(colors)
    
    fig_user_pie = px.pie(
        df_user_classes,
        names="Class",
        values="Count",
        title="My Predictions by Class",
        hole=0.4,
        color="Class",
        color_discrete_map=colors
    )
    fig_user_pie.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#b8b8d1')
    )
    st.plotly_chart(fig_user_pie, use_container_width=True)
else:
    st.info("📊 No class distribution data yet.")

st.markdown("<br><br>", unsafe_allow_html=True)

# Recent Predictions
st.markdown("<h2>🔍 My Recent Predictions</h2>", unsafe_allow_html=True)

user_recent = analytics.get_user_recent_predictions(username, limit=10)

if user_recent:
    df_recent = pd.DataFrame(user_recent)
    df_recent["confidence"] = df_recent["confidence"].apply(lambda x: f"{x:.2%}" if x else "N/A")
    display_cols = ["id", "filename", "predicted_label", "confidence", "created_at", "patient_id"]
    available_cols = [col for col in display_cols if col in df_recent.columns]
    st.dataframe(df_recent[available_cols], hide_index=True)
else:
    st.info("🔬 No recent predictions.")

st.markdown("<br><br>", unsafe_allow_html=True)

# Confidence Trend
st.markdown("<h2>📊 My Confidence Score Trend</h2>", unsafe_allow_html=True)

conf_trend = analytics.get_user_confidence_trend(username, days=30)

if conf_trend:
    df_conf_trend = pd.DataFrame(conf_trend, columns=["Date", "Avg Confidence"])
    df_conf_trend["Avg Confidence"] = df_conf_trend["Avg Confidence"] * 100
    
    fig_conf = px.line(
        df_conf_trend,
        x="Date",
        y="Avg Confidence",
        markers=True,
        title="Average Confidence Score Over Time",
        labels={"Avg Confidence": "Average Confidence (%)", "Date": "Date"},
    )
    fig_conf.update_traces(line_color="#4facfe", line_width=3)
    fig_conf.add_hline(
        y=70,
        line_dash="dash",
        line_color="red",
        annotation_text="70% Threshold",
        annotation_position="right"
    )
    fig_conf.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#b8b8d1')
    )
    st.plotly_chart(fig_conf, use_container_width=True)
else:
    st.info("📊 Not enough data for confidence trend.")

st.markdown("<br><br>", unsafe_allow_html=True)

# User Feedback Section
st.markdown("<h2>💬 My Feedback Contributions</h2>", unsafe_allow_html=True)

user_feedback_stats = analytics.get_user_feedback_stats(username)

if user_feedback_stats['total_feedback'] > 0:
    # Feedback Stats KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📝</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: var(--primary-color);">
                    {user_feedback_stats['total_feedback']}
                </div>
                <div style="color: var(--text-muted); font-size: 0.85rem;">Total Feedback</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #4CAF50;">
                    {user_feedback_stats['correct']}
                </div>
                <div style="color: var(--text-muted); font-size: 0.85rem;">Confirmed Correct</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">❌</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #f44336;">
                    {user_feedback_stats['incorrect']}
                </div>
                <div style="color: var(--text-muted); font-size: 0.85rem;">Marked Incorrect</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #2196F3;">
                    {user_feedback_stats['agreement_rate']:.1f}%
                </div>
                <div style="color: var(--text-muted); font-size: 0.85rem;">Agreement Rate</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Feedback Contribution Message
    contribution_level = ""
    if user_feedback_stats['total_feedback'] >= 50:
        contribution_level = "🏆 **Elite Contributor!** You've provided extensive feedback to help improve the model."
    elif user_feedback_stats['total_feedback'] >= 20:
        contribution_level = "⭐ **Active Contributor!** Your feedback is valuable for model improvement."
    elif user_feedback_stats['total_feedback'] >= 10:
        contribution_level = "✨ **Regular Contributor!** Keep up the great work!"
    else:
        contribution_level = "🌱 **Getting Started!** Every piece of feedback helps!"
    
    st.info(contribution_level)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Feedback History Table
    st.markdown("<h3>📋 My Feedback History</h3>", unsafe_allow_html=True)
    
    user_feedback_history = analytics.get_user_feedback_history(username, limit=50)
    
    if user_feedback_history:
        df_history = pd.DataFrame(user_feedback_history)
        
        # Format for display
        df_history['confidence'] = df_history['confidence'].apply(lambda x: f"{x:.2%}" if x else "N/A")
        df_history['created_at'] = df_history['created_at'].apply(lambda x: x[:19] if x else "")
        df_history['feedback_type'] = df_history['feedback_type'].apply(
            lambda x: f"{'✅' if x == 'correct' else '❌' if x == 'incorrect' else '❓'} {x.title()}"
        )
        
        display_cols = ['prediction_id', 'filename', 'predicted_label', 'confidence', 
                       'feedback_type', 'actual_label', 'notes', 'created_at']
        available_cols = [col for col in display_cols if col in df_history.columns]
        
        display_df = df_history[available_cols].copy()
        display_df.columns = ['Pred ID', 'Filename', 'Predicted', 'Confidence', 
                              'My Feedback', 'Actual Label', 'My Notes', 'Date']
        
        st.dataframe(
            display_df,
            hide_index=True
        )
    else:
        st.info("No feedback history available")
    
else:
    st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">💬</div>
            <h3>No Feedback Submitted Yet</h3>
            <p style="color: var(--text-muted); max-width: 500px; margin: 1rem auto;">
                After making predictions, you can provide feedback to help improve the model's accuracy.
                Your contributions will appear here!
            </p>
        </div>
    """, unsafe_allow_html=True)

