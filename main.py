from pathlib import Path
import streamlit as st
import pandas as pd
from analysis import load_data, clean_data, get_summary, get_numeric_stats, get_category_counts, export_to_pdf
from visualization import plot_bar, plot_histogram, plot_pie, plot_scatter
from ai_helper import ask_ai

st.set_page_config(page_title="AI Data Analysis Assistant", page_icon="📊", layout="wide")

st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Go to",[
    "Home","Upload Dataset","Dataset Preview","Statistics",
    "Visualizations","AI Assistant","Export Report","About"
])

if "df" not in st.session_state:
    st.session_state.df=None
    st.session_state.filename=None

if page == "Home":

    st.title("📊 AI Data Analysis Assistant")
    st.markdown("""
    Welcome to the **AI Data Analysis Assistant**.

    This application helps users analyze CSV datasets quickly using
    interactive visualizations, statistical analysis, and Artificial Intelligence.

    ---
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🚀 Project Features")

        st.markdown("""
        ✅ Upload any CSV dataset

        ✅ Automatic data cleaning

        ✅ Dataset preview

        ✅ Dataset information

        ✅ Statistical summary

        ✅ Missing value detection

        ✅ Interactive charts

        - 📊 Bar Chart
        - 📈 Histogram
        - 🥧 Pie Chart
        - 📉 Scatter Plot

        ✅ AI-powered dataset analysis

        ✅ Ask questions about your data

        ✅ Generate AI insights

        ✅ Export AI report as PDF

        ✅ Fast and user-friendly interface

        ✅ Built using:
        - Streamlit
        - Pandas
        - Plotly
        - OpenRouter AI
        """)

    with col2:

        st.info("""
### 🎯 Use This App

1. Upload CSV File

2. Explore Dataset

3. View Statistics

4. Create Visualizations

5. Ask AI Questions

6. Download PDF Report
""")

    st.markdown("---")

    st.subheader("💡 Why Use This Project?")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.success("""
### ⚡ Fast

Analyze datasets within seconds using automated processing.
""")

    with c2:
        st.warning("""
### 🤖 AI Powered

Ask natural language questions and receive intelligent insights.
""")

    with c3:
        st.info("""
### 📊 Interactive

Generate beautiful and interactive visualizations instantly.
""")

    st.markdown("---")

    st.subheader("🛠 Technologies Used")

    tech1, tech2, tech3, tech4 = st.columns(4)

    tech1.metric("Frontend", "Streamlit")
    tech2.metric("Data", "Pandas")
    tech3.metric("Charts", "Plotly")
    tech4.metric("AI", "OpenRouter")

    st.markdown("---")

    st.success("👈 Select **Upload Dataset** from the sidebar to get started.")

elif page=="Upload Dataset":
    file=st.file_uploader("Upload CSV",type=["csv"])
    if file:
        df=clean_data(load_data(file))
        st.session_state.df=df
        st.session_state.filename=file.name
        st.success("Dataset loaded successfully!")
        st.dataframe(df.head())

else:
    df=st.session_state.df
    if df is None:
        st.warning("Please upload a dataset first.")
        st.stop()

    if page=="Dataset Preview":
        st.title("Dataset Preview")
        st.dataframe(df)
        c1,c2,c3=st.columns(3)
        c1.metric("Rows",df.shape[0])
        c2.metric("Columns",df.shape[1])
        c3.metric("Missing",int(df.isna().sum().sum()))

    elif page=="Statistics":
        st.title("Statistics")
        stats=get_numeric_stats(df)
        if stats is not None:
            st.dataframe(stats)
        st.subheader("Missing Values")
        st.dataframe(df.isna().sum().rename("Missing"))

    elif page=="Visualizations":
        st.title("Visualizations")
        nums=df.select_dtypes(include="number").columns.tolist()
        cats=df.select_dtypes(exclude="number").columns.tolist()
        chart=st.selectbox("Chart",["Bar","Histogram","Pie","Scatter"])
        if chart=="Bar" and cats:
            c=st.selectbox("Category",cats)
            st.plotly_chart(plot_bar(df,c),use_container_width=True)
        elif chart=="Histogram" and nums:
            c=st.selectbox("Numeric",nums)
            st.plotly_chart(plot_histogram(df,c),use_container_width=True)
        elif chart=="Pie" and cats:
            c=st.selectbox("Category",cats)
            st.plotly_chart(plot_pie(df,c),use_container_width=True)
        elif chart=="Scatter" and len(nums)>=2:
            x=st.selectbox("X",nums)
            y=st.selectbox("Y",nums,index=1)
            st.plotly_chart(plot_scatter(df,x,y),use_container_width=True)

    elif page=="AI Assistant":
        st.title("AI Assistant")
        q=st.text_input("Ask about your dataset")
        if st.button("Ask AI") and q:
            summary=get_summary(df,st.session_state.filename)
            ans=ask_ai(q,summary)
            st.write(ans)
            st.session_state.answer=ans

    elif page=="Export Report":
        st.title("Export")
        ans=st.session_state.get("answer","No AI analysis available.")
        if st.button("Generate PDF"):
            pdf=export_to_pdf(ans)
            with open(pdf,"rb") as f:
                st.download_button("Download PDF",f,file_name=pdf,mime="application/pdf")

    elif page=="About":
        st.title("About")
        st.info("AI Data Analysis Assistant built with Streamlit, Plotly and OpenRouter.")
