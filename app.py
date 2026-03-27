import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# --- 0. ADMIN CONTROL ---
CURRENT_CYCLE = 5

# --- INITIALIZE SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection)

# --- 1. DATA SETUP (FROM IMAGE) ---
# Classification based on provided screenshot
LEVEL_3 = ["English III AP", "English III IB", "English IV AP", "English IV IB", "Calculus AB AP", "Calculus BC AP", "Math: Analysis & Appr IB SL", "Math: Analysis & Appr IB HL", "Math: Application & Int IB SL", "Math: Application & Int IB HL", "Precalculus AP", "Statistics AP", "Biology AP", "Biology IB SL", "Biology IB HL", "Chemistry AP", "Chemistry IB SL", "Chemistry IB HL", "Environmental Science AP", "Physics 1 AP", "Physics 2 AP", "Physics C: Mechanics AP", "Physics IB SL", "Physics IB HL", "European History AP", "History of the Americas IB", "Human Geography AP", "Macroeconomics AP", "Microeconomics AP", "Psychology AP", "Psychology IB", "U.S. Government AP", "U.S. History AP", "World History AP", "Chinese IV AP", "French IV AP", "French IB SL", "French IB HL", "Latin IV AP", "Latin IB SL", "Latin IB HL", "Spanish IV AP", "Spanish V AP", "Spanish IB SL", "Spanish IB HL"]
LEVEL_2 = ["AP Seminar", "English I Advanced", "English I QUEST", "English II Advanced", "English II QUEST", "Algebra I Advanced", "Algebra II Advanced", "Geometry Advanced", "Pre-Calculus Advanced", "Pre-Calculus OnRamps", "Pre-Calculus IB Prep", "Biology Advanced", "Chemistry Advanced", "Investigations in Psychology", "Chinese II Advanced", "Chinese III Advanced", "French II Advanced", "French III Advanced", "French V Advanced", "Latin II Advanced", "Latin III Advanced", "Spanish II Advanced", "Spanish III Advanced", "Advanced Language or Career Applications", "Seminar in Languages other than English", "Advanced Spanish"]
LEVEL_1 = ["English I", "English II", "English III", "English IV", "Algebra I", "Algebra II", "Algebraic Reasoning", "College Prep Math", "Geometry", "Math Models", "Pre-Calculus", "Statistics", "Astronomy", "Biology", "Chemistry", "Environmental Systems", "Earth & Space Science", "Earth Systems Science", "Integrated Physics and Chemistry", "Physics", "Specialized Topics in Science I-III", "An American Experience", "African American Studies", "Economics", "Mexican American Studies", "New Testament Bible & Amer Civ", "Old Testament Bible & Amer Civ", "Personal Financial Literacy", "Psychology", "Sociology", "U.S. Government", "U.S. History", "World Geography", "World History", "American Sign Language I", "American Sign Language II", "American Sign Language III", "American Sign Language IV", "Chinese I", "Chinese II", "Chinese III", "Chinese IV", "French I", "French II", "Latin I", "Latin II", "Spanish I", "Spanish II", "Spanish III"]
ALL_CLASSES = sorted(list(set(LEVEL_3 + LEVEL_2 + LEVEL_1)))

# --- 2. GPA MATH ---
def calculate_sem_gpa(class_list):
    class_gpas = []
    for cls, grades_list in class_list:
        if not cls: continue
        
        # Filter valid numeric grades (ignore blanks for current cycle)
        valid_grades = []
        for g in grades_list:
            if g.strip() == "": continue
            try: valid_grades.append(float(g))
            except: continue
            
        if not valid_grades: continue
        
        # 1. Sem Average
        avg = sum(valid_grades) / len(valid_grades)
        
        # 2. Base Scale
        max_gpa = 6.0 if cls in LEVEL_3 else 5.5 if cls in LEVEL_2 else 5.0
        
        # 3. Calculation: every 1pt < 100 is -0.1
        if avg >= 70:
            class_gpa = max(0, max_gpa - ((100 - avg) * 0.1))
        else:
            class_gpa = 0.0
        class_gpas.append(class_gpa)
        
    return sum(class_gpas) / len(class_gpas) if class_gpas else 0.0

# --- 3. PERSISTENT STATE HELPERS ---
SAVE_KEY_PREFIXES = ["S1c", "S2c", "S1g", "S2g", "num_S", "sync_toggle"]

