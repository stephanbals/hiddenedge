from flask import Flask, request, jsonify, send_file, redirect
from core.cv.cv_service import CVService
import zipfile
import io
import os
import re

from docx import Document
import PyPDF2
from openai import OpenAI
import stripe

# ===== CONFIG =====
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")

app = Flask(__name__)
cv_service = CVService()

# =========================================
# DOMAIN DETECTION
# =========================================

DOMAIN_KEYWORDS = {
    "medical": ["doctor", "physician", "clinical", "surgery", "hospital", "patient", "orl", "ent"],
    "tech": ["it", "cloud", "software", "sap", "aws", "azure", "digital", "devops"],
    "finance": ["finance", "accounting", "audit", "tax", "banking"],
    "legal": ["law", "legal", "compliance", "contract"],
    "construction": ["construction", "site", "civil", "engineering"],
}


def detect_domain(text):
    text = text.lower()
    scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        scores[domain] = sum(1 for k in keywords if k in text)

    best_domain = max(scores, key=scores.get)

    if scores[best_domain] == 0:
        return "unknown"

    return best_domain


# =========================================
# CONTEXT MESSAGE ENGINE
# =========================================

def build_context(score, cv_domain, job_domain):

    if cv_domain != job_domain and cv_domain != "unknown" and job_domain != "unknown":
        return f"Strong domain mismatch detected ({cv_domain} vs {job_domain})"

    if score < 20:
        return "Very low alignment with core role requirements"

    elif score < 40:
        return "Limited overlap with role expectations"

    elif score < 60:
        return "Partial alignment — significant gaps present"

    elif score < 75:
        return "Good alignment with some gaps"

    elif score < 90:
        return "Strong alignment with minor gaps"

    else:
        return "Excellent fit for the role"


# =========================================
# ROUTES
# =========================================

@app.route("/")
def landing():
    return open("templates/landing.html").read()


@app.route("/eula")
def eula():
    return open("templates/eula.html").read()


@app.route("/email")
def email():
    return open("templates/email.html").read()


@app.route("/app")
def app_page():
    return open("templates/index.html").read()


# =========================================
# STRIPE
# =========================================

@app.route("/create-checkout-session")
def create_checkout_session():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{
            "price": STRIPE_PRICE_ID,
            "quantity": 1,
        }],
        success_url="https://hiddenedge-live.onrender.com/app?paid=true",
        cancel_url="https://hiddenedge-live.onrender.com/app",
    )
    return redirect(session.url, code=303)


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
# UPLOAD
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
# ANALYZE (WITH CONTEXT LINE)
# =========================================

@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.json
    texts = data.get("texts", [])
    job_text = data.get("job_text", "")

    combined_cv = "\n".join(texts)

    cv_domain = detect_domain(combined_cv)
    job_domain = detect_domain(job_text)

    # HARD DOMAIN MISMATCH
    if cv_domain != "unknown" and job_domain != "unknown" and cv_domain != job_domain:
        score = 3
        context = build_context(score, cv_domain, job_domain)

        return jsonify({
            "match_score": score,
            "context_line": context,
            "confidence": "High",
            "final_decision": "DO NOT APPLY",
            "recruiter_view": "Domain mismatch detected.",
            "hiring_manager_view": "Candidate does not meet baseline requirements.",
            "advice": "Do not apply."
        })

    # AI SCORING
    try:
        prompt = f"""
You are a strict recruiter.

Score match between CV and job from 0 to 100.

CV:
{combined_cv[:3000]}

JOB:
{job_text[:1500]}

Return ONLY a number.
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        score_text = response.choices[0].message.content.strip()
        score = int(re.sub("[^0-9]", "", score_text))

    except:
        score = 50

    context = build_context(score, cv_domain, job_domain)

    return jsonify({
        "match_score": max(0, min(score, 100)),
        "context_line": context,
        "confidence": "Medium",
        "final_decision": "TRY",
        "recruiter_view": "Locked",
        "hiring_manager_view": "Locked",
        "advice": "Upgrade required"
    })


# =========================================
# DOWNLOAD
# =========================================

@app.route("/download_cv", methods=["POST"])
def download_cv():

    data = request.json
    cv_text = data.get("cv", "")

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
    app.run(debug=True)