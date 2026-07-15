"""
Data loading, cleaning, statistics, PDF reporting, and AutoML prediction.

This module is the "business logic" layer for DataLens: main.py/pages.py
only orchestrate the UI, everything that touches pandas, matplotlib,
fpdf, or scikit-learn lives here.

Sections in this file, top to bottom:
    1. File I/O            load_data, clean_data, compute_file_hash
    2. Dataset summaries    get_summary, get_numeric_stats, get_category_counts,
                            calculate_quality_score, get_missing_summary,
                            get_correlation_insights, get_outlier_summary
    3. PDF report engine    ReportPDF, chart builders, section helpers,
                            export_dataset_report, export_to_pdf
    4. Prediction (AutoML)  detect_prediction_problem, train_prediction_model,
                            predict_with_model, save/load_prediction_model,
                            forecast_regression_series
"""

import hashlib
import io
import os
import re
import tempfile
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # headless backend — Streamlit has no display, only saves PNGs to disk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import joblib
from fpdf import FPDF

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor


def clean_pdf_text(text):
    """
    Convert Unicode text into Latin-1 safe text for FPDF.
    
    This function handles all Unicode characters by:
    1. Converting to string if None
    2. Replacing common Unicode symbols with ASCII equivalents
    3. Removing any remaining non-Latin-1 characters
    4. Ensuring the result is always a valid Latin-1 string
    """
    if text is None:
        return ""

    text = str(text)

    # Comprehensive Unicode to ASCII replacements
    replacements = {
        # Bullets and dashes
        "•": "-",
        "–": "-",
        "—": "-",
        "−": "-",
        "‐": "-",
        "‑": "-",
        
        # Smart quotes
        """: '"',
        """: '"',
        "'": "'",
        "'": "'",
        "`": "'",
        "´": "'",
        
        # Checkmarks and crosses
        "✓": "[OK]",
        "✔": "[OK]",
        "✕": "[X]",
        "✖": "[X]",
        "✘": "[X]",
        
        # Arrows
        "→": "->",
        "←": "<-",
        "↑": "^",
        "↓": "v",
        "↔": "<->",
        "⇒": "=>",
        "⇐": "<=",
        
        # Mathematical symbols
        "°": " deg",
        "±": "+/-",
        "×": "x",
        "÷": "/",
        "≈": "~",
        "≠": "!=",
        "≤": "<=",
        "≥": ">=",
        "∞": "inf",
        "√": "sqrt",
        
        # Currency symbols
        "€": "EUR",
        "£": "GBP",
        "¥": "JPY",
        "₹": "INR",
        "₽": "RUB",
        
        # Common symbols
        "©": "(c)",
        "®": "(r)",
        "™": "(tm)",
        "§": "section",
        "¶": "paragraph",
        
        # Emojis and pictographs (common ones)
        "📊": "[Chart]",
        "📈": "[Graph]",
        "📉": "[Graph]",
        "📄": "[Doc]",
        "🚀": "[Launch]",
        "💾": "[Save]",
        "🔮": "[Predict]",
        "⬇": "[Download]",
        "✨": "[Star]",
        "⚡": "[Fast]",
        "🤖": "[AI]",
        "🔬": "[Lab]",
        "🏠": "[Home]",
        "📂": "[Folder]",
        "🧹": "[Clean]",
        "🔍": "[Search]",
        "ℹ️": "[Info]",
        
        # Other common Unicode
        "…": "...",
        "—": "-",
        "–": "-",
        "«": "<<",
        "»": ">>",
        "‹": "<",
        "›": ">",
        "‛": "'",
        "‚": ",",
        "„": '"',
        "‟": '"',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove any remaining non-Latin-1 characters
    try:
        # Try to encode as Latin-1, ignoring characters that can't be encoded
        cleaned = text.encode("latin-1", "ignore").decode("latin-1")
        return cleaned
    except (UnicodeEncodeError, UnicodeDecodeError):
        # If that fails, use a more aggressive approach
        try:
            # Replace any non-ASCII characters with their closest ASCII equivalent
            cleaned = text.encode("ascii", "ignore").decode("ascii")
            return cleaned
        except Exception:
            # Last resort: return empty string
            return ""


# ══════════════════════════════════════════════════════════════════════════════
# Report brand colors (RGB tuples — fpdf2's set_fill_color/set_text_color
# both accept *color unpacked like this). Kept as module constants so the
# PDF's palette can be changed in one place.
# ══════════════════════════════════════════════════════════════════════════════
PRIMARY = (67, 97, 238)
SECONDARY = (76, 201, 240)
SUCCESS = (46, 204, 113)
WARNING = (243, 156, 18)
DANGER = (231, 76, 60)
LIGHT = (245, 247, 250)
DARK = (44, 62, 80)


# ══════════════════════════════════════════════════════════════════════════════
# 1. FILE I/O
# ══════════════════════════════════════════════════════════════════════════════

def compute_file_hash(file_bytes):
    """Stable MD5 hash of an uploaded file's raw bytes — used as a cache key."""
    return hashlib.md5(file_bytes).hexdigest()


@st.cache_data
def load_data(file_bytes, filename="dataset"):
    """Load CSV, Excel, JSON, TSV, or Parquet bytes into a pandas DataFrame.

    Dispatches on the file extension in `filename`; CSV/TSV additionally
    fall back through a few common encodings since uploaded files aren't
    guaranteed to be UTF-8.
    """
    name = (filename or "dataset").lower()
    buffer = io.BytesIO(file_bytes)

    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(buffer)

    if name.endswith(".json"):
        return pd.read_json(buffer)

    if name.endswith(".parquet"):
        return pd.read_parquet(buffer)

    if name.endswith((".tsv", ".txt")):
        try:
            return pd.read_csv(buffer, sep="\t", encoding="utf-8")
        except UnicodeDecodeError:
            buffer.seek(0)
            return pd.read_csv(buffer, sep="\t", encoding="cp1252")

    # Default: comma-separated. Try encodings in order of likelihood before
    # giving up to the permissive python engine as a last resort.
    for encoding in ("utf-8", "cp1252", "latin1"):
        try:
            buffer.seek(0)
            return pd.read_csv(buffer, encoding=encoding)
        except UnicodeDecodeError:
            continue
    buffer.seek(0)
    return pd.read_csv(buffer, encoding="latin1", engine="python")


@st.cache_data
def clean_data(df):
    """Baseline auto-clean applied right after upload: trims whitespace on
    text columns, normalizes obvious null-like strings to real NaN, coerces
    common currency/amount columns to numeric, and drops exact duplicate rows.
    Deliberately conservative — this runs automatically, so it must never
    silently change what the data *means*.
    """
    cleaned = df.copy()  # never mutate the cached input in place
    if cleaned.empty:
        return cleaned

    for column in cleaned.columns:
        if cleaned[column].dtype == object:
            cleaned[column] = cleaned[column].astype(str).str.strip()
            cleaned[column] = cleaned[column].replace({"nan": np.nan, "None": np.nan, "": np.nan})

    for column in cleaned.columns:
        if column.lower() in {"gross", "price", "cost", "amount", "revenue"}:
            try:
                cleaned[column] = cleaned[column].astype(str).str.replace(",", "", regex=False)
                cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
            except Exception:
                continue

    return cleaned.drop_duplicates().reset_index(drop=True)


def apply_one_hot_encoding(df, columns=None, drop_first=False):
    """Apply one-hot encoding to specified categorical columns.
    
    Args:
        df: Input DataFrame
        columns: List of column names to encode. If None, encodes all object dtype columns.
        drop_first: If True, drops the first category to avoid multicollinearity (useful for regression)
    
    Returns:
        DataFrame with one-hot encoded columns
    """
    encoded_df = df.copy()
    
    if columns is None:
        columns = encoded_df.select_dtypes(include=['object']).columns.tolist()
    
    for column in columns:
        if column in encoded_df.columns:
            # Get dummies with optional drop_first
            dummies = pd.get_dummies(encoded_df[column], prefix=column, drop_first=drop_first, dtype=int)
            encoded_df = pd.concat([encoded_df.drop(column, axis=1), dummies], axis=1)
    
    return encoded_df


def apply_label_encoding(df, columns=None):
    """Apply label encoding to specified categorical columns.
    
    Args:
        df: Input DataFrame
        columns: List of column names to encode. If None, encodes all object dtype columns.
    
    Returns:
        DataFrame with label encoded columns and a dictionary of encoders for each column
    """
    encoded_df = df.copy()
    encoders = {}
    
    if columns is None:
        columns = encoded_df.select_dtypes(include=['object']).columns.tolist()
    
    for column in columns:
        if column in encoded_df.columns:
            le = LabelEncoder()
            # Handle NaN values by converting to string first
            encoded_df[column] = encoded_df[column].astype(str)
            encoded_df[column] = le.fit_transform(encoded_df[column])
            encoders[column] = le
    
    return encoded_df, encoders


def get_encoding_recommendations(df):
    """Analyze categorical columns and recommend encoding strategy.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Dictionary with encoding recommendations for each categorical column
    """
    categorical = df.select_dtypes(include=['object'])
    recommendations = {}
    
    for column in categorical.columns:
        unique_count = df[column].nunique()
        total_count = len(df)
        cardinality_ratio = unique_count / total_count
        
        if unique_count <= 2:
            recommendation = "Label Encoding (binary)"
            reason = "Binary column - label encoding is most efficient"
        elif unique_count <= 10:
            recommendation = "One-Hot Encoding"
            reason = "Low cardinality - one-hot encoding preserves all information"
        elif cardinality_ratio < 0.05:
            recommendation = "One-Hot Encoding"
            reason = "Low cardinality ratio - one-hot encoding is manageable"
        else:
            recommendation = "Label Encoding or Target Encoding"
            reason = "High cardinality - label encoding reduces dimensionality"
        
        recommendations[column] = {
            "unique_values": unique_count,
            "total_rows": total_count,
            "cardinality_ratio": round(cardinality_ratio, 4),
            "recommended_encoding": recommendation,
            "reason": reason
        }
    
    return recommendations


# ══════════════════════════════════════════════════════════════════════════════
# 2. DATASET SUMMARIES
# ══════════════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════════════
# 3. PDF REPORT ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class ReportPDF(FPDF):
    """FPDF subclass with a branded header band and a footer that stamps the
    generation date + page number on every page automatically."""

    def header(self):
        self.set_fill_color(*PRIMARY)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 16)
        self.cell(0, 12, clean_pdf_text("DataLens AI Report"), ln=True, align="C", fill=True)
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, clean_pdf_text(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}  -  Page {self.page_no()}"), align="C")


