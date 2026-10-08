# ai_engine.py
import json
import streamlit as st
from google import genai

# Change GEMINI_MODEL in secrets.toml if Google renames/retires this model (error 404).
MODEL = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")


@st.cache_resource
def _client():
    key = st.secrets.get("GEMINI_API_KEY", "")
    if not key or key == "paste-your-key-here":
        raise RuntimeError("GEMINI_API_KEY is not set in .streamlit/secrets.toml")
    return genai.Client(api_key=key)


def _ask_json(prompt):
    """Send a prompt, clean the reply, and convert it from JSON to Python."""
    response = _client().models.generate_content(
        model=MODEL, contents=prompt,
        config={"response_mime_type": "application/json"},   # ask Gemini for pure JSON
    )
    text = (response.text or "").replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: keep only the part between the first and last bracket
        start = min((i for i in (text.find("["), text.find("{")) if i != -1), default=-1)
        end = max(text.rfind("]"), text.rfind("}"))
        if start == -1 or end <= start:
            raise
        return json.loads(text[start:end + 1])


def generate_questions(field, difficulty="Medium", n=5, resume_text=""):
    resume_part = ""
    if resume_text:
        resume_part = (f"\nThe candidate's resume is below. Make at least 2 questions "
                       f"about their projects or skills.\nRESUME:\n{resume_text[:3000]}")
    prompt = f"""You are an experienced interviewer.
Generate {n} interview questions for a {field} role at {difficulty} difficulty.
Mix conceptual and practical questions. Keep each question to 1-2 sentences.{resume_part}
Return ONLY a JSON list of strings, no other text. Example: ["Question 1", "Question 2"]"""
    try:
        questions = [str(q).strip() for q in _ask_json(prompt) if str(q).strip()][:n]
        if not questions:
            raise ValueError("AI returned no questions")
        return questions
    except Exception as e:
        # Saved in session_state so the Interview page can still show it after st.rerun()
        st.session_state.ai_warning = (f"AI error while generating questions: {e}. "
                                       "Using standard questions instead.")
        return [f"Tell me about yourself and your interest in {field}.",
                f"What are the most important skills for a {field} role?",
                "Describe a project you are proud of.",
                "What is your biggest weakness and how are you improving it?",
                "Where do you see yourself in 3 years?"][:n]


def evaluate_answer(question, answer):
    if not answer or not answer.strip():
        return {"score": 0, "strengths": "No answer given.",
                "where_you_went_wrong": "The question was left unanswered.",
                "ideal_answer": "Attempt every question, even partially."}
    prompt = f"""You are a fair but strict interviewer. Evaluate the candidate's answer.
Judge only on correctness, completeness, and clarity. Ignore grammar mistakes.
Question: {question}
Candidate's answer: {answer}
Return ONLY this JSON, no other text:
{{"score": <integer 0 to 10>,
  "strengths": "<what was good, 1-2 sentences>",
  "where_you_went_wrong": "<mistakes or missing points, 1-3 sentences>",
  "ideal_answer": "<a short model answer, 2-4 sentences>"}}"""
    try:
        result = _ask_json(prompt)
        return {"score": max(0, min(10, int(result["score"]))),
                "strengths": str(result.get("strengths", "-")),
                "where_you_went_wrong": str(result.get("where_you_went_wrong", "-")),
                "ideal_answer": str(result.get("ideal_answer", "-"))}
    except Exception as e:
        return {"score": 0, "strengths": "-",
                "where_you_went_wrong": f"Could not evaluate automatically ({e}).",
                "ideal_answer": "-"}


def overall_feedback(qa_list):
    """qa_list = list of (question, answer, evaluation_dict)"""
    summary = "\n".join(
        f"Q: {q}\nA: {a}\nScore: {e['score']}/10\n" for q, a, e in qa_list)
    prompt = f"""Here is a candidate's full mock interview with scores:
{summary}
Return ONLY this JSON:
{{"strengths": "<overall strengths, 2-3 sentences>",
  "weaknesses": "<overall weaknesses and what to study next, 2-3 sentences>"}}"""
    try:
        result = _ask_json(prompt)
        return {"strengths": str(result["strengths"]), "weaknesses": str(result["weaknesses"])}
    except Exception:
        return {"strengths": "See per-question feedback.",
                "weaknesses": "See per-question feedback."}
