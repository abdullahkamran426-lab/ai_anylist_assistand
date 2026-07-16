"""
Home page
=========
The landing page: hero banner, feature grid, upload CTA, and a
three-step "how it works" walkthrough. Purely informational — no
dataframe is required, so this is the one page that works before
anything has been uploaded.
"""

import streamlit as st

from modules.utils import section


def render_home_page():
    """
    Render the Home page - landing page with app overview.
    This page is purely informational/marketing and doesn't require a dataframe.
    """
    # ------------------------------------------------------------------------
    # HERO BANNER
    # Big gradient banner introducing the app
    # ------------------------------------------------------------------------
    st.markdown("""
    <div class='hero'>
        <div class='hero-title'>Understand your data<br>in <span>minutes, not hours.</span></div>
        <div class='hero-sub'>
            Upload a CSV, clean it interactively, explore statistics and charts,
            then ask AI anything about your dataset — all in one place.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # FEATURE CARDS
    # Summarizing the app's capabilities in a 3-column grid (2 rows of 3 columns)
    # ------------------------------------------------------------------------
    section("CAPABILITIES", "Everything you need")
    
    # First row of features
    cols1 = st.columns(3)
    features1 = [
        ("📂", "Upload & Parse",      "Drag-and-drop CSV, TSV, JSON, Parquet, or Excel files with auto-detected encoding."),
        ("🧹", "Interactive Cleaning","Drop duplicates, fix missing values, rename/drop columns, and cast datatypes visually."),
        ("📈", "Rich Visualizations", "Bar, histogram, pie, scatter, box, violin, and correlation charts powered by Plotly."),
    ]
    for col, (icon, title, desc) in zip(cols1, features1):
        with col:
            st.markdown(f"""
            <div class='feat-card'>
                <div class='feat-icon'>{icon}</div>
                <div class='feat-title'>{title}</div>
                <div class='feat-desc'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    # Second row of features
    cols2 = st.columns(3)
    features2 = [
        ("🤖", "AI Assistant",         "Ask plain-English questions and get instant insights from OpenRouter AI (Llama 3.1)."),
        ("🔮", "AutoML Predictor",     "Train regression/classification models, evaluate performances, and run single-row predictions."),
        ("🎓", "Student Sandbox Mode",  "Interactive math tooltips, inline statistical notes (Z-scores, IQR), and model trace logs."),
    ]
    for col, (icon, title, desc) in zip(cols2, features2):
        with col:
            st.markdown(f"""
            <div class='feat-card'>
                <div class='feat-icon'>{icon}</div>
                <div class='feat-title'>{title}</div>
                <div class='feat-desc'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # CTA BUTTON
    # Prominent button to upload a dataset
    # ------------------------------------------------------------------------
    st.markdown("<div style='text-align:center;margin:32px 0'>", unsafe_allow_html=True)
    if st.button("Upload a dataset", key="home_upload_btn"):
        st.session_state.redirect_to = "📂 Upload Dataset"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # HOW IT WORKS
    # Three-step onboarding cards pointing at the relevant pages
    # ------------------------------------------------------------------------
    section("WORKFLOW", "Three steps to insight")
    s1, s2, s3 = st.columns(3)
    steps = [
        ("1", "Upload your CSV",        "Drop any tabular data file.",              "Start on the Upload page →"),
        ("2", "Clean & Explore",        "Fix nulls, remove duplicates, cast types.", "Use the Clean Data page →"),
        ("3", "Visualize & Ask AI",     "Chart your data, then interrogate it.",    "Head to AI Assistant →"),
    ]
    for col, (n, title, body, cta) in zip([s1, s2, s3], steps):
        with col:
            st.markdown(f"""
            <div class='clean-panel'>
                <div style='font-size:2rem;font-weight:800;color:rgba(99,102,241,.4);
                            font-family:Space Grotesk;margin-bottom:8px'>{n}</div>
                <div style='font-weight:700;color:#fff;font-size:1rem;margin-bottom:6px'>{title}</div>
                <div style='color:#94a3b8;font-size:.87rem;line-height:1.6;margin-bottom:10px'>{body}</div>
                <div style='color:#6366f1;font-size:.8rem;font-weight:600'>{cta}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # TECH PILLS
    # Technology stack badges
    # ------------------------------------------------------------------------
    section("STACK", "Built with")
    st.markdown("""
    <span class='pill pill-blue'>Streamlit</span>
    <span class='pill pill-blue'>Pandas</span>
    <span class='pill pill-blue'>Plotly</span>
    <span class='pill pill-blue'>OpenRouter AI</span>
    <span class='pill pill-blue'>NumPy</span>
    <span class='pill pill-blue'>scikit-learn</span>
    <span class='pill pill-blue'>joblib</span>
    <span class='pill pill-blue'>fpdf2</span>
    """, unsafe_allow_html=True)
