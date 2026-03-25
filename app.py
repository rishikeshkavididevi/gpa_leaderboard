import streamlit as st
import pandas as pd
import re

# --- 0. ADMIN CONTROL ---
CURRENT_CYCLE = 5 
MAX_CLASSES = 8
MIN_CLASSES = 1

# --- 1. DATA SETUP ---
LEVEL_3 = ["English III AP", "English III IB", "English IV AP", "English IV IB", "Calculus AB AP", "Calculus BC AP", "Math: Analysis & Appr IB SL", "Math: Analysis & Appr IB HL", "Math: Application & Int IB SL", "Math: Application & Int IB HL", "Precalculus AP", "Statistics AP", "Biology AP", "Biology IB SL", "Biology IB HL", "Chemistry AP", "Chemistry IB SL", "Chemistry IB HL", "Environmental Science AP", "Physics 1 AP", "Physics 2 AP", "Physics C: Mechanics AP", "Physics IB SL", "Physics IB HL", "European History AP", "History of the Americas IB", "Human Geography AP", "Macroeconomics AP", "Microeconomics AP", "Psychology AP", "Psychology IB", "U.S. Government AP", "U.S. History AP", "World History AP", "Chinese IV AP", "French IV AP", "French IB SL", "French IB HL", "Latin IV AP", "Latin IB SL", "Latin IB HL", "Spanish IV AP", "Spanish V AP", "Spanish IB SL", "Spanish IB HL"]
LEVEL_2 = ["AP Seminar", "English I Advanced", "English I QUEST", "English II Advanced", "English II QUEST", "Algebra I Advanced", "Algebra II Advanced", "Geometry Advanced", "Pre-Calculus Advanced", "Pre-Calculus OnRamps", "Pre-Calculus IB Prep", "Biology Advanced", "Chemistry Advanced", "Investigations in Psychology", "Chinese II Advanced", "Chinese III Advanced", "French II Advanced", "French III Advanced", "French V Advanced", "Latin II Advanced", "Latin III Advanced", "Spanish II Advanced", "Spanish III Advanced", "Advanced Language or Career Applications", "Seminar in Languages other than English", "Advanced Spanish"]
LEVEL_1 = ["English I", "English II", "English III", "English IV", "Algebra I", "Algebra II", "Algebraic Reasoning", "College Prep Math", "Geometry", "Math Models", "Pre-Calculus", "Statistics", "Astronomy", "Biology", "Chemistry", "Environmental Systems", "Earth & Space Science", "Earth Systems Science", "Integrated Physics and Chemistry", "Physics", "Specialized Topics in Science", "An American Experience", "African American Studies", "Economics", "Mexican American Studies", "New Testament Bible & Amer Civ", "Old Testament Bible & Amer Civ", "Personal Financial Literacy", "Psychology", "Sociology", "U.S. Government", "U.S. History", "World Geography", "World History", "American Sign Language I", "American Sign Language II", "American Sign Language III", "American Sign Language IV", "Chinese I", "Chinese II", "Chinese III", "Chinese IV", "French I", "French II", "Latin I", "Latin II", "Spanish I", "Spanish II", "Spanish III"]
ALL_CLASSES = sorted(list(set(LEVEL_3 + LEVEL_2 + LEVEL_1)))

# --- 2. LOGIC HELPERS ---
def trigger_sync():
    """Forces Semester 2 to match Semester 1 immediately."""
    if st.session_state.sync_toggle:
        st.session_state.num_s2 = st.session_state.num_s1
        for i in range(st.session_state.num_s1):
            s1_val = st.session_state.get(f"S1c{i}_val", "")
            st.session_state[f"S2c{i}_val"] = s1_val
            # Update the widget itself directly so it reflects on the first frame
            st.session_state[f"S2c{i}_widget"] = s1_val

