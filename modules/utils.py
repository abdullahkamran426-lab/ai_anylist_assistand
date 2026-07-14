"""
Utility Functions
This file contains helper functions used throughout the application.
"""

import streamlit as st
import pandas as pd
from modules.config import LARGE_DF_THRESHOLD


def section(label: str, title: str):
    """
    Render a consistent section header pattern.
    
    This function renders the small-uppercase-eyebrow + large-title heading pattern
    used at the top of most pages (e.g. label='ANALYSIS', title='Statistical Summary').
    Keeping this as a function ensures every page gets an identical, consistently-styled heading.
    
    Args:
        label (str): Small uppercase label (e.g., 'ANALYSIS', 'CAPABILITIES')
        title (str): Large title (e.g., 'Statistical Summary', 'Everything you need')
    """
    st.markdown(f"<div class='section-label'>{label}</div>"
                f"<div class='section-title'>{title}</div>",
                unsafe_allow_html=True)


def sample_df_for_speed(frame: pd.DataFrame, enabled: bool, n: int = 50_000) -> pd.DataFrame:
    """
    Return a random sample of the dataframe when enabled and it's large.
    Otherwise return the frame itself.
    
    This function is used to keep Statistics/Visualizations responsive on large CSVs.
    When the dataframe exceeds the threshold, we offer to work on a random sample.
    
    Args:
        frame (pd.DataFrame): The dataframe to (maybe) sample
        enabled (bool): Whether the user has opted into sampling (checkbox on the page)
        n (int): Max rows to keep when sampling (default: 50,000)
    
    Returns:
        pd.DataFrame: Either the original frame or a sampled version
    
    Note:
        A fixed random_state=42 keeps the sample identical across reruns,
        so numbers don't visibly jump around every time a widget is touched.
    """
    if enabled and len(frame) > n:
        return frame.sample(n, random_state=42)
    return frame
