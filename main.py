"""
DataLens — AI Data Analysis Assistant
======================================
A Streamlit app that lets a user upload a CSV, clean it interactively,
explore it with stats/charts, and ask an AI questions about it.

Page flow (controlled by the sidebar radio in `page`):
    Home → Upload Dataset → Clean Data → Dataset Preview / Statistics /
    Visualizations → AI Assistant → Export Report → About

All page state (the loaded dataframe, chat history, chart selections, etc.)
lives in `st.session_state` so it survives Streamlit's rerun-on-every-
interaction model.
"""

import streamlit as st            # the web app framework that renders every widget on the page
import pandas as pd                # dataframe engine used for all data manipulation
import numpy as np                 # numeric helpers (currently only needed indirectly via pandas)

# Project-local modules: business logic is kept out of this UI file on purpose,
# so main.py only orchestrates *what* happens, not *how*.
from analysis import load_data, clean_data, get_summary, get_numeric_stats, get_category_counts, export_to_pdf
from visualization import plot_bar, plot_histogram, plot_pie, plot_scatter
from ai_helper import ask_ai

# ── Page config ────────────────────────────────────────────────────────────────
# Must be the first Streamlit call in the script. Sets the browser tab title/icon
# and switches the app to a wide, full-width layout instead of the default centered one.
st.set_page_config(
    page_title="DataLens — AI Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",   # sidebar starts open instead of collapsed
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
# Streamlit doesn't expose a theming API rich enough for a fully custom look, so we
# inject raw CSS once here. Everything below targets Streamlit's internal
# `data-testid` attributes (stable across widget types) or our own custom classes
# used inside st.markdown(..., unsafe_allow_html=True) calls further down the file.
# Each `/* ── Section ── */` comment marks one visual area of the app.
st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;700&display=swap');

/* ── Root palette ──
   CSS custom properties (variables) so every color in the app is defined once
   and reused everywhere via var(--name). Change a value here to re-theme the whole app. */
:root {
    --bg:        #0f1117;
    --surface:   #1a1d27;
    --card:      #21253a;
    --border:    #2e3354;
    --accent:    #6366f1;
    --accent2:   #818cf8;
    --success:   #22d3a5;
    --warning:   #fbbf24;
    --danger:    #f87171;
    --text:      #e2e8f0;
    --muted:     #94a3b8;
    --radius:    14px;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ── Sidebar ──
   The page navigation is a plain st.radio() widget in the sidebar (see the
   Python code below). Streamlit renders radio options as <label> elements
   containing a hidden native radio dot + a text div. All the CSS below
   re-skins those labels into a modern "nav item" list without touching
   any Python logic. */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.4rem; }

/* Nav radio group container */
[data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] {
    gap: 3px;
}

/* Each nav item */
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

/* Hide the native radio dot — we show selection state via background/border instead */
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child {
    display: none !important;
}

/* Label text */
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:last-child {
    font-size: 0.88rem;
    font-weight: 500;
    color: var(--muted);
    letter-spacing: .01em;
}

/* Selected item — :has() lets pure CSS react to the hidden radio input's checked
   state without any JavaScript or Streamlit component. */
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

/* Section group labels, injected above specific nav items.
   nth-of-type(N) targets the Nth radio option by its fixed position in the
   `_nav_options` list below (3 = Clean Data, 4 = Dataset Preview, 7 = AI
   Assistant, 9 = About) and draws a small uppercase caption above it via
   ::after, purely visual grouping — no extra widgets needed. */
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

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 18px 22px !important;
}
[data-testid="stMetricValue"] { color: var(--accent2) !important; font-weight: 700; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: .06em; }

/* ── Buttons ── */
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

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: var(--radius) !important; overflow: hidden; }

/* ── Selectbox / Text input ── */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 9px !important;
    color: var(--text) !important;
}

/* ── Expander ── */
details {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    margin-bottom: 10px;
}
summary { font-weight: 600; color: var(--text) !important; }

/* ── Alerts ── */
.stAlert { border-radius: var(--radius) !important; }

/* ── Hero band ── */
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

/* ── Section headers ── */
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

/* ── Feature card ── */
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

/* ── Clean tag pills ── */
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

/* ── Step badge ── */
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

/* ── Clean panel ── */
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

