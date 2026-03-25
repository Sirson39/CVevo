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
    Extracts name, email and phone number using regex.
    """
    email = re.findall(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    
    # Simple name extraction: look at the first few lines
    lines = [L.strip() for L in text.split('\n') if L.strip()]
    name = ""
    if lines:
        # Usually the first non-empty line is the name
        # We skip lines that look like emails or phones
        for line in lines[:5]:
            if not re.search(r'@', line) and not re.search(r'\d{3}', line):
                name = line
                break

    return {
        "name": name,
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
            "Python", "Java", "C++", "C#", "PHP", "Ruby", "Swift", "Go", "Rust",
            "JavaScript", "React", "Angular", "Vue", "Node.js", "Express", "Next.js",
            "Django", "Flask", "Spring Boot", "Laravel", "Ruby on Rails",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle",
            "AWS", "Docker", "Kubernetes", "Azure", "GCP", "Terraform", "Jenkins",
            "Machine Learning", "Data Analysis", "Deep Learning", "Computer Vision",
            "HTML", "CSS", "Sass", "TypeScript", "Tailwind", "Bootstrap",
            "Git", "Agile", "Scrum", "Project Management", "Product Management",
            "NLP", "AI", "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn",
            "Tableau", "PowerBI", "SQL", "NoSQL", "REST API", "GraphQL", "Microservices",
            "Cybersecurity", "Blockchain", "Solidity", "Unit Testing", "DevOps"
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

def extract_role(text):
    """
    Identifies the likely current or target role of the candidate.
    """
    if not nlp: return "Unknown"
    
    doc = nlp(text)
    # Look for common role indicators or first non-entity lines
    # Often found near the top or after names
    lines = [L.strip() for L in text.split('\n') if L.strip()]
    
    # Common job titles candidates put near the top
    common_roles = ["Developer", "Engineer", "Manager", "Analyst", "Consultant", "Architect", "Designer", "Lead"]
    
    for line in lines[:10]:
        if any(role.lower() in line.lower() for role in common_roles):
            # Clean up the line for role extraction
            if len(line.split()) < 6: # Likely a title, not a sentence
                return line
                
    return "Not specified"

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
    role = extract_role(text)
    
    return {
        "contact": contact,
        "skills": skills,
        "sections": sections,
        "role": role,
        "full_text": text
    }