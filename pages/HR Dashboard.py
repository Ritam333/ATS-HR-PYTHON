import streamlit as st
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

# Simulated example data (replace with actual model or backend logic)
sample_data = {
    "Candidate Name": ["Ravi Kumar", "Ayesha Sharma", "Ritu Das"],
    "Match %": [87, 45, 72],
    "Status": ["Shortlisted", "Rejected", "Shortlisted"],
    "Rejection Reason": ["", "Low skill match", ""]
}

df = pd.DataFrame(sample_data)

if "job_description" in st.session_state:
    st.subheader(f"Analysis for: {st.session_state['job_title']}")
    st.dataframe(df)

    # Optional: Download results
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Result CSV", csv, "ats_results.csv", "text/csv")
else:
    st.info("ℹ️ Upload a job description to see analysis results.")
