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

# ---------------- DECISION ENGINE ----------------

def analyze_with_ai(cv_text, job_text):

    if not client:
        return {
            "score": 50,
            "decision": "Moderate Match",
            "hiring_signal": "Medium",
            "key_requirements": [],
            "strengths": ["AI not configured"],
            "gaps": [],
            "deal_breakers": [],
            "risk_factors": [],
            "improvements": [],
            "competitive_position": "AI not active",
            "final_advice": "Set OpenAI API key"
        }

    prompt = f"""
You are a senior IT recruiter making a hiring decision.

STEP 1: Extract the most important requirements.
STEP 2: Compare CV vs requirements.
STEP 3: Evaluate hiring likelihood vs typical candidates.

Return STRICT JSON:

{{
  "score": number (0-100),
  "decision": "Strong Match" | "Moderate Match" | "Weak Match",
  "hiring_signal": "High" | "Medium" | "Low",

  "key_requirements": [],
  "strengths": [],
  "gaps": [],

  "deal_breakers": [],
  "risk_factors": [],

  "improvements": [],

  "competitive_position": "",
  "final_advice": ""
}}

Rules:
- Be realistic and critical
- Identify if candidate would actually get hired
- Highlight what stronger candidates may have
- Do NOT be polite — be accurate

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

        raw = response.choices[0].message.content.strip()
        parsed = safe_json_parse(raw)

        if parsed:
            return parsed

        raise Exception("Parse failed")

    except Exception:
        logging.exception("AI ERROR")

        return {
            "score": 60,
            "decision": "Moderate Match",
            "hiring_signal": "Medium",
            "key_requirements": [],
            "strengths": ["General experience present"],
            "gaps": ["Detailed analysis unavailable"],
            "deal_breakers": [],
            "risk_factors": ["Analysis fallback triggered"],
            "improvements": ["Retry"],
            "competitive_position": "Unable to determine",
            "final_advice": "System fallback"
        }

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

    file_bytes = file.read()
    cv_text = extract_text(file.filename, file_bytes)

    result = analyze_with_ai(cv_text, job)

    return jsonify(result)

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)