# ats_model.py
import re
import requests
import fitz
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from dateutil import parser as date_parser


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
    date_str = date_str.strip().replace(',', '')
    date_formats = [
        "%B %d %Y",  # February 3 2025
        "%b %d %Y",  # Feb 3 2025
        "%B %Y",     # February 2025
        "%b %Y",     # Feb 2025
        "%Y"         # 2025
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    if date_str.lower() == "present":
        return datetime.now()
    return None


def extract_experience(text):
    import itertools

    text = text.replace('\u00A0', ' ').replace('\n', ' ').replace('\r', ' ')
    # text = text.replace('–', '-').replace('—', '-')  # ✅ NEW: Handle en-dash/em-dash
    text = re.sub(r'\s+', ' ', text).strip()

    # Patterns for date ranges (e.g. Jan 2020 - Present, Mar 2022 to Feb 2023)
    date_range_pattern = re.findall(
        r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|'
        r'Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})\s*[-to]+\s*'
        r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|'
        r'Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?\s+\d{4}|present))',
        text,
        flags=re.IGNORECASE
    )

    if not date_range_pattern:
        return 0, "Not Found"

    total_months = 0

    for start_str, end_str in date_range_pattern:
        try:
            start = date_parser.parse(start_str, fuzzy=True)
            end = datetime.now() if "present" in end_str.lower() else date_parser.parse(end_str, fuzzy=True)
            months = (end.year - start.year) * 12 + (end.month - start.month)
            if months > 0:
                total_months += months
        except:
            continue

    if total_months == 0:
        return 0, "Not Found"

    years = total_months // 12
    months = total_months % 12

    if years and months:
        return total_months, f"{years} years and {months} months"
    elif years:
        return total_months, f"{years} years"
    else:
        return total_months, f"{months} months"





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
