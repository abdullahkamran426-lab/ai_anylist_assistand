"""
Sidebar Rendering Module - Application Navigation and Status
=============================================================

This file handles the rendering of the application sidebar, which is the primary
navigation interface for DataLens. The sidebar provides access to all pages and
displays dataset status information.

Purpose:
--------
- Provides main navigation interface for the application
- Displays dataset status (loaded/not loaded)
- Shows dataset information when data is loaded
- Allows users to clear/reset the dataset
- Displays app branding and footer

Key Functions:
--------------
- render_sidebar(): Main function that renders the complete sidebar
  - Returns the selected page name for routing in main.py
  - Displays logo, navigation, dataset status, and footer
  - Handles dataset clearing functionality

Components:
-----------
1. Logo and Branding: App logo with pulsing "AI Analysis" status indicator
2. Navigation Radio: Radio buttons for all pages defined in NAV_OPTIONS
3. Dataset Status Badge: Shows filename, row count, column count when data loaded
4. Clear Dataset Button: Allows users to reset the app state
5. Footer: App branding and version information

Navigation:
-----------
The navigation uses radio buttons (st.radio) which provides a clean, single-selection
interface. The selected page is returned and used in main.py for routing.

Dataset Status:
--------------
When a dataset is loaded, the sidebar displays:
- Filename of the uploaded CSV
- Number of rows and columns
- Quality score (calculated in analysis.py)
- Clear dataset button to reset state

Integration:
------------
- Uses NAV_OPTIONS from config.py for page list
- Uses clear_dataset_state() from session.py for reset functionality
- Returns selected page to main.py for routing
"""

import streamlit as st
from modules.config import NAV_OPTIONS
from modules.session import clear_dataset_state


def render_sidebar():
    """
    Render the complete sidebar and return the selected page.
    
    Returns:
        str: The selected page name from NAV_OPTIONS
    
    The sidebar includes:
    1. Logo and app name with pulsing "AI Analysis" status dot
    2. Navigation radio buttons for all pages
    3. Dataset status badge (shown only when data is loaded)
    4. Clear dataset button (shown only when data is loaded)
    5. Footer with app branding
    """
    # ============================================================================
    # SIDEBAR CONTAINER
    # Everything inside this `with` block renders in the left sidebar column
    # ============================================================================
    with st.sidebar:
        
        # ------------------------------------------------------------------------
        # LOGO AND BRANDING
        # Display app logo, name, and pulsing "AI Analysis" status indicator
        # ------------------------------------------------------------------------
        st.markdown("""
        <style>
        @keyframes pulse-dot { 0%,100% { opacity:1; } 50% { opacity:.35; } }
        </style>
        <div style='display:flex;align-items:center;gap:12px;padding:6px 2px 22px'>
            <div style='width:40px;height:40px;border-radius:11px;flex-shrink:0;
                        background:linear-gradient(135deg,#6366f1,#818cf8);
                        display:flex;align-items:center;justify-content:center;
                        font-size:1.15rem;box-shadow:0 6px 18px rgba(99,102,241,.35)'>🔬</div>
            <div>
                <div style='font-family:Space Grotesk;font-size:1.15rem;font-weight:700;
                            color:#fff;line-height:1.1'>DataLens</div>
                <div style='display:flex;align-items:center;gap:5px;margin-top:2px'>
                    <span style='width:6px;height:6px;border-radius:50%;background:#22d3a5;
                                display:inline-block;animation:pulse-dot 2s infinite'></span>
                    <span style='color:#64748b;font-size:.68rem;font-weight:600;
                                letter-spacing:.08em;text-transform:uppercase'>AI Analysis</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ------------------------------------------------------------------------
        # NAVIGATION CONTROL
        # Radio buttons for page navigation with cross-page redirect support
        # ------------------------------------------------------------------------
        
        # Cross-page navigation trick: other pages can set st.session_state.redirect_to
        # to a page name and call st.rerun() to force the sidebar radio to open on that page.
        # We consume it once here (read it into _default_index, then clear it) so it doesn't
        # keep forcing that page on every future rerun.
        _default_index = 0
        if st.session_state.redirect_to in NAV_OPTIONS:
            _default_index = NAV_OPTIONS.index(st.session_state.redirect_to)
            st.session_state.redirect_to = None

        # The actual navigation control
        # Its visible label is hidden because the logo block above already establishes context
        page = st.radio(
            "Navigation",
            NAV_OPTIONS,
            index=_default_index,
            label_visibility="collapsed",
        )

        # ------------------------------------------------------------------------
        # DATASET STATUS BADGE
        # Only shown once a file has been uploaded
        # Shows filename, row/column count, and data health percentage
        # ------------------------------------------------------------------------
        if st.session_state.df is not None:
            df_info = st.session_state.df
            total_cells = df_info.shape[0] * df_info.shape[1]
            missing_cells = int(df_info.isna().sum().sum())
            
            # Calculate data health percentage (cells that are NOT missing)
            # Guard against division by zero for empty dataframe
            health_pct = 100 if total_cells == 0 else round(100 - (missing_cells / total_cells * 100), 1)
            
            # Traffic-light coloring based on data health
            health_color = "#22d3a5" if health_pct >= 90 else ("#fbbf24" if health_pct >= 70 else "#f87171")

            # Render the dataset status badge
            st.markdown("<div class='div' style='margin:18px 0 14px'></div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,rgba(99,102,241,.12) 0%,rgba(99,102,241,.03) 100%);
                        border:1px solid rgba(99,102,241,.3);border-radius:12px;padding:16px;'>
                <div style='display:flex;align-items:center;gap:8px;margin-bottom:10px'>
                    <span style='font-size:.95rem'>📁</span>
                    <span style='font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;
                                color:#818cf8;font-weight:700'>Active Dataset</span>
                </div>
                <div style='color:#e2e8f0;font-weight:600;font-size:.87rem;
                            word-break:break-all;margin-bottom:8px'>{st.session_state.filename}</div>
                <div style='color:#94a3b8;font-size:.78rem;margin-bottom:10px'>
                    {df_info.shape[0]:,} rows &nbsp;·&nbsp; {df_info.shape[1]} columns
                </div>
                <div style='display:flex;justify-content:space-between;font-size:.7rem;
                            color:#64748b;margin-bottom:4px'>
                    <span>Data health</span><span style='color:{health_color};font-weight:700'>{health_pct}%</span>
                </div>
                <div style='background:rgba(255,255,255,.06);border-radius:99px;height:5px;overflow:hidden'>
                    <div style='width:{health_pct}%;height:100%;background:{health_color};border-radius:99px'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ------------------------------------------------------------------------
            # CLEAR DATASET BUTTON
            # Wipes every piece of state tied to the current dataset
            # Then reruns to reflect the cleared state
            # ------------------------------------------------------------------------
            if st.button("Clear dataset", key="clear_dataset"):
                clear_dataset_state()
                st.rerun()

        # ------------------------------------------------------------------------
        # FOOTER
        # App branding at the bottom of the sidebar
        # ------------------------------------------------------------------------
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style='color:#4b5065;font-size:.68rem;text-align:center;letter-spacing:.03em'>
            DataLens · Streamlit + Plotly + AI
        </div>
        """, unsafe_allow_html=True)

    # Return the selected page for routing in main.py
    return page
