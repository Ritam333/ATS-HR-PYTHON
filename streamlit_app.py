import streamlit as st

st.title("ATS Resume Screening System")

option = st.selectbox("Select a Dashboard", ["-- Select --", "HR Dashboard", "Job Seeker Dashboard"])

if option == "HR Dashboard":
    st.switch_page("pages/hr_dashboard.py")
elif option == "Job Seeker Dashboard":
    st.switch_page("pages/job_seeker_dashboard.py")
