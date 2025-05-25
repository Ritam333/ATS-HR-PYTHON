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





def extract_experience(text: str) -> tuple:
    """
    Robust experience extractor:
    - Supports a wide range of date formats.
    - Falls back to job title detection if no dates found.
    """
    now = datetime.now()
    min_year, max_year = 1950, now.year + 1
    seen_ranges = set()
    total_months = 0

    # Expanded date token regex
    month_names = r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|' \
                  r'May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|' \
                  r'Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'

    date_token = (
        rf'(\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}|'  # dd-mm-yyyy
        rf'\d{{4}}[/-]\d{{1,2}}[/-]?\d*|'           # yyyy-mm or yyyy-mm-dd
        rf'{month_names}[ \t.,-]*\d{{2,4}}|'        # Month Year
        rf'\d{{4}}|'                                # year
        rf'present|current)'
    )

    range_re = re.compile(rf'({date_token})\s*(?:-|–|—|to|until)?\s*({date_token})',
                          flags=re.IGNORECASE | re.MULTILINE)

    for match in range_re.findall(text):
        start_str, end_str = match[0], match[-1]
        try:
            start = now if start_str.strip().lower() in ("present", "current") else date_parser.parse(start_str, fuzzy=True)
            end = now if end_str.strip().lower() in ("present", "current") else date_parser.parse(end_str, fuzzy=True)
            if start.year < min_year or end.year < min_year or start.year > max_year or end.year > max_year:
                continue
            if start > end:
                start, end = end, start
            key = (start.strftime('%Y-%m'), end.strftime('%Y-%m'))
            if key in seen_ranges:
                continue
            seen_ranges.add(key)
            months = (end.year - start.year) * 12 + (end.month - start.month)
            if 0 < months < 120:  # ignore unreasonable gaps
                total_months += months
        except Exception:
            continue

    # Fallback to estimating by job titles
    if total_months == 0:
        job_titles = [
            "software engineer", "developer", "data analyst", "project manager", "consultant",
            "intern", "research assistant", "data scientist", "business analyst", "team lead"
        ]
        found_jobs = set()
        for jt in job_titles:
            if re.search(rf'\b{jt}\b', text, flags=re.IGNORECASE):
                found_jobs.add(jt)
        total_months = len(found_jobs) * 12  # estimate 1 year per unique role

    if total_months == 0:
        return 0, "Not Found"

    years, months = divmod(total_months, 12)
    if years and months:
        return total_months, f"{years} years and {months} months"
    elif years:
        return total_months, f"{years} years"
    return total_months, f"{months} months"




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
