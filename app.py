import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# --- 0. ADMIN CONTROL ---
CURRENT_CYCLE = 5

# --- INITIALIZE SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection)

# --- 1. DATA SETUP (CLASSIFIED FROM IMAGE) ---
LEVEL_3 = ["English III AP", "English III IB", "English IV AP", "English IV IB", "Calculus AB AP", "Calculus BC AP", "Math: Analysis & Appr IB SL", "Math: Analysis & Appr IB HL", "Math: Application & Int IB SL", "Math: Application & Int IB HL", "Precalculus AP", "Statistics AP", "Biology AP", "Biology IB SL", "Biology IB HL", "Chemistry AP", "Chemistry IB SL", "Chemistry IB HL", "Environmental Science AP", "Physics 1 AP", "Physics 2 AP", "Physics C: Mechanics AP", "Physics IB SL", "Physics IB HL", "European History AP", "History of the Americas IB", "Human Geography AP", "Macroeconomics AP", "Microeconomics AP", "Psychology AP", "Psychology IB", "U.S. Government AP", "U.S. History AP", "World History AP", "Chinese IV AP", "French IV AP", "French IB SL", "French IB HL", "Latin IV AP", "Latin IB SL", "Latin IB HL", "Spanish IV AP", "Spanish V AP", "Spanish IB SL", "Spanish IB HL"]
LEVEL_2 = ["AP Seminar", "English I Advanced", "English I QUEST", "English II Advanced", "English II QUEST", "Algebra I Advanced", "Algebra II Advanced", "Geometry Advanced", "Pre-Calculus Advanced", "Pre-Calculus OnRamps", "Pre-Calculus IB Prep", "Biology Advanced", "Chemistry Advanced", "Investigations in Psychology", "Chinese II Advanced", "Chinese III Advanced", "French II Advanced", "French III Advanced", "French V Advanced", "Latin II Advanced", "Latin III Advanced", "Spanish II Advanced", "Spanish III Advanced", "Advanced Language or Career Applications", "Seminar in Languages other than English", "Advanced Spanish"]
LEVEL_1 = ["English I", "English II", "English III", "English IV", "Algebra I", "Algebra II", "Algebraic Reasoning", "College Prep Math", "Geometry", "Math Models", "Pre-Calculus", "Statistics", "Astronomy", "Biology", "Chemistry", "Environmental Systems", "Earth & Space Science", "Earth Systems Science", "Integrated Physics and Chemistry", "Physics", "Specialized Topics in Science I-III", "An American Experience", "African American Studies", "Economics", "Mexican American Studies", "New Testament Bible & Amer Civ", "Old Testament Bible & Amer Civ", "Personal Financial Literacy", "Psychology", "Sociology", "U.S. Government", "U.S. History", "World Geography", "World History", "American Sign Language I", "American Sign Language II", "American Sign Language III", "American Sign Language IV", "Chinese I", "Chinese II", "Chinese III", "Chinese IV", "French I", "French II", "Latin I", "Latin II", "Spanish I", "Spanish II", "Spanish III"]
ALL_CLASSES = sorted(list(set(LEVEL_3 + LEVEL_2 + LEVEL_1)))

# --- 2. GPA MATH ---
def calculate_sem_gpa(class_data):
    class_gpas = []
    for entry in class_data:
        cls = entry['class']
        grades = entry['grades']
        if not cls: continue
        
        # Filter valid numeric grades (ignore blanks for current cycle)
        valid_grades = []
        for g in grades:
            if g is not None and str(g).strip() != "":
                try: valid_grades.append(float(g))
                except: continue
        
        if not valid_grades: continue
        
        # 1. Find Sem Average (adding all cycles together)
        sem_avg = sum(valid_grades) / len(valid_grades)
        
        # 2. Determine Scale
        max_val = 6.0 if cls in LEVEL_3 else 5.5 if cls in LEVEL_2 else 5.0
        
        # 3. Calculation: GPA = Max - ((100 - avg) * 0.1)
        if sem_avg >= 70:
            class_gpa = max(0, max_val - ((100 - sem_avg) * 0.1))
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