def _section_title(pdf, title, subtitle=None):
    """Filled banner section heading, with an optional muted subtitle line."""
    pdf.set_fill_color(*PRIMARY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, clean_pdf_text(title), ln=True, fill=True)
    if subtitle:
        pdf.ln(1)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(0, 5, clean_pdf_text(subtitle))
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)


def _body(pdf, text):
    """Plain wrapped paragraph text."""
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, clean_pdf_text(text))
    pdf.ln(2)


def _add_kpi_card(pdf, title, value, color, x, y, w=45, h=20):
    """One small colored KPI tile (used in a row of 4 across the top of page 1)."""
    pdf.set_fill_color(*color)
    pdf.rect(x, y, w, h, style="F")
    pdf.set_xy(x + 3, y + 3)
    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(w - 6, 4, clean_pdf_text(title), ln=True)
    pdf.set_xy(x + 3, y + 10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(w - 6, 6, clean_pdf_text(str(value)), ln=True)
    pdf.set_text_color(0, 0, 0)


def _ensure_space(pdf, needed_height):
    """Force a page break if the remaining vertical space on the current
    page is smaller than `needed_height` (in mm). Used before every chart
    image so charts never get sliced across a page boundary — a real bug
    in the previous version, which placed images at hardcoded (x, y)
    coordinates regardless of how much text came before them."""
    if pdf.get_y() + needed_height > pdf.page_break_trigger:
        pdf.add_page()


def _create_plot(path, draw_fn):
    """Run `draw_fn` (which does all the actual plt.* calls), save the
    current matplotlib figure to `path`, then close it so figures don't
    leak across repeated report generations in the same Streamlit session."""
    draw_fn()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def create_histogram(df):
    """Histogram of the first numeric column found."""
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        return None
    column = numeric.columns[0]
    path = os.path.join(tempfile.gettempdir(), "histogram.png")

    def draw():
        plt.figure(figsize=(5.5, 3.2))
        plt.hist(numeric[column].dropna(), bins=20, color="#6366f1", edgecolor="black")
        plt.title(f"Histogram · {column}")
        plt.xlabel(column)
        plt.ylabel("Frequency")

    _create_plot(path, draw)
    return path


def create_missing_chart(df):
    """Bar chart of missing-value counts per affected column."""
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if missing.empty:
        return None
    path = os.path.join(tempfile.gettempdir(), "missing.png")

    def draw():
        plt.figure(figsize=(5.5, 3.2))
        missing.plot(kind="bar", color="#f87171")
        plt.title("Missing values by column")
        plt.ylabel("Count")

    _create_plot(path, draw)
    return path


def create_dtype_chart(df):
    """Pie chart of column dtypes (int64 / float64 / object / ...)."""
    counts = df.dtypes.astype(str).value_counts()
    if counts.empty:
        return None
    path = os.path.join(tempfile.gettempdir(), "dtype.png")

    def draw():
        plt.figure(figsize=(4.8, 4.2))
        plt.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=90,
                colors=["#6366f1", "#22d3a5", "#f59e0b", "#ef4444", "#818cf8"])
        plt.title("Column dtypes")

    _create_plot(path, draw)
    return path


