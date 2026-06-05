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

def _basic_clean_and_normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s+#./-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Import new AI/NLP module
try:
    from ai_nlp.pipeline import process_resume_against_jd
    from ai_nlp.extractor import get_text_from_file, extract_text_from_pdf as new_extract_pdf, extract_text_from_docx as new_extract_docx
    from ai_nlp.parser import parse_resume
    from ai_nlp.analyzer import calculate_ats_score as new_ats_score
    from ai_nlp.parser import clean_and_normalize_text
    AI_NLP_AVAILABLE = True
except ImportError:
    clean_and_normalize_text = _basic_clean_and_normalize_text
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
            "summary": parsed.get("sections", {}).get("summary", ""),
            "skills": ", ".join(parsed.get("skills", [])),
            "experience": parsed.get("sections", {}).get("experience", ""),
            "education": parsed.get("sections", {}).get("education", ""),
            "projects": parsed.get("sections", {}).get("projects", ""),
            "certifications": parsed.get("sections", {}).get("certifications", ""),
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

def calculate_ats_score(resume_text, job_requirements, **kwargs):
    """
    Enhanced scoring using the new AI/NLP module.
    """
    jd_fields = kwargs.get('jd_fields')
    if AI_NLP_AVAILABLE:
        parsed_data = parse_resume(resume_text)
        result = new_ats_score(parsed_data, jd_text=job_requirements, jd_fields=jd_fields)
        # Extract the fields expected by the caller as a tuple
        return {
            "ats_score": result.get("final_score", 0),
            "matched_keywords": result.get("matched_skills", []),
            "missing_skills": result.get("missing_skills", []),
            "feedback": result.get("feedback", ""),
            "pillars": result.get("pillars", {}),
            "suggestions": result.get("suggestions", [])
        }

    # Basic logic as fallback
    if not job_requirements:
        return {
            "ats_score": 0,
            "matched_keywords": [],
            "missing_skills": [],
            "feedback": "No requirements provided for comparison.",
            "pillars": {},
            "strengths": [],
            "weaknesses": [],
            "quality_issues": [],
            "suggestions": []
        }

    def _fallback_keyword_terms(text):
        terms = []
        generic_prefixes = (
            "and ", "or ", "with ", "to ", "for ", "of ", "in ", "on ",
            "the ", "a ", "an ", "we ", "you ", "our "
        )
        generic_verbs = {
            "develop", "developing", "developer", "build", "building", "create",
            "creating", "design", "designing", "manage", "managing", "implement",
            "implementing", "maintain", "maintaining", "support", "supporting"
        }
        for chunk in re.split(r"[,;\n•]+", text or ""):
            cleaned = re.sub(r"\s+", " ", chunk.lower()).strip()
            if not cleaned:
                continue
            for prefix in generic_prefixes:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
            cleaned = cleaned.strip(" .:-")
            if not cleaned:
                continue
            words = cleaned.split()
            if len(words) > 4 or len(cleaned) > 42:
                continue
            if words[0] in generic_verbs:
                continue
            if cleaned.startswith(("we ", "you ", "our ", "the ", "a ", "an ")) and len(words) > 2:
                continue
            if cleaned in {"responsibilities", "requirements", "experience", "skills"}:
                continue
            terms.append(cleaned)
        return terms

    req_keywords = _fallback_keyword_terms(job_requirements)
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

    # Build a structured breakdown so the frontend still renders properly
    resume_sections = {
        "summary": "",
        "experience": "",
        "education": "",
        "projects": "",
        "skills": "",
    }

    section_patterns = {
        "summary": r"(?is)(summary|objective|profile|about me|professional summary)(.*?)(experience|education|skills|projects|certifications|$)",
        "experience": r"(?is)(experience|work experience|employment|professional experience)(.*?)(education|skills|projects|summary|certifications|$)",
        "education": r"(?is)(education|academic background|qualifications|qualification)(.*?)(experience|skills|projects|summary|certifications|$)",
        "projects": r"(?is)(projects|project experience|personal projects|academic projects)(.*?)(experience|education|skills|summary|certifications|$)",
        "skills": r"(?is)(skills|technical skills|core skills|expertise|competencies)(.*?)(experience|education|projects|summary|certifications|$)",
    }
    for name, pattern in section_patterns.items():
        match = re.search(pattern, resume_text)
        if match:
            resume_sections[name] = clean_and_normalize_text(match.group(2))

    normalized_resume = clean_and_normalize_text(resume_text)
    normalized_jd = clean_and_normalize_text(job_requirements)
    resume_tokens = set(re.findall(r"\b[a-z0-9+#.]{2,}\b", normalized_resume))
    jd_tokens = set(re.findall(r"\b[a-z0-9+#.]{2,}\b", normalized_jd))
    token_overlap = resume_tokens.intersection(jd_tokens)
    semantic_score = min(10, round((len(token_overlap) / len(jd_tokens)) * 10, 2)) if jd_tokens else 5

    resume_has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', resume_text))
    resume_has_phone = bool(re.search(r'\+?\d[\d\s().-]{7,}\d', resume_text))
    resume_has_name = len((resume_text.splitlines()[0] if resume_text.splitlines() else "").split()) >= 2

    completeness_hits = sum([
        1 if resume_sections["summary"] else 0,
        1 if resume_sections["experience"] else 0,
        1 if resume_sections["education"] else 0,
        1 if resume_sections["skills"] else 0,
        1 if resume_has_email else 0,
    ])
    completeness_score = round((completeness_hits / 5) * 5, 2)

    # Quality score reused from the general scan logic for a stable fallback.
    try:
        file_size = len(resume_text.encode("utf-8"))
        file_ext = "txt"
        quality_result = calculate_general_score(resume_text, file_size, file_ext)
        quality_pillar_score = round((quality_result["quality_score"] / 100) * 10, 2)
        quality_issues = quality_result.get("issues_found", [])
        quality_suggestions = quality_result.get("recommendations", [])
    except Exception:
        quality_result = {"quality_score": 60, "issues_found": [], "recommendations": []}
        quality_pillar_score = 6
        quality_issues = []
        quality_suggestions = []

    core_skills_score = round(min(30, (len(matched) / len(req_keywords)) * 30), 2) if req_keywords else 20
    tools_score = round(min(10, (len(token_overlap) / len(jd_tokens)) * 10), 2) if jd_tokens else 8
    experience_score = 7 if resume_sections["experience"] else 0
    project_score = 4 if resume_sections["projects"] else 0
    education_score = 5 if resume_sections["education"] else 0

    final_score = round(min(
        100,
        core_skills_score +
        tools_score +
        experience_score +
        project_score +
        education_score +
        semantic_score +
        completeness_score +
        quality_pillar_score
    ), 2)

    if final_score >= 80:
        match_level = "Strong Fit"
    elif final_score >= 60:
        match_level = "Moderate Fit"
    else:
        match_level = "Low Fit"

    strengths = []
    if matched:
        strengths.append(f"Matches {len(matched)} job requirements.")
    if resume_sections["experience"]:
        strengths.append("Experience section is present.")
    if resume_has_email:
        strengths.append("Contact details are present.")
    if quality_result.get("quality_score", 0) >= 75:
        strengths.append("Resume quality is solid.")

    weaknesses = []
    if missing:
        weaknesses.append("Some job requirements are not covered in the resume.")
    if not resume_sections["skills"]:
        weaknesses.append("Skills section is missing or hard to detect.")
    if not resume_sections["projects"]:
        weaknesses.append("Projects section is missing or hard to detect.")
    if quality_result.get("quality_score", 0) < 60:
        weaknesses.append("Resume quality and completeness need improvement.")

    return {
        "ats_score": final_score,
        "quality_score": quality_result.get("quality_score", 0),
        "final_score": final_score,
        "match_level": match_level,
        "matched_keywords": matched,
        "missing_skills": missing,
        "feedback": feedback,
        "pillars": {
            "Core Skills": core_skills_score,
            "Tools & Frameworks": tools_score,
            "Experience Relevance": experience_score,
            "Project Relevance": project_score,
            "Education Match": education_score,
            "Semantic Similarity": semantic_score,
            "Resume Completeness": completeness_score,
            "Resume Quality": quality_pillar_score,
        },
        "suggestions": quality_suggestions or [],
        "strengths": strengths,
        "weaknesses": weaknesses,
        "quality_issues": quality_issues,
        "missing_critical_skills": missing[:5]
    }


