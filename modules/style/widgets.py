"""
Generic Streamlit widget styling
================================
Re-skins built-in Streamlit components that appear across many pages:
st.metric(), st.button(), st.download_button(), st.dataframe(),
st.selectbox()/st.text_input()/st.text_area(), st.expander(),
st.warning()/st.error()/st.info() alerts, the page scrollbar, and
st.segmented_control() (used by the Visualizations chart-type picker).
Nothing here is specific to any one page.

This module only exports a raw CSS string — no <style> tag wrapper — so it can
be concatenated with the other styles/*.py modules by styles/__init__.py,
which wraps the combined result in a single <style>...</style> block exactly
like the original monolithic styles.py did.
"""

WIDGETS_CSS = """
/* ============================================================================
   METRIC CARDS
   Styling for st.metric() components
============================================================================ */
[data-testid="metric-container"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 18px 22px !important;
}
[data-testid="stMetricValue"] { color: var(--accent2) !important; font-weight: 700; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: .06em; }

/* ============================================================================
   BUTTONS
   Styling for st.button() components
============================================================================ */
.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.4rem !important;
    transition: opacity .15s, transform .1s !important;
}
.stButton > button:hover { opacity: .88 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }

/* Download button variant */
.stDownloadButton > button {
    background: var(--success) !important;
    color: #0f1117 !important;
    border-radius: 9px !important;
    font-weight: 700 !important;
}

/* ============================================================================
   DATAFRAME
   Styling for st.dataframe() components
============================================================================ */
[data-testid="stDataFrame"] { border-radius: var(--radius) !important; overflow: hidden; }

/* ============================================================================
   INPUT FIELDS
   Styling for selectbox, text input, and textarea components
============================================================================ */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 9px !important;
    color: var(--text) !important;
}

/* ============================================================================
   EXPANDER
   Styling for st.expander() components
============================================================================ */
details {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    margin-bottom: 10px;
}
summary { font-weight: 600; color: var(--text) !important; }

/* ============================================================================
   ALERTS
   Styling for st.warning(), st.error(), st.info() components
============================================================================ */
.stAlert { border-radius: var(--radius) !important; }


/* ============================================================================
   SCROLLBAR
   Custom scrollbar styling
============================================================================ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }


/* ============================================================================
   SEGMENTED CONTROL
   Styling for st.segmented_control() (chart type picker)
============================================================================ */
[data-testid="stSegmentedControl"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 4px !important;
}
[data-testid="stSegmentedControl"] label {
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: .88rem !important;
    color: var(--muted) !important;
}
[data-testid="stSegmentedControl"] label[aria-checked="true"],
[data-testid="stSegmentedControl"] label[data-checked="true"] {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #fff !important;
}
"""
