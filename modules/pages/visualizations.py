"""
Visualizations page
===================
Bar, histogram, pie and scatter charts powered by Plotly. Honors a
one-time column/chart-type preselection set by the Statistics page's
"visualize this column" shortcut (read from st.session_state, then
cleared so it doesn't stick on later visits).
"""

import streamlit as st

from modules.visualization import plot_bar, plot_histogram, plot_pie, plot_scatter


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
