"""
Cancer Detection App - Modern UI Landing Page
Multi-page architecture with stunning visuals
"""
import streamlit as st
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Cancer Detection AI | Advanced Medical Imaging",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom CSS
def load_css():
    css_file = Path(__file__).parent / "assets" / "style.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Landing Page
def show_landing():
    # Hero Section
    st.markdown("""
        <div class="hero-section animated-fade">
            <h1 class="hero-title">🔬 Cancer Detection AI</h1>
            <p class="hero-subtitle">
                Advanced Breast Ultrasound Analysis with Explainable AI
            </p>
            <p style="color: var(--text-muted); max-width: 600px; margin: 0 auto;">
                Powered by ResNet-18 Deep Learning | 97% Accuracy | Real-time Grad-CAM Visualization
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Feature Cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="feature-card animated-fade">
                <div class="feature-icon">🎯</div>
                <h3>97% Accuracy</h3>
                <p>State-of-the-art ResNet-18 model trained on thousands of ultrasound images</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="feature-card animated-fade" style="animation-delay: 0.1s;">
                <div class="feature-icon">🔍</div>
                <h3>Explainable AI</h3>
                <p>Grad-CAM heatmaps show exactly which regions influenced the diagnosis</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="feature-card animated-fade" style="animation-delay: 0.2s;">
                <div class="feature-icon">📊</div>
                <h3>Analytics Dashboard</h3>
                <p>Comprehensive analytics and reporting for clinical decision support</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Stats Section
    st.markdown("""
        <div style="text-align: center; margin: 4rem 0;">
            <h2 style="margin-bottom: 3rem;">Trusted by Healthcare Professionals</h2>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="stats-card animated-float">
                <div class="stats-number">97%</div>
                <div class="stats-label">Accuracy</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="stats-card animated-float" style="animation-delay: 0.2s;">
                <div class="stats-number">3</div>
                <div class="stats-label">Classes Detected</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="stats-card animated-float" style="animation-delay: 0.4s;">
                <div class="stats-number">&lt;1s</div>
                <div class="stats-label">Inference Time</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="stats-card animated-float" style="animation-delay: 0.6s;">
                <div class="stats-number">24/7</div>
                <div class="stats-label">Availability</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # CTA Section
    st.markdown("""
        <div style="text-align: center; margin: 4rem 0;">
            <h2 style="margin-bottom: 1rem;">Ready to Get Started?</h2>
            <p style="color: var(--text-secondary); margin-bottom: 2rem;">
                Login or register to access the AI-powered diagnostic platform
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Login/Register Section
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            show_login_form()
        
        with tab2:
            show_register_form()

def show_login_form():
    from src.utils.db_utils import authenticate_user, log_user_activity
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit = st.form_submit_button("🚀 Login", width="stretch")
        
        if submit:
            if not username or not password:
                st.error("⚠️ Please provide both username and password")
            elif authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                try:
                    log_user_activity(username, "login")
                except Exception:
                    pass
                st.success(f"✅ Welcome back, {username}!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")

def show_register_form():
    from src.utils.db_utils import create_user, validate_password, get_password_strength
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Password Requirements
    st.markdown("""
        <div style="background: rgba(33, 150, 243, 0.1); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
            <h4 style="margin: 0 0 0.5rem 0; color: #2196F3;">🔒 Password Requirements</h4>
            <ul style="margin: 0; padding-left: 1.5rem; color: var(--text-secondary); font-size: 0.9rem;">
                <li>Minimum 8 characters</li>
                <li>At least 1 uppercase letter (A-Z)</li>
                <li>At least 1 lowercase letter (a-z)</li>
                <li>At least 1 number (0-9)</li>
                <li>At least 1 special character (!@#$%^&*...)</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("register_form"):
        new_username = st.text_input("👤 Choose Username", placeholder="Enter desired username")
        new_password = st.text_input("🔒 Choose Password", type="password", placeholder="Enter a strong password", key="reg_pwd")
        confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Re-enter your password", key="reg_pwd_confirm")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit = st.form_submit_button("✨ Create Account", width="stretch", type="primary")
        
        if submit:
            # Validation
            if not new_username or not new_password or not confirm_password:
                st.error("⚠️ Please fill in all fields")
            elif len(new_username) < 3:
                st.error("❌ Username must be at least 3 characters long")
            elif len(new_username) > 30:
                st.error("❌ Username must be less than 30 characters")
            elif not new_username.isalnum() and '_' not in new_username:
                st.error("❌ Username can only contain letters, numbers, and underscores")
            elif new_password != confirm_password:
                st.error("❌ Passwords don't match! Please re-enter.")
            else:
                # Validate password strength
                is_valid, message = validate_password(new_password)
                
                if not is_valid:
                    st.error(message)
                else:
                    # Attempt to create user
                    if create_user(new_username, new_password):
                        st.success("✅ Account created successfully! Please login.")
                        st.balloons()
                    else:
                        st.error("❌ Username already exists. Please choose another.")
    
    # Show password strength indicator outside form (real-time feedback)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Password strength meter placeholder
    password_input = st.session_state.get("reg_pwd", "")
    
    if password_input:
        strength = get_password_strength(password_input)
        
        # Color coding
        strength_colors = {
            "Weak": "#f44336",
            "Medium": "#FF9800", 
            "Strong": "#4CAF50"
        }
        
        strength_emojis = {
            "Weak": "⚠️",
            "Medium": "⚡",
            "Strong": "✅"
        }
        
        color = strength_colors.get(strength, "#888")
        emoji = strength_emojis.get(strength, "")
        
        # Progress bar width
        strength_width = {
            "Weak": "33%",
            "Medium": "66%",
            "Strong": "100%"
        }
        
        st.markdown(f"""
            <div style="margin-top: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.9rem; color: var(--text-secondary);">Password Strength:</span>
                    <span style="font-weight: bold; color: {color};">{emoji} {strength}</span>
                </div>
                <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                    <div style="width: {strength_width[strength]}; height: 100%; background: {color}; transition: all 0.3s ease;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# Main app logic
def main():
    from src.utils.db_utils import init_db, ensure_user_table
    
    # Initialize database
    init_db()
    ensure_user_table()
    
    if not st.session_state.authenticated:
        show_landing()
    else:
        # Redirect to home page
        st.markdown("""
            <div style="text-align: center; margin: 4rem 0;">
                <h1>🎉 Welcome to Cancer Detection AI!</h1>
                <p style="font-size: 1.2rem; color: var(--text-secondary); margin: 2rem 0;">
                    Redirecting to your dashboard...
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div style="text-align: center;">
                <p style="color: var(--text-muted);">
                    Please navigate using the sidebar or the buttons below:
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏠 Home Dashboard", width="stretch"):
                st.switch_page("pages/Home.py")
        
        with col2:
            if st.button("🔬 Make Prediction", width="stretch"):
                st.switch_page("pages/Prediction.py")
        
        with col3:
            if st.button("📊 My Analytics", width="stretch"):
                st.switch_page("pages/User_Analytics.py")

if __name__ == "__main__":
    main()