def calculate_general_score(resume_text, file_size, extension):
    """
    Evaluates resume quality without a JOB DESCRIPTION.
    Point-based system (100 total).
    """
    import re
    
    text_lower = resume_text.lower()
    recommendations = []
    
    # Massive Technical & Professional Skill Library
    tech_library = [
        # Programming & Web
        "python", "java", "javascript", "react", "django", "nodejs", "git", "sql", "aws", "docker",
        "kubernetes", "html", "css", "mongodb", "postgresql", "rest api", "azure", "typescript",
        "angular", "vue", "php", "laravel", "c++", "c#", "flutter", "dart", "ruby", "rails", "go",
        "rust", "swift", "ios", "android", "kotlin", "spring", "flask", "webpack", "babel",
        # Data & AI
        "machine learning", "data science", "nlp", "tensorflow", "pytorch", "pandas", "numpy", 
        "tableau", "power bi", "big data", "hadoop", "spark", "r", "sas", "deep learning",
        # Cyber & DevOps
        "cybersecurity", "network", "security", "linux", "unix", "bash", "jenkins", "terraform",
        "ansible", "cloud", "firebase", "mysql", "sqlite", "oracle", "grafana", "prometheus",
        # Design & Soft Skills
        "figma", "ui", "ux", "adobe", "photoshop", "illustrator", "sketch", "management", 
        "leadership", "communication", "agile", "scrum", "devops", "marketing", "sales", 
        "finance", "accounting", "hr", "operations", "project management", "quality assurance",
        "testing", "automated testing", "selenium", "cypress", "api", "backend", "frontend",
        "fullstack", "mobile development", "seo", "content writing", "copywriting",
        # High-Value Buzzwords
        "problem solving", "critical thinking", "collaboration", "teamwork", "analytical",
        "deadline oriented", "results driven", "innovation", "creativity"
    ]
    
    found_keywords = []
    for skill in tech_library:
        if re.search(rf'\b{re.escape(skill)}\b', text_lower):
            found_keywords.append(skill.capitalize())
    
    # Identify popular missing ones if found count is low
    missing_keywords = []
    if len(found_keywords) < 8:
        for skill in tech_library:
            if skill.capitalize() not in found_keywords:
                missing_keywords.append(skill.capitalize())
                if len(missing_keywords) >= 8: break
    
    # -------------------------
    # 1. Contact Information (15 pts)
    # -------------------------
    contact_score = 0
    contact_details = []
    if re.search(r'[\w\.-]+@[\w\.-]+', resume_text):
        contact_score += 4
        contact_details.append("Email address found.")
    else:
        contact_details.append("Email address missing.")
    
    if re.search(r'\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b|\(\d{3}\)\s*\d{3}[-.\s]??\d{4}', resume_text):
        contact_score += 4
        contact_details.append("Phone number found.")
    else:
        contact_details.append("Phone number missing.")

    if re.search(r'\b[A-Z][a-z]+, [A-Z]{2}\b', resume_text) or "nepal" in text_lower:
        contact_score += 3
        contact_details.append("Location found.")
    else:
        contact_details.append("Location details unclear.")

    if len(resume_text.splitlines()[0].split()) >= 2:
        contact_score += 4
        contact_details.append("Full name detected.")
    else:
        contact_details.append("Name might be missing or poorly formatted.")

    # -------------------------
    # 2. Professional Summary (10 pts)
    # -------------------------
    summary_score = 0
    summary_details = []
    summary_match = re.search(r'(?i)(summary|objective|profile|about)(.*?)(experience|education|skills|$)', text_lower, re.S)
    if summary_match:
        summary_txt = summary_match.group(2).strip()
        words = len(summary_txt.split())
        if 30 <= words <= 150:
            summary_score = 10
            summary_details.append("Well-proportioned summary found.")
        else:
            summary_score = 5
            summary_details.append("Summary present but could be improved.")
    else:
        summary_details.append("No clear Summary or Objective section found.")
        recommendations.append("Add a 3-4 sentence professional summary at the top.")

    # -------------------------
    # 3. Section Completeness (20 pts)
    # -------------------------
    section_score = 0
    section_details = []
    core_sections = ["experience", "education", "skills", "projects"]
    for s in core_sections:
        if re.search(r'\b' + s + r'\b', text_lower):
            section_score += 5
            section_details.append(f"Found {s.capitalize()} section.")
        else:
            section_details.append(f"Missing {s.capitalize()} section.")
            recommendations.append(f"Ensure you have a dedicated '{s.capitalize()}' section.")

    # -------------------------
    # 4. Grammar & Spelling (15 pts)
    # -------------------------
    grammar_score = 15
    grammar_details = []
    try:
        import language_tool_python
        tool = language_tool_python.LanguageTool('en-US')
        matches = tool.check(resume_text[:2000])
        technical_names = ["django", "react", "sql", "aws", "docker", "kubernetes", "nepal", "islington"]
        real_matches = []
        for m in matches:
            if m.ruleId in ['UPPERCASE_SENTENCE_START', 'WHITESPACE_RULE']: continue
            w = resume_text[m.offset:m.offset+m.errorLength].lower()
            if w not in technical_names:
                real_matches.append(m)
        
        if len(real_matches) > 10:
            grammar_score -= 8
            grammar_details.append(f"Major grammatical issues ({len(real_matches)} found).")
            recommendations.append("Consider using a professional proofreading service.")
        elif len(real_matches) > 3:
            grammar_score -= 4
            grammar_details.append("Minor spelling or grammatical errors detected.")
        else:
            grammar_details.append("Grammar and spelling look consistent.")
        tool.close()
    except:
        grammar_details.append("Writing quality looks professional.")

    first_person = len(re.findall(r'\b(i|me|my|mine|we)\b', text_lower))
    if first_person > 5:
        grammar_score = max(5, grammar_score - 4)
        grammar_details.append("High usage of first-person pronouns.")
        recommendations.append("Use action-oriented language instead of first-person pronouns.")

    # -------------------------
    # 5. Formatting & Readability (15 pts)
    # -------------------------
    formatting_score = 10
    formatting_details = []
    try:
        import textstat
        flesch = textstat.flesch_reading_ease(resume_text)
        if flesch < 30:
            formatting_score -= 3
            formatting_details.append(f"Complex readability (Flesch Score: {flesch:.1f}).")
            recommendations.append("Simplify your writing for better automated processing.")
        else:
            formatting_details.append(f"Professional readability level (Flesch: {flesch:.1f}).")
    except:
        pass

    if re.search(r'[\u2022\u2023\u25E6\u2043\u2219•*-]', resume_text):
        formatting_score = min(15, formatting_score + 5)
        formatting_details.append("Effective use of bullet points.")
    else:
        formatting_details.append("Consider using bullet points for better structure.")
        recommendations.append("Use bullet points to break down your responsibilities.")

    # -------------------------
    # 6. Hyperlinks (5 pts)
    # -------------------------
    hyperlink_score = 0
    hyperlink_details = []
    links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', resume_text)
    pro_domains = ["linkedin.com", "github.com", "portfolio", "behance.net", "dribbble.com"]
    if any(any(d in l.lower() for d in pro_domains) for l in links):
        hyperlink_score = 5
        hyperlink_details.append("Professional links (LinkedIn/GitHub/Portfolio) found.")
    elif links:
        hyperlink_score = 2
        hyperlink_details.append("Basic links detected.")
    else:
        hyperlink_details.append("Missing professional links.")
        recommendations.append("Add a LinkedIn profile or portfolio link.")

    # -------------------------
    # 7. File Quality (10 pts)
    # -------------------------
    file_score = 0
    file_details = []
    if file_size < 3 * 1024 * 1024:
        file_score += 5
        file_details.append("File size is optimal (under 3MB).")
    if extension.lower() in ['pdf', 'docx']:
        file_score += 5
        file_details.append(f"Format: {extension.upper()}.")

    # -------------------------
    # 8. Content Quality (10 pts)
    # -------------------------
    content_score = 7
    content_details = []
    word_count = len(resume_text.split())
    if 400 <= word_count <= 1000:
        content_score = 10
        content_details.append("Strong content density.")
    elif word_count < 200:
        content_score = 3
        content_details.append("Content is too brief.")
        recommendations.append("Expand on your achievements and responsibilities.")

    # Final Compilation
    total_score = round(contact_score + summary_score + section_score + grammar_score + 
                        formatting_score + hyperlink_score + file_score + content_score)
    total_score = max(min(total_score, 100), 5)

    if total_score >= 90: label = "Excellent"
    elif total_score >= 75: label = "Good"
    elif total_score >= 60: label = "Fair"
    elif total_score >= 40: label = "Needs Improvement"
    else: label = "Poor"

    result = {
        "scan_type": "general_quality_scan",
        "quality_score": total_score,
        "quality_label": label,
        "summary": f"Your resume is rated as '{label}' ({total_score}/100). Focus on improving {('structure' if total_score < 70 else 'specific details')} for better results.",
        "breakdown": {
            "contact_information": { "score": contact_score, "max_score": 15, "details": contact_details },
            "professional_summary": { "score": summary_score, "max_score": 10, "details": summary_details },
            "section_completeness": { "score": section_score, "max_score": 20, "details": section_details },
            "grammar_spelling": { "score": grammar_score, "max_score": 15, "details": grammar_details },
            "formatting_readability": { "score": formatting_score, "max_score": 15, "details": formatting_details },
            "hyperlinks": { "score": hyperlink_score, "max_score": 5, "details": hyperlink_details },
            "file_quality": { "score": file_score, "max_score": 10, "details": file_details },
            "content_quality": { "score": content_score, "max_score": 10, "details": content_details }
        },
        "strengths": [d for d in contact_details + summary_details + section_details + formatting_details if "detected" in d.lower() or "found" in d.lower() or "optimal" in d.lower() or "effective" in d.lower() or "strong" in d.lower()],
        "issues_found": [d for d in contact_details + summary_details + section_details if "missing" in d.lower() or "unclear" in d.lower()],
        "recommendations": recommendations,
        "found_keywords": found_keywords,
        "missing_keywords": missing_keywords
    }

    return result
