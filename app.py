import streamlit as st
import pandas as pd
import re
from datetime import datetime
from supabase import create_client, Client

# --- 0. ADMIN CONTROL ---
CURRENT_CYCLE = 5

# --- INITIALIZE SUPABASE (direct client, not st.connection) ---
SUPABASE_URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

# --- 3. AUTH HELPERS ---
def get_user_from_session():
    """Restore Supabase session from stored tokens."""
    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")
    if not access_token or not refresh_token:
        return None
    try:
        session = supabase.auth.set_session(access_token, refresh_token)
        return session.user if session else None
    except:
        return None

def sign_out():
    try:
        supabase.auth.sign_out()
    except:
        pass
    for key in ["access_token", "refresh_token", "user_id", "real_name", "email", "step"]:
        st.session_state.pop(key, None)
    st.session_state.step = 1

# --- 4. PERSISTENT STATE HELPERS ---
SAVE_KEY_PREFIXES = ["S1c", "S2c", "S1g", "S2g", "num_s", "sync_toggle"]

def save_user_data():
    """Upsert grade/class data to Supabase for the authenticated user."""
    user_id = st.session_state.get("user_id")
    if not user_id:
        return
    keys_to_save = {}
    for key, val in st.session_state.items():
        if any(key.startswith(p) for p in SAVE_KEY_PREFIXES):
            keys_to_save[key] = val
    try:
        supabase.table("user_data").upsert({
            "user_id": user_id,
            "data": keys_to_save,
            "updated_at": datetime.now().isoformat()
        }).execute()
    except:
        pass

def load_user_data():
    """Load saved grade/class data from Supabase for the authenticated user."""
    user_id = st.session_state.get("user_id")
    if not user_id:
        return
    try:
        result = supabase.table("user_data").select("data").eq("user_id", user_id).execute()
        if result.data:
            saved = result.data[0]["data"]
            for k, v in saved.items():
                st.session_state[k] = v
    except:
        pass

# --- 5. SMART SYNC CALLBACK ---
def on_class_change(sem, i):
    new_val = st.session_state[f"{sem}c{i}_widget_{st.session_state.sync_toggle}"]
    st.session_state[f"{sem}c{i}_val"] = new_val
    if st.session_state.sync_toggle:
        if sem == "S1":
            st.session_state[f"S2c{i}_val"] = new_val
        elif sem == "S2":
            if new_val != st.session_state.get(f"S1c{i}_val", ""):
                st.session_state.sync_toggle = False
    save_user_data()

