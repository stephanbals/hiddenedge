import os
import json
from openai import OpenAI
from docx import Document
import PyPDF2

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------
# FILE EXTRACTION (FIXED)
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

        except:
            texts.append("")

    return texts


# -------------------------------
# NESTOR
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
            model="gpt-5.3",
            messages=[{"role":"user","content":prompt}],
            temperature=0.3
        )
        return json.loads(r.choices[0].message.content)

    except:
        return {
            "decision":"Potential Match",
            "fit_score":5,
            "heatmap":{"skills":50,"experience":50,"tools":50,"domain":50,"seniority":50},
            "domain_analysis":"Fallback",
            "strengths":["Basic alignment"],
            "gaps":["Missing specific requirements"],
            "risk_flags":["Low confidence"],
            "cv_diff":[]
        }


# -------------------------------
# ALEC
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

    r = client.chat.completions.create(
        model="gpt-5.3",
        messages=[{"role":"user","content":prompt}],
        temperature=0.4
    )

    return r.choices[0].message.content