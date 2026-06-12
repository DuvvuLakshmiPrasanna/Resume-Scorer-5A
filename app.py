import json
import os
import re
from typing import List

import pandas as pd
import streamlit as st
from pydantic import BaseModel, HttpUrl, ValidationError, validator


class LearningResource(BaseModel):
    skill: str
    resource_type: str
    link: HttpUrl


class ResumeScore(BaseModel):
    score: int
    rationale: str
    missing_skills: List[str]
    suggestions: List[str]
    technical_skills_match: float
    soft_skills_match: float
    experience_relevance: float
    project_fit: float
    learning_resources: List[LearningResource]

    @validator("score")
    def clamp_score(cls, value):
        return max(0, min(100, value))

    @validator("technical_skills_match", "soft_skills_match", "experience_relevance", "project_fit")
    def clamp_percent(cls, value):
        return max(0.0, min(100.0, value))


def create_gemini_client(api_key: str):
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        return genai
    except ImportError:
        pass

    try:
        import google.genai as genai

        return genai.Client(api_key=api_key)
    except ImportError as exc:
        raise RuntimeError(
            "Unable to import Gemini client. Install google-genai or google-generativeai."
        ) from exc


def create_groq_client(api_key: str):
    try:
        from groq import Groq
    except ImportError as exc:
        raise RuntimeError(
            "Unable to import Groq client. Install the groq package."
        ) from exc

    return Groq(api_key=api_key)


def parse_text_response(response):
    if hasattr(response, "choices"):
        try:
            first_choice = response.choices[0]
            if hasattr(first_choice, "message") and hasattr(first_choice.message, "content"):
                return first_choice.message.content
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict) and "content" in message:
                    return message["content"]
            if hasattr(first_choice, "text"):
                return first_choice.text
        except (IndexError, AttributeError):
            pass

    if hasattr(response, "text"):
        return response.text
    if hasattr(response, "response") and hasattr(response.response, "text"):
        return response.response.text
    if isinstance(response, dict) and "text" in response:
        return response["text"]
    return str(response)


def extract_json_text(raw_text: str) -> str:
    text = raw_text.strip()

    # Remove markdown fences and surrounding explanation text.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text).strip()

    if text.startswith("{") or text.startswith("["):
        return text

    start_candidates = [idx for idx in (text.find("{"), text.find("[")) if idx != -1]
    if start_candidates:
        start = min(start_candidates)
        end_char = "}" if text[start] == "{" else "]"
        end = text.rfind(end_char)
        if end != -1 and end > start:
            return text[start : end + 1]

    return text


def build_prompt(resume_text: str, job_description: str) -> str:
    return (
        "You are a resume scoring assistant. Compare the candidate resume against the job description. "
        "Return only valid JSON with the following fields:\n"
        "score: integer 0-100\n"
        "rationale: string explanation of the match\n"
        "missing_skills: list of important skills missing from the resume\n"
        "suggestions: list of actionable recommendations to improve alignment\n"
        "technical_skills_match: number 0-100\n"
        "soft_skills_match: number 0-100\n"
        "experience_relevance: number 0-100\n"
        "project_fit: number 0-100\n"
        "learning_resources: list of objects with skill, resource_type, link\n"
        "Return only the JSON object. Do not include any markdown fences, labels, or extra text.\n"
        "Use concise language and valid JSON arrays/objects."
        "\nResume:\n" + resume_text + "\n\nJob Description:\n" + job_description
    )


