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

Educational Note for Students:
-----------------------------
Descriptive statistics help us summarize the properties of a dataset. In this module,
we implement several important algorithms:

1. Standard Deviation Degrees of Freedom (`ddof=0`): In standard statistical formulas,
   dividing by N (number of observations) assumes we are calculating the population
   standard deviation, while N-1 assumes a sample. We use `ddof=0` (Delta Degrees of Freedom = 0)
   to divide by N, matching standard numpy behaviors.
   
2. Z-Score Outlier Detection: A Z-score measures how many standard deviations a data point
   is from the mean. The formula is: Z = (x - mean) / std. Any data point with an absolute
   Z-score greater than 3 (|Z| > 3) is commonly flagged as an outlier (Empirical Rule).
   
3. Correlation Matrix & Filtering: Pearson correlation coefficient ranges from -1 to +1,
   describing the linear relationship between two variables. We use nested loops to find
   pairs with high correlation (>= 0.7), preventing duplicate pairs by starting the inner
   loop after the outer loop's index (`i + 1`).
   
4. Quality Score Heuristic: A simple weighted score starting at 100. It docks points based on
   the proportion of missing values (60% weight) and duplicated rows (40% weight).
"""

import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data
def get_summary(df, filename):
    """
    Compact narrative summary of the dataset.
    This is passed to the AI model so it can answer questions with context
    without needing to download or process millions of raw rows directly.
    """
    # Group columns by data type
    numeric = df.select_dtypes(include=np.number)
    categorical = df.select_dtypes(exclude=np.number)
    
    # Analyze missing values
    missing = df.isna().sum().sort_values(ascending=False)
    missing_summary = ", ".join(f"{col}: {int(cnt)}" for col, cnt in missing[missing > 0].head(8).items()) or "None"

    # Compile the summary text
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

    # Show top 3 most common values for the first 5 categorical columns
    if not categorical.empty:
        for column in categorical.columns[:5]:
            top = df[column].value_counts(dropna=False).head(3)
            if not top.empty:
                summary_lines.append(f"{column}: {top.to_dict()}")

    return "\n".join(summary_lines)


def get_numeric_stats(df):
    """
    Extended descriptive statistics for every numeric column.
    
    This includes:
    - Count, mean, min, max (standard pandas describe())
    - Median (50th percentile)
    - Variance: How far numbers are spread out from the mean.
    - Standard Deviation: Average distance of data points from the mean.
    - Skewness: Degree of asymmetry of the distribution (positive = tail on right, negative = tail on left).
    - Kurtosis: Measures how heavy or light the tails of the distribution are.
    - IQR (Interquartile Range): Width of the middle 50% of data (75th percentile - 25th percentile).
    - Range: Maximum value minus minimum value.
    - Outliers count: Count of values outside 3 standard deviations from the mean.
    """
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        return None

    # Get baseline stats
    stats = numeric.describe().T
    
    # Calculate advanced parameters
    stats["median"] = numeric.median()
    stats["variance"] = numeric.var(ddof=0)  # ddof=0 calculates population variance
    stats["std"] = numeric.std(ddof=0)       # ddof=0 calculates population standard deviation
    stats["skewness"] = numeric.skew()
    stats["kurtosis"] = numeric.kurt()
    stats["iqr"] = numeric.quantile(0.75) - numeric.quantile(0.25)
    stats["range"] = numeric.max() - numeric.min()
    stats["missing"] = numeric.isna().sum()
    
    # Detect outliers using Z-score logic: count cells where |Z| > 3
    stats["outliers"] = numeric.apply(lambda s: int(((s - s.mean()).abs() > 3 * s.std()).sum()))

    # Sort columns in a logical reading order
    columns = ["count", "mean", "median", "std", "variance", "min", "max",
               "range", "iqr", "skewness", "kurtosis", "missing", "outliers"]
    return stats[columns].round(4)


def get_category_counts(df, col):
    """Value counts (including NaN) for a categorical column, top 20."""
    return df[col].value_counts(dropna=False).head(20)


def calculate_quality_score(df):
    """
    Calculate a data quality score (0 to 100).
    
    Logic:
    - Starts at 100.
    - Missing cells ratio is penalized (weighted 60% of the penalty).
    - Duplicate rows ratio is penalized (weighted 40% of the penalty).
    - Ensures score never drops below 0.
    """
    if df.empty:
        return 100
    score = 100.0
    
    # Total missing cells divided by total capacity (rows * columns)
    missing_ratio = df.isna().sum().sum() / (df.shape[0] * df.shape[1]) if df.shape[0] and df.shape[1] else 0
    
    # Total duplicate rows divided by number of rows
    duplicate_ratio = df.duplicated().sum() / len(df) if len(df) else 0
    
    # Apply penalties
    score -= missing_ratio * 100 * 0.6
    score -= duplicate_ratio * 100 * 0.4
    return max(0, round(score))


def get_missing_summary(df):
    """
    Per-column missing count + percentage.
    Filters out columns with no missing data, sorted highest-to-lowest.
    """
    missing = df.isna().sum().sort_values(ascending=False)
    missing = missing[missing > 0]
    return missing.to_frame(name="missing_count").assign(share=lambda s: round(s["missing_count"] / len(df) * 100, 2))


def get_correlation_insights(df):
    """
    Find pairs of columns with a strong linear relationship (|correlation| >= 0.7).
    
    How the nested loops work:
    To avoid comparing Column A with Column A (which is always 1.0) and avoid listing both
    (Column A, Column B) and (Column B, Column A), we use index slicing.
    The inner loop starts at `i + 1` relative to the outer loop's index `i`.
    """
    numeric = df.select_dtypes(include=np.number)
    if numeric.shape[1] < 2:
        return []
        
    # Calculate correlation matrix using Pearson correlation
    corr = numeric.corr().abs()
    pairs = []
    
    # Nested loops using column indices
    for i, col_a in enumerate(corr.columns):
        for col_b in corr.columns[i + 1:]:
            value = corr.loc[col_a, col_b]
            if value >= 0.7:
                pairs.append((col_a, col_b, round(float(value), 3)))
    return pairs


def get_outlier_summary(df):
    """
    Per numeric column, count of values with |z-score| > 3, sorted worst-first.
    
    Z-Score formula: Z = (X - Mean) / StdDev.
    Values greater than 3 standard deviations away from the mean are counted.
    """
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        return pd.DataFrame(columns=["column", "outliers"])
        
    outliers = []
    for column in numeric.columns:
        series = numeric[column].dropna()
        # Columns with constant values (std == 0) or empty columns cannot have standard Z-scores
        if series.empty or series.std(ddof=0) == 0:
            continue
            
        # Z-Score math
        z = (series - series.mean()) / series.std(ddof=0)
        outliers.append({"column": column, "outliers": int((z.abs() > 3).sum())})
        
    # Convert list to DataFrame and sort it
    return pd.DataFrame(outliers).sort_values("outliers", ascending=False).reset_index(drop=True)
