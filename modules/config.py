"""
App-wide Configuration Constants
==================================
"""

# ----------------------------------------------------------------------------
# NAVIGATION
# Master list of pages, in sidebar display order.
#
# IMPORTANT: modules/style/sidebar.py's CSS uses :nth-of-type(3), (4), (7),
# and (9) to draw the PREPARE / EXPLORE / INSIGHTS / MORE section-group labels
# above specific nav items. Those positions assume THIS exact order:
#   3 = Clean Data (PREPARE), 4 = Dataset Preview (EXPLORE),
#   7 = AI Assistant (INSIGHTS), 9 = About (MORE).
# If you reorder this list, update those nth-of-type selectors to match.
# ----------------------------------------------------------------------------
NAV_OPTIONS = [
    "🏠 Home",
    "📂 Upload Dataset",
    "🧹 Clean Data",
    "🔍 Dataset Preview",
    "📊 Statistics",
    "📈 Visualizations",
    "🤖 AI Assistant",
    "📄 Export Report",
    "ℹ️ About",
]

# ----------------------------------------------------------------------------
# SESSION STATE DEFAULTS
# Every key the app relies on across reruns, seeded once by
# modules.session.initialize_session_state().
# ----------------------------------------------------------------------------
SESSION_STATE_DEFAULTS = {
    "df": None,                    # the current (possibly cleaned) working dataframe
    "original_df": None,           # untouched copy, used by the "Reset to original" button
    "filename": None,              # name of the uploaded file, shown in the sidebar/export
    "answer": None,                # most recent AI answer, used by the Export Report page
    "clean_log": [],               # human-readable list of cleaning actions applied so far
    "selected_chart_column": None, # column to pre-select when Statistics redirects to Visualizations
    "selected_chart_type": None,   # chart type to pre-select for the same redirect
    "redirect_to": None,           # page name to force-navigate to on the next rerun
    "chat_history": [],            # list of {"q":..., "a":...} turns for the AI chat UI
    "ai_prefill": "",              # text to pre-fill the AI question box (from a suggestion chip)
}

# ----------------------------------------------------------------------------
# DATA HANDLING
# Row count above which we offer to work on a random sample instead of the
# full dataframe, so Statistics/Visualizations stay responsive on big CSVs.
# ----------------------------------------------------------------------------
LARGE_DF_THRESHOLD = 100_000