def on_class_change(sem, i):
    new_val = st.session_state[f"{sem}c{i}_widget"]
    st.session_state[f"{sem}c{i}_val"] = new_val
    
    # Push S1 change to S2 if sync is ON
    if sem == "S1" and st.session_state.get("sync_toggle", False):
        st.session_state[f"S2c{i}_val"] = new_val
        st.session_state[f"S2c{i}_widget"] = new_val
        
    # Break sync if S2 is changed manually to something different
    if sem == "S2" and st.session_state.get("sync_toggle", False):
        if new_val != st.session_state.get(f"S1c{i}_val", ""):
            st.session_state.sync_toggle = False

def validate_all_grades(s1_data, s2_data):
    for sem_name, sem_data, sem_key in [("Semester 1", s1_data, "S1"), ("Semester 2", s2_data, "S2")]:
        for i, (cls, grades) in enumerate(sem_data):
            if not cls or cls == "":
                return f"Row {i+1} in {sem_name} is missing a Class selection."
            for j, grade in enumerate(grades):
                cycle_num = (1, 2, 3)[j] if sem_name == "Semester 1" else (4, 5, 6)[j]
                if not str(grade).strip() or str(grade).strip() == f"C{cycle_num}":
                    if cycle_num == CURRENT_CYCLE:
                        if not st.session_state.get(f"{sem_key}na{cycle_num}_{i}", False):
                            return f"Missing grade or N/A for {cls} in Cycle {cycle_num}"
                    else:
                        return f"Please enter a grade for {cls} in Cycle {cycle_num}"
    return None

def get_detailed_gpa(data):
    results = []
    for cls, grades in data:
        v_grades = []
        for g in grades:
            try: v_grades.append(float(g))
            except: continue
        if not v_grades: continue
        avg = sum(v_grades) / len(v_grades)
        max_gpa = 6.0 if cls in LEVEL_3 else 5.5 if cls in LEVEL_2 else 5.0
        cgpa = max(0, max_gpa - ((100 - avg) * 0.1)) if avg >= 70 else 0.0
        results.append({"Class": cls, "GPA": round(cgpa, 4)})
    return results

