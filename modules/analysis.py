import hashlib
import io

import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import re


def compute_file_hash(file_bytes):
    """Return a stable hash for an uploaded file payload."""
    return hashlib.md5(file_bytes).hexdigest()


@st.cache_data
def load_data(file_bytes):
    """Reads CSV bytes with fallback encodings. Cached by content hash."""
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="cp1252")
        except:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")
    return df


@st.cache_data
def clean_data(df):
    """Cleans specific columns like Gross."""
    if 'Gross' in df.columns:
        df['Gross'] = df['Gross'].replace(',', '', regex=True)
        df['Gross'] = pd.to_numeric(df['Gross'], errors='coerce')
    return df


@st.cache_data
def get_summary(df, filename):
    """Generates a text summary of the dataset for the AI."""
    return f"""
File: {filename}
Rows: {df.shape[0]}
Columns: {df.shape[1]}
Column Names: {list(df.columns)}
Data Types: {df.dtypes.to_string()}
First Rows: {df.head(5).to_string()}
Statistics: {df.describe().head(10).to_string()}
"""

def get_numeric_stats(df):
    """Returns statistics for numeric columns."""
    numeric = df.select_dtypes(include=np.number)
    if len(numeric.columns):
        return numeric.describe()
    return None

def get_category_counts(df, col):
    """Returns value counts for a categorical column."""
    return df[col].value_counts()

def export_to_pdf(text_content, filename="AI_Analysis_Report.pdf"):
    """Exports AI insights to a downloadable PDF file."""
    # FPDF struggles with emojis, so we remove them
    clean_text = re.sub(r'[^\x00-\x7F]+', ' ', text_content)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="AI Data Analysis Report", ln=True, align='C')
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=clean_text)
    pdf.output(filename)
    return filename