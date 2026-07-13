from pathlib import Path
import hashlib
import io
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
</style>
""", unsafe_allow_html=True)
 
# ── Session state ──────────────────────────────────────────────────────────────
for key, default in {
    "df": None,
    "original_df": None,
    "filename": None,
    "answer": None,
    "clean_log": [],
    "cached_summary": None,
    "history": [],
    "selected_chart_column": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

LARGE_DF_THRESHOLD = 100_000
SAMPLE_SIZE = 10_000

def push_history(df):
    """Keep a short undo history for data mutations."""
    if "history" not in st.session_state or st.session_state.history is None:
        st.session_state.history = []
    st.session_state.history.append(df.copy())
    if len(st.session_state.history) > 20:
        st.session_state.history = st.session_state.history[-20:]


def sample_df_for_speed(df, use_sample: bool):
    """Return a sampled DataFrame when the dataset is large and speed mode enabled."""
    if use_sample and len(df) > LARGE_DF_THRESHOLD:
        return df.sample(n=min(SAMPLE_SIZE, len(df)), random_state=42)
    return df


def detect_type_suggestions(df):
    """Identify object columns that likely contain numeric or datetime values."""
    suggestions = []
    for col in df.columns:
        if df[col].dtype == object:
            nonnull = df[col].dropna().astype(str)
            if len(nonnull) == 0:
                continue
            sample = nonnull.sample(n=min(300, len(nonnull)), random_state=42)
            numeric_ratio = sample.str.match(r'^[-+]?\d*\.?\d+$').mean()
            if numeric_ratio > 0.9:
                suggestions.append((col, "numeric"))
                continue
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().mean() > 0.85:
                suggestions.append((col, "datetime"))
    return suggestions


def auto_clean_pipeline(df):
    """Apply a standard auto-clean pipeline to the dataframe."""
    df = df.copy()
    log = []
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        log.append(f"✅ Removed {dup_count} duplicate rows")

    for col in df.columns:
        if df[col].isna().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                log.append(f"✅ Filled '{col}' nulls with median ({median_val:.4g})")
            else:
                mode_vals = df[col].mode(dropna=True)
                if not mode_vals.empty:
                    mode_val = mode_vals.iloc[0]
                    df[col] = df[col].fillna(mode_val)
                    log.append(f"✅ Filled '{col}' nulls with mode ({mode_val})")
    return df, log
 
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
 
    page = st.radio(
        "Navigation",
        ["🏠 Home", "📂 Upload Dataset", "🧹 Clean Data",
         "🔍 Dataset Preview", "📊 Statistics",
         "📈 Visualizations", "🤖 AI Assistant",
         "📄 Export Report", "ℹ️ About"],
        label_visibility="collapsed",
        key="page",
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
    section("STEP 1", "Upload your dataset")
 
    uploaded = st.file_uploader(
        "Drop a CSV file here or click to browse",
        type=["csv"],
        help="Only CSV files are supported.",
    )
 
    if uploaded:
        raw_bytes = uploaded.getvalue()
        with st.spinner("Reading and auto-cleaning…"):
            raw_df = load_data(raw_bytes)
            df = clean_data(raw_df)

        st.session_state.df = df
        st.session_state.original_df = df.copy()
        st.session_state.filename = uploaded.name
        st.session_state.clean_log = ["✅ Initial auto-clean applied (whitespace stripped, obvious duplicates removed)"]
        st.session_state.cached_summary = None
        st.session_state.file_hash = hashlib.md5(raw_bytes).hexdigest()
        st.session_state.history = [df.copy()]
        st.success(f"**{uploaded.name}** loaded — {df.shape[0]:,} rows × {df.shape[1]} columns")
 
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows",            f"{df.shape[0]:,}")
        c2.metric("Columns",         df.shape[1])
        c3.metric("Missing cells",   int(df.isna().sum().sum()))
        c4.metric("Duplicate rows",  int(df.duplicated().sum()))
 
        st.markdown("<div class='div'></div>", unsafe_allow_html=True)
        st.subheader("Preview (first 10 rows)")
        st.dataframe(df.head(10), use_container_width=True)
    else:
        st.info("👆 Upload a CSV file to get started.")
 
 
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
            push_history(df)
            df = df.drop_duplicates().reset_index(drop=True)
            st.session_state.df = df
            st.session_state.cached_summary = None
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
                push_history(df)
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
                st.session_state.cached_summary = None
                st.session_state.clean_log.append(msg)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
 
        # 3. Auto-clean + persist download
        st.markdown("<div class='clean-panel'><h4>⚡ Auto-clean & Download</h4>", unsafe_allow_html=True)
        if st.button("Run Auto-clean", key="auto_clean"):
            push_history(df)
            df, auto_log = auto_clean_pipeline(df)
            st.session_state.df = df
            st.session_state.cached_summary = None
            st.session_state.clean_log.extend(auto_log)
            st.session_state.clean_log.append("✅ Auto-clean pipeline applied")
            st.rerun()

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download cleaned CSV",
            csv_bytes,
            file_name=f"cleaned_{st.session_state.filename or 'dataset'}.csv",
            mime="text/csv",
            key="download_cleaned_csv",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # 4. Drop columns
        st.markdown("<div class='clean-panel'><h4>🗑️ Drop Columns</h4>", unsafe_allow_html=True)
        drop_cols = st.multiselect("Select columns to drop", df.columns.tolist(), key="drop_cols")
        if drop_cols and st.button("Drop selected", key="apply_drop"):
            push_history(df)
            df = df.drop(columns=drop_cols)
            st.session_state.df = df
            st.session_state.cached_summary = None
            st.session_state.clean_log.append(f"✅ Dropped columns: {', '.join(drop_cols)}")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
 
        # 4. Type suggestions
        st.markdown("<div class='clean-panel'><h4>🔧 Type Suggestions</h4>", unsafe_allow_html=True)
        type_suggestions = detect_type_suggestions(df)
        if type_suggestions:
            for col, suggestion in type_suggestions:
                col_label = f"{col} → {suggestion}"
                if st.button(f"Fix type: {col_label}", key=f"fix_{col}"):
                    push_history(df)
                    if suggestion == "numeric":
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    else:
                        df[col] = pd.to_datetime(df[col], errors="coerce")
                    st.session_state.df = df
                    st.session_state.cached_summary = None
                    st.session_state.clean_log.append(f"✅ Fixed type for '{col}' to {suggestion}")
                    st.rerun()
            if st.button("Fix all suggested types", key="fix_all_types"):
                push_history(df)
                for col, suggestion in type_suggestions:
                    if suggestion == "numeric":
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    else:
                        df[col] = pd.to_datetime(df[col], errors="coerce")
                    st.session_state.clean_log.append(f"✅ Fixed type for '{col}' to {suggestion}")
                st.session_state.df = df
                st.session_state.cached_summary = None
                st.rerun()
        else:
            st.markdown("<span class='pill pill-green'>No suggested type fixes detected.</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 5. Rename column
        st.markdown("<div class='clean-panel'><h4>✏️ Rename Column</h4>", unsafe_allow_html=True)
        ren_from = st.selectbox("Column to rename", df.columns.tolist(), key="ren_from")
        ren_to   = st.text_input("New name", key="ren_to")
        if st.button("Rename", key="apply_rename") and ren_to:
            push_history(df)
            df = df.rename(columns={ren_from: ren_to})
            st.session_state.df = df
            st.session_state.cached_summary = None
            st.session_state.clean_log.append(f"✅ Renamed '{ren_from}' → '{ren_to}'")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
 
        # 5. Cast dtype
        st.markdown("<div class='clean-panel'><h4>🔁 Change Column Type</h4>", unsafe_allow_html=True)
        cast_col   = st.selectbox("Column", df.columns.tolist(), key="cast_col")
        cast_dtype = st.selectbox("Target type", ["int", "float", "str", "datetime"], key="cast_dtype")
        if st.button("Cast", key="apply_cast"):
            push_history(df)
            try:
                if cast_dtype == "datetime":
                    df[cast_col] = pd.to_datetime(df[cast_col], errors="coerce")
                else:
                    df[cast_col] = df[cast_col].astype(cast_dtype)
                st.session_state.df = df
                st.session_state.cached_summary = None
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
                push_history(df)
                before = len(df)
                expr   = f"`{flt_col}` {flt_op} {flt_val}"
                df     = df.query(expr).reset_index(drop=True)
                st.session_state.df = df
                st.session_state.cached_summary = None
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
            st.session_state.cached_summary = None
            st.session_state.clean_log = ["↩️ Reset to original dataset"]
            st.session_state.history = [st.session_state.df.copy()]
            st.rerun()

        if st.button("↩️ Undo", key="undo_clean"):
            if st.session_state.history and len(st.session_state.history) > 1:
                st.session_state.history.pop()
                st.session_state.df = st.session_state.history[-1].copy()
                st.session_state.cached_summary = None
                st.session_state.clean_log.append("↩️ Undid last clean step")
                st.rerun()
            else:
                st.warning("Nothing to undo.")
 
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
 
        use_sample = False
        if len(df) > LARGE_DF_THRESHOLD:
            use_sample = st.checkbox(
                "Sample for speed",
                value=True,
                help="Use a smaller random sample for preview and analysis when the dataset is very large.",
            )

        display_df = sample_df_for_speed(df, use_sample)
        if len(display_df) != len(df):
            st.info(f"Showing {len(display_df):,} sampled rows for speed. Full dataset still exists in memory.")

        with st.expander("Column types"):
            dtype_df = df.dtypes.rename("Type").to_frame()
            dtype_df["Nulls"] = df.isna().sum()
            dtype_df["Unique"] = df.nunique()
            st.dataframe(dtype_df, use_container_width=True)
 
        st.dataframe(display_df, use_container_width=True, height=480)
 
    # ── Statistics ───────────────────────────────────────────────────────────
    elif page == "📊 Statistics":
        section("ANALYSIS", "Statistical Summary")
 
        tabs = st.tabs(["Numeric Stats", "Missing Values", "Value Counts"])
 
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

        with tabs[0]:
            stats = get_numeric_stats(analysis_df)
            if stats is not None:
                st.markdown("#### Numeric stats — click a column to visualize")
                if not stats.empty:
                    stat_cols = stats.columns.tolist()
                    chosen_stat = st.radio("Select column to visualize", stat_cols, horizontal=True)
                    if chosen_stat:
                        st.session_state.selected_chart_column = chosen_stat
                        st.session_state.selected_chart_type = "📈 Histogram"
                        st.session_state.page = "📈 Visualizations"
                        st.experimental_rerun()
                st.dataframe(stats, use_container_width=True)
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
 
        sample_analysis = False
        if len(df) > LARGE_DF_THRESHOLD:
            sample_analysis = st.checkbox(
                "Sample for speed",
                value=True,
                help="Use a smaller sample for chart rendering on large datasets.",
            )

        render_df = sample_df_for_speed(df, sample_analysis)
        if len(render_df) != len(df):
            st.info(f"Using {len(render_df):,} sampled rows for charts.")

        nums = render_df.select_dtypes(include="number").columns.tolist()
        cats = render_df.select_dtypes(exclude="number").columns.tolist()
 
        chart = st.session_state.selected_chart_type or "📊 Bar"
        chart = st.segmented_control(
            "Chart type",
            ["📊 Bar", "📈 Histogram", "🥧 Pie", "📉 Scatter"],
            default=chart,
        ) if hasattr(st, "segmented_control") else st.radio(
            "Chart type", ["📊 Bar", "📈 Histogram", "🥧 Pie", "📉 Scatter"],
            index=["📊 Bar", "📈 Histogram", "🥧 Pie", "📉 Scatter"].index(chart) if chart in ["📊 Bar", "📈 Histogram", "🥧 Pie", "📉 Scatter"] else 0,
            horizontal=True,
        )
 
        st.markdown("<br>", unsafe_allow_html=True)
 
        selected_col = st.session_state.selected_chart_column
        if selected_col and chart == "📈 Histogram" and selected_col in nums:
            c = selected_col
            st.markdown(f"#### Visualizing selected column: {c}")
            st.plotly_chart(plot_histogram(render_df, c), use_container_width=True)
        elif "Bar" in chart and cats:
            c = st.selectbox("Category column", cats)
            st.plotly_chart(plot_bar(render_df, c), use_container_width=True)
        elif "Histogram" in chart and nums:
            c = st.selectbox("Numeric column", nums)
            st.plotly_chart(plot_histogram(render_df, c), use_container_width=True)
        elif "Pie" in chart and cats:
            c = st.selectbox("Category column", cats)
            st.plotly_chart(plot_pie(render_df, c), use_container_width=True)
        elif "Scatter" in chart and len(nums) >= 2:
            x_col = st.selectbox("X axis", nums)
            y_col = st.selectbox("Y axis", nums, index=1)
            st.plotly_chart(plot_scatter(render_df, x_col, y_col), use_container_width=True)
        else:
            st.info("Not enough columns of the required type for this chart.")
 
    # ── AI Assistant ─────────────────────────────────────────────────────────
    elif page == "🤖 AI Assistant":
        section("AI", "Data Assistant")
 
        st.markdown("""
        <div style='color:#94a3b8;font-size:.92rem;margin-bottom:24px'>
        Ask anything about your dataset in plain English.
        The AI uses a statistical summary of your data — no raw rows are sent.
        </div>
        """, unsafe_allow_html=True)
 
        q = st.text_area("Your question", placeholder="e.g. Which column has the most missing values?", height=90)
        if st.button("Ask AI →"):
            if q.strip():
                with st.spinner("Thinking…"):
                    if st.session_state.cached_summary is None:
                        st.session_state.cached_summary = get_summary(df, st.session_state.filename)
                    ans = ask_ai(q, st.session_state.cached_summary)
                st.session_state.answer = ans
            else:
                st.warning("Please enter a question.")
 
        if st.session_state.answer:
            st.markdown("<div class='div'></div>", unsafe_allow_html=True)
            st.markdown("**AI Response**")
            st.markdown(f"""
            <div style='background:var(--card);border:1px solid var(--border);
                        border-left:4px solid #6366f1;border-radius:var(--radius);
                        padding:22px;line-height:1.75;color:var(--text)'>
            {st.session_state.answer}
            </div>
            """, unsafe_allow_html=True)
 
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
