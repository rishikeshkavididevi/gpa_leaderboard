import streamlit as st
import pandas as pd
import re

# --- 0. ADMIN CONTROL ---
# Host: Change this number (1-6) to control which cycles are open
CURRENT_CYCLE = 4 

# --- 1. DATA SETUP (Transcribed from Image) ---
LEVEL_3 = [
    "English III AP", "English III IB", "English IV AP", "English IV IB",
    "Calculus AB AP", "Calculus BC AP", "Math: Analysis & Appr IB SL", "Math: Analysis & Appr IB HL", "Math: Application & Int IB SL", "Math: Application & Int IB HL", "Precalculus AP", "Statistics AP",
    "Biology AP", "Biology IB SL", "Biology IB HL", "Chemistry AP", "Chemistry IB SL", "Chemistry IB HL", "Environmental Science AP", "Physics 1 AP", "Physics 2 AP", "Physics C: Mechanics AP", "Physics IB SL", "Physics IB HL",
    "European History AP", "History of the Americas IB", "Human Geography AP", "Macroeconomics AP", "Microeconomics AP", "Psychology AP", "Psychology IB", "U.S. Government AP", "U.S. History AP", "World History AP",
    "Chinese IV AP", "French IV AP", "French IB SL", "French IB HL", "Latin IV AP", "Latin IB SL", "Latin IB HL", "Spanish IV AP", "Spanish V AP", "Spanish IB SL", "Spanish IB HL"
]

LEVEL_2 = [
    "AP Seminar", # Added per request
    "English I Advanced", "English I QUEST", "English II Advanced", "English II QUEST",
    "Algebra I Advanced", "Algebra II Advanced", "Geometry Advanced", "Pre-Calculus Advanced", "Pre-Calculus OnRamps", "Pre-Calculus IB Prep",
    "Biology Advanced", "Chemistry Advanced",
    "Investigations in Psychology",
    "Chinese II Advanced", "Chinese III Advanced", "French II Advanced", "French III Advanced", "French V Advanced", "Latin II Advanced", "Latin III Advanced", "Spanish II Advanced", "Spanish III Advanced", "Advanced Language or Career Applications", "Seminar in Languages other than English", "Advanced Spanish"
]

LEVEL_1 = [
    "English I", "English II", "English III", "English IV",
    "Algebra I", "Algebra II", "Algebraic Reasoning", "College Prep Math", "Geometry", "Math Models", "Pre-Calculus", "Statistics",
    "Astronomy", "Biology", "Chemistry", "Environmental Systems", "Earth & Space Science", "Earth Systems Science", "Integrated Physics and Chemistry", "Physics", "Specialized Topics in Science",
    "An American Experience", "African American Studies", "Economics", "Mexican American Studies", "New Testament Bible & Amer Civ", "Old Testament Bible & Amer Civ", "Personal Financial Literacy", "Psychology", "Sociology", "U.S. Government", "U.S. History", "World Geography", "World History",
    "American Sign Language I", "American Sign Language II", "American Sign Language III", "American Sign Language IV", "Chinese I", "Chinese II", "Chinese III", "Chinese IV", "French I", "French II", "Latin I", "Latin II", "Spanish I", "Spanish II", "Spanish III"
]
ALL_CLASSES = sorted(list(set(LEVEL_3 + LEVEL_2 + LEVEL_1)))

# --- 2. GPA MATH ---
def calculate_gpa(s1_data, s2_data):
    def get_sem_points(data):
        pts = []
        for row in data:
            cls, g1, g2, g3 = row
            if not cls: continue
            
            # Filter out "Locked" or "N/A" strings
            valid_grades = []
            for g in [g1, g2, g3]:
                if isinstance(g, (int, float)): valid_grades.append(g)
            
            if not valid_grades: continue
            avg = sum(valid_grades) / len(valid_grades)
            
            # Base Max
            if cls in LEVEL_3: max_gpa = 6.0
            elif cls in LEVEL_2: max_gpa = 5.5
            else: max_gpa = 5.0
            
            # Deduction Logic
            class_gpa = max_gpa - ((100 - avg) * 0.1) if avg >= 70 else 0.0
            pts.append(max(0, class_gpa))
        return pts

    s1_pts = get_sem_points(s1_data)
    s2_pts = get_sem_points(s2_data)
    
    s1_avg = sum(s1_pts) / len(s1_pts) if s1_pts else 0.0
    s2_avg = sum(s2_pts) / len(s2_pts) if s2_pts else 0.0
    
    return s1_avg, s2_avg, (s1_avg + s2_avg) / 2

