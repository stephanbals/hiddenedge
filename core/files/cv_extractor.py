from docx import Document


# =========================================
# CV EXTRACTION
# =========================================

def extract_cv_text(file):

    if not file:
        return ""

    filename = file.filename.lower()

    allowed_extensions = (
        ".pdf",
        ".docx",
        ".txt"
    )

    if not filename.endswith(allowed_extensions):

        raise ValueError(
            "Unsupported file format. "
            "Please upload a PDF, DOCX, or TXT file."
        )

    try:

        if filename.endswith(".docx"):

            doc = Document(file)

            text = "\n".join([
                p.text for p in doc.paragraphs
            ])

            return text.strip()

        elif filename.endswith(".pdf"):

            try:

                from pypdf import PdfReader

                reader = PdfReader(file)

                text = ""

                for page in reader.pages:

                    extracted = page.extract_text()

                    if extracted:
                        text += extracted + "\n"

                return text.strip()

            except Exception as pdf_error:

                print(
                    "PDF PARSE ERROR:",
                    pdf_error
                )

                raise ValueError(
                    "Unable to read PDF file."
                )

        elif filename.endswith(".txt"):

            return file.read().decode(
                "utf-8",
                errors="ignore"
            ).strip()

        else:

            raise ValueError(
                "Unsupported file format."
            )

    except ValueError:
        raise

    except Exception as e:

        print("CV PARSE ERROR:", e)

        raise ValueError(
            "Failed to process uploaded file."
        )