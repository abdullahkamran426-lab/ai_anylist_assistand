"""
DataLens — AI Data Analysis Assistant
======================================
A Streamlit app that lets a user upload a CSV, clean it interactively,
explore it with stats/charts, and ask an AI questions about it.

This is the main entry point that orchestrates the application.
All business logic and page rendering is delegated to modules.
"""

import streamlit as st

# ============================================================================
# IMPORT MODULES
# Import all UI components and helper modules
# ============================================================================
from modules.styles import inject_css
from modules.session import initialize_session_state
from modules.sidebar import render_sidebar
from modules.pages import (
    render_home_page,
    render_upload_page,
    render_clean_data_page,
    render_dataset_preview_page,
    render_statistics_page,
    render_visualizations_page,
    render_ai_assistant_page,
    render_export_page,
    render_about_page,
)

# ============================================================================
# PAGE CONFIGURATION
# Must be the first Streamlit call. Sets browser tab title/icon and layout.
# ============================================================================
st.set_page_config(
    page_title="DataLens — AI Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# INJECT CSS STYLES
# Apply all custom CSS for the application
# ============================================================================
inject_css()

# ============================================================================
# INITIALIZE SESSION STATE
# Set up all session state variables with their default values
# ============================================================================
initialize_session_state()

# ============================================================================
# RENDER SIDEBAR AND GET SELECTED PAGE
# The sidebar contains navigation, dataset status, and branding
# Returns the selected page name for routing
# ============================================================================
page = render_sidebar()

# ============================================================================
# PAGE ROUTING
# Route to the appropriate page function based on sidebar selection
# Pages that require data are guarded by a common check
# ============================================================================

# ------------------------------------------------------------------------
# HOME PAGE
# Landing page - no data required
# ------------------------------------------------------------------------
if page == "🏠 Home":
    render_home_page()

# ------------------------------------------------------------------------
# UPLOAD PAGE
# Entry point for uploading data - no data required
# ------------------------------------------------------------------------
elif page == "📂 Upload Dataset":
    render_upload_page()

# ------------------------------------------------------------------------
# CLEAN DATA PAGE
# Interactive data cleaning - requires data
# ------------------------------------------------------------------------
elif page == "🧹 Clean Data":
    df = st.session_state.df
    if df is None:
        st.warning("Upload a dataset first.")
        st.stop()
    render_clean_data_page()

# ------------------------------------------------------------------------
# ALL OTHER PAGES REQUIRE DATA
# Common guard clause for data-required pages
# ------------------------------------------------------------------------
else:
    df = st.session_state.df

    if df is None:
        st.warning("Upload a dataset first.")
        st.stop()

    # --------------------------------------------------------------------
    # DATASET PREVIEW PAGE
    # View the loaded dataset with column details
    # --------------------------------------------------------------------
    if page == "🔍 Dataset Preview":
        render_dataset_preview_page()

    # --------------------------------------------------------------------
    # STATISTICS PAGE
    # Statistical summaries and analysis
    # --------------------------------------------------------------------
    elif page == "📊 Statistics":
        render_statistics_page()

    # --------------------------------------------------------------------
    # VISUALIZATIONS PAGE
    # Plotly charts (bar, histogram, pie, scatter)
    # --------------------------------------------------------------------
    elif page == "📈 Visualizations":
        render_visualizations_page()

    # --------------------------------------------------------------------
    # AI ASSISTANT PAGE
    # Natural-language Q&A with AI
    # --------------------------------------------------------------------
    elif page == "🤖 AI Assistant":
        render_ai_assistant_page()

    # --------------------------------------------------------------------
    # EXPORT PAGE
    # Download AI-generated PDF report
    # --------------------------------------------------------------------
    elif page == "📄 Export Report":
        render_export_page()

    # --------------------------------------------------------------------
    # ABOUT PAGE
    # App information and technology stack
    # --------------------------------------------------------------------
    elif page == "ℹ️ About":
        render_about_page()
