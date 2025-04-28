import streamlit as st
import pandas as pd
import requests
import base64

# --- Supabase Configuration ---
SUPABASE_URL = "https://dkziaqgekmdfrdtujfqf.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRremlhcWdla21kZnJkdHVqZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUzNDI3MTgsImV4cCI6MjA2MDkxODcxOH0.9GNoEzHngK0Uz9VVKoD5im5WLy-pmfc2Xbb2uom4OBU"

# Table names
JOB_TABLE = "job_posts"
APPLICATION_TABLE = "applications"    # <-- Your new table to store applications
STORAGE_BUCKET = "resumes"             # <-- Your storage bucket for uploaded files

def fetch_jobs():
    url = f"{SUPABASE_URL}/rest/v1/{JOB_TABLE}?select=*"
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

def upload_to_storage(file, filename):
    """Uploads file to Supabase Storage and returns the public URL."""
    url = f"{SUPABASE_URL}/storage/v1/object/{STORAGE_BUCKET}/{filename}"
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/octet-stream"
    }
    response = requests.put(url, headers=headers, data=file)   # <-- notice PUT not POST
    
    if response.status_code in (200, 201):
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{filename}"
        return public_url
    else:
        st.error(f"Failed to upload resume to storage! Error: {response.text}")
        return None


def save_application(job_id, job_title, resume_url):
    """Saves the application info to Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/{APPLICATION_TABLE}"
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "job_uid": job_id,
        "job_title": job_title,
        "resume_url": resume_url
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code in (200, 201)

# --- Streamlit App ---
st.set_page_config(page_title="Job Seeker Dashboard")
st.title("🔎 Job Seeker Dashboard")

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

            # Upload CV
            uploaded_cv = st.file_uploader(
                "📄 Upload your Resume (PDF or DOCX)",
                type=['pdf', 'docx'],
                key=f"cv_{job.get('job_id', job.get('id'))}"
            )

            if uploaded_cv is not None:
                if st.button("📤 Submit Resume", key=f"submit_{job.get('job_id', job.get('id'))}"):
                    # Upload the file to Supabase Storage
                    file_bytes = uploaded_cv.read()
                    filename = f"{job.get('job_id', job.get('id'))}_{uploaded_cv.name}"
                    resume_url = upload_to_storage(file_bytes, filename)

                    if resume_url:
                        success = save_application(
                            job_id=job.get('job_id', job.get('id')),
                            job_title=job.get('job_title', 'N/A'),
                            resume_url=resume_url
                        )
                        if success:
                            st.success(f"✅ Resume submitted successfully for {job.get('job_title', 'this role')}!")
                        else:
                            st.error("❌ Failed to save application!")

            st.markdown("---")  # Separator between job posts

else:
    st.info("No job postings available right now. Please check back later!")