def update_count(sem, delta):
    key = f"num_{sem}"
    new_val = st.session_state[key] + delta
    if 1 <= new_val <= 8: st.session_state[key] = new_val
    save_user_data()

# --- 4. APP UI ---
st.set_page_config(page_title="Analytics Pro", page_icon="✨", layout="wide")

# Custom CSS from your original code
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com');
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background: radial-gradient(circle at top left, #1e1e2f, #111119); font-family: 'Inter', sans-serif; color: #e0e0e0; }
    div[data-testid="stVerticalBlock"] > div:has(div.stSubheader) { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 20px !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { background-color: rgba(0, 0, 0, 0.2) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; color: white !important; border-radius: 12px !important; }
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; font-weight: 700 !important; color: #a855f7 !important; }
    </style>
    """, unsafe_allow_html=True)

if 'num_S1' not in st.session_state: st.session_state.num_S1 = 4
if 'num_S2' not in st.session_state: st.session_state.num_S2 = 4

st.title("Analytics Pro ✨")
st.info("Note: You can leave the current cycle blank if you have no grade yet.")

col1, col2 = st.columns(2)

# SEMESTER 1
with col1:
    st.subheader("First Semester")
    s1_data = []
    for i in range(st.session_state.num_S1):
        r = st.container()
        c1, c2, c3, c4 = r.columns([3, 1, 1, 1])
        cls = c1.selectbox(f"Class {i+1}", [""] + ALL_CLASSES, key=f"S1c{i}", on_change=save_user_data)
        g1 = c2.text_input("C1", key=f"S1g{i}_1", on_change=save_user_data)
        g2 = c3.text_input("C2", key=f"S1g{i}_2", on_change=save_user_data)
        g3 = c4.text_input("C3", key=f"S1g{i}_3", on_change=save_user_data)
        s1_data.append({'class': cls, 'grades': [g1, g2, g3]})

    st.button("➕ Add Class", key="add_s1", on_click=update_count, args=("S1", 1))
    st.button("➖ Remove Class", key="rem_s1", on_click=update_count, args=("S1", -1))

# SEMESTER 2
with col2:
    st.subheader("Second Semester")
    st.toggle("Auto-sync classes", key="sync_toggle", on_change=save_user_data)
    s2_data = []
    for i in range(st.session_state.num_S2):
        if st.session_state.get("sync_toggle") and i < st.session_state.num_S1:
            st.session_state[f"S2c{i}"] = st.session_state.get(f"S1c{i}", "")
            
        r = st.container()
        c1, c2, c3, c4 = r.columns([3, 1, 1, 1])
        cls = c1.selectbox(f"Class {i+1}", [""] + ALL_CLASSES, key=f"S2c{i}", on_change=save_user_data)
        g4 = c2.text_input("C4", key=f"S2g{i}_4", on_change=save_user_data)
        g5 = c3.text_input("C5", key=f"S2g{i}_5", on_change=save_user_data)
        g6 = c4.text_input("C6", key=f"S2g{i}_6", on_change=save_user_data)
        s2_data.append({'class': cls, 'grades': [g4, g5, g6]})

    st.button("➕ Add Class", key="add_s2", on_click=update_count, args=("S2", 1))
    st.button("➖ Remove Class", key="rem_s2", on_click=update_count, args=("S2", -1))

# GPA CALCULATION
gpa1 = calculate_sem_gpa(s1_data)
gpa2 = calculate_sem_gpa(s2_data)
final_gpa = (gpa1 + gpa2) / 2 if (gpa1 > 0 and gpa2 > 0) else (gpa1 or gpa2)

st.divider()
m1, m2, m3 = st.columns(3)
m1.metric("Sem 1 GPA", f"{gpa1:.4f}")
m2.metric("Sem 2 GPA", f"{gpa2:.4f}")
m3.metric("Cumulative GPA", f"{final_gpa:.4f}")
