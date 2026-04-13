from flask import Flask, request, jsonify, render_template, session
from core.cv.cv_service import extract_text_from_files, evaluate_fit, tailor_cv

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

    # Ensure valid extraction
    cleaned = [t.strip() for t in texts if t and t.strip()]

    if not cleaned:
        return jsonify({"error": "CV could not be read. Please upload a valid DOCX or PDF."})

    # Store in session for safety
    session["texts"] = cleaned

    return jsonify({"texts": cleaned})


# -----------------------------
# ANALYZE + TAILOR
# -----------------------------
@app.route("/tailor_cv", methods=["POST"])
def tailor():

    data = request.json

    # Always use session as source of truth
    texts = session.get("texts", [])
    job_text = data.get("job_text", "")

    if not texts:
        return jsonify({"error": "No CV found. Please upload again."})

    if not job_text or not job_text.strip():
        return jsonify({"error": "Job description is empty."})

    # PAYWALL
    session["count"] = session.get("count", 0) + 1

    if session["count"] > 3 and not session.get("paid"):
        return jsonify({"paywall": True})

    # PROCESS
    evaluation = evaluate_fit(texts, job_text)
    tailored = tailor_cv(texts, job_text, evaluation)

    return jsonify({
        "evaluation": evaluation,
        "tailored_cv": tailored
    })


# -----------------------------
# PAYWALL UNLOCK
# -----------------------------
@app.route("/unlock", methods=["POST"])
def unlock():
    session["paid"] = True
    return jsonify({"status": "unlocked"})


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    print("🚀 HiddenEdge server running...")
    app.run(debug=True)