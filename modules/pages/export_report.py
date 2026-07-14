"""
Export Report page
==================
Lets the user download the AI Assistant's most recent answer as a
PDF report. Shows a prompt to run the AI Assistant first if no
answer has been generated yet this session.
"""

import streamlit as st

from modules.analysis import export_to_pdf
from modules.utils import section


def render_export_page():
    """
    Render the Export Report page.
    Download AI-generated analysis as a PDF report.
    """
    section("EXPORT", "Download Report")

    ans = st.session_state.get("answer")
    if not ans:
        st.markdown("""
        <div style='background:linear-gradient(135deg,rgba(34,211,165,.12) 0%,rgba(34,211,165,.03) 100%);
                    border:2px solid #22d3a5;border-radius:12px;padding:20px 24px;margin:20px 0'>
            <div style='display:flex;align-items:center;gap:12px'>
                <div style='font-size:1.5rem'>🤖</div>
                <div>
                    <div style='font-weight:700;color:#fff;font-size:1rem'>Run AI Assistant first</div>
                    <div style='color:#94a3b8;font-size:.87rem;margin-top:2px'>
                        Go to the AI Assistant page to generate content for the report.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Show preview of AI analysis
        st.markdown("""
        <div style='background:var(--card);border:1px solid var(--border);
                    border-radius:var(--radius);padding:22px;margin-bottom:24px'>
        <b style='color:#fff'>AI Analysis Preview</b><br><br>
        """ + str(ans) + "</div>", unsafe_allow_html=True)

        # Generate and download PDF
        if st.button("Generate PDF"):
            with st.spinner("Building PDF…"):
                pdf_path = export_to_pdf(ans)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇️ Download PDF",
                    f,
                    file_name=pdf_path,
                    mime="application/pdf",
                )
