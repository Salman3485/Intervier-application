# ui.py
import json
import streamlit as st
import db


def show_result(r):
    c1, c2, c3 = st.columns(3)
    c1.metric("Overall Score", f"{r['total_score']}/100")
    c2.metric("Domain", r["field_name"])
    c3.metric("Date", r["result_date"])
    st.progress(r["total_score"] / 100)
    st.success(f"**Strengths:** {r['strengths']}")
    st.warning(f"**Areas to improve:** {r['weaknesses']}")
    st.subheader("Question-wise Breakdown")
    for i, q in enumerate(db.get_questions(r["schedule_id"]), start=1):
        try:
            fb = json.loads(q["feedback"] or "{}")
        except json.JSONDecodeError:
            fb = {}
        with st.expander(f"Q{i}: {q['question_text']}  —  {q['score']}/10"):
            st.markdown(f"**Your answer:** {q['answer_text'] or '_No answer_'}")
            st.markdown(f"**✅ What was good:** {fb.get('strengths', '-')}")
            st.markdown(f"**❌ Where you went wrong:** {fb.get('where_you_went_wrong', '-')}")
            st.markdown(f"**💡 Ideal answer:** {fb.get('ideal_answer', '-')}")
