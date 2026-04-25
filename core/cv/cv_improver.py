if __name__ == "__main__":
    print("HiddenEdge Engine v1.0 | SB3PM")
# =========================================
# HiddenEdge / SB3PM Advisory & Services Ltd
# Author: Stephan Bals
# © 2026 SB3PM Advisory & Services Ltd
#
# This code is proprietary and confidential.
# Unauthorized use, distribution, or replication is prohibited.
# =========================================

from core.llm.llm_client import call_llm


def improve_cv_with_answers(cv_text: str, answers: str) -> str:

    prompt = f"""
You are a senior CV writer.

Your task:
Improve the CV by integrating the user's answers.

STRICT RULES:
- Keep the original structure of the CV
- Do NOT remove roles or rewrite everything
- Enhance existing bullet points with:
    - measurable impact
    - scale (teams, budgets, systems)
    - business outcomes
- Use the answers to strengthen the CV
- Be precise and professional
- Avoid generic phrasing
- Do not add fake information

ORIGINAL CV:
{cv_text}

USER ANSWERS:
{answers}

OUTPUT:
Return ONLY the improved CV.
"""

    response = call_llm(prompt)

    return response.strip() if response else cv_text