# =========================================
# HiddenEdge / SB3PM Advisory & Services Ltd
# =========================================

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    send_file,
    redirect
)

from flask_cors import CORS

from core.routes.page_routes import (
    page_routes
)

from core.cv.cv_service import CVService

from core.scoring.scoring_engine import (
    score_job,
    extract_keywords_from_text
)

from core.db.subscription_service import (
    get_subscription_by_email,
    get_user_free_uses,
    increment_user_free_uses,
    save_subscription
)

from core.files.cv_extractor import (
    extract_cv_text
)

from core.jobs.job_search_service import (
    search_jobs_real_sources
)

from core.payments.stripe_service import (
    handle_success,
    create_checkout_session,
    create_customer_portal_session
)

from core.routes.billing_routes import (
    billing_routes
)


import traceback
import os
import stripe

from io import BytesIO

from dotenv import load_dotenv

# from docx import Document
from docx.shared import Pt

# =========================================
# LOAD ENV
# =========================================

load_dotenv()

# =========================================
# BASE URL
# =========================================

BASE_URL = os.getenv(
    "BASE_URL",
    "http://127.0.0.1:5000"
)

# =========================================
# APP INIT
# =========================================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

CORS(app)

app.register_blueprint(
    page_routes
)

app.register_blueprint(
    billing_routes
)

cv_service = CVService()



# =========================================
# STRIPE
# =========================================

stripe.api_key = os.getenv(
    "STRIPE_SECRET_KEY"
)

FREE_TRIAL_LIMIT = 3

# =========================================
# DATABASE
# =========================================

from core.db.database import (
    get_db,
    init_db
)

from core.db.subscription_repository import (
    get_subscription_by_email,
    get_user_free_uses,
    increment_user_free_uses,
    save_subscription
)

# =========================================
# OWNER ACCESS
# =========================================

OWNER_EMAILS = [

    email.strip().lower()

    for email in os.getenv(
        "OWNER_EMAILS",
        ""
    ).split(",")

    if email.strip()
]

def is_owner(email):

    return (
        email
        and email.lower() in OWNER_EMAILS
    )

# =========================================
# FLOW CONTROL
# =========================================

@app.route(
    "/accept-eula",
    methods=["POST"]
)
def accept_eula():

    return jsonify({
        "redirect": "/privacy"
    })


@app.route(
    "/accept-privacy",
    methods=["POST"]
)
def accept_privacy():

    return jsonify({
        "redirect": "/email"
    })

# =========================================
# EMAIL SUBMISSION
# =========================================

