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

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO


def generate_report_pdf(evaluation):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    content = []

    # TITLE
    content.append(Paragraph("HiddenEdge – CV Assessment Report", styles['Title']))
    content.append(Spacer(1, 12))

    # DECISION
    content.append(Paragraph(
        f"<b>Decision:</b> {evaluation.get('decision')} ({evaluation.get('fit_score')}/10)",
        styles['Normal']
    ))
    content.append(Spacer(1, 12))

    # HEATMAP
    heat = evaluation.get("heatmap", {})
    content.append(Paragraph("<b>Scoring Breakdown</b>", styles['Heading2']))
    heat_items = [f"{k.capitalize()}: {v}%" for k, v in heat.items()]
    content.append(ListFlowable([Paragraph(x, styles['Normal']) for x in heat_items]))
    content.append(Spacer(1, 12))

    # DOMAIN
    content.append(Paragraph("<b>Domain Analysis</b>", styles['Heading2']))
    content.append(Paragraph(evaluation.get("domain_analysis", ""), styles['Normal']))
    content.append(Spacer(1, 12))

    # STRENGTHS
    content.append(Paragraph("<b>Strengths</b>", styles['Heading2']))
    strengths = evaluation.get("strengths", [])
    content.append(ListFlowable([Paragraph(x, styles['Normal']) for x in strengths]))
    content.append(Spacer(1, 12))

    # GAPS
    content.append(Paragraph("<b>Gaps</b>", styles['Heading2']))
    gaps = evaluation.get("gaps", [])
    content.append(ListFlowable([Paragraph(x, styles['Normal']) for x in gaps]))
    content.append(Spacer(1, 12))

    # RISKS
    content.append(Paragraph("<b>Risks</b>", styles['Heading2']))
    risks = evaluation.get("risk_flags", [])
    content.append(ListFlowable([Paragraph(x, styles['Normal']) for x in risks]))
    content.append(Spacer(1, 12))

    # CV DIFF
    content.append(Paragraph("<b>CV Improvements Applied</b>", styles['Heading2']))
    diff = evaluation.get("cv_diff", [])
    content.append(ListFlowable([Paragraph(x, styles['Normal']) for x in diff]))

    doc.build(content)

    buffer.seek(0)
    return buffer.getvalue()