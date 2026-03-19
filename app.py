import streamlit as st
import pandas as pd
import re

# --- 0. ADMIN CONTROL ---
CURRENT_CYCLE = 4 

# --- 1. DATA SETUP ---
LEVEL_3 = ["English III AP", "English III IB", "English IV AP", "English IV IB", "Calculus AB AP", "Calculus BC AP", "Math: Analysis & Appr IB SL", "Math: Analysis & Appr IB HL", "Math: Application & Int IB SL", "Math: Application & Int IB HL", "Precalculus AP", "Statistics AP", "Biology AP", "Biology IB SL", "Biology IB HL", "Chemistry AP", "Chemistry IB SL", "Chemistry IB HL", "Environmental Science AP", "Physics 1 AP", "Physics 2 AP", "Physics C: Mechanics AP", "Physics IB SL", "Physics IB HL", "European History AP", "History of the Americas IB", "Human Geography AP", "Macroeconomics AP", "Microeconomics AP", "Psychology AP", "Psychology IB", "U.S. Government AP", "U.S. History AP", "World History AP", "Chinese IV AP", "French IV AP", "French IB SL", "French IB HL", "Latin IV AP", "Latin IB SL", "Latin IB HL", "Spanish IV AP", "Spanish V AP", "Spanish IB SL", "Spanish IB HL"]
LEVEL_2 = ["AP Seminar", "English I Advanced", "English I QUEST", "English II Advanced", "English II QUEST", "Algebra I Advanced", "Algebra II Advanced", "Geometry Advanced", "Pre-Calculus Advanced", "Pre-Calculus OnRamps", "Pre-Calculus IB Prep", "Biology Advanced", "Chemistry Advanced", "Investigations in Psychology", "Chinese II Advanced", "Chinese III Advanced", "French II Advanced", "French III Advanced", "French V Advanced", "Latin II Advanced", "Latin III Advanced", "Spanish II Advanced", "Spanish III Advanced", "Advanced Language or Career Applications", "Seminar in Languages other than English", "Advanced Spanish"]
LEVEL_1 = ["English I", "English II", "English III", "English IV", "Algebra I", "Algebra II", "Algebraic Reasoning", "College Prep Math", "Geometry", "Math Models", "Pre-Calculus", "Statistics", "Astronomy", "Biology", "Chemistry", "Environmental Systems", "Earth & Space Science", "Earth Systems Science", "Integrated Physics and Chemistry", "Physics", "Specialized Topics in Science", "An American Experience", "African American Studies", "Economics", "Mexican American Studies", "New Testament Bible & Amer Civ", "Old Testament Bible & Amer Civ", "Personal Financial Literacy", "Psychology", "Sociology", "U.S. Government", "U.S. History", "World Geography", "World History", "American Sign Language I", "American Sign Language II", "American Sign Language III", "American Sign Language IV", "Chinese I", "Chinese II", "Chinese III", "Chinese IV", "French I", "French II", "Latin I", "Latin II", "Spanish I", "Spanish II", "Spanish III"]
ALL_CLASSES = sorted(list(set(LEVEL_3 + LEVEL_2 + LEVEL_1)))

# --- 2. GPA CALCULATION LOGIC ---
def calculate_gpa(s1_data, s2_data):
    total_points = 0
    total_classes = 0
    for row in (s1_data + s2_data):
        cls, g1, g2, g3 = row
        if not cls: continue
        
        grades = []
        for g in [g1, g2, g3]:
            try: grades.append(float(g))
            except: continue
        
        if not grades: continue
        avg = sum(grades) / len(grades)
        
        # Simple 4.0 base + weight (adjust as needed for Leander ISD 5.0/6.0)
        base = (avg - 60) / 10 if avg >= 70 else 0 
        if cls in LEVEL_3: base += 1.0
        elif cls in LEVEL_2: base += 0.5
        
        total_points += base
        total_classes += 1
    
    return round(total_points / total_classes, 3) if total_classes > 0 else 0.0

# --- 3. APP UI ---
st.set_page_config(page_title="Glenn HS GPA Calc", layout="wide")

if 'step' not in st.session_state: st.session_state.step = 1
if 'num_s1' not in st.session_state: st.session_state.num_s1 = 4
if 'num_s2' not in st.session_state: st.session_state.num_s2 = 4
if 'sync_toggle' not in st.session_state: st.session_state.sync_toggle = False

