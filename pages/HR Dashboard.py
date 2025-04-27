import streamlit as st
import pandas as pd
import requests
import json

# --- Supabase Configuration ---
SUPABASE_URL = "https://yourproject.supabase.co"
SUPABASE_API_KEY = "your-anon-key"
TABLE_NAME = "job_posts"

def insert_into_supabase(data):
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response

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
        
        # Insert into Supabase via API
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

# Section 2: Resume Analysis Result
st.header("📊 Resume Analysis")
