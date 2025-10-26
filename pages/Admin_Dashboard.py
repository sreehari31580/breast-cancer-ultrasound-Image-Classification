"""
Admin Dashboard - System-wide Analytics and Management
"""
import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import analytics
from src.config.settings import settings
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Admin Dashboard | Cancer Detection AI",
    page_icon="🔐",
    layout="wide"
)

# Load CSS
def load_css():
    css_file = Path(__file__).parent.parent / "assets" / "style.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Check authentication and admin status
if not st.session_state.get('authenticated'):
    st.warning("⚠️ Please login first")
    if st.button("🔐 Go to Login"):
        st.switch_page("app.py")
    st.stop()

username = st.session_state.username
is_admin = username in settings.admin_users

if not is_admin:
    st.error("❌ Access Denied: Admin privileges required")
    st.info("👤 You are logged in as a regular user. Please contact an administrator for access.")
    if st.button("🏠 Back to Home"):
        st.switch_page("pages/Home.py")
    st.stop()

# Header
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("""
        <h1>🔐 Admin Dashboard</h1>
        <p style="font-size: 1.1rem; color: var(--text-secondary);">
            System-wide analytics and management console
        </p>
    """, unsafe_allow_html=True)

with col2:
    if st.button("🏠 Back to Home", width="stretch"):
        st.switch_page("pages/Home.py")

st.markdown("<br>", unsafe_allow_html=True)

# Key Performance Indicators
st.markdown("<h2>📊 Key Performance Indicators</h2>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_users = analytics.get_total_users()
    st.metric(
        label="👥 Total Users",
        value=total_users,
        delta="+3 this week"
    )

with col2:
    total_preds = analytics.get_total_predictions()
    st.metric(
        label="🔬 Total Predictions",
        value=total_preds,
        delta="+12 today"
    )

with col3:
    avg_conf = analytics.get_average_confidence()
    st.metric(
        label="🎯 Avg Confidence",
        value=f"{avg_conf:.1%}",
        delta="+1.2%"
    )

with col4:
    active_users_today = analytics.get_active_users_count(days=1)
    st.metric(
        label="⚡ Active Today",
        value=active_users_today,
        delta="Real-time"
    )

with col5:
    st.metric(
        label="🤖 Model Version",
        value=settings.model_version,
        delta="Latest"
    )

st.markdown("<br><br>", unsafe_allow_html=True)

# Charts Section
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div class="glass-card">
            <h3>📈 Predictions Over Time (Last 30 Days)</h3>
        </div>
    """, unsafe_allow_html=True)
    
    daily_preds = analytics.get_daily_predictions(days=30)
    
    if daily_preds:
        import pandas as pd
        df = pd.DataFrame(daily_preds, columns=['date', 'count'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['count'],
            mode='lines+markers',
            name='Predictions',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8, color='#764ba2'),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.1)'
        ))
        
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            height=300,
            xaxis_title="Date",
            yaxis_title="Predictions",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 No prediction data available yet")

with col2:
    st.markdown("""
        <div class="glass-card">
            <h3>🎨 Class Distribution</h3>
        </div>
    """, unsafe_allow_html=True)
    
    class_dist = analytics.get_class_distribution()
    
    if class_dist:
        labels = [item['label'] for item in class_dist]
        values = [item['count'] for item in class_dist]
        
        colors = {
            'Normal': '#43e97b',
            'Benign': '#ffa726',
            'Malignant': '#ef5350'
        }
        color_list = [colors.get(label, '#666') for label in labels]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=color_list),
            hole=0.4,
            textposition='inside',
            textinfo='label+percent'
        )])
        
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            height=300,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 No class distribution data available yet")

st.markdown("<br>", unsafe_allow_html=True)

# User Activity and Model Performance
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div class="glass-card">
            <h3>👥 Top Active Users</h3>
        </div>
    """, unsafe_allow_html=True)
    
    top_users = analytics.get_most_active_users(limit=10)
    
    if top_users:
        import pandas as pd
        df = pd.DataFrame(top_users)
        df.columns = ['User', 'Predictions']
        
        fig = go.Figure(data=[go.Bar(
            x=df['Predictions'],
            y=df['User'],
            orientation='h',
            marker=dict(
                color=df['Predictions'],
                colorscale='Viridis',
                showscale=False
            )
        )])
        
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            height=300,
            xaxis_title="Total Predictions",
            yaxis_title="",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👥 No user activity data available yet")

