"""
Upload Dataset page
===================
Entry point for getting data into the app: the file uploader, the
empty state shown before a file is picked, and the success flow that
reads + auto-cleans the data and stores it in st.session_state for
every other page to use.
"""

import streamlit as st

from modules.analysis import clean_data, load_data


def render_upload_page():
    st.markdown("""
    <div class='hero' style='padding:40px 44px;margin-bottom:28px'>
        <div class='hero-title' style='font-size:2rem'>Bring in your <span>dataset</span></div>
        <div class='hero-sub'>Upload a CSV, Excel, JSON, TSV, or Parquet file. We auto-detect types, clean common issues, and prepare it for analysis.</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drop a dataset here or click to browse",
        type=["csv", "xlsx", "json", "tsv", "parquet"],
        help="Supports CSV, Excel, JSON, TSV, and Parquet files.",
        label_visibility="collapsed",
    )

    if not uploaded:
        st.markdown("""
        <div class='upload-empty'>
            <div class='icon'>📄</div>
            <div class='title'>No file selected yet</div>
            <div class='desc'>Drag a supported dataset into the box above, or click it to browse your computer.</div>
            <div class='req-row'>
                <div class='req-chip'>📐 Tabular data</div>
                <div class='req-chip'>🔤 CSV / Excel / JSON / TSV / Parquet</div>
                <div class='req-chip'>🚀 Ready for cleaning and modeling</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    with st.spinner("Reading and auto-cleaning…"):
        raw_df = load_data(uploaded.getvalue(), filename=uploaded.name)
        df = clean_data(raw_df)

    st.session_state.df = df
    st.session_state.original_df = df.copy()
    st.session_state.filename = uploaded.name
    st.session_state.clean_log = ["✅ Initial auto-clean applied (whitespace normalized, obvious duplicates removed)"]
    st.session_state.chat_history = []
    st.session_state.answer = None

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
    c1.metric("Rows", f"{df.shape[0]:,}")
    c2.metric("Columns", df.shape[1])
    c3.metric("Missing cells", int(df.isna().sum().sum()))
    c4.metric("Duplicate rows", int(df.duplicated().sum()))

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    prev_tab, types_tab = st.tabs(["👁️ Preview", "🧬 Column types"])
    with prev_tab:
        st.dataframe(df.head(10))
    with types_tab:
        dtype_df = df.dtypes.rename("Type").astype(str).to_frame()
        dtype_df["Nulls"] = df.isna().sum()
        dtype_df["Unique values"] = df.nunique()
        st.dataframe(dtype_df)

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
            if st.button("Go →", key=f"go_{target}"):
                st.session_state.redirect_to = target
                st.rerun()
