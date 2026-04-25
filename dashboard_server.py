# =========================================
# HiddenEdge / SB3PM Advisory & Services Ltd
# Author: Stephan Bals
# © 2026 SB3PM Advisory & Services Ltd
# =========================================

from flask import Flask, request, jsonify, send_file, render_template, Response, session
from core.cv.cv_service import CVService
import zipfile
import io
import os
import stripe

from docx import Document
import PyPDF2

print("HiddenEdge Engine v1.0 | SB3PM")

app = Flask(__name__, template_folder="templates")

# 🔥 REQUIRED FOR SESSION (EMAIL FLOW)
app.secret_key = "hiddenedge_dev_secret"

cv_service = CVService()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# =========================================
# ROUTES
# =========================================

@app.route("/")
def index():
    return render_template("index.html")


# 🔥 KEEP YOUR CURRENT SAFE VERSION
@app.route("/app")
def app_page():
    with open("templates/app.html", "r", encoding="utf-8") as f:
        html = f.read()
    return Response(html, content_type="text/html; charset=utf-8")


@app.route("/eula")
def eula():
    return render_template("eula.html")


@app.route("/email")
def email():
    return render_template("email.html")


# =========================================
# 🔥 FIX: EMAIL SUBMIT (MISSING LINK IN FLOW)
# =========================================

@app.route("/submit-email", methods=["POST"])
def submit_email():
    try:
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"success": False, "error": "No email provided"}), 400

        # Store email (future: DB)
        session["user_email"] = email

        print(f"Captured email: {email}")

        return jsonify({
            "success": True,
            "redirect": "/app"
        })

    except Exception as e:
        print("EMAIL ERROR:", str(e))
        return jsonify({"success": False}), 500


# =========================================
# SUCCESS PAGE (UNCHANGED)
# =========================================

@app.route("/success")
def success():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>HiddenEdge – Payment Successful</title>
        <style>
            body {
                background: linear-gradient(135deg, #0b1220, #132a4a);
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
                padding-top: 60px;
            }
            .container {
                max-width: 700px;
                margin: auto;
            }
            img {
                width: 180px;
                margin-bottom: 20px;
            }
            .btn {
                display: inline-block;
                padding: 14px 24px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
                background: linear-gradient(135deg, #4facfe, #6a82fb);
                color: white;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <img src="/static/robots/nestor.png">
            <h1>✅ Your payment was successful</h1>
            <p>You now have full access to HiddenEdge.</p>
            <a href="/app" class="btn">🚀 Back to platform</a>
        </div>
    </body>
    </html>
    """


# =========================================
# FILE EXTRACTION
# =========================================

def extract_text_from_docx(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def extract_text_from_pdf(file_bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    return "\n".join([p.extract_text() or "" for p in reader.pages])


def extract_text_from_file(filename, file_bytes):
    if filename.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    return None


# =========================================
# ANALYZE
# =========================================

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        files = request.files.getlist("files")
        job_text = request.form.get("job_text", "")

        texts = []
        for file in files:
            extracted = extract_text_from_file(file.filename.lower(), file.read())
            if extracted:
                texts.append(extracted)

        if not texts:
            return jsonify({"error": "No CV content extracted"}), 400

        result = cv_service.analyze_cv(texts, job_text)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================
# REFINE
# =========================================

@app.route("/refine-cv", methods=["POST"])
def refine_cv():
    try:
        files = request.files.getlist("files")
        job_text = request.form.get("job_text", "")
        answers = request.form.get("answers", "")

        texts = []
        for file in files:
            extracted = extract_text_from_file(file.filename.lower(), file.read())
            if extracted:
                texts.append(extracted)

        if not texts:
            return jsonify({"error": "No CV content extracted"}), 400

        result = cv_service.refine_cv_with_answers(texts, job_text, answers)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================
# DOWNLOAD
# =========================================

@app.route("/download_cv", methods=["POST"])
def download_cv():
    data = request.json
    cv = data.get("cv", {})

    doc = Document()
    doc.add_heading(cv.get("name", "Candidate"), 0)

    if cv.get("summary"):
        doc.add_heading("Summary", level=1)
        doc.add_paragraph(cv.get("summary"))

    stream = io.BytesIO()
    doc.save(stream)
    stream.seek(0)

    return send_file(
        stream,
        as_attachment=True,
        download_name="HiddenEdge_CV.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


# =========================================
# STRIPE TEST
# =========================================

@app.route("/test-stripe")
def test_stripe():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price": os.getenv("STRIPE_PRICE_ID"),
            "quantity": 1,
        }],
        success_url="http://127.0.0.1:5000/success",
        cancel_url="http://127.0.0.1:5000/",
    )

    return f"<a href='{session.url}'>Test Payment</a>"


# =========================================
# RUN
# =========================================

if __name__ == "__main__":
    app.run(debug=True)