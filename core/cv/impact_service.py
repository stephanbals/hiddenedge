from typing import List, Dict
from core.llm.llm_client import call_llm


def detect_level(cv_text: str) -> str:

    text = cv_text.lower()

    if any(x in text for x in [
        "program manager", "director", "transformation lead", "head of"
    ]):
        return "senior"

    if any(x in text for x in [
        "manager", "consultant", "specialist"
    ]):
        return "mid"

    return "operational"


def split_roles(cv_text: str) -> List[Dict]:

    lines = cv_text.split("\n")

    roles = []
    current = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if "|" in line and any(char.isdigit() for char in line):
            if current:
                roles.append("\n".join(current))
                current = []

        current.append(line)

    if current:
        roles.append("\n".join(current))

    parsed = []
    for r in roles[:6]:
        title = r.split("\n")[0][:80]
        parsed.append({"title": title, "content": r})

    return parsed


def generate_questions(role_title: str, role_text: str, level: str) -> List[str]:

    if level == "operational":

        prompt = f"""
You are a friendly recruiter having a normal, relaxed conversation with a candidate for an admin / support role.

The candidate:
- is not a manager
- does not own strategy, budgets, or KPIs

Your goal:
Ask 3 natural questions that help the candidate reflect a bit and explain their experience better.

VERY IMPORTANT:
- Write like you are speaking in a real conversation
- Keep it simple, warm, and human
- Avoid formal or corporate language
- Do NOT use words like: projects, initiatives, strategy, metrics, impact

TONE:
- Questions should feel easy to answer, but still make the person think a little
- Slightly informal is good
- Avoid repeating patterns like:
  "Can you share an example..."
  "Describe a situation..."
  "What specific contributions..."

GOOD STYLE:
- "Looking back, what’s something you did at work that you’re proud of?"
- "Was there a moment at work where things got a bit tricky? What did you do?"
- "How do you usually handle it when things get busy or a bit chaotic?"

ROLE:
{role_title}

DETAILS:
{role_text}

OUTPUT:
- One question per line
"""

    elif level == "mid":

        prompt = f"""
You are a recruiter speaking to a mid-level professional.

Ask 3 natural, conversational questions about:
- their contributions
- teamwork
- problem solving

Keep the tone human and avoid overly formal phrasing.

ROLE:
{role_title}

DETAILS:
{role_text}

OUTPUT:
- One question per line
"""

    else:  # senior

        prompt = f"""
You are a recruiter speaking to a senior transformation leader.

Ask 3 focused questions about:
- business impact
- scale
- decision-making

Keep it sharp and professional.

ROLE:
{role_title}

DETAILS:
{role_text}

OUTPUT:
- One question per line
"""

    response = call_llm(prompt)

    questions = [
        q.strip("- ").strip()
        for q in response.split("\n")
        if q.strip()
    ]

    return questions[:3]


def analyze_cv_gaps(cv_text: str) -> Dict:

    level = detect_level(cv_text)
    roles = split_roles(cv_text)

    result = []

    for role in roles:
        questions = generate_questions(
            role["title"],
            role["content"],
            level
        )

        if questions:
            result.append({
                "role": role["title"],
                "questions": questions
            })

    return {
        "level_detected": level,
        "roles": result
    }