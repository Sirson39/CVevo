import fitz  # PyMuPDF

def extract_text_from_resume(path):
    text = ""
    if path.lower().endswith('.pdf'):
        doc = fitz.open(path)
        for page in doc:
            text += page.get_text()
    else:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    return text.lower()

def match_resume_to_job(resume_path, job_text):
    resume_text = extract_text_from_resume(resume_path)

    job_keywords = set(job_text.split())
    resume_words = set(resume_text.split())

    matched = list(job_keywords.intersection(resume_words))
    missing = list(job_keywords.difference(resume_words))

    match_score = int((len(matched) / max(len(job_keywords), 1)) * 100)

    return match_score, matched[:10], missing[:10]
