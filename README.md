# 🧠 ATS Resume-Job Matching System

A smart **Applicant Tracking System (ATS)** that uses **NLP** and **Machine Learning** to evaluate and score resumes against job descriptions, helping recruiters make faster, data-driven hiring decisions.

## 🚀 Project Highlights

- ✅ Resume vs Job Description Matching  
- 🔍 NLP-based skill, education, and experience extraction  
- 📊 ATS score with matching insights  
- 📄 Streamlit-powered interactive dashboard  
- ☁️ Optional cloud storage with Supabase (for resumes & job data)  

## 🛠️ Tech Stack

| Tool/Library           | Purpose                                |
|------------------------|----------------------------------------|
| Python                 | Core programming language              |
| Streamlit              | Web UI for uploading & displaying      |
| sentence-transformers  | Embedding resumes & job texts          |
| scikit-learn           | ML-based similarity calculations       |
| Pandas                 | Data handling & transformation         |
| Supabase (optional)    | Cloud database and file storage        |

## 📁 Folder Structure


## 💡 Features

### ✅ Resume & JD Upload
Upload both documents using a simple Streamlit interface.

### 🔎 Smart Matching
The model checks for:
- **Skill overlap**
- **Experience match**
- **Education qualification**
- **Location preference**

### 📊 ATS Score & Explanation
Get:
- **Overall ATS Score (0–100%)**
- **Matched & Missing skills**
- **Reasons for rejection or suggestions for improvement**

## 🧪 How It Works (Flowchart)

```mermaid
graph TD
A[Upload Resume & JD] --> B[Text Extraction & Cleaning]
B --> C[Sentence Embedding]
C --> D[Cosine Similarity Calculation]
D --> E[Rule-Based Matching]
E --> F[Score + Suggestions]
F --> G[Display in Streamlit Dashboard]
