import streamlit as st
import pandas as pd


st.set_page_config(page_title="HR Dashboard", layout="wide")

# Title
st.title("📊 HR Dashboard")

# Upload CSV
uploaded_file = st.file_uploader("Upload Employee Data (CSV)", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Sidebar filters
    st.sidebar.header("Filter")
    dept_filter = st.sidebar.multiselect("Select Department", df['Department'].unique(), default=df['Department'].unique())
    gender_filter = st.sidebar.multiselect("Select Gender", df['Gender'].unique(), default=df['Gender'].unique())

    # Apply filter
    filtered_df = df[(df['Department'].isin(dept_filter)) & (df['Gender'].isin(gender_filter))]

    # KPIs
    total_employees = filtered_df.shape[0]
    avg_age = round(filtered_df['Age'].mean(), 1)
    avg_salary = round(filtered_df['Salary'].mean(), 2)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Employees", total_employees)
    col2.metric("Average Age", avg_age)
    col3.metric("Average Salary", f"${avg_salary}")

    # Charts
    st.subheader("📌 Gender Distribution")
    gender_count = filtered_df['Gender'].value_counts()
    fig1, ax1 = plt.subplots()
    ax1.pie(gender_count, labels=gender_count.index, autopct='%1.1f%%', startangle=90)
    ax1.axis("equal")
    st.pyplot(fig1)

    st.subheader("📌 Employees by Department")
    dept_count = filtered_df['Department'].value_counts()
    st.bar_chart(dept_count)

    # Data Preview
    st.subheader("📄 Employee Data")
    st.dataframe(filtered_df)

else:
    st.info("Please upload a CSV file to view the dashboard.")
