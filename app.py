import streamlit as st
import pandas as pd
import re

# --- 1. DATA SETUP ---
LEVEL_3 = ["English III AP", "English III IB", "English IV AP", "English IV IB", "Calculus AB AP", "Calculus BC AP", "Math: Analysis & Appr IB SL", "Math: Analysis & Appr IB HL", "Math: Application & Int IB SL", "Math: Application & Int IB HL", "Precalculus AP", "Statistics AP", "Biology AP", "Biology IB SL", "Biology IB HL", "Chemistry AP", "Chemistry IB SL", "Chemistry IB HL", "Environmental Science AP", "Physics 1 AP", "Physics 2 AP", "Physics C: Mechanics AP", "Physics IB SL", "Physics IB HL", "European History AP", "History of the Americas IB", "Human Geography AP", "Macroeconomics AP", "Microeconomics AP", "Psychology AP", "Psychology IB", "U.S. Government AP", "U.S. History AP", "World History AP", "Chinese IV AP", "French IV AP", "French IB SL", "French IB HL", "Latin IV AP", "Latin IB SL", "Latin IB HL", "Spanish IV AP", "Spanish V AP", "Spanish IB SL", "Spanish IB HL"]
LEVEL_2 = ["AP Seminar", "English I Advanced", "English I QUEST", "English II Advanced", "English II QUEST", "Algebra I Advanced", "Algebra II Advanced", "Geometry Advanced", "Pre-Calculus Advanced", "Pre-Calculus OnRamps", "Pre-Calculus IB Prep", "Biology Advanced", "Chemistry Advanced", "Investigations in Psychology", "Chinese II Advanced", "Chinese III Advanced", "French II Advanced", "French III Advanced", "French V Advanced", "Latin II Advanced", "Latin III Advanced", "Spanish II Advanced", "Spanish III Advanced", "Advanced Language or Career Applications", "Seminar in Languages other than English", "Advanced Spanish"]
LEVEL_1 = ["English I", "English II", "English III", "English IV", "Algebra I", "Algebra II", "Algebraic Reasoning", "College Prep Math", "Geometry", "Math Models", "Pre-Calculus", "Statistics", "Astronomy", "Biology", "Chemistry", "Environmental Systems", "Earth & Space Science", "Earth Systems Science", "Integrated Physics and Chemistry", "Physics", "Specialized Topics in Science", "An American Experience", "African American Studies", "Economics", "Mexican American Studies", "New Testament Bible & Amer Civ", "Old Testament Bible & Amer Civ", "Personal Financial Literacy", "Psychology", "Sociology", "U.S. Government", "U.S. History", "World Geography", "World History", "American Sign Language I", "American Sign Language II", "American Sign Language III", "American Sign Language IV", "Chinese I", "Chinese II", "Chinese III", "Chinese IV", "French I", "French II", "Latin I", "Latin II", "Spanish I", "Spanish II", "Spanish III"]
ALL_CLASSES = sorted(list(set(LEVEL_3 + LEVEL_2 + LEVEL_1)))

# --- 2. GPA CALCULATION ---
def calculate_gpa(s1_data, s2_data):
    total_pts, total_cls = 0, 0
    for row in (s1_data + s2_data):
        cls, g1, g2, g3 = row
        if not cls: continue
        grades = [float(g) for g in [g1, g2, g3] if g.replace('.','',1).isdigit()]
        if not grades: continue
        avg = sum(grades) / len(grades)
        base = (avg - 60) / 10 if avg >= 70 else 0 
        if cls in LEVEL_3: base += 1.0
        elif cls in LEVEL_2: base += 0.5
        total_pts += base
        total_cls += 1
    return round(total_pts / total_cls, 3) if total_cls > 0 else 0.0

# --- 3. SMART SYNC CALLBACK ---
def on_class_change(sem, i):
    # This captures the manual change in the UI
    new_val = st.session_state[f"{sem}c{i}_widget_{st.session_state.sync_toggle}"]
    st.session_state[f"{sem}c{i}_val"] = new_val
    
    if st.session_state.sync_toggle:
        if sem == "S1":
            # Push to S2 physically
            st.session_state[f"S2c{i}_val"] = new_val
        elif sem == "S2":
            # If S2 becomes different from S1, KILL TOGGLE
            if new_val != st.session_state.get(f"S1c{i}_val", ""):
                st.session_state.sync_toggle = False

