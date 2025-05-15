# --- Imports ---
import streamlit as st
from model_demo import calculate_ats_score, clean_text
from sentence_transformers import SentenceTransformer
import fitz
import numpy as np
from supabase import create_client

# --- Supabase Configuration ---
SUPABASE_URL = "https://dkziaqgekmdfrdtujfqf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRremlhcWdla21kZnJkdHVqZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUzNDI3MTgsImV4cCI6MjA2MDkxODcxOH0.9GNoEzHngK0Uz9VVKoD5im5WLy-pmfc2Xbb2uom4OBU"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Fetch Job Details Function ---
def fetch_job_details(job_id):
    response = supabase.table("job_table").select("*").eq("job_id", job_id).execute()
    if response.data:
        job = response.data[0]
        return {
            "expected_skills": job["skills"].split(","),
            "required_experience": job["experience"],
            "required_education_keywords": job["education"].split(","),
            "preferred_locations": job["location"].split(",")
        }
    return None

# --- Streamlit App Logic ---
st.title("📄 ATS Resume Evaluator")

job_id = st.text_input("Enter Job ID")
uploaded_resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

if job_id and uploaded_resume:
    job_params = fetch_job_details(job_id)
    if job_params:
        with fitz.open(stream=uploaded_resume.read(), filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()

        cleaned_resume = clean_text(text)
        jd_text = st.text_area("Paste Job Description")

        if jd_text:
            model = SentenceTransformer('all-MiniLM-L6-v2')
            score, details = calculate_ats_score(
                cleaned_resume, clean_text(jd_text),
                job_params["expected_skills"],
                job_params["required_experience"],
                job_params["required_education_keywords"],
                job_params["preferred_locations"]
            )

            st.metric("✅ ATS Score", f"{score}/100")
            st.subheader("🔍 Match Details")
            st.json(details)
    else:
        st.warning("⚠️ No job found with that ID.")
