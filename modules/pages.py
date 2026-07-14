"""
Page Rendering Functions
This file contains all page rendering functions for the DataLens application.
Each function renders a complete page and should be called from main.py based on
the selected page from the sidebar navigation.
"""

import streamlit as st
import pandas as pd
import numpy as np

# Import helper modules
from modules.analysis import load_data, clean_data, get_summary, get_numeric_stats, get_category_counts, export_to_pdf
from modules.visualization import plot_bar, plot_histogram, plot_pie, plot_scatter
from modules.ai_helper import ask_ai
from modules.utils import section, sample_df_for_speed
from modules.config import LARGE_DF_THRESHOLD


def render_home_page():
    """
    Render the Home page - landing page with app overview.
    This page is purely informational/marketing and doesn't require a dataframe.
    """
    # ------------------------------------------------------------------------
    # HERO BANNER
    # Big gradient banner introducing the app
    # ------------------------------------------------------------------------
    st.markdown("""
    <div class='hero'>
        <div class='hero-title'>Understand your data<br>in <span>minutes, not hours.</span></div>
        <div class='hero-sub'>
            Upload a CSV, clean it interactively, explore statistics and charts,
            then ask AI anything about your dataset — all in one place.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # FEATURE CARDS
    # Four-column grid summarizing the app's capabilities
    # ------------------------------------------------------------------------
    section("CAPABILITIES", "Everything you need")
    cols = st.columns(4)
    features = [
        ("📂", "Upload & Parse",      "Drag-and-drop any CSV file. Instant preview with auto-detection."),
        ("🧹", "Interactive Cleaning","Drop duplicates, fix nulls, rename columns, cast types — visually."),
        ("📈", "Rich Visualisations", "Bar, histogram, pie and scatter charts powered by Plotly."),
        ("🤖", "AI Insights",         "Ask plain-English questions. Get instant answers from OpenRouter AI."),
    ]
    # zip() pairs each Streamlit column with its matching feature tuple
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

    # ------------------------------------------------------------------------
    # CTA BUTTON
    # Prominent button to upload a dataset
    # ------------------------------------------------------------------------
    st.markdown("<div style='text-align:center;margin:32px 0'>", unsafe_allow_html=True)
    if st.button("📂 Upload a dataset", key="home_upload_btn", use_container_width=True):
        st.session_state.redirect_to = "📂 Upload Dataset"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # HOW IT WORKS
    # Three-step onboarding cards pointing at the relevant pages
    # ------------------------------------------------------------------------
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

    # ------------------------------------------------------------------------
    # TECH PILLS
    # Technology stack badges
    # ------------------------------------------------------------------------
    section("STACK", "Built with")
    st.markdown("""
    <span class='pill pill-blue'>Streamlit</span>
    <span class='pill pill-blue'>Pandas</span>
    <span class='pill pill-blue'>Plotly</span>
    <span class='pill pill-blue'>OpenRouter AI</span>
    <span class='pill pill-blue'>NumPy</span>
    """, unsafe_allow_html=True)


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


def render_clean_data_page():
    """
    Render the Clean Data page.
    Interactive cleaning pipeline with live preview and audit log.
    Every control mutates df, saves it back to session_state, appends to clean_log,
    then calls st.rerun() to redraw with updated data.
    """
    df = st.session_state.df

    # Guard: this page is meaningless without data
    if df is None:
        st.markdown("""
        <div style='background:linear-gradient(135deg,rgba(34,211,165,.12) 0%,rgba(34,211,165,.03) 100%);
                    border:2px solid #22d3a5;border-radius:12px;padding:20px 24px;margin:20px 0'>
            <div style='display:flex;align-items:center;gap:12px'>
                <div style='font-size:1.5rem'>📂</div>
                <div>
                    <div style='font-weight:700;color:#fff;font-size:1rem'>Upload a dataset first</div>
                    <div style='color:#94a3b8;font-size:.87rem;margin-top:2px'>
                        Go to the Upload Dataset page to get started.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    section("DATA CLEANING", "Fix, reshape & prepare")

    # ------------------------------------------------------------------------
    # BEFORE/AFTER KPIs
    # Compare current state against original upload
    # ------------------------------------------------------------------------
    orig = st.session_state.original_df
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Current rows",    f"{df.shape[0]:,}",  f"{df.shape[0]-orig.shape[0]:,}" if orig is not None else None)
    col_b.metric("Missing cells",   int(df.isna().sum().sum()),
                 f"{int(df.isna().sum().sum()) - int(orig.isna().sum().sum())}" if orig is not None else None)
    col_c.metric("Duplicate rows",  int(df.duplicated().sum()))
    col_d.metric("Columns",         df.shape[1])

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # DOWNLOAD CLEANED DATASET
    # Encode current dataframe to CSV for download buttons
    # ------------------------------------------------------------------------
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

    # ------------------------------------------------------------------------
    # TWO-COLUMN LAYOUT
    # Left: cleaning controls, Right: live preview
    # ------------------------------------------------------------------------
    ctrl, prev = st.columns([1, 1.6], gap="large")

    with ctrl:
        # --------------------------------------------------------------------
        # 1. DUPLICATE ROWS
        # Detect and remove exact row-level duplicates
        # --------------------------------------------------------------------
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

        # --------------------------------------------------------------------
        # 2. MISSING VALUES
        # Per-column strategy picker (drop / mean / median / mode / constant)
        # --------------------------------------------------------------------
        missing_cols = df.columns[df.isna().any()].tolist()
        st.markdown("<div class='clean-panel'><h4>❓ Missing Values</h4>", unsafe_allow_html=True)
        if not missing_cols:
            st.markdown("<span class='pill pill-green'>✅ No missing values</span>", unsafe_allow_html=True)
        else:
            # Show one pill per affected column
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
                
                # Apply selected strategy
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

        # --------------------------------------------------------------------
        # 3. DROP COLUMNS
        # Remove one or more columns entirely
        # --------------------------------------------------------------------
        st.markdown("<div class='clean-panel'><h4>🗑️ Drop Columns</h4>", unsafe_allow_html=True)
        drop_cols = st.multiselect("Select columns to drop", df.columns.tolist(), key="drop_cols")
        if drop_cols and st.button("Drop selected", key="apply_drop"):
            df = df.drop(columns=drop_cols)
            st.session_state.df = df
            st.session_state.clean_log.append(f"✅ Dropped columns: {', '.join(drop_cols)}")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # --------------------------------------------------------------------
        # 4. RENAME COLUMN
        # Simple find/replace on a single column header
        # --------------------------------------------------------------------
        st.markdown("<div class='clean-panel'><h4>✏️ Rename Column</h4>", unsafe_allow_html=True)
        ren_from = st.selectbox("Column to rename", df.columns.tolist(), key="ren_from")
        ren_to   = st.text_input("New name", key="ren_to")
        if st.button("Rename", key="apply_rename") and ren_to:
            df = df.rename(columns={ren_from: ren_to})
            st.session_state.df = df
            st.session_state.clean_log.append(f"✅ Renamed '{ren_from}' → '{ren_to}'")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # --------------------------------------------------------------------
        # 5. CAST DTYPE
        # Force a column to int/float/str/datetime
        # --------------------------------------------------------------------
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

        # --------------------------------------------------------------------
        # 6. FILTER ROWS
        # Keep only rows matching a simple numeric comparison
        # --------------------------------------------------------------------
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

        # --------------------------------------------------------------------
        # 7. RESET & DOWNLOAD
        # Undo everything back to original, or download current state
        # --------------------------------------------------------------------
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
        # --------------------------------------------------------------------
        # LIVE PREVIEW
        # Right-hand column always reflects current df state
        # --------------------------------------------------------------------
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

        # Clean log - running audit trail
        if st.session_state.clean_log:
            st.markdown("#### Cleaning log")
            for entry in reversed(st.session_state.clean_log):
                st.markdown(f"<small style='color:#94a3b8'>{entry}</small>", unsafe_allow_html=True)


def render_dataset_preview_page():
    """
    Render the Dataset Preview page.
    Full table view with column details and search functionality.
    """
    df = st.session_state.df

    # Guard: this page requires data
    if df is None:
        st.markdown("""
        <div style='background:linear-gradient(135deg,rgba(34,211,165,.12) 0%,rgba(34,211,165,.03) 100%);
                    border:2px solid #22d3a5;border-radius:12px;padding:20px 24px;margin:20px 0'>
            <div style='display:flex;align-items:center;gap:12px'>
                <div style='font-size:1.5rem'>📂</div>
                <div>
                    <div style='font-weight:700;color:#fff;font-size:1rem'>Upload a dataset first</div>
                    <div style='color:#94a3b8;font-size:.87rem;margin-top:2px'>
                        Go to the Upload Dataset page to get started.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ------------------------------------------------------------------------
    # HERO STRIP
    # Compact hero banner with dataset info
    # ------------------------------------------------------------------------
    st.markdown(
        f"""
        <div class='explore-hero'>
            <div class='eh-icon'>🔍</div>
            <div>
                <div class='eh-title'>Dataset Preview</div>
                <div class='eh-sub'>
                    {st.session_state.filename} ·
                    {df.shape[0]:,} rows ·
                    {df.shape[1]} columns
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------------
    # KPI METRICS
    # Quick stats at top of page
    # ------------------------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{df.shape[0]:,}")
    c2.metric("Columns", df.shape[1])
    c3.metric("Missing Cells", int(df.isna().sum().sum()))
    c4.metric("Duplicate Rows", int(df.duplicated().sum()))

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # DATA TABLE VIEW
    # Full table view with search functionality
    # ------------------------------------------------------------------------
    # Search columns functionality
    search = st.text_input(
        "🔎 Search Columns",
        placeholder="Type a column name..."
    )

    shown_df = df

    if search.strip():
        matches = [c for c in df.columns if search.lower() in c.lower()]
        if matches:
            shown_df = df[matches]
        else:
            st.warning(f"No columns match '{search}'.")

    st.dataframe(shown_df, width="stretch", height=460)


def render_statistics_page():
    """
    Render the Statistics page.
    Numeric distributions, missing data, and category breakdowns.
    """
    df = st.session_state.df

    # Guard: this page requires data
    if df is None:
        st.markdown("""
        <div style='background:linear-gradient(135deg,rgba(34,211,165,.12) 0%,rgba(34,211,165,.03) 100%);
                    border:2px solid #22d3a5;border-radius:12px;padding:20px 24px;margin:20px 0'>
            <div style='display:flex;align-items:center;gap:12px'>
                <div style='font-size:1.5rem'>📂</div>
                <div>
                    <div style='font-weight:700;color:#fff;font-size:1rem'>Upload a dataset first</div>
                    <div style='color:#94a3b8;font-size:.87rem;margin-top:2px'>
                        Go to the Upload Dataset page to get started.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ------------------------------------------------------------------------
    # HERO STRIP
    # ------------------------------------------------------------------------
    st.markdown(f"""
    <div class='explore-hero'>
        <div class='eh-icon'>📊</div>
        <div>
            <div class='eh-title'>Statistical Summary</div>
            <div class='eh-sub'>Numeric distributions, missing data and category breakdowns</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # SAMPLING OPTION
    # Offer sampling for large datasets
    # ------------------------------------------------------------------------
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

    # ------------------------------------------------------------------------
    # TABS
    # Numeric Stats, Missing Values, Value Counts
    # ------------------------------------------------------------------------
    tabs = st.tabs(["📐 Numeric Stats", "❓ Missing Values", "🏷️ Value Counts"])

    # ========================================================================
    # NUMERIC STATS TAB
    # ========================================================================
    with tabs[0]:
        stats = get_numeric_stats(analysis_df)
        if stats is not None and not stats.empty:
            st.markdown("<div class='stat-panel'><h4>📐 Summary statistics</h4>", unsafe_allow_html=True)
            st.dataframe(stats, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Visualize a column option with redirect to Visualizations
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

    # ========================================================================
    # MISSING VALUES TAB
    # ========================================================================
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

    # ========================================================================
    # VALUE COUNTS TAB
    # ========================================================================
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


def render_visualizations_page():
    """
    Render the Visualizations page.
    Bar, histogram, pie and scatter charts powered by Plotly.
    """
    df = st.session_state.df

    # Guard: this page requires data
    if df is None:
        st.markdown("""
        <div style='background:linear-gradient(135deg,rgba(34,211,165,.12) 0%,rgba(34,211,165,.03) 100%);
                    border:2px solid #22d3a5;border-radius:12px;padding:20px 24px;margin:20px 0'>
            <div style='display:flex;align-items:center;gap:12px'>
                <div style='font-size:1.5rem'>📂</div>
                <div>
                    <div style='font-weight:700;color:#fff;font-size:1rem'>Upload a dataset first</div>
                    <div style='color:#94a3b8;font-size:.87rem;margin-top:2px'>
                        Go to the Upload Dataset page to get started.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ------------------------------------------------------------------------
    # HERO STRIP
    # ------------------------------------------------------------------------
    st.markdown(f"""
    <div class='explore-hero'>
        <div class='eh-icon'>📈</div>
        <div>
            <div class='eh-title'>Visualizations</div>
            <div class='eh-sub'>Bar, histogram, pie and scatter charts — powered by Plotly</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # COLUMN CATEGORIZATION
    # Separate numeric and categorical columns
    # ------------------------------------------------------------------------
    nums = df.select_dtypes(include="number").columns.tolist()
    cats = df.select_dtypes(exclude="number").columns.tolist()

    # ------------------------------------------------------------------------
    # CHART TYPE SELECTOR
    # Use segmented_control if available, otherwise radio
    # ------------------------------------------------------------------------
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

    # Consume one-time preselection so later visits start fresh
    preselect_col = st.session_state.selected_chart_column
    st.session_state.selected_chart_type = None
    st.session_state.selected_chart_column = None

    st.markdown("<br>", unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # CHART TITLES
    # ------------------------------------------------------------------------
    chart_titles = {
        "📊 Bar": "Bar chart — category frequency",
        "📈 Histogram": "Histogram — value distribution",
        "🥧 Pie": "Pie chart — category share",
        "📉 Scatter": "Scatter plot — relationship between two variables",
    }

    # ------------------------------------------------------------------------
    # TWO-COLUMN LAYOUT
    # Left: chart settings, Right: chart output
    # ------------------------------------------------------------------------
    picker_col, chart_col = st.columns([1, 2.4], gap="large")

    with picker_col:
        st.markdown("<div class='stat-panel'><h4>⚙️ Chart settings</h4>", unsafe_allow_html=True)
        selected_col = None
        x_col = y_col = None
        
        # Select column based on chart type
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
        # --------------------------------------------------------------------
        # CHART OUTPUT
        # Render the selected chart type
        # --------------------------------------------------------------------
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


def render_ai_assistant_page():
    """
    Render the AI Assistant page.
    Natural-language Q&A with conversation history and suggested prompts.
    """
    df = st.session_state.df

    # Guard: this page requires data
    if df is None:
        st.markdown("""
        <div style='background:linear-gradient(135deg,rgba(34,211,165,.12) 0%,rgba(34,211,165,.03) 100%);
                    border:2px solid #22d3a5;border-radius:12px;padding:20px 24px;margin:20px 0'>
            <div style='display:flex;align-items:center;gap:12px'>
                <div style='font-size:1.5rem'>📂</div>
                <div>
                    <div style='font-weight:700;color:#fff;font-size:1rem'>Upload a dataset first</div>
                    <div style='color:#94a3b8;font-size:.87rem;margin-top:2px'>
                        Go to the Upload Dataset page to get started.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ------------------------------------------------------------------------
    # INITIALIZE CHAT STATE
    # One-time chat history list, separate from single "answer" used by Export
    # ------------------------------------------------------------------------
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "ai_prefill" not in st.session_state:
        st.session_state.ai_prefill = ""

    # ------------------------------------------------------------------------
    # HERO BANNER
    # AI-specific gradient banner
    # ------------------------------------------------------------------------
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

    # ------------------------------------------------------------------------
    # SUGGESTED PROMPTS
    # Quick-start question chips
    # ------------------------------------------------------------------------
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

    # ------------------------------------------------------------------------
    # CONVERSATION HISTORY
    # Display previous Q&A turns
    # ------------------------------------------------------------------------
    if st.session_state.chat_history:
        st.markdown("<div style='color:#64748b;font-size:.78rem;font-weight:600;"
                    "text-transform:uppercase;letter-spacing:.08em;margin-bottom:14px'>"
                    "Conversation</div>", unsafe_allow_html=True)

        for turn in st.session_state.chat_history:
            # User question (right-aligned)
            st.markdown(f"""
            <div style='display:flex;justify-content:flex-end;margin-bottom:10px'>
                <div style='max-width:75%;background:var(--accent);color:#fff;
                            padding:12px 16px;border-radius:16px 16px 4px 16px;
                            font-size:.9rem;line-height:1.55'>
                    {turn['q']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # AI answer (left-aligned with icon)
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

        # Clear conversation button
        if st.button("🗑️ Clear conversation", key="clear_chat"):
            st.session_state.chat_history = []
            st.session_state.answer = None
            st.rerun()

        st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # QUESTION COMPOSER
    # Text area for user to ask questions
    # ------------------------------------------------------------------------
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

    # ------------------------------------------------------------------------
    # SUBMIT QUESTION
    # Call AI and store response
    # ------------------------------------------------------------------------
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


def render_export_page():
    """
    Render the Export Report page.
    Download AI-generated analysis as a PDF report.
    """
    section("EXPORT", "Download Report")

    ans = st.session_state.get("answer")
    if not ans:
        st.markdown("""
        <div style='background:linear-gradient(135deg,rgba(34,211,165,.12) 0%,rgba(34,211,165,.03) 100%);
                    border:2px solid #22d3a5;border-radius:12px;padding:20px 24px;margin:20px 0'>
            <div style='display:flex;align-items:center;gap:12px'>
                <div style='font-size:1.5rem'>🤖</div>
                <div>
                    <div style='font-weight:700;color:#fff;font-size:1rem'>Run AI Assistant first</div>
                    <div style='color:#94a3b8;font-size:.87rem;margin-top:2px'>
                        Go to the AI Assistant page to generate content for the report.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Show preview of AI analysis
        st.markdown("""
        <div style='background:var(--card);border:1px solid var(--border);
                    border-radius:var(--radius);padding:22px;margin-bottom:24px'>
        <b style='color:#fff'>AI Analysis Preview</b><br><br>
        """ + str(ans) + "</div>", unsafe_allow_html=True)

        # Generate and download PDF
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


def render_about_page():
    """
    Render the About page.
    App description and technology stack information.
    """
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

    # Technology stack metrics
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("UI",       "Streamlit")
    t2.metric("Data",     "Pandas / NumPy")
    t3.metric("Charts",   "Plotly")
    t4.metric("AI model", "OpenRouter")
