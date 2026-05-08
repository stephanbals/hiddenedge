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

from core.cv.cv_service import CVService

from core.scoring.scoring_engine import (
    score_job,
    extract_keywords_from_text
)

import psycopg2
import requests
import traceback
import os
import stripe

from io import BytesIO

from dotenv import load_dotenv

from docx import Document
from docx.shared import Pt

# =========================================
# LOAD ENV
# =========================================

load_dotenv()

# =========================================
# APP INIT
# =========================================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

CORS(app)

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

def get_db():

    return psycopg2.connect(
        os.getenv("DATABASE_URL")
    )

# =========================================
# INIT DATABASE
# =========================================

def init_db():

    try:

        conn = get_db()

        cur = conn.cursor()

        # =========================================
        # USERS
        # =========================================

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id SERIAL PRIMARY KEY,

            email TEXT UNIQUE,

            free_uses INTEGER
            DEFAULT 0,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # =========================================
        # SUBSCRIPTIONS
        # =========================================

        cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (

            id SERIAL PRIMARY KEY,

            email TEXT,

            stripe_customer_id TEXT,

            stripe_subscription_id TEXT UNIQUE,

            status TEXT,

            plan TEXT,

            cancel_at_period_end BOOLEAN
            DEFAULT FALSE,

            current_period_end TIMESTAMP,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # =========================================
        # SAFE MIGRATION
        # =========================================

        try:

            cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS free_uses INTEGER DEFAULT 0
            """)

        except Exception as migration_error:

            print(
                "[MIGRATION WARNING]",
                migration_error
            )

        conn.commit()

        cur.close()
        conn.close()

        print(
            "[DB] initialization complete"
        )

    except Exception as e:

        print(
            "[DB INIT ERROR]",
            e
        )

        traceback.print_exc()

# =========================================
# SUBSCRIPTION LOOKUP
# =========================================

def get_subscription_by_email(email):

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""

        SELECT
            email,
            status,
            plan,
            current_period_end

        FROM subscriptions

        WHERE email = %s

        ORDER BY created_at DESC

        LIMIT 1

        """, (email,))

        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            return None

        return {

            "email": row[0],
            "status": row[1],
            "plan": row[2],
            "current_period_end": row[3]
        }

    except Exception as e:

        print(
            "[SUB LOOKUP ERROR]",
            e
        )

        return None

# =========================================
# USER USAGE
# =========================================

def get_user_free_uses(email):

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""

        SELECT free_uses

        FROM users

        WHERE email = %s

        """, (email,))

        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            return 0

        return row[0] or 0

    except Exception as e:

        print(
            "[FREE USE LOOKUP ERROR]",
            e
        )

        return 0


def increment_user_free_uses(email):

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""

        UPDATE users

        SET free_uses = free_uses + 1

        WHERE email = %s

        """, (email,))

        conn.commit()

        cur.close()
        conn.close()

        print(
            f"[FREE USE INCREMENTED] {email}"
        )

    except Exception as e:

        print(
            "[FREE USE INCREMENT ERROR]",
            e
        )

        traceback.print_exc()

# =========================================
# SAVE SUBSCRIPTION
# =========================================