with col2:
    st.markdown("""
        <div class="glass-card">
            <h3>🎯 Confidence Distribution</h3>
        </div>
    """, unsafe_allow_html=True)
    
    conf_dist = analytics.get_confidence_distribution()
    
    if conf_dist:
        ranges = [item['range'] for item in conf_dist]
        counts = [item['count'] for item in conf_dist]
        
        fig = go.Figure(data=[go.Bar(
            x=ranges,
            y=counts,
            marker=dict(
                color=counts,
                colorscale='Blues',
                showscale=False
            )
        )])
        
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            height=300,
            xaxis_title="Confidence Range",
            yaxis_title="Count",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("🎯 No confidence distribution data available yet")

st.markdown("<br><br>", unsafe_allow_html=True)

# Model Performance Summary
st.markdown("<h2>🤖 Model Performance Summary</h2>", unsafe_allow_html=True)

perf = analytics.get_model_performance_summary()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div class="glass-card text-center">
            <div class="stats-number">{perf.get('total_predictions', 0)}</div>
            <div class="stats-label">Total Analyzed</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    avg_conf = perf.get('average_confidence', 0)
    st.markdown(f"""
        <div class="glass-card text-center">
            <div class="stats-number">{avg_conf:.1%}</div>
            <div class="stats-label">Avg Confidence</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    high_conf = perf.get('high_confidence_count', 0)
    st.markdown(f"""
        <div class="glass-card text-center">
            <div class="stats-number">{high_conf}</div>
            <div class="stats-label">High Confidence (>90%)</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    low_conf = perf.get('low_confidence_count', 0)
    st.markdown(f"""
        <div class="glass-card text-center">
            <div class="stats-number">{low_conf}</div>
            <div class="stats-label">Low Confidence (<70%)</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Recent System Activity
st.markdown("<h2>📋 Recent System Activity</h2>", unsafe_allow_html=True)

recent_preds = analytics.get_recent_predictions(limit=20)

if recent_preds:
    import pandas as pd
    df = pd.DataFrame(recent_preds)
    
    # Format columns
    df['confidence'] = df['confidence'].apply(lambda x: f"{x:.2%}" if x else "N/A")
    df['created_at'] = df['created_at'].apply(lambda x: x[:19] if x else "")
    
    # Rename for display
    display_df = df[['user', 'filename', 'predicted_label', 'confidence', 'created_at']].copy()
    display_df.columns = ['User', 'Filename', 'Prediction', 'Confidence', 'Timestamp']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("📋 No recent predictions available")

st.markdown("<br><br>", unsafe_allow_html=True)

# System Information
st.markdown("<h2>ℹ️ System Information</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="glass-card">
            <h4>🤖 Model Details</h4>
            <ul style="color: var(--text-secondary); line-height: 2;">
                <li><strong>Architecture:</strong> ResNet-18</li>
                <li><strong>Version:</strong> """ + settings.model_version + """</li>
                <li><strong>Classes:</strong> Normal, Benign, Malignant</li>
                <li><strong>Input Size:</strong> 224x224</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="glass-card">
            <h4>👥 User Management</h4>
            <ul style="color: var(--text-secondary); line-height: 2;">
                <li><strong>Total Users:</strong> {total_users}</li>
                <li><strong>Active Users (7d):</strong> {analytics.get_active_users_count(days=7)}</li>
                <li><strong>New Users (30d):</strong> {analytics.get_new_users_count(days=30)}</li>
                <li><strong>Admins:</strong> {len(settings.admin_users)}</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="glass-card">
            <h4>📊 Database Stats</h4>
            <ul style="color: var(--text-secondary); line-height: 2;">
                <li><strong>Predictions:</strong> {total_preds}</li>
                <li><strong>Today:</strong> {analytics.get_predictions_today()}</li>
                <li><strong>This Week:</strong> {analytics.get_predictions_this_week()}</li>
                <li><strong>This Month:</strong> {analytics.get_predictions_this_month()}</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Feedback & Ground Truth Analytics Section
st.markdown("<h2>💬 Feedback & Model Accuracy</h2>", unsafe_allow_html=True)

# Get feedback stats
feedback_stats = analytics.get_feedback_stats()
model_accuracy = analytics.get_model_accuracy_with_feedback()
feedback_by_class = analytics.get_feedback_by_class()

if feedback_stats.get('total', 0) > 0:
    # Feedback Summary KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📝</div>
                <div style="font-size: 2rem; font-weight: bold; color: var(--primary-color);">
                    {feedback_stats.get('total', 0)}
                </div>
                <div style="color: var(--text-muted); font-size: 0.9rem;">Total Feedback</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">✅</div>
                <div style="font-size: 2rem; font-weight: bold; color: #4CAF50;">
                    {model_accuracy.get('accuracy', 0):.1f}%
                </div>
                <div style="color: var(--text-muted); font-size: 0.9rem;">Model Accuracy</div>
                <div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.25rem;">
                    ({model_accuracy.get('sample_size', 0)} reviewed)
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">✅</div>
                <div style="font-size: 2rem; font-weight: bold; color: #4CAF50;">
                    {feedback_stats.get('correct', 0)}
                </div>
                <div style="color: var(--text-muted); font-size: 0.9rem;">Correct</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">❌</div>
                <div style="font-size: 2rem; font-weight: bold; color: #f44336;">
                    {feedback_stats.get('incorrect', 0)}
                </div>
                <div style="color: var(--text-muted); font-size: 0.9rem;">Incorrect</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Class-wise Accuracy
    if feedback_by_class:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div class="glass-card">
                    <h3>🎯 Class-Wise Accuracy</h3>
                </div>
            """, unsafe_allow_html=True)
            
            import pandas as pd
            df_class = pd.DataFrame(feedback_by_class)
            
            fig_class_acc = go.Figure(data=[go.Bar(
                x=df_class['class'],
                y=df_class['accuracy'],
                text=[f"{acc:.1f}%" for acc in df_class['accuracy']],
                textposition='auto',
                marker=dict(
                    color=df_class['accuracy'],
                    colorscale='RdYlGn',
                    showscale=False,
                    line=dict(color='rgba(255,255,255,0.2)', width=1)
                )
            )])
            
            fig_class_acc.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=20, b=0),
                height=300,
                xaxis_title="Predicted Class",
                yaxis_title="Accuracy (%)",
                yaxis=dict(range=[0, 100]),
                showlegend=False
            )
            
            st.plotly_chart(fig_class_acc, use_container_width=True)
        
        with col2:
            st.markdown("""
                <div class="glass-card">
                    <h3>📊 Feedback Distribution</h3>
                </div>
            """, unsafe_allow_html=True)
            
            feedback_dist = pd.DataFrame([
                {'type': 'Correct', 'count': feedback_stats.get('correct', 0), 'color': '#4CAF50'},
                {'type': 'Incorrect', 'count': feedback_stats.get('incorrect', 0), 'color': '#f44336'},
                {'type': 'Uncertain', 'count': feedback_stats.get('uncertain', 0), 'color': '#FF9800'}
            ])
            
            fig_feedback = go.Figure(data=[go.Pie(
                labels=feedback_dist['type'],
                values=feedback_dist['count'],
                hole=0.4,
                marker=dict(colors=feedback_dist['color']),
                textinfo='label+percent+value',
                textposition='outside'
            )])
            
            fig_feedback.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=20, b=0),
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig_feedback, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Flagged Predictions (Incorrect/Uncertain)
    st.markdown("<h3>🚩 Flagged Predictions Requiring Review</h3>", unsafe_allow_html=True)
    
    flagged = analytics.get_flagged_predictions(limit=20)
    
    if flagged:
        import pandas as pd
        df_flagged = pd.DataFrame(flagged)
        
        # Format for display
        df_flagged['confidence'] = df_flagged['confidence'].apply(lambda x: f"{x:.2%}" if x else "N/A")
        df_flagged['created_at'] = df_flagged['created_at'].apply(lambda x: x[:19] if x else "")
        df_flagged['feedback_date'] = df_flagged['feedback_date'].apply(lambda x: x[:19] if x else "")
        
        display_cols = ['id', 'filename', 'predicted_label', 'confidence', 'user', 
                       'feedback_type', 'actual_label', 'notes', 'feedback_date']
        available_cols = [col for col in display_cols if col in df_flagged.columns]
        
        display_df = df_flagged[available_cols].copy()
        display_df.columns = ['ID', 'Filename', 'Predicted', 'Confidence', 'User', 
                              'Feedback', 'Actual Label', 'Notes', 'Feedback Date']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("✅ No flagged predictions - all reviewed predictions were marked as correct!")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Feedback Trend
    st.markdown("<h3>📈 Feedback Submission Trend (30 Days)</h3>", unsafe_allow_html=True)
    
    feedback_trend = analytics.get_feedback_trend(days=30)
    
    if feedback_trend:
        import pandas as pd
        df_trend = pd.DataFrame(feedback_trend, columns=['date', 'count'])
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df_trend['date'],
            y=df_trend['count'],
            mode='lines+markers',
            name='Feedback',
            line=dict(color='#2196F3', width=3),
            marker=dict(size=8, color='#2196F3'),
            fill='tozeroy',
            fillcolor='rgba(33, 150, 243, 0.1)'
        ))
        
        fig_trend.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            height=300,
            xaxis_title="Date",
            yaxis_title="Feedback Count",
            showlegend=False
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("📊 No feedback trend data available yet")

