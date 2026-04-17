import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------
# FILE EXTRACTION
# -------------------------------

def extract_text_from_files(files):
    texts = []
    for f in files:
        try:
            texts.append(f.read().decode("utf-8", errors="ignore"))
        except:
            texts.append("")
    return texts


# -------------------------------
# NESTOR (AI)
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
        return fallback_response()


# -------------------------------
# ALEC (REWRITE)
# -------------------------------

def tailor_cv(texts, job_text, evaluation):

    cv_text = "\n".join(texts)

    prompt = f"""
Rewrite CV for job.

Do NOT invent experience.

CV:
{cv_text}

JOB:
{job_text}
"""

    try:
        r = client.chat.completions.create(
            model="gpt-5.3",
            messages=[{"role":"user","content":prompt}],
            temperature=0.4
        )
        return r.choices[0].message.content
    except:
        return cv_text


# -------------------------------
# SIMULATION
# -------------------------------

def simulate_improvement(texts, job_text, evaluation):

    prompt = f"""
Simulate improved CV outcome.

Current evaluation:
{json.dumps(evaluation)}

Return JSON:
{{
 "new_score": number,
 "new_decision": "...",
 "improvements_applied": [],
 "reasoning": "..."
}}
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
            "new_score": min(10, evaluation.get("fit_score",5)+1),
            "new_decision":"Improved",
            "improvements_applied":["General improvements"],
            "reasoning":"Fallback"
        }


# -------------------------------
# 🔥 NEW: REGENERATE FROM SIMULATION
# -------------------------------

def regenerate_from_simulation(texts, job_text, improvements):

    cv_text = "\n".join(texts)

    prompt = f"""
Rewrite CV applying these improvements:

{improvements}

Rules:
- no hallucination
- apply improvements clearly

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


# -------------------------------
# FALLBACK
# -------------------------------

def fallback_response():
    return {
        "decision":"Potential Match",
        "fit_score":5,
        "heatmap":{"skills":50,"experience":50,"tools":50,"domain":50,"seniority":50},
        "domain_analysis":"Unknown",
        "strengths":[],
        "gaps":[],
        "risk_flags":[],
        "cv_diff":[]
    }