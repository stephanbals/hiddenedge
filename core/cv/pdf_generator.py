from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


def generate_pdf(cv_text, filepath):

    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(filepath, pagesize=A4)

    elements = []

    for line in cv_text.split("\n"):
        if not line.strip():
            elements.append(Spacer(1, 8))
        else:
            elements.append(Paragraph(line, styles["Normal"]))

    doc.build(elements)