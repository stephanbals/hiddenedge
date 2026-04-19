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

client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)

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

# ---------------- RECOMMENDATION LOGIC ----------------

def compute_recommendation(score, signal):

    if score >= 75 and signal == "High":
        return {
            "decision": "Apply",
            "reason": "Your profile strongly matches the role and you are likely to progress."
        }

    if score < 50 or signal == "Low":
        return {
            "decision": "Do Not Apply",
            "reason": "There is a fundamental mismatch with the core requirements of this role."
        }

    return {
        "decision": "Consider",
        "reason": "There is partial alignment, but you may face stronger competing candidates."
    }

# ---------------- AI ENGINE ----------------

def analyze_with_ai(cv_text, job_text):

    if not client:
        fallback = {
            "score": 50,
            "decision": "Moderate Match",
            "hiring_signal": "Medium",
            "context": {},
            "recruiter_view": {
                "screening_decision": "Moderate Match",
                "risk_level": "Medium",
                "observations": [],
                "concerns": [],
                "verdict": "AI not active"
            },
            "hiring_manager_view": {
                "confidence_level": "Low",
                "strengths": [],
                "concerns": [],
                "verdict": "AI not active"
            },
            "improvement_plan": {
                "priority_actions": [],
                "quick_wins": [],
                "strategic_changes": []
            },
            "final_advice": "Set OpenAI API key"
        }

        fallback["apply_recommendation"] = compute_recommendation(50, "Medium")
        return fallback

    prompt = f"""
You are simulating TWO perspectives:

1. Recruiter (screening gatekeeper)
2. Hiring Manager (final decision maker)

Additionally:
You are advising the CANDIDATE on what to do next.

Return STRICT JSON:

{{
  "context": {{
    "role_type": "",
    "seniority": "",
    "domain": "",
    "environment": ""
  }},

  "score": number,
  "decision": "Strong Match" | "Moderate Match" | "Weak Match",
  "hiring_signal": "High" | "Medium" | "Low",

  "recruiter_view": {{
    "screening_decision": "",
    "risk_level": "Low" | "Medium" | "High",
    "observations": [],
    "concerns": [],
    "verdict": ""
  }},

  "hiring_manager_view": {{
    "confidence_level": "High" | "Medium" | "Low",
    "strengths": [],
    "concerns": [],
    "verdict": ""
  }},

  "improvement_plan": {{
    "priority_actions": [],
    "quick_wins": [],
    "strategic_changes": []
  }},

  "final_advice": ""
}}

IMPORTANT RULES:
- Recruiter view = screening perspective
- Hiring manager view = delivery & trust perspective

- Improvement Plan MUST be written TO THE CANDIDATE
- Final Advice MUST be written TO THE CANDIDATE
- NEVER give advice to employer or hiring team
- NEVER say "seek candidates" or "refine job description"
- Always speak directly to the person applying (use "you")

- Be realistic, critical, and specific
- Avoid generic statements

CV:
{cv_text}

JOB:
{job_text}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        parsed = safe_json_parse(response.choices[0].message.content)

        if not parsed:
            raise Exception("Parse failed")

        parsed["apply_recommendation"] = compute_recommendation(
            parsed.get("score", 50),
            parsed.get("hiring_signal", "Medium")
        )

        return parsed

    except Exception:
        logging.exception("AI ERROR")

        fallback = {
            "score": 60,
            "decision": "Moderate Match",
            "hiring_signal": "Medium",
            "context": {},
            "recruiter_view": {},
            "hiring_manager_view": {},
            "improvement_plan": {
                "priority_actions": ["Retry analysis"],
                "quick_wins": [],
                "strategic_changes": []
            },
            "final_advice": "Retry the analysis."
        }

        fallback["apply_recommendation"] = compute_recommendation(60, "Medium")
        return fallback

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

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)