import streamlit as st
import pandas as pd
import re

# --- 0. ADMIN CONTROL ---
CURRENT_CYCLE = 5 

# --- 1. DATA SETUP ---
LEVEL_3 = ["English III AP", "English III IB", "English IV AP", "English IV IB", "Calculus AB AP", "Calculus BC AP", "Math: Analysis & Appr IB SL", "Math: Analysis & Appr IB HL", "Math: Application & Int IB SL", "Math: Application & Int IB HL", "Precalculus AP", "Statistics AP", "Biology AP", "Biology IB SL", "Biology IB HL", "Chemistry AP", "Chemistry IB SL", "Chemistry IB HL", "Environmental Science AP", "Physics 1 AP", "Physics 2 AP", "Physics C: Mechanics AP", "Physics IB SL", "Physics IB HL", "European History AP", "History of the Americas IB", "Human Geography AP", "Macroeconomics AP", "Microeconomics AP", "Psychology AP", "Psychology IB", "U.S. Government AP", "U.S. History AP", "World History AP", "Chinese IV AP", "French IV AP", "French IB SL", "French IB HL", "Latin IV AP", "Latin IB SL", "Latin IB HL", "Spanish IV AP", "Spanish V AP", "Spanish IB SL", "Spanish IB HL"]
LEVEL_2 = ["AP Seminar", "English I Advanced", "English I QUEST", "English II Advanced", "English II QUEST", "Algebra I Advanced", "Algebra II Advanced", "Geometry Advanced", "Pre-Calculus Advanced", "Pre-Calculus OnRamps", "Pre-Calculus IB Prep", "Biology Advanced", "Chemistry Advanced", "Investigations in Psychology", "Chinese II Advanced", "Chinese III Advanced", "French II Advanced", "French III Advanced", "French V Advanced", "Latin II Advanced", "Latin III Advanced", "Spanish II Advanced", "Spanish III Advanced", "Advanced Language or Career Applications", "Seminar in Languages other than English", "Advanced Spanish"]
LEVEL_1 = ["English I", "English II", "English III", "English IV", "Algebra I", "Algebra II", "Algebraic Reasoning", "College Prep Math", "Geometry", "Math Models", "Pre-Calculus", "Statistics", "Astronomy", "Biology", "Chemistry", "Environmental Systems", "Earth & Space Science", "Earth Systems Science", "Integrated Physics and Chemistry", "Physics", "Specialized Topics in Science", "An American Experience", "African American Studies", "Economics", "Mexican American Studies", "New Testament Bible & Amer Civ", "Old Testament Bible & Amer Civ", "Personal Financial Literacy", "Psychology", "Sociology", "U.S. Government", "U.S. History", "World Geography", "World History", "American Sign Language I", "American Sign Language II", "American Sign Language III", "American Sign Language IV", "Chinese I", "Chinese II", "Chinese III", "Chinese IV", "French I", "French II", "Latin I", "Latin II", "Spanish I", "Spanish II", "Spanish III"]
ALL_CLASSES = sorted(list(set(LEVEL_3 + LEVEL_2 + LEVEL_1)))

# --- 2. GPA MATH ---
def get_detailed_gpa(data):
    results = []
    for entry in data:
        cls, grades = entry[0], entry[1]
        if not cls: continue
        valid_grades = []
        for g in grades:
            try: valid_grades.append(float(g))
            except: continue 
        if not valid_grades: continue
        avg = sum(valid_grades) / len(valid_grades)
        max_gpa = 6.0 if cls in LEVEL_3 else 5.5 if cls in LEVEL_2 else 5.0
        class_gpa = max(0, max_gpa - ((100 - avg) * 0.1)) if avg >= 70 else 0.0
        results.append({"Class": cls, "GPA": round(class_gpa, 4)})
    return results

# --- 3. SMART SYNC CALLBACK ---
def on_class_change(sem, i):
    new_val = st.session_state[f"{sem}c{i}_widget_{st.session_state.sync_toggle}"]
    st.session_state[f"{sem}c{i}_val"] = new_val
    if st.session_state.sync_toggle:
        if sem == "S1":
            st.session_state[f"S2c{i}_val"] = new_val
        elif sem == "S2":
            if new_val != st.session_state.get(f"S1c{i}_val", ""):
                st.session_state.sync_toggle = False

