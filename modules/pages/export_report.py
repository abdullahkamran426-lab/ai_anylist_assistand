import streamlit as st
from modules.analysis import export_dataset_report
from modules.utils import section


def render_export_page():
    section("EXPORT", "Professional Dataset Report")

    df = st.session_state.get("df")

    if df is None:
        st.warning("Upload a dataset first.")
        return

    st.info("""
    📄 Report Includes

    • Dataset Overview
    • Data Quality Score
    • Missing Values Analysis
    • Statistical Summary
    • AI Insights
    • Charts & Visualizations
    • Recommendations
    """)

    if st.button("🚀 Generate Report", use_container_width=True):

        with st.spinner("Creating PDF Report..."):
            pdf_path = export_dataset_report(
                df=df,
                ai_text=st.session_state.get("answer", "")
            )

        with open(pdf_path, "rb") as f:
            st.download_button(
                "⬇ Download PDF Report",
                f,
                file_name="DataLens_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
