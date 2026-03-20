import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from ai_nlp.pipeline import process_resume_against_jd

def test_pipeline():
    # Create a dummy resume and JD for testing if they don't exist
    resume_path = "test_resume.docx"
    jd_text = """
    We are looking for a Python Developer with experience in Django, React, and AWS.
    Knowledge of SQL and Git is mandatory.
    """
    
    # In a real test, we'd have a file here. 
    # For now, let's just see if we can import everything.
    print("Testing AI/NLP Pipeline installation and imports...")
    try:
        import spacy
        import pdfplumber
        import docx
        import sklearn
        print("Required libraries are installed.")
    except ImportError as e:
        print(f"Error: Missing library - {e}")
        return

    # Check if spaCy model is loaded
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("spaCy model 'en_core_web_sm' is available.")
    except Exception as e:
        print(f"Warning: spaCy model not found - {e}")

    print("Pipeline ready for execution.")

if __name__ == "__main__":
    test_pipeline()
