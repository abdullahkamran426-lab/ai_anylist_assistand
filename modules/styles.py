"""
CSS Styling for DataLens Application
This file contains all custom CSS for the application.
Streamlit doesn't expose a rich theming API, so we inject raw CSS.
The CSS targets Streamlit's internal data-testid attributes and custom classes.
"""

import streamlit as st


def inject_css():
    """
    Injects the complete CSS stylesheet into the Streamlit application.
    Call this function once at the beginning of main.py after page config.
    """
    st.markdown(get_css(), unsafe_allow_html=True)


def get_css():
    """
    Returns the complete CSS string for the application.
    Each section is marked with comments explaining what it styles.
    """
    return """
<style>
/* ============================================================================
   FONTS
   Import Google Fonts: Inter for body text, Space Grotesk for headings
============================================================================ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;700&display=swap');

/* ============================================================================
   ROOT PALETTE - CSS Custom Properties
   Define all colors once and reuse via var(--name) throughout the app.
   Change values here to re-theme the entire application.
============================================================================ */
:root {
    --bg:        #0f1117;      /* Main background color */
    --surface:   #1a1d27;      /* Sidebar/surface background */
    --card:      #21253a;      /* Card/panel background */
    --border:    #2e3354;      /* Border color */
    --accent:    #6366f1;      /* Primary accent color */
    --accent2:   #818cf8;      /* Secondary accent color */
    --success:   #22d3a5;      /* Success/green color */
    --warning:   #fbbf24;      /* Warning/yellow color */
    --danger:    #f87171;      /* Danger/red color */
    --text:      #e2e8f0;      /* Primary text color */
    --muted:     #94a3b8;      /* Muted/secondary text color */
    --radius:    14px;         /* Default border radius */
}

/* ============================================================================
   BASE STYLES
   Apply font and background color to all elements
============================================================================ */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ============================================================================
   SIDEBAR STYLING
   The navigation is a st.radio() widget in the sidebar.
   We re-skin the radio labels into modern nav items without touching Python logic.
============================================================================ */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.4rem; }

/* Nav radio group container */
[data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] {
    gap: 3px;
}

/* Each nav item label */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    position: relative;
    display: flex !important;
    align-items: center;
    width: 100%;
    padding: 10px 14px 10px 16px !important;
    margin: 0 !important;
    border-radius: 10px;
    border: 1px solid transparent;
    background: transparent;
    cursor: pointer;
    transition: background .15s ease, border-color .15s ease, transform .1s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: var(--card);
    border-color: var(--border);
    transform: translateX(2px);
}

/* Hide the native radio dot - we show selection via background/border instead */
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child {
    display: none !important;
}

/* Label text styling */
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:last-child {
    font-size: 0.88rem;
    font-weight: 500;
    color: var(--muted);
    letter-spacing: .01em;
}

/* Selected item state - uses :has() to react to hidden radio input */
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(90deg, rgba(99,102,241,.22) 0%, rgba(99,102,241,.06) 100%);
    border-color: rgba(99,102,241,.45);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked)::before {
    content: '';
    position: absolute;
    left: -1px; top: 6px; bottom: 6px;
    width: 3px;
    border-radius: 3px;
    background: linear-gradient(180deg, var(--accent2), var(--accent));
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) > div:last-child {
    color: #fff;
    font-weight: 700;
}

/* Section group labels - injected above specific nav items
   nth-of-type targets specific positions to draw section captions */
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(3),
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(4),
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(7),
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(9) {
    margin-top: 20px !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(3)::after,
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(4)::after,
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(7)::after,
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(9)::after {
    position: absolute;
    top: -18px; left: 16px;
    font-size: .66rem;
    font-weight: 700;
    letter-spacing: .12em;
    color: #4b5065;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(3)::after { content: 'PREPARE'; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(4)::after { content: 'EXPLORE'; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(7)::after { content: 'INSIGHTS'; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(9)::after { content: 'MORE'; }

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
   HERO BAND
   Large gradient banner for landing page and section headers
============================================================================ */
.hero {
    background: linear-gradient(135deg, #1a1d27 0%, #1e2040 60%, #1a1d27 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 52px 48px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(99,102,241,.18) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    letter-spacing: -.02em;
    line-height: 1.15;
    color: #fff;
    margin: 0 0 12px;
}
.hero-title span { color: var(--accent2); }
.hero-sub { color: var(--muted); font-size: 1.05rem; max-width: 540px; line-height: 1.65; }

/* ============================================================================
   SECTION HEADERS
   Consistent heading pattern: small uppercase label + large title
============================================================================ */
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--accent2);
    margin-bottom: 4px;
}
.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.55rem;
    font-weight: 700;
    color: #fff;
    margin: 0 0 24px;
}

/* ============================================================================
   FEATURE CARDS
   Cards used on home page to showcase app capabilities
============================================================================ */
.feat-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    height: 100%;
    transition: border-color .2s;
}
.feat-card:hover { border-color: var(--accent); }
.feat-icon { font-size: 1.8rem; margin-bottom: 10px; }
.feat-title { font-weight: 700; font-size: 1rem; color: #fff; margin-bottom: 6px; }
.feat-desc { color: var(--muted); font-size: 0.87rem; line-height: 1.6; }

/* ============================================================================
   CLEAN TAG PILLS
   Small pill badges for status indicators
============================================================================ */
.pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 2px;
}
.pill-green  { background: rgba(34,211,165,.12); color: var(--success); }
.pill-yellow { background: rgba(251,191,36,.12);  color: var(--warning); }
.pill-red    { background: rgba(248,113,113,.12); color: var(--danger);  }
.pill-blue   { background: rgba(99,102,241,.12);  color: var(--accent2); }

/* ============================================================================
   STEP BADGE
   Numbered badges for workflow steps
============================================================================ */
.step {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px; height: 32px;
    background: rgba(99,102,241,.2);
    color: var(--accent2);
    border-radius: 50%;
    font-weight: 700;
    font-size: 0.85rem;
    margin-right: 10px;
    flex-shrink: 0;
}
.step-row { display: flex; align-items: flex-start; gap: 0; margin-bottom: 14px; }
.step-content { color: var(--text); font-size: 0.95rem; padding-top: 5px; }
.step-content small { display: block; color: var(--muted); font-size: 0.82rem; margin-top: 2px; }

/* ============================================================================
   CLEAN PANEL
   Panel component for cleaning tools and other sections
============================================================================ */
.clean-panel {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 26px;
    margin-bottom: 20px;
}
.clean-panel h4 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #fff;
    margin: 0 0 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ============================================================================
   DIVIDER
   Horizontal separator line
============================================================================ */
.div { border-top: 1px solid var(--border); margin: 32px 0; }

/* ============================================================================
   SCROLLBAR
   Custom scrollbar styling
============================================================================ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ============================================================================
   FILE UPLOADER DROPZONE
   Styling for st.file_uploader() component
============================================================================ */
[data-testid="stFileUploaderDropzone"] {
    background: linear-gradient(180deg, rgba(99,102,241,.06) 0%, rgba(99,102,241,.02) 100%) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: 16px !important;
    padding: 8px !important;
    transition: border-color .2s, background .2s;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--accent) !important;
    background: linear-gradient(180deg, rgba(99,102,241,.1) 0%, rgba(99,102,241,.03) 100%) !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] small {
    color: var(--muted) !important;
}
[data-testid="stFileUploaderFile"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

/* ============================================================================
   UPLOAD EMPTY STATE
   Styling for the empty state when no file is uploaded
============================================================================ */
.upload-empty {
    text-align: center;
    padding: 10px 20px 4px;
}
.upload-empty .icon {
    font-size: 2.6rem;
    margin-bottom: 6px;
    filter: drop-shadow(0 6px 18px rgba(99,102,241,.35));
}
.upload-empty .title { font-weight: 700; color: #fff; font-size: 1.05rem; margin-bottom: 4px; }
.upload-empty .desc  { color: var(--muted); font-size: .87rem; max-width: 420px; margin: 0 auto; line-height: 1.6; }

/* ============================================================================
   UPLOAD SUCCESS BANNER
   Styling for the success banner after file upload
============================================================================ */
.upload-success {
    display: flex;
    align-items: center;
    gap: 16px;
    background: linear-gradient(135deg, rgba(34,211,165,.12) 0%, rgba(34,211,165,.03) 100%);
    border: 1px solid rgba(34,211,165,.35);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin-bottom: 22px;
}
.upload-success .check {
    width: 44px; height: 44px; border-radius: 12px; flex-shrink: 0;
    background: rgba(34,211,165,.18); color: var(--success);
    display: flex; align-items: center; justify-content: center; font-size: 1.3rem;
}
.upload-success .fname { font-weight: 700; color: #fff; font-size: .98rem; word-break: break-all; }
.upload-success .fmeta { color: var(--muted); font-size: .82rem; margin-top: 2px; }

/* ============================================================================
   REQUIREMENT CHIP ROW
   Row of requirement chips for upload page
============================================================================ */
.req-row { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-top: 14px; }
.req-chip {
    display: flex; align-items: center; gap: 6px;
    background: var(--card); border: 1px solid var(--border);
    border-radius: 99px; padding: 5px 12px; font-size: .78rem; color: var(--muted);
}

/* ============================================================================
   NEXT-STEP CTA CARD
   Cards for next step suggestions
============================================================================ */
.next-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 18px;
    height: 100%;
}
.next-card .n-icon { font-size: 1.3rem; margin-bottom: 6px; }
.next-card .n-title { font-weight: 700; color: #fff; font-size: .9rem; margin-bottom: 3px; }
.next-card .n-desc { color: var(--muted); font-size: .8rem; line-height: 1.5; }

/* ============================================================================
   EXPLORE PAGES HERO STRIP
   Compact hero banner for explore pages
============================================================================ */
.explore-hero {
    background: linear-gradient(135deg, #1a1d27 0%, #1e2440 65%, #1a1d27 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 26px 30px;
    margin-bottom: 22px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.explore-hero .eh-icon {
    width: 46px; height: 46px; border-radius: 12px; flex-shrink: 0;
    background: linear-gradient(135deg, #6366f1, #818cf8);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem; box-shadow: 0 8px 20px rgba(99,102,241,.3);
}
.explore-hero .eh-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.3rem; font-weight: 700; color: #fff; }
.explore-hero .eh-sub { color: var(--muted); font-size: .84rem; margin-top: 2px; }

/* ============================================================================
   COLUMN CHIP GRID
   Grid of column detail cards for Dataset Preview page
============================================================================ */
.col-chip-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 10px; }
.col-chip {
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 14px 16px; transition: border-color .15s;
}
.col-chip:hover { border-color: var(--accent); }
.col-chip .cc-name { font-weight: 700; color: #fff; font-size: .86rem; margin-bottom: 8px; word-break: break-all; }
.col-chip .cc-type {
    display: inline-block; font-size: .66rem; font-weight: 700; padding: 2px 9px;
    border-radius: 99px; margin-bottom: 8px; letter-spacing: .03em; text-transform: uppercase;
}
.col-chip .cc-meta { color: var(--muted); font-size: .76rem; margin-top: 4px; }
.col-chip .cc-bar { background: rgba(255,255,255,.07); border-radius: 99px; height: 4px; overflow: hidden; margin-top: 8px; }
.col-chip .cc-bar-fill { height: 100%; border-radius: 99px; }
.type-num  { background: rgba(99,102,241,.16); color: #818cf8; }
.type-obj  { background: rgba(34,211,165,.16); color: #22d3a5; }
.type-date { background: rgba(251,191,36,.16); color: #fbbf24; }
.type-bool { background: rgba(248,113,113,.16); color: #f87171; }

/* ============================================================================
   STAT / ANALYSIS CARDS
   Cards for statistics and analysis panels
============================================================================ */
.stat-panel {
    background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 22px; margin-bottom: 18px;
}
.stat-panel h4 {
    font-family: 'Space Grotesk', sans-serif; font-size: .98rem; font-weight: 700;
    color: #fff; margin: 0 0 14px; display: flex; align-items: center; gap: 8px;
}
.vc-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.vc-label { width: 130px; flex-shrink: 0; font-size: .82rem; color: var(--text); word-break: break-all; }
.vc-bar-track { flex: 1; background: rgba(255,255,255,.06); border-radius: 99px; height: 10px; overflow: hidden; }
.vc-bar-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, var(--accent), var(--accent2)); }
.vc-count { width: 64px; text-align: right; font-size: .78rem; color: var(--muted); flex-shrink: 0; }

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

/* ============================================================================
   CHART OUTPUT CARD
   Card wrapper for Plotly charts
============================================================================ */
.chart-card {
    background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 18px 20px 6px; margin-top: 4px;
}
.chart-card .cc-title { color: var(--muted); font-size: .8rem; font-weight: 600; margin-bottom: 4px; }
</style>
"""
