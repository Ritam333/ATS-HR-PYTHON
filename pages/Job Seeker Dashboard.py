import streamlit as st
import pandas as pd
import requests

# --- Supabase Configuration ---
SUPABASE_URL = "https://dkziaqgekmdfrdtujfqf.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRremlhcWdla21kZnJkdHVqZnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUzNDI3MTgsImV4cCI6MjA2MDkxODcxOH0.9GNoEzHngK0Uz9VVKoD5im5WLy-pmfc2Xbb2uom4OBU"
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
    df = pd.DataFrame(jobs_data)

    # Optional: Only show available columns
    columns_we_want = ['job_id', 'job_title', 'position_level', 'location', 'experience_required', 'skills_required']

    # Filter columns that actually exist
    available_columns = [col for col in columns_we_want if col in df.columns]

    if available_columns:
        st.subheader("📄 Available Job Openings")
        st.dataframe(df[available_columns])
    else:
        st.info("No matching columns found in the fetched data.")

else:
    st.info("No job postings available right now. Please check back later!")