@app.route(
    "/submit-email",
    methods=["POST"]
)
def submit_email():

    data = request.get_json()

    email = data.get("email")

    if not email:

        return jsonify({
            "error": "no email"
        }), 400

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""

        INSERT INTO users (

            email

        )

        VALUES (%s)

        ON CONFLICT (email)
        DO NOTHING

        """, (email,))

        conn.commit()

        cur.close()
        conn.close()

        subscription = (
            get_subscription_by_email(email)
        )

        subscription_active = (

    subscription
    and subscription.get("status")
    in [
        "active",
        "trialing"
    ]
)

        if subscription_active:

            return jsonify({

                "access": "granted",

                "subscription": True,

                "free_trials_remaining":
                    "unlimited"
            })

        used_tries = (
            get_user_free_uses(email)
        )
        print("USED TRIES:", used_tries)
        print("EMAIL:", email)
        
        remaining = max(
            0,
            FREE_TRIAL_LIMIT - used_tries
        )

        if remaining <= 0:

            return jsonify({

                "access": "paywall",

                "subscription": False,

                "free_trials_remaining": 0
            })

        return jsonify({

            "access": "granted",

            "subscription": False,

            "free_trials_remaining":
                remaining
        })

    except Exception as e:

        print("DB ERROR:", e)

        traceback.print_exc()

        return jsonify({
            "error": "db_error"
        }), 500

# =========================================
# ANALYZE
# =========================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    try:

        file = request.files.get("files")

        if not file:

            return jsonify({
                "error":
                    "Please upload a CV file."
            }), 400

        job_text = request.form.get(
            "job_text",
            ""
        )

        email = request.form.get(
            "email",
            ""
        )

        print(f"[ANALYZE EMAIL] {email}")

        subscription = (
            get_subscription_by_email(email)
        )

        subscription_active = (

            subscription
            and subscription.get("status")
            in [
                "active",
                "trialing"
            ]
        )

        used_tries = (
            get_user_free_uses(email)
        )

        access_granted = (
            subscription_active
            or is_owner(email)
        )

        if (
            not access_granted
            and used_tries >= FREE_TRIAL_LIMIT
        ):

            return jsonify({

                "paywall": True,

                "message":
                    "Free trial exhausted."

            }), 403

        try:

            cv_text = extract_cv_text(file)

        except ValueError as validation_error:

            return jsonify({

                "error":
                    str(validation_error)

            }), 400

        result = cv_service.analyze_cv(
            [cv_text],
            job_text
        )

        if not subscription_active:

            increment_user_free_uses(email)

            remaining = max(
                0,
                FREE_TRIAL_LIMIT -
                (used_tries + 1)
            )

            result[
                "free_trials_remaining"
            ] = remaining

        else:

            result[
                "free_trials_remaining"
            ] = "unlimited"

        result[
            "subscription_active"
        ] = subscription_active

        return jsonify(result)

    except Exception as e:

        print("[ANALYZE ERROR]")

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

# =========================================
# REFINE
# =========================================

@app.route(
    "/refine",
    methods=["POST"]
)
def refine():

    try:

        file = request.files.get("files")

        if not file:

            return jsonify({
                "error":
                    "Please upload a CV file."
            }), 400

        job_text = request.form.get(
            "job_text",
            ""
        )

        email = request.form.get(
            "email",
            ""
        )

        answers = request.form.getlist(
            "answers"
        )

        subscription = (
            get_subscription_by_email(email)
        )

        subscription_active = (

            subscription
            and subscription.get("status")
            in [
                "active",
                "trialing"
            ]
        )

        access_granted = (
            subscription_active
            or is_owner(email)
        )

        if not access_granted:

            return jsonify({

                "paywall": True,

                "message":
                    "Premium subscription required."

            }), 403

        try:

            cv_text = extract_cv_text(file)

        except ValueError as validation_error:

            return jsonify({

                "error":
                    str(validation_error)

            }), 400

        result = cv_service.refine_cv_with_answers(
            [cv_text],
            job_text,
            answers
        )

        return jsonify(result)

    except Exception as e:

        print("[REFINE ERROR]")

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

# =========================================
# DOWNLOAD CV
# =========================================

@app.route(
    "/download-cv",
    methods=["POST"]
)
def download_cv():

    try:

        data = request.get_json()

        cv_text = data.get(
            "cv",
            ""
        )

        if not cv_text.strip():

            return jsonify({
                "error": "No CV content"
            }), 400

        doc = Document()

        style = doc.styles["Normal"]

        style.font.name = "Calibri"
        style.font.size = Pt(11)

        title = doc.add_heading(
            "Tailored Curriculum Vitae",
            level=1
        )

        title.runs[0].font.size = Pt(22)

        disclaimer = doc.add_paragraph()

        disclaimer_run = disclaimer.add_run(
            "Please review and personalize "
            "this CV before submission to "
            "ensure accuracy, tone, and "
            "alignment with your target role."
        )

        disclaimer_run.italic = True
        disclaimer_run.font.size = Pt(10)

        doc.add_paragraph(" ")

        lines = cv_text.split("\n")

        for line in lines:

            cleaned = line.strip()

            if not cleaned:
                continue

            if (
                cleaned.isupper()
                and len(cleaned) < 60
            ):

                heading = doc.add_heading(
                    cleaned,
                    level=2
                )

                heading.runs[0].font.size = Pt(14)

            elif cleaned.startswith("-"):

                doc.add_paragraph(
                    cleaned[1:].strip(),
                    style="List Bullet"
                )

            else:

                doc.add_paragraph(
                    cleaned
                )

        file_stream = BytesIO()

        doc.save(file_stream)

        file_stream.seek(0)

        return send_file(

            file_stream,

            as_attachment=True,

            download_name=
                "HiddenEdge_Tailored_CV.docx",

            mimetype=(
                "application/vnd.openxmlformats-"
                "officedocument.wordprocessingml."
                "document"
            )
        )

    except Exception as e:

        print("DOCX EXPORT ERROR:", e)

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

# =========================================
# JOB SEARCH + SCORING
# =========================================

@app.route(
    "/api/jobs/search",
    methods=["POST"]
)
def search_jobs():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "Missing JSON body"
            }), 400

        keywords = data.get(
            "keywords",
            ""
        ).strip()

        region = data.get(
            "region",
            ""
        ).strip()

        if not keywords and not region:

            return jsonify({
                "error": "Missing search input"
            }), 400

        jobs = search_jobs_real_sources(
            keywords,
            region
        )

        candidate = {

            "keywords":
                extract_keywords_from_text(
                    keywords
                ),

            "seniority":
                "senior"
        }

        scored_jobs = []

        for job in jobs:

            job_profile = {

                "keywords":
                    extract_keywords_from_text(
                        (job.get("title") or "")
                        + " "
                        + (job.get("company") or "")
                    ),

                "rate":
                    job.get("rate"),

                "seniority":
                    "mid",

                "description":
                    job.get("title")
            }

            score = score_job(
                job_profile,
                candidate
            )

            job["fitScore"] = score[
                "fit_score"
            ]

            job["decision"] = score[
                "decision"
            ]

            job["confidence"] = score[
                "confidence"
            ]

            job["explanation"] = score[
                "explanation"
            ]

            scored_jobs.append(job)

        return jsonify({
            "jobs": scored_jobs
        })

    except Exception as e:

        print(
            "[ERROR] /api/jobs/search failed"
        )

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

# =========================================
# GLOBAL ERROR HANDLER
# =========================================

@app.errorhandler(404)
def handle_404(e):

    return "", 204


@app.errorhandler(Exception)
def handle_exception(e):

    print("[GLOBAL ERROR]")

    traceback.print_exc()

    return jsonify({
        "error": "Internal server error"
    }), 500

# =========================================
# RUN
# =========================================

if __name__ == "__main__":

    init_db()

    port = int(os.environ.get("PORT", 5000))

    debug_mode = (
        os.getenv("MODE", "prod").lower()
        == "dev"
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode
    )