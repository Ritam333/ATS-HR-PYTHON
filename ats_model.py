import re
import requests
import fitz
import numpy as np
from datetime import datetime
from dateutil import parser as date_parser
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Qualification mapping
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
    return re.sub(r'\s+', ' ', text).strip()


def normalize_qualification(text: str) -> str:
    t = text.lower()
    for abbr, forms in QUALIFICATION_MAP.items():
        if any(f in t for f in forms):
            return abbr
    return None


def extract_text_from_pdf_url(url: str) -> str:
    """Extract text from PDF via fitz"""
    try:
        data = requests.get(url).content
        with fitz.open(stream=data, filetype="pdf") as doc:
            return "\n".join(page.get_text() for page in doc)
    except:
        return ""


def extract_skills(text: str, skill_list: list) -> set:
    """Extract matching skills from text"""
    t = text.lower()
    return {s for s in skill_list if s.lower() in t}





def calculate_duration(start, end):
    """Return duration between two dates as years, months, and days."""
    delta_years = end.year - start.year
    delta_months = end.month - start.month
    delta_days = end.day - start.day

    if delta_days < 0:
        delta_months -= 1
        delta_days += (start.replace(month=start.month % 12 + 1, day=1) - start.replace(day=1)).days

    if delta_months < 0:
        delta_years -= 1
        delta_months += 12

    return delta_years, delta_months, delta_days

def extract_experience(text):
    # Patterns to match common date ranges
    patterns = [
        r'(?P<start>[A-Za-z]+\s\d{4})\s*(?:–|-|to)\s*(?P<end>[A-Za-z]+\s\d{4}|Present)',
        r'(?P<start>\d{1,2}/\d{1,2}/\d{4})\s*(?:–|-|to)\s*(?P<end>\d{1,2}/\d{1,2}/\d{4}|Present)',
        r'(?P<start>[A-Za-z]+\s\d{1,2},\s*\d{4})\s*(?:–|-|to)\s*(?P<end>[A-Za-z]+\s\d{1,2},\s*\d{4}|Present)'
    ]
    
    total_experience_days = 0
    experience_durations = []

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            start_str = match.group('start')
            end_str = match.group('end')

            try:
                start_date = parser.parse(start_str)
            except:
                continue

            if end_str.lower() == 'present':
                end_date = datetime.today()
            else:
                try:
                    end_date = parser.parse(end_str)
                except:
                    continue

            y, m, d = calculate_duration(start_date, end_date)
            experience_durations.append((y, m, d))
            total_experience_days += (end_date - start_date).days

    # Calculate total years of experience as float
    total_years_exp = round(total_experience_days / 365, 2)

    return total_years_exp, experience_durations






def education_match(resume_text: str, required_qualifications: list) -> bool:
    quals = {normalize_qualification(line) for line in resume_text.splitlines() if normalize_qualification(line)}
    return bool(quals.intersection({q.lower() for q in required_qualifications}))


def check_location(text: str, locations: list) -> bool:
    t = text.lower()
    return any(loc.lower() in t for loc in locations)


def calculate_ats_score(resume_text: str, jd_text: str, skills: list, exp: int, edu_keywords: list, locations: list) -> tuple:
    # embeddings
    resume_embedding = model.encode(resume_text)
    jd_embedding = model.encode(jd_text)
    cosine_score = cosine_similarity([resume_embedding], [jd_embedding])[0][0]
    # skills
    matched_skills = extract_skills(resume_text, skills)
    skill_score = len(matched_skills)/len(skills) if skills else 0
    # experience
    resume_exp_num, resume_exp_str = extract_experience(resume_text)
    exp_score = min(resume_exp_num/exp, 1) if exp else 0
    # education & location
    edu_score = education_match(resume_text, edu_keywords)
    loc_score = check_location(resume_text, locations)
    final_score = (cosine_score*0.5 + skill_score*0.2 + exp_score*0.1 + edu_score*0.1 + loc_score*0.1)*100
    return round(final_score,2), {
        "cosine_similarity": round(cosine_score,2),
        "skills_matched": list(matched_skills),
        "experience_years": resume_exp_str,
        "education_matched": bool(edu_score),
        "location_matched": bool(loc_score)
    }
