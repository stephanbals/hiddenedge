# =========================================
# HiddenEdge / SB3PM Advisory & Services Ltd
# =========================================

from core.llm.llm_client import call_llm


def reposition_cv(cv_text: str, job_text: str = "", answers: str = "") -> str:

    prompt = f"""
You are an expert CV strategist and recruiter.

Your task is to improve and reposition a CV so it is strongly aligned with the target job, while remaining truthful.

CORE OBJECTIVE:
- Align CV to target role
- Increase credibility and specificity
- Improve interview probability

STRICT RULES:
- DO NOT invent experience
- DO NOT inflate seniority
- KEEP all roles
- Improve wording, structure, and clarity

ALIGNMENT:
- Detect domain, role type, seniority
- Emphasize relevant experience
- Reframe transferable experience if needed

QUALITY IMPROVEMENT:
- Add measurable outcomes where possible
- Replace vague phrasing with concrete statements
- Clarify ownership, scope, and impact

USER INPUT:
- Integrate answers naturally
- Use them to strengthen credibility

STYLE:
- Professional, sharp, credible
- No buzzwords
- No fluff

OUTPUT:
Return ONLY the improved CV.

CV:
{cv_text}

JOB:
{job_text}

ANSWERS:
{answers}
"""

    response = call_llm(prompt)

    return response.strip() if response else cv_text