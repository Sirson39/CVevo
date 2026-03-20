from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

def extract_keywords_from_jd(jd_text):
    """
    Identify key professional terms from JD.
    For simplicity, we split by common separators or use NLTK/spaCy.
    """
    # Assuming JD requirements are often comma-separated or list-like
    # We can also use simple frequency or TF-IDF on a set of common nouns/proper nouns
    keywords = re.findall(r'\b[A-Za-z+#.]{2,}\b', jd_text)
    # Filter common stopwords or short words
    stop_words = {'and', 'the', 'for', 'with', 'our', 'will', 'you', 'are', 'should', 'have'}
    important_keywords = [kw.lower() for kw in keywords if kw.lower() not in stop_words and len(kw) > 2]
    return list(set(important_keywords))

def calculate_ats_score(resume_parsed_data, jd_text):
    """
    Detailed scoring logic.
    """
    resume_text = resume_parsed_data.get("full_text", "").lower()
    jd_keywords = extract_keywords_from_jd(jd_text)
    
    if not jd_keywords:
        return 0, [], [], ["Job description content is insufficient for analysis."]
    
    matched_keywords = []
    missing_keywords = []

    for kw in jd_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', resume_text):
            matched_keywords.append(kw)
        else:
            missing_keywords.append(kw)
            
    # --- Scoring weights ---
    # 1. Keyword overlap (50%)
    keyword_score = (len(matched_keywords) / len(jd_keywords)) * 50 if jd_keywords else 0
    
    # 2. Section presence (20%)
    sections = resume_parsed_data.get("sections", {})
    section_score = 0
    if sections.get("experience"): section_score += 10
    if sections.get("education"): section_score += 5
    if sections.get("summary") or sections.get("projects"): section_score += 5
    
    # 3. Semantic Similarity (30%) - Optional advanced feature
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf = vectorizer.fit_transform([resume_text, jd_text])
        similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        semantic_score = similarity * 30
    except:
        semantic_score = 15  # Default if TF-IDF fails
        
    total_score = keyword_score + section_score + semantic_score
    total_score = min(100, round(total_score, 2))
    
    # --- Recommendations ---
    recommendations = []
    if missing_keywords:
        recommendations.append(f"Incorporate missing keywords: {', '.join(missing_keywords[:5])}.")
    if not sections.get("summary"):
        recommendations.append("Add a professional summary section to quickly highlight your value.")
    if not sections.get("experience"):
        recommendations.append("Ensure your work experience is clearly labeled and detailed.")
    if total_score < 70:
        recommendations.append("Tailor your skills and experience descriptions to more closely match the job description.")
    elif total_score > 85:
        recommendations.append("Great match! Ensure your contact information is up to date.")
        
    return total_score, matched_keywords, missing_keywords, recommendations
