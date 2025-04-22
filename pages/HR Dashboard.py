import streamlit as st
import pandas as pd

st.set_page_config(page_title="HR Dashboard")
st.title("👔 HR Dashboard")

# Section 1: Upload Job Details
st.header("📄 Upload Job Requirement")

with st.form("job_posting_form"):
    job_title = st.text_input("🏷️ Job Title", placeholder="e.g., Software Engineer")
    position_level = st.selectbox("🧑‍💼 Required Position", ["-- Select --", "Intern", "Junior", "Mid-Level", "Senior", "Lead"])
    location = st.text_input("📍 Onsite Location", placeholder="e.g., Bangalore, India")
    experience = st.slider("📆 Years of Experience Required", min_value=0, max_value=15, value=2)
    job_description = st.text_area("📝 General Job Description", placeholder="e.g., Responsibilities, skills required, etc.")
    
    submit_job = st.form_submit_button("📤 Upload Job Info")

if submit_job:
    if job_title and position_level != "-- Select --" and location and job_description:
        st.success(f"✅ Job for '{position_level} {job_title}' at '{location}' uploaded successfully!")
        # You can save this directly to database here
    else:
        st.warning("⚠️ Please fill in all fields before submitting.")

# Section 2: Resume Analysis Result
st.header("📊 Resume Analysis")
