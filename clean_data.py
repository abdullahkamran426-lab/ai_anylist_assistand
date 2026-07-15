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
        <p style='color:#94a3b8;line-height:1.75'>
        <b style='color:#fff'>DataLens</b> is an AI-powered data analysis assistant built with
        Streamlit, Pandas, Plotly, and OpenRouter. It lets you upload, clean, explore,
        visualize and interrogate CSV datasets without writing a single line of code.
        </p>
        <p style='color:#94a3b8;line-height:1.75'>
        The <b style='color:#fff'>Clean Data</b> page gives you a full interactive pipeline:
        remove duplicates, handle missing values with multiple strategies, drop or rename columns,
        cast types, and filter rows — all with a live preview and an audit log.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Technology stack metrics
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("UI",       "Streamlit")
    t2.metric("Data",     "Pandas / NumPy")
    t3.metric("Charts",   "Plotly")
    t4.metric("AI model", "OpenRouter")
