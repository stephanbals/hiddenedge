import os
import json
from openai import OpenAI
from docx import Document
import PyPDF2

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------
# FILE EXTRACTION
# -------------------------------

def extract_text_from_files(files):

    texts = []

    for f in files:
        filename = f.filename.lower()

        try:
            if filename.endswith(".pdf"):
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                texts.append(text)

            elif filename.endswith(".docx"):
                doc = Document(f)
                text = "\n".join([p.text for p in doc.paragraphs])
                texts.append(text)

            else:
                texts.append(f.read().decode("utf-8", errors="ignore"))

        except Exception as e:
            print("FILE ERROR:", str(e))
            texts.append("")

    return texts


# -------------------------------
# NESTOR (ANALYSIS)
# -------------------------------

def evaluate_fit(texts, job_text):

    cv_text = "\n".join(texts)

    prompt = f"""
Analyze CV vs job.

Return JSON:
{{
 "decision": "...",
 "fit_score": number,
 "heatmap": {{"skills":0-100,"experience":0-100,"tools":0-100,"domain":0-100,"seniority":0-100}},
 "domain_analysis": "...",
 "strengths": [],
 "gaps": [],
 "risk_flags": [],
 "cv_diff": []
}}

CV:
{cv_text}

JOB:
{job_text}
"""

    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return json.loads(r.choices[0].message.content)

    except Exception as e:
        print("EVALUATE ERROR:", str(e))

        return {
            "decision": "Error",
            "fit_score": 0,
            "heatmap": {"skills": 0, "experience": 0, "tools": 0, "domain": 0, "seniority": 0},
            "domain_analysis": "Failed to analyze",
            "strengths": [],
            "gaps": ["Analysis failed"],
            "risk_flags": ["Backend error"],
            "cv_diff": []
        }


# -------------------------------
# ALEC (CV REWRITE)
# -------------------------------

def tailor_cv(texts, job_text, evaluation):

    cv_text = "\n".join(texts)

    prompt = f"""
Rewrite CV for job.

Rules:
- No hallucination
- Improve clarity and alignment

CV:
{cv_text}

JOB:
{job_text}
"""

    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )

        return r.choices[0].message.content

    except Exception as e:
        print("TAILOR ERROR:", str(e))
        return "CV generation failed"


# -------------------------------
# OPTIONAL SAFE FALLBACKS
# -------------------------------

def simulate_improvement(*args, **kwargs):
    return {"improvements_applied": []}


def regenerate_from_simulation(texts, job, improvements):
    return "\n".join(texts)