def save_subscription(

    email,
    customer_id,
    subscription_id,
    status,
    plan,
    current_period_end

):

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""

        INSERT INTO subscriptions (

            email,
            stripe_customer_id,
            stripe_subscription_id,
            status,
            plan,
            current_period_end

        )

        VALUES (

            %s,
            %s,
            %s,
            %s,
            %s,

            CASE
                WHEN %s IS NOT NULL
                THEN to_timestamp(%s)
                ELSE NULL
            END
        )

        ON CONFLICT (
            stripe_subscription_id
        )

        DO UPDATE SET

            status = EXCLUDED.status,

            current_period_end =
                EXCLUDED.current_period_end

        """, (

            email,
            customer_id,
            subscription_id,
            status,
            plan,

            current_period_end,
            current_period_end

        ))

        conn.commit()

        cur.close()
        conn.close()

        print(
            f"[SUBSCRIPTION SAVED] {email}"
        )

    except Exception as e:

        print(
            "[SAVE SUB ERROR]",
            e
        )

        traceback.print_exc()

# =========================================
# CV EXTRACTION
# =========================================

def extract_cv_text(file):

    if not file:
        return ""

    filename = file.filename.lower()

    # =========================================
    # ALLOWED FILE TYPES
    # =========================================

    allowed_extensions = (
        ".pdf",
        ".docx",
        ".txt"
    )

    if not filename.endswith(allowed_extensions):

        raise ValueError(
            "Unsupported file format. "
            "Please upload a PDF, DOCX, or TXT file."
        )

    try:

        # =========================================
        # DOCX
        # =========================================

        if filename.endswith(".docx"):

            doc = Document(file)

            text = "\n".join([
                p.text for p in doc.paragraphs
            ])

            return text.strip()

        # =========================================
        # PDF
        # =========================================

        elif filename.endswith(".pdf"):

            try:

                from pypdf import PdfReader

                reader = PdfReader(file)

                text = ""

                for page in reader.pages:

                    extracted = page.extract_text()

                    if extracted:
                        text += extracted + "\n"

                return text.strip()

            except Exception as pdf_error:

                print(
                    "PDF PARSE ERROR:",
                    pdf_error
                )

                raise ValueError(
                    "Unable to read PDF file."
                )

        # =========================================
        # TXT
        # =========================================

        elif filename.endswith(".txt"):

            return file.read().decode(
                "utf-8",
                errors="ignore"
            ).strip()

        # =========================================
        # SAFETY FALLBACK
        # =========================================

        else:

            raise ValueError(
                "Unsupported file format."
            )

    except ValueError:
        raise

    except Exception as e:

        print("CV PARSE ERROR:", e)

        raise ValueError(
            "Failed to process uploaded file."
        )

# =========================================
# PAGE ROUTES
# =========================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/eula")
def eula():
    return render_template("eula.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/email")
def email():
    return render_template("email.html")


@app.route("/app")
def app_page():
    return render_template("app.html")


@app.route("/payment")
def payment():
    return render_template("payment.html")


@app.route("/payment-cancel")
def payment_cancel():
    return render_template(
        "payment-cancel.html"
    )

# =========================================
# STRIPE SUCCESS
# =========================================

@app.route("/success")
def success():

    try:

        session_id = request.args.get(
            "session_id"
        )

        print(
            f"[STRIPE SUCCESS] session_id={session_id}"
        )

        if not session_id:

            return redirect("/app")

        checkout_session = (
            stripe.checkout.Session.retrieve(
                session_id
            )
        )

        subscription_id = (
            checkout_session.subscription
        )

        customer_id = (
            checkout_session.customer
        )

        customer_email = None

        try:

            if (
                hasattr(
                    checkout_session,
                    "customer_details"
                )
                and checkout_session.customer_details
            ):

                customer_email = (
                    checkout_session
                    .customer_details
                    .email
                )

        except Exception:
            pass

        if not customer_email:

            try:

                customer_email = (
                    checkout_session
                    .customer_email
                )

            except Exception:
                pass

        subscription = (
            stripe.Subscription.retrieve(
                subscription_id
            )
        )

        current_period_end = None

        try:

            if (
                hasattr(subscription, "_data")
                and isinstance(
                    subscription._data,
                    dict
                )
            ):

                current_period_end = (
                    subscription._data.get(
                        "current_period_end",
                        None
                    )
                )

        except Exception:

            current_period_end = None

        save_subscription(

            email=customer_email,

            customer_id=customer_id,

            subscription_id=subscription_id,

            status=subscription.status,

            plan="premium",

            current_period_end=current_period_end
        )

        return redirect(
            "/app?payment=success"
        )

    except Exception as e:

        print(
            "[SUCCESS ROUTE ERROR]"
        )

        print(e)

        traceback.print_exc()

        return redirect(
            "/app?payment=failed"
        )

# =========================================
# STRIPE CUSTOMER PORTAL
# =========================================

@app.route(
    "/create-customer-portal-session",
    methods=["POST"]
)
def create_customer_portal():

    try:

        data = request.get_json()

        email = data.get("email")

        if not email:

            return jsonify({
                "error": "Missing email"
            }), 400

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""

        SELECT stripe_customer_id

        FROM subscriptions

        WHERE email = %s

        ORDER BY created_at DESC

        LIMIT 1

        """, (email,))

        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:

            return jsonify({
                "error": "No subscription found"
            }), 404

        stripe_customer_id = row[0]

        session = stripe.billing_portal.Session.create(

            customer=stripe_customer_id,

            return_url="http://127.0.0.1:5000/app"
        )

        return jsonify({
            "url": session.url
        })

    except Exception as e:

        print(
            "[CUSTOMER PORTAL ERROR]",
            e
        )

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

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
            == "active"
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

        subscription = (
            get_subscription_by_email(email)
        )

        subscription_active = (

            subscription
            and subscription.get("status")
            == "active"
        )

        used_tries = (
            get_user_free_uses(email)
        )

        if (
            not subscription_active
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
            == "active"
        )

        if not subscription_active:

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
# JOB SOURCE
# =========================================

