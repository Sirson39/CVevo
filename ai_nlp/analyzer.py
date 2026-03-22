from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

def extract_keywords_from_jd(jd_text):
    """
    Identify key professional terms from JD using NLP.
    Filters for Nouns and Proper Nouns to find skills and technologies.
    """
    from .parser import nlp
    if not nlp:
        # Fallback to regex if spacy not loaded
        return list(set(re.findall(r'\b[A-Za-z+#.]{2,}\b', jd_text.lower())))
    
    doc = nlp(jd_text)
    keywords = set()
    
    # Filter for Nouns, Proper Nouns, and multi-word tech terms
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 1:
            keywords.add(token.text.lower())
            
    # Remove common filler words that might be tagged as nouns
    stop_words = {'and', 'the', 'for', 'with', 'our', 'will', 'you', 'are', 'should', 'have', 'experience', 'team', 'work', 'skills'}
    important_keywords = [kw for kw in keywords if kw not in stop_words]
    
    return important_keywords

def calculate_ats_score(resume_parsed_data, jd_text):
    """
    Strong ATS Scoring Formula:
    1. Keyword Match Score = 35%
    2. Skills Match Score = 25%
    3. Experience Relevance Score = 20%
    4. Education / Qualification Score = 10%
    5. Resume Structure / ATS Readability Score = 10%
    """
    resume_text = resume_parsed_data.get("full_text", "").lower()
    jd_keywords = extract_keywords_from_jd(jd_text)
    
    if not jd_keywords:
        return 0, [], [], "Job description content is insufficient for analysis."
    
    # 1. Keyword Match (35%)
    # --- Exact vs Partial Matching ---
    strong_matches = []
    partial_matches = []
    missing_critical = []
    
    # Simple heuristic for critical vs preferred: 
    # Words like "required", "must", "essential" in the sentence containing the keyword?
    # For now, let's treat all JD extracted keywords as important.
    for kw in jd_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', resume_text):
            strong_matches.append(kw)
        else:
            # Check for partial matches (substring)
            if any(kw in word for word in resume_text.split()):
                partial_matches.append(kw)
            else:
                missing_critical.append(kw)
                
    keyword_score_raw = (len(strong_matches) + (0.5 * len(partial_matches))) / len(jd_keywords)
    keyword_pillar = keyword_score_raw * 35
    
    # 2. Skills Match (25%)
    # Use the skills identified by the parser
    extracted_skills = [s.lower() for s in resume_parsed_data.get("skills", [])]
    # How many of the JD keywords are in the 'skills' list specifically?
    jd_skills_in_resume = [kw for kw in jd_keywords if kw in extracted_skills]
    skills_score_raw = (len(jd_skills_in_resume) / len(jd_keywords)) if jd_keywords else 0
    skills_pillar = min(25, skills_score_raw * 25 * 1.5) # Bonus for appearing in skills section
    
    # 3. Experience Relevance (20%)
    experience_text = resume_parsed_data.get("sections", {}).get("experience", "").lower()
    # Check if keyword density is higher in experience section
    exp_matches = [kw for kw in jd_keywords if re.search(r'\b' + re.escape(kw) + r'\b', experience_text)]
    exp_relevance_raw = (len(exp_matches) / len(jd_keywords)) if jd_keywords else 0
    experience_pillar = exp_relevance_raw * 20
    
    # 4. Education / Qualification (10%)
    education_text = resume_parsed_data.get("sections", {}).get("education", "").lower()
    education_pillar = 0
    if education_text:
        education_pillar = 10
        # Boost if degree keywords found
        if any(deg in education_text for deg in ["bachelor", "master", "phd", "degree", "university", "college"]):
            education_pillar = 10
        else:
            education_pillar = 5
            
    # 5. ATS Readability (10%)
    sections = resume_parsed_data.get("sections", {})
    readability_notes = []
    readability_score = 0
    
    if sections.get("experience"): readability_score += 3
    else: readability_notes.append("Experience section header not clearly identified.")
    
    if sections.get("education"): readability_score += 3
    else: readability_notes.append("Education section header not clearly identified.")
    
    if sections.get("skills"): readability_score += 2
    else: readability_notes.append("Skills section header not clearly identified.")
    
    if len(resume_text.split()) > 200: readability_score += 2 # Length check
    else: readability_notes.append("Resume might be too short for detailed ATS analysis.")
    
    readability_pillar = min(10, readability_score)
    if not readability_notes: readability_notes.append("Resume structure follows standard ATS conventions.")

    # Final Score Calculation
    final_score = keyword_pillar + skills_pillar + experience_pillar + education_pillar + readability_pillar
    final_score = min(100, round(final_score, 2))
    
    # Match Level
    if final_score >= 80: match_level = "Strong"
    elif final_score >= 50: match_level = "Moderate"
    else: match_level = "Weak"
    
    # Improvement Suggestions
    suggestions = []
    if missing_critical:
        suggestions.append(f"Add missing critical keywords: {', '.join(missing_critical[:3])}")
    if education_pillar < 10:
        suggestions.append("Clarify your degree and institution in the education section.")
    if readability_pillar < 8:
        suggestions.append("Use clearer section headings (e.g., 'Work Experience' instead of 'What I've Done').")

    # Format Concise Report
    matched_count = len(strong_matches) + len(partial_matches)
    total_count = len(jd_keywords)
    feedback_report = f"Matched {matched_count} out of {total_count} specific requirements. "
    if missing_critical:
        feedback_report += f"Consider adding skills like: {', '.join(missing_critical[:3])}."
    else:
        feedback_report += "Great job! Your resume aligns well with the job requirements."

    return final_score, strong_matches, missing_critical, feedback_report
