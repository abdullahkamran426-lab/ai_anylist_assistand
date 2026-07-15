"""
Visualizations page
===================
Expanded Plotly-based chart gallery with the core portfolio of statistical visuals.
"""

import streamlit as st

from modules.visualization import (
    plot_area,
    plot_bar,
    plot_bubble,
    plot_box,
    plot_correlation_matrix,
    plot_histogram,
    plot_line,
    plot_pie,
    plot_scatter,
    plot_sunburst,
    plot_treemap,
    plot_violin,
)


def render_visualizations_page():
    df = st.session_state.df

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

    st.markdown("""
    <div class='explore-hero'>
        <div class='eh-icon'>📈</div>
        <div>
            <div class='eh-title'>Visualizations</div>
            <div class='eh-sub'>Interactive charts for distributions, relationships, and structure</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nums = df.select_dtypes(include="number").columns.tolist()
    cats = df.select_dtypes(exclude="number").columns.tolist()

    default_chart = st.session_state.selected_chart_type or "📊 Bar"
    chart_options = ["📊 Bar", "📈 Histogram", "🥧 Pie", "📉 Scatter", "📦 Box Plot", "🎻 Violin Plot", "📐 Line Chart", "📈 Area Chart", "🫧 Bubble Chart", "🌳 Treemap", "🌞 Sunburst", "🧮 Correlation Matrix"]
    chart = st.radio("Chart type", chart_options, horizontal=True, index=chart_options.index(default_chart), label_visibility="collapsed")

    preselect_col = st.session_state.selected_chart_column
    st.session_state.selected_chart_type = None
    st.session_state.selected_chart_column = None

    picker_col, chart_col = st.columns([1, 2.4], gap="large")
    with picker_col:
        st.markdown("<div class='stat-panel'><h4>⚙️ Chart settings</h4>", unsafe_allow_html=True)
        selected_col = None
        x_col = y_col = size_col = None

        if chart in {"📊 Bar", "🥧 Pie"} and cats:
            idx = cats.index(preselect_col) if preselect_col in cats else 0
            selected_col = st.selectbox("Category column", cats, index=idx)
        elif chart in {"📈 Histogram", "📦 Box Plot", "🎻 Violin Plot"} and nums:
            idx = nums.index(preselect_col) if preselect_col in nums else 0
            selected_col = st.selectbox("Numeric column", nums, index=idx)
        elif chart in {"📉 Scatter", "📐 Line Chart", "📈 Area Chart", "🫧 Bubble Chart"} and len(nums) >= 2:
            x_col = st.selectbox("X axis", nums)
            y_col = st.selectbox("Y axis", nums, index=min(1, len(nums) - 1))
            if chart == "🫧 Bubble Chart":
                size_col = st.selectbox("Bubble size", nums + [None], index=len(nums))
        elif chart == "🌳 Treemap" and len(cats) >= 1:
            selected_col = st.selectbox("Category column", cats)
        elif chart == "🌞 Sunburst" and len(cats) >= 2:
            selected_col = st.selectbox("Category column", cats)
        elif chart == "🧮 Correlation Matrix" and len(nums) >= 2:
            st.caption("Correlation matrix uses all numeric columns.")
        else:
            st.caption("Not enough columns for this chart type.")
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_col:
        st.markdown("<div class='chart-card'><div class='cc-title'>Interactive visualization</div>", unsafe_allow_html=True)
        if chart == "📊 Bar" and cats and selected_col:
            st.plotly_chart(plot_bar(df, selected_col))
        elif chart == "📈 Histogram" and nums and selected_col:
            st.plotly_chart(plot_histogram(df, selected_col))
        elif chart == "🥧 Pie" and cats and selected_col:
            st.plotly_chart(plot_pie(df, selected_col))
        elif chart == "📉 Scatter" and x_col and y_col:
            st.plotly_chart(plot_scatter(df, x_col, y_col))
        elif chart == "📦 Box Plot" and nums and selected_col:
            st.plotly_chart(plot_box(df, selected_col))
        elif chart == "🎻 Violin Plot" and nums and selected_col:
            st.plotly_chart(plot_violin(df, selected_col))
        elif chart == "📐 Line Chart" and x_col and y_col:
            st.plotly_chart(plot_line(df, x_col, y_col))
        elif chart == "📈 Area Chart" and x_col and y_col:
            st.plotly_chart(plot_area(df, x_col, y_col))
        elif chart == "🫧 Bubble Chart" and x_col and y_col:
            st.plotly_chart(plot_bubble(df, x_col, y_col, size_col=size_col))
        elif chart == "🌳 Treemap" and selected_col:
            st.plotly_chart(plot_treemap(df, [selected_col], selected_col))
        elif chart == "🌞 Sunburst" and selected_col:
            st.plotly_chart(plot_sunburst(df, [selected_col], selected_col))
        elif chart == "🧮 Correlation Matrix" and len(nums) >= 2:
            st.plotly_chart(plot_correlation_matrix(df))
        else:
            st.info("Not enough columns of the required type for this chart.")
        st.markdown("</div>", unsafe_allow_html=True)