def create_pie_chart(df):
    """Pie chart of the top categories in the dataset's most useful
    categorical column (highest cardinality under 12 unique values, so the
    chart stays readable). Falls back to the dtype breakdown if no such
    column exists — this is what satisfies the report's dedicated
    "Pie chart" section, distinct from the dtype-only chart above."""
    categorical = df.select_dtypes(exclude=np.number)
    candidate = None
    for column in categorical.columns:
        nunique = df[column].nunique(dropna=True)
        if 1 < nunique <= 12:
            candidate = column
            break

    if candidate is None:
        return create_dtype_chart(df)

    counts = df[candidate].value_counts(dropna=False).head(8)
    path = os.path.join(tempfile.gettempdir(), "pie.png")

    def draw():
        plt.figure(figsize=(4.8, 4.2))
        plt.pie(counts.values, labels=[str(v) for v in counts.index], autopct="%1.1f%%", startangle=90,
                colors=["#6366f1", "#22d3a5", "#f59e0b", "#ef4444", "#818cf8", "#a78bfa", "#f472b6", "#34d399"])
        plt.title(f"Proportion of {candidate}")

    _create_plot(path, draw)
    return path


def create_heatmap(df):
    """Correlation heatmap across all numeric columns."""
    numeric = df.select_dtypes(include=np.number)
    if numeric.shape[1] < 2:
        return None
    corr = numeric.corr()
    path = os.path.join(tempfile.gettempdir(), "heatmap.png")

    def draw():
        plt.figure(figsize=(5.5, 4.2))
        plt.imshow(corr, cmap="coolwarm")
        plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right", fontsize=8)
        plt.yticks(range(len(corr.columns)), corr.columns, fontsize=8)
        plt.colorbar()
        plt.title("Correlation heatmap")

    _create_plot(path, draw)
    return path


