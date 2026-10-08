# pages/4_HR_Dashboard.py
from datetime import date
import streamlit as st
import db
from ui import show_result

user = st.session_state.get("user")
if not user or user["role"] != "HR":
    st.warning("Please log in as HR on the home page.")
    st.stop()

st.title("🏢 HR Dashboard")
tab1, tab2, tab3 = st.tabs(["Candidates", "Schedule Interview", "Reports"])

with tab1:
    candidates = db.get_all_candidates()
    st.metric("Total candidates", len(candidates))
    st.dataframe([dict(c) for c in candidates], hide_index=True)

with tab2:
    candidates = db.get_all_candidates()
    if not candidates:
        st.info("No candidates registered yet.")
    else:
        cand_opts = {f"{c['name']} ({c['email']})": c["candidate_id"] for c in candidates}
        field_opts = {f"{f['category']} → {f['field_name']}": f["field_id"] for f in db.get_fields()}
        cand = st.selectbox("Candidate", list(cand_opts))
        field = st.selectbox("Interview field", list(field_opts))
        when = st.date_input("Date", min_value=date.today())
        if st.button("Schedule", type="primary"):
            db.create_schedule(cand_opts[cand], user["id"], field_opts[field], str(when))
            st.success("Interview scheduled! The candidate will see it on their Interview page.")
    st.subheader("All scheduled interviews")
    st.dataframe([dict(s) for s in db.get_all_schedules()], hide_index=True)

with tab3:
    results = db.get_all_results()
    if not results:
        st.info("No results yet.")
    else:
        st.metric("Average score", f"{sum(r['total_score'] for r in results) / len(results):.1f}/100")
        st.dataframe([{"Candidate": r["candidate"], "Field": r["field_name"],
                       "Score": r["total_score"], "Date": r["result_date"]} for r in results],
                     hide_index=True)
        labels = {f"#{r['result_id']} — {r['candidate']} — {r['field_name']} — {r['result_date']}": r
                  for r in results}
        pick = st.selectbox("View detailed report", list(labels))
        show_result(labels[pick])
