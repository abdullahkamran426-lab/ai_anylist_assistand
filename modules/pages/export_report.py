import streamlit as st
from modules.pdf_export import export_dataset_report
from modules.utils import section


def render_export_page():
    section("EXPORT", "Professional Dataset Report")

    df = st.session_state.get("df")

    if df is None:
        st.warning("Upload a dataset first.")
        return

    st.info("""
    Report Includes

    - Dataset Overview
    - Data Quality Score
    - Missing Values Analysis
    - Statistical Summary
    - AI Insights
    - Charts & Visualizations
    - Recommendations
    """)

    if st.button("Generate Report", type="primary"):

        with st.spinner("Creating PDF Report..."):
            try:
                pdf_path = export_dataset_report(
                    df=df,
                    ai_text=st.session_state.get("answer", "")
                )

                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Download PDF Report",
                        f,
                        file_name="DataLens_Report.pdf",
                        mime="application/pdf"
                    )
            except ValueError as e:
                st.error(f"Validation Error: {str(e)}")
            except RuntimeError as e:
                st.error(f"PDF Generation Error: {str(e)}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                st.error("Please try again or contact support if the issue persists.")
