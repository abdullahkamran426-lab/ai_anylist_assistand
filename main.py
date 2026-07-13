from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
from analysis import load_data, clean_data, get_summary, get_numeric_stats, get_category_counts, export_to_pdf
from visualization import plot_bar, plot_histogram, plot_pie, plot_scatter
from ai_helper import ask_ai

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataLens — AI Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;700&display=swap');

/* ── Root palette ── */
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

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stRadio label {
    padding: 8px 14px;
    border-radius: 8px;
    transition: background .15s;
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--muted);
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: var(--card);
    color: var(--text);
}

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
</style>
""", unsafe_allow_html=True)

# ── Large-data helpers ─────────────────────────────────────────────────────────
LARGE_DF_THRESHOLD = 100_000

def sample_df_for_speed(frame: pd.DataFrame, enabled: bool, n: int = 50_000) -> pd.DataFrame:
    """Return a random sample of `frame` when enabled and it's large; otherwise the frame itself."""
    if enabled and len(frame) > n:
        return frame.sample(n, random_state=42)
    return frame

# ── Session state ──────────────────────────────────────────────────────────────
for key, default in {
    "df": None,
    "original_df": None,
    "filename": None,
    "answer": None,
    "clean_log": [],
    "selected_chart_column": None,
    "selected_chart_type": None,
    "redirect_to": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:12px 0 20px'>
        <div style='font-family:Space Grotesk;font-size:1.25rem;font-weight:700;color:#fff'>
            🔬 DataLens
        </div>
        <div style='color:#6366f1;font-size:0.75rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase'>
            AI Analysis
        </div>
    </div>
    """, unsafe_allow_html=True)

    _nav_options = ["🏠 Home", "📂 Upload Dataset", "🧹 Clean Data",
                     "🔍 Dataset Preview", "📊 Statistics",
                     "📈 Visualizations", "🤖 AI Assistant",
                     "📄 Export Report", "ℹ️ About"]

    # If Statistics asked us to jump to Visualizations with a pre-picked column,
    # honor that once, then clear it so normal navigation resumes.
    _default_index = 0
    if st.session_state.redirect_to in _nav_options:
        _default_index = _nav_options.index(st.session_state.redirect_to)
        st.session_state.redirect_to = None

    page = st.radio(
        "Navigation",
        _nav_options,
        index=_default_index,
        label_visibility="collapsed",
    )

    # Dataset status badge
    if st.session_state.df is not None:
        df_info = st.session_state.df
        st.markdown("<div class='div'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background:rgba(99,102,241,.1);border:1px solid rgba(99,102,241,.3);
                    border-radius:10px;padding:14px;'>
            <div style='font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;
                        color:#818cf8;font-weight:700;margin-bottom:8px'>Active Dataset</div>
            <div style='color:#e2e8f0;font-weight:600;font-size:.9rem;
                        word-break:break-all'>{st.session_state.filename}</div>
            <div style='color:#94a3b8;font-size:.8rem;margin-top:6px'>
                {df_info.shape[0]:,} rows · {df_info.shape[1]} columns
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Helper: section header ─────────────────────────────────────────────────────
def section(label: str, title: str):
    st.markdown(f"<div class='section-label'>{label}</div>"
                f"<div class='section-title'>{title}</div>",
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.markdown("""
    <div class='hero'>
        <div class='hero-title'>Understand your data<br>in <span>minutes, not hours.</span></div>
        <div class='hero-sub'>
            Upload a CSV, clean it interactively, explore statistics and charts,
            then ask AI anything about your dataset — all in one place.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature cards ──
    section("CAPABILITIES", "Everything you need")
    cols = st.columns(4)
    features = [
        ("📂", "Upload & Parse",      "Drag-and-drop any CSV file. Instant preview with auto-detection."),
        ("🧹", "Interactive Cleaning","Drop duplicates, fix nulls, rename columns, cast types — visually."),
        ("📈", "Rich Visualisations", "Bar, histogram, pie and scatter charts powered by Plotly."),
        ("🤖", "AI Insights",         "Ask plain-English questions. Get instant answers from OpenRouter AI."),
    ]
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

    # ── How it works ──
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
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📂 Upload Dataset":
    st.markdown("""
    <div class='hero' style='padding:40px 44px;margin-bottom:28px'>
        <div class='hero-title' style='font-size:2rem'>Bring in your <span>dataset</span></div>
        <div class='hero-sub'>Drop a CSV below. We'll auto-detect types, strip stray whitespace,
        and get it ready for cleaning and analysis — all in a couple of seconds.</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drop a CSV file here or click to browse",
        type=["csv"],
        help="Only CSV files are supported.",
        label_visibility="collapsed",
    )

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
        with st.spinner("Reading and auto-cleaning…"):
            raw_df = load_data(uploaded.getvalue())
            df = clean_data(raw_df)

        st.session_state.df = df
        st.session_state.original_df = df.copy()
        st.session_state.filename = uploaded.name
        st.session_state.clean_log = ["✅ Initial auto-clean applied (whitespace stripped, obvious duplicates removed)"]

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

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows",            f"{df.shape[0]:,}")
        c2.metric("Columns",         df.shape[1])
        c3.metric("Missing cells",   int(df.isna().sum().sum()))
        c4.metric("Duplicate rows",  int(df.duplicated().sum()))

        st.markdown("<div class='div'></div>", unsafe_allow_html=True)

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
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧹 Clean Data":
    df = st.session_state.df
    if df is None:
        st.warning("Upload a dataset first.")
        st.stop()

    section("DATA CLEANING", "Fix, reshape & prepare")

    # ── Before/after KPIs ──
    orig = st.session_state.original_df
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Current rows",    f"{df.shape[0]:,}",  f"{df.shape[0]-orig.shape[0]:,}" if orig is not None else None)
    col_b.metric("Missing cells",   int(df.isna().sum().sum()),
                 f"{int(df.isna().sum().sum()) - int(orig.isna().sum().sum())}" if orig is not None else None)
    col_c.metric("Duplicate rows",  int(df.duplicated().sum()))
    col_d.metric("Columns",         df.shape[1])

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ── Left: controls   Right: live preview ──
    ctrl, prev = st.columns([1, 1.6], gap="large")

    with ctrl:
        # 1. Duplicate rows
        st.markdown("<div class='clean-panel'><h4>🔂 Duplicate Rows</h4>", unsafe_allow_html=True)
        dup_count = int(df.duplicated().sum())
        st.markdown(f"<span class='pill pill-{'red' if dup_count else 'green'}'>"
                    f"{'⚠️ ' if dup_count else '✅ '}{dup_count} duplicate{'s' if dup_count!=1 else ''}</span>",
                    unsafe_allow_html=True)
        if dup_count and st.button("Remove duplicates", key="rm_dup"):
            df = df.drop_duplicates().reset_index(drop=True)
            st.session_state.df = df
            st.session_state.clean_log.append(f"✅ Removed {dup_count} duplicate rows")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 2. Missing values
        missing_cols = df.columns[df.isna().any()].tolist()
        st.markdown("<div class='clean-panel'><h4>❓ Missing Values</h4>", unsafe_allow_html=True)
        if not missing_cols:
            st.markdown("<span class='pill pill-green'>✅ No missing values</span>", unsafe_allow_html=True)
        else:
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
                    mode_val = col_data.mode()[0]
                    df[mv_col] = col_data.fillna(mode_val)
                    msg = f"✅ Filled '{mv_col}' nulls with mode ({mode_val})"
                elif mv_strat == "Fill with constant" and mv_const != "":
                    try:
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

        # 3. Drop columns
        st.markdown("<div class='clean-panel'><h4>🗑️ Drop Columns</h4>", unsafe_allow_html=True)
        drop_cols = st.multiselect("Select columns to drop", df.columns.tolist(), key="drop_cols")
        if drop_cols and st.button("Drop selected", key="apply_drop"):
            df = df.drop(columns=drop_cols)
            st.session_state.df = df
            st.session_state.clean_log.append(f"✅ Dropped columns: {', '.join(drop_cols)}")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 4. Rename column
        st.markdown("<div class='clean-panel'><h4>✏️ Rename Column</h4>", unsafe_allow_html=True)
        ren_from = st.selectbox("Column to rename", df.columns.tolist(), key="ren_from")
        ren_to   = st.text_input("New name", key="ren_to")
        if st.button("Rename", key="apply_rename") and ren_to:
            df = df.rename(columns={ren_from: ren_to})
            st.session_state.df = df
            st.session_state.clean_log.append(f"✅ Renamed '{ren_from}' → '{ren_to}'")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 5. Cast dtype
        st.markdown("<div class='clean-panel'><h4>🔁 Change Column Type</h4>", unsafe_allow_html=True)
        cast_col   = st.selectbox("Column", df.columns.tolist(), key="cast_col")
        cast_dtype = st.selectbox("Target type", ["int", "float", "str", "datetime"], key="cast_dtype")
        if st.button("Cast", key="apply_cast"):
            try:
                if cast_dtype == "datetime":
                    df[cast_col] = pd.to_datetime(df[cast_col], errors="coerce")
                else:
                    df[cast_col] = df[cast_col].astype(cast_dtype)
                st.session_state.df = df
                st.session_state.clean_log.append(f"✅ Cast '{cast_col}' to {cast_dtype}")
            except Exception as exc:
                st.error(f"Could not cast: {exc}")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 6. Filter rows
        st.markdown("<div class='clean-panel'><h4>🔍 Filter Rows</h4>", unsafe_allow_html=True)
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if num_cols:
            flt_col = st.selectbox("Numeric column", num_cols, key="flt_col")
            flt_op  = st.selectbox("Operator", [">", ">=", "<", "<=", "==", "!="], key="flt_op")
            flt_val = st.number_input("Value", key="flt_val")
            if st.button("Apply filter", key="apply_flt"):
                before = len(df)
                expr   = f"`{flt_col}` {flt_op} {flt_val}"
                df     = df.query(expr).reset_index(drop=True)
                st.session_state.df = df
                st.session_state.clean_log.append(
                    f"✅ Filter '{flt_col} {flt_op} {flt_val}' kept {len(df):,}/{before:,} rows")
                st.rerun()
        else:
            st.caption("No numeric columns available.")
        st.markdown("</div>", unsafe_allow_html=True)

        # 7. Reset
        st.markdown("<div class='div'></div>", unsafe_allow_html=True)
        if st.button("↩️ Reset to original", key="reset_clean"):
            st.session_state.df = st.session_state.original_df.copy()
            st.session_state.clean_log = ["↩️ Reset to original dataset"]
            st.rerun()

    with prev:
        st.markdown("#### Live Preview")
        st.dataframe(df.head(50), use_container_width=True, height=340)

        # Missing-value heatmap summary
        if df.isna().any().any():
            st.markdown("#### Missing-value breakdown")
            miss = (df.isna().sum()
                      .rename("Missing")
                      .to_frame()
                      .assign(Pct=lambda d: (d["Missing"]/len(df)*100).round(2))
                      .query("Missing > 0"))
            st.dataframe(miss, use_container_width=True)

        # Clean log
        if st.session_state.clean_log:
            st.markdown("#### Cleaning log")
            for entry in reversed(st.session_state.clean_log):
                st.markdown(f"<small style='color:#94a3b8'>{entry}</small>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Guard — all remaining pages need a loaded dataframe
# ══════════════════════════════════════════════════════════════════════════════
else:
    df = st.session_state.df
    if df is None:
        st.warning("Upload a dataset first.")
        st.stop()

    # ── Dataset Preview ──────────────────────────────────────────────────────
    if page == "🔍 Dataset Preview":
        section("EXPLORE", "Dataset Preview")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows",          f"{df.shape[0]:,}")
        c2.metric("Columns",       df.shape[1])
        c3.metric("Missing cells", int(df.isna().sum().sum()))
        c4.metric("Duplicates",    int(df.duplicated().sum()))

        st.markdown("<div class='div'></div>", unsafe_allow_html=True)

        with st.expander("Column types"):
            dtype_df = df.dtypes.rename("Type").to_frame()
            dtype_df["Nulls"] = df.isna().sum()
            dtype_df["Unique"] = df.nunique()
            st.dataframe(dtype_df, use_container_width=True)

        st.dataframe(df, use_container_width=True, height=480)

    # ── Statistics ───────────────────────────────────────────────────────────
    elif page == "📊 Statistics":
        section("ANALYSIS", "Statistical Summary")

        sample_analysis = False
        if len(df) > LARGE_DF_THRESHOLD:
            sample_analysis = st.checkbox(
                "Sample for speed",
                value=True,
                help="Use a smaller sample for statistics and charts on large datasets.",
            )

        analysis_df = sample_df_for_speed(df, sample_analysis)
        if len(analysis_df) != len(df):
            st.info(f"Using {len(analysis_df):,} sampled rows for this analysis.")

        tabs = st.tabs(["Numeric Stats", "Missing Values", "Value Counts"])

        with tabs[0]:
            stats = get_numeric_stats(analysis_df)
            if stats is not None and not stats.empty:
                st.markdown("#### Numeric stats")
                st.dataframe(stats, use_container_width=True)

                st.markdown("#### Visualize a column")
                stat_cols = stats.columns.tolist()
                chosen_stat = st.radio(
                    "Select column to visualize",
                    stat_cols,
                    horizontal=True,
                    key="stats_chart_pick",
                )
                if st.button("📈 Visualize this column", key="go_visualize"):
                    st.session_state.selected_chart_column = chosen_stat
                    st.session_state.selected_chart_type = "📈 Histogram"
                    st.session_state.redirect_to = "📈 Visualizations"
                    st.rerun()
            else:
                st.info("No numeric columns found.")

        with tabs[1]:
            miss = analysis_df.isna().sum().rename("Missing").to_frame()
            miss["Pct (%)"] = (miss["Missing"] / len(analysis_df) * 100).round(2)
            miss = miss.sort_values("Missing", ascending=False)
            st.dataframe(miss, use_container_width=True)

        with tabs[2]:
            cat_cols = df.select_dtypes(exclude="number").columns.tolist()
            if cat_cols:
                chosen = st.selectbox("Column", cat_cols)
                vc = df[chosen].value_counts().rename("Count").to_frame()
                vc["Pct (%)"] = (vc["Count"] / len(df) * 100).round(2)
                st.dataframe(vc, use_container_width=True)
            else:
                st.info("No categorical columns found.")

    # ── Visualizations ───────────────────────────────────────────────────────
    elif page == "📈 Visualizations":
        section("CHARTS", "Visualizations")

        nums = df.select_dtypes(include="number").columns.tolist()
        cats = df.select_dtypes(exclude="number").columns.tolist()

        default_chart = st.session_state.selected_chart_type or "📊 Bar"
        chart = st.segmented_control(
            "Chart type",
            ["📊 Bar", "📈 Histogram", "🥧 Pie", "📉 Scatter"],
            default=default_chart,
        ) if hasattr(st, "segmented_control") else st.radio(
            "Chart type", ["📊 Bar", "📈 Histogram", "🥧 Pie", "📉 Scatter"],
            horizontal=True,
            index=["📊 Bar", "📈 Histogram", "🥧 Pie", "📉 Scatter"].index(default_chart),
        )

        preselect_col = st.session_state.selected_chart_column
        # Consume the one-time preselection so later visits start fresh.
        st.session_state.selected_chart_type = None
        st.session_state.selected_chart_column = None

        st.markdown("<br>", unsafe_allow_html=True)

        if "Bar" in chart and cats:
            idx = cats.index(preselect_col) if preselect_col in cats else 0
            c = st.selectbox("Category column", cats, index=idx)
            st.plotly_chart(plot_bar(df, c), use_container_width=True)
        elif "Histogram" in chart and nums:
            idx = nums.index(preselect_col) if preselect_col in nums else 0
            c = st.selectbox("Numeric column", nums, index=idx)
            st.plotly_chart(plot_histogram(df, c), use_container_width=True)
        elif "Pie" in chart and cats:
            idx = cats.index(preselect_col) if preselect_col in cats else 0
            c = st.selectbox("Category column", cats, index=idx)
            st.plotly_chart(plot_pie(df, c), use_container_width=True)
        elif "Scatter" in chart and len(nums) >= 2:
            x_col = st.selectbox("X axis", nums)
            y_col = st.selectbox("Y axis", nums, index=1)
            st.plotly_chart(plot_scatter(df, x_col, y_col), use_container_width=True)
        else:
            st.info("Not enough columns of the required type for this chart.")

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
