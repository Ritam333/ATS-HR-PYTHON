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
    # Try multiple date formats
    formats = [
        "%B %d %Y",    # February 3 2025
        "%b %d %Y",    # Feb 3 2025
        "%B %Y",       # February 2025
        "%b %Y",       # Feb 2025
        "%m/%Y",       # 02/2025
        "%Y-%m",       # 2025-02
        "%m-%Y",       # 02-2025
        "%Y"           # 2025
    ]
    for fmt in formats:
        try:
            if '%d' not in fmt:
                # add day=1 for month/year or year-only formats
                if fmt in ("%B %Y", "%b %Y"):
                    return datetime.strptime("01 " + date_str, "%d " + fmt)
                elif fmt in ("%m/%Y", "%Y-%m", "%m-%Y"):
                    parts = re.split(r'[/-]', date_str)
                    if len(parts) == 2:
                        # Normalize format to YYYY-MM-DD or MM-YYYY-DD accordingly
                        if len(parts[0]) == 4:
                            return datetime.strptime(f"{parts[0]}-{parts[1]}-01", "%Y-%m-%d")
                        else:
                            return datetime.strptime(f"{parts[0]}-{parts[1]}-01", "%m-%Y-%d")
                elif fmt == "%Y" and re.match(r'^\d{4}$', date_str):
                    return datetime.strptime(f"{date_str}-01-01", "%Y-%m-%d")
            else:
                return datetime.strptime(date_str, fmt)
        except:
            continue
    return None

def extract_experience(text):
    text = text.lower()
    total_months = 0

    patterns = [
        # Month day, year - Month day, year or Present
        r'([a-z]{3,9}\.? \d{1,2},? \d{4})\s*(?:-|–|to)\s*(present|[a-z]{3,9}\.? \d{1,2},? \d{4})',
        # Month year - Month year or Present
        r'([a-z]{3,9}\.? \d{4})\s*(?:-|–|to)\s*(present|[a-z]{3,9}\.? \d{4})',
        # MM/YYYY - MM/YYYY or Present
        r'(\d{1,2}/\d{4})\s*(?:-|–|to)\s*(present|\d{1,2}/\d{4})',
        # YYYY-MM - YYYY-MM or Present
        r'(\d{4}-\d{2})\s*(?:-|–|to)\s*(present|\d{4}-\d{2})',
        # YYYY - YYYY or Present
        r'(\d{4})\s*(?:-|–|to)\s*(present|\d{4})'
    ]

    matches = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, text))

    if not matches:
        return 0, "0 year(s), 0 month(s)"

    for start_str, end_str in matches:
        start_date = parse_date(start_str)
        if not start_date:
            continue

        if "present" in end_str:
            end_date = datetime.today()
        else:
            end_date = parse_date(end_str)
            if not end_date:
                continue

        if start_date > end_date:
            # Skip invalid ranges where start is in future
            continue

        months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
        total_months += months_diff

    years = total_months // 12
    months = total_months % 12

    if total_months == 0 and any("present" in end_str for _, end_str in matches):
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
