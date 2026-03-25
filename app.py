import streamlit as st
import pandas as pd
import re

# --- 0. ADMIN CONTROL ---
CURRENT_CYCLE = 4 
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
            except: continue # Skips "Locked" or "N/A" strings

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
st.set_page_config(page_title="GPA Calculator", layout="wide")

if 'step' not in st.session_state: st.session_state.step = 1
if 'num_s1' not in st.session_state: st.session_state.num_s1, st.session_state.num_s2 = 4, 4
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
        else: st.error("Use your @k12.leanderisd.org email")

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

    def grade_row(sem, i, cycles):
        cols = st.columns([2.5, 1, 1, 1])
        stored_val = st.session_state.get(f"{sem}c{i}_val", "")
        with cols[0]:
            cls = st.selectbox(f"{sem} Class {i+1}", [""] + ALL_CLASSES, 
                             index=ALL_CLASSES.index(stored_val)+1 if stored_val in ALL_CLASSES else 0,
                             key=f"{sem}c{i}_widget_{st.session_state.sync_toggle}",
                             on_change=on_class_change, args=(sem, i))

        grades = []
        for j, cyc in enumerate(cycles):
            with cols[j+1]:
                if cyc > CURRENT_CYCLE:
                    st.text_input(f"C{cyc}", "Locked", disabled=True, key=f"{sem}g{cyc}_{i}")
                    grades.append("Locked")
                else:
                    is_na = st.checkbox("N/A", key=f"{sem}na{cyc}_{i}") if cyc == CURRENT_CYCLE else False
                    if is_na:
                        st.text_input(f"C{cyc}", "N/A", disabled=True, key=f"{sem}g{cyc}_{i}")
                        grades.append("N/A")
                    else:
                        val = st.text_input(f"C{cyc}", value="", key=f"{sem}g{cyc}_{i}")
                        grades.append(val)
        return cls, grades

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Semester 1")
        b1, b2 = st.columns(2)
        if b1.button("➕ Add Class (S1)"): 
            st.session_state.num_s1 += 1
            if st.session_state.sync_toggle: st.session_state.num_s2 = st.session_state.num_s1
            st.rerun()
        if b2.button("➖ Remove Class (S1)") and st.session_state.num_s1 > 1:
            st.session_state.num_s1 -= 1
            if st.session_state.sync_toggle: st.session_state.num_s2 = st.session_state.num_s1
            st.rerun()
        s1_data = [grade_row("S1", i, [1, 2, 3]) for i in range(st.session_state.num_s1)]

    with col_r:
        st.subheader("Semester 2")
        b3, b4 = st.columns(2)
        if b3.button("➕ Add Class (S2)"): 
            st.session_state.num_s2 += 1
            if st.session_state.sync_toggle and st.session_state.num_s2 != st.session_state.num_s1: st.session_state.sync_toggle = False
            st.rerun()
        if b4.button("➖ Remove Class (S2)") and st.session_state.num_s2 > 1:
            st.session_state.num_s2 -= 1
            if st.session_state.sync_toggle and st.session_state.num_s2 != st.session_state.num_s1: st.session_state.sync_toggle = False
            st.rerun()
        s2_data = [grade_row("S2", i, [4, 5, 6]) for i in range(st.session_state.num_s2)]

    st.markdown("---")
    if st.button("📊 Calculate Final Breakdown", use_container_width=True):
        errors = []
        s1_active = [r for r in s1_data if r[0] != ""]
        s2_active = [r for r in s2_data if r[0] != ""]

        if not s1_active: errors.append("Select at least one class for Semester 1.")
        if not s2_active: errors.append("Select at least one class for Semester 2.")

        for sem, active_rows in [("S1", s1_active), ("S2", s2_active)]:
            for cls, grades in active_rows:
                if any(g == "" for g in grades):
                    errors.append(f"Missing grade in {sem} for '{cls}'.")

        if errors:
            for err in set(errors): st.error(err)
        else:
            s1_res = get_detailed_gpa(s1_active)
            s2_res = get_detailed_gpa(s2_active)
            s1_avg = sum([x['GPA'] for x in s1_res]) / len(s1_res)
            s2_avg = sum([x['GPA'] for x in s2_res]) / len(s2_res)

            st.balloons()
            st.subheader("📝 Detailed GPA Breakdown")
            t1, t2 = st.columns(2)
            with t1:
                st.table(pd.DataFrame(s1_res))
                st.info(f"**S1 Average: {round(s1_avg, 4)}**")
            with t2:
                st.table(pd.DataFrame(s2_res))
                st.info(f"**S2 Average: {round(s2_avg, 4)}**")
            st.success(f"### Final Combined GPA: {round((s1_avg + s2_avg) / 2, 4)}")