def search_jobs_real_sources(
    keywords,
    region
):

    all_results = []

    fallback_regions = [
        region,
        "Netherlands",
        "Germany",
        "Remote",
        "Europe"
    ]

    seen = set()

    search_regions = []

    for r in fallback_regions:

        if r and r.lower() not in seen:

            search_regions.append(r)

            seen.add(r.lower())

    for current_region in search_regions:

        region_results = []

        # =========================================
        # ADZUNA
        # =========================================

        try:

            adzuna_url = (
                "https://api.adzuna.com/"
                "v1/api/jobs/be/search/1"
            )

            adzuna_params = {

                "app_id":
                    os.getenv(
                        "ADZUNA_APP_ID"
                    ),

                "app_key":
                    os.getenv(
                        "ADZUNA_APP_KEY"
                    ),

                "what":
                    keywords,

                "where":
                    current_region,

                "results_per_page":
                    5
            }

            adzuna_response = requests.get(
                adzuna_url,
                params=adzuna_params
            )

            adzuna_data = (
                adzuna_response.json()
            )

            for job in adzuna_data.get(
                "results",
                []
            ):

                region_results.append({

                    "id":
                        f"adzuna_{job.get('id')}",

                    "title":
                        job.get("title"),

                    "company":
                        job.get(
                            "company",
                            {}
                        ).get(
                            "display_name"
                        ),

                    "location":
                        job.get(
                            "location",
                            {}
                        ).get(
                            "display_name"
                        ),

                    "url":
                        job.get(
                            "redirect_url"
                        ),

                    "rate":
                        job.get(
                            "salary_max"
                        )
                })

        except Exception as e:

            print(
                "ADZUNA FETCH ERROR:",
                e
            )

        # =========================================
        # JOOBLE
        # =========================================

        try:

            jooble_key = os.getenv(
                "JOOBLE_API_KEY"
            )

            jooble_url = (
                f"https://jooble.org/api/"
                f"{jooble_key}"
            )

            jooble_payload = {

                "keywords":
                    keywords,

                "location":
                    current_region
            }

            jooble_response = requests.post(
                jooble_url,
                json=jooble_payload
            )

            jooble_data = (
                jooble_response.json()
            )

            for job in jooble_data.get(
                "jobs",
                []
            ):

                region_results.append({

                    "id":
                        f"jooble_{job.get('id')}",

                    "title":
                        job.get("title"),

                    "company":
                        job.get("company"),

                    "location":
                        job.get("location"),

                    "url":
                        job.get("link"),

                    "rate":
                        None
                })

        except Exception as e:

            print(
                "JOOBLE FETCH ERROR:",
                e
            )

        if len(region_results) > 0:

            all_results.extend(
                region_results
            )

            break

    return all_results[:10]

# =========================================
# STRIPE CHECKOUT
# =========================================

@app.route(
    "/create-checkout-session",
    methods=["POST"]
)
def create_checkout():

    try:

        data = request.get_json(
            silent=True
        )

        customer_email = None

        if data and isinstance(data, dict):

            customer_email = data.get(
                "email"
            )

        if not customer_email:

            customer_email = request.form.get(
                "email"
            )

        if not customer_email:

            customer_email = request.args.get(
                "email"
            )

        if not customer_email:

            return jsonify({
                "error": "Missing email"
            }), 400

        price_id = os.getenv(
            "STRIPE_PRICE_ID"
        )

        checkout = (
            stripe.checkout.Session.create(

                mode="subscription",

                customer_email=
                    customer_email,

                line_items=[{
                    "price": price_id,
                    "quantity": 1
                }],

                success_url=(

                    "http://127.0.0.1:5000/"
                    "success"
                    "?session_id={CHECKOUT_SESSION_ID}"
                ),

                cancel_url=(

                    "http://127.0.0.1:5000/"
                    "payment-cancel"
                )
            )
        )

        return jsonify({
            "url": checkout.url
        })

    except Exception as e:

        print("STRIPE ERROR:", e)

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

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )