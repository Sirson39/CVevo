import os
import re

template_dir = r"c:\Users\User\OneDrive - islingtoncollege.edu.np\Desktop\CVevo - Copy\frontend\partials\resume_templates"

def clean_template(content):
    # 1. Remove the "Notice" block if it exists
    content = re.sub(r'<div[^>]*border:[^>]*red;[^>]*>.*?</div>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Extract only the main content div if it exists (usually a container)
    # Most templates use a "container" or "wrap" class. 
    # But since they are all different, let's just strip the common garbage:
    
    # Remove <!DOCTYPE>, <html>, <head>, <body> tags if they wrap it
    content = re.sub(r'<!doctype.*?>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<html.*?>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</html>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<head>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<body.*?>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</body>', '', content, flags=re.IGNORECASE)
    
    # 3. Handle placeholders from previous "Stripping"
    # Convert <!-- Removed Var --> or [Removed Var] to something useful
    # This is hard because we don't know which field is which.
    # However, most templates follow a pattern:
    
    # First <h1> or <h2> is usually the name
    content = re.sub(r'(<h[12][^>]*>)(?:<!-- Removed Var -->|\[Removed Var\])', r'\1<span data-field="full_name"></span>', content)
    
    # Specific common patterns
    content = content.replace('email@example.com', '<span data-field="email"></span>')
    content = content.replace('+1 234 567 890', '<span data-field="phone"></span>')
    content = content.replace('City, Country', '<span data-field="location"></span>')
    
    # Remove the script tags that were added for solo-viewing
    content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    return content.strip()

for filename in os.listdir(template_dir):
    if filename.endswith(".html"):
        path = os.path.join(template_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cleaned = clean_template(content)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print(f"Cleaned {filename}")
