import os
import json
from openai import OpenAI
import docx
import pdfplumber

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------
# FILE EXTRACTION (UPDATED)
# -----------------------------
def extract_text_from_files(files):
    texts = []

    for file in files:
        filename = file.filename.lower()

        try:
            # DOCX
            if filename.endswith(".docx"):
                doc = docx.Document(file)
                text = "\n".join([p.text for p in doc.paragraphs])

            # PDF
            elif filename.endswith(".pdf"):
                with pdfplumber.open(file) as pdf:
                    pages = [page.extract_text() or "" for page in pdf.pages]
                    text = "\n".join(pages)

            # TXT (NEW)
            elif filename.endswith(".txt"):
                text = file.read().decode("utf-8", errors="ignore")

            else:
                text = "Unsupported file format"

        except Exception as e:
            text = f"Error reading file: {str(e)}"

        texts.append(text)

    return texts


# -----------------------------
# NESTOR
# -----------------------------
def evaluate_fit(texts, job_text):

    cv_text = "\n".join(texts)

    prompt = f"""
You are a senior recruiter.

STEP 1 — Extract ONLY explicit facts from the CV:
- roles
- industries
- skills
- languages
- responsibilities
- financial scope

STEP 2 — Evaluate match vs job using ONLY those facts.

STRICT RULES:
- NO hallucination
- NO ignoring existing info

RETURN JSON:

{{
  "fit_score": number,
  "decision": "APPLY" | "STRETCH" | "HIGH_RISK",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "strengths": [],
  "gaps": [],
  "risk_flags": []
}}

CV:
{cv_text}

JOB:
{job_text}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        return {
            "fit_score": 50,
            "decision": "STRETCH",
            "confidence": "LOW",
            "strengths": [],
            "gaps": [f"LLM error: {str(e)}"],
            "risk_flags": []
        }


# -----------------------------
# ALEC
# -----------------------------
def tailor_cv(texts, job_text, evaluation):

    cv_text = "\n".join(texts)

    prompt = f"""
You are a senior CV strategist.

Rewrite CV to better align with job.

STRICT:
- NO fake experience
- NO role invention
- NO changing titles

ALLOWED:
- rephrase
- reorder
- emphasize

INPUT:

STRENGTHS:
{evaluation.get("strengths", [])}

GAPS:
{evaluation.get("gaps", [])}

RISKS:
{evaluation.get("risk_flags", [])}

JOB:
{job_text}

CV:
{cv_text}

OUTPUT:
Return FULL CV only.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return response.choices[0].message.content

    except:
        return cv_text