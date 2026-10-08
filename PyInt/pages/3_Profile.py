# pages/3_Profile.py
import streamlit as st
from pypdf import PdfReader
import db

user = st.session_state.get("user")
if not user or user["role"] != "Candidate":
    st.warning("Please log in as a Candidate on the home page.")
    st.stop()

st.title("👤 My Profile")
st.write(f"**Name:** {user['name']}")
current = db.get_resume(user["id"])
st.write("**Resume uploaded:**", "✅ Yes" if current else "❌ No")

pdf = st.file_uploader("Upload your resume (PDF)", type="pdf")
if pdf and st.button("Save Resume"):
    try:
        text = "\n".join(page.extract_text() or "" for page in PdfReader(pdf).pages)
    except Exception as e:
        text = ""
        st.error(f"Could not open this PDF ({e}).")
    if text.strip():
        db.save_resume(user["id"], text)
        st.success("Resume saved! Interview questions will now include your projects and skills.")
        current = text
    else:
        st.error("Could not read text from this PDF (it may be a scanned image).")

if current:
    with st.expander("View extracted resume text"):
        st.text(current[:3000])