def add_statistics(pdf, df):
    """'Statistical summary' section: per-numeric-column describe() table."""
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        return

    _section_title(pdf, "Statistical Summary", "Descriptive statistics for every numeric column")
    stats = numeric.describe().round(2)

    for column in stats.columns:
        _ensure_space(pdf, 8 + len(stats.index) * 7)

        pdf.set_fill_color(*PRIMARY)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, clean_pdf_text(column), ln=True, fill=True)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 9)
        for idx in stats.index:
            pdf.cell(40, 7, clean_pdf_text(str(idx)), border=1)
            pdf.cell(40, 7, clean_pdf_text(str(stats.loc[idx, column])), border=1, ln=True)
        pdf.ln(4)


def add_ai_insights(pdf, ai_text):
    """'AI insights' section: the AI assistant's most recent answer, boxed."""
    _ensure_space(pdf, 40)
    _section_title(pdf, "AI Insights", "Generated by the AI Assistant from this dataset's summary")

    clean_text = re.sub(r"[^\x00-\x7F]+", " ", ai_text or "No AI insights were generated for this dataset.")
    pdf.set_font("Arial", "", 10)
    pdf.set_fill_color(*LIGHT)
    pdf.multi_cell(0, 8, clean_pdf_text(clean_text[:1200]), border=1, fill=True)
    pdf.ln(4)


