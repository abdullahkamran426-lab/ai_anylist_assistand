"""
CSS Styling for DataLens Application
=====================================
Streamlit doesn't expose a theming API rich enough for a fully custom look,
so the whole app's visual design is injected as one raw CSS stylesheet via
st.markdown(..., unsafe_allow_html=True). This package used to be a single
~560-line styles.py; it's now split into one module per visual area so each
piece is easier to find and edit:

    modules/style/
        base.py      Fonts, CSS variable palette, base html/body rules
        sidebar.py   Sidebar navigation re-skin
        widgets.py   Generic Streamlit widget skins (buttons, dataframe, etc.)
        layout.py    Custom layout primitives shared across pages (.hero, .pill, ...)
        upload.py    Upload Dataset page-specific styling
        explore.py   Dataset Preview / Statistics / Visualizations styling

The public API is unchanged from the original single-file styles.py:
call `inject_css()` once, right after st.set_page_config(), in main.py
(import as `from modules.style import inject_css`).
"""

import streamlit as st

from .base import BASE_CSS
from .sidebar import SIDEBAR_CSS
from .widgets import WIDGETS_CSS
from .layout import LAYOUT_CSS
from .upload import UPLOAD_CSS
from .explore import EXPLORE_CSS

# Order matters only in the sense that later rules can override earlier ones
# on equal CSS specificity — this order mirrors the original styles.py so
# behavior is unchanged: base variables/fonts first, then generic widget/
# layout skins, then the two page-group-specific stylesheets last.
_CSS_MODULES = [
    BASE_CSS,
    SIDEBAR_CSS,
    WIDGETS_CSS,
    LAYOUT_CSS,
    UPLOAD_CSS,
    EXPLORE_CSS,
]


def get_css() -> str:
    """
    Returns the complete CSS string for the application, wrapped in a single
    <style> tag — identical output to the original monolithic styles.py's
    get_css(), just assembled from the split modules above instead of one
    long literal string.
    """
    combined_rules = "\n".join(module.strip("\n") for module in _CSS_MODULES)
    return f"<style>\n{combined_rules}\n</style>\n"


def inject_css() -> None:
    """
    Injects the complete CSS stylesheet into the Streamlit application.
    Call this function once at the beginning of main.py, right after
    st.set_page_config().
    """
    st.markdown(get_css(), unsafe_allow_html=True)