# --- 4. APP UI ---
st.set_page_config(page_title="Glenn HS GPA", layout="wide")

if 'step' not in st.session_state: st.session_state.step = 1
if 'num_s1' not in st.session_state: st.session_state.num_s1 = 4
if 'num_s2' not in st.session_state: st.session_state.num_s2 = 4
if 'sync_toggle' not in st.session_state: st.session_state.sync_toggle = False

if st.session_state.step == 1:
    st.title("🏆 GPA Calculator")
    e_in = st.text_input("School Email")
    if st.button("Start"):
        if re.match(r"^([a-z]+)\.([a-z]+)(\d*)@k12\.leanderisd\.org$", e_in.lower().strip()):
            match = re.match(r"^([a-z]+)\.([a-z]+)", e_in.lower().strip())
            st.session_state.real_name = f"{match.group(1).capitalize()} {match.group(2).capitalize()}"
            st.session_state.step = 2
            st.rerun()
        else: st.error("Use @k12.leanderisd.org email")

elif st.session_state.step == 2:
    st.header(f"Welcome, {st.session_state.real_name}")
    
    sync_ui = st.toggle("Sync Semester 2 to Semester 1", value=st.session_state.sync_toggle)
    if sync_ui != st.session_state.sync_toggle:
        st.session_state.sync_toggle = sync_ui
        if sync_ui:
            st.session_state.num_s2 = st.session_state.num_s1
            for i in range(st.session_state.num_s1):
                st.session_state[f"S2c{i}_val"] = st.session_state.get(f"S1c{i}_val", "")
        st.rerun()

    def grade_row(sem, i, start_c):
        c_sel, c_1, c_2, c_3 = st.columns([2.5, 1, 1, 1])
        stored_val = st.session_state.get(f"{sem}c{i}_val", "")
        
        with c_sel:
            # The secret: Adding the toggle state to the KEY forces a physical UI refresh
            st.selectbox(
                f"{sem} Class {i+1}", 
                [""] + ALL_CLASSES, 
                index=ALL_CLASSES.index(stored_val)+1 if stored_val in ALL_CLASSES else 0,
                key=f"{sem}c{i}_widget_{st.session_state.sync_toggle}",
                on_change=on_class_change,
                args=(sem, i)
            )
        with c_1: g1 = st.text_input(f"C{start_c}", value="0", key=f"{sem}g{start_c}_{i}")
        with c_2: g2 = st.text_input(f"C{start_c+1}", value="0", key=f"{sem}g{start_c+1}_{i}")
        with c_3: g3 = st.text_input(f"C{start_c+2}", value="0", key=f"{sem}g{start_c+2}_{i}")
        return st.session_state.get(f"{sem}c{i}_val", ""), g1, g2, g3

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Semester 1")
        b1, b2 = st.columns(2)
        if b1.button("➕ S1"): 
            st.session_state.num_s1 += 1
            if st.session_state.sync_toggle: st.session_state.num_s2 = st.session_state.num_s1
            st.rerun()
        if b2.button("➖ S1") and st.session_state.num_s1 > 1:
            st.session_state.num_s1 -= 1
            if st.session_state.sync_toggle: st.session_state.num_s2 = st.session_state.num_s1
            st.rerun()
        s1_data = [grade_row("S1", i, 1) for i in range(st.session_state.num_s1)]

    with col_r:
        st.subheader("Semester 2")
        b3, b4 = st.columns(2)
        if b3.button("➕ S2", disabled=st.session_state.sync_toggle): 
            st.session_state.num_s2 += 1; st.rerun()
        if b4.button("➖ S2", disabled=st.session_state.sync_toggle) and st.session_state.num_s2 > 1:
            st.session_state.num_s2 -= 1; st.rerun()
        s2_data = [grade_row("S2", i, 4) for i in range(st.session_state.num_s2)]

    if st.button("📊 Calculate Final GPA", use_container_width=True):
        st.metric("Final GPA", f"{calculate_gpa(s1_data, s2_data)}")
        st.balloons()
