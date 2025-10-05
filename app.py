import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# File paths for persistence
LEADERBOARD_FILE = 'leaderboard.json'
ACTUALS_FILE = 'actuals.csv'

# Initialize session state
if 'admin_unlocked' not in st.session_state:
    st.session_state.admin_unlocked = False
if 'actuals_data' not in st.session_state:
    st.session_state.actuals_data = None

# Load leaderboard from file
def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save leaderboard to file
def save_leaderboard(leaderboard):
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard, f, indent=2)

# Load actuals from file if exists
def load_actuals():
    if os.path.exists(ACTUALS_FILE):
        try:
            df = pd.read_csv(ACTUALS_FILE, header=None)
            actuals = df.values.flatten().tolist()
            actuals = [float(x) for x in actuals if pd.notna(x)]
            return actuals
        except:
            return None
    return None

# Save actuals to file
def save_actuals(actuals):
    df = pd.DataFrame(actuals)
    df.to_csv(ACTUALS_FILE, index=False, header=False)

# Parse CSV data
def parse_csv(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, header=None)
        values = df.values.flatten().tolist()
        values = [float(x) for x in values if pd.notna(x)]
        return values
    except Exception as e:
        st.error(f"Error parsing CSV: {e}")
        return None

# Page config
st.set_page_config(
    page_title="Prediction Accuracy Calculator",
    page_icon="🎯",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px 0;
    }
    .stButton>button {
        width: 100%;
    }
    .accuracy-score {
        font-size: 48px;
        text-align: center;
        color: #667eea;
        font-weight: 700;
        padding: 20px;
    }
    .leaderboard-item {
        background: #f8f9ff;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    div[data-testid="stFileUploader"] {
        background-color: #f8f9ff;
        border: 2px dashed #667eea;
        border-radius: 8px;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 style='text-align: center;'>🎯 Prediction Accuracy Calculator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Upload your predictions CSV to calculate accuracy</p>", unsafe_allow_html=True)

st.markdown("---")

# Admin Section - Password Protected Actuals Upload
with st.expander("🔒 Admin Section - Upload Actuals", expanded=not st.session_state.admin_unlocked):
    if not st.session_state.admin_unlocked:
        st.warning("Enter password to upload actuals CSV")
        password = st.text_input("Password", type="password", key="admin_password")
        if st.button("Unlock", key="unlock_btn"):
            if password == "1234":
                st.session_state.admin_unlocked = True
                st.rerun()
            else:
                st.error("❌ Incorrect password")
    else:
        st.success("✅ Admin access granted")
        
        # Check if actuals already exist
        existing_actuals = load_actuals()
        if existing_actuals:
            st.info(f"📊 Actuals already loaded: {len(existing_actuals)} values")
            if st.button("Replace Actuals", key="replace_actuals"):
                st.session_state.actuals_data = None
                if os.path.exists(ACTUALS_FILE):
                    os.remove(ACTUALS_FILE)
                st.rerun()
        
        if not existing_actuals or st.session_state.get('replacing_actuals'):
            actuals_file = st.file_uploader(
                "Upload Actuals CSV",
                type=['csv'],
                key="actuals_uploader",
                help="Upload the CSV file containing actual values"
            )
            
            if actuals_file is not None:
                actuals_data = parse_csv(actuals_file)
                if actuals_data:
                    st.session_state.actuals_data = actuals_data
                    save_actuals(actuals_data)
                    st.success(f"✓ Loaded {len(actuals_data)} actuals")
                    st.rerun()
        else:
            st.session_state.actuals_data = existing_actuals

st.markdown("---")

# Load actuals if they exist
if st.session_state.actuals_data is None:
    st.session_state.actuals_data = load_actuals()

# Predictions Upload Section
st.subheader("📊 Upload Predictions")

predictions_file = st.file_uploader(
    "Upload your predictions CSV",
    type=['csv'],
    key="predictions_uploader",
    help="Upload the CSV file containing your predictions"
)

predictions_data = None
if predictions_file is not None:
    predictions_data = parse_csv(predictions_file)
    if predictions_data:
        st.success(f"✓ Loaded {len(predictions_data)} predictions")

st.markdown("---")

# User Selection
st.subheader("👤 Select Your Name")
col1, col2 = st.columns([3, 2])

with col1:
    name_option = st.selectbox(
        "Choose name",
        ["", "Bob", "Alex", "Ben", "Other"],
        key="name_select"
    )

custom_name = ""
if name_option == "Other":
    with col2:
        custom_name = st.text_input("Enter custom name", key="custom_name")

selected_name = custom_name if name_option == "Other" else name_option

st.markdown("---")

# Calculate Button
if st.button("🎯 Calculate Accuracy", type="primary", disabled=not (st.session_state.actuals_data and predictions_data and selected_name)):
    if len(st.session_state.actuals_data) != len(predictions_data):
        st.error("❌ Error: Actuals and predictions must have the same length!")
    else:
        # Calculate accuracy
        correct = sum(1 for a, p in zip(st.session_state.actuals_data, predictions_data) if a == p)
        total = len(st.session_state.actuals_data)
        accuracy = (correct / total) * 100
        
        # Display results
        st.markdown(f"<div class='accuracy-score'>{accuracy:.2f}%</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Predictions", total)
        with col2:
            st.metric("Correct", correct)
        with col3:
            st.metric("Name", selected_name)
        
        # Update leaderboard
        leaderboard = load_leaderboard()
        
        if selected_name not in leaderboard or leaderboard[selected_name]['accuracy'] < accuracy:
            leaderboard[selected_name] = {
                'accuracy': accuracy,
                'correct': correct,
                'total': total,
                'timestamp': datetime.now().isoformat()
            }
            save_leaderboard(leaderboard)
            st.success("🎉 Leaderboard updated!")
        else:
            st.info("ℹ️ Your previous best score was higher")

st.markdown("---")

# Leaderboard Section
st.subheader("🏆 Leaderboard")

leaderboard = load_leaderboard()

if not leaderboard:
    st.info("No results yet. Be the first to submit!")
else:
    # Sort by accuracy
    sorted_leaderboard = sorted(
        leaderboard.items(),
        key=lambda x: x[1]['accuracy'],
        reverse=True
    )
    
    medals = ['🥇', '🥈', '🥉']
    
    for idx, (name, data) in enumerate(sorted_leaderboard):
        rank = idx + 1
        medal = medals[idx] if idx < 3 else f"#{rank}"
        
        col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
        
        with col1:
            st.markdown(f"<h2 style='text-align: center;'>{medal}</h2>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{name}**")
            st.caption(f"{data['correct']} / {data['total']} correct")
        with col3:
            st.markdown(f"<h3 style='color: #667eea; text-align: right;'>{data['accuracy']:.2f}%</h3>", unsafe_allow_html=True)
        with col4:
            timestamp = datetime.fromisoformat(data['timestamp'])
            st.caption(f"🕒 {timestamp.strftime('%Y-%m-%d %H:%M')}")
        
        st.markdown("<hr style='margin: 10px 0; opacity: 0.2;'>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("💾 All data is persisted to local files")