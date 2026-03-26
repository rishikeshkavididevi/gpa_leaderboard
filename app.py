import streamlit as st
import pandas as pd

# --- 0. SNOWFLAKE CONNECTION ---
# Ensure your Streamlit Cloud Secrets are updated with the correct account locator
conn = st.connection("snowflake", type="snowflake")

# --- 1. SETTINGS & DATA ---
LEVEL_3 = ["English III AP", "English III IB", "English IV AP", "English IV IB", "Calculus AB AP", "Calculus BC AP", "Math: Analysis & Appr IB SL", "Math: Analysis & Appr IB HL", "Math: Application & Int IB SL", "Math: Application & Int IB HL", "Precalculus AP", "Statistics AP", "Biology AP", "Biology IB SL", "Biology IB HL", "Chemistry AP", "Chemistry IB SL", "Chemistry IB HL", "Environmental Science AP", "Physics 1 AP", "Physics 2 AP", "Physics C: Mechanics AP", "Physics IB SL", "Physics IB HL", "European History AP", "History of the Americas IB", "Human Geography AP", "Macroeconomics AP", "Microeconomics AP", "Psychology AP", "Psychology IB", "U.S. Government AP", "U.S. History AP", "World History AP", "Chinese IV AP", "French IV AP", "French IB SL", "French IB HL", "Latin IV AP", "Latin IB SL", "Latin IB HL", "Spanish IV AP", "Spanish V AP", "Spanish IB SL", "Spanish IB HL"]
LEVEL_2 = ["AP Seminar", "English I Advanced", "English I QUEST", "English II Advanced", "English II QUEST", "Algebra I Advanced", "Algebra II Advanced", "Geometry Advanced", "Pre-Calculus Advanced", "Pre-Calculus OnRamps", "Pre-Calculus IB Prep", "Biology Advanced", "Chemistry Advanced", "Investigations in Psychology", "Chinese II Advanced", "Chinese III Advanced", "French II Advanced", "French III Advanced", "French V Advanced", "Latin II Advanced", "Latin III Advanced", "Spanish II Advanced", "Spanish III Advanced", "Advanced Language or Career Applications", "Seminar in Languages other than English", "Advanced Spanish"]
LEVEL_1 = ["English I", "English II", "English III", "English IV", "Algebra I", "Algebra II", "Algebraic Reasoning", "College Prep Math", "Geometry", "Math Models", "Pre-Calculus", "Statistics", "Astronomy", "Biology", "Chemistry", "Environmental Systems", "Earth & Space Science", "Earth Systems Science", "Integrated Physics and Chemistry", "Physics", "Specialized Topics in Science", "An American Experience", "African American Studies", "Economics", "Mexican American Studies", "New Testament Bible & Amer Civ", "Old Testament Bible & Amer Civ", "Personal Financial Literacy", "Psychology", "Sociology", "U.S. Government", "U.S. History", "World Geography", "World History", "American Sign Language I", "American Sign Language II", "American Sign Language III", "American Sign Language IV", "Chinese I", "Chinese II", "Chinese III", "Chinese IV", "French I", "French II", "Latin I", "Latin II", "Spanish I", "Spanish II", "Spanish III"]
ALL_CLASSES = sorted(list(set(LEVEL_3 + LEVEL_2 + LEVEL_1)))

# --- 2. PERSISTENCE LOGIC ---
def save_val(sem, idx, col, val):
    user = st.session_state.get('user_email', 'guest')
    try:
        conn.query(f"""
            MERGE INTO GPA_STUDENT_PORTAL.PUBLIC.GPA_PERSISTENCE AS target
            USING (SELECT '{user}' as id, '{sem}' as s, {idx} as i) AS source
            ON target.USER_ID = source.id AND target.SEMESTER = source.s AND target.CLASS_INDEX = source.i
            WHEN MATCHED THEN UPDATE SET {col} = '{val}'
            WHEN NOT MATCHED THEN INSERT (USER_ID, SEMESTER, CLASS_INDEX, {col}) 
            VALUES ('{user}', '{sem}', {idx}, '{val}')
        """)
    except:
        pass # Silently fail if DB isn't ready

# --- 3. APP UI SETUP ---
st.set_page_config(page_title="Analytics Pro", layout="wide")

# CUSTOM CSS FOR READABILITY AND ALIGNMENT
st.markdown("""
    <style>
    /* Force text to be bright white */
    label, p, .stMarkdown, .stCheckbox, .stSubheader {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif;
    }
    /* Fix the grid contrast */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        color: white !important;
    }
    /* Vertical spacing for N/A checkbox */
    .stCheckbox { margin-bottom: -15px !important; }
    .stApp { background: radial-gradient(circle at top left, #1e1e2f, #111119); }
    </style>
    """, unsafe_allow_html=True)

# Login Guard
if 'logged_in' not in st.session_state:
    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<h1 style='text-align: center;'>✨ Analytics Pro</h1>", unsafe_allow_html=True)
        e_in = st.text_input("School Email", placeholder="first.last@k12.leanderisd.org")
        if st.button("Initialize Dashboard", use_container_width=True, type="primary"):
            if e_in:
                st.session_state.logged_in = True
                st.session_state.user_email = e_in
                st.rerun()
    st.stop()

# --- 4. DASHBOARD ---
st.markdown(f"#### 🎓 Active Profile: **{st.session_state.user_email}**")

with st.container():
    st.subheader("System Configuration")
    c1, c2, c3 = st.columns(3)
    with c1: sys_val = st.selectbox("Number of Cycles", [6, 4], key="system_cycles")
    with c2: curr_val = st.selectbox("Current Cycle", range(1, sys_val + 1), key="current_cycle")
    with c3: st.toggle("Sync Semester 2 to Semester 1", key="sync_toggle")

def grade_row(sem, i, cycles):
    # Alignment: 3 units for class name, 1 unit for each cycle input
    col_layout = [3.0] + [1.0] * len(cycles)
    cols = st.columns(col_layout, gap="medium")
    
    with cols[0]:
        st.markdown('<p style="margin-bottom:-10px;">Select Class</p>', unsafe_allow_html=True)
        cls = st.selectbox(f"Cls_{sem}_{i}", [""] + ALL_CLASSES, label_visibility="collapsed", key=f"{sem}c{i}_w")
    
    for idx, cyc in enumerate(cycles):
        with cols[idx+1]:
            # N/A Checkbox on top
            is_na = st.checkbox(f"N/A", key=f"{sem}na{cyc}_{i}")
            # Grade input below
            st.text_input(f"C{cyc}", placeholder=f"C{cyc}", label_visibility="collapsed", 
                         key=f"{sem}g{i}_{cyc}", disabled=is_na)

st.divider()
st.subheader("Second Semester")
s2_cycles = [4, 5, 6] if sys_val == 6 else [3, 4]

for row in range(4):
    grade_row("S2", row, s2_cycles)
