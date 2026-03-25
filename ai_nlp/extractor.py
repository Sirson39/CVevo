import pdfplumber
import docx
import os

def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF file using pdfplumber for better formatting retention.
    """
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting PDF with pdfplumber: {e}")
        # Fallback or return empty
    return text.strip()

def extract_text_from_docx(file_path):
    """
    Extracts text from a DOCX file using python-docx.
    """
    try:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs]).strip()
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
        return ""

def get_text_from_file(file_path):
    """
    Determines file type and extracts text accordingly.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    else:
        return ""