def on_class_change(sem, i):
    key = f"{sem}c{i}_sync_{st.session_state.sync_toggle}"
    val = st.session_state.get(key, "")
    st.session_state[f"{sem}c{i}"] = val
    if st.session_state.sync_toggle and sem == "S1":
        st.session_state[f"S2c{i}"] = val

if st.session_state.step == 1:
    st.title("🏆 GPA Calculator")
    e_in = st.text_input("School Email")
    if st.button("Start"):
        match = re.match(r"^([a-z]+)\.([a-z]+)(\d*)@k12\.leanderisd\.org$", e_in.lower().strip())
        if match:
            st.session_state.real_name = f"{match.group(1).capitalize()} {match.group(2).capitalize()}"
            st.session_state.step = 2
            st.rerun()
        else: st.error("Please use your @k12.leanderisd.org email.")

elif st.session_state.step == 2:
    st.header(f"Welcome, {st.session_state.real_name}")
    sync_ui = st.toggle("Sync Semester 2 Classes to Semester 1", value=st.session_state.sync_toggle)
    if sync_ui != st.session_state.sync_toggle:
        st.session_state.sync_toggle = sync_ui
        if sync_ui:
            st.session_state.num_s2 = st.session_state.num_s1
            for i in range(st.session_state.num_s1):
                st.session_state[f"S2c{i}"] = st.session_state.get(f"S1c{i}", "")
        st.rerun()

    def grade_row(sem, i, start_c):
        c_sel, c_1, c_2, c_3 = st.columns([2.5, 1, 1, 1])
        curr = st.session_state.get(f"{sem}c{i}", "")
        with c_sel:
            cls = st.selectbox(f"{sem} Class {i+1}", [""] + ALL_CLASSES, 
                             index=ALL_CLASSES.index(curr)+1 if curr in ALL_CLASSES else 0, 
                             key=f"{sem}c{i}_sync_{st.session_state.sync_toggle}", 
                             on_change=on_class_change, args=(sem, i))
        with c_1: g1 = st.text_input(f"C{start_c}", value="0", key=f"{sem}g{start_c}_{i}")
        with c_2: g2 = st.text_input(f"C{start_c+1}", value="0", key=f"{sem}g{start_c+1}_{i}")
        with c_3: g3 = st.text_input(f"C{start_c+2}", value="0", key=f"{sem}g{start_c+2}_{i}")
        return cls, g1, g2, g3

    col_l, col_r = st.columns(2)
    
    with col_l:
        st.subheader("Semester 1")
        ca1, cr1 = st.columns(2)
        if ca1.button("➕ Add Class (S1)", key="add_s1"): 
            st.session_state.num_s1 += 1
            if st.session_state.sync_toggle: st.session_state.num_s2 = st.session_state.num_s1
            st.rerun()
        if cr1.button("➖ Remove Class (S1)", key="rem_s1") and st.session_state.num_s1 > 1:
            st.session_state.num_s1 -= 1
            if st.session_state.sync_toggle: st.session_state.num_s2 = st.session_state.num_s1
            st.rerun()
        s1_data = [grade_row("S1", i, 1) for i in range(st.session_state.num_s1)]

    with col_r:
        st.subheader("Semester 2")
        ca2, cr2 = st.columns(2)
        # S2 Add/Remove buttons are disabled if Sync is on
        if ca2.button("➕ Add Class (S2)", key="add_s2", disabled=st.session_state.sync_toggle): 
            st.session_state.num_s2 += 1; st.rerun()
        if cr2.button("➖ Remove Class (S2)", key="rem_s2", disabled=st.session_state.sync_toggle) and st.session_state.num_s2 > 1:
            st.session_state.num_s2 -= 1; st.rerun()
        
        if st.session_state.sync_toggle:
            st.session_state.num_s2 = st.session_state.num_s1
            
        s2_data = [grade_row("S2", i, 4) for i in range(st.session_state.num_s2)]

    st.markdown("---")
    if st.button("📊 Calculate Final GPA", use_container_width=True):
        final_gpa = calculate_gpa(s1_data, s2_data)
        st.balloons()
        st.metric("Your Calculated GPA", f"{final_gpa}")

# Pro-tip: If you want to change the math to a 5.0 or 6.0 scale, let me know!
