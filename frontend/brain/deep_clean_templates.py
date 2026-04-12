import os
import re

template_dir = r"c:\Users\User\OneDrive - islingtoncollege.edu.np\Desktop\CVevo - Copy\frontend\partials\resume_templates"

def deep_clean_template(filename, content):
    # Regex to find the main container (t1-container, t2-container, etc.)
    # The pattern is usually class="t[Number]-container" or class="t[Number]-wrap"
    match = re.search(r'<(div|section)[^>]*class="(t\d+-|resume-)[^"]*container[^"]*"[^>]*>', content, re.IGNORECASE)
    
    # If we find the starting container
    if match:
        start_idx = match.start()
        # Find the matching closing div for this specific container
        # This is hard with regex, so we'll use a simple counter
        level = 0
        end_idx = -1
        for i in range(start_idx, len(content)):
            if content[i:i+4] == "<div" or content[i:i+8] == "<section":
                level += 1
            if content[i:i+5] == "</div" or content[i:i+9] == "</section":
                level -= 1
                if level == 0:
                    # Found the end!
                    # Find the closing '>'
                    close_tag_end = content.find('>', i)
                    end_idx = close_tag_end + 1
                    break
        
        if end_idx != -1:
            resume_html = content[start_idx:end_idx]
            
            # Preserve Styles
            styles = re.findall(r'<style.*?>.*?</style>', content, flags=re.DOTALL | re.IGNORECASE)
            
            # Standardization: Convert IDs to data-fields
            resume_html = resume_html.replace('id="pName"', 'data-field="full_name"')
            resume_html = resume_html.replace('id="pEmail"', 'data-field="email"')
            resume_html = resume_html.replace('id="pPhone"', 'data-field="phone"')
            resume_html = resume_html.replace('id="pLocation"', 'data-field="location"')
            resume_html = resume_html.replace('id="pSummary"', 'data-field="summary"')
            resume_html = resume_html.replace('id="pTitle"', 'data-field="position"')
            
            # List mapping
            resume_html = resume_html.replace('id="pExperience"', 'data-list="experiences"')
            resume_html = resume_html.replace('id="pSkills"', 'data-list="skills"')
            resume_html = resume_html.replace('id="pEducation"', 'data-list="educations"')
            
            # Clean up residual Django tags or messy spans
            resume_html = re.sub(r'<!-- Removed Var -->|\[Removed Var\]', '', resume_html)
            
            return "\n".join(styles) + "\n" + resume_html
            
    return content # Fallback if no container found

for filename in os.listdir(template_dir):
    if filename.endswith(".html"):
        path = os.path.join(template_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cleaned = deep_clean_template(filename, content)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print(f"Deep Cleaned {filename}")
