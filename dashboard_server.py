from flask import Flask, request, jsonify, send_file, redirect
from core.cv.cv_service import CVService
import zipfile
import io
import os

from docx import Document
import PyPDF2
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
cv_service = CVService()

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
# ANALYZE (LIMITED MODE)
# =========================================

@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.json
    texts = data.get("texts", [])
    job_text = data.get("job_text", "")

    return jsonify({
        "match_score": 65,
        "confidence": "Medium",
        "final_decision": "TRY",
        "recruiter_view": "LOCKED",
        "hiring_manager_view": "LOCKED",
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