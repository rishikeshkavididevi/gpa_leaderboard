import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import re

# --- 0. ADMIN CONTROL ---
CURRENT_CYCLE = 4 

# --- 1. DATA SETUP (Example Class Lists) ---
# Note: Define LEVEL_3, LEVEL_2, LEVEL_1, and ALL_CLASSES here.
# Refer to code in for full list of courses.
ALL_CLASSES = sorted(list(set(LEVEL_3 + LEVEL_2 + LEVEL_1)))

# --- 2. GOOGLE SHEETS CONNECTION ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

def get_leaderboard():
    try:
        # worksheet name MUST be exact match to your Sheet tab name
        return conn.read(worksheet="Sheet1", ttl=0)
    except Exception as e:
        st.warning(f"Could not load leaderboard: {e}")
        return pd.DataFrame(columns=["email", "display_name", "gpa"])

def save_to_leaderboard(email, name, gpa):
    try:
        df = get_leaderboard()
        new_entry = pd.DataFrame([{"email": email, "display_name": name, "gpa": gpa}])
        if not df.empty and email in df['email'].values:
            df.loc[df['email'] == email, ['display_name', 'gpa']] = [name, gpa]
        else:
            df = pd.concat([df, new_entry], ignore_index=True)
        conn.update(worksheet="Sheet1", data=df)
        st.success("Leaderboard updated!")
    except Exception as e:
        st.error(f"Save failed: {e}")

# --- 3. CALCULATIONS (Simplified Example) ---
def get_points(grade, class_name):
    if not grade or grade == "N/A" or grade == "Locked": return None
    try:
        g = float(grade)
        base = 0
        if g >= 90: base = 4.0
        elif g >= 80: base = 3.0
        elif g >= 70: base = 2.0
        else: base = 0.0
        
        if class_name in LEVEL_3: return base + 1.0
        if class_name in LEVEL_2: return base + 0.5
        return base
    except: return None

# --- 4. APP UI ---
st.set_page_config(page_title="Leaderboard", layout="wide")

if 'step' not in st.session_state: st.session_state.step = 1
# ... (rest of the UI logic, including state management for classes,
#      columns, and input components as shown in the original code) ...

# See the full implementation in the original source code

# Navigation and input handling logic...
if page == "Leaderboard":
    st.title("Current Standings")
    if not lb_data.empty:
        st.dataframe(lb_data.sort_values(by="gpa", ascending=False).reset_index(drop=True), use_container_width=True)
    else:
        st.info("Leaderboard is currently empty.")
