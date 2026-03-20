import spacy
from spacy.matcher import PhraseMatcher
import re

# Load spaCy model
# Note: Ensure 'en_core_web_sm' is downloaded
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # This will be handled after installation
    nlp = None

def extract_contact_info(text):
    """
    Extracts email and phone number using regex.
    """
    email = re.findall(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    return {
        "email": email[0] if email else "",
        "phone": phone[0] if phone else ""
    }

def extract_skills(text, skills_list=None):
    """
    Extracts skills using PhraseMatcher or simple keyword matching.
    """
    if not nlp: return []
    
    if not skills_list:
        # Default common skills for a tech project
        skills_list = [
            "Python", "Java", "C++", "JavaScript", "React", "Angular", "Vue", "Node.js",
            "Django", "Flask", "PostgreSQL", "MySQL", "MongoDB", "AWS", "Docker", "Kubernetes",
            "Machine Learning", "Data Analysis", "HTML", "CSS", "TypeScript", "Git", "Agile",
            "Project Management", "NLP", "AI", "TensorFlow", "PyTorch", "Pandas", "NumPy"
        ]
    
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in skills_list]
    matcher.add("SKILLS", patterns)
    
    doc = nlp(text)
    matches = matcher(doc)
    
    extracted_skills = set()
    for match_id, start, end in matches:
        span = doc[start:end]
        extracted_skills.add(span.text)
    
    return list(extracted_skills)

def extract_sections(text):
    """
    Identify sections like Experience, Education using common headers.
    """
    sections = {
        "experience": "",
        "education": "",
        "projects": "",
        "summary": ""
    }
    
    # Simple header detection
    headers = {
        "experience": [r'experience', r'work history', r'employment', r'professional background'],
        "education": [r'education', r'academic', r'qualification'],
        "projects": [r'projects', r'personal projects', r'academic projects'],
        "summary": [r'summary', r'objective', r'profile']
    }
    
    lines = text.split('\n')
    current_section = None
    
    for line in lines:
        clean_line = line.strip().lower()
        found_header = False
        for section, patterns in headers.items():
            for pattern in patterns:
                if re.match(r'^' + pattern + r'[:\s]*$', clean_line):
                    current_section = section
                    found_header = True
                    break
            if found_header: break
        
        if not found_header and current_section:
            sections[current_section] += line + "\n"
            
    return {k: v.strip() for k, v in sections.items()}

def parse_resume(text):
    """
    Main parsing function.
    """
    contact = extract_contact_info(text)
    skills = extract_skills(text)
    sections = extract_sections(text)
    
    return {
        "contact": contact,
        "skills": skills,
        "sections": sections,
        "full_text": text
    }
