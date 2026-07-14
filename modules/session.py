"""
Session State Management
This file handles initialization and management of Streamlit session state.
Streamlit reruns the entire script on every interaction, so we use session_state
to persist data across reruns.
"""

import streamlit as st
from modules.config import SESSION_STATE_DEFAULTS


def initialize_session_state():
    """
    Initialize all session state variables with their default values.
    This function should be called once at the beginning of main.py.
    It only sets values if they don't already exist, preserving state across reruns.
    
    Session state variables:
    - df: Current (possibly cleaned) working dataframe
    - original_df: Untouched copy for "Reset to original" button
    - filename: Name of uploaded file (shown in sidebar/export)
    - answer: Most recent AI answer (used by Export Report page)
    - clean_log: List of cleaning actions applied (audit trail)
    - selected_chart_column: Column to pre-select when redirecting to Visualizations
    - selected_chart_type: Chart type to pre-select for the same redirect
    - redirect_to: Page name to force-navigate to on next rerun
    - chat_history: List of {"q":..., "a":...} turns for AI chat UI
    - ai_prefill: Text to pre-fill AI question box (from suggestion chips)
    """
    # Loop through all default values and initialize if not present
    for key, default in SESSION_STATE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def clear_dataset_state():
    """
    Clear all dataset-related session state.
    This is called when the user clicks "Clear dataset" in the sidebar.
    It resets the app to the state before any data was uploaded.
    """
    st.session_state.df = None
    st.session_state.original_df = None
    st.session_state.filename = None
    st.session_state.clean_log = []
    st.session_state.answer = None
    st.session_state.chat_history = []
