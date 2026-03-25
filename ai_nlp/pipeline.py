from .extractor import get_text_from_file
from .parser import parse_resume
from .analyzer import calculate_ats_score

def process_resume_against_jd(resume_file_path, jd_text):
    """
    Main entry point for analyzing a resume against a job description.
    """
    # 1. Extract text
    text = get_text_from_file(resume_file_path)
    if not text:
        return None, "Failed to extract text from the resume file."
    
    # 2. Parse resume
    parsed_data = parse_resume(text)
    
    # 3. Analyze against JD
    score, matched, missing, recommendations = calculate_ats_score(parsed_data, jd_text)
    
    return {
        "score": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "recommendations": recommendations,
        "extracted_data": {
            "skills": parsed_data.get("skills", []),
            "sections": parsed_data.get("sections", {}),
            "contact": parsed_data.get("contact", {})
        }
    }, None