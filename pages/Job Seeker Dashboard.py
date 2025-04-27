import streamlit as st
import pandas as pd
import requests

# --- Supabase Configuration ---
SUPABASE_URL = "https://dkziaqgekmdfrdtujfqf.supabase.co"    # Replace with your URL
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRremlhcWdla21kZnJkdHVqZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUzNDI3MTgsImV4cCI6MjA2MDkxODcxOH0.9GNoEzHngK0Uz9VVKoD5im5WLy-pmfc2Xbb2uom4OBU"                  # Replace with your key
TABLE_NAME = "job_posts"

def fetch_jobs():
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*"
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        jobs = response.json()
        return jobs
    else:
        st.error("Failed to fetch jobs!")
        return []

# --- Streamlit App ---
st.set_page_config(page_title="Job Seeker Dashboard")
st.title("🔎 Job Seeker Dashboard")

# Fetch and show jobs
jobs_data = fetch_jobs()

if jobs_data:
    st.subheader("📄 Available Job Openings")

    for job in jobs_data:
        with st.container():
            st.markdown(f"## {job.get('job_title', 'N/A')}")
            st.write(f"**Position Level:** {job.get('position_level', 'N/A')}")
            st.write(f"**Location:** {job.get('location', 'N/A')}")
            st.write(f"**Experience Required:** {job.get('experience_required', 'N/A')} years")
            
            # Skills
            skills_value = job.get('skills_required', [])
            if isinstance(skills_value, list):
                skills = ", ".join(skills_value)
            elif isinstance(skills_value, str):
                skills = skills_value
            else:
                skills = "N/A"
            st.write(f"**Skills Required:** {skills}")

            # Job Description
            job_description = job.get('job_description', 'No description provided.')
            st.markdown(f"**📝 Job Description:** {job_description}")

            # Apply Button
            if st.button(f"Apply for {job.get('job_title', 'this role')}", key=job.get('job_id', job.get('id'))):
                st.success(f"You have applied for {job.get('job_title', 'this role')}! 🎯")
            
            st.markdown("---")  # Separator between job posts

else:
    st.info("No job postings available right now. Please check back later!")
