"""
Dataset Preview page
====================
Full table view of the current dataset, split across two tabs:
- Data Table: searchable column view of the raw rows.
- Column Details: a "data dictionary" grid — one card per column showing
  its detected type, unique-value count, missing-value rate, and a visual
  completeness bar.
"""

import html

import pandas as pd
import streamlit as st


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
    # TABS: Data Table / Column Details
    # ------------------------------------------------------------------------
    tab_table, tab_cols = st.tabs(["📋 Data Table", "🧬 Column Details"])

    # ========================================================================
    # DATA TABLE TAB
    # Full table view with column-name search
    # ========================================================================
    with tab_table:
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

        st.dataframe(shown_df, height=460)

    # ========================================================================
    # COLUMN DETAILS TAB
    # A "data dictionary" card grid: one chip per column showing detected
    # type, unique-value count, missing rate, and a completeness bar.
    # ========================================================================
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
            # Bar WIDTH represents completeness (100% - missing%), not missing%
            # directly — a fully clean column should fill the whole bar green;
            # a column that's mostly missing should show a short, red bar.
            # Clamped to [2, 100] so a completely empty column still renders a
            # visible sliver instead of vanishing entirely.
            completeness = max(0.0, min(100.0, 100 - pct_missing))
            bar_width = max(completeness, 2)
            # Escaping the column name protects against any quote/angle-bracket
            # character in a real-world CSV header breaking out of the HTML
            # attribute it sits in — which is exactly what causes a card's
            # raw markup to spill out as visible text instead of rendering.
            safe_col = html.escape(str(col))
            # IMPORTANT: chip HTML must be compact with NO leading whitespace.
            # Markdown treats 4+ leading spaces on a new line as a code block,
            # rendering raw tags as visible text instead of actual elements.
            chip = (
                f"<div class='col-chip'>"
                f"<div class='cc-name' title='{safe_col}'>{safe_col}</div>"
                f"<span class='cc-type {css_class}'>{label}</span>"
                f"<div class='cc-meta'>{uniq:,} unique · {nulls:,} missing ({pct_missing}%)</div>"
                f"<div class='cc-bar'><div class='cc-bar-fill' style='width:{bar_width}%;background:{bar_color}'></div></div>"
                f"</div>"
            )
            chips.append(chip)
        st.markdown(f"<div class='col-chip-grid'>{''.join(chips)}</div>", unsafe_allow_html=True)
