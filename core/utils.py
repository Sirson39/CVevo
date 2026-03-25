import re
from pdfminer.high_level import extract_text as extract_pdf_text
import docx
import os
from django.core.files.storage import FileSystemStorage

class OverwriteStorage(FileSystemStorage):
    """
    Custom storage to overwrite files with the same name.
    """
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            self.delete(name)
        return name

# Import new AI/NLP module
try:
    from ai_nlp.pipeline import process_resume_against_jd
    from ai_nlp.extractor import get_text_from_file, extract_text_from_pdf as new_extract_pdf, extract_text_from_docx as new_extract_docx
    from ai_nlp.parser import parse_resume
    from ai_nlp.analyzer import calculate_ats_score as new_ats_score
    AI_NLP_AVAILABLE = True
except ImportError:
    AI_NLP_AVAILABLE = False

def extract_text_from_pdf(file_path):
    if AI_NLP_AVAILABLE:
        return new_extract_pdf(file_path)
    try:
        return extract_pdf_text(file_path)
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def extract_text_from_docx(file_path):
    if AI_NLP_AVAILABLE:
        return new_extract_docx(file_path)
    try:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
        return ""

def parse_resume_text(text):
    """
    Enhanced parsing using the new AI/NLP module.
    """
    if AI_NLP_AVAILABLE:
        parsed = parse_resume(text)
        # Map to the format expected by views if different
        contact = parsed.get("contact", {})
        return {
            "name": contact.get("name", ""),
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
            "skills": ", ".join(parsed.get("skills", [])),
            "experience": parsed.get("sections", {}).get("experience", ""),
            "education": parsed.get("sections", {}).get("education", ""),
        }
    
    # Basic rule-based parsing as fallback
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
    Enhanced scoring using the new AI/NLP module.
    """
    if AI_NLP_AVAILABLE:
        parsed_data = parse_resume(resume_text)
        score, matched, missing, feedback = new_ats_score(parsed_data, job_requirements)
        return score, matched, missing, feedback

    # Basic logic as fallback
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