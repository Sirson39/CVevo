import re
from typing import Dict, List, Set
from sklearn.metrics.pairwise import cosine_similarity
from .parser import nlp, clean_and_normalize_text, extract_skills

try:
    from sentence_transformers import SentenceTransformer
    sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as e:
    print(f"Warning: Could not load sentence-transformers model: {e}")
    sbert_model = None


# -----------------------------
# Config / Constants
# -----------------------------

STOP_WORDS = {
    "experience", "team", "work", "skills", "responsibilities",
    "required", "preferred", "candidates", "environment", "description",
    "ability", "abilities", "knowledge", "role", "position", "job",
    "candidate", "year", "years", "strong", "good", "excellent",
    "understanding", "including", "must", "should", "using"
}

ACTION_VERBS = {
    "built", "developed", "created", "implemented", "designed",
    "led", "optimized", "improved", "managed", "delivered",
    "engineered", "deployed", "automated", "integrated", "maintained"
}

DEGREE_TERMS = {
    "bachelor", "master", "phd", "degree", "university", "college",
    "bsc", "msc", "bs", "ms"
}

CRITICAL_SKILL_HINTS = {
    "python", "java", "javascript", "react", "django", "flask",
    "spring boot", "node.js", "postgresql", "mysql", "mongodb",
    "docker", "kubernetes", "aws", "azure", "gcp", "sql",
    "machine learning", "data analysis", "rest api", "git"
}


# -----------------------------
# Helper Functions
# -----------------------------

def safe_divide(a: float, b: float) -> float:
    return a / b if b else 0.0


def normalize_list(values: List[str]) -> List[str]:
    seen = set()
    cleaned = []
    for value in values:
        if not value:
            continue
        norm = clean_and_normalize_text(value).strip()
        if norm and norm not in seen:
            seen.add(norm)
            cleaned.append(norm)
    return cleaned


def extract_years_of_experience(text: str) -> List[int]:
    """
    Extract numeric years from phrases like:
    '2 years', '3+ years', 'minimum 1 year'
    """
    if not text:
        return []

    patterns = [
        r'(\d+)\+?\s+years?',
        r'minimum\s+(\d+)\s+years?',
        r'at least\s+(\d+)\s+years?',
    ]

    years = []
    lowered = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, lowered)
        years.extend([int(m) for m in matches if str(m).isdigit()])

    return sorted(set(years))


