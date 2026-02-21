import re
from pdfminer.high_level import extract_text as extract_pdf_text
import docx

def extract_text_from_pdf(file_path):
    try:
        return extract_pdf_text(file_path)
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def extract_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
        return ""

def parse_resume_text(text):
    """
    Basic rule-based parsing using regex to identify common resume sections.
    """
    sections = {
        "skills": "",
        "experience": "",
        "education": "",
    }

    # Normalize text
    text_clean = re.sub(r'\s+', ' ', text)
    
    # Try to find Skills
    skills_match = re.search(r'(?i)(skills|technologies|expertise)(.*?)(experience|education|projects|summary|$)', text_clean)
    if skills_match:
        sections["skills"] = skills_match.group(2).strip()

    # Try to find Experience
    exp_match = re.search(r'(?i)(experience|work history|employment)(.*?)(education|skills|projects|summary|$)', text_clean)
    if exp_match:
        sections["experience"] = exp_match.group(2).strip()

    # Try to find Education
    edu_match = re.search(r'(?i)(education|academic)(.*?)(experience|skills|projects|summary|$)', text_clean)
    if edu_match:
        sections["education"] = edu_match.group(2).strip()

    return sections

def calculate_ats_score(resume_text, job_requirements):
    """
    Compares resume text against job requirements.
    requirements usually comma-separated keywords.
    """
    if not job_requirements:
        return 0, [], [], "No requirements provided for comparison."

    req_keywords = [k.strip().lower() for k in job_requirements.split(',') if k.strip()]
    resume_text_lower = resume_text.lower()

    matched = []
    missing = []

    for kw in req_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', resume_text_lower):
            matched.append(kw)
        else:
            missing.append(kw)

    score = 0
    if req_keywords:
        score = (len(matched) / len(req_keywords)) * 100

    feedback = f"Matched {len(matched)} out of {len(req_keywords)} specific requirements."
    if missing:
        feedback += f" Consider adding skills like: {', '.join(missing[:3])}."
    else:
        feedback += " Excellent match with all requirements!"

    return round(score, 2), matched, missing, feedback
