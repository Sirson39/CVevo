import re
import spacy
from spacy.matcher import PhraseMatcher

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None

SYNONYM_MAP = {
    "js": "javascript",
    "postgres": "postgresql",
    "restful api": "rest api",
    "restful": "rest api",
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "reactjs": "react",
    "nextjs": "next.js",
    "nodejs": "node.js",
    "mongodb": "mongo",
}

DEFAULT_SKILLS = [
    "Python", "Java", "C++", "C#", "PHP", "Ruby", "Swift", "Go", "Rust",
    "JavaScript", "TypeScript", "React", "Angular", "Vue", "Node.js", "Express", "Next.js",
    "Django", "Flask", "Spring Boot", "Laravel", "Ruby on Rails",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle",
    "AWS", "Docker", "Kubernetes", "Azure", "GCP", "Terraform", "Jenkins",
    "Machine Learning", "Data Analysis", "Deep Learning", "Computer Vision",
    "HTML", "CSS", "Sass", "Tailwind", "Bootstrap",
    "Git", "Agile", "Scrum", "Project Management", "Product Management",
    "NLP", "AI", "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn",
    "Tableau", "Power BI", "SQL", "NoSQL", "REST API", "GraphQL", "Microservices",
    "Cybersecurity", "Blockchain", "Solidity", "Unit Testing", "DevOps"
]

SECTION_PATTERNS = {
    "summary": [r"summary", r"objective", r"profile", r"about me", r"professional summary"],
    "experience": [r"experience", r"work experience", r"employment", r"work history", r"professional experience"],
    "education": [r"education", r"academic background", r"qualification", r"educational background"],
    "projects": [r"projects", r"personal projects", r"academic projects", r"key projects"],
    "certifications": [r"certifications", r"certificates", r"licenses", r"awards"],
    "skills": [r"skills", r"technical skills", r"core skills", r"expertise", r"competencies"],
}

def clean_and_normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^\w\s+#./-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    for old, new in SYNONYM_MAP.items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text)

    return text

def extract_contact_info(text: str) -> dict:
    email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
    phone_pattern = r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}"
    linkedin_pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\d-]+"
    github_pattern = r"(?:https?://)?(?:www\.)?github\.com/[\w\d-]+"

    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    linkedin = re.findall(linkedin_pattern, text, flags=re.I)
    github = re.findall(github_pattern, text, flags=re.I)

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    name = ""
    for line in lines[:6]:
        if "@" not in line and len(line.split()) <= 4 and not re.search(r"\d", line):
            name = line
            break

    return {
        "name": name,
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "links": {
            "linkedin": linkedin[0] if linkedin else "",
            "github": github[0] if github else "",
        },
    }

def extract_skills(text: str, skills_list=None) -> list:
    skills_list = skills_list or DEFAULT_SKILLS
    if not text:
        return []

    if nlp:
        matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        patterns = [nlp.make_doc(skill) for skill in skills_list]
        matcher.add("SKILLS", patterns)

        doc = nlp(text)
        matches = matcher(doc)
        found = {doc[start:end].text.strip() for _, start, end in matches}
        return sorted(found)

    normalized = text.lower()
    found = []
    for skill in skills_list:
        if re.search(rf"\b{re.escape(skill.lower())}\b", normalized):
            found.append(skill)
    return sorted(set(found))

def is_section_header(line: str) -> str | None:
    cleaned = re.sub(r"[^a-z ]", "", line.lower()).strip()
    for section, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if cleaned == pattern:
                return section
    return None

def extract_sections(text: str) -> dict:
    sections = {key: "" for key in SECTION_PATTERNS.keys()}
    lines = text.split("\n")
    current_section = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        header = is_section_header(stripped)
        if header:
            current_section = header
            continue

        if current_section:
            sections[current_section] += stripped + "\n"

    return {k: v.strip() for k, v in sections.items()}

def parse_resume(text: str) -> dict:
    contact = extract_contact_info(text)
    sections = extract_sections(text)
    full_skills = extract_skills(text)
    section_skills = extract_skills(sections.get("skills", "")) if sections.get("skills") else []
    found_skills = sorted(set(full_skills + section_skills))

    return {
        "contact": contact,
        "skills": found_skills,
        "sections": sections,
        "full_text": text,
        "normalized_text": clean_and_normalize_text(text),
    }