# --- 6. APP UI ---
st.set_page_config(page_title="Analytics Pro", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com');
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stStatusWidget"], .stAppDeployButton {display:none;}
    .stApp {
        background: radial-gradient(circle at top left, #1e1e2f, #111119);
        font-family: 'Inter', sans-serif;
        color: #e0e0e0;
    }
    div[data-testid="stVerticalBlock"] > div:has(div.stSubheader) {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 30px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(0, 0, 0, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 12px !important;
    }
    button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 3rem !important;
        font-weight: 700 !important;
        color: #a855f7 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE DEFAULTS ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'num_s1' not in st.session_state: st.session_state.num_s1, st.session_state.num_s2 = 7, 7
if 'sync_toggle' not in st.session_state: st.session_state.sync_toggle = False
if 'magic_sent' not in st.session_state: st.session_state.magic_sent = False

# --- RESTORE SESSION IF TOKENS EXIST ---
if st.session_state.step == 1 and not st.session_state.magic_sent:
    user = get_user_from_session()
    if user:
        email = user.email
        match = re.match(r"^([a-z]+)\.([a-z]+)", email.lower())
        st.session_state.real_name = f"{match.group(1).capitalize()} {match.group(2).capitalize()}" if match else email
        st.session_state.email = email
        st.session_state.user_id = user.id
        st.session_state.step = 2
        load_user_data()

# --- STEP 1: LOGIN ---
if st.session_state.step == 1:
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("<h1 style='text-align: center; color: white;'>✨ Analytics Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Premium Academic Insight Engine</p>", unsafe_allow_html=True)
        with st.container():
            if not st.session_state.magic_sent:
                e_in = st.text_input("School Email", placeholder="your.name@k12.leanderisd.org")
                if st.button("Initialize Dashboard", use_container_width=True, type="primary"):
                    email_clean = e_in.lower().strip()
                    if re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email_clean):
                        try:
                            supabase.auth.sign_in_with_otp({
                                "email": email_clean,
                                "options": {"should_create_user": True}
                            })
                            st.session_state.pending_email = email_clean
                            st.session_state.magic_sent = True
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Could not send login email: {ex}")
                    else:
                        st.error("Please enter a valid email address.")
            else:
                pending = st.session_state.get("pending_email", "your school email")
                st.info(f"📬 A 6-digit code was sent to **{pending}**. Check your inbox.")
                otp_code = st.text_input("Enter your code", placeholder="123456", max_chars=6)
                if st.button("Verify Code", use_container_width=True, type="primary"):
                    try:
                        response = supabase.auth.verify_otp({
                            "email": pending,
                            "token": otp_code.strip(),
                            "type": "email"
                        })
                        user = response.user
                        session = response.session
                        if user and session:
                            st.session_state.access_token = session.access_token
                            st.session_state.refresh_token = session.refresh_token
                            st.session_state.user_id = user.id
                            st.session_state.email = pending
                            match = re.match(r"^([a-z]+)\.([a-z]+)", pending)
                            if match:
                                st.session_state.real_name = f"{match.group(1).capitalize()} {match.group(2).capitalize()}"
                            else:
                                st.session_state.real_name = pending.split("@")[0].capitalize()
                            st.session_state.magic_sent = False
                            try:
                                supabase.table("user_logins").insert({
                                    "name": st.session_state.real_name,
                                    "email": pending,
                                    "login_time": datetime.now().isoformat()
                                }).execute()
                            except:
                                pass
                            load_user_data()
                            st.session_state.step = 2
                            st.rerun()
                        else:
                            st.error("Invalid or expired code. Please try again.")
                    except Exception as ex:
                        st.error(f"Verification failed: {ex}")
                if st.button("← Use a different email"):
                    st.session_state.magic_sent = False
                    st.rerun()

# --- STEP 2: DASHBOARD ---
elif st.session_state.step == 2:
    # Auto-save on every rerun (catches grade text input changes)
    save_user_data()

    col_name, col_out = st.columns([5, 1])
    with col_name:
        st.markdown(f"#### Logged in as **{st.session_state.real_name}**")
    with col_out:
        if st.button("Sign Out", use_container_width=True):
            sign_out()
            st.rerun()

    c1, c2 = st.columns([3, 1])
    with c2:
        sync_ui = st.toggle("Auto-Sync Semesters", value=st.session_state.sync_toggle)

    if sync_ui != st.session_state.sync_toggle:
        st.session_state.sync_toggle = sync_ui
        if sync_ui:
            st.session_state.num_s2 = st.session_state.num_s1
            for i in range(st.session_state.num_s1):
                st.session_state[f"S2c{i}_val"] = st.session_state.get(f"S1c{i}_val", "")
        save_user_data()
        st.rerun()

    def grade_row(sem, i, cycles):
        cols = st.columns([3, 1, 1, 1])
        stored_val = st.session_state.get(f"{sem}c{i}_val", "")
        with cols[0]:
            cls = st.selectbox(f"Class {i+1}", [""] + ALL_CLASSES,
                               index=ALL_CLASSES.index(stored_val)+1 if stored_val in ALL_CLASSES else 0,
                               key=f"{sem}c{i}_widget_{st.session_state.sync_toggle}",
                               on_change=on_class_change, args=(sem, i), label_visibility="collapsed")
        grades = []
        for j, cyc in enumerate(cycles):
            with cols[j+1]:
                if cyc > CURRENT_CYCLE:
                    st.text_input(f"C{cyc}", "Locked", disabled=True, key=f"{sem}g{cyc}_{i}", label_visibility="collapsed")
                    grades.append(None)
                else:
                    saved_grade = st.session_state.get(f"{sem}g{cyc}_{i}", "")
                    g = st.text_input(f"C{cyc}", placeholder=f"C{cyc}", key=f"{sem}g{cyc}_{i}",
                                      value=saved_grade, label_visibility="collapsed")
                    grades.append(g)
        return cls, grades

    s1_data, s2_data = [], []
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.subheader("Semester 1")
        for i in range(st.session_state.num_s1):
            s1_data.append(grade_row("S1", i, [1, 2, 3]))

    with col_s2:
        st.subheader("Semester 2")
        for i in range(st.session_state.num_s2):
            s2_data.append(grade_row("S2", i, [4, 5, 6]))

    if st.button("Calculate Final Analytics", type="primary"):
        res1 = get_detailed_gpa(s1_data)
        res2 = get_detailed_gpa(s2_data)
        all_gpas = [r['GPA'] for r in res1 + res2]
        if all_gpas:
            final_gpa = sum(all_gpas) / len(all_gpas)
            st.metric("Estimated Weighted GPA", f"{final_gpa:.4f}")
            st.dataframe(pd.DataFrame(res1 + res2), hide_index=True, use_container_width=True)
            try:
                supabase.table("gpa_results").insert({
                    "user_id": st.session_state.user_id,
                    "name": st.session_state.real_name,
                    "email": st.session_state.email,
                    "gpa": round(final_gpa, 4),
                    "calculated_at": datetime.now().isoformat()
                }).execute()
            except:
                pass
