import os
import re
import pdfplumber
import docx

def clean_extracted_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\x00", "")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def _rewind_source(source):
    if hasattr(source, "seek"):
        try:
            source.seek(0)
        except Exception:
            pass
    return source

def extract_text_from_pdf(file_path) -> str:
    file_path = _rewind_source(file_path)
    text = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""
    return clean_extracted_text("\n".join(text))

def extract_text_from_docx(file_path) -> str:
    file_path = _rewind_source(file_path)
    try:
        doc = docx.Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return clean_extracted_text(text)
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
        return ""

def get_text_from_file(file_path) -> str:
    if not file_path:
        return ""

    if isinstance(file_path, (str, os.PathLike)):
        if not os.path.exists(file_path):
            return ""
        ext = os.path.splitext(file_path)[1].lower()
    else:
        ext = os.path.splitext(getattr(file_path, "name", ""))[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    if ext == ".docx":
        return extract_text_from_docx(file_path)
    return ""