def add_recommendations(pdf, df):
    """'Smart recommendations' section: a short checklist derived from
    simple, explainable rules about the dataset's current state."""
    _ensure_space(pdf, 60)
    _section_title(pdf, "Smart Recommendations", "Suggested next steps before modeling")

    recommendations = []
    if df.isna().sum().sum() > 0:
        recommendations.append("Fill or drop missing values before training ML models.")
    if df.duplicated().sum() > 0:
        recommendations.append("Remove duplicate records to avoid biased statistics.")
    if len(df) < 500:
        recommendations.append("More rows would likely improve prediction accuracy.")
    if df.select_dtypes(include=np.number).shape[1] > 1:
        recommendations.append("Review highly correlated features for possible feature selection.")
    recommendations += [
        "Normalize or scale numerical features for distance-based models.",
        "Encode categorical variables (one-hot or ordinal, depending on cardinality).",
        "Always split data into train/test sets before evaluating a model.",
    ]

    pdf.set_font("Arial", "", 10)
    for rec in recommendations:
        pdf.multi_cell(0, 7, f"-  {rec}")
    pdf.ln(3)


def add_summary(pdf, df):
    """'Dataset quality score' closing section: the headline score plus a
    one-line verdict on how ready the data is for analysis/modeling."""
    _ensure_space(pdf, 45)
    score = calculate_quality_score(df)

    pdf.set_fill_color(*PRIMARY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 12, clean_pdf_text(f"Overall Dataset Quality: {score}/100"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    if score >= 90:
        verdict = "Excellent — this dataset is ready for machine learning with minimal prep."
    elif score >= 70:
        verdict = "Good — minor cleaning is recommended before modeling."
    else:
        verdict = "Needs work — address missing values and duplicates before deeper analysis."

    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, clean_pdf_text(verdict))


def export_dataset_report(df, ai_text=""):
    """Build the full branded PDF report and return the path it was saved to.

    Section order matches the product spec: cover → overview → KPI cards →
    dataset info → missing values → statistics → correlation → histogram →
    pie chart → heatmap → AI insights → recommendations → quality score.
    Auto page-breaking (`_ensure_space` + fpdf2's own `set_auto_page_break`)
    is used throughout instead of hardcoded (x, y) image coordinates, so
    sections never overlap regardless of how much text precedes them.
    
    This function includes comprehensive error handling to prevent crashes
    and provide user-friendly error messages.
    """
    # Validate inputs
    if df is None:
        raise ValueError("No dataset provided for report generation")
    
    if df.empty:
        raise ValueError("Dataset is empty - cannot generate report")
    
    # Ensure ai_text is a string
    if ai_text is None:
        ai_text = ""
    
    pdf = None
    output_path = None
    
    try:
        pdf = ReportPDF()
        pdf.set_auto_page_break(True, margin=15)

        try:
            filename = st.session_state.get("filename", "Dataset")
        except Exception:
            filename = "Dataset"

        score = calculate_quality_score(df)
        missing_total = int(df.isna().sum().sum())
        duplicate_total = int(df.duplicated().sum())
        missing_df = get_missing_summary(df)
        numeric = df.select_dtypes(include=np.number)
        quality_subtitle = f"{df.shape[0]:,} rows - {df.shape[1]} columns - {score}/100 quality score"

        # ── Page 1: cover band + overview + KPI cards + dataset info ──
        pdf.add_page()
        pdf.set_fill_color(*PRIMARY)
        pdf.rect(0, 0, 210, 55, style="F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(15, 15)
        pdf.set_font("Arial", "B", 22)
        pdf.cell(0, 10, clean_pdf_text("DataLens AI Report"))
        pdf.set_xy(15, 30)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, clean_pdf_text("Professional dataset analysis with AI-ready insights"))
        pdf.set_xy(15, 43)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, clean_pdf_text(f"Dataset: {filename}"))
        pdf.set_text_color(0, 0, 0)

        pdf.set_xy(15, 65)
        _section_title(pdf, "Dataset Overview", quality_subtitle)
        _body(pdf, f"The uploaded dataset contains {df.shape[0]:,} rows and {df.shape[1]} columns. "
                    f"The quality score is {score}/100, with {missing_total} missing values and "
                    f"{duplicate_total} duplicate rows.")

        kpi_y = pdf.get_y() + 4
        _add_kpi_card(pdf, "Rows", f"{df.shape[0]:,}", PRIMARY, 15, kpi_y, 40, 24)
        _add_kpi_card(pdf, "Columns", df.shape[1], SUCCESS, 60, kpi_y, 40, 24)
        _add_kpi_card(pdf, "Quality", f"{score}%", WARNING, 105, kpi_y, 40, 24)
        _add_kpi_card(pdf, "Missing", missing_total, DANGER, 150, kpi_y, 40, 24)
        pdf.set_y(kpi_y + 30)

        _section_title(pdf, "Dataset Information")
        info_rows = [
            ("Rows", df.shape[0]),
            ("Columns", df.shape[1]),
            ("Memory usage", f"{round(df.memory_usage(deep=True).sum() / 1024, 2)} KB"),
            ("Duplicate rows", duplicate_total),
            ("Missing cells", missing_total),
        ]
        pdf.set_font("Arial", "", 10)
        for key, value in info_rows:
            pdf.cell(60, 7, clean_pdf_text(str(key)), border=1)
            pdf.cell(100, 7, clean_pdf_text(str(value)), border=1, ln=True)

        # ── Page 2+: missing values → statistics → correlation → charts ──
        pdf.add_page()
        _section_title(pdf, "Missing Values Analysis", "Columns most affected by nulls")
        if not missing_df.empty:
            pdf.set_font("Arial", "", 9)
            for name, row in missing_df.head(8).iterrows():
                pdf.cell(80, 6, clean_pdf_text(str(name)), border=1)
                pdf.cell(30, 6, clean_pdf_text(str(int(row["missing_count"]))), border=1)
                pdf.cell(25, 6, clean_pdf_text(f"{row['share']}%"), border=1, ln=True)
            pdf.ln(3)
            missing_chart = create_missing_chart(df)
            if missing_chart:
                _ensure_space(pdf, 90)
                pdf.image(missing_chart, w=140)
                pdf.ln(4)
        else:
            _body(pdf, "No missing values were found in this dataset.")

        # Statistical summary — delegated to the (previously unused) helper.
        add_statistics(pdf, df)

        # Correlation analysis
        _ensure_space(pdf, 30)
        corr_pairs = get_correlation_insights(df)
        _section_title(pdf, "Correlation Analysis")
        if corr_pairs:
            pdf.set_font("Arial", "", 10)
            for a, b, value in corr_pairs[:8]:
                pdf.cell(0, 6, clean_pdf_text(f"-  {a} and {b} show a strong correlation ({value})"), ln=True)
            pdf.ln(2)
        else:
            _body(pdf, "No strong numeric correlations (|r| >= 0.7) were detected in this dataset.")

        # Histogram, pie chart, heatmap — each guarded by _ensure_space so a
        # chart is never split across a page boundary.
        hist_path = create_histogram(df)
        if hist_path:
            _ensure_space(pdf, 95)
            _section_title(pdf, "Histogram")
            pdf.image(hist_path, w=150)
            pdf.ln(4)

        pie_path = create_pie_chart(df)
        if pie_path:
            _ensure_space(pdf, 100)
            _section_title(pdf, "Pie Chart")
            pdf.image(pie_path, w=120)
            pdf.ln(4)

        heatmap_path = create_heatmap(df)
        if heatmap_path:
            _ensure_space(pdf, 100)
            _section_title(pdf, "Correlation Heatmap")
            pdf.image(heatmap_path, w=150)
            pdf.ln(4)

        # AI insights, recommendations, and the closing quality-score verdict —
        # each of these was previously a dead/unused function; now wired in.
        add_ai_insights(pdf, ai_text)
        add_recommendations(pdf, df)
        add_summary(pdf, df)

        # Create temporary file with proper error handling
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            output_path = tmp.name
        
        # Output PDF with error handling
        try:
            pdf.output(output_path)
        except Exception as e:
            # Clean up the temporary file if output fails
            if output_path and os.path.exists(output_path):
                try:
                    os.unlink(output_path)
                except Exception:
                    pass
            raise RuntimeError(f"Failed to write PDF file: {str(e)}")
        
        # Verify the file was created successfully
        if not os.path.exists(output_path):
            raise RuntimeError("PDF file was not created")
        
        if os.path.getsize(output_path) == 0:
            os.unlink(output_path)
            raise RuntimeError("PDF file is empty")
        
        return output_path
        
    except Exception as e:
        # Clean up temporary file if any error occurs
        if output_path and os.path.exists(output_path):
            try:
                os.unlink(output_path)
            except Exception:
                pass
        raise RuntimeError(f"PDF generation failed: {str(e)}")


