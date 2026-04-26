# =========================================
# HiddenEdge CV Service - DYNAMIC ENGINE
# SB3PM Advisory & Services Ltd
# =========================================

import re

class CVService:

    # =========================================
    # ANALYSIS (unchanged stable version)
    # =========================================
    def analyze_cv(self, texts, job_text):

        if not texts:
            return self._empty_response("No CV content provided.")

        if not job_text or len(job_text.strip()) < 30:
            return self._empty_response("Job description too vague.")

        return {
            "fit_score": 78,
            "match_summary": "Strong leadership profile with partial alignment to role requirements.",

            "recruiter_view": {
                "summary": "Strong delivery-focused candidate with leadership experience.",
                "strengths": [
                    "Proven transformation delivery",
                    "Strong stakeholder management",
                    "Leadership across complex environments"
                ],
                "concerns": [
                    "Limited domain specialization",
                    "Missing tooling references"
                ]
            },

            "hiring_manager_view": {
                "summary": "Strategic thinker with execution capability.",
                "strengths": [
                    "Delivers outcomes in complex environments",
                    "Strong business-IT alignment",
                    "Leadership maturity"
                ],
                "concerns": [
                    "Needs deeper technical specificity",
                    "Limited industry examples"
                ]
            },

            "strengths": [
                "Leadership experience",
                "Transformation delivery",
                "Stakeholder alignment"
            ],

            "key_gaps": [
                "Domain specificity",
                "Tooling depth"
            ],

            "recommended_roles": {
                "good_fit": [
                    "Program Manager",
                    "Transformation Lead"
                ]
            },

            "suggested_improvements": [
                "Add measurable outcomes",
                "Align keywords with job description",
                "Highlight governance and delivery impact"
            ],

            "questions": [
                "Describe a complex project you led and its outcome.",
                "How did you manage stakeholders?",
                "What results did you achieve?",
                "How did you handle risks?"
            ]
        }


    # =========================================
    # 🔥 DYNAMIC CV BUILDER
    # =========================================
    def refine_cv_with_answers(self, texts=None, job_text="", answers=""):

        raw_cv = " ".join(texts) if texts else ""
        answers = answers or ""

        # --- extract keywords from job description ---
        keywords = self._extract_keywords(job_text)

        # --- build sections dynamically ---
        summary = self._build_summary(raw_cv, keywords, answers)
        skills = self._build_skills(keywords, raw_cv)
        experience = self._build_experience(raw_cv, answers)

        cv_text = f"""
PROFESSIONAL SUMMARY
{summary}

CORE SKILLS
{skills}

PROFESSIONAL EXPERIENCE
{experience}
"""

        delta = self._build_delta(answers, keywords)

        return {
            "cv_text": cv_text.strip(),
            "delta": delta.strip()
        }


    # =========================================
    # HELPERS
    # =========================================

    def _extract_keywords(self, job_text):
        words = re.findall(r'\b\w+\b', job_text.lower())
        keywords = list(set([w for w in words if len(w) > 5]))
        return keywords[:10]


    def _build_summary(self, cv, keywords, answers):

        base = "Experienced professional with a strong background in complex environments."

        if keywords:
            base += " Relevant expertise includes " + ", ".join(keywords[:5]) + "."

        if answers:
            base += " Demonstrated ability through hands-on experience and proven delivery outcomes."

        return base


    def _build_skills(self, keywords, cv):

        base_skills = [
            "Stakeholder Management",
            "Project / Program Delivery",
            "Risk Management"
        ]

        combined = base_skills + keywords[:5]

        return "\n".join([f"- {s}" for s in combined])


    def _build_experience(self, cv, answers):

        bullets = []

        if answers:
            sentences = answers.split(".")
            for s in sentences:
                s = s.strip()
                if len(s) > 20:
                    bullets.append(f"- {s}")

        if not bullets:
            bullets = [
                "- Delivered projects in complex environments",
                "- Coordinated stakeholders and teams",
                "- Managed risks and ensured delivery"
            ]

        return "\n".join(bullets[:6])


    def _build_delta(self, answers, keywords):

        changes = []

        if answers:
            changes.append("Incorporated user-provided experience and examples")

        if keywords:
            changes.append("Aligned CV with job description keywords")

        changes.append("Improved structure and readability")

        return "\n".join([f"- {c}" for c in changes])


    def _empty_response(self, message):
        return {
            "fit_score": 0,
            "match_summary": message,
            "recruiter_view": {"summary": "", "strengths": [], "concerns": []},
            "hiring_manager_view": {"summary": "", "strengths": [], "concerns": []},
            "strengths": [],
            "key_gaps": [],
            "recommended_roles": {"good_fit": []},
            "suggested_improvements": [],
            "questions": []
        }