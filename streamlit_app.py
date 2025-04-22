import streamlit as st

st.title("ATS Resume Screening System")

option = st.selectbox("Select a Dashboard", ["-- Select --", "HR Dashboard", "Job Seeker Dashboard"])

if option == "HR Dashboard":
    st.switch_page("pages/1️⃣ HR Dashboard.py")
elif option == "Job Seeker Dashboard":
    st.switch_page("pages/2️⃣ Job Seeker Dashboard.py")
