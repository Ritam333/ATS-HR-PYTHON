import streamlit as st
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.title("💼 HR Dashboard")

# Section selection inside the same dashboard
section = st.radio("Choose a section:", ["Upload Job Description", "ATS Resume Analysis"])

# Make sure storage directory exists
os.makedirs("storage", exist_ok=True)

# ---------------------- Upload Section ----------------------
if section == "Upload Job Description":
    st.subheader("📄 Upload Job Description")

    uploaded_jd = st.file_uploader("Upload JD (txt/pdf)", type=["txt", "pdf"])
    
    if uploaded_jd is not None:
        jd_text = uploaded_jd.read().decode("utf-8", errors="ignore")
        st.text_area("Preview", jd_text, height=250)

        if st.button("Save JD"):
            with open("storage/job_description.txt", "w", encoding="utf-8") as f:
                f.write(jd_text)
            st.success("Job description saved!")

# ---------------------- ATS Section ----------------------
elif section == "ATS Resume Analysis":
    st.subheader("📊 Analyze Resume Against JD")

    # Load saved JD
    try:
        with open("storage/job_description.txt", "r", encoding="utf-8") as f:
            jd_text = f.read()
    except FileNotFoundError:
        st.error("❗ Please upload a job description first.")
        st.stop()

    st.text_area("Current JD", jd_text, height=200)

    uploaded_resume = st.file_uploader("Upload Resume (txt)", type=["txt"])
    if uploaded_resume is not None:
        resume_text = uploaded_resume.read().decode("utf-8", errors="ignore")

        # Calculate ATS match score using TF-IDF + cosine similarity
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([jd_text, resume_text])
        similarity_score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0] * 100

        st.metric("ATS Match Score", f"{similarity_score:.2f}%")
        if similarity_score >= 60:
            st.success("✅ Resume is a good match!")
        else:
            st.warning("⚠️ Resume needs improvement.")

