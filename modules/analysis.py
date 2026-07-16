"""
analysis.py — backward-compatible facade
=========================================
This file used to contain everything (data loading, cleaning, statistics,
PDF export, and AutoML) in one ~850-line module, which is what caused the
original corruption: duplicate logic and orphaned code from merged edits
eventually left dead code sitting at module scope that crashed on import.

It's now split into six focused modules:

    data_loading.py    load_data, compute_file_hash
    data_cleaning.py   clean_data
    encoding.py         get_encoding_recommendations, apply_one_hot_encoding,
                        apply_label_encoding
    statistics.py      get_summary, get_numeric_stats, get_category_counts,
                        calculate_quality_score, get_missing_summary,
                        get_correlation_insights, get_outlier_summary
    pdf_export.py       ReportPDF, chart builders, export_dataset_report,
                        export_to_pdf
    automl.py           detect_prediction_problem, train_prediction_model,
                        predict_with_model, save/load_prediction_model,
                        forecast_regression_series

This file re-exports everything from those five modules under the same
names as before, so existing code elsewhere in the project — e.g.
pages.py's `from modules.analysis import load_data, clean_data,
get_summary, get_numeric_stats, get_category_counts, export_to_pdf` —
keeps working with zero changes. New code should prefer importing
directly from the specific module (e.g. `from modules.automl import
train_prediction_model`) since that's clearer about what it depends on;
this facade exists purely for compatibility.
"""

from modules.data_loading import compute_file_hash, load_data
from modules.data_cleaning import clean_data
from modules.encoding import (
    get_encoding_recommendations,
    apply_one_hot_encoding,
    apply_label_encoding,
)
from modules.statistics import (
    get_summary,
    get_numeric_stats,
    get_category_counts,
    calculate_quality_score,
    get_missing_summary,
    get_correlation_insights,
    get_outlier_summary,
)
from modules.pdf_export import (
    PRIMARY,
    SECONDARY,
    SUCCESS,
    WARNING,
    DANGER,
    LIGHT,
    DARK,
    ReportPDF,
    create_histogram,
    create_missing_chart,
    create_dtype_chart,
    create_pie_chart,
    create_heatmap,
    add_statistics,
    add_ai_insights,
    add_recommendations,
    add_summary,
    export_dataset_report,
    export_to_pdf,
)
from modules.automl import (
    detect_prediction_problem,
    train_prediction_model,
    predict_with_model,
    save_prediction_model,
    load_prediction_model,
    forecast_regression_series,
)

__all__ = [
    "compute_file_hash", "load_data", "clean_data",
    "get_encoding_recommendations", "apply_one_hot_encoding", "apply_label_encoding",
    "get_summary", "get_numeric_stats", "get_category_counts",
    "calculate_quality_score", "get_missing_summary",
    "get_correlation_insights", "get_outlier_summary",
    "PRIMARY", "SECONDARY", "SUCCESS", "WARNING", "DANGER", "LIGHT", "DARK",
    "ReportPDF", "create_histogram", "create_missing_chart", "create_dtype_chart",
    "create_pie_chart", "create_heatmap", "add_statistics", "add_ai_insights",
    "add_recommendations", "add_summary", "export_dataset_report", "export_to_pdf",
    "detect_prediction_problem", "train_prediction_model", "predict_with_model",
    "save_prediction_model", "load_prediction_model", "forecast_regression_series",
]
