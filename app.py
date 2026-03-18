import streamlit as st
import pandas as pd
import sqlite3
import re
import time

# --- 0. ADMIN CONTROL ---
CURRENT_CYCLE = 4 

# --- 1. DATA & DATABASE SETUP ---
LEVEL_3 = ["English III AP", "English III IB", "English IV AP", "English IV IB", "Calculus AB AP", "Calculus BC AP", "Math: Analysis & Appr IB SL", "Math: Analysis & Appr IB HL", "Math: Application & Int IB SL", "Math: Application & Int IB HL", "Precalculus AP", "Statistics AP", "Biology AP", "Biology IB SL", "Biology IB HL", "Chemistry AP", "Chemistry IB SL", "Chemistry IB HL", "Environmental Science AP", "Physics 1 AP", "Physics 2 AP", "Physics C: Mechanics AP", "Physics IB SL", "Physics IB HL", "European History AP", "History of the Americas IB", "Human Geography AP", "Macroeconomics AP", "Microeconomics AP", "Psychology AP", "Psychology IB", "U.S. Government AP", "U.S. History AP", "World History AP", "Chinese IV AP", "French IV AP", "French IB SL", "French IB HL", "Latin IV AP", "Latin IB SL", "Latin IB HL", "Spanish IV AP", "Spanish V AP", "Spanish IB SL", "Spanish IB HL"]
LEVEL_2 = ["AP Seminar", "English I Advanced", "English I QUEST", "English II Advanced", "English II QUEST", "Algebra I Advanced", "Algebra II Advanced", "Geometry Advanced", "Pre-Calculus Advanced", "Pre-Calculus OnRamps", "Pre-Calculus IB Prep", "Biology Advanced", "Chemistry Advanced", "Investigations in Psychology", "Chinese II Advanced", "Chinese III Advanced", "French II Advanced", "French III Advanced", "French V Advanced", "Latin II Advanced", "Latin III Advanced", "Spanish II Advanced", "Spanish III Advanced", "Advanced Language or Career Applications", "Seminar in Languages other than English", "Advanced Spanish"]
LEVEL_1 = ["English I", "English II", "English III", "English IV", "Algebra I", "Algebra II", "Algebraic Reasoning", "College Prep Math", "Geometry", "Math Models", "Pre-Calculus", "Statistics", "Astronomy", "Biology", "Chemistry", "Environmental Systems", "Earth & Space Science", "Earth Systems Science", "Integrated Physics and Chemistry", "Physics", "Specialized Topics in Science", "An American Experience", "African American Studies", "Economics", "Mexican American Studies", "New Testament Bible & Amer Civ", "Old Testament Bible & Amer Civ", "Personal Financial Literacy", "Psychology", "Sociology", "U.S. Government", "U.S. History", "World Geography", "World History", "American Sign Language I", "American Sign Language II", "American Sign Language III", "American Sign Language IV", "Chinese I", "Chinese II", "Chinese III", "Chinese IV", "French I", "French II", "Latin I", "Latin II", "Spanish I", "Spanish II", "Spanish III"]
ALL_CLASSES = sorted(list(set(LEVEL_3 + LEVEL_2 + LEVEL_1)))

def init_db():
    conn = sqlite3.connect('glenn_rankings.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, display_name TEXT, gpa REAL)')
    conn.commit()
    conn.close()

def validate_name(email):
    match = re.match(r"^([a-z]+)\.([a-z]+)(\d*)@k12\.leanderisd\.org$", email.lower().strip())
    return f"{match.group(1).capitalize()} {match.group(2).capitalize()}" if match else None

st.set_page_config(page_title="Glenn HS Leaderboard", layout="wide")

st.markdown("""
    <style>
    .stTextInput label, .stSelectbox label { display: none !important; }
    div[data-testid="column"] { padding: 0px 5px !important; }
    .stCheckbox { margin-top: -10px; }
    </style>
    """, unsafe_allow_html=True)

init_db()

