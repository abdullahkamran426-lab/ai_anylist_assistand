"""
About page
==========
Static app description and technology-stack summary. No dataframe
or session state required.
"""

import streamlit as st

from modules.utils import section


def render_about_page():
    """
    Render the About page.
    App description and technology stack information.
    """
    section("INFO", "About DataLens")
    
    st.markdown("""
    <div class='clean-panel'>
        <p style='color:#94a3b8;line-height:1.75;margin-bottom:12px'>
        <b style='color:#fff'>DataLens</b> is a modular AI-powered data analysis assistant built to help you explore,
        clean, visualize, and model datasets without writing a single line of code.
        </p>
        <p style='color:#94a3b8;line-height:1.75;margin-bottom:12px'>
        The app offers an interactive <b style='color:#fff'>Data Cleaning Pipeline</b> (allowing you to drop duplicates,
        impute or handle missing values, cast column datatypes, and rename fields with a live audit trail),
        an interactive <b style='color:#fff'>Plotly Visualization Suite</b>, and a natural language <b style='color:#fff'>AI Assistant</b>.
        </p>
        <p style='color:#94a3b8;line-height:1.75;margin-bottom:12px'>
        In addition, the built-in <b style='color:#fff'>AutoML Prediction Studio</b> races multiple machine learning models
        (Regression & Classification) behind a standardized preprocessor to train, cross-validate, evaluate, and let you
        make single-row predictions or export complete PDF reports.
        </p>
        <p style='color:#94a3b8;line-height:1.75'>
        Designed with a <b style='color:#fff'>Student Sandbox Mode</b>, DataLens provides detailed inline mathematical tooltips
        and logs explaining statistics concepts (such as Z-score outliers, Pearson correlation coefficients, IQR, standard deviations,
        and machine learning validation metrics) directly inside the codebase and UI.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Technology stack metrics
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    t1, t2, t3, t4, t5, t6 = st.columns(6)
    t1.metric("Frontend UI", "Streamlit")
    t2.metric("Data Engine", "Pandas/NumPy")
    t3.metric("Charts",      "Plotly")
    t4.metric("AI Model",    "OpenRouter")
    t5.metric("ML AutoML",   "scikit-learn")
    t6.metric("Report PDF",  "FPDF2")
