import os
import json
from openai import OpenAI
import docx
import pdfplumber

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -----------------------------
# FILE EXTRACTION
# -----------------------------
def extract_text_from_files(files):
    texts = []

    for file in files:
        filename = file.filename.lower()

        try:
            if filename.endswith(".docx"):
                doc = docx.Document(file)
                text = "\n".join([p.text for p in doc.paragraphs])

            elif filename.endswith(".pdf"):
                with pdfplumber.open(file) as pdf:
                    pages = [page.extract_text() or "" for page in pdf.pages]
                    text = "\n".join(pages)

            else:
                text = "Unsupported file format"

        except Exception as e:
            text = f"Error reading file: {str(e)}"

        texts.append(text)

    return texts


# -----------------------------
# NESTOR (FIXED — FACT EXTRACTION FIRST)
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
- financial scope (budgets, P&L)

STEP 2 — Evaluate match against job using ONLY those facts.

STRICT RULES:
- DO NOT ignore information that IS present
- DO NOT say something is missing if it appears in the CV
- DO NOT assume or infer
- DO NOT hallucinate

RETURN STRICT JSON:

{{
  "fit_score": number,
  "decision": "APPLY" | "STRETCH" | "HIGH_RISK",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "strengths": [],
  "gaps": [],
  "risk_flags": []
}}

RULES:
- max 4 per list
- short phrases only
- grounded in CV

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
# ALEC (SAFE — NO FABRICATION)
# -----------------------------
def tailor_cv(texts, job_text, evaluation):

    cv_text = "\n".join(texts)

    prompt = f"""
You are a senior CV strategist.

Rewrite the CV to improve alignment with the job.

STRICT RULES:
- DO NOT invent experience, education, skills, or languages
- DO NOT change job titles or create new roles
- DO NOT downgrade seniority
- DO NOT fabricate industry experience

ALLOWED:
- Rephrase
- Reorder
- Emphasize relevant transferable experience

USE THIS INPUT:

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