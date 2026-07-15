import hashlib
import io
import os
import re
import tempfile
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from fpdf import FPDF


# ==========================================================
# DATA LOADING
# ==========================================================

def compute_file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


@st.cache_data
def load_data(file_bytes, filename="dataset.csv"):
    """Load a supported dataset file into a pandas DataFrame."""
    filename = (filename or "dataset.csv").lower()
    buffer = io.BytesIO(file_bytes)

    try:
        if filename.endswith(".csv"):
            return _read_csv(buffer, sep=",")
        if filename.endswith(".tsv"):
            return _read_csv(buffer, sep="\t")
        if filename.endswith(".xlsx"):
            return pd.read_excel(buffer)
        if filename.endswith(".json"):
            return pd.read_json(buffer, orient="records", convert_dates=True)
        if filename.endswith(".parquet"):
            try:
                return pd.read_parquet(buffer)
            except ImportError as exc:
                raise ImportError("Parquet support requires pyarrow or fastparquet.") from exc
        return _read_csv(buffer, sep=",")
    except Exception:
        if filename.endswith(".csv") or filename.endswith(".tsv"):
            for encoding in ["utf-8", "cp1252", "latin1"]:
                try:
                    buffer.seek(0)
                    return pd.read_csv(buffer, sep="," if filename.endswith(".csv") else "\t", encoding=encoding)
                except UnicodeDecodeError:
                    continue
        raise


def _read_csv(buffer, sep=","):
    for encoding in ["utf-8", "cp1252", "latin1"]:
        try:
            buffer.seek(0)
            return pd.read_csv(buffer, sep=sep, encoding=encoding)
        except UnicodeDecodeError:
            continue
    buffer.seek(0)
    return pd.read_csv(buffer, sep=sep, encoding="utf-8", engine="python")


@st.cache_data
def clean_data(df):
    """Apply light-touch cleaning while preserving the dataframe shape."""
    cleaned = df.copy()
    cleaned.columns = [str(col).strip() for col in cleaned.columns]

    for column in cleaned.columns:
        series = cleaned[column]
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            cleaned[column] = series.astype(str).str.strip()
            cleaned[column] = cleaned[column].replace({"nan": np.nan, "None": np.nan, "": np.nan})

            try:
                numeric_series = pd.to_numeric(cleaned[column], errors="coerce")
                if numeric_series.notna().sum() / max(len(cleaned), 1) > 0.8:
                    cleaned[column] = numeric_series
            except Exception:
                pass

    if "gross" in {col.lower() for col in cleaned.columns}:
        gross_col = next(col for col in cleaned.columns if col.lower() == "gross")
        cleaned[gross_col] = cleaned[gross_col].astype(str).str.replace(",", "", regex=False)
        cleaned[gross_col] = pd.to_numeric(cleaned[gross_col], errors="coerce")

    cleaned = cleaned.drop_duplicates().reset_index(drop=True)
    return cleaned


@st.cache_data
def get_summary(df, filename):
    """Return a rich text summary for AI prompting and reporting."""
    numeric = df.select_dtypes(include=np.number)
    categorical = df.select_dtypes(exclude=np.number)
    missing_summary = df.isna().sum().sort_values(ascending=False)
    missing_top = missing_summary[missing_summary > 0].head(5).to_dict()

    summary_parts = [
        f"Dataset: {filename or 'Uploaded dataset'}",
        f"Rows: {df.shape[0]} | Columns: {df.shape[1]}",
        f"Numeric columns: {', '.join(numeric.columns.tolist()) if not numeric.empty else 'None'}",
        f"Categorical columns: {', '.join(categorical.columns.tolist()) if not categorical.empty else 'None'}",
        f"Missing values: {int(df.isna().sum().sum())} total cells",
    ]

    if missing_top:
        summary_parts.append("Top missing value columns: " + ", ".join(f"{k} ({v})" for k, v in missing_top.items()))

    if not numeric.empty:
        summary_parts.append("Numeric highlights:")
        for col in numeric.columns[:5]:
            series = numeric[col]
            summary_parts.append(
                f"- {col}: mean={series.mean():.2f}, median={series.median():.2f}, std={series.std():.2f}, missing={series.isna().sum()}"
            )

    if not categorical.empty:
        top_col = categorical.columns[0]
        counts = categorical[top_col].value_counts(dropna=False).head(5)
        summary_parts.append(f"Top values in {top_col}: {', '.join(f'{k} ({v})' for k, v in counts.items())}")

    return "\n".join(summary_parts)


