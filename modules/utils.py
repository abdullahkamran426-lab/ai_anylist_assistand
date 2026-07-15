"""
Shared UI Helpers
==================
Small, page-agnostic helper functions used by more than one page module.
Extracted verbatim (same behavior, same output) from the original monolithic
main.py, where they lived as plain top-level functions.
"""

import streamlit as st
import pandas as pd


def section(label: str, title: str):
    """Render the small-uppercase-eyebrow + large-title heading pattern used
    at the top of most pages (e.g. label='ANALYSIS', title='Statistical Summary').
    Kept as a function so every page gets an identical, consistently-styled heading."""
    st.markdown(f"<div class='section-label'>{label}</div>"
                f"<div class='section-title'>{title}</div>",
                unsafe_allow_html=True)


def sample_df_for_speed(frame: pd.DataFrame, enabled: bool, n: int = 50_000) -> pd.DataFrame:
    """Return a random sample of `frame` when enabled and it's large; otherwise the frame itself.

    Args:
        frame:   the dataframe to (maybe) sample.
        enabled: whether the user has opted into sampling (checkbox on the page).
        n:       max rows to keep when sampling.
    A fixed `random_state=42` keeps the sample identical across reruns, so
    numbers don't visibly jump around every time a widget is touched.
    """
    if enabled and len(frame) > n:
        return frame.sample(n, random_state=42)
    return frame
