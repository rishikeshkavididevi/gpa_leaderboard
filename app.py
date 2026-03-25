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

# --- 2. GPA MATH & VALIDATION ---
def get_detailed_gpa(data):
    results = []
    for cls, grades in data:
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

def validate_all_grades(s1_data, s2_data):
    """Returns an error message if grades are missing, otherwise returns None."""
    for sem_name, sem_data, sem_key in [("Semester 1", s1_data, "S1"), ("Semester 2", s2_data, "S2")]:
        for i, (cls, grades) in enumerate(sem_data):
            if not cls: continue 
            for j, grade in enumerate(grades):
                cycle_num = (1, 2, 3)[j] if sem_name == "Semester 1" else (4, 5, 6)[j]
                
                # Check if it's the CURRENT cycle (Cycle 5)
                is_current = (cycle_num == CURRENT_CYCLE)
                
                # If grade is empty OR looks like the placeholder "C1", "C2" etc
                if not str(grade).strip() or str(grade).strip() == f"C{cycle_num}":
                    if is_current:
                        # Check if N/A checkbox is checked in session state
                        if not st.session_state.get(f"{sem_key}na{cycle_num}_{i}", False):
                            return f"Missing grade or N/A for {cls} in Cycle {cycle_num}"
                    else:
                        # Mandatory for all other cycles
                        return f"Please enter a grade for {cls} in Cycle {cycle_num}"
    return None

# --- 3. APP UI ---
st.set_page_config(page_title="Analytics Pro", page_icon="✨", layout="wide")

# AESTHETIC DARK CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com');
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background: radial-gradient(circle at top left, #1e1e2f, #111119); font-family: 'Inter', sans-serif; color: #e0e0e0; }
    div[data-testid="stVerticalBlock"] > div:has(div.stSubheader) {
        background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 2rem !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(0, 0, 0, 0.4) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important; border-radius: 10px !important;
    }
    .dummy-label { height: 23px; margin-bottom: -18px; }
    button[kind="primary"] { background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important;}
    </style>
    """, unsafe_allow_html=True)

if 'step' not in st.session_state: st.session_state.step = 1
if 'num_s1' not in st.session_state: st.session_state.num_s1, st.session_state.num_s2 = 4, 4

# --- LOGIN SCREEN ---
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

# --- MAIN DASHBOARD ---
elif st.session_state.step == 2:
    st.markdown(f"#### 🎓 Student: **{st.session_state.real_name}**")
    
    def grade_row(sem, i, cycles):
        cols = st.columns([2.5, 1, 1, 1], gap="medium")
        with cols[0]:
            st.markdown('<div class="dummy-label"></div>', unsafe_allow_html=True)
            cls = st.selectbox(f"Class {i+1}", [""] + ALL_CLASSES, key=f"{sem}c{i}", label_visibility="collapsed")
        
        grades = []
        for j, cyc in enumerate(cycles):
            with cols[j+1]:
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
        return cls, grades

    t1, t2 = st.tabs(["📊 Semester I", "📊 Semester II"])
    with t1:
        st.subheader("Semester I (Cycles 1-3)")
        s1_data = [grade_row("S1", i, [1, 2, 3]) for i in range(st.session_state.num_s1)]
        b1, b2, _ = st.columns([0.4, 0.4, 3])
        if b1.button("➕ Add", key="as1"): st.session_state.num_s1 += 1; st.rerun()
        if b2.button("➖ Drop", key="rs1") and st.session_state.num_s1 > 1: st.session_state.num_s1 -= 1; st.rerun()

    with t2:
        st.subheader("Semester II (Cycles 4-6)")
        s2_data = [grade_row("S2", i, [4, 5, 6]) for i in range(st.session_state.num_s2)]
        b3, b4, _ = st.columns([0.4, 0.4, 3])
        if b3.button("➕ Add", key="as2"): st.session_state.num_s2 += 1; st.rerun()
        if b4.button("➖ Drop", key="rs2") and st.session_state.num_s2 > 1: st.session_state.num_s2 -= 1; st.rerun()

    st.divider()
    if st.button("Generate Performance Report", type="primary", use_container_width=True):
        # VALIDATION CHECK
        error = validate_all_grades(s1_data, s2_data)
        if error:
            st.error(f"⚠️ {error}")
        else:
            results = get_detailed_gpa(s1_data + s2_data)
            if results:
                df = pd.DataFrame(results)
                avg = df["GPA"].mean()
                st.markdown(f"""
                    <div style="text-align: center; padding: 20px; border-radius: 15px; background: rgba(168, 85, 247, 0.1); border: 1px solid #a855f7;">
                        <h3 style="margin: 0; color: #a855f7;">Calculated GPA</h3>
                        <h1 style="margin: 0; font-size: 4rem;">{avg:.4f}</h1>
                    </div>
                """, unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("Please enter at least one class.")
