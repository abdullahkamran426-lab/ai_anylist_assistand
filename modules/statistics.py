"""
Statistics
==========
Everything that describes/summarizes a dataset without changing it:
    - get_summary()              narrative summary fed to the AI assistant
    - get_numeric_stats()        extended descriptive stats (variance, skew,
                                  kurtosis, IQR, range, outliers, ...)
    - get_category_counts()      value_counts() for one categorical column
    - calculate_quality_score()  0-100 heuristic data-health score
    - get_missing_summary()      per-column missing count/percentage
    - get_correlation_insights() strong numeric correlation pairs
    - get_outlier_summary()      per-column z-score outlier counts

Note: `statistics.py` is a submodule of the `modules` package, imported
elsewhere as `from modules.statistics import ...` (absolute import), so it
does not shadow or conflict with Python's standard-library `statistics`
module — that module is a completely separate top-level package.
"""

import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data
def get_summary(df, filename):
    """Compact narrative summary of the dataset, fed to the AI assistant as
    context so it can answer questions without seeing every raw row."""
    numeric = df.select_dtypes(include=np.number)
    categorical = df.select_dtypes(exclude=np.number)
    missing = df.isna().sum().sort_values(ascending=False)
    missing_summary = ", ".join(f"{col}: {int(cnt)}" for col, cnt in missing[missing > 0].head(8).items()) or "None"

    summary_lines = [
        f"File: {filename or 'dataset'}",
        f"Rows: {df.shape[0]:,}",
        f"Columns: {df.shape[1]}",
        f"Numeric columns: {', '.join(numeric.columns.tolist()) if len(numeric.columns) else 'None'}",
        f"Categorical columns: {', '.join(categorical.columns.tolist()) if len(categorical.columns) else 'None'}",
        f"Missing values: {missing_summary}",
        "Quick stats:",
        numeric.describe().round(2).to_string() if not numeric.empty else "No numeric columns",
        "",
        "Top values:",
    ]

    if not categorical.empty:
        for column in categorical.columns[:5]:
            top = df[column].value_counts(dropna=False).head(3)
            if not top.empty:
                summary_lines.append(f"{column}: {top.to_dict()}")

    return "\n".join(summary_lines)


def get_numeric_stats(df):
    """Extended descriptive statistics for every numeric column: the usual
    count/mean/min/max plus variance, std, skewness, kurtosis, IQR, range,
    missing count, and a simple z-score outlier count (|z| > 3)."""
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        return None

    stats = numeric.describe().T
    stats["median"] = numeric.median()
    stats["variance"] = numeric.var(ddof=0)
    stats["std"] = numeric.std(ddof=0)
    stats["skewness"] = numeric.skew()
    stats["kurtosis"] = numeric.kurt()
    stats["iqr"] = numeric.quantile(0.75) - numeric.quantile(0.25)
    stats["range"] = numeric.max() - numeric.min()
    stats["missing"] = numeric.isna().sum()
    stats["outliers"] = numeric.apply(lambda s: int(((s - s.mean()).abs() > 3 * s.std()).sum()))

    columns = ["count", "mean", "median", "std", "variance", "min", "max",
               "range", "iqr", "skewness", "kurtosis", "missing", "outliers"]
    return stats[columns].round(4)


def get_category_counts(df, col):
    """Value counts (including NaN) for a categorical column, top 20."""
    return df[col].value_counts(dropna=False).head(20)


def calculate_quality_score(df):
    """0-100 heuristic score: starts at 100, docked for missing cells
    (weighted 60%) and duplicate rows (weighted 40%)."""
    if df.empty:
        return 100
    score = 100.0
    missing_ratio = df.isna().sum().sum() / (df.shape[0] * df.shape[1]) if df.shape[0] and df.shape[1] else 0
    duplicate_ratio = df.duplicated().sum() / len(df) if len(df) else 0
    score -= missing_ratio * 100 * 0.6
    score -= duplicate_ratio * 100 * 0.4
    return max(0, round(score))


def get_missing_summary(df):
    """Per-column missing count + percentage, sorted worst-first, columns
    with zero missing values excluded."""
    missing = df.isna().sum().sort_values(ascending=False)
    missing = missing[missing > 0]
    return missing.to_frame(name="missing_count").assign(share=lambda s: round(s["missing_count"] / len(df) * 100, 2))


def get_correlation_insights(df):
    """List of (col_a, col_b, |correlation|) triples for every numeric pair
    with |correlation| >= 0.7 — i.e. only the "strong" relationships."""
    numeric = df.select_dtypes(include=np.number)
    if numeric.shape[1] < 2:
        return []
    corr = numeric.corr().abs()
    pairs = []
    for i, col_a in enumerate(corr.columns):
        for col_b in corr.columns[i + 1:]:
            value = corr.loc[col_a, col_b]
            if value >= 0.7:
                pairs.append((col_a, col_b, round(float(value), 3)))
    return pairs


def get_outlier_summary(df):
    """Per numeric column, count of values with |z-score| > 3, worst first."""
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        return pd.DataFrame(columns=["column", "outliers"])
    outliers = []
    for column in numeric.columns:
        series = numeric[column].dropna()
        if series.empty or series.std(ddof=0) == 0:
            continue
        z = (series - series.mean()) / series.std(ddof=0)
        outliers.append({"column": column, "outliers": int((z.abs() > 3).sum())})
    return pd.DataFrame(outliers).sort_values("outliers", ascending=False).reset_index(drop=True)