# --- 3. UI CALLBACKS ---
def handle_change(sem, i):
    new_val = st.session_state[f"{sem}c{i}_widget_{st.session_state.sync_toggle}"]
    st.session_state[f"{sem}c{i}_val"] = new_val
    if st.session_state.sync_toggle:
        if sem == "S1": st.session_state[f"S2c{i}_val"] = new_val
        elif sem == "S2" and new_val != st.session_state.get(f"S1c{i}_val", ""):
            st.session_state.sync_toggle = False

# --- 4. APP UI ---
st.set_page_config(page_title="Glenn HS GPA", layout="wide")

if 'step' not in st.session_state: st.session_state.step = 1
if 'num_s1' not in st.session_state: st.session_state.num_s1, st.session_state.num_s2 = 4, 4
if 'sync_toggle' not in st.session_state: st.session_state.sync_toggle = False

if st.session_state.step == 1:
    st.title("🏆 LISD 6.0 GPA Calculator")
    e_in = st.text_input("School Email")
    if st.button("Verify"):
        if re.match(r"^([a-z]+)\.([a-z]+)(\d*)@k12\.leanderisd\.org$", e_in.lower().strip()):
            match = re.match(r"^([a-z]+)\.([a-z]+)", e_in.lower().strip())
            st.session_state.real_name = f"{match.group(1).capitalize()} {match.group(2).capitalize()}"
            st.session_state.step = 2
            st.rerun()
        else: st.error("Use your @k12.leanderisd.org email")

elif st.session_state.step == 2:
    st.header(f"Welcome, {st.session_state.real_name}")
    st.info(f"Admin Info: System currently set to **Cycle {CURRENT_CYCLE}**")
    
    sync_ui = st.toggle("Sync Semester 2 Classes to Semester 1", value=st.session_state.sync_toggle)
    if sync_ui != st.session_state.sync_toggle:
        st.session_state.sync_toggle = sync_ui
        if sync_ui:
            st.session_state.num_s2 = st.session_state.num_s1
            for i in range(st.session_state.num_s1):
                st.session_state[f"S2c{i}_val"] = st.session_state.get(f"S1c{i}_val", "")
        st.rerun()

    def grade_row(sem, i, cycles):
        c_sel, c1, c2, c3 = st.columns([2.5, 1, 1, 1])
        stored_val = st.session_state.get(f"{sem}c{i}_val", "")
        
        with c_sel:
            st.selectbox(f"{sem} Class {i+1}", [""] + ALL_CLASSES, index=ALL_CLASSES.index(stored_val)+1 if stored_val in ALL_CLASSES else 0, key=f"{sem}c{i}_widget_{st.session_state.sync_toggle}", on_change=handle_change, args=(sem, i))
        
        cycle_grades = []
        for col, cyc_num in zip([c1, c2, c3], cycles):
            with col:
                if cyc_num > CURRENT_CYCLE:
                    st.text_input(f"Cycle {cyc_num}", value="Locked", disabled=True, key=f"{sem}g{cyc_num}_{i}")
                    cycle_grades.append("Locked")
                else:
                    # N/A Toggle for current cycle
                    is_na = False
                    if cyc_num == CURRENT_CYCLE:
                        is_na = st.checkbox("N/A", key=f"{sem}na{cyc_num}_{i}")
                    
                    if is_na:
                        st.text_input(f"Cycle {cyc_num}", value="N/A", disabled=True, key=f"{sem}g{cyc_num}_{i}")
                        cycle_grades.append("N/A")
                    else:
                        val = st.text_input(f"Cycle {cyc_num}", value="0", key=f"{sem}g{cyc_num}_{i}")
                        try: cycle_grades.append(float(val))
                        except: cycle_grades.append(0.0)
        
        return st.session_state.get(f"{sem}c{i}_val", ""), cycle_grades[0], cycle_grades[1], cycle_grades[2]

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Semester 1")
        if st.button("➕ Add S1"): 
            st.session_state.num_s1 += 1
            if st.session_state.sync_toggle: st.session_state.num_s2 = st.session_state.num_s1
            st.rerun()
        s1_data = [grade_row("S1", i, [1, 2, 3]) for i in range(st.session_state.num_s1)]

    with col_r:
        st.subheader("Semester 2")
        if st.button("➕ Add S2"): 
            st.session_state.num_s2 += 1
            if st.session_state.sync_toggle: st.session_state.sync_toggle = False
            st.rerun()
        s2_data = [grade_row("S2", i, [4, 5, 6]) for i in range(st.session_state.num_s2)]

    if st.button("📊 Calculate LISD GPA", use_container_width=True):
        s1_avg, s2_avg, total = calculate_gpa(s1_data, s2_data)
        st.balloons()
        m1, m2, m3 = st.columns(3)
        m1.metric("Sem 1", f"{round(s1_avg, 4)}")
        m2.metric("Sem 2", f"{round(s2_avg, 4)}")
        m3.metric("TOTAL GPA", f"{round(total, 4)}")