def get_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity using sentence-transformers.
    Returns a value between 0.0 and 1.0 approximately.
    """
    if not sbert_model or not text1 or not text2:
        return 0.0

    try:
        embeddings = sbert_model.encode([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(max(0.0, min(1.0, similarity)))
    except Exception:
        return 0.0


# -----------------------------
# JD Parsing
# -----------------------------

def parse_job_description(jd_text: str) -> Dict:
    """
    Parse the job description into useful ATS components.
    """
    if not jd_text:
        return {
            "skills": [],
            "keywords": [],
            "critical_skills": [],
            "years_required": [],
            "degree_required": [],
            "full_text": "",
            "normalized_text": ""
        }

    normalized_jd = clean_and_normalize_text(jd_text)

    # Extract technical skills from parser skill list
    jd_skills = normalize_list(extract_skills(jd_text))

    # Extract general keywords
    keywords = set()
    if nlp:
        doc = nlp(jd_text)
        for token in doc:
            word = token.text.lower().strip()
            if (
                token.pos_ in ["NOUN", "PROPN"] and
                len(word) > 2 and
                word not in STOP_WORDS
            ):
                keywords.add(word)
    else:
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+.#-]{2,}\b', jd_text.lower())
        keywords = {w for w in words if w not in STOP_WORDS}

    # Critical skills = important technical items from JD
    critical_skills = []
    for skill in jd_skills:
        if skill in CRITICAL_SKILL_HINTS:
            critical_skills.append(skill)

    # fallback: first few JD skills if no critical skill found
    if not critical_skills:
        critical_skills = jd_skills[:5]

    years_required = extract_years_of_experience(jd_text)

    degree_required = []
    for term in DEGREE_TERMS:
        if re.search(rf'\b{re.escape(term)}\b', normalized_jd):
            degree_required.append(term)

    return {
        "skills": jd_skills,
        "keywords": sorted(keywords),
        "critical_skills": critical_skills,
        "years_required": years_required,
        "degree_required": sorted(set(degree_required)),
        "full_text": jd_text,
        "normalized_text": normalized_jd
    }


# -----------------------------
# Resume Quality Analysis
# -----------------------------

def detect_resume_quality(resume_data: Dict) -> Dict:
    """
    Score resume quality separately from ATS match score.
    """
    sections = resume_data.get("sections", {}) or {}
    contact = resume_data.get("contact", {}) or {}
    full_text = resume_data.get("full_text", "") or ""
    skills = resume_data.get("skills", []) or []

    score = 0
    issues = []
    suggestions = []

    # Contact completeness (20)
    if contact.get("email"):
        score += 8
    else:
        issues.append("Missing email address.")
        suggestions.append("Add a professional email address.")

    if contact.get("phone"):
        score += 6
    else:
        issues.append("Missing phone number.")
        suggestions.append("Add a phone number so recruiters can contact you.")

    if contact.get("links", {}).get("linkedin") or contact.get("links", {}).get("github"):
        score += 6
    else:
        issues.append("No professional profile links found.")
        suggestions.append("Add LinkedIn or GitHub if relevant to the role.")

    # Summary (10)
    summary = sections.get("summary", "")
    if summary:
        score += 10
        if len(summary.split()) < 20:
            issues.append("Professional summary is too short.")
            suggestions.append("Write a stronger summary tailored to the target role.")
    else:
        issues.append("Missing professional summary.")
        suggestions.append("Add a short professional summary.")

    # Experience (20)
    experience = sections.get("experience", "")
    if experience:
        score += 12

        exp_lower = experience.lower()
        if any(verb in exp_lower for verb in ACTION_VERBS):
            score += 4
        else:
            issues.append("Experience section lacks strong action verbs.")
            suggestions.append("Use verbs like developed, built, implemented, designed, optimized.")

        if re.search(r'\b\d+%|\b\d+\+? users|\b\d+\+? projects|\b\d+\+? clients|\b\d+\+? teams?', experience.lower()):
            score += 4
        else:
            issues.append("Experience section lacks measurable achievements.")
            suggestions.append("Add numbers and outcomes, such as percentages, project counts, or impact.")
    else:
        issues.append("Missing experience section.")
        suggestions.append("Add internships, jobs, freelance work, or volunteer experience.")

    # Projects (15)
    projects = sections.get("projects", "")
    if projects:
        score += 15
    else:
        issues.append("Missing projects section.")
        suggestions.append("Add personal, academic, or professional projects related to the role.")

    # Education (10)
    education = sections.get("education", "")
    if education:
        score += 10
    else:
        issues.append("Missing education section.")
        suggestions.append("Add your education details clearly.")

    # Skills (10)
    if skills:
        score += 10
        if len(skills) < 5:
            issues.append("Skills section is too limited.")
            suggestions.append("Add more relevant technical and role-specific skills.")
    else:
        issues.append("Missing skills section.")
        suggestions.append("Add a dedicated skills section.")

    # Content richness (15)
    word_count = len(full_text.split())
    if word_count >= 250:
        score += 15
    elif word_count >= 150:
        score += 10
    elif word_count >= 100:
        score += 5
    else:
        issues.append("Resume content is too short.")
        suggestions.append("Add more relevant achievements, projects, skills, and details.")

    return {
        "quality_score": min(100, round(score, 2)),
        "issues": issues,
        "suggestions": suggestions
    }


# -----------------------------
# ATS Score Calculation
# -----------------------------

def calculate_ats_score(resume_data: Dict, jd_text: str = "", jd_fields: Dict = None) -> Dict:
    """
    Main ATS scoring function. Honors structured JD fields if provided for higher precision.

    Returns:
    - ats_score, quality_score, final_score, match_level, pillars, matched_skills, etc.
    """
    # 1. Prepare JD Data (Structured fields override general text)
    if jd_fields:
        full_jd_text = "\n".join([
            jd_fields.get("title", ""),
            jd_fields.get("description", ""),
            jd_fields.get("required_skills", ""),
            jd_fields.get("experience_requirements", ""),
            jd_fields.get("education_requirements", ""),
            jd_fields.get("tools_and_technologies", ""),
            jd_fields.get("requirements", "")
        ])
        jd_data = parse_job_description(full_jd_text)
        
        # Override specific lists if HR provided them
        if jd_fields.get("required_skills"):
            jd_data["critical_skills"] = normalize_list(extract_skills(jd_fields["required_skills"]))
        if jd_fields.get("tools_and_technologies"):
            jd_data["skills"] = normalize_list(extract_skills(jd_fields["tools_and_technologies"])) + jd_data["critical_skills"]
        if jd_fields.get("requirements"):
            # Keywords from the specific "ATS scanning keywords" field
            kws = [k.strip().lower() for k in jd_fields["requirements"].split(',') if k.strip()]
            jd_data["keywords"] = normalize_list(kws)
    else:
        jd_data = parse_job_description(jd_text)
        full_jd_text = jd_text

    resume_text = resume_data.get("full_text", "") or ""
    resume_sections = resume_data.get("sections", {}) or {}
    resume_contact = resume_data.get("contact", {}) or {}

    resume_skills = set(normalize_list(resume_data.get("skills", [])))
    jd_skills = set(normalize_list(jd_data.get("skills", [])))
    jd_keywords = set(normalize_list(jd_data.get("keywords", [])))
    critical_skills = set(normalize_list(jd_data.get("critical_skills", [])))

    normalized_resume = clean_and_normalize_text(resume_text)
    normalized_experience = clean_and_normalize_text(resume_sections.get("experience", ""))
    normalized_projects = clean_and_normalize_text(resume_sections.get("projects", ""))
    normalized_education = clean_and_normalize_text(resume_sections.get("education", ""))
    summary_text = resume_sections.get("summary", "") or resume_text[:700]

    # 1. Core Skills Match (30)
    skill_overlap = resume_skills.intersection(jd_skills)
    core_skill_ratio = safe_divide(len(skill_overlap), len(jd_skills))
    core_skills_score = min(30, core_skill_ratio * 30) if jd_skills else 20

    # 2. Tools / Frameworks / JD Keywords (10)
    matched_keywords = []
    for kw in jd_keywords:
        if re.search(rf'\b{re.escape(kw)}\b', normalized_resume):
            matched_keywords.append(kw)

    keyword_ratio = safe_divide(len(matched_keywords), len(jd_keywords))
    tools_score = min(10, keyword_ratio * 10) if jd_keywords else 8

    # 3. Experience Relevance (20)
    exp_matches = []
    for kw in jd_keywords:
        if normalized_experience and re.search(rf'\b{re.escape(kw)}\b', normalized_experience):
            exp_matches.append(kw)

    exp_ratio = safe_divide(len(exp_matches), len(jd_keywords))
    if normalized_experience and jd_keywords:
        experience_score = min(15, exp_ratio * 15 * 1.25)
    elif normalized_experience:
        experience_score = 6
    else:
        experience_score = 0

    # 4. Project Relevance (10)
    proj_matches = []
    for kw in jd_keywords:
        if normalized_projects and re.search(rf'\b{re.escape(kw)}\b', normalized_projects):
            proj_matches.append(kw)

    proj_ratio = safe_divide(len(proj_matches), len(jd_keywords))
    if normalized_projects and jd_keywords:
        project_score = min(10, proj_ratio * 10 * 1.25)
    elif normalized_projects:
        project_score = 4
    else:
        project_score = 0

    # 5. Education Match (10)
    education_score = 0
    if normalized_education:
        education_score = 5

        degree_hits = 0
        for degree in jd_data.get("degree_required", []):
            if re.search(rf'\b{re.escape(degree)}\b', normalized_education):
                degree_hits += 1

        if jd_data.get("degree_required"):
            degree_ratio = safe_divide(degree_hits, len(jd_data["degree_required"]))
            education_score = max(5, min(10, degree_ratio * 10))
        else:
            if any(term in normalized_education for term in DEGREE_TERMS):
                education_score = 10

    # 6. Semantic Similarity (10)
    semantic_summary = get_semantic_similarity(summary_text, full_jd_text)
    semantic_experience = get_semantic_similarity(resume_sections.get("experience", ""), full_jd_text)
    semantic_projects = get_semantic_similarity(resume_sections.get("projects", ""), full_jd_text)

    semantic_score = (
        (semantic_summary * 0.40) +
        (semantic_experience * 0.40) +
        (semantic_projects * 0.20)
    ) * 10
    semantic_score = min(10, semantic_score)

    # 7. Resume Completeness (5)
    completeness = 0
    if resume_sections.get("summary"):
        completeness += 1
    if resume_sections.get("experience"):
        completeness += 1
    if resume_sections.get("education"):
        completeness += 1
    if resume_sections.get("skills"):
        completeness += 1
    if resume_contact.get("email"):
        completeness += 1

    completeness_score = (completeness / 5) * 5

    # 8. Resume Quality (10)
    quality_result = detect_resume_quality(resume_data)
    # Scale from 100 to 10 points
    quality_pillar_score = round((quality_result["quality_score"] / 100) * 10, 2)

    # ATS score total (Sum of all pillars = 100)
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
    
    # Backward compatibility
    ats_score = final_score
    quality_score = quality_result["quality_score"]

    # Missing skills
    missing_skills = sorted(jd_skills - resume_skills)
    missing_critical_skills = sorted(skill for skill in critical_skills if skill not in resume_skills)

    # Match level
    if final_score >= 80:
        match_level = "Strong Fit"
    elif final_score >= 60:
        match_level = "Moderate Fit"
    else:
        match_level = "Low Fit"

    # Feedback generation
    feedback_parts = []

    if skill_overlap:
        feedback_parts.append(
            f"Your resume matches important job skills such as {', '.join(sorted(skill_overlap)[:6])}."
        )

    if missing_critical_skills:
        feedback_parts.append(
            f"You are missing critical skills like {', '.join(missing_critical_skills[:5])}."
        )

    if not resume_sections.get("projects"):
        feedback_parts.append(
            "Adding a projects section could improve your relevance for technical roles."
        )

    if quality_result["issues"]:
        feedback_parts.append(
            "Key quality issues include: " + "; ".join(quality_result["issues"][:3])
        )

    if not feedback_parts:
        feedback_parts.append("Your resume is reasonably aligned with the job description.")

    # Main strengths
    strengths = []
    if core_skills_score >= 20:
        strengths.append("Good overlap with required technical skills.")
    if experience_score >= 12:
        strengths.append("Experience section is relevant to the job description.")
    if semantic_score >= 6:
        strengths.append("Resume content is semantically aligned with the role.")
    if quality_score >= 75:
        strengths.append("Resume structure and completeness are strong.")

    # Main weaknesses
    weaknesses = []
    if core_skills_score < 15:
        weaknesses.append("Low overlap with required technical skills.")
    if experience_score < 8:
        weaknesses.append("Experience section is not strongly aligned to the job.")
    if project_score < 4:
        weaknesses.append("Projects section is weak or missing.")
    if quality_score < 60:
        weaknesses.append("Resume quality and completeness need improvement.")

    return {
        "ats_score": ats_score,
        "quality_score": quality_score,
        "final_score": final_score,
        "match_level": match_level,
        "pillars": {
            "Core Skills": round(core_skills_score, 2),
            "Tools & Frameworks": round(tools_score, 2),
            "Experience Relevance": round(experience_score, 2),
            "Project Relevance": round(project_score, 2),
            "Education Match": round(education_score, 2),
            "Semantic Similarity": round(semantic_score, 2),
            "Resume Completeness": round(completeness_score, 2),
            "Resume Quality": round(quality_pillar_score, 2),
        },
        "matched_skills": sorted(skill_overlap),
        "missing_skills": missing_skills,
        "matched_keywords": sorted(set(matched_keywords)),
        "missing_critical_skills": missing_critical_skills,
        "quality_issues": quality_result["issues"],
        "suggestions": quality_result["suggestions"],
        "strengths": strengths,
        "weaknesses": weaknesses,
        "feedback": " ".join(feedback_parts)
    }