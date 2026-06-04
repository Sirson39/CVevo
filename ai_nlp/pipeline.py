from .extractor import get_text_from_file
from .parser import parse_resume
from .analyzer import calculate_ats_score

def process_resume_against_jd(resume_file_path, jd_text):
    text = get_text_from_file(resume_file_path)
    if not text:
        return None, "Failed to extract text from the resume file."

    parsed_data = parse_resume(text)
    result = calculate_ats_score(parsed_data, jd_text)

    return {
        "ats_score": result["ats_score"],
        "quality_score": result["quality_score"],
        "final_score": result["final_score"],
        "match_level": result["match_level"],
        "matched_keywords": result["matched_keywords"],
        "matched_skills": result["matched_skills"],
        "missing_keywords": result["missing_skills"],
        "missing_critical_skills": result["missing_critical_skills"],
        "pillars": result["pillars"],
        "feedback": result["feedback"],
        "suggestions": result["suggestions"],
        "quality_issues": result["quality_issues"],
        "extracted_data": {
            "skills": parsed_data.get("skills", []),
            "sections": parsed_data.get("sections", {}),
            "contact": parsed_data.get("contact", {}),
            "full_text": parsed_data.get("full_text", "")
        }
    }, None