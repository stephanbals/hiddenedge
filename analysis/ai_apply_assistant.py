import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_assist(role, company, description):

    prompt = f"""
You are an expert career coach.

A senior IT transformation professional is applying to this role:

ROLE: {role}
COMPANY: {company}

JOB DESCRIPTION:
{description}

TASK:

1. Suggest how to adapt the CV (bullet points, focus areas)
2. Highlight key skills to emphasize
3. Write a short professional intro message (3-5 lines)

Keep it concise and practical.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content