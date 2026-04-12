import os
import re

template_dir = r"c:\Users\User\OneDrive - islingtoncollege.edu.np\Desktop\CVevo - Copy\frontend\partials\resume_templates"

def clean_template_v2(content):
    # Preserve <style> tags
    styles = re.findall(r'<style.*?>.*?</style>', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove Garbage
    content = re.sub(r'<!doctype.*?>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<html.*?>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</html>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<head>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<body.*?>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</body>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<div[^>]*border:[^>]*red;[^>]*>.*?</div>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # Convert common IDs to data-fields
    replacements = {
        'id="pName"': 'data-field="full_name"',
        'id="pEmail"': 'data-field="email"',
        'id="pPhone"': 'data-field="phone"',
        'id="pLocation"': 'data-field="location"',
        'id="pSummary"': 'data-field="summary"',
        'id="pTitle"': 'data-field="position"',
        'id="pExperience"': 'data-list="experiences"',
        'id="pSkills"': 'data-list="skills"',
        'id="pEducation"': 'data-list="educations"',
        'id="pCertificates"': 'data-list="certificates"',
        'id="pProjects"': 'data-list="projects"',
    }

    for old, new in replacements.items():
        content = content.replace(old, new)

    # Handle List Items (add data-tpl to the first child)
    # This is a bit tricky, but let's try to tag the first div inside a data-list
    content = re.sub(r'(data-list="experiences"[^>]*>\s*<div)', r'\1 data-tpl', content)
    content = re.sub(r'(data-list="skills"[^>]*>\s*<span)', r'\1 data-tpl', content)
    content = re.sub(r'(data-list="skills"[^>]*>\s*<li)', r'\1 data-tpl', content)
    content = re.sub(r'(data-list="educations"[^>]*>\s*<div)', r'\1 data-tpl', content)

    # Add back styles at the top
    final = "\n".join(styles) + "\n" + content
    return final.strip()

for filename in os.listdir(template_dir):
    if filename.endswith(".html"):
        path = os.path.join(template_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cleaned = clean_template_v2(content)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print(f"Refined {filename}")