else:
    st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 3rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">💬</div>
            <h3>No Feedback Collected Yet</h3>
            <p style="color: var(--text-muted);">
                Users can submit feedback on predictions to help improve model accuracy.
                Feedback will appear here once submitted.
            </p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Low Confidence Predictions Alert
st.markdown("<h3>⚠️ Low Confidence Predictions (<70%)</h3>", unsafe_allow_html=True)

low_conf_preds = analytics.get_low_confidence_predictions(threshold=0.7, limit=20)

if low_conf_preds:
    import pandas as pd
    df_low_conf = pd.DataFrame(low_conf_preds)
    
    df_low_conf['confidence'] = df_low_conf['confidence'].apply(lambda x: f"{x:.2%}" if x else "N/A")
    df_low_conf['created_at'] = df_low_conf['created_at'].apply(lambda x: x[:19] if x else "")
    df_low_conf['feedback_type'] = df_low_conf['feedback_type'].fillna('Not Reviewed')
    
    display_cols = ['id', 'filename', 'predicted_label', 'confidence', 'user', 'feedback_type', 'created_at']
    available_cols = [col for col in display_cols if col in df_low_conf.columns]
    
    display_df = df_low_conf[available_cols].copy()
    display_df.columns = ['ID', 'Filename', 'Predicted', 'Confidence', 'User', 'Review Status', 'Date']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    st.warning(f"⚠️ **{len(low_conf_preds)} predictions** have confidence below 70% and may require manual review.")
else:
    st.success("✅ All predictions have confidence ≥70%!")

st.markdown("<br><br>", unsafe_allow_html=True)

# Admin Actions
st.markdown("<h2>⚙️ Admin Actions</h2>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📊 Export All Data", width="stretch"):
        st.info("📊 Export feature coming soon!")

with col2:
    if st.button("🔄 Refresh Analytics", width="stretch"):
        st.rerun()

with col3:
    if st.button("📈 Generate Report", width="stretch"):
        st.info("📈 Report generation coming soon!")

with col4:
    if st.button("⚙️ System Settings", width="stretch"):
        st.info("⚙️ Settings page coming soon!")

st.markdown("<br><br>", unsafe_allow_html=True)

# Footer
st.markdown("""
    <div class="glass-card">
        <p style="color: var(--text-muted); text-align: center; margin: 0;">
            🔐 Admin Dashboard | Last Updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """ | Logged in as: <strong>""" + username + """</strong>
        </p>
    </div>
""", unsafe_allow_html=True)
