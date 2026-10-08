# pages/1_Interview.py
import json
import streamlit as st
import db
import ai_engine as ai

user = st.session_state.get("user")
if not user or user["role"] != "Candidate":
    st.warning("Please log in as a Candidate on the home page.")
    st.stop()

st.title("📝 Attend Interview")

INTERVIEW_KEYS = ["questions", "answers", "idx", "schedule_id", "field_id", "ai_warning"]

# ---------- STEP 1: Setup (shown only before the interview starts) ----------
if "questions" not in st.session_state:
    fields = db.get_fields()
    field_options = {f"{f['category']} → {f['field_name']}": f for f in fields}
    pending = db.get_pending_schedules(user["id"])
    mode = "Practice"
    if pending:
        st.info(f"You have {len(pending)} interview(s) scheduled by HR.")
        mode = st.radio("Interview type", ["Practice", "Scheduled by HR"], horizontal=True)
    if mode == "Practice":
        label = st.selectbox("Choose a domain", list(field_options))
        field = field_options[label]
        field_id, field_name, schedule_id = field["field_id"], field["field_name"], None
    else:
        sched_options = {f"{s['field_name']} (on {s['scheduled_date']})": s for s in pending}
        s = sched_options[st.selectbox("Choose your scheduled interview", list(sched_options))]
        field_id, field_name, schedule_id = s["field_id"], s["field_name"], s["schedule_id"]
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Medium")
    num_q = st.slider("Number of questions", 3, 10, 5)
    has_resume = bool(db.get_resume(user["id"]))
    use_resume = st.checkbox("Ask questions from my resume", value=has_resume,
                             disabled=not has_resume,
                             help=None if has_resume else "Upload a resume on the Profile page first.")
    if st.button("🚀 Start Interview", type="primary"):
        st.session_state.pop("ai_warning", None)
        resume = db.get_resume(user["id"]) if use_resume else ""
        with st.spinner("AI is preparing your questions..."):
            questions = ai.generate_questions(field_name, difficulty, num_q, resume or "")
        st.session_state.questions = questions
        st.session_state.answers = []
        st.session_state.idx = 0
        st.session_state.schedule_id = schedule_id   # None = practice (created when saving)
        st.session_state.field_id = field_id
        st.rerun()
    st.stop()

# ---------- STEP 2: Ask questions one at a time ----------
questions = st.session_state.questions
idx = st.session_state.idx

if idx < len(questions):
    if "ai_warning" in st.session_state:
        st.warning(st.session_state.ai_warning)
    st.progress(idx / len(questions), text=f"Question {idx + 1} of {len(questions)}")
    st.subheader(questions[idx])
    answer = st.text_area("Your answer", key=f"answer_{idx}", height=200)
    last = idx == len(questions) - 1
    col1, col2 = st.columns([1, 5])
    if col1.button("Submit Interview ✅" if last else "Next ➜", type="primary"):
        st.session_state.answers.append(answer)
        st.session_state.idx += 1
        st.rerun()
    if col2.button("✖ Quit interview"):
        for key in INTERVIEW_KEYS:
            st.session_state.pop(key, None)
        st.rerun()

# ---------- STEP 3: Evaluate and save ----------
else:
    answers = st.session_state.answers
    evaluations = []
    with st.spinner("AI is evaluating your answers... (takes ~20 seconds)"):
        for q, a in zip(questions, answers):
            evaluations.append(ai.evaluate_answer(q, a))
        total = round(sum(e["score"] for e in evaluations) / len(evaluations) * 10)
        summary = ai.overall_feedback(list(zip(questions, answers, evaluations)))
        # Everything is saved together only after all AI calls finished
        sid = db.save_interview(
            user["id"], st.session_state.schedule_id, st.session_state.field_id,
            [(q, a, e["score"], json.dumps(e)) for q, a, e in zip(questions, answers, evaluations)],
            total, summary["strengths"], summary["weaknesses"],
        )
    for key in INTERVIEW_KEYS:
        st.session_state.pop(key, None)
    st.session_state.last_schedule = sid
    st.switch_page("pages/2_Results.py")
