# pages/2_Results.py
import streamlit as st
import db
from ui import show_result

user = st.session_state.get("user")
if not user or user["role"] != "Candidate":
    st.warning("Please log in as a Candidate on the home page.")
    st.stop()

st.title("📊 My Results")
results = db.get_results(user["id"])
if not results:
    st.info("No interviews yet. Go to the Interview page to start one!")
    st.stop()

# Score trend chart across all past interviews (oldest → newest)
if len(results) > 1:
    st.subheader("Score trend")
    st.line_chart({"Score": [r["total_score"] for r in reversed(results)]})

labels = {f"#{r['result_id']} — {r['field_name']} — {r['result_date']} — {r['total_score']}/100": r
          for r in results}
keys = list(labels)
default = 0
if "last_schedule" in st.session_state:   # open the interview just finished
    for i, r in enumerate(results):
        if r["schedule_id"] == st.session_state.last_schedule:
            default = i
    st.toast("Interview evaluated! Here is your result.")
    del st.session_state["last_schedule"]

choice = st.selectbox("Past interviews", keys, index=default)
show_result(labels[choice])
