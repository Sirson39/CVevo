import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ''
    for page in doc:
        text += page.get_text()
    return text.lower()

def analyze_resume(file_path):
    text = extract_text_from_pdf(file_path)

    score = 100
    issues = []

    expected_sections = ['experience', 'education', 'skills', 'contact', 'projects']

    for section in expected_sections:
        if section not in text:
            score -= 10
            issues.append(f"Missing section: {section.capitalize()}")

    if len(text) < 300:
        score -= 15
        issues.append("Resume content too short")

    return max(score, 0), issues
