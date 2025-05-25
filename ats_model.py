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
    Enhanced experience extractor:
    1. Try to extract experience from date ranges.
    2. If not found, fallback to job titles and estimate duration.
    Returns: (total_months, readable_string)
    """
    now = datetime.now()
    min_year, max_year = 1950, now.year + 1
    seen_ranges = set()
    total_months = 0

    # Extended date formats
    date_token = r'(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}' \
                 r'|\d{4}' \
                 r'|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[ .,/-]?\d{2,4}' \
                 r'|present|current)'

    range_re = re.compile(rf'({date_token})\s*(?:-|–|to|until)\s*({date_token})',
                          flags=re.IGNORECASE | re.MULTILINE)

    for start_str, end_str in range_re.findall(text):
        try:
            s = now if start_str.lower() in ('present', 'current') else date_parser.parse(start_str, fuzzy=True)
            e = now if end_str.lower() in ('present', 'current') else date_parser.parse(end_str, fuzzy=True)
            if s.year < min_year or e.year < min_year or s.year > max_year or e.year > max_year:
                continue
            if s > e:
                s, e = e, s
            key = (s.strftime('%Y-%m'), e.strftime('%Y-%m'))
            if key in seen_ranges:
                continue
            seen_ranges.add(key)
            months = (e.year - s.year) * 12 + (e.month - s.month)
            if 0 < months < 120:  # cap each block to 10 years
                total_months += months
        except:
            continue

    # Fallback: estimate from job titles if no date ranges found
    if total_months == 0:
        job_titles = [
            "software engineer", "developer", "data analyst", "project manager", "consultant",
            "intern", "research assistant", "data scientist", "business analyst", "team lead"
        ]
        found_jobs = set()
        for jt in job_titles:
            if re.search(rf'\b{jt}\b', text, flags=re.IGNORECASE):
                found_jobs.add(jt)
        estimated_months = len(found_jobs) * 12  # assume 1 year per unique job title
        if estimated_months:
            total_months = estimated_months

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