def inject_styles():
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        .stApp {
            background: linear-gradient(180deg, #eef5ff 0%, #f8fbff 100%);
        }
        .section-card {
            border: 1px solid #d7e4fb;
            border-radius: 18px;
            background: #ffffff;
            padding: 1.8rem;
            box-shadow: 0 16px 40px rgba(31, 119, 180, 0.08);
            margin-bottom: 1.5rem;
        }
        .metric-card .stMetric {
            border-radius: 18px;
            padding: 1rem 1.25rem;
            background: #f4f8ff;
        }
        .stTextArea>div>div>textarea,
        .stTextInput>div>div>input {
            border: 1px solid #d7e4fb;
            border-radius: 14px;
            background: #fbfdff;
        }
        .stButton>button {
            border-radius: 12px;
            padding: 0.8rem 1.2rem;
            background-color: #1f77b4;
            color: #ffffff;
            border: 1px solid #175d9d;
        }
        .stButton>button:hover {
            background-color: #175d9d;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1f6cc8 0%, #2d8af0 100%);
        }
        [data-testid="stSidebar"] .css-1inwz65.egzxvld1 {
            color: #ffffff;
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #0f172a;
        }
        .fat-text {
            color: #1f77b4;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def score_resume(resume_text: str, job_description: str, api_key: str, provider: str) -> ResumeScore:
    prompt = build_prompt(resume_text, job_description)

    if provider == "Groq":
        client = create_groq_client(api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
    else:
        client = create_gemini_client(api_key)
        if hasattr(client, "generate_text"):
            response = client.generate_text(
                model="gemini-2.5-flash",
                prompt=prompt,
                temperature=0,
            )
        else:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )

    raw_text = parse_text_response(response)
    cleaned_text = extract_json_text(raw_text)
    try:
        parsed = json.loads(cleaned_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "The model did not return valid JSON. Cleaned response was:\n"
            + cleaned_text
            + "\n\nOriginal response was:\n"
            + raw_text
        ) from exc

    return ResumeScore(**parsed)


def render_score_card(score: ResumeScore):
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Resume score results")
    st.divider()

    score_columns = st.columns(4)
    score_columns[0].metric("Overall", f"{score.score}/100")
    score_columns[1].metric("Technical", f"{score.technical_skills_match:.0f}%")
    score_columns[2].metric("Soft Skills", f"{score.soft_skills_match:.0f}%")
    score_columns[3].metric("Experience", f"{score.experience_relevance:.0f}%")

    st.markdown("#### Match breakdown")
    categories = {
        "Technical Skills": score.technical_skills_match,
        "Soft Skills": score.soft_skills_match,
        "Experience Relevance": score.experience_relevance,
        "Project Fit": score.project_fit,
    }
    chart_data = pd.DataFrame(
        {
            "category": list(categories.keys()),
            "match": list(categories.values()),
        }
    ).set_index("category")
    st.bar_chart(chart_data)

    st.markdown("#### Rationale")
    st.write(score.rationale)

    left, right = st.columns(2)
    with left:
        st.subheader("Missing Skills")
        if score.missing_skills:
            for skill in score.missing_skills:
                st.write(f"- {skill}")
        else:
            st.success("No major missing skills detected.")

    with right:
        st.subheader("Suggestions")
        if score.suggestions:
            for suggestion in score.suggestions:
                st.write(f"- {suggestion}")
        else:
            st.write("No suggestions available.")

    if score.learning_resources:
        st.subheader("Learning Resources")
        for resource in score.learning_resources:
            st.markdown(
                f"- **{resource.skill}** ({resource.resource_type}) — [{resource.link}]({resource.link})"
            )
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="Résumé Scorer",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    st.markdown("# Résumé Scorer")
    st.markdown(
        "Use Groq or Gemini to compare a résumé to a job description and generate a professional fit score with actionable feedback."
    )
    st.markdown(
        '<div class="section-card"><p><strong class="fat-text">Groq or Gemini AI</strong> powers the scoring engine, delivering actionable resume feedback that is clear, modern, and easy to act on.</p></div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Settings")
        groq_key = st.secrets.get("GROQ_API_KEY")
        gemini_key = st.secrets.get("GEMINI_API_KEY")

        provider_options = []
        if groq_key:
            provider_options.append("Groq")
        if gemini_key:
            provider_options.append("Gemini")
        if not provider_options:
            provider_options = ["Groq", "Gemini"]

        provider = st.selectbox("AI provider", provider_options)
        api_key = groq_key if provider == "Groq" else gemini_key

        if api_key is None:
            api_key = st.text_input(
                f"{provider} API Key",
                type="password",
                help=(
                    "Add your API key for the selected provider. "
                    "Use Streamlit Secrets for deployment, or paste a key here during development."
                ),
            )

        if provider == "Groq" and groq_key:
            st.info("Using GROQ_API_KEY from Streamlit secrets.")
        elif provider == "Gemini" and gemini_key:
            st.info("Using GEMINI_API_KEY from Streamlit secrets.")
        elif not api_key:
            st.warning(f"Enter a valid {provider} API key to score the résumé.")

        st.markdown("---")
        st.markdown(
            "### Tips\n- Paste a full resume and job description.\n- Use clear skill and experience detail.\n- If you deploy, store the key in `.streamlit/secrets.toml`."
        )

        st.markdown("---")
        st.markdown(
            "#### Sample data\nUse the sample resume and JD below to verify the app. Replace them with your own text for final scoring."
        )

    left, right = st.columns([2, 2])
    resume_text = left.text_area(
        "Resume text",
        height=280,
        placeholder="Paste the candidate resume here...",
        value="John Doe\n\nSkills:\nPython\nJava\nSQL\nProblem Solving\n\nExperience:\n3+ years building web applications and APIs.",
    )
    job_description = right.text_area(
        "Job description",
        height=280,
        placeholder="Paste the job description here...",
        value="Seeking a Software Engineer with Python, SQL, and strong problem-solving skills.\nExperience with cloud services and collaborative development is preferred.",
    )

    button_col, _ = st.columns([1, 3])
    with button_col:
        score_clicked = st.button("Score Resume")

    if score_clicked:
        if not resume_text.strip() or not job_description.strip():
            st.error("Both resume and job description are required.")
        elif not api_key:
            st.error(f"{provider} API key is required to score the resume.")
        else:
            with st.spinner("Scoring resume..."):
                try:
                    score = score_resume(resume_text, job_description, api_key, provider)
                    render_score_card(score)
                except ValidationError as exc:
                    st.error("Response validation failed: " + str(exc))
                except Exception as exc:
                    message = str(exc)
                    if "API key not valid" in message or "API_KEY_INVALID" in message or "invalid api key" in message.lower():
                        st.error(
                            f"Invalid {provider} API key. Replace the key in the sidebar with a valid key."
                        )
                    else:
                        st.error(message)


if __name__ == "__main__":
    main()
