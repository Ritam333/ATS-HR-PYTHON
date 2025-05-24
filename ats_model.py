# ats_model.py
import re
import requests
import fitz
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime


model = SentenceTransformer('all-MiniLM-L6-v2')


# Qualification abbreviation to full-form mapping
QUALIFICATION_MAP = {
    "mca": ["master of computer application", "master in computer application", "m.c.a"],
    "btech": ["bachelor of technology", "b.tech", "bachelor in technology"],
    "bsc": ["bachelor of science", "b.sc"],
    "msc": ["master of science", "m.sc"],
    "mba": ["master of business administration"],
    "diploma": ["diploma"],
    "bcom": ["bachelor of commerce", "b.com"],
    "be": ["bachelor of engineering", "b.e"]
}













def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text





def normalize_qualification(text):
    text = text.lower()
    for abbr, full_forms in QUALIFICATION_MAP.items():
        for form in full_forms:
            if form in text:
                return abbr
    return None




def extract_text_from_pdf_url(url: str) -> str:
    try:
        with fitz.open(stream=requests.get(url).content, filetype="pdf") as doc:
            return "".join(page.get_text() for page in doc)
    except:
        return ""

def extract_skills(text, skill_list):
    text = text.lower()
    return {skill for skill in skill_list if skill.lower() in text}







def parse_date(date_str):
    date_str = date_str.strip().lower().replace(',', '')
    
    # Define a set of possible date formats to try
    formats = [
        "%B %d %Y",    # e.g., "February 3 2025", "March 15 2023"
        "%b %d %Y",    # e.g., "Feb 3 2025", "Mar 15 2023"
        "%B. %d %Y",   # e.g., "Feb. 3 2025" (with dot after abbreviation)
        "%b. %d %Y",   # e.g., "Mar. 15 2023"

        "%B %Y",       # e.g., "February 2025", "March 2023"
        "%b %Y",       # e.g., "Feb 2025", "Mar 2023"
        "%b. %Y",      # e.g., "Feb. 2025", "Mar. 2023" (with dot after abbreviation)

        "%m/%Y",       # e.g., "02/2025", "3/2023"
        "%Y-%m",       # e.g., "2025-02", "2023-03"
        "%m-%Y",       # e.g., "02-2025", "03-2023"
        
        "%Y"           # e.g., "2025"
    ]
    
    # For date strings that only contain month and year, we'll assume the 1st day of the month
    # This helps in consistent date object creation for calculations
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            # If parsing fails, try adding a default day (1) for month-year formats
            if "%B %Y" in fmt or "%b %Y" in fmt or "%b. %Y" in fmt:
                try:
                    return datetime.strptime(f"1 {date_str}", f"%d {fmt}")
                except ValueError:
                    pass
            elif "%m/%Y" in fmt or "%Y-%m" in fmt or "%m-%Y" in fmt:
                try:
                    # For MM/YYYY, YYYY-MM, MM-YYYY, assume day 1
                    parts = re.split(r'[/-]', date_str)
                    if len(parts) == 2:
                        if len(parts[0]) == 4: # YYYY-MM
                            return datetime.strptime(f"{parts[0]}-{parts[1]}-01", "%Y-%m-%d")
                        else: # MM/YYYY or MM-YYYY
                            return datetime.strptime(f"{parts[0]}-{parts[1]}-01", "%m-%Y-%d")
                except ValueError:
                    pass
            elif fmt == "%Y":
                try:
                    return datetime.strptime(f"1 {date_str}", "%j %Y") # Day 1 of the year
                except ValueError:
                    pass
    return None

def extract_experience(text):
    text = text.lower()
    total_months = 0

    # Improved patterns to capture various date formats including 'present' and 'to'
    # Prioritize more specific patterns (with day) before less specific ones (month/year only)
    patterns = [
        # Pattern 1: Month Day, Year - Month Day, Year or Present
        r'([a-z]{3,9}\.? \d{1,2},? \d{4})\s*(?:-|–|to)\s*(present|[a-z]{3,9}\.? \d{1,2},? \d{4})',
        # Pattern 2: Month Year - Month Year or Present
        r'([a-z]{3,9}\.? \d{4})\s*(?:-|–|to)\s*(present|[a-z]{3,9}\.? \d{4})',
        # Pattern 3: MM/YYYY - MM/YYYY or Present
        r'(\d{1,2}/\d{4})\s*(?:-|–|to)\s*(present|\d{1,2}/\d{4})',
        # Pattern 4: YYYY-MM - YYYY-MM or Present (e.g., 2023-01 - 2024-12)
        r'(\d{4}-\d{2})\s*(?:-|–|to)\s*(present|\d{4}-\d{2})',
        # Pattern 5: YYYY - YYYY or Present
        r'(\d{4})\s*(?:-|–|to)\s*(present|\d{4})'
    ]

    matches = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, text))

    for start_str, end_str in matches:
        start_date = parse_date(start_str)
        
        # Handle "present" by setting end_date to today
        if "present" in end_str:
            end_date = datetime.today()
        else:
            end_date = parse_date(end_str)

        if not start_date or not end_date:
            continue

        # Ensure start_date is always before or equal to end_date
        if start_date > end_date:
            continue # Skip invalid ranges

        # Calculate the total number of months
        # Add 1 to include the current month in the calculation
        # This handles cases like Feb 3, 2025 - Feb 28, 2025 being 1 month
        months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
        
        total_months += months_diff

    years = total_months // 12
    months = total_months % 12
    
    # Adjust if months_diff is 0, but it spans across a partial month.
    # For example, if it's "Feb 28, 2025 - Mar 3, 2025", the above will give 1 month.
    # If the experience is less than a month but present, it should still show 1 month.
    if total_months == 0 and matches and "present" in text:
        total_months = 1 # At least 1 month if "present" is there and no full month is calculated yet.


    return years + months / 12, f"{years} year(s), {months} month(s)"



def education_match(resume_text, required_qualifications):
    resume_text = resume_text.lower()
    resume_qualifications = set()

    for line in resume_text.splitlines():
        normalized = normalize_qualification(line)
        if normalized:
            resume_qualifications.add(normalized)

    required_abbr = {q.lower() for q in required_qualifications}
    return bool(resume_qualifications.intersection(required_abbr))


def check_location(text, locations):
    text = text.lower()
    return any(loc.lower() in text for loc in locations)

def calculate_ats_score(resume_text, jd_text, skills, exp, edu_keywords, locations):
    resume_embedding = model.encode(resume_text)
    jd_embedding = model.encode(jd_text)
    cosine_score = cosine_similarity([resume_embedding], [jd_embedding])[0][0]

    matched_skills = extract_skills(resume_text, skills)
    skill_score = len(matched_skills) / len(skills) if skills else 0

    resume_exp_num, resume_exp_str = extract_experience(resume_text)
    exp_score = min(resume_exp_num / exp, 1) if exp else 0

    edu_score = education_match(resume_text, edu_keywords)
    loc_score = check_location(resume_text, locations)

    final_score = (cosine_score * 0.5 + skill_score * 0.2 + exp_score * 0.1 + edu_score * 0.1 + loc_score * 0.1) * 100

    return round(final_score, 2), {
        "cosine_similarity": round(cosine_score, 2),
        "skills_matched": list(matched_skills),
        "experience_years": resume_exp_str,

        "education_matched": bool(edu_score),
        "location_matched": bool(loc_score)
    }
