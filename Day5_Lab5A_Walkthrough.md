# Day 5 — Lab 5A: Résumé-Scorer Streamlit (Turnkey Walkthrough)

**Time:** 90 minutes (11:15 — 13:00)
**Format:** Individual at laptop in VS Code; trainer demos paid Cursor in 12 min first
**Goal:** Each mentor builds and deploys a public Streamlit app that scores a résumé against a JD using free Gemini + Continue.dev.

---

## Setup (5 min)

Each mentor has:
- Python 3.10+ installed locally
- VS Code installed
- Their Gemini API key (1Password)
- ai-mentor-portfolio repo cloned locally OR a fresh subfolder for this lab
- `starter_notebooks/Day5_Resume_Scorer_app.py` from the lab kit

---

## Step 1 — Install Continue.dev VS Code extension (10 min)

In VS Code:
- Extensions sidebar → search "Continue"
- Install **Continue - Codestral, Claude, and more**
- Click Continue icon in left sidebar
- First-run config: pick "Continue with Gemini"
- Paste your Gemini API key when prompted
- Test: Cmd+L (Mac) or Ctrl+L (Win) → ask "what is recursion?" → Gemini responds in Continue panel

**Trainer note:** Continue.dev is free + BYOK. The bootcamp standard. Mentors who try to use Cursor instead will pay $20/month — fine for them, but the discipline is free-tier.

**Acceptance:** Continue.dev side panel loads, mentor can chat with Gemini through it.

---

## Step 2 — Project setup (10 min)

In terminal:

```bash
mkdir resume-scorer && cd resume-scorer
python -m venv venv
source venv/bin/activate   # Mac/Linux
# OR: venv\Scripts\activate  # Win
pip install streamlit google-genai pydantic
```

Open the folder in VS Code: `code .`

Create `app.py` and paste from the lab kit's `Day5_Resume_Scorer_app.py`:

```python
import streamlit as st
from google import genai
import os, json

st.set_page_config(page_title='Résumé Scorer', layout='wide')
st.title('Résumé vs JD Fit Scorer')
st.caption('Day 5 Lab 5A — Free tools end-to-end')

col1, col2 = st.columns(2)
with col1:
    resume = st.text_area('Paste résumé', height=400)
with col2:
    jd = st.text_area('Paste job description', height=400)

api_key = st.text_input('Gemini API key', type='password',
                       help='Free key from aistudio.google.com')

if st.button('Score') and resume and jd and api_key:
    with st.spinner('Scoring...'):
        client = genai.Client(api_key=api_key)
        prompt = f"""You are a placement coach. Given this résumé and JD,
return JSON: {{"score": int 0-100, "rationale": str, "missing_skills": [str], "suggestions": [str]}}.

Résumé:
{resume}

JD:
{jd}"""
        resp = client.models.generate_content(
            model='gemini-2.5-flash', contents=prompt,
            config={'response_mime_type': 'application/json'})
        result = json.loads(resp.text)
        st.metric('Fit Score', f"{result['score']}/100")
        st.subheader('Rationale')
        st.write(result['rationale'])
        st.subheader('Missing skills')
        for s in result['missing_skills']:
            st.write(f'- {s}')
        st.subheader('Suggestions')
        for s in result['suggestions']:
            st.write(f'- {s}')
```

In terminal:

```bash
streamlit run app.py
```

Browser opens at `http://localhost:8501` with the running app.

**Acceptance:** App loads, two text areas + Score button visible.

---

## Step 3 — Smoke-test with sample data (10 min)

Use sample data from the lab kit:
- Paste résumé 1 (Ravi Kumar) from `data/sample_resumes.txt`
- Paste JD 1 (TCS Digital) from `data/jds_cached.jsonl`

Click Score. Wait 5-15 seconds. Result: score in the 60-80 range, rationale referencing Java + DSA match, missing_skills mentions Spring Boot or AWS.

**Acceptance:** App returns a coherent score + rationale + missing skills.

---

## Step 4 — Use Continue.dev to add features (30 min)

Now use Continue.dev to extend the app. The discipline: **explain every accepted suggestion in one line.**

### Feature A — Add a "score breakdown" section

In `app.py`, place cursor below `st.metric('Fit Score', ...)`. Open Continue.dev (Cmd+I or Ctrl+I).

Prompt:

> "Add a breakdown chart below the fit score. Use st.bar_chart to show 4 sub-scores: technical_skills_match, soft_skills_match, experience_relevance, project_fit. Modify the Gemini prompt to also return these 4 fields in the JSON. Each is 0-100."

Continue.dev suggests changes. **Read every line.** Accept only if you can explain WHY each line.

### Feature B — Add improvement suggestions

Below the Suggestions section, prompt Continue.dev:

> "Add a 'Top 3 missing skills with learning resources' section. For each missing skill, suggest one free YouTube channel or one free course. Modify the Gemini prompt to return this as `learning_resources: List[Dict[str, str]]` where each dict has `skill`, `resource_type`, `link`."

Same discipline: explain each accepted line.

### Feature C — Acceptance log

Create `acceptance_log.md` in the same folder. For every Continue.dev suggestion you accept, write one line:

