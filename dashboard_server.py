import os
import io
import json
import logging
from flask import Flask, request, jsonify, render_template
from docx import Document
import PyPDF2
from openai import OpenAI

app = Flask(__name__, template_folder="templates", static_folder="static")
logging.basicConfig(level=logging.INFO)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ---------------- FILE PARSING ----------------

def extract_text_from_pdf(file_bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def extract_text_from_docx(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def extract_text(filename, file_bytes):
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    if filename.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    return file_bytes.decode("utf-8", errors="ignore")

# ---------------- SAFE JSON ----------------

def safe_json_parse(text):
    try:
        return json.loads(text)
    except:
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None

# ---------------- RECOMMENDATION ----------------

def compute_recommendation(score, signal):
    if score >= 75 and signal == "High":
        return {"decision": "Apply", "reason": "Your profile strongly matches the role and you are likely to progress."}
    if score < 50 or signal == "Low":
        return {"decision": "Do Not Apply", "reason": "There is a fundamental mismatch with the core requirements of this role."}
    return {"decision": "Consider", "reason": "There is partial alignment, but you may face stronger competing candidates."}

# ---------------- ANALYSIS (NESTOR) ----------------

def analyze_with_ai(cv_text, job_text):
    if not client:
        base = {
            "score": 50, "decision": "Moderate Match", "hiring_signal": "Medium",
            "context": {}, "recruiter_view": {}, "hiring_manager_view": {},
            "improvement_plan": {}, "better_fit_roles": [], "final_advice": "Set OpenAI API key"
        }
        base["apply_recommendation"] = compute_recommendation(50, "Medium")
        return base

    prompt = f"""
You are an intelligent career advisor.

Return STRICT JSON:

{{
  "context": {{"role_type": "", "seniority": "", "domain": "", "environment": ""}},
  "score": number,
  "decision": "",
  "hiring_signal": "",
  "recruiter_view": {{"screening_decision": "", "risk_level": "", "observations": [], "concerns": [], "verdict": ""}},
  "hiring_manager_view": {{"confidence_level": "", "strengths": [], "concerns": [], "verdict": ""}},
  "improvement_plan": {{"priority_actions": [], "quick_wins": [], "strategic_changes": []}},
  "better_fit_roles": [],
  "final_advice": ""
}}

RULES:
- Address the candidate directly where appropriate
- Be specific and realistic

CV:
{cv_text}

JOB:
{job_text}
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        parsed = safe_json_parse(res.choices[0].message.content)
        if not parsed:
            raise Exception("Parse failed")
        parsed["apply_recommendation"] = compute_recommendation(parsed.get("score", 50), parsed.get("hiring_signal", "Medium"))
        return parsed
    except Exception:
        logging.exception("AI ERROR")
        base = {
            "score": 60, "decision": "Moderate Match", "hiring_signal": "Medium",
            "context": {}, "recruiter_view": {}, "hiring_manager_view": {},
            "improvement_plan": {}, "better_fit_roles": [], "final_advice": "Fallback response"
        }
        base["apply_recommendation"] = compute_recommendation(60, "Medium")
        return base

# ---------------- ALEC (CV OPTIMIZER) ----------------

def tailor_cv_with_ai(cv_text, job_text):
    if not client:
        return {"tailored_cv": "Set OpenAI API key to enable CV optimization."}

    prompt = f"""
You are Alec, an expert CV optimizer.

Rewrite the candidate CV so it is tailored for the given job.

Rules:
- Keep it realistic (do NOT invent experience)
- Strengthen impact and clarity
- Inject relevant keywords from the job description
- Improve bullet points to be results-oriented
- Keep it concise and professional

Return ONLY the rewritten CV text.

CV:
{cv_text}

JOB:
{job_text}
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return {"tailored_cv": res.choices[0].message.content.strip()}
    except Exception:
        logging.exception("ALEC ERROR")
        return {"tailored_cv": "Error generating tailored CV."}

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("cv_file")
    job = request.form.get("job_description")
    if not file or not job:
        return jsonify({"error": "Missing input"}), 400

    cv_text = extract_text(file.filename, file.read())
    result = analyze_with_ai(cv_text, job)
    return jsonify(result)

@app.route("/tailor", methods=["POST"])
def tailor():
    file = request.files.get("cv_file")
    job = request.form.get("job_description")
    if not file or not job:
        return jsonify({"error": "Missing input"}), 400

    cv_text = extract_text(file.filename, file.read())
    result = tailor_cv_with_ai(cv_text, job)
    return jsonify(result)

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)