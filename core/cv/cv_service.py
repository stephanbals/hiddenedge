import os
from openai import OpenAI

# Initialize OpenAI client safely
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable")

client = OpenAI(api_key=OPENAI_API_KEY)


# =========================================
# EXISTING FUNCTION (UNCHANGED)
# =========================================

def tailor_cv(texts, job, evaluation):
    """
    Takes:
        texts: extracted CV text
        job: job description
        evaluation: match analysis (score, reasoning, etc.)
    Returns:
        improved CV text
    """

    try:
        prompt = f"""
You are an expert CV optimization assistant.

TASK:
Rewrite and improve the candidate's CV to maximize alignment with the job description.

RULES:
- Keep it realistic and truthful
- Strengthen alignment with required skills
- Use strong, professional language
- Improve structure and clarity
- Keep it concise and impactful

INPUTS:

=== CURRENT CV ===
{texts}

=== JOB DESCRIPTION ===
{job}

=== MATCH ANALYSIS ===
{evaluation}

OUTPUT:
Provide the improved CV only.
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
        )

        result = response.choices[0].message.content

        if not result:
            raise ValueError("Empty response from OpenAI")

        return result

    except Exception as e:
        print("❌ OpenAI CV generation failed:", str(e))
        raise


# =========================================
# REQUIRED CLASS (NEW — WRAPPER ONLY)
# =========================================

class CVService:

    def generate_master_cv(self, texts):
        """
        Simple aggregation of CV inputs
        (keeps your existing behavior intact)
        """
        return {"cv": "\n\n".join(texts)}

    def tailor_cv_to_job(self, texts, job_text):
        """
        Uses existing tailor_cv function
        """
        combined_cv = "\n\n".join(texts)

        # Minimal evaluation placeholder (safe)
        evaluation = "Initial match analysis placeholder"

        improved = tailor_cv(combined_cv, job_text, evaluation)

        return {"cv": improved}