```markdown
## Day 5 Lab 5A — Continue.dev acceptance log

1. Accepted: bar_chart visualization of sub-scores
   Why: makes the score breakdown immediately scannable

2. Accepted: prompt modification adding 4 sub-fields
   Why: needed for the bar chart; keeps the prompt-output contract clear

3. Accepted: learning resources structure
   Why: actionable for students — score alone is not useful; next steps are

[continue for each accepted suggestion]
```

**Trainer note:** The acceptance log is the proof of AI-augmented (not AI-replaced) coding. Walk the room and read 2-3 mentors' logs aloud — they'll see what "explained acceptance" looks like.

**Acceptance:** App has 2 new features + acceptance_log.md with 5+ entries.

---

## Step 5 — Push to GitHub + deploy (15 min)

Stop the local Streamlit (Ctrl+C in terminal).

Move keys to secrets:

```bash
mkdir .streamlit
cat > .streamlit/secrets.toml << EOF
GEMINI_API_KEY = "<paste your key>"
EOF

cat > .gitignore << EOF
venv/
.streamlit/secrets.toml
__pycache__/
EOF
```

Modify `app.py` to read from secrets in deployment:

```python
api_key = st.secrets.get('GEMINI_API_KEY', None) or st.text_input('Gemini API key', type='password')
```

(Local: prompts for key. Deployed with secrets: uses st.secrets.)

Commit:

```bash
git add app.py acceptance_log.md .gitignore
git commit -m "Day 5: Streamlit résumé scorer with Continue.dev"
git push
```

Now deploy:
- Go to https://share.streamlit.io
- Sign in with GitHub
- **New app** → select `ai-mentor-portfolio` repo, branch `main`, file `app.py`
- Click **Advanced settings** → **Secrets** → paste:
  ```
  GEMINI_API_KEY = "<your key>"
  ```
- Click **Deploy**

Wait 60-120 seconds for build. Public URL appears: `https://<your-app>.streamlit.app`.

**Acceptance:** Public URL works, smoke-tested with one résumé + JD.

---

## Step 6 — Document deploy in README (5 min)

```markdown
## Day 5 — Résumé Scorer Streamlit

**Live URL:** https://<your-app>.streamlit.app
**Code:** [app.py](app.py)
**Acceptance log:** [acceptance_log.md](acceptance_log.md)
**Tools used:** Continue.dev + Gemini 2.5 Flash + Streamlit Community Cloud

### Features
- Fit score with rationale
- 4-axis bar chart breakdown
- Missing skills + free learning resources

### Reflection (3 lines)
- **Vibe vs engineered:** This is vibe-coded. To productionise, I would add caching, error handling on Gemini failures, rate limiting per user.
- **What Continue.dev did well:** scaffolded the Streamlit layout fast.
- **What I had to fix:** Continue.dev forgot to add the 4 sub-score fields to the Gemini prompt itself; I had to add them.
```

Push.

**Acceptance:** README links to live URL + code + acceptance log + reflection.

---

## Common bugs + recovery

- **Streamlit Cloud deploy fails with "module not found"** → forgot `requirements.txt`. Add one with `streamlit\ngoogle-genai\npydantic`. Push. Streamlit auto-redeploys.
- **Cold-start sleep on free tier (30s warm-up)** → known. Mention it in any demo.
- **API key visible in commit history** → `git log --all --oneline | head` to find the bad commit. `git filter-branch` or `git filter-repo` to remove. Force push. Revoke the key in AI Studio. Regenerate. Use `.streamlit/secrets.toml` from now on. The cleanup IS the lesson.
- **Continue.dev connector fails** → fall back to copy-paste from chat.gemini.com. Less efficient but works.
- **App returns malformed JSON from Gemini** → add a try/except around `json.loads`. If parse fails, show raw response with a "could not parse" warning.

---

## Trainer notes

1. **Walk the room during Step 4 (Continue.dev features).** This is where AI-augmented coding discipline is taught. If you see a mentor accepting suggestions without reading, intervene. Ask "explain this line" — if they can't, reject.
2. **The teaching moment is "explain every accepted line".** Demonstrate publicly: pick one mentor, ask them to walk through 3 random lines they accepted from Continue.dev. If they can — pass. If they can't — that's the lesson.
3. **Cold-start sleep IS the lesson.** Show it live: open the deployed app after lunch break, watch the 30-second wakeup. Mentors will warn audiences before demos forever.
4. **API key leak recovery — make it a public lesson.** Show on the projector: how to find a leaked key in commit history, revoke, regenerate, redeploy with secrets. The cleanup is more useful than the never-leaking.
5. **Stretch goal for fast finishers:** add a PDF upload (use PyMuPDF or pdfplumber) instead of paste-text. ~30 lines of code, more realistic UX.

---

## Acceptance check (final 5 min)

For each mentor:
- ✅ App runs locally without errors
- ✅ App deployed to Streamlit Community Cloud (public URL)
- ✅ Acceptance log has 5+ entries with reasoning
- ✅ Repo includes `.streamlit/secrets.toml` in `.gitignore` (no leaked keys)
- ✅ README links live URL + code + reflection

If a mentor's deploy is failing at 12:55, focus on local-running for the last 5 minutes. Deploy can finish during lunch.
