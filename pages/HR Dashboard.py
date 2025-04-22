import streamlit as st
st.set_page_config(page_title="HR Dashboard")

import pandas as pd

st.title("👔 HR Dashboard")

# Section 1: Upload Job Description
st.header("📄 Upload Job Description")

with st.form("job_description_form"):
    job_title = st.text_input("Job Title")
    job_description = st.text_area("Paste Job Description Here")
    submit_job = st.form_submit_button("Upload Job Description")

if submit_job:
    if job_title and job_description:
        st.success(f"✅ Job Description for '{job_title}' uploaded successfully!")
        # Store in session state for later access
        st.session_state["job_title"] = job_title
        st.session_state["job_description"] = job_description
    else:
        st.warning("⚠️ Please provide both a job title and description.")

# Section 2: Resume Analysis Result
st.header("📊 Resume Analysis")

