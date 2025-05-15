import streamlit as st
import pandas as pd
import requests
import json

from ats_model import (
    clean_text, extract_text_from_pdf_url, calculate_ats_score
)

# --- Supabase Configuration ---
SUPABASE_URL = "https://dkziaqgekmdfrdtujfqf.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRremlhcWdla21kZnJkdHVqZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUzNDI3MTgsImV4cCI6MjA2MDkxODcxOH0.9GNoEzHngK0Uz9VVKoD5im5WLy-pmfc2Xbb2uom4OBU"

JOB_TABLE = "job_posts"
APPLICATION_TABLE = "applications"

# --- Helper to insert job post ---
def insert_into_supabase(data):
    url = f"{SUPABASE_URL}/rest/v1/{JOB_TABLE}"
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    return requests.post(url, headers=headers, data=json.dumps(data))

# --- Helper to fetch Supabase data ---
def fetch_table_data(table):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}"
    }
    return requests.get(url, headers=headers).json()

# --- Streamlit App ---
st.set_page_config(page_title="HR Dashboard")
st.title("👔 HR Dashboard")

# Section 1: Upload Job Details
st.header("📄 Upload Job Requirement")

with st.form("job_posting_form"):
    job_title = st.text_input("🏷️ Job Title", placeholder="e.g., Software Engineer")
    position_level = st.selectbox("🧑‍💼 Required Position", ["-- Select --", "Intern", "Junior", "Mid-Level", "Senior", "Lead"])
    location = st.text_input("📍 Onsite Location", placeholder="e.g., Bangalore, India")
    experience = st.slider("📆 Years of Experience Required", min_value=0, max_value=15, value=2)
    qualification = st.multiselect("🎓 Minimum Qualification", ["Diploma", "B.Sc", "B.Tech/B.E", "M.Sc", "MCA", "MBA", "Other"])
    skills = st.multiselect("🛠️ Required Skills", ["Python", "SQL", "Excel", "Communication", "Machine Learning", "JavaScript", "Power BI", "Django", "HTML/CSS", "React", "Git"])
    job_description = st.text_area("📝 General Job Description", placeholder="e.g., Responsibilities, skills required, etc.")
    
    submit_job = st.form_submit_button("📤 Upload Job Info")

if submit_job:
    if (job_title and position_level != "-- Select --" and location and job_description and qualification and skills):
        data = {
            "job_title": job_title,
            "position_level": position_level,
            "location": location,
            "experience_required": experience,
            "qualification": qualification,
            "skills_required": skills,
            "job_description": job_description
        }
        response = insert_into_supabase(data)
        if response.status_code == 201:
            st.success(f"✅ Job for '{position_level} {job_title}' at '{location}' uploaded successfully to Supabase!")
        else:
            st.error(f"❌ Failed to upload job info! Error: {response.text}")
    else:
        st.warning("⚠️ Please fill in all fields before submitting.")

# Section 2: Resume Analysis
st.header("📊 Resume Analysis")

jobs = fetch_table_data(JOB_TABLE)
applications = fetch_table_data(APPLICATION_TABLE)

if jobs and applications:
    for job in jobs:
        st.subheader(f"{job['job_title']} ({job['location']})")
        related_apps = [a for a in applications if a.get("job_uid") == job.get("id")]

        if not related_apps:
            st.info("No applications received yet.")
            continue

        for app in related_apps:
            resume_url = app.get("resume_url")
            if not resume_url:
                st.warning("No resume URL found.")
                continue

            resume_raw = extract_text_from_pdf_url(resume_url)
            resume_clean = clean_text(resume_raw)
            jd_clean = clean_text(job.get('job_description', ''))

            score, details = calculate_ats_score(
                resume_clean,
                jd_clean,
                job.get('skills_required', []),
                job.get('experience_required', 0),
                job.get('qualification', []),
                [job.get('location', '')]
            )

            with st.expander(f"📄 Resume: {resume_url.split('/')[-1]} | ATS Score: {score}%"):
                st.write("🔹 Cosine Similarity:", details["cosine_similarity"])
                st.write("🔹 Skills Matched:", ", ".join(details["skills_matched"]))
                st.write("🔹 Experience (Years):", details["experience_years"])
                st.write("🔹 Education Match:", "✅ Yes" if details["education_matched"] else "❌ No")
                st.write("🔹 Location Match:", "✅ Yes" if details["location_matched"] else "❌ No")

else:
    st.warning("No job or application data found.")
