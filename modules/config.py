"""
Application Configuration Constants
This file contains all configuration constants used throughout the application.
"""

# ============================================================================
# DATA SAMPLING CONFIGURATION
# ============================================================================
# Row count above which we offer to work on a random sample instead of the full
# dataframe, so Statistics/Visualizations stay responsive on big CSVs.
LARGE_DF_THRESHOLD = 100_000


# ============================================================================
# NAVIGATION CONFIGURATION
# ============================================================================
# Navigation options - must match CSS nth-of-type selectors in styles.py
# The order is important as CSS targets specific positions for section labels
NAV_OPTIONS = [
    "🏠 Home",              # Landing page with app overview
    "📂 Upload Dataset",    # CSV upload page
    "🧹 Clean Data",        # Interactive data cleaning
    "🔍 Dataset Preview",   # View the loaded dataset
    "📊 Statistics",         # Statistical summaries
    "📈 Visualizations",    # Plotly charts
    "🤖 AI Assistant",      # AI-powered Q&A
    "📄 Export Report",     # Download PDF report
    "ℹ️ About"              # App information
]


# ============================================================================
# SESSION STATE CONFIGURATION
# ============================================================================
# Session state keys with their default values.
# Streamlit reruns the entire script on every interaction, so we use
# session_state to persist data across reruns.
SESSION_STATE_DEFAULTS = {
    "df": None,                    # Current (possibly cleaned) working dataframe
    "original_df": None,           # Untouched copy for "Reset to original" button
    "filename": None,              # Name of uploaded file (shown in sidebar/export)
    "answer": None,                # Most recent AI answer (used by Export Report page)
    "clean_log": [],               # List of cleaning actions applied (audit trail)
    "selected_chart_column": None, # Column to pre-select when redirecting to Visualizations
    "selected_chart_type": None,   # Chart type to pre-select for the same redirect
    "redirect_to": None,           # Page name to force-navigate to on next rerun
    "chat_history": [],            # List of {"q":..., "a":...} turns for AI chat UI
    "ai_prefill": "",              # Text to pre-fill AI question box (from suggestion chips)
}
