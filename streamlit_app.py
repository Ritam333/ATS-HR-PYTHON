import streamlit as st

st.title("ATS Resume Screening System")

option = st.selectbox("Select a Dashboard", ["-- Select --", "HR Dashboard", "Job Seeker Dashboard"])

if option == "HR Dashboard":
    st.switch_page("HR Dashboard")  # not filename — must match page title
elif option == "Job Seeker Dashboard":
    st.switch_page("Job Seeker Dashboard")
