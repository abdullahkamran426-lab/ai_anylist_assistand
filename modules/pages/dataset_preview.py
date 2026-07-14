"""
Dataset Preview page
====================
Full table view of the current dataset, with a column-name search
box to narrow which columns are shown.
"""

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
