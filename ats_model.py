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
    print(f"DEBUG: parse_date received: '{date_str}'")
    date_str = date_str.strip().lower().replace(',', '')
    
    # Define a set of possible date formats to try
    formats = [
        "%B %d %Y",    # e.g., "february 3 2025"
        "%b %d %Y",    # e.g., "feb 3 2025"
        "%B. %d %Y",   # e.g., "feb. 3 2025"
        "%b. %d %Y",   # e.g., "feb. 3 2025"

        "%B %Y",       # e.g., "february 2025"
        "%b %Y",       # e.g., "feb 2025"
        "%b. %Y",      # e.g., "feb. 2025"

        "%m/%Y",       # e.g., "02/2025"
        "%Y-%m",       # e.g., "2025-02"
        "%m-%Y",       # e.g., "02-2025"
        
        "%Y"           # e.g., "2025"
    ]
    
    for fmt in formats:
        try:
            # If the format includes a day (%d), use it directly.
            # Otherwise, for month-year formats, append '01' to assume the first day.
            if '%d' not in fmt:
                # Handle cases where the date string might omit the day,
                # but the format string expects it (e.g., trying to parse "February 2025" with "%B %d %Y")
                # We need to ensure the format string matches the structure of date_str
                if ('%B %Y' in fmt or '%b %Y' in fmt) and re.match(r'^[a-z]{3,9}\.? \d{4}$', date_str):
                    parsed_date = datetime.strptime(f"01 {date_str}", f"%d {fmt}")
                    print(f"DEBUG: parse_date success with forced day: {parsed_date} using format '{fmt}'")
                    return parsed_date
                elif ('%m/%Y' in fmt or '%Y-%m' in fmt or '%m-%Y' in fmt) and re.match(r'^\d{2}[/-]\d{4}$|^\d{4}[/-]\d{2}$', date_str):
                     # For MM/YYYY, YYYY-MM, MM-YYYY, assume day 1
                    parts = re.split(r'[/-]', date_str)
                    if len(parts) == 2:
                        if len(parts[0]) == 4: # YYYY-MM
                            parsed_date = datetime.strptime(f"{parts[0]}-{parts[1]}-01", "%Y-%m-%d")
                            print(f"DEBUG: parse_date success with forced day: {parsed_date} using format '%Y-%m-%d'")
                            return parsed_date
                        else: # MM/YYYY or MM-YYYY
                            parsed_date = datetime.strptime(f"{parts[0]}-{parts[1]}-01", "%m-%Y-%d")
                            print(f"DEBUG: parse_date success with forced day: {parsed_date} using format '%m-%Y-%d'")
                            return parsed_date
                elif fmt == "%Y" and re.match(r'^\d{4}$', date_str):
                    parsed_date = datetime.strptime(f"{date_str}-01-01", "%Y-%m-%d") # Assume Jan 1st of the year
                    print(f"DEBUG: parse_date success for year only: {parsed_date} using format '%Y-%m-%d'")
                    return parsed_date
            else:
                parsed_date = datetime.strptime(date_str, fmt)
                print(f"DEBUG: parse_date success: {parsed_date} using format '{fmt}'")
                return parsed_date
        except ValueError:
            # print(f"DEBUG: parse_date failed for '{date_str}' with format '{fmt}'") # Can be too verbose
            continue
    print(f"DEBUG: parse_date FAILED to parse '{date_str}' with any format.")
    return None

def extract_experience(text):
    print(f"\nDEBUG: extract_experience received text (partial): '{text[:500]}...'")
    text = text.lower()
    total_months = 0

    # Improved patterns to capture various date formats including 'present' and 'to'
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
        found_matches = re.findall(pattern, text)
        if found_matches:
            print(f"DEBUG: Pattern '{pattern}' found matches: {found_matches}")
            matches.extend(found_matches)
    
    if not matches:
        print("DEBUG: No date range patterns matched in the text.")
        return 0, "0 year(s), 0 month(s)"

    for start_str, end_str in matches:
        print(f"\nDEBUG: Processing match: Start='{start_str}', End='{end_str}'")
        start_date = parse_date(start_str)
        
        # Handle "present" by setting end_date to today
        if "present" in end_str:
            end_date = datetime.today()
            print(f"DEBUG: End date (Present): {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            end_date = parse_date(end_str)
            print(f"DEBUG: End date (explicit): {end_date.strftime('%Y-%m-%d %H:%M:%S') if end_date else 'None'}")

        if not start_date or not end_date:
            print(f"DEBUG: Skipping due to parsing error for '{start_str}' or '{end_str}'.")
            continue

        # Crucial check: If start_date is in the future relative to end_date (e.g., today), skip or treat as 0 experience.
        # This means an experience listed as "Feb 2026 - Present" run today (May 2025) will be skipped.
        if start_date > end_date:
            print(f"DEBUG: Skipping: Start date {start_date} is after end date {end_date}. (Future experience)")
            continue 

        # Calculate the total number of months
        # Add 1 to include the current month in the calculation for partial months
        # For example, Feb 3 to May 24: Feb, Mar, Apr, May (4 months).
        # (5 - 2) = 3 months. Adding 1 makes it 4.
        months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        
        # If the start day is after the end day, subtract a month if it's not a full month span
        # This corrects for cases like 'Feb 28 - Mar 3' where it might incorrectly count 2 months if we just add 1
        # But for your case "Feb 3, 2025 - Present" (May 24, 2025), it should be fine.
        # A simple +1 to months_diff at the end is usually good for total experience.
        # Let's stick to the current logic where we add 1 month to include the current month.
        
        calculated_months_for_period = months_diff + 1
        print(f"DEBUG: Calculated months for period ('{start_str}' to '{end_str}'): {calculated_months_for_period} months ({(calculated_months_for_period-1)} diff + 1 current month)")
        total_months += calculated_months_for_period

    print(f"DEBUG: Final accumulated total_months: {total_months}")

    years = total_months // 12
    months = total_months % 12
    
    # This block is a fallback, but with the corrected month calculation above, it might not be strictly needed.
    # It ensures that if 'present' is matched but months calculate to 0 (e.g., very new entry in the *current* month), it still shows 1 month.
    if total_months == 0 and any("present" in end_str for _, end_str in matches):
        print("DEBUG: total_months was 0 but 'present' found, setting to 1 month.")
        total_months = 1
        years = 0
        months = 1

    return years + months / 12, f"{years} year(s), {months} month(s)"

# (Rest of your ats_model.py code remains the same)



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
