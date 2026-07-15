"""
Statistics page
===============
Numeric distributions (describe()), missing-value breakdowns, and
categorical value counts, split across three tabs. Offers to sample
large datasets for speed, and lets the user jump straight from a
numeric column here into a pre-filled histogram on the
Visualizations page.
"""

import streamlit as st

from modules.analysis import get_numeric_stats
from modules.config import LARGE_DF_THRESHOLD
from modules.utils import sample_df_for_speed


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
            st.dataframe(stats, width='stretch')
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
        st.dataframe(miss, width='stretch')

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
            st.dataframe(vc, width='stretch')
        else:
            st.info("No categorical columns found.")
