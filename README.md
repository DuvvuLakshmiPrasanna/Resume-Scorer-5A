# Resume Scorer

A Streamlit app that compares a resume and job description using AI. This version supports both **Groq** and **Gemini** providers, with Groq as the recommended option for deployment.

The app includes a polished UI with a sidebar, two-column input layout, score metrics, a bar-chart breakdown, missing skills, suggestions, and learning resources.

**Author:** Duvvu Lakshmi Prasanna

## Live Demo

🔗 [https://resume-scorer-5a-nrgw9s76um6pfsa6rgquml.streamlit.app/](https://resume-scorer-5a-nrgw9s76um6pfsa6rgquml.streamlit.app/)

## Screenshots

### ATS Score Result

![Resume ATS](ResumeATS.png)

### Resume Review

![Resume Review](Resume_Review.png)

## Setup

1. Create and activate the virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Add your Groq or Gemini API key to `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY="YOUR_GROQ_KEY"
# or
GEMINI_API_KEY="YOUR_GEMINI_KEY"
```

If you supply both keys, the sidebar lets you choose which provider to use.

## Run

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Then open `http://localhost:8501`.

## How it works

- Groq: uses `groq.chat.completions.create(...)` with model `llama-3.3-70b-versatile`
- Gemini: uses the existing Gemini client and `gemini-2.5-flash`
- The app builds a JSON-only prompt and validates the response before rendering the score

## Testing

1. Confirm the app loads with:
   - Resume text box
   - Job description text box
   - Provider selector in the sidebar
   - API key field or secret-loaded provider indicator
   - Score Resume button

2. Use this sample data to verify the flow:

### Resume

```text
John Doe
Skills:
Python
Java
SQL
Problem Solving

Experience:
3+ years building web applications and APIs.
```

### Job Description

```text
Seeking a Software Engineer with Python, SQL, and strong problem-solving skills.
Experience with cloud services and collaborative development is preferred.
```

3. Click **Score Resume** and verify the app returns:
   - Fit score
   - Rationale
   - Missing skills
   - Suggestions
   - Learning resources (if available)

## Common Fixes

- `ModuleNotFoundError: No module named 'streamlit'`
  - Run `pip install streamlit`
- `ModuleNotFoundError: No module named 'groq'`
  - Run `pip install groq`
- `ModuleNotFoundError: No module named 'google'`
  - Run `pip install google-genai`
- `Invalid API Key`
  - Add a valid Groq key to `GROQ_API_KEY` or a valid Gemini key to `GEMINI_API_KEY`

## Files

- `app.py` — Streamlit application
- `requirements.txt` — Python dependencies
- `.streamlit/secrets.toml` — API secret placeholder for Groq and Gemini
- `.streamlit/config.toml` — light-mode theme configuration
- `acceptance_log.md` — lab acceptance log

## Notes

- Wide layout for productivity
- Two-column text input for resume and JD
- Sidebar for API key entry and tips
- Score summary cards and bar chart
- Clear sections for missing skills, suggestions, and learning resources
- For deployment, Streamlit Cloud secrets should use `GROQ_API_KEY` or `GEMINI_API_KEY`.
- Groq is a compatible alternative when Gemini quota or key issues occur.
- The app is scored on whether it runs, compares resume + JD, and returns AI-generated feedback.

## Tech Stack

- **Frontend/App Framework:** Streamlit
- **AI Model:** Groq or Google Gemini
- **Language:** Python

## Future Improvements

- Support for multiple resume formats (PDF, DOCX upload)
- Resume builder suggestions based on JD keywords
- History tracking of previous scoring sessions
- Multi-language resume support

## License

This project is open-source and available for personal and educational use.