# ==========================================================
# BASIC ANALYSIS
# ==========================================================

def get_numeric_stats(df):
    """Return a richer descriptive statistics table for numeric columns."""
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        return pd.DataFrame()

    stats = []
    for col in numeric.columns:
        series = numeric[col].dropna()
        if series.empty:
            continue
        stats.append(
            {
                "Column": col,
                "Mean": round(float(series.mean()), 4),
                "Median": round(float(series.median()), 4),
                "Mode": round(float(series.mode().iloc[0]), 4) if not series.mode().empty else np.nan,
                "Variance": round(float(series.var()), 4),
                "Std Dev": round(float(series.std()), 4),
                "Skewness": round(float(series.skew()), 4),
                "Kurtosis": round(float(series.kurt()), 4),
                "IQR": round(float(series.quantile(0.75) - series.quantile(0.25)), 4),
                "Range": round(float(series.max() - series.min()), 4),
                "Min": round(float(series.min()), 4),
                "Max": round(float(series.max()), 4),
            }
        )
    return pd.DataFrame(stats).set_index("Column")


def get_missing_summary(df):
    missing = df.isna().sum().rename("Missing").to_frame()
    missing["Percentage"] = (missing["Missing"] / len(df) * 100).round(2) if len(df) else 0
    return missing.sort_values(["Missing", "Percentage"], ascending=False)


def get_category_counts(df, col):
    return df[col].value_counts(dropna=False)


def calculate_quality_score(df):
    """Return a simple quality score from missing and duplicate rates."""
    score = 100.0
    total_cells = df.shape[0] * df.shape[1]
    missing_rate = (df.isna().sum().sum() / total_cells) * 100 if total_cells else 0
    duplicate_rate = (df.duplicated().sum() / len(df)) * 100 if len(df) else 0
    score -= missing_rate * 0.5
    score -= duplicate_rate * 0.5
    return max(0, round(score))


def detect_outliers(df, column, method="iqr"):
    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if series.empty:
        return pd.Series(dtype=float)
    if method == "zscore":
        std = series.std()
        mean = series.mean()
        if std == 0:
            return pd.Series(False, index=series.index)
        z = (series - mean) / std
        return (z.abs() > 3)
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return (series < lower) | (series > upper)


def get_correlation_summary(df):
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty or numeric.shape[1] < 2:
        return pd.DataFrame()
    corr = numeric.corr().round(3)
    corr = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    return corr.stack().dropna().sort_values(ascending=False)


# ==========================================================
# PDF CLASS
# ==========================================================

class ReportPDF(FPDF):
    def header(self):
        self.set_fill_color(79, 70, 229)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 18)
        self.cell(0, 14, "DataLens Professional Report", ln=True, align="C", fill=True)
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()} • Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")


def section_title(pdf, title):
    pdf.set_fill_color(30, 64, 175)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 9, title, ln=True, fill=True)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)


def body(pdf, text, font_size=11):
    pdf.set_font("Arial", "", font_size)
    pdf.multi_cell(0, 6.5, text)
    pdf.ln(2)


# ==========================================================
# CHART GENERATION
# ==========================================================

def _save_chart_path(name):
    return os.path.join(tempfile.gettempdir(), f"{name}.png")