# --- 4. APP UI ---
st.set_page_config(page_title="Analytics Pro", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com');
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stStatusWidget"], .stAppDeployButton {display:none;}
    .stApp { background: radial-gradient(circle at top left, #1e1e2f, #111119); font-family: 'Inter', sans-serif; color: #e0e0e0; }
    
    /* Clean Cards */
    div[data-testid="stVerticalBlock"] > div:has(div.stSubheader) {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem !important;
    }

    /* Input & Select Box Styling */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(0, 0, 0, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 10px !important;
    }

    /* Force Checkbox to be small and tight */
    .stCheckbox {
        margin-bottom: -18px !important;
        margin-top: 0px !important;
    }
    .stCheckbox label p {
        font-size: 0.75rem !important;
        color: #888 !important;
    }
    
    /* Placeholder for Alignment */
    .dummy-label {
        height: 23px;
        margin-bottom: -18px;
    }

    button[kind="primary"] { background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important; border: none !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'step' not in st.session_state: st.session_state.step = 1
if 'num_s1' not in st.session_state: st.session_state.num_s1, st.session_state.num_s2 = 4, 4
if 'sync_toggle' not in st.session_state: st.session_state.sync_toggle = False

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
                else: st.error("Verification failed: Use @k12.leanderisd.org")

elif st.session_state.step == 2:
    st.markdown(f"#### Welcome back, **{st.session_state.real_name}**")
    
    sync_ui = st.toggle("Auto-Sync Semesters", value=st.session_state.sync_toggle)
    if sync_ui != st.session_state.sync_toggle:
        st.session_state.sync_toggle = sync_ui
        if sync_ui:
            st.session_state.num_s2 = st.session_state.num_s1
            for i in range(st.session_state.num_s1):
                st.session_state[f"S2c{i}_val"] = st.session_state.get(f"S1c{i}_val", "")
        st.rerun()

    def grade_row(sem, i, cycles):
        cols = st.columns([3, 1, 1, 1], gap="medium")
        stored_val = st.session_state.get(f"{sem}c{i}_val", "")
        
        with cols[0]:
            # Add a vertical offset to class select so it aligns with the inputs below checkboxes
            st.markdown('<div class="dummy-label"></div>', unsafe_allow_html=True)
            cls = st.selectbox(f"Class {i+1}", [""] + ALL_CLASSES, 
                             index=ALL_CLASSES.index(stored_val)+1 if stored_val in ALL_CLASSES else 0,
                             key=f"{sem}c{i}_widget_{st.session_state.sync_toggle}",
                             on_change=on_class_change, args=(sem, i), label_visibility="collapsed")
        
        grades = []
        for j, cyc in enumerate(cycles):
            with cols[j+1]:
                # THE FIX: Checkboxes or Placeholders in every column to force height symmetry
                if cyc == CURRENT_CYCLE:
                    is_na = st.checkbox("N/A", key=f"{sem}na{cyc}_{i}")
                else:
                    st.markdown('<div class="dummy-label"></div>', unsafe_allow_html=True)
                    is_na = False
                
                if cyc > CURRENT_CYCLE:
                    st.text_input(f"C{cyc}", "Locked", disabled=True, key=f"{sem}g{cyc}_{i}", label_visibility="collapsed")
                    grades.append("Locked")
                elif is_na:
                    st.text_input(f"C{cyc}", "N/A", disabled=True, key=f"{sem}g{cyc}_{i}", label_visibility="collapsed")
                    grades.append("N/A")
                else:
                    val = st.text_input(f"C{cyc}", value="", key=f"{sem}g{cyc}_{i}", label_visibility="collapsed", placeholder=f"C{cyc}")
                    grades.append(val)
        return cls, grades

    t1, t2 = st.tabs(["📊 Semester I", "📊 Semester II"])
    
    with t1:
        st.subheader("First Semester (Cycles 1-3)")
        s1_data = [grade_row("S1", i, [1, 2, 3]) for i in range(st.session_state.num_s1)]
        b1, b2, _ = st.columns([0.4, 0.4, 3])
        if b1.button("➕ Add", key="add_s1"): 
            st.session_state.num_s1 += 1
            if st.session_state.sync_toggle: st.session_state.num_s2 = st.session_state.num_s1
            st.rerun()
        if b2.button("➖ Drop", key="rem_s1") and st.session_state.num_s1 > 1:
            st.session_state.num_s1 -= 1
            st.rerun()

    with t2:
        st.subheader("Second Semester (Cycles 4-6)")
        s2_data = [grade_row("S2", i, [4, 5, 6]) for i in range(st.session_state.num_s2)]
        b3, b4, _ = st.columns([0.4, 0.4, 3])
        if b3.button("➕ Add", key="add_s2"): 
            st.session_state.num_s2 += 1
            st.rerun()
        if b4.button("➖ Drop", key="rem_s2") and st.session_state.num_s2 > 1:
            st.session_state.num_s2 -= 1
            st.rerun()

    st.divider()
    if st.button("Generate Performance Report", type="primary", use_container_width=True):
        full_results = get_detailed_gpa(s1_data + s2_data)
        if full_results:
            df = pd.DataFrame(full_results)
            avg_gpa = df["GPA"].mean()
            st.metric("Estimated Cumulative GPA", f"{avg_gpa:.4f}")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("Enter grades to calculate.")
