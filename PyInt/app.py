# app.py
import streamlit as st
import db

st.set_page_config(page_title="PyInterviewer", page_icon="🎤", layout="wide")
db.init_db()

# The single HR account comes from secrets.toml (there is no HR sign-up)
if all(k in st.secrets for k in ("HR_NAME", "HR_EMAIL", "HR_PASSWORD")):
    db.ensure_admin_hr(st.secrets["HR_NAME"], st.secrets["HR_EMAIL"], st.secrets["HR_PASSWORD"])

st.title("🎤 PyInterviewer — AI Mock Interview Platform")

# Already logged in
if "user" in st.session_state:
    user = st.session_state.user
    st.success(f"Logged in as **{user['name']}** ({user['role']})")
    if user["role"] == "Candidate":
        st.info("Use the sidebar: **Interview** to practice, **Results** to see scores, "
                "**Profile** to upload your resume.")
    else:
        st.info("Use the sidebar: **HR Dashboard** to manage candidates and reports.")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
    st.stop()

role = st.radio("I am a:", ["Candidate", "HR"], horizontal=True)

if role == "HR":
    login_tab, = st.tabs(["Login"])
else:
    login_tab, register_tab = st.tabs(["Login", "Register"])

with login_tab:
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pw")
    if st.button("Login"):
        user = db.login(role, email, password)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Incorrect email or password.")

if role == "Candidate":
    with register_tab:
        name = st.text_input("Full name")
        r_email = st.text_input("Email", key="reg_email")
        r_pw = st.text_input("Password", type="password", key="reg_pw")
        if st.button("Register"):
            if not (name.strip() and r_email.strip() and r_pw):
                st.error("Please fill all fields.")
            elif "@" not in r_email:
                st.error("Please enter a valid email.")
            elif db.register(name, r_email, r_pw):
                st.success("Registered! Now log in from the Login tab.")
            else:
                st.error("This email is already registered.")