# --- 3. APP UI ---
st.set_page_config(page_title="Analytics Pro", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com');
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background: radial-gradient(circle at top left, #1e1e2f, #111119); font-family: 'Inter', sans-serif; color: #e0e0e0; }
    div[data-testid="stVerticalBlock"] > div:has(div.stSubheader) {
        background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 1.5rem !important;
    }
    .stCheckbox { margin-bottom: -22px !important; margin-top: 0px !important; transform: scale(0.8); transform-origin: left; }
    .dummy-label { height: 23px; margin-bottom: -22px; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(0, 0, 0, 0.4) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important; border-radius: 10px !important;
    }
    button[kind="primary"] { background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important; border: none !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'step' not in st.session_state: st.session_state.step = 1
if 'num_s1' not in st.session_state: st.session_state.num_s1 = 4
if 'num_s2' not in st.session_state: st.session_state.num_s2 = 4

# --- LOGIN ---
if st.session_state.step == 1:
    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<h1 style='text-align: center; color: white;'>✨ Analytics Pro</h1>", unsafe_allow_html=True)
        with st.container():
            e_in = st.text_input("School Email", placeholder="first.last@k12.leanderisd.org")
            if st.button("Initialize Dashboard", use_container_width=True, type="primary"):
                if re.match(r"^([a-z]+)\.([a-z]+)(\d*)@k12\.leanderisd\.org$", e_in.lower().strip()):
                    match = re.match(r"^([a-z]+)\.([a-z]+)", e_in.lower().strip())
                    st.session_state.real_name = f"{match.group(1).capitalize()} {match.group(2).capitalize()}"
                    st.session_state.step = 2
                    st.rerun()
                else: st.error("Verification failed")

# --- DASHBOARD ---
elif st.session_state.step == 2:
    st.markdown(f"#### 🎓 Student: **{st.session_state.real_name}**")
    
    st.toggle("Sync Semester 2 to Semester 1", key="sync_toggle", on_change=trigger_sync)

    def grade_row(sem, i, cycles):
        cols = st.columns([2.5, 1, 1, 1], gap="medium")
        # Ensure we always pull the current "true" value for the box
        stored_val = st.session_state.get(f"{sem}c{i}_val", "")
        
        with cols[0]:
            st.markdown('<div class="dummy-label"></div>', unsafe_allow_html=True)
            st.selectbox(f"Class {i+1}", [""] + ALL_CLASSES, 
                             index=ALL_CLASSES.index(stored_val)+1 if stored_val in ALL_CLASSES else 0,
                             key=f"{sem}c{i}_widget", on_change=on_class_change, args=(sem, i),
                             label_visibility="collapsed")
        
        grades = []
        for idx, cyc in enumerate(cycles):
            with cols[idx+1]:
                if cyc == CURRENT_CYCLE:
                    is_na = st.checkbox("N/A", key=f"{sem}na{cyc}_{i}")
                else:
                    st.markdown('<div class="dummy-label"></div>', unsafe_allow_html=True)
                    is_na = False
                
                if is_na:
                    st.text_input(f"C{cyc}", "N/A", disabled=True, key=f"{sem}g{cyc}_{i}", label_visibility="collapsed")
                    grades.append("N/A")
                else:
                    val = st.text_input(f"C{cyc}", value="", key=f"{sem}g{cyc}_{i}", label_visibility="collapsed", placeholder=f"C{cyc}")
                    grades.append(val)
        return st.session_state.get(f"{sem}c{i}_val", ""), grades

    t1, t2 = st.tabs(["📊 Semester I", "📊 Semester II"])
    
    with t1:
        st.subheader("First Semester")
        s1_data = [grade_row("S1", i, [1, 2, 3]) for i in range(st.session_state.num_s1)]
        b1, b2, _ = st.columns([0.4, 0.4, 3])
        if b1.button("➕ Add", key="as1", disabled=st.session_state.num_s1 >= MAX_CLASSES):
            st.session_state.num_s1 += 1
            if st.session_state.sync_toggle: trigger_sync()
            st.rerun()
        if b2.button("➖ Drop", key="rs1", disabled=st.session_state.num_s1 <= MIN_CLASSES):
            st.session_state.num_s1 -= 1
            if st.session_state.sync_toggle: trigger_sync()
            st.rerun()

    with t2:
        st.subheader("Second Semester")
        s2_data = [grade_row("S2", i, [4, 5, 6]) for i in range(st.session_state.num_s2)]
        b3, b4, _ = st.columns([0.4, 0.4, 3])
        # Disable Sem 2 manual Add/Drop if sync is active
        if b3.button("➕ Add", key="as2", disabled=st.session_state.num_s2 >= MAX_CLASSES or st.session_state.sync_toggle):
            st.session_state.num_s2 += 1
            st.rerun()
        if b4.button("➖ Drop", key="rs2", disabled=st.session_state.num_s2 <= MIN_CLASSES or st.session_state.sync_toggle):
            st.session_state.num_s2 -= 1
            st.rerun()

    st.divider()
    if st.button("Generate Performance Report", type="primary", use_container_width=True):
        error = validate_all_grades(s1_data, s2_data)
        if error: st.error(f"⚠️ {error}")
        else:
            final = get_detailed_gpa(s1_data + s2_data)
            if final:
                df = pd.DataFrame(final)
                avg = df["GPA"].mean()
                st.markdown(f'<div style="text-align:center; padding:20px; border-radius:15px; background:rgba(168,85,247,0.1); border:1px solid #a855f7;"><h3 style="margin:0; color:#a855f7;">Calculated GPA</h3><h1 style="margin:0; font-size:4rem;">{avg:.4f}</h1></div>', unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, hide_index=True)