def export_to_pdf(ai_text=""):
    """Convenience wrapper used by the Export Report page: reads the current
    dataset out of session_state so callers don't need to pass it explicitly."""
    df = st.session_state.get("df")
    if df is None:
        raise ValueError("No dataset loaded")
    return export_dataset_report(df, ai_text=ai_text)


# ══════════════════════════════════════════════════════════════════════════════
# 4. PREDICTION (AutoML)
# ══════════════════════════════════════════════════════════════════════════════

def detect_prediction_problem(df, target_column):
    """Guess classification vs. regression from the target column: numeric
    with more than 10 distinct values is treated as regression, everything
    else (text, or numeric with few distinct values, e.g. a 0/1 flag) as
    classification."""
    target = df[target_column]
    if pd.api.types.is_numeric_dtype(target):
        return "classification" if target.nunique() <= 10 else "regression"
    return "classification"


def _build_preprocessor(features):
    """ColumnTransformer that imputes + scales numeric columns and
    imputes + one-hot-encodes categorical columns. Shared by every
    candidate model so comparisons are apples-to-apples."""
    numeric_features = features.select_dtypes(include=np.number).columns.tolist()
    categorical_features = features.select_dtypes(exclude=np.number).columns.tolist()

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer(transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features),
    ])


def _candidate_models(problem):
    """The fixed set of models AutoML training races against each other.
    Kept intentionally small (5 each) so training stays fast enough for an
    interactive Streamlit page rather than a background job."""
    if problem == "classification":
        return {
            "Logistic Regression": LogisticRegression(max_iter=1000),
            "Decision Tree": DecisionTreeClassifier(random_state=42),
            "Random Forest": RandomForestClassifier(n_estimators=150, random_state=42),
            "Gradient Boosting": GradientBoostingClassifier(random_state=42),
            "K-Nearest Neighbors": KNeighborsClassifier(),
        }
    return {
        "Linear Regression": LinearRegression(),
        "Decision Tree": DecisionTreeRegressor(random_state=42),
        "Random Forest": RandomForestRegressor(n_estimators=150, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(random_state=42),
        "K-Nearest Neighbors": KNeighborsRegressor(),
    }


def train_prediction_model(df, target_column):
    """AutoML entry point: detects the problem type, trains every candidate
    model behind a shared preprocessing pipeline, cross-validates each, and
    keeps the best one by held-out score (accuracy for classification, R²
    for regression).

    Returns a dict with everything the Prediction page needs:
        model               the winning fitted sklearn Pipeline
        problem             "classification" or "regression"
        best_model_name     human-readable name of the winner
        metrics             headline metrics for the winning model
                            (classification: accuracy, f1, confusion_matrix, labels
                             regression: mae, rmse, r2, actual, predicted — the
                             last two are what the UI needs for an
                             Actual-vs-Predicted / residual plot)
        comparison          list of {model, <metrics>} for every candidate,
                            for a model-comparison table
        feature_importance  top-10 (feature, importance) pairs, empty list
                            if the winning model doesn't expose importances
        feature_columns     the feature column names used for training,
                            needed to build the "make a prediction" form
        target_column       echoed back for convenience
    """
    if target_column not in df.columns:
        raise ValueError("Target column not found")
    if df[target_column].isna().all():
        raise ValueError("Target column has no usable values")

    # Rows with a missing target can't be used for supervised training.
    working = df.dropna(subset=[target_column]).copy()
    X = working.drop(columns=[target_column])
    y = working[target_column]
    problem = detect_prediction_problem(working, target_column)

    # Stratify keeps class proportions balanced across train/test for
    # classification, but only works if every class has >= 2 members —
    # fall back to a plain split if that's not the case.
    try:
        stratify = y if (problem == "classification" and y.nunique() > 1) else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=stratify
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    preprocessor = _build_preprocessor(X_train)
    candidates = _candidate_models(problem)
    scoring = "accuracy" if problem == "classification" else "r2"

    comparison = []
    best_name, best_pipeline, best_preds, best_score = None, None, None, -np.inf

    for name, estimator in candidates.items():
        pipeline = Pipeline(steps=[("preprocess", preprocessor), ("model", estimator)])
        try:
            pipeline.fit(X_train, y_train)
            preds = pipeline.predict(X_test)

            try:
                cv_score = float(np.mean(cross_val_score(pipeline, X_train, y_train, cv=3, scoring=scoring)))
            except Exception:
                cv_score = float("nan")  # e.g. a class too rare for 3-fold CV

            if problem == "classification":
                row = {
                    "model": name,
                    "accuracy": round(float(accuracy_score(y_test, preds)), 4),
                    "f1_score": round(float(f1_score(y_test, preds, average="weighted")), 4),
                    "cv_score": round(cv_score, 4) if not np.isnan(cv_score) else None,
                }
                primary = row["accuracy"]
            else:
                row = {
                    "model": name,
                    "mae": round(float(mean_absolute_error(y_test, preds)), 4),
                    "rmse": round(float(np.sqrt(mean_squared_error(y_test, preds))), 4),
                    "r2_score": round(float(r2_score(y_test, preds)), 4),
                    "cv_score": round(cv_score, 4) if not np.isnan(cv_score) else None,
                }
                primary = row["r2_score"]

            comparison.append(row)
            if primary > best_score:
                best_score, best_name, best_pipeline, best_preds = primary, name, pipeline, preds
        except Exception as exc:
            # A candidate can legitimately fail (e.g. too few samples) —
            # record it in the comparison table instead of crashing training.
            comparison.append({"model": name, "error": str(exc)})

    if best_pipeline is None:
        raise ValueError("No candidate model could be trained successfully on this data.")

    if problem == "classification":
        metrics = {
            "problem": problem,
            "best_model": best_name,
            "accuracy": round(float(accuracy_score(y_test, best_preds)), 4),
            "f1": round(float(f1_score(y_test, best_preds, average="weighted")), 4),
            "confusion_matrix": confusion_matrix(y_test, best_preds).tolist(),
            "labels": sorted(y_test.unique().tolist(), key=str),
        }
    else:
        metrics = {
            "problem": problem,
            "best_model": best_name,
            "mae": round(float(mean_absolute_error(y_test, best_preds)), 4),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, best_preds))), 4),
            "r2": round(float(r2_score(y_test, best_preds)), 4),
            "actual": [float(v) for v in y_test.tolist()],
            "predicted": [float(v) for v in best_preds],
        }

    # Feature importance only exists on tree-based estimators.
    feature_importance = []
    fitted_model = best_pipeline.named_steps["model"]
    if hasattr(fitted_model, "feature_importances_"):
        try:
            feature_names = best_pipeline.named_steps["preprocess"].get_feature_names_out()
        except Exception:
            feature_names = X_train.columns.tolist()
        importances = fitted_model.feature_importances_
        feature_importance = [
            {"feature": str(f), "importance": round(float(i), 4)}
            for f, i in sorted(zip(feature_names, importances), key=lambda item: item[1], reverse=True)[:10]
        ]

    return {
        "model": best_pipeline,
        "problem": problem,
        "best_model_name": best_name,
        "metrics": metrics,
        "comparison": comparison,
        "feature_importance": feature_importance,
        "feature_columns": X_train.columns.tolist(),
        "target_column": target_column,
    }


def predict_with_model(model, sample_row):
    """Run one prediction for a single row given as a dict of {column: value}."""
    return model.predict(pd.DataFrame([sample_row]))[0]


def save_prediction_model(model, path):
    """Serialize a fitted pipeline to disk with joblib (used for the
    "Download model (.pkl)" button)."""
    joblib.dump(model, path)


def load_prediction_model(path):
    """Load a previously saved joblib pipeline."""
    return joblib.load(path)


def forecast_regression_series(series, periods=5):
    """Very simple linear-trend forecast: fits a straight line to the
    series' index vs. value, then extrapolates `periods` steps forward.
    Intended for quick "where is this heading" forecasts on a numeric
    column that behaves roughly like a time series (e.g. already sorted
    by date), not a substitute for real time-series modeling."""
    values = np.array(series.dropna()).astype(float)
    if len(values) < 2:
        return [float(values[-1])] * periods if len(values) else [0.0] * periods

    x = np.arange(len(values)).reshape(-1, 1)
    model = LinearRegression().fit(x, values)
    future_x = np.arange(len(values), len(values) + periods).reshape(-1, 1)
    preds = model.predict(future_x)
    return [round(float(v), 2) for v in preds]