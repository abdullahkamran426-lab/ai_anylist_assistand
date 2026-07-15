import hashlib
import io
import os
import re
import tempfile

import streamlit as st
import pandas as pd
import numpy as np

from fpdf import FPDF

import matplotlib.pyplot as plt


# ==========================================================
# DATA LOADING
# ==========================================================

def compute_file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


@st.cache_data
def load_data(file_bytes):

    try:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")

    except UnicodeDecodeError:

        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="cp1252")

        except UnicodeDecodeError:

            df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")

    return df


@st.cache_data
def clean_data(df):

    df = df.copy()

    if "Gross" in df.columns:

        df["Gross"] = (
            df["Gross"]
            .replace(",", "", regex=True)
        )

        df["Gross"] = pd.to_numeric(
            df["Gross"],
            errors="coerce",
        )

    return df


@st.cache_data
def get_summary(df, filename):

    return f"""
File : {filename}

Rows : {df.shape[0]}

Columns : {df.shape[1]}

Column Names

{list(df.columns)}

Statistics

{df.describe(include='all').fillna('').to_string()}
"""


# ==========================================================
# BASIC ANALYSIS
# ==========================================================

def get_numeric_stats(df):

    numeric = df.select_dtypes(include=np.number)

    if len(numeric.columns):

        return numeric.describe()

    return None


def get_category_counts(df, col):

    return df[col].value_counts()


def calculate_quality_score(df):

    score = 100

    missing = (
        df.isna().sum().sum()
        /
        (df.shape[0] * df.shape[1])
    ) * 100

    duplicate = (
        df.duplicated().sum()
        /
        len(df)
    ) * 100 if len(df) else 0

    score -= missing * 0.5
    score -= duplicate * 0.5

    return max(0, round(score))


# ==========================================================
# PDF CLASS
# ==========================================================

class ReportPDF(FPDF):

    def header(self):

        self.set_fill_color(55, 80, 180)

        self.set_text_color(255,255,255)

        self.set_font("Arial","B",18)

        self.cell(
            0,
            14,
            "DataLens Professional Report",
            ln=True,
            align="C",
            fill=True
        )

        self.ln(6)

        self.set_text_color(0,0,0)


    def footer(self):

        self.set_y(-15)

        self.set_font("Arial","I",9)

        self.set_text_color(120)

        self.cell(
            0,
            10,
            f"Page {self.page_no()}",
            align="C"
        )


def section_title(pdf,title):

    pdf.set_fill_color(70,110,255)

    pdf.set_text_color(255)

    pdf.set_font("Arial","B",13)

    pdf.cell(
        0,
        9,
        title,
        ln=True,
        fill=True
    )

    pdf.ln(2)

    pdf.set_text_color(0)


def body(pdf,text):

    pdf.set_font("Arial","",11)

    pdf.multi_cell(
        0,
        7,
        text
    )

    pdf.ln(2)


# ==========================================================
# CHART GENERATION
# ==========================================================

def create_numeric_chart(df):
    """
    Create a bar chart using the first numeric column.
    Returns image path.
    """

    numeric = df.select_dtypes(include=np.number)

    if numeric.empty:
        return None

    col = numeric.columns[0]

    plt.figure(figsize=(7, 4))

    numeric[col].head(20).plot(
        kind="bar",
        color="#4F46E5"
    )

    plt.title(col)
    plt.tight_layout()

    path = os.path.join(
        tempfile.gettempdir(),
        "chart.png"
    )

    plt.savefig(path, dpi=200)

    plt.close()

    return path


# ==========================================================
# PDF REPORT
# ==========================================================

def export_dataset_report(df, ai_text=""):

    pdf = ReportPDF()

    pdf.set_auto_page_break(True, margin=15)

    # ------------------------------------------------------
    # PAGE 1
    # ------------------------------------------------------

    pdf.add_page()

    section_title(pdf, "Dataset Overview")

    body(
        pdf,
        f"""
Dataset Name : {st.session_state.get('filename','Dataset')}

Rows : {df.shape[0]}

Columns : {df.shape[1]}

Memory Usage :
{round(df.memory_usage(deep=True).sum()/1024,2)} KB
"""
    )

    # ------------------------------------------------------

    section_title(pdf, "Data Quality")

    score = calculate_quality_score(df)

    missing = int(df.isna().sum().sum())

    duplicate = int(df.duplicated().sum())

    body(
        pdf,
        f"""
Quality Score : {score}/100

Missing Values : {missing}

Duplicate Rows : {duplicate}
"""
    )

    # ------------------------------------------------------

    section_title(pdf, "Column Information")

    pdf.set_font("Arial", "", 10)

    for col in df.columns:

        pdf.cell(
            95,
            7,
            col,
            border=1
        )

        pdf.cell(
            40,
            7,
            str(df[col].dtype),
            border=1
        )

        pdf.cell(
            40,
            7,
            str(df[col].isna().sum()),
            border=1,
            ln=True
        )

    pdf.ln(5)

    # ------------------------------------------------------

    chart = create_numeric_chart(df)

    if chart:

        section_title(pdf, "Dataset Chart")

        pdf.image(chart, w=170)

    # ------------------------------------------------------
    # PAGE 2
    # ------------------------------------------------------

    pdf.add_page()

    section_title(pdf, "Statistical Summary")

    numeric = df.select_dtypes(include=np.number)

    if not numeric.empty:

        stats = numeric.describe().round(2)

        pdf.set_font("Arial", "", 8)

        for column in stats.columns:

            pdf.set_font("Arial", "B", 10)

            pdf.cell(
                0,
                8,
                column,
                ln=True
            )

            pdf.set_font("Arial", "", 8)

            for idx in stats.index:

                pdf.cell(
                    45,
                    6,
                    str(idx),
                    border=1
                )

                pdf.cell(
                    45,
                    6,
                    str(stats.loc[idx, column]),
                    border=1,
                    ln=True
                )

            pdf.ln(4)

    # ------------------------------------------------------

    section_title(pdf, "AI Insights")

    clean_ai = re.sub(
        r"[^\x00-\x7F]+",
        " ",
        ai_text if ai_text else "No AI Insights Available."
    )

    body(pdf, clean_ai)

    # ------------------------------------------------------

    section_title(pdf, "Recommendations")

    recommendations = []

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




