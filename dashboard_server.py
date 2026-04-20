from flask import Flask, request, jsonify, send_file
from core.cv.cv_service import CVService
import zipfile
import io
import os

from docx import Document
import PyPDF2

# 🔥 AI
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
cv_service = CVService()

# =========================================
# FILE EXTRACTION
# =========================================

def extract_text_from_txt(file_bytes):
    return file_bytes.decode("utf-8", errors="ignore")


def extract_text_from_docx(file_bytes):
    file_stream = io.BytesIO(file_bytes)
    doc = Document(file_stream)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def extract_text_from_pdf(file_bytes):
    file_stream = io.BytesIO(file_bytes)
    reader = PyPDF2.PdfReader(file_stream)
    text = []
    for page in reader.pages:
        try:
            text.append(page.extract_text() or "")
        except:
            continue
    return "\n".join(text)


def extract_text_from_file(filename, file_bytes):
    filename = filename.lower()

    if filename.endswith(".txt") or filename.endswith(".md"):
        return extract_text_from_txt(file_bytes)

    elif filename.endswith(".docx"):
        return extract_text_from_docx(file_bytes)

    elif filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)

    return None


# =========================================
# HOME
# =========================================

@app.route("/")
def index():
    return open("templates/index.html").read()


# =========================================
# UPLOAD CV(s)
# =========================================

@app.route("/upload_cv", methods=["POST"])
def upload_cv():

    files = request.files.getlist("files")
    texts = []

    for file in files:

        filename = file.filename.lower()

        if filename.endswith(".zip"):
            with zipfile.ZipFile(file, 'r') as zip_ref:
                for name in zip_ref.namelist():
                    if name.endswith("/"):
                        continue
                    try:
                        file_bytes = zip_ref.read(name)
                        extracted = extract_text_from_file(name, file_bytes)
                        if extracted and extracted.strip():
                            texts.append(extracted)
                    except:
                        continue

        else:
            try:
                file_bytes = file.read()
                extracted = extract_text_from_file(filename, file_bytes)
                if extracted and extracted.strip():
                    texts.append(extracted)
            except:
                continue

    if not texts:
        return jsonify({"error": "No content extracted"}), 400

    result = cv_service.generate_master_cv(texts)

    return jsonify({
        "texts": texts,
        "master_cv": result.get("cv", "")
    })


# =========================================
# BASE SCORING (SAFE)
# =========================================

def compute_match_score(cv_text, job_text):
    try:
        cv_words = set(cv_text.lower().split())
        job_words = set(job_text.lower().split())

        if not job_words:
            return 0

        overlap = cv_words.intersection(job_words)
        score = int((len(overlap) / len(job_words)) * 100)

        return min(score, 95)
    except:
        return 50


# =========================================
# ELITE AI ANALYSIS (NEW LAYER)
# =========================================

def elite_analysis(cv_text, job_text):

    try:
        prompt = f"""
You are BOTH:
1. A senior recruiter (ATS + screening mindset)
2. A hiring manager responsible for delivery

Analyze the candidate against the job.

Be realistic, critical, and specific.

RETURN EXACT FORMAT:

RECRUITER VIEW:
- Strong signals (bullet points)
- Concerns (bullet points)
- Screening Decision: PASS or REJECT
- Reason

HIRING MANAGER VIEW:
- Strengths (bullet points)
- Risks (bullet points)
- Decision: HIRE or DO NOT HIRE
- Reason

NO GENERIC TEXT. NO FLUFF.

CV:
{cv_text[:4000]}

JOB:
{job_text[:2000]}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        print("AI ERROR:", e)
        return None


# =========================================
# STRUCTURED OUTPUT (SAFE FALLBACK)
# =========================================

def build_safe_output(score):

    if score >= 75:
        decision = "APPLY"
        confidence = "High"
    elif score >= 50:
        decision = "TRY"
        confidence = "Medium"
    else:
        decision = "DO NOT APPLY"
        confidence = "Low"

    return decision, confidence


# =========================================
# ANALYZE
# =========================================

@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.json
    texts = data.get("texts", [])
    job_text = data.get("job_text", "")

    if not texts or not job_text:
        return jsonify({"error": "Missing input"}), 400

    combined_cv = "\n".join(texts)

    # ===== BASE SCORE =====
    score = compute_match_score(combined_cv, job_text)
    decision, confidence = build_safe_output(score)

    # ===== ELITE LAYER =====
    ai_analysis = elite_analysis(combined_cv, job_text)

    # ===== FALLBACK =====
    if not ai_analysis:
        recruiter_view = "Fallback recruiter analysis (AI unavailable)"
        hiring_view = "Fallback hiring manager analysis (AI unavailable)"
    else:
        # crude split but reliable
        parts = ai_analysis.split("HIRING MANAGER VIEW:")

        recruiter_view = parts[0].strip()
        hiring_view = "HIRING MANAGER VIEW:" + parts[1].strip() if len(parts) > 1 else ""

    return jsonify({
        "match_score": score,
        "confidence": confidence,
        "final_decision": decision,
        "recruiter_view": recruiter_view,
        "hiring_manager_view": hiring_view,
        "advice": f"FINAL DECISION: {decision}\nConfidence: {confidence}"
    })


# =========================================
# TAILOR (UNCHANGED)
# =========================================

@app.route("/tailor_cv", methods=["POST"])
def tailor_cv():

    data = request.json
    texts = data.get("texts", [])
    job_text = data.get("job_text", "")

    if not texts or not job_text:
        return jsonify({"error": "Missing input"}), 400

    master = cv_service.generate_master_cv(texts)
    tailored = cv_service.tailor_cv_to_job(texts, job_text)

    return jsonify({
        "master_cv": master.get("cv", ""),
        "tailored_cv": tailored.get("cv", "")
    })


# =========================================
# DOWNLOAD (UNCHANGED)
# =========================================

@app.route("/download_cv", methods=["POST"])
def download_cv():

    data = request.json
    cv_text = data.get("cv", "")

    if not cv_text:
        return jsonify({"error": "Empty CV"}), 400

    doc = Document()

    for line in cv_text.split("\n"):
        doc.add_paragraph(line)

    stream = io.BytesIO()
    doc.save(stream)
    stream.seek(0)

    return send_file(
        stream,
        as_attachment=True,
        download_name="Tailored_CV.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


# =========================================
# RUN
# =========================================

if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    app.run(debug=True)