def save_user_data():
    email = st.session_state.get("email", "")
    if not email: return
    keys_to_save = {k: v for k, v in st.session_state.items() if any(k.startswith(p) for p in SAVE_KEY_PREFIXES)}
    try:
        conn.table("user_data").upsert({"email": email, "data": keys_to_save, "updated_at": datetime.now().isoformat()}).execute()
    except: pass

def load_user_data(email):
    try:
        result = conn.table("user_data").select("data").eq("email", email).execute()
        if result.data:
            for k, v in result.data[0]["data"].items(): st.session_state[k] = v
    except: pass

# --- 4. CALLBACKS ---
def update_count(sem, delta):
    key = f"num_{sem}"
    new_val = st.session_state[key] + delta
    if 1 <= new_val <= 8:
        st.session_state[key] = new_val
    save_user_data()

# --- 5. APP UI ---
st.set_page_config(page_title="Analytics Pro", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com');
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stStatusWidget"], .stAppDeployButton {display:none;}
    .stApp { background: radial-gradient(circle at top left, #1e1e2f, #111119); font-family: 'Inter', sans-serif; color: #e0e0e0; }
    div[data-testid="stVerticalBlock"] > div:has(div.stSubheader) { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 30px !important; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { background-color: rgba(0, 0, 0, 0.2) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; color: white !important; border-radius: 12px !important; }
    button[kind="primary"] { background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important; border: none !important; border-radius: 12px !important; font-weight: 600 !important; padding: 10px 20px !important; }
    [data-testid="stMetricValue"] { font-size: 3rem !important; font-weight: 700 !important; color: #a855f7 !important; }
    </style>
    """, unsafe_allow_html=True)

# SESSION STATE DEFAULTS
if 'num_S1' not in st.session_state: st.session_state.num_S1 = 4
if 'num_S2' not in st.session_state: st.session_state.num_S2 = 4
if 'sync_toggle' not in st.session_state: st.session_state.sync_toggle = True

st.title("Analytics Pro ✨")
st.markdown("##### **Note:** You can leave the current cycle blank if you have no grade.")

# Layout
col1, col2 = st.columns(2)

# Semester 1
with col1:
    st.subheader("First Semester")
    s1_classes = []
    for i in range(st.session_state.num_S1):
        c1, c2 = st.columns([2, 1])
        cls = c1.selectbox(f"S1 Class {i+1}", [""] + ALL_CLASSES, key=f"S1c{i}", on_change=save_user_data)
        grd = c2.text_input(f"S1 Grades {i+1}", key=f"S1g{i}", on_change=save_user_data, placeholder="95, 100")
        s1_classes.append((cls, grd.split(",") if grd else []))
        if st.session_state.sync_toggle: st.session_state[f"S2c{i}"] = cls
    
    st.button("➕ Add Class", key="btn_add_s1", on_click=update_count, args=("S1", 1))
    st.button("➖ Remove Class", key="btn_rem_s1", on_click=update_count, args=("S1", -1))

# Semester 2
with col2:
    st.subheader("Second Semester")
    st.toggle("Auto-sync Classes", key="sync_toggle", on_change=save_user_data)
    s2_classes = []
    for i in range(st.session_state.num_S2):
        c1, c2 = st.columns([2, 1])
        cls = c1.selectbox(f"S2 Class {i+1}", [""] + ALL_CLASSES, key=f"S2c{i}", on_change=save_user_data)
        grd = c2.text_input(f"S2 Grades {i+1}", key=f"S2g{i}", on_change=save_user_data, placeholder="88, 92")
        s2_classes.append((cls, grd.split(",") if grd else []))

    st.button("➕ Add Class", key="btn_add_s2", on_click=update_count, args=("S2", 1))
    st.button("➖ Remove Class", key="btn_rem_s2", on_click=update_count, args=("S2", -1))

# Calculations
gpa1 = calculate_sem_gpa(s1_classes)
gpa2 = calculate_sem_gpa(s2_classes)
final_gpa = (gpa1 + gpa2) / 2 if (gpa1 > 0 and gpa2 > 0) else (gpa1 or gpa2)

st.divider()
m1, m2, m3 = st.columns(3)
m1.metric("Sem 1 GPA", f"{gpa1:.4f}")
m2.metric("Sem 2 GPA", f"{gpa2:.4f}")
m3.metric("Final GPA", f"{final_gpa:.4f}")
