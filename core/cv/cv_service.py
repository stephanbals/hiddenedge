import os
from openai import OpenAI

# Initialize OpenAI client safely
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable")

client = OpenAI(api_key=OPENAI_API_KEY)


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
            model="gpt-4.1-mini",  # stable & available
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