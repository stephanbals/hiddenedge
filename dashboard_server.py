from flask import Flask, request, jsonify, render_template, session, send_file
from core.cv.cv_service import extract_text_from_files, evaluate_fit, tailor_cv
from core.cv.docx_export import generate_docx
import os
import uuid

app = Flask(__name__)
app.secret_key = "hiddenedge-secret"


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------
# UPLOAD CV
# -----------------------------
@app.route("/upload_cv", methods=["POST"])
def upload_cv():

    files = request.files.getlist("files")

    if not files:
        return jsonify({"error": "No file uploaded."})

    texts = extract_text_from_files(files)

    cleaned = [t.strip() for t in texts if t and t.strip()]

    if not cleaned:
        return jsonify({"error": "CV could not be read. Please upload a valid DOCX or PDF."})

    session["texts"] = cleaned

    return jsonify({"texts": cleaned})


# -----------------------------
# ANALYZE + TAILOR
# -----------------------------
@app.route("/tailor_cv", methods=["POST"])
def tailor():

    data = request.json

    texts = session.get("texts", [])
    job_text = data.get("job_text", "")

    if not texts:
        return jsonify({"error": "No CV found. Please upload again."})

    if not job_text or not job_text.strip():
        return jsonify({"error": "Job description is empty."})

    # PAYWALL COUNTER
    session["count"] = session.get("count", 0) + 1

    if session["count"] > 3 and not session.get("paid"):
        return jsonify({"paywall": True})

    evaluation = evaluate_fit(texts, job_text)
    tailored = tailor_cv(texts, job_text, evaluation)

    # STORE FOR DOWNLOAD
    session["last_tailored_cv"] = tailored

    return jsonify({
        "evaluation": evaluation,
        "tailored_cv": tailored
    })


# -----------------------------
# DOWNLOAD DOCX (PAYWALL CONTROLLED)
# -----------------------------
@app.route("/download_cv", methods=["POST"])
def download_cv():

    if not session.get("paid"):
        return jsonify({"paywall": True}), 403

    tailored = session.get("last_tailored_cv")

    if not tailored:
        return jsonify({"error": "No CV available. Run analysis first."})

    filename = f"tailored_cv_{uuid.uuid4().hex}.docx"
    filepath = os.path.join("/tmp", filename)

    # ✅ CORRECT FUNCTION CALL
    generate_docx(tailored, filepath)

    return send_file(filepath, as_attachment=True)


# -----------------------------
# PAYWALL UNLOCK
# -----------------------------
@app.route("/unlock", methods=["POST"])
def unlock():
    session["paid"] = True
    return jsonify({"status": "unlocked"})


# -----------------------------
# RUN (RENDER COMPATIBLE)
# -----------------------------
if __name__ == "__main__":
    print("🚀 HiddenEdge server running...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)