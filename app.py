import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import re

# --- 0. ADMIN CONTROL ---
CURRENT_CYCLE = 4 

# --- 1. DATA SETUP ---
LEVEL_3 = ["English III AP", "English III IB", "English IV AP", "English IV IB", "Calculus AB AP", "Calculus BC AP", "Math: Analysis & Appr IB SL", "Math: Analysis & Appr IB HL", "Math: Application & Int IB SL", "Math: Analysis & Appr IB HL", "Precalculus AP", "Statistics AP", "Biology AP", "Biology IB SL", "Biology IB HL", "Chemistry AP", "Chemistry IB SL", "Chemistry IB HL", "Environmental Science AP", "Physics 1 AP", "Physics 2 AP", "Physics C: Mechanics AP", "Physics IB SL", "Physics IB HL", "European History AP", "History of the Americas IB", "Human Geography AP", "Macroeconomics AP", "Microeconomics AP", "Psychology AP", "Psychology IB", "U.S. Government AP", "U.S. History AP", "World History AP", "Chinese IV AP", "French IV AP", "French IB SL", "French IB HL", "Latin IV AP", "Latin IB SL", "Latin IB HL", "Spanish IV AP", "Spanish V AP", "Spanish IB SL", "Spanish IB HL"]
LEVEL_2 = ["AP Seminar", "English I Advanced", "English I QUEST", "English II Advanced", "English II QUEST", "Algebra I Advanced", "Algebra II Advanced", "Geometry Advanced", "Pre-Calculus Advanced", "Pre-Calculus OnRamps", "Pre-Calculus IB Prep", "Biology Advanced", "Chemistry Advanced", "Investigations in Psychology", "Chinese II Advanced", "Chinese III Advanced", "French II Advanced", "French III Advanced", "French V Advanced", "Latin II Advanced", "Latin III Advanced", "Spanish II Advanced", "Spanish III Advanced", "Advanced Language or Career Applications", "Seminar in Languages other than English", "Advanced Spanish"]
LEVEL_1 = ["English I", "English II", "English III", "English IV", "Algebra I", "Algebra II", "Algebraic Reasoning", "College Prep Math", "Geometry", "Math Models", "Pre-Calculus", "Statistics", "Astronomy", "Biology", "Chemistry", "Environmental Systems", "Earth & Space Science", "Earth Systems Science", "Integrated Physics and Chemistry", "Physics", "Specialized Topics in Science", "An American Experience", "African American Studies", "Economics", "Mexican American Studies", "New Testament Bible & Amer Civ", "Old Testament Bible & Amer Civ", "Personal Financial Literacy", "Psychology", "Sociology", "U.S. Government", "U.S. History", "World Geography", "World History", "American Sign Language I", "American Sign Language II", "American Sign Language III", "American Sign Language IV", "Chinese I", "Chinese II", "Chinese III", "Chinese IV", "French I", "French II", "Latin I", "Latin II", "Spanish I", "Spanish II", "Spanish III"]
ALL_CLASSES = sorted(list(set(LEVEL_3 + LEVEL_2 + LEVEL_1)))

# --- 2. GOOGLE SHEETS CONNECTION ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Failed to connect to Google Sheets: {str(e)}")
    st.stop()

def get_leaderboard():
    try:
        # worksheet name MUST exactly match your Google Sheet tab name
        return conn.read(worksheet="Sheet1", ttl=0)
    except Exception as e:
        st.warning(f"Could not load leaderboard: {str(e)}")
        return pd.DataFrame(columns=["email", "display_name", "gpa"])

def save_to_leaderboard(email, name, gpa):
    try:
        df = get_leaderboard()
        new_entry = pd.DataFrame([{"email": email, "display_name": name, "gpa": gpa}])
        if not df.empty and email in df['email'].values:
            df.loc[df['email'] == email, ['display_name', 'gpa']] = [name, gpa]
        else:
            df = pd.concat([df, new_entry], ignore_index=True)
        conn.update(worksheet="Sheet1", data=df)
        st.success("Successfully saved to leaderboard!")
    except Exception as e:
        st.error(f"Failed to save to leaderboard: {str(e)}")

# --- 3. APP UI ---
st.set_page_config(page_title="Glenn HS Leaderboard", layout="wide")

if 'step' not in st.session_state: st.session_state.step = 1
if 'num_s1' not in st.session_state: st.session_state.num_s1 = 4
if 'num_s2' not in st.session_state: st.session_state.num_s2 = 4
if 'sync_toggle' not in st.session_state: st.session_state.sync_toggle = False

# Navigation logic
lb = get_leaderboard()
has_joined = 'user_email' in st.session_state and not lb.empty and st.session_state.user_email in lb['email'].values
nav = ["Join", "Leaderboard"] if has_joined else ["Join"]
page = st.sidebar.radio("Navigate", nav)

if page == "Join":
    if st.session_state.step == 1:
        st.title("🏆 Verify Identity")
        e_in = st.text_input("School Email")
        if st.button("Verify"):
            # Logic for validating school email format
            if re.match(r"^([a-z]+)\.([a-z]+)(\d*)@k12\.leanderisd\.org$", e_in.lower().strip()):
                match = re.match(r"^([a-z]+)\.([a-z]+)", e_in.lower().strip())
                st.session_state.real_name = f"{match.group(1).capitalize()} {match.group(2).capitalize()}"
                st.session_state.user_email = e_in
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("Invalid @k12.leanderisd.org email.")

    elif st.session_state.step == 2:
        st.header(f"Welcome, {st.session_state.real_name}")
        
        # GPA Calculation logic would go here
        st.info("Fill out your classes to calculate your GPA.")
        
        # Example Save Button
        if st.button("Submit to Leaderboard"):
            # Placeholder GPA for testing
            save_to_leaderboard(st.session_state.user_email, st.session_state.real_name, 4.0)

elif page == "Leaderboard":
    st.title("🏆 School Leaderboard")
    st.dataframe(lb.sort_values(by="gpa", ascending=False), hide_index=True)
