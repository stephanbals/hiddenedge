from docx import Document
import io

def generate_docx(text):

    doc = Document()

    for line in text.split("\n"):
        doc.add_paragraph(line)

    file_stream = io.BytesIO()
    doc.save(file_stream)

    file_stream.seek(0)

    return file_stream.read()