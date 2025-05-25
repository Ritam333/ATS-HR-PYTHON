import re
import requests
import fitz
import numpy as np
from datetime import datetime
from dateutil import parser as date_parser
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline

# Initialize models
model = SentenceTransformer('all-MiniLM-L6-v2')
ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)

# Qualification abbreviation mapping
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

def normalize_qualification(text):
    t = text.lower()
    for abbr, forms in QUALIFICATION_MAP.items():
        if any(f in t for f in forms): return abbr
    return None

def extract_text_from_pdf_url(url: str) -> str:
    """Extract text from PDF via fitz"""
    try:
        data = requests.get(url).content
        with fitz.open(stream=data, filetype="pdf") as doc:
            return "\n".join(page.get_text() for page in doc)
    except:
        return ""

def extract_experience_hf(text):
    """
    Use explicit regex ranges first, then fallback to HF NER + regex tokens.
    """
    now = datetime.now()

    # 1) Explicit date-range regex
    date_token = _REGEX_DATE
    range_re = re.compile(rf'({date_token})\s*(?:-|–|to)\s*({date_token})', flags=re.IGNORECASE)
    total_months = 0
    ranges = range_re.findall(text)
    if ranges:
        for start_str, end_str in ranges:
            try:
                s = now if start_str.lower() in ('present','current') else date_parser.parse(start_str, fuzzy=True)
                e = now if end_str.lower() in ('present','current') else date_parser.parse(end_str, fuzzy=True)
                if s > e: 
                    s, e = e, s
                months = (e.year - s.year) * 12 + (e.month - s.month)
                if months > 0:
                    total_months += months
            except:
                continue

    # 2) Fallback: merge HF NER tokens and regex tokens
    else:
        entities = ner_pipeline(text)
        hf_dates = [e['word'].replace(',', '').strip() for e in entities if e['entity_group']=='DATE']
        regex_dates = re.findall(_REGEX_DATE, text, flags=re.IGNORECASE)
        regex_dates = [d.strip() for d in regex_dates]

        seen = set()
        tokens = []
        for d in hf_dates + regex_dates:
            key = d.lower()
            if key not in seen:
                seen.add(key)
                tokens.append(d)

        for i in range(len(tokens) - 1):
            try:
                s = now if tokens[i].lower() in ('present','current') else date_parser.parse(tokens[i], fuzzy=True)
                e = now if tokens[i+1].lower() in ('present','current') else date_parser.parse(tokens[i+1], fuzzy=True)
                if s > e:
                    s, e = e, s
                months = (e.year - s.year) * 12 + (e.month - s.month)
                if months > 0:
                    total_months += months
            except:
                continue

    if total_months == 0:
        return 0, "Not Found"

    years, months = divmod(total_months, 12)
    if years and months:
        human = f"{years} years and {months} months"
    elif years:
        human = f"{years} years"
    else:
        human = f"{months} months"

    return total_months, human





def education_match(resume_text, required_qualifications):
    quals = {normalize_qualification(l) for l in resume_text.splitlines() if normalize_qualification(l)}
    return bool(quals.intersection({q.lower() for q in required_qualifications}))


def check_location(text, locations):
    t = text.lower()
    return any(loc.lower() in t for loc in locations)


def calculate_ats_score(resume_text, jd_text, skills, exp, edu_keywords, locations):
    # semantic similarity
    resume_embedding = model.encode(resume_text)
    jd_embedding = model.encode(jd_text)
    cosine_score = cosine_similarity([resume_embedding], [jd_embedding])[0][0]

    # skills
    matched_skills = extract_skills(resume_text, skills)
    skill_score = len(matched_skills) / len(skills) if skills else 0

    # experience via HF + regex
    resume_exp_num, resume_exp_str = extract_experience_hf(resume_text)
    exp_score = min(resume_exp_num / exp, 1) if exp else 0

    edu_score = education_match(resume_text, edu_keywords)
    loc_score = check_location(resume_text, locations)

    final_score = (cosine_score * 0.5
                   + skill_score * 0.2
                   + exp_score * 0.1
                   + edu_score * 0.1
                   + loc_score * 0.1) * 100

    return round(final_score, 2), {
        "cosine_similarity": round(cosine_score, 2),
        "skills_matched": list(matched_skills),
        "experience_years": resume_exp_str,
        "education_matched": bool(edu_score),
        "location_matched": bool(loc_score)
    }
