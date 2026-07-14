"""
Page Rendering Functions
=========================
This package contains all page-rendering functions for the DataLens
application. It used to be a single ~1,100-line pages.py; it's now split into
one module per page so each is easier to find, read, and edit independently:

    pages/
        home.py               render_home_page()
        upload.py             render_upload_page()
        clean_data.py         render_clean_data_page()
        dataset_preview.py    render_dataset_preview_page()
        statistics.py         render_statistics_page()
        visualizations.py     render_visualizations_page()
        ai_assistant.py       render_ai_assistant_page()
        export_report.py      render_export_page()
        about.py              render_about_page()

Each function renders one complete page and should be called from main.py
based on the page selected in the sidebar navigation.

The imports below re-export every render_* function at the package level, so
existing code that did:

    from pages import render_home_page, render_upload_page, ...

continues to work completely unchanged — only the internal file layout moved.
"""

from .home import render_home_page
from .upload import render_upload_page
from .clean_data import render_clean_data_page
from .dataset_preview import render_dataset_preview_page
from .statistics import render_statistics_page
from .visualizations import render_visualizations_page
from .ai_assistant import render_ai_assistant_page
from .export_report import render_export_page
from .about import render_about_page

__all__ = [
    "render_home_page",
    "render_upload_page",
    "render_clean_data_page",
    "render_dataset_preview_page",
    "render_statistics_page",
    "render_visualizations_page",
    "render_ai_assistant_page",
    "render_export_page",
    "render_about_page",
]