if 'step' not in st.session_state: st.session_state.step = 1
if 'num_s1' not in st.session_state: st.session_state.num_s1 = 4
if 'num_s2' not in st.session_state: st.session_state.num_s2 = 4
if 'sync_toggle' not in st.session_state: st.session_state.sync_toggle = False
if 'show_sync_note' not in st.session_state: st.session_state.show_sync_note = 0
if 'calculated_gpa' not in st.session_state: st.session_state.calculated_gpa = None
if 'has_joined' not in st.session_state: st.session_state.has_joined = False
if 'breakdown_data' not in st.session_state: st.session_state.breakdown_data = None

def on_class_change(sem, i):
    key = f"{sem}c{i}_sync_{st.session_state.sync_toggle}"
    new_val = st.session_state[key]
    st.session_state[f"{sem}c{i}"] = new_val
    if st.session_state.sync_toggle:
        if sem == "S2":
            if new_val != st.session_state.get(f"S1c{i}", ""): st.session_state.sync_toggle = False
        elif sem == "S1": st.session_state[f"S2c{i}"] = new_val

nav_options = ["Join"]
if st.session_state.has_joined: nav_options.append("Leaderboard")
page = st.sidebar.radio("Navigate", nav_options)

if page == "Join":
    if st.session_state.step == 1:
        st.title("🏆 Verify Identity")
        e_in = st.text_input("School Email")
        if st.button("Verify"):
            name = validate_name(e_in)
            if name: 
                st.session_state.user_email, st.session_state.real_name, st.session_state.step = e_in, name, 2
                st.rerun()
            else: st.error("Invalid @k12.leanderisd.org email.")

    elif st.session_state.step == 2:
        st.header(f"Welcome, {st.session_state.real_name}")
        col_t1, col_t2 = st.columns(2)
        with col_t1: show_real = st.toggle("Show real name on leaderboard", value=True)
        with col_t2: sync_ui = st.toggle("Sync Semester 2 to Semester 1", value=st.session_state.sync_toggle)

        if sync_ui != st.session_state.sync_toggle:
            st.session_state.sync_toggle = sync_ui
            if sync_ui:
                st.session_state.num_s2 = st.session_state.num_s1
                for i in range(st.session_state.num_s1): st.session_state[f"S2c{i}"] = st.session_state.get(f"S1c{i}", "")
            st.rerun()

        st.markdown("---")
        col_l, col_r = st.columns(2)
        
        def grade_row(sem, i, start_c):
            c_sel, c_1, c_2, c_3 = st.columns([2.5, 1, 1, 1])
            curr_choice = st.session_state.get(f"{sem}c{i}", "")
            with c_sel:
                st.write(f"**{sem} Class {i+1}**")
                cls = st.selectbox("", [""] + ALL_CLASSES, index=ALL_CLASSES.index(curr_choice)+1 if curr_choice in ALL_CLASSES else 0, key=f"{sem}c{i}_sync_{st.session_state.sync_toggle}", on_change=on_class_change, args=(sem, i))
                st.session_state[f"{sem}c{i}"] = cls

            def cycle_cell(cycle_num, col_obj, label):
                with col_obj:
                    h_left, h_right = st.columns([1, 1.2])
                    with h_left: st.write(f"**{label}**")
                    is_na = (cycle_num == CURRENT_CYCLE and st.checkbox("N/A", key=f"{sem}na{cycle_num}_{i}"))
                    if cycle_num > CURRENT_CYCLE: return st.text_input("", value="Locked", disabled=True, key=f"{sem}g{cycle_num}_{i}") and "Locked"
                    if is_na: return st.text_input("", value="N/A", disabled=True, key=f"{sem}g{cycle_num}_{i}") and "N/A"
                    val = st.text_input("", value="0", key=f"{sem}g{cycle_num}_{i}")
                    try: return int(round(float(val))) if val.strip() != "" else ""
                    except: return ""

            return cls, cycle_cell(start_c, c_1, "C1" if sem=="S1" else "C4"), cycle_cell(start_c+1, c_2, "C2" if sem=="S1" else "C5"), cycle_cell(start_c+2, c_3, "C3" if sem=="S1" else "C6")

        with col_l:
            st.subheader("Semester 1")
            ca, cr = st.columns(2)
            if ca.button("➕ Add Class (S1)", disabled=st.session_state.num_s1 >= 8):
                st.session_state.num_s1 += 1
                if st.session_state.sync_toggle: st.session_state.num_s2 = st.session_state.num_s1
                st.rerun()
            if cr.button("➖ Remove Class (S1)", disabled=st.session_state.num_s1 <= 1):
                st.session_state.num_s1 -= 1
                if st.session_state.sync_toggle: st.session_state.num_s2 = st.session_state.num_s1
                st.rerun()
            s1_data = [grade_row("S1", i, 1) for i in range(st.session_state.num_s1)]

        with col_r:
            st.subheader("Semester 2")
            ca2, cr2 = st.columns(2)
            if ca2.button("➕ Add Class (S2)", disabled=st.session_state.num_s2 >= 8 or st.session_state.sync_toggle): st.session_state.num_s2 += 1; st.rerun()
            if cr2.button("➖ Remove Class (S2)", disabled=st.session_state.num_s2 <= 1 or st.session_state.sync_toggle): st.session_state.num_s2 -= 1; st.rerun()
            s2_data = [grade_row("S2", i, 4) for i in range(st.session_state.num_s2)]

        st.markdown("---")
        if st.button("Calculate GPA", type="primary"):
            def process(data, sem_label):
                res = []
                breakdown = []
                for idx, (cls, g1, g2, g3) in enumerate(data):
                    if not cls: return None, None, f"Select class for {sem_label} Row {idx+1}"
                    if "" in [g1, g2, g3]: return None, None, f"Fill grades for {cls} ({sem_label})"
                    vals = [v for v in [g1, g2, g3] if isinstance(v, int)]
                    if vals:
                        avg = sum(vals)/len(vals)
                        scale_max = 6.0 if cls in LEVEL_3 else (5.5 if cls in LEVEL_2 else 5.0)
                        class_gpa = 0.0 if avg < 70 else max(0.0, round(scale_max - ((100 - avg) * 0.1), 2))
                        res.append(class_gpa)
                        breakdown.append({"Class": cls, "Avg": round(avg, 1), "GPA": class_gpa})
                return res, breakdown, None

            s1_v, b1, e1 = process(s1_data, "S1")
            if e1: st.error(e1)
            else:
                s2_v, b2, e2 = process(s2_data, "S2")
                if e2: st.error(e2)
                else:
                    a1, a2 = sum(s1_v)/len(s1_v) if s1_v else 0, sum(s2_v)/len(s2_v) if s2_v else 0
                    st.session_state.calculated_gpa = round((a1 + a2) / 2, 4)
                    st.session_state.breakdown_data = {"S1": b1, "S2": b2, "S1_Avg": round(a1, 4), "S2_Avg": round(a2, 4)}

        if st.session_state.calculated_gpa is not None:
            st.info(f"### Final Combined GPA: **{st.session_state.calculated_gpa}**")
            
            # GPA Summary Tables
            sum_l, sum_r = st.columns(2)
            with sum_l:
                st.write("**Semester 1 Breakdown**")
                st.table(pd.DataFrame(st.session_state.breakdown_data["S1"]))
                st.write(f"**S1 Total Average: {st.session_state.breakdown_data['S1_Avg']}**")
            with sum_r:
                st.write("**Semester 2 Breakdown**")
                st.table(pd.DataFrame(st.session_state.breakdown_data["S2"]))
                st.write(f"**S2 Total Average: {st.session_state.breakdown_data['S2_Avg']}**")

            if st.button("🚀 Join Leaderboard"):
                conn = sqlite3.connect('glenn_rankings.db')
                c = conn.cursor()
                name = st.session_state.real_name if show_real else "Anonymous Grizzly"
                c.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?)', (st.session_state.user_email, name, st.session_state.calculated_gpa))
                conn.commit(); conn.close(); st.session_state.has_joined = True; st.rerun()

elif page == "Leaderboard":
    st.title("🏆 Glenn HS Leaderboard")
    conn = sqlite3.connect('glenn_rankings.db')
    df = pd.read_sql_query("SELECT display_name as 'Name', gpa as 'Weighted GPA' FROM users ORDER BY gpa DESC", conn)
    conn.close(); st.table(df)
