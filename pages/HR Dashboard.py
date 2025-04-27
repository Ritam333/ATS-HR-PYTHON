import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- Supabase Configuration ---
url = "https://dkziaqgekmdfrdtujfqf.supabase.co"   # your Project URL
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRremlhcWdla21kZnJkdHVqZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUzNDI3MTgsImV4cCI6MjA2MDkxODcxOH0.9GNoEzHngK0Uz9VVKoD5im5WLy-pmfc2Xbb2uom4OBU"

supabase: Client = create_client(url, key)

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
        
        # Insert into Supabase
        data = {
            "job_title": job_title,
            "position_level": position_level,
            "location": location,
            "experience_required": experience,
            "qualification": qualification,
            "skills_required": skills,
            "job_description": job_description
        }
        
        response = supabase.table("job_posts").insert(data).execute()

        if response.status_code == 201:
            st.success(f"✅ Job for '{position_level} {job_title}' at '{location}' uploaded successfully to Supabase!")
        else:
            st.error(f"❌ Failed to upload job info! Error: {response.data}")
    else:
        st.warning("⚠️ Please fill in all fields before submitting.")

# Section 2: Resume Analysis Result
st.header("📊 Resume Analysis")
