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


def extract_skills(text, skill_list):
    t = text.lower()
    return {s for s in skill_list if s.lower() in t}


def extract_experience_hf(text):
    """
    Use Hugging Face NER to extract DATE entities and compute total experience.
    """
    entities = ner_pipeline(text)
    dates = [e['word'].replace(',', '').strip() for e in entities if e['entity_group'] == 'DATE']
    # dedupe
    seen = set()
    tokens = []
    for d in dates:
        kl = d.lower()
        if kl not in seen:
            seen.add(kl)
            tokens.append(d)
    if len(tokens) < 2:
        return 0, "Not Found"
    total_months = 0
    now = datetime.now()
    for i in range(len(tokens)-1):
        try:
            start = now if tokens[i].lower() in ('present','current') else date_parser.parse(tokens[i], fuzzy=True)
            end = now if tokens[i+1].lower() in ('present','current') else date_parser.parse(tokens[i+1], fuzzy=True)
            if start > end:
                start, end = end, start
            months = (end.year - start.year) * 12 + (end.month - start.month)
            if months > 0:
                total_months += months
        except:
            continue
    if total_months == 0:
        return 0, "Not Found"
    years, months = divmod(total_months, 12)
    if years and months:
        return total_months, f"{years} years and {months} months"
    elif years:
        return total_months, f"{years} years"
    else:
        return total_months, f"{months} months"


def education_match(resume_text, required_qualifications):
    resume_text = resume_text.lower()
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

    # experience via HF
    resume_exp_num, resume_exp_str = extract_experience_hf(resume_text)
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