/* ── Divider ── */
.div { border-top: 1px solid var(--border); margin: 32px 0; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── File uploader dropzone ── */
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

/* ── Upload empty-state ── */
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

/* ── Upload success banner ── */
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

/* ── Requirement chip row ── */
.req-row { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-top: 14px; }
.req-chip {
    display: flex; align-items: center; gap: 6px;
    background: var(--card); border: 1px solid var(--border);
    border-radius: 99px; padding: 5px 12px; font-size: .78rem; color: var(--muted);
}

/* ── Next-step CTA card ── */
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

/* ── Explore pages: hero strip ── */
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

/* ── Column chip grid (Dataset Preview → Column Details) ── */
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

/* ── Stat / analysis cards ── */
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

/* ── Segmented control (chart type picker) ── */
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

/* ── Chart output card ── */
.chart-card {
    background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 18px 20px 6px; margin-top: 4px;
}
.chart-card .cc-title { color: var(--muted); font-size: .8rem; font-weight: 600; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Large-data helpers ─────────────────────────────────────────────────────────
# Row count above which we offer to work on a random sample instead of the full
# dataframe, so Statistics/Visualizations stay responsive on big CSVs.
LARGE_DF_THRESHOLD = 100_000

def sample_df_for_speed(frame: pd.DataFrame, enabled: bool, n: int = 50_000) -> pd.DataFrame:
    """Return a random sample of `frame` when enabled and it's large; otherwise the frame itself.

    Args:
        frame:   the dataframe to (maybe) sample.
        enabled: whether the user has opted into sampling (checkbox on the page).
        n:       max rows to keep when sampling.
    A fixed `random_state=42` keeps the sample identical across reruns, so
    numbers don't visibly jump around every time a widget is touched.
    """
    if enabled and len(frame) > n:
        return frame.sample(n, random_state=42)
    return frame

# ── Session state ──────────────────────────────────────────────────────────────
# Streamlit reruns this whole script top-to-bottom on every widget interaction,
# so anything that must persist across reruns (the loaded data, chat log, which
# page to jump to next, etc.) is stored in st.session_state instead of a normal
# Python variable. This loop seeds every key with a default exactly once —
# `if key not in st.session_state` stops it from wiping existing values on rerun.
for key, default in {
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
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ────────────────────────────────────────────────────────────────────
# Everything inside this `with` block renders in the left sidebar column.
with st.sidebar:
    # Logo + app name + a small pulsing "AI Analysis" status dot (pure CSS animation
    # defined inline here since it's only used once).
    st.markdown("""
    <style>
    @keyframes pulse-dot { 0%,100% { opacity:1; } 50% { opacity:.35; } }
    </style>
    <div style='display:flex;align-items:center;gap:12px;padding:6px 2px 22px'>
        <div style='width:40px;height:40px;border-radius:11px;flex-shrink:0;
                    background:linear-gradient(135deg,#6366f1,#818cf8);
                    display:flex;align-items:center;justify-content:center;
                    font-size:1.15rem;box-shadow:0 6px 18px rgba(99,102,241,.35)'>🔬</div>
        <div>
            <div style='font-family:Space Grotesk;font-size:1.15rem;font-weight:700;
                        color:#fff;line-height:1.1'>DataLens</div>
            <div style='display:flex;align-items:center;gap:5px;margin-top:2px'>
                <span style='width:6px;height:6px;border-radius:50%;background:#22d3a5;
                            display:inline-block;animation:pulse-dot 2s infinite'></span>
                <span style='color:#64748b;font-size:.68rem;font-weight:600;
                            letter-spacing:.08em;text-transform:uppercase'>AI Analysis</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # The master list of pages, in display order. The CSS `nth-of-type` rules above
    # rely on this exact order (items 3, 4, 7, 9) to draw section group labels —
    # if you reorder this list, update the CSS selectors to match.
    _nav_options = ["🏠 Home", "📂 Upload Dataset", "🧹 Clean Data",
                     "🔍 Dataset Preview", "📊 Statistics",
                     "📈 Visualizations", "🤖 AI Assistant",
                     "📄 Export Report", "ℹ️ About"]

    # Cross-page navigation trick: other pages (e.g. Statistics) can set
    # st.session_state.redirect_to to a page name and call st.rerun() to force
    # the sidebar radio to open on that page next render. We consume it once
    # here (read it into _default_index, then clear it) so it doesn't keep
    # forcing that page on every future rerun — normal manual navigation
    # resumes immediately after.
    _default_index = 0
    if st.session_state.redirect_to in _nav_options:
        _default_index = _nav_options.index(st.session_state.redirect_to)
        st.session_state.redirect_to = None

    # The actual navigation control. Its visible label is hidden (collapsed)
    # because the logo block above already establishes context; all the pill/
    # highlight styling comes from the CSS block earlier in the file.
    page = st.radio(
        "Navigation",
        _nav_options,
        index=_default_index,
        label_visibility="collapsed",
    )

    # ── Dataset status badge ──
    # Only shown once a file has been uploaded. Gives an at-a-glance summary of
    # what's loaded and a rough "data health" score (% of cells that are NOT
    # missing) so the user doesn't have to visit Statistics just to check.
    if st.session_state.df is not None:
        df_info = st.session_state.df
        total_cells = df_info.shape[0] * df_info.shape[1]
        missing_cells = int(df_info.isna().sum().sum())
        # Guard against division by zero for an empty dataframe.
        health_pct = 100 if total_cells == 0 else round(100 - (missing_cells / total_cells * 100), 1)
        # Traffic-light coloring: green when mostly complete, amber when patchy, red when sparse.
        health_color = "#22d3a5" if health_pct >= 90 else ("#fbbf24" if health_pct >= 70 else "#f87171")

        st.markdown("<div class='div' style='margin:18px 0 14px'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,rgba(99,102,241,.12) 0%,rgba(99,102,241,.03) 100%);
                    border:1px solid rgba(99,102,241,.3);border-radius:12px;padding:16px;'>
            <div style='display:flex;align-items:center;gap:8px;margin-bottom:10px'>
                <span style='font-size:.95rem'>📁</span>
                <span style='font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;
                            color:#818cf8;font-weight:700'>Active Dataset</span>
            </div>
            <div style='color:#e2e8f0;font-weight:600;font-size:.87rem;
                        word-break:break-all;margin-bottom:8px'>{st.session_state.filename}</div>
            <div style='color:#94a3b8;font-size:.78rem;margin-bottom:10px'>
                {df_info.shape[0]:,} rows &nbsp;·&nbsp; {df_info.shape[1]} columns
            </div>
            <div style='display:flex;justify-content:space-between;font-size:.7rem;
                        color:#64748b;margin-bottom:4px'>
                <span>Data health</span><span style='color:{health_color};font-weight:700'>{health_pct}%</span>
            </div>
            <div style='background:rgba(255,255,255,.06);border-radius:99px;height:5px;overflow:hidden'>
                <div style='width:{health_pct}%;height:100%;background:{health_color};border-radius:99px'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Wipes every piece of state tied to the current dataset so the app
        # behaves as if nothing was ever uploaded, then reruns to reflect it.
        if st.button("🗑️ Clear dataset", key="clear_dataset", use_container_width=True):
            st.session_state.df = None
            st.session_state.original_df = None
            st.session_state.filename = None
            st.session_state.clean_log = []
            st.session_state.answer = None
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='color:#4b5065;font-size:.68rem;text-align:center;letter-spacing:.03em'>
        DataLens · Streamlit + Plotly + AI
    </div>
    """, unsafe_allow_html=True)

# ── Helper: section header ─────────────────────────────────────────────────────
def section(label: str, title: str):
    """Render the small-uppercase-eyebrow + large-title heading pattern used
    at the top of most pages (e.g. label='ANALYSIS', title='Statistical Summary').
    Kept as a function so every page gets an identical, consistently-styled heading."""
    st.markdown(f"<div class='section-label'>{label}</div>"
                f"<div class='section-title'>{title}</div>",
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HOME
# The landing page. Purely informational/marketing — no dataframe is required
# here, so it's the one page that works before anything is uploaded.
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    # Big gradient banner introducing the app.
    st.markdown("""
    <div class='hero'>
        <div class='hero-title'>Understand your data<br>in <span>minutes, not hours.</span></div>
        <div class='hero-sub'>
            Upload a CSV, clean it interactively, explore statistics and charts,
            then ask AI anything about your dataset — all in one place.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature cards ── four-column grid summarizing the app's capabilities.
    section("CAPABILITIES", "Everything you need")
    cols = st.columns(4)
    features = [
        ("📂", "Upload & Parse",      "Drag-and-drop any CSV file. Instant preview with auto-detection."),
        ("🧹", "Interactive Cleaning","Drop duplicates, fix nulls, rename columns, cast types — visually."),
        ("📈", "Rich Visualisations", "Bar, histogram, pie and scatter charts powered by Plotly."),
        ("🤖", "AI Insights",         "Ask plain-English questions. Get instant answers from OpenRouter AI."),
    ]
    # zip() pairs each Streamlit column with its matching feature tuple so we
    # can loop once instead of writing four nearly-identical blocks.
    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(f"""
            <div class='feat-card'>
                <div class='feat-icon'>{icon}</div>
                <div class='feat-title'>{title}</div>
                <div class='feat-desc'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ── How it works ── three-step onboarding cards pointing at the relevant pages.
    section("WORKFLOW", "Three steps to insight")
    s1, s2, s3 = st.columns(3)
    steps = [
        ("1", "Upload your CSV",        "Drop any comma-separated file.",           "Start on the Upload page →"),
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

    # ── Tech pills ──
    section("STACK", "Built with")
    st.markdown("""
    <span class='pill pill-blue'>Streamlit</span>
    <span class='pill pill-blue'>Pandas</span>
    <span class='pill pill-blue'>Plotly</span>
    <span class='pill pill-blue'>OpenRouter AI</span>
    <span class='pill pill-blue'>NumPy</span>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD
# Entry point for getting data into the app. Reads the CSV, runs it through
# the auto-clean pipeline (analysis.clean_data), and stores the result in
# session_state so every other page can read st.session_state.df.
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📂 Upload Dataset":
    st.markdown("""
    <div class='hero' style='padding:40px 44px;margin-bottom:28px'>
        <div class='hero-title' style='font-size:2rem'>Bring in your <span>dataset</span></div>
        <div class='hero-sub'>Drop a CSV below. We'll auto-detect types, strip stray whitespace,
        and get it ready for cleaning and analysis — all in a couple of seconds.</div>
    </div>
    """, unsafe_allow_html=True)

    # The actual upload widget. `type=["csv"]` restricts the file picker/drop
    # target to .csv files only. Returns None until a file is chosen.
    uploaded = st.file_uploader(
        "Drop a CSV file here or click to browse",
        type=["csv"],
        help="Only CSV files are supported.",
        label_visibility="collapsed",
    )

    # Nothing uploaded yet → show a friendly empty state instead of a blank page.
    if not uploaded:
        st.markdown("""
        <div class='upload-empty'>
            <div class='icon'>📄</div>
            <div class='title'>No file selected yet</div>
            <div class='desc'>Drag a .csv file into the box above, or click it to browse your computer.</div>
            <div class='req-row'>
                <div class='req-chip'>📐 Comma-separated</div>
                <div class='req-chip'>🔤 UTF-8 or CP1252</div>
                <div class='req-chip'>🚀 Cached for speed</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if uploaded:
        # `.getvalue()` returns the raw file bytes. We pass bytes (not the
        # UploadedFile object) into load_data() because that function is
        # decorated with @st.cache_data in analysis.py, and cache keys must
        # be hashable — bytes are, file-like objects aren't.
        with st.spinner("Reading and auto-cleaning…"):
            raw_df = load_data(uploaded.getvalue())
            df = clean_data(raw_df)   # baseline auto-clean: trims whitespace, drops exact duplicate rows, etc.

        # Persist the freshly-loaded data for every other page to use.
        st.session_state.df = df
        st.session_state.original_df = df.copy()   # untouched snapshot for the "Reset" button on Clean Data
        st.session_state.filename = uploaded.name
        st.session_state.clean_log = ["✅ Initial auto-clean applied (whitespace stripped, obvious duplicates removed)"]

        # Human-readable file size (KB below 1MB, MB above).
        size_kb = len(uploaded.getvalue()) / 1024
        size_txt = f"{size_kb:,.1f} KB" if size_kb < 1024 else f"{size_kb/1024:,.2f} MB"

        st.markdown(f"""
        <div class='upload-success'>
            <div class='check'>✓</div>
            <div>
                <div class='fname'>{uploaded.name}</div>
                <div class='fmeta'>{size_txt} · {df.shape[0]:,} rows · {df.shape[1]} columns · loaded successfully</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Quick at-a-glance KPIs for the freshly loaded data.
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows",            f"{df.shape[0]:,}")
        c2.metric("Columns",         df.shape[1])
        c3.metric("Missing cells",   int(df.isna().sum().sum()))
        c4.metric("Duplicate rows",  int(df.duplicated().sum()))

        st.markdown("<div class='div'></div>", unsafe_allow_html=True)

        # Two views into the data: a row preview, and a per-column dtype summary.
        prev_tab, types_tab = st.tabs(["👁️ Preview", "🧬 Column types"])
        with prev_tab:
            st.dataframe(df.head(10), use_container_width=True)
        with types_tab:
            dtype_df = df.dtypes.rename("Type").astype(str).to_frame()
            dtype_df["Nulls"] = df.isna().sum()
            dtype_df["Unique values"] = df.nunique()
            st.dataframe(dtype_df, use_container_width=True)

        st.markdown("<div class='div'></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>NEXT UP</div>", unsafe_allow_html=True)

        # "What next?" shortcut cards. Each "Go →" button uses the same
        # redirect_to session-state trick as the Statistics→Visualizations
        # jump, so clicking it takes the user straight to that page.
        n1, n2, n3 = st.columns(3)
        next_steps = [
            (n1, "🧹", "Clean it up", "Handle nulls, duplicates & types.", "🧹 Clean Data"),
            (n2, "📊", "Check the stats", "Numeric summaries & missing values.", "📊 Statistics"),
            (n3, "🤖", "Ask the AI", "Get instant plain-English insights.", "🤖 AI Assistant"),
        ]
        for col, icon, title, desc, target in next_steps:
            with col:
                st.markdown(f"""
                <div class='next-card'>
                    <div class='n-icon'>{icon}</div>
                    <div class='n-title'>{title}</div>
                    <div class='n-desc'>{desc}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Go →", key=f"go_{target}", use_container_width=True):
                    st.session_state.redirect_to = target
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# CLEAN DATA  (new feature)
# The interactive cleaning pipeline. Every control here mutates `df`, saves it
# back into st.session_state.df, appends a message to clean_log, then calls
# st.rerun() to redraw the page with the updated data — this is the standard
# Streamlit pattern for "apply an edit and refresh immediately".
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧹 Clean Data":
    df = st.session_state.df
    if df is None:
        # Guard: this page is meaningless without data, so bail out early.
        st.warning("Upload a dataset first.")
        st.stop()

    section("DATA CLEANING", "Fix, reshape & prepare")

    # ── Before/after KPIs ──
    # `orig` is the untouched copy saved at upload time; comparing against it
    # lets st.metric() show a delta (e.g. "-12 rows") next to the current value.
    orig = st.session_state.original_df
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Current rows",    f"{df.shape[0]:,}",  f"{df.shape[0]-orig.shape[0]:,}" if orig is not None else None)
    col_b.metric("Missing cells",   int(df.isna().sum().sum()),
                 f"{int(df.isna().sum().sum()) - int(orig.isna().sum().sum())}" if orig is not None else None)
    col_c.metric("Duplicate rows",  int(df.duplicated().sum()))
    col_d.metric("Columns",         df.shape[1])

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ── Download cleaned dataset ──
    # Encode the current (possibly cleaned) dataframe to CSV bytes once, up
    # front, so both download buttons below (top banner + bottom shortcut)
    # can reuse the same `csv_bytes`/`clean_filename` without recomputing.
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    clean_filename = f"cleaned_{st.session_state.filename or 'dataset.csv'}"
    if not clean_filename.lower().endswith(".csv"):
        clean_filename += ".csv"

    dl_col1, dl_col2 = st.columns([3, 1])
    with dl_col1:
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,rgba(34,211,165,.12) 0%,rgba(34,211,165,.03) 100%);
                    border:1px solid rgba(34,211,165,.35);border-radius:var(--radius);
                    padding:16px 20px;display:flex;align-items:center;gap:14px;height:100%'>
            <div style='width:38px;height:38px;border-radius:10px;flex-shrink:0;
                        background:rgba(34,211,165,.18);color:var(--success);
                        display:flex;align-items:center;justify-content:center;font-size:1.1rem'>⬇️</div>
            <div>
                <div style='color:#fff;font-weight:700;font-size:.9rem'>Cleaned dataset ready</div>
                <div style='color:#94a3b8;font-size:.8rem'>
                    {df.shape[0]:,} rows · {df.shape[1]} columns · {len(st.session_state.clean_log)} step(s) applied
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with dl_col2:
        st.markdown("<div style='height:100%;display:flex;align-items:center'>", unsafe_allow_html=True)
        st.download_button(
            "⬇️ Download CSV",
            data=csv_bytes,
            file_name=clean_filename,
            mime="text/csv",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ── Left: controls   Right: live preview ──
    # Two-column layout: every cleaning tool lives in the narrower left column,
    # while the wider right column always mirrors the current state of `df`.
    ctrl, prev = st.columns([1, 1.6], gap="large")

    with ctrl:
        # 1. Duplicate rows — detect exact row-level duplicates and offer a one-click removal.
        st.markdown("<div class='clean-panel'><h4>🔂 Duplicate Rows</h4>", unsafe_allow_html=True)
        dup_count = int(df.duplicated().sum())
        st.markdown(f"<span class='pill pill-{'red' if dup_count else 'green'}'>"
                    f"{'⚠️ ' if dup_count else '✅ '}{dup_count} duplicate{'s' if dup_count!=1 else ''}</span>",
                    unsafe_allow_html=True)
        if dup_count and st.button("Remove duplicates", key="rm_dup"):
            df = df.drop_duplicates().reset_index(drop=True)  # reset_index keeps row numbers contiguous after dropping
            st.session_state.df = df
            st.session_state.clean_log.append(f"✅ Removed {dup_count} duplicate rows")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 2. Missing values — per-column strategy picker (drop / mean / median / mode / constant).
        missing_cols = df.columns[df.isna().any()].tolist()
        st.markdown("<div class='clean-panel'><h4>❓ Missing Values</h4>", unsafe_allow_html=True)
        if not missing_cols:
            st.markdown("<span class='pill pill-green'>✅ No missing values</span>", unsafe_allow_html=True)
        else:
            # Show one pill per affected column so the user can see the scope
            # of the problem before deciding on a fix.
            for col in missing_cols:
                cnt = int(df[col].isna().sum())
                pct = cnt / len(df) * 100
                st.markdown(f"<span class='pill pill-yellow'>⚠️ {col}: {cnt} ({pct:.1f}%)</span>",
                            unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            mv_col   = st.selectbox("Column", missing_cols, key="mv_col")
            mv_strat = st.selectbox("Strategy", ["Drop rows", "Fill with mean",
                                                  "Fill with median", "Fill with mode",
                                                  "Fill with constant"], key="mv_strat")
            mv_const = ""
            if mv_strat == "Fill with constant":
                mv_const = st.text_input("Constant value", key="mv_const")

            if st.button("Apply", key="apply_mv"):
                col_data = df[mv_col]
                before   = int(col_data.isna().sum())
                # Each branch below implements one strategy. Mean/median only
                # make sense for numeric columns, so they're guarded by a
                # dtype check; if the check fails the final `else` reports
                # that the strategy was skipped instead of silently no-op'ing.
                if mv_strat == "Drop rows":
                    df = df.dropna(subset=[mv_col]).reset_index(drop=True)
                    msg = f"✅ Dropped {before} rows with nulls in '{mv_col}'"
                elif mv_strat == "Fill with mean" and pd.api.types.is_numeric_dtype(col_data):
                    df[mv_col] = col_data.fillna(col_data.mean())
                    msg = f"✅ Filled '{mv_col}' nulls with mean ({col_data.mean():.4g})"
                elif mv_strat == "Fill with median" and pd.api.types.is_numeric_dtype(col_data):
                    df[mv_col] = col_data.fillna(col_data.median())
                    msg = f"✅ Filled '{mv_col}' nulls with median ({col_data.median():.4g})"
                elif mv_strat == "Fill with mode":
                    mode_val = col_data.mode()[0]   # most frequent value; works for numeric or text columns
                    df[mv_col] = col_data.fillna(mode_val)
                    msg = f"✅ Filled '{mv_col}' nulls with mode ({mode_val})"
                elif mv_strat == "Fill with constant" and mv_const != "":
                    try:
                        # Coerce the typed-in text to a number when the target
                        # column is numeric, so we don't turn an int column into
                        # an object column just by filling with "0" (a string).
                        fill = float(mv_const) if pd.api.types.is_numeric_dtype(col_data) else mv_const
                    except ValueError:
                        fill = mv_const
                    df[mv_col] = col_data.fillna(fill)
                    msg = f"✅ Filled '{mv_col}' nulls with '{fill}'"
                else:
                    msg = "⚠️ Strategy not applicable to column type — skipped."
                st.session_state.df = df
                st.session_state.clean_log.append(msg)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 3. Drop columns — remove one or more columns entirely (e.g. IDs, free-text noise).
        st.markdown("<div class='clean-panel'><h4>🗑️ Drop Columns</h4>", unsafe_allow_html=True)
        drop_cols = st.multiselect("Select columns to drop", df.columns.tolist(), key="drop_cols")
        if drop_cols and st.button("Drop selected", key="apply_drop"):
            df = df.drop(columns=drop_cols)
            st.session_state.df = df
            st.session_state.clean_log.append(f"✅ Dropped columns: {', '.join(drop_cols)}")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 4. Rename column — simple find/replace on a single column header.
        st.markdown("<div class='clean-panel'><h4>✏️ Rename Column</h4>", unsafe_allow_html=True)
        ren_from = st.selectbox("Column to rename", df.columns.tolist(), key="ren_from")
        ren_to   = st.text_input("New name", key="ren_to")
        if st.button("Rename", key="apply_rename") and ren_to:
            df = df.rename(columns={ren_from: ren_to})
            st.session_state.df = df
            st.session_state.clean_log.append(f"✅ Renamed '{ren_from}' → '{ren_to}'")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 5. Cast dtype — force a column to int/float/str/datetime.
        st.markdown("<div class='clean-panel'><h4>🔁 Change Column Type</h4>", unsafe_allow_html=True)
        cast_col   = st.selectbox("Column", df.columns.tolist(), key="cast_col")
        cast_dtype = st.selectbox("Target type", ["int", "float", "str", "datetime"], key="cast_dtype")
        if st.button("Cast", key="apply_cast"):
            try:
                # Datetime needs pd.to_datetime (astype("datetime") doesn't parse
                # strings); errors="coerce" turns unparseable values into NaT
                # instead of raising, so one bad row doesn't kill the whole cast.
                if cast_dtype == "datetime":
                    df[cast_col] = pd.to_datetime(df[cast_col], errors="coerce")
                else:
                    df[cast_col] = df[cast_col].astype(cast_dtype)
                st.session_state.df = df
                st.session_state.clean_log.append(f"✅ Cast '{cast_col}' to {cast_dtype}")
            except Exception as exc:
                # e.g. casting "abc" to int — surface the real pandas error to the user.
                st.error(f"Could not cast: {exc}")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 6. Filter rows — keep only rows matching a simple numeric comparison.
        st.markdown("<div class='clean-panel'><h4>🔍 Filter Rows</h4>", unsafe_allow_html=True)
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if num_cols:
            flt_col = st.selectbox("Numeric column", num_cols, key="flt_col")
            flt_op  = st.selectbox("Operator", [">", ">=", "<", "<=", "==", "!="], key="flt_op")
            flt_val = st.number_input("Value", key="flt_val")
            if st.button("Apply filter", key="apply_flt"):
                before = len(df)
                # Build a pandas query string like "`age` >= 18" and evaluate it.
                # Backticks around the column name protect against spaces/special
                # characters in the header.
                expr   = f"`{flt_col}` {flt_op} {flt_val}"
                df     = df.query(expr).reset_index(drop=True)
                st.session_state.df = df
                st.session_state.clean_log.append(
                    f"✅ Filter '{flt_col} {flt_op} {flt_val}' kept {len(df):,}/{before:,} rows")
                st.rerun()
        else:
            st.caption("No numeric columns available.")
        st.markdown("</div>", unsafe_allow_html=True)

        # 7. Reset & Download — undo everything back to the original upload,
        # or grab the CSV as it stands right now (mirrors the top banner button).
        st.markdown("<div class='div'></div>", unsafe_allow_html=True)
        rc1, rc2 = st.columns(2)
        with rc1:
            if st.button("↩️ Reset to original", key="reset_clean", use_container_width=True):
                st.session_state.df = st.session_state.original_df.copy()
                st.session_state.clean_log = ["↩️ Reset to original dataset"]
                st.rerun()
        with rc2:
            st.download_button(
                "⬇️ Download CSV",
                data=csv_bytes,
                file_name=clean_filename,
                mime="text/csv",
                key="dl_csv_bottom",
                use_container_width=True,
            )

    with prev:
        # Right-hand column: always reflects the *current* `df`, so every
        # button click on the left is visible here immediately after the rerun.
        st.markdown("#### Live Preview")
        st.dataframe(df.head(50), use_container_width=True, height=340)

        # Missing-value heatmap summary — a compact table of just the columns
        # that still have nulls, built as a small pandas method chain:
        # count nulls → rename → to a DataFrame → add a Pct column → keep only rows with Missing > 0.
        if df.isna().any().any():
            st.markdown("#### Missing-value breakdown")
            miss = (df.isna().sum()
                      .rename("Missing")
                      .to_frame()
                      .assign(Pct=lambda d: (d["Missing"]/len(df)*100).round(2))
                      .query("Missing > 0"))
            st.dataframe(miss, use_container_width=True)

        # Clean log — running audit trail of every action applied this
        # session, newest first, so the user can see exactly what happened.
        if st.session_state.clean_log:
            st.markdown("#### Cleaning log")
            for entry in reversed(st.session_state.clean_log):
                st.markdown(f"<small style='color:#94a3b8'>{entry}</small>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Guard — all remaining pages need a loaded dataframe
# Dataset Preview, Statistics, Visualizations, AI Assistant and Export Report
# all share this single `else` branch and the same "no data → warn and stop"
# check, so it only needs to be written once instead of on every page.
# ══════════════════════════════════════════════════════════════════════════════
else:
    df = st.session_state.df
    if df is None:
        st.warning("Upload a dataset first.")
        st.stop()

    # ── Dataset Preview ──────────────────────────────────────────────────────
    # Read-only exploration of the raw table: a searchable data grid, plus a
    # per-column "profile card" view (type, uniqueness, missingness).
    if page == "🔍 Dataset Preview":
        st.markdown(f"""
        <div class='explore-hero'>
            <div class='eh-icon'>🔍</div>
            <div>
                <div class='eh-title'>Dataset Preview</div>
                <div class='eh-sub'>{st.session_state.filename} · {df.shape[0]:,} rows · {df.shape[1]} columns</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows",          f"{df.shape[0]:,}")
        c2.metric("Columns",       df.shape[1])
        c3.metric("Missing cells", int(df.isna().sum().sum()))
        c4.metric("Duplicates",    int(df.duplicated().sum()))

        st.markdown("<div class='div'></div>", unsafe_allow_html=True)

        tab_table, tab_cols = st.tabs(["📋 Data Table", "🧬 Column Details"])

        with tab_table:
            # Simple case-insensitive substring filter on column *names* (not
            # cell values) — lets the user narrow a wide table down quickly.
            search = st.text_input("🔎 Search columns", placeholder="Type a column name to filter the view…")
            shown_df = df
            if search.strip():
                matches = [c for c in df.columns if search.lower() in c.lower()]
                if matches:
                    shown_df = df[matches]
                else:
                    st.warning(f"No columns match '{search}'.")
            st.dataframe(shown_df, use_container_width=True, height=460)

        with tab_cols:
            # Build one "chip" card per column summarizing its dtype, unique
            # count, and missing-value rate. Card HTML is accumulated into a
            # list and joined once at the end (one st.markdown call) rather
            # than calling st.markdown per column, which is both faster and
            # lets the CSS grid lay all cards out together.
            type_map = {"num": ("Numeric", "type-num"), "obj": ("Text", "type-obj"),
                        "date": ("Date", "type-date"), "bool": ("Boolean", "type-bool")}
            chips = []
            for col in df.columns:
                s = df[col]
                # Order matters: bool must be checked before numeric, since
                # pandas boolean columns also satisfy is_numeric_dtype.
                if pd.api.types.is_bool_dtype(s):
                    tkey = "bool"
                elif pd.api.types.is_datetime64_any_dtype(s):
                    tkey = "date"
                elif pd.api.types.is_numeric_dtype(s):
                    tkey = "num"
                else:
                    tkey = "obj"
                label, css_class = type_map[tkey]
                nulls = int(s.isna().sum())
                pct_missing = round(nulls / len(df) * 100, 1) if len(df) else 0
                uniq = int(s.nunique())
                # Traffic-light bar color based on how much of the column is missing.
                bar_color = "#f87171" if pct_missing > 20 else ("#fbbf24" if pct_missing > 0 else "#22d3a5")
                chips.append(f"""
                <div class='col-chip'>
                    <div class='cc-name'>{col}</div>
                    <span class='cc-type {css_class}'>{label}</span>
                    <div class='cc-meta'>{uniq:,} unique · {nulls:,} missing ({pct_missing}%)</div>
                    <div class='cc-bar'><div class='cc-bar-fill' style='width:{max(pct_missing,2)}%;background:{bar_color}'></div></div>
                </div>
                """)
            st.markdown(f"<div class='col-chip-grid'>{''.join(chips)}</div>", unsafe_allow_html=True)

    # ── Statistics ───────────────────────────────────────────────────────────
    elif page == "📊 Statistics":
        st.markdown(f"""
        <div class='explore-hero'>
            <div class='eh-icon'>📊</div>
            <div>
                <div class='eh-title'>Statistical Summary</div>
                <div class='eh-sub'>Numeric distributions, missing data and category breakdowns</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        sample_analysis = False
        if len(df) > LARGE_DF_THRESHOLD:
            sample_analysis = st.checkbox(
                "⚡ Sample for speed",
                value=True,
                help="Use a smaller sample for statistics and charts on large datasets.",
            )

        analysis_df = sample_df_for_speed(df, sample_analysis)
        if len(analysis_df) != len(df):
            st.info(f"Using {len(analysis_df):,} sampled rows for this analysis.")

        tabs = st.tabs(["📐 Numeric Stats", "❓ Missing Values", "🏷️ Value Counts"])

        with tabs[0]:
            stats = get_numeric_stats(analysis_df)
            if stats is not None and not stats.empty:
                st.markdown("<div class='stat-panel'><h4>📐 Summary statistics</h4>", unsafe_allow_html=True)
                st.dataframe(stats, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div class='stat-panel'><h4>📈 Visualize a column</h4>", unsafe_allow_html=True)
                stat_cols = stats.columns.tolist()
                chosen_stat = st.radio(
                    "Select column to visualize",
                    stat_cols,
                    horizontal=True,
                    key="stats_chart_pick",
                    label_visibility="collapsed",
                )
                if st.button("📈 Visualize this column →", key="go_visualize"):
                    st.session_state.selected_chart_column = chosen_stat
                    st.session_state.selected_chart_type = "📈 Histogram"
                    st.session_state.redirect_to = "📈 Visualizations"
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No numeric columns found.")

        with tabs[1]:
            miss = analysis_df.isna().sum().rename("Missing").to_frame()
            miss["Pct (%)"] = (miss["Missing"] / len(analysis_df) * 100).round(2)
            miss = miss.sort_values("Missing", ascending=False)

            total_missing = int(miss["Missing"].sum())
            st.markdown(f"""
            <div class='stat-panel'>
                <h4>❓ Missing values {"— none found 🎉" if total_missing == 0 else f"— {total_missing:,} cells across {int((miss['Missing']>0).sum())} column(s)"}</h4>
            """, unsafe_allow_html=True)
            if total_missing > 0:
                max_missing = max(int(miss["Missing"].max()), 1)
                rows_html = ""
                for col, row in miss[miss["Missing"] > 0].iterrows():
                    width = max(row["Missing"] / max_missing * 100, 2)
                    rows_html += f"""
                    <div class='vc-row'>
                        <div class='vc-label'>{col}</div>
                        <div class='vc-bar-track'><div class='vc-bar-fill' style='width:{width}%;background:linear-gradient(90deg,#f87171,#fbbf24)'></div></div>
                        <div class='vc-count'>{int(row['Missing']):,} ({row['Pct (%)']}%)</div>
                    </div>
                    """
                st.markdown(rows_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.dataframe(miss, use_container_width=True)

        with tabs[2]:
            cat_cols = df.select_dtypes(exclude="number").columns.tolist()
            if cat_cols:
                chosen = st.selectbox("Column", cat_cols)
                vc = df[chosen].value_counts().rename("Count").to_frame()
                vc["Pct (%)"] = (vc["Count"] / len(df) * 100).round(2)

                st.markdown(f"<div class='stat-panel'><h4>🏷️ Top values in '{chosen}'</h4>", unsafe_allow_html=True)
                top = vc.head(10)
                max_count = int(top["Count"].max()) if not top.empty else 1
                rows_html = ""
                for label, row in top.iterrows():
                    width = max(row["Count"] / max_count * 100, 2)
                    rows_html += f"""
                    <div class='vc-row'>
                        <div class='vc-label'>{label}</div>
                        <div class='vc-bar-track'><div class='vc-bar-fill' style='width:{width}%'></div></div>
                        <div class='vc-count'>{int(row['Count']):,} ({row['Pct (%)']}%)</div>
                    </div>
                    """
                st.markdown(rows_html, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                st.dataframe(vc, use_container_width=True)
            else:
                st.info("No categorical columns found.")

    # ── Visualizations ───────────────────────────────────────────────────────
    elif page == "📈 Visualizations":
        st.markdown(f"""
        <div class='explore-hero'>
            <div class='eh-icon'>📈</div>
            <div>
                <div class='eh-title'>Visualizations</div>
                <div class='eh-sub'>Bar, histogram, pie and scatter charts — powered by Plotly</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        nums = df.select_dtypes(include="number").columns.tolist()
        cats = df.select_dtypes(exclude="number").columns.tolist()

        default_chart = st.session_state.selected_chart_type or "📊 Bar"
        chart_options = ["📊 Bar", "📈 Histogram", "🥧 Pie", "📉 Scatter"]
        if hasattr(st, "segmented_control"):
            try:
                chart = st.segmented_control(
                    "Chart type", chart_options, default=default_chart,
                    label_visibility="collapsed",
                )
            except TypeError:
                chart = st.segmented_control("Chart type", chart_options, default=default_chart)
        else:
            chart = st.radio(
                "Chart type", chart_options, horizontal=True,
                index=chart_options.index(default_chart),
                label_visibility="collapsed",
            )

        preselect_col = st.session_state.selected_chart_column
        # Consume the one-time preselection so later visits start fresh.
        st.session_state.selected_chart_type = None
        st.session_state.selected_chart_column = None

        st.markdown("<br>", unsafe_allow_html=True)

        chart_titles = {
            "📊 Bar": "Bar chart — category frequency",
            "📈 Histogram": "Histogram — value distribution",
            "🥧 Pie": "Pie chart — category share",
            "📉 Scatter": "Scatter plot — relationship between two variables",
        }

        picker_col, chart_col = st.columns([1, 2.4], gap="large")

        with picker_col:
            st.markdown("<div class='stat-panel'><h4>⚙️ Chart settings</h4>", unsafe_allow_html=True)
            selected_col = None
            x_col = y_col = None
            if "Bar" in chart and cats:
                idx = cats.index(preselect_col) if preselect_col in cats else 0
                selected_col = st.selectbox("Category column", cats, index=idx)
            elif "Histogram" in chart and nums:
                idx = nums.index(preselect_col) if preselect_col in nums else 0
                selected_col = st.selectbox("Numeric column", nums, index=idx)
            elif "Pie" in chart and cats:
                idx = cats.index(preselect_col) if preselect_col in cats else 0
                selected_col = st.selectbox("Category column", cats, index=idx)
            elif "Scatter" in chart and len(nums) >= 2:
                x_col = st.selectbox("X axis", nums)
                y_col = st.selectbox("Y axis", nums, index=1)
            else:
                st.caption("Not enough columns of the required type for this chart.")
            st.markdown("</div>", unsafe_allow_html=True)

        with chart_col:
            st.markdown(f"""
            <div class='chart-card'>
                <div class='cc-title'>{chart_titles.get(chart, '')}</div>
            """, unsafe_allow_html=True)

            if "Bar" in chart and cats and selected_col:
                st.plotly_chart(plot_bar(df, selected_col), use_container_width=True)
            elif "Histogram" in chart and nums and selected_col:
                st.plotly_chart(plot_histogram(df, selected_col), use_container_width=True)
            elif "Pie" in chart and cats and selected_col:
                st.plotly_chart(plot_pie(df, selected_col), use_container_width=True)
            elif "Scatter" in chart and x_col and y_col:
                st.plotly_chart(plot_scatter(df, x_col, y_col), use_container_width=True)
            else:
                st.info("Not enough columns of the required type for this chart.")

            st.markdown("</div>", unsafe_allow_html=True)

    # ── AI Assistant ─────────────────────────────────────────────────────────
    elif page == "🤖 AI Assistant":
        # one-time chat history list, separate from the single "answer" used by Export
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "ai_prefill" not in st.session_state:
            st.session_state.ai_prefill = ""

        # ── Hero banner ──
        st.markdown("""
        <div style='background:linear-gradient(135deg,#1a1d27 0%,#241a3d 55%,#1a1d27 100%);
                    border:1px solid var(--border);border-radius:18px;
                    padding:32px 36px;margin-bottom:24px;position:relative;overflow:hidden'>
            <div style='position:absolute;top:-60px;right:-40px;width:220px;height:220px;
                        background:radial-gradient(circle,rgba(99,102,241,.25) 0%,transparent 70%);
                        border-radius:50%'></div>
            <div style='display:flex;align-items:center;gap:16px;position:relative'>
                <div style='width:52px;height:52px;border-radius:14px;
                            background:linear-gradient(135deg,#6366f1,#818cf8);
                            display:flex;align-items:center;justify-content:center;
                            font-size:1.6rem;flex-shrink:0;
                            box-shadow:0 8px 24px rgba(99,102,241,.35)'>🤖</div>
                <div>
                    <div style='font-family:Space Grotesk;font-size:1.4rem;font-weight:700;
                                color:#fff;margin-bottom:2px'>Ask your data anything</div>
                    <div style='color:#94a3b8;font-size:.88rem'>
                        Answers are generated from a statistical summary — your raw rows never leave the app.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Suggested prompts ──
        nums = df.select_dtypes(include="number").columns.tolist()
        suggestions = [
            "📉 What columns have the most missing values?",
            "📈 Summarize the key trends in this dataset",
            f"🔢 What's notable about the '{nums[0]}' column?" if nums else "🧭 What should I explore first?",
            "🧩 Are there any outliers I should worry about?",
        ]
        st.markdown("<div style='color:#64748b;font-size:.78rem;font-weight:600;"
                    "text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px'>"
                    "Try asking</div>", unsafe_allow_html=True)
        chip_cols = st.columns(len(suggestions))
        for col, sug in zip(chip_cols, suggestions):
            with col:
                if st.button(sug, key=f"chip_{sug}", use_container_width=True):
                    st.session_state.ai_prefill = sug.split(" ", 1)[1]

        st.markdown("<div class='div'></div>", unsafe_allow_html=True)

        # ── Conversation history ──
        if st.session_state.chat_history:
            st.markdown("<div style='color:#64748b;font-size:.78rem;font-weight:600;"
                        "text-transform:uppercase;letter-spacing:.08em;margin-bottom:14px'>"
                        "Conversation</div>", unsafe_allow_html=True)

            for turn in st.session_state.chat_history:
                st.markdown(f"""
                <div style='display:flex;justify-content:flex-end;margin-bottom:10px'>
                    <div style='max-width:75%;background:var(--accent);color:#fff;
                                padding:12px 16px;border-radius:16px 16px 4px 16px;
                                font-size:.9rem;line-height:1.55'>
                        {turn['q']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div style='display:flex;justify-content:flex-start;gap:10px;margin-bottom:22px'>
                    <div style='width:30px;height:30px;border-radius:9px;flex-shrink:0;
                                background:linear-gradient(135deg,#6366f1,#818cf8);
                                display:flex;align-items:center;justify-content:center;
                                font-size:.9rem'>🤖</div>
                    <div style='max-width:75%;background:var(--card);border:1px solid var(--border);
                                color:var(--text);padding:14px 18px;border-radius:4px 16px 16px 16px;
                                font-size:.9rem;line-height:1.7'>
                        {turn['a']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if st.button("🗑️ Clear conversation", key="clear_chat"):
                st.session_state.chat_history = []
                st.session_state.answer = None
                st.rerun()

            st.markdown("<div class='div'></div>", unsafe_allow_html=True)

        # ── Composer ──
        st.markdown("<div style='color:#64748b;font-size:.78rem;font-weight:600;"
                    "text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px'>"
                    "Ask a question</div>", unsafe_allow_html=True)

        with st.form(key="ai_form", clear_on_submit=True):
            q = st.text_area(
                "Your question",
                value=st.session_state.ai_prefill,
                placeholder="e.g. Which column has the most missing values?",
                height=90,
                label_visibility="collapsed",
            )
            c1, c2 = st.columns([5, 1])
            with c2:
                submitted = st.form_submit_button("Ask AI →", use_container_width=True)

        if submitted:
            st.session_state.ai_prefill = ""
            if q.strip():
                with st.spinner("Thinking…"):
                    summary = get_summary(df, st.session_state.filename)
                    ans = ask_ai(q, summary)
                st.session_state.answer = ans
                st.session_state.chat_history.append({"q": q.strip(), "a": ans})
                st.rerun()
            else:
                st.warning("Please enter a question.")

    # ── Export ───────────────────────────────────────────────────────────────
    elif page == "📄 Export Report":
        section("EXPORT", "Download Report")

        ans = st.session_state.get("answer")
        if not ans:
            st.info("Run the AI Assistant first to generate content for the report.")
        else:
            st.markdown("""
            <div style='background:var(--card);border:1px solid var(--border);
                        border-radius:var(--radius);padding:22px;margin-bottom:24px'>
            <b style='color:#fff'>AI Analysis Preview</b><br><br>
            """ + str(ans) + "</div>", unsafe_allow_html=True)

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

    # ── About ────────────────────────────────────────────────────────────────
    elif page == "ℹ️ About":
        section("INFO", "About DataLens")
        st.markdown("""
        <div class='clean-panel'>
            <p style='color:#94a3b8;line-height:1.75'>
            <b style='color:#fff'>DataLens</b> is an AI-powered data analysis assistant built with
            Streamlit, Pandas, Plotly, and OpenRouter. It lets you upload, clean, explore,
            visualize and interrogate CSV datasets without writing a single line of code.
            </p>
            <p style='color:#94a3b8;line-height:1.75'>
            The <b style='color:#fff'>Clean Data</b> page gives you a full interactive pipeline:
            remove duplicates, handle missing values with multiple strategies, drop or rename columns,
            cast types, and filter rows — all with a live preview and an audit log.
            </p>
        </div>
        """, unsafe_allow_html=True)

        t1, t2, t3, t4 = st.columns(4)
        t1.metric("UI",       "Streamlit")
        t2.metric("Data",     "Pandas / NumPy")
        t3.metric("Charts",   "Plotly")
        t4.metric("AI model", "OpenRouter")
