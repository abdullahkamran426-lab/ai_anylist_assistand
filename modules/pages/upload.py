"""
Upload Dataset page
===================
Entry point for getting data into the app: the file uploader, the
empty state shown before a file is picked, and the success flow that
reads + auto-cleans the CSV and stores it in st.session_state for
every other page to use.
"""

import streamlit as st

from modules.analysis import load_data, clean_data


def render_upload_page():
    """
    Render the Upload Dataset page.
    Entry point for getting data into the app. Reads the CSV, runs it through
    the auto-clean pipeline, and stores the result in session_state.
    """
    # ------------------------------------------------------------------------
    # HERO BANNER
    # Page-specific hero banner
    # ------------------------------------------------------------------------
    st.markdown("""
    <div class='hero' style='padding:40px 44px;margin-bottom:28px'>
        <div class='hero-title' style='font-size:2rem'>Bring in your <span>dataset</span></div>
        <div class='hero-sub'>Drop a CSV below. We'll auto-detect types, strip stray whitespace,
        and get it ready for cleaning and analysis — all in a couple of seconds.</div>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # FILE UPLOADER
    # The actual upload widget restricted to CSV files only
    # ------------------------------------------------------------------------
    uploaded = st.file_uploader(
        "Drop a CSV file here or click to browse",
        type=["csv"],
        help="Only CSV files are supported.",
        label_visibility="collapsed",
    )

    # ------------------------------------------------------------------------
    # EMPTY STATE
    # Show friendly empty state when no file is uploaded
    # ------------------------------------------------------------------------
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

    # ------------------------------------------------------------------------
    # FILE PROCESSING
    # When a file is uploaded, load it, clean it, and store in session state
    # ------------------------------------------------------------------------
    if uploaded:
        # .getvalue() returns raw file bytes. We pass bytes (not the UploadedFile object)
        # into load_data() because cache keys must be hashable — bytes are, file-like objects aren't.
        with st.spinner("Reading and auto-cleaning…"):
            raw_df = load_data(uploaded.getvalue())
            df = clean_data(raw_df)   # baseline auto-clean

        # Persist the freshly-loaded data for every other page to use
        st.session_state.df = df
        st.session_state.original_df = df.copy()   # untouched snapshot for "Reset" button
        st.session_state.filename = uploaded.name
        st.session_state.clean_log = ["✅ Initial auto-clean applied (whitespace stripped, obvious duplicates removed)"]

        # Human-readable file size (KB below 1MB, MB above)
        size_kb = len(uploaded.getvalue()) / 1024
        size_txt = f"{size_kb:,.1f} KB" if size_kb < 1024 else f"{size_kb/1024:,.2f} MB"

        # ------------------------------------------------------------------------
        # SUCCESS BANNER
        # Show upload success with file details
        # ------------------------------------------------------------------------
        st.markdown(f"""
        <div class='upload-success'>
            <div class='check'>✓</div>
            <div>
                <div class='fname'>{uploaded.name}</div>
                <div class='fmeta'>{size_txt} · {df.shape[0]:,} rows · {df.shape[1]} columns · loaded successfully</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ------------------------------------------------------------------------
        # QUICK KPIs
        # At-a-glance metrics for the freshly loaded data
        # ------------------------------------------------------------------------
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows",            f"{df.shape[0]:,}")
        c2.metric("Columns",         df.shape[1])
        c3.metric("Missing cells",   int(df.isna().sum().sum()))
        c4.metric("Duplicate rows",  int(df.duplicated().sum()))

        st.markdown("<div class='div'></div>", unsafe_allow_html=True)

        # ------------------------------------------------------------------------
        # DATA PREVIEW TABS
        # Two views: row preview and column type summary
        # ------------------------------------------------------------------------
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

        # ------------------------------------------------------------------------
        # NEXT STEPS
        # Shortcut cards to navigate to other pages
        # ------------------------------------------------------------------------
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
