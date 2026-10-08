# 🎤 PyInterviewer — AI Mock Interview Platform

Streamlit + SQLite + Google Gemini. Candidates practice interviews and get AI scores and feedback; HR schedules interviews and views reports.

## Run locally

1. **Get a free Gemini API key:** go to https://aistudio.google.com, sign in, then **Get API key → Create API key**.
2. **Edit `.streamlit/secrets.toml`:**
   - Paste your key into `GEMINI_API_KEY`.
   - Change `HR_EMAIL` / `HR_PASSWORD` to the HR login you want.
3. **Start the app:**
   ```
   venv\Scripts\activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. **Open http://localhost:8501.**
   - **Candidates:** register on the home page.
   - **HR:** log in with the email and password from `secrets.toml`. There is no HR sign-up.

## Host on Streamlit Community Cloud (free)

1. **Push this folder to a GitHub repo.** `.gitignore` already keeps `secrets.toml`, `interview.db` and `venv/` out.
2. **Create the app:** at https://share.streamlit.io, choose **Create app**, pick the repo and set **Main file** = `app.py`.
3. **Add your secrets:** under **Advanced settings → Secrets**, paste the contents of your local `secrets.toml`.
4. **Deploy.**

> Note: SQLite data (users, results) is wiped whenever the cloud app restarts or sleeps. The HR account is re-created automatically from Secrets.

## Troubleshooting

| Problem | Fix |
|---|---|
| "AI error ... GEMINI_API_KEY is not set" | Put your real key in `.streamlit/secrets.toml` |
| AI error 404 model not found | Change `GEMINI_MODEL` in secrets (check AI Studio for the current free Flash model) |
| AI error 429 / quota | Free-tier rate limit; wait a minute or use fewer questions |
| `database is locked` | Close any SQLite viewer while the app runs |
| "Please log in" after refresh | Normal: refreshing clears the session |
