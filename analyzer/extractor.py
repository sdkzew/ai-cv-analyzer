import pdfplumber
import docx
import re


def extract_text(filepath: str) -> str:
    if filepath.lower().endswith(".pdf"):
        return _extract_pdf(filepath)
    elif filepath.lower().endswith(".docx"):
        return _extract_docx(filepath)
    return ""


def _extract_pdf(filepath: str) -> str:
    text = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text.append(t)
    return "\n".join(text)


def _extract_docx(filepath: str) -> str:
    doc = docx.Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
