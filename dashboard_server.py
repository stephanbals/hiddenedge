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

# ---------------- ANALYSIS ----------------

def analyze_with_ai(cv_text, job_text):

    if not client:
        return {
            "score": 50,
            "decision": "Moderate Match",
            "key_requirements": [],
            "strengths": ["AI not configured"],
            "gaps": [],
            "improvements": [],
            "final_advice": "Set OpenAI API key"
        }

    prompt = f"""
You are a senior IT recruiter evaluating a candidate.

Your job:
1. Extract key requirements from the job
2. Compare CV vs those requirements
3. Give a realistic hiring-style assessment

Return STRICT JSON:

{{
  "score": number (0-100),
  "decision": "Strong Match" | "Moderate Match" | "Weak Match",

  "key_requirements": [],
  "strengths": [],
  "gaps": [],
  "improvements": [],
  "final_advice": ""
}}

Rules:
- Be critical and realistic
- No generic statements
- No placeholders like "AI failed"
- Base everything on actual comparison

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

    except Exception as e:
        logging.exception("AI ERROR")

        return {
            "score": 60,
            "decision": "Moderate Match",
            "key_requirements": [],
            "strengths": ["General experience present"],
            "gaps": ["Detailed analysis unavailable"],
            "improvements": ["Retry analysis"],
            "final_advice": "System fallback triggered"
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