def create_summary_charts(df):
    paths = {}
    numeric = df.select_dtypes(include=np.number)
    categorical = df.select_dtypes(exclude=np.number)

    if not numeric.empty:
        col = numeric.columns[0]
        fig, ax = plt.subplots(figsize=(4.5, 2.8))
        numeric[col].dropna().head(20).plot(kind="bar", color="#4f46e5", ax=ax)
        ax.set_title(f"{col} distribution")
        ax.set_xlabel(col)
        ax.set_ylabel("Value")
        fig.tight_layout()
        fig.savefig(_save_chart_path("pdf_histogram"), dpi=180)
        plt.close(fig)
        paths["histogram"] = _save_chart_path("pdf_histogram")

    if not categorical.empty:
        col = categorical.columns[0]
        counts = categorical[col].value_counts().head(6)
        fig, ax = plt.subplots(figsize=(4.5, 2.8))
        counts.plot(kind="pie", autopct="%1.1f%%", startangle=90, ax=ax, colors=sns.color_palette("Set2", n_colors=len(counts)))
        ax.set_title(f"{col} distribution")
        ax.set_ylabel("")
        fig.tight_layout()
        fig.savefig(_save_chart_path("pdf_pie"), dpi=180)
        plt.close(fig)
        paths["pie"] = _save_chart_path("pdf_pie")

    if not numeric.empty and numeric.shape[1] > 1:
        fig, ax = plt.subplots(figsize=(4.4, 3.4))
        corr = numeric.corr()
        sns.heatmap(corr, annot=False, cmap="Purples", ax=ax)
        ax.set_title("Correlation heatmap")
        fig.tight_layout()
        fig.savefig(_save_chart_path("pdf_heatmap"), dpi=180)
        plt.close(fig)
        paths["heatmap"] = _save_chart_path("pdf_heatmap")

    return paths


# ==========================================================
# PDF REPORT
# ==========================================================

def export_dataset_report(df, ai_text="", filename=None):
    """Generate a two-page, professional PDF report for the current dataset."""
    pdf = ReportPDF()
    pdf.set_auto_page_break(True, margin=16)
    display_name = filename or st.session_state.get("filename", "Dataset")
    quality_score = calculate_quality_score(df)
    missing_summary = get_missing_summary(df)
    numeric = df.select_dtypes(include=np.number)
    top_correlation = get_correlation_summary(df)
    chart_paths = create_summary_charts(df)

    # ------------------------------------------------------------------
    # Cover page
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 18, "DataLens Professional Report", ln=True, align="C", fill=True)
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 7, f"Prepared for: {display_name}\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    pdf.ln(6)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Dataset Snapshot", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"Rows: {df.shape[0]} | Columns: {df.shape[1]} | Quality Score: {quality_score}/100", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Key Highlights", ln=True)
    pdf.set_font("Arial", "", 11)
    body(pdf, f"- Missing values: {int(df.isna().sum().sum())}\n- Duplicate rows: {int(df.duplicated().sum())}\n- Numeric columns: {len(numeric.columns)}\n- AI summary available: {'Yes' if ai_text else 'No'}")
    pdf.ln(6)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Recommendations", ln=True)
    pdf.set_font("Arial", "", 10)
    recommendations = [
        "Review missing values before modeling.",
        "Investigate extreme outliers on numeric variables.",
        "Use the AI assistant for narrative insights.",
    ]
    for item in recommendations:
        pdf.cell(0, 6, f"• {item}", ln=True)

    # ------------------------------------------------------------------
    # Analytical page
    # ------------------------------------------------------------------
    pdf.add_page()
    section_title(pdf, "Dataset Overview")
    body(pdf, f"Dataset: {display_name}\nRows: {df.shape[0]}\nColumns: {df.shape[1]}\nMemory usage: {round(df.memory_usage(deep=True).sum() / 1024, 2)} KB")

    section_title(pdf, "Missing Values Analysis")
    if missing_summary.empty or (missing_summary["Missing"] == 0).all():
        body(pdf, "No missing values detected.")
    else:
        missing_df = missing_summary.head(8).reset_index().rename(columns={"index": "Column"})
        for _, row in missing_df.iterrows():
            pdf.cell(0, 6, f"• {row['Column']}: {int(row['Missing'])} missing ({row['Percentage']}%)", ln=True)

    section_title(pdf, "Statistical Summary")
    if not numeric.empty:
        stats = numeric.describe().round(2)
        for col in stats.columns[:3]:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 7, f"{col}", ln=True)
            pdf.set_font("Arial", "", 8)
            for idx in stats.index:
                pdf.cell(35, 5, str(idx), border=1)
                pdf.cell(35, 5, str(stats.loc[idx, col]), border=1, ln=True)
            pdf.ln(2)

    section_title(pdf, "Correlation Insights")
    if not top_correlation.empty:
        top_pairs = top_correlation.head(6)
        for idx, value in top_pairs.items():
            left, right = idx
            pdf.cell(0, 6, f"• {left} ↔ {right}: correlation {value:.3f}", ln=True)
    else:
        body(pdf, "Not enough numeric columns for correlation analysis.")

    if "histogram" in chart_paths:
        pdf.add_page()
        section_title(pdf, "Charts")
        pdf.image(chart_paths["histogram"], x=12, y=40, w=85)
        if "pie" in chart_paths:
            pdf.image(chart_paths["pie"], x=105, y=40, w=85)
        if "heatmap" in chart_paths:
            pdf.image(chart_paths["heatmap"], x=55, y=125, w=95)

    section_title(pdf, "AI Insights")
    clean_ai = re.sub(r"[^\x00-\x7F]+", " ", ai_text if ai_text else "No AI insights were provided for this dataset.")
    body(pdf, clean_ai, font_size=10)

    output_path = os.path.join(tempfile.gettempdir(), "DataLens_Report.pdf")
    pdf.output(output_path)
    return output_path


    if missing > 0:

        recommendations.append(
            "- Fill missing values before model training."
        )

    if duplicate > 0:

        recommendations.append(
            "- Remove duplicate records."
        )

    if score >= 90:

        recommendations.append(
            "- Excellent dataset quality."
        )

    elif score >= 70:

        recommendations.append(
            "- Dataset is good but needs minor cleaning."
        )

    else:

        recommendations.append(
            "- Dataset requires preprocessing before analysis."
        )

    body(
        pdf,
        "\n".join(recommendations)
    )

    # ------------------------------------------------------

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ) as tmp:

        filename = tmp.name

    pdf.output(filename)

    return filename

# ==========================================================
# COLORS
# ==========================================================

PRIMARY = (67, 97, 238)
SECONDARY = (76, 201, 240)
SUCCESS = (46, 204, 113)
WARNING = (243, 156, 18)
DANGER = (231, 76, 60)
LIGHT = (245, 247, 250)
DARK = (44, 62, 80)


# ==========================================================
# DRAW KPI CARD
# ==========================================================

def draw_card(pdf, title, value, color):

    x = pdf.get_x()
    y = pdf.get_y()

    pdf.set_fill_color(*color)

    pdf.rect(
        x,
        y,
        60,
        28,
        style="F"
    )

    pdf.set_xy(x+3, y+4)

    pdf.set_font("Arial","B",10)
    pdf.set_text_color(255,255,255)

    pdf.cell(
        54,
        6,
        title
    )

    pdf.set_xy(x+3,y+13)

    pdf.set_font("Arial","B",18)

    pdf.cell(
        54,
        8,
        str(value)
    )

    pdf.set_text_color(0)

    pdf.set_xy(x+65,y)


def cover_title(pdf):

    pdf.set_fill_color(*PRIMARY)

    pdf.rect(
        0,
        0,
        210,
        40,
        style="F"
    )

    pdf.set_text_color(255)

    pdf.set_xy(15,12)

    pdf.set_font(
        "Arial",
        "B",
        24
    )

    pdf.cell(
        0,
        10,
        "DataLens AI Report"
    )

    pdf.set_xy(15,25)

    pdf.set_font(
        "Arial",
        "",
        11
    )

    pdf.cell(
        0,
        8,
        "Professional Dataset Analysis"
    )

    pdf.set_text_color(0)

    pdf.ln(25)



def add_kpis(pdf, df):

    score = calculate_quality_score(df)

    rows = len(df)

    cols = len(df.columns)

    missing = int(df.isna().sum().sum())

    pdf.set_font(
        "Arial",
        "B",
        14
    )

    pdf.cell(
        0,
        10,
        "Dataset KPIs",
        ln=True
    )

    draw_card(
        pdf,
        "Rows",
        rows,
        PRIMARY
    )

    draw_card(
        pdf,
        "Columns",
        cols,
        SUCCESS
    )

    draw_card(
        pdf,
        "Quality",
        f"{score}%",
        WARNING
    )

    pdf.ln(34)

    draw_card(
        pdf,
        "Missing",
        missing,
        DANGER
    )

    pdf.ln(34)




def dataset_information(pdf, df):

    pdf.set_font(
        "Arial",
        "B",
        14
    )

    pdf.cell(
        0,
        10,
        "Dataset Information",
        ln=True
    )

    pdf.set_font(
        "Arial",
        "",
        10
    )

    memory = round(
        df.memory_usage(deep=True).sum()/1024,
        2
    )

    info = [

        ("Rows", df.shape[0]),

        ("Columns", df.shape[1]),

        ("Memory", f"{memory} KB"),

        ("Duplicates", int(df.duplicated().sum())),

        ("Missing", int(df.isna().sum().sum()))

    ]

    for key,value in info:

        pdf.cell(
            60,
            8,
            str(key),
            border=1
        )

        pdf.cell(
            100,
            8,
            str(value),
            border=1,
            ln=True
        )

    pdf.ln(6)




# ==========================================================
# CHARTS FOR PDF
# ==========================================================

def create_histogram(df):

    numeric = df.select_dtypes(include=np.number)

    if numeric.empty:
        return None

    column = numeric.columns[0]

    plt.figure(figsize=(6,4))

    plt.hist(
        numeric[column].dropna(),
        bins=20,
        color="#4361EE",
        edgecolor="black"
    )

    plt.title(f"Histogram - {column}")

    plt.xlabel(column)

    plt.ylabel("Frequency")

    plt.tight_layout()

    path = os.path.join(
        tempfile.gettempdir(),
        "histogram.png"
    )

    plt.savefig(path,dpi=200)

    plt.close()

    return path


# ==========================================================
# MISSING VALUES BAR CHART
# ==========================================================

def create_missing_chart(df):

    missing = df.isna().sum()

    missing = missing[missing>0]

    if missing.empty:
        return None

    plt.figure(figsize=(6,4))

    missing.plot(
        kind="bar",
        color="#EF4444"
    )

    plt.title("Missing Values")

    plt.ylabel("Count")

    plt.tight_layout()

    path = os.path.join(
        tempfile.gettempdir(),
        "missing.png"
    )

    plt.savefig(path,dpi=200)

    plt.close()

    return path


# ==========================================================
# DATA TYPE PIE CHART
# ==========================================================

def create_dtype_chart(df):

    counts = df.dtypes.astype(str).value_counts()

    plt.figure(figsize=(5,5))

    plt.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.1f%%",
        startangle=90
    )

    plt.title("Column Data Types")

    path = os.path.join(
        tempfile.gettempdir(),
        "dtype.png"
    )

    plt.savefig(path,dpi=200)

    plt.close()

    return path


# ==========================================================
# CORRELATION HEATMAP
# ==========================================================

def create_heatmap(df):

    numeric = df.select_dtypes(include=np.number)

    if numeric.shape[1] < 2:
        return None

    corr = numeric.corr()

    plt.figure(figsize=(6,5))

    plt.imshow(
        corr,
        cmap="coolwarm",
        interpolation="nearest"
    )

    plt.colorbar()

    plt.xticks(
        range(len(corr.columns)),
        corr.columns,
        rotation=90,
        fontsize=8
    )

    plt.yticks(
        range(len(corr.columns)),
        corr.columns,
        fontsize=8
    )

    plt.title("Correlation Heatmap")

    plt.tight_layout()

    path = os.path.join(
        tempfile.gettempdir(),
        "heatmap.png"
    )

    plt.savefig(path,dpi=200)

    plt.close()

    return path



# ======================================================
# CHARTS
# ======================================================

hist = create_histogram(df)

if hist:

    pdf.set_font("Arial","B",13)

    pdf.cell(
        0,
        10,
        "Histogram",
        ln=True
    )

    pdf.image(
        hist,
        w=160
    )

    pdf.ln(6)


missing_chart = create_missing_chart(df)

if missing_chart:

    pdf.set_font("Arial","B",13)

    pdf.cell(
        0,
        10,
        "Missing Values",
        ln=True
    )

    pdf.image(
        missing_chart,
        w=160
    )

    pdf.ln(6)


dtype = create_dtype_chart(df)

if dtype:

    pdf.set_font("Arial","B",13)

    pdf.cell(
        0,
        10,
        "Data Types",
        ln=True
    )

    pdf.image(
        dtype,
        w=120
    )

    pdf.ln(6)


heat = create_heatmap(df)

if heat:

    pdf.set_font("Arial","B",13)

    pdf.cell(
        0,
        10,
        "Correlation Heatmap",
        ln=True
    )

    pdf.image(
        heat,
        w=170
    )




# ==========================================================
# ADVANCED STATISTICS
# ==========================================================

def add_statistics(pdf, df):

    numeric = df.select_dtypes(include=np.number)

    if numeric.empty:
        return

    pdf.set_font("Arial", "B", 15)
    pdf.cell(0, 10, "Statistical Summary", ln=True)

    stats = numeric.describe().round(2)

    for column in stats.columns:

        pdf.set_fill_color(67, 97, 238)
        pdf.set_text_color(255)

        pdf.cell(
            0,
            8,
            column,
            ln=True,
            fill=True
        )

        pdf.set_text_color(0)
        pdf.set_font("Arial", "", 9)

        for idx in stats.index:

            pdf.cell(
                40,
                7,
                str(idx),
                border=1
            )

            pdf.cell(
                40,
                7,
                str(stats.loc[idx, column]),
                border=1,
                ln=True
            )

        pdf.ln(4)


# ==========================================================
# AI INSIGHTS
# ==========================================================

def add_ai_insights(pdf, ai_text):

    pdf.set_font("Arial", "B", 15)

    pdf.cell(
        0,
        10,
        "AI Insights",
        ln=True
    )

    pdf.set_fill_color(245,247,250)

    pdf.multi_cell(
        0,
        8,
        ai_text if ai_text else "No AI insights available.",
        border=1,
        fill=True
    )

    pdf.ln(6)


# ==========================================================
# SMART RECOMMENDATIONS
# ==========================================================

def add_recommendations(pdf, df):

    pdf.set_font("Arial","B",15)

    pdf.cell(
        0,
        10,
        "Recommendations",
        ln=True
    )

    recommendations=[]

    if df.isna().sum().sum()>0:

        recommendations.append(
            "• Fill missing values before training ML models."
        )

    if df.duplicated().sum()>0:

        recommendations.append(
            "• Remove duplicate records."
        )

    if len(df)<500:

        recommendations.append(
            "• More data may improve prediction accuracy."
        )

    if df.select_dtypes(include=np.number).shape[1]>1:

        recommendations.append(
            "• Perform feature selection using correlation."
        )

    recommendations.append(
        "• Normalize numerical features."
    )

    recommendations.append(
        "• Encode categorical variables."
    )

    recommendations.append(
        "• Split data into Train/Test before prediction."
    )

    pdf.set_font("Arial","",11)

    for rec in recommendations:

        pdf.multi_cell(
            0,
            8,
            rec
        )

    pdf.ln(5)


# ==========================================================
# FOOTER SUMMARY
# ==========================================================

def add_summary(pdf, df):

    score = calculate_quality_score(df)

    pdf.set_fill_color(67,97,238)

    pdf.set_text_color(255)

    pdf.set_font(
        "Arial",
        "B",
        14
    )

    pdf.cell(
        0,
        12,
        f"Overall Dataset Quality : {score}/100",
        ln=True,
        fill=True
    )

    pdf.set_text_color(0)

    pdf.ln(5)

    pdf.set_font(
        "Arial",
        "",
        11
    )

    if score>=90:

        text="Excellent dataset ready for Machine Learning."

    elif score>=70:

        text="Good dataset with minor preprocessing required."

    else:

        text="Dataset requires cleaning before analysis."

    pdf.multi_cell(
        0,
        8,
        text
    )




