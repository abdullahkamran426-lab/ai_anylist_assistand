"""
Data Cleaning
=============
The baseline auto-clean pipeline applied automatically right after upload
(see data_loading.py). This is intentionally conservative: it only fixes
things that are unambiguous formatting noise (stray whitespace, "nan"-as-
text, obvious currency columns, exact duplicate rows) — it never guesses
at semantic fixes, since those belong in the interactive Clean Data page
where the user explicitly chooses a strategy.

Educational Note for Students:
-----------------------------
Clean data is crucial for machine learning and analysis. This module demonstrates:
1. Copy-on-Write: Keeping the original cached data pristine.
2. String Normalization: Stripping whitespace and standardizing null values.
3. Type Coercion: Safely converting text representations of numbers into actual floats.
4. Index Management: Resetting index labels after removing duplicate rows.
"""

import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data
def clean_data(df):
    """
    Baseline auto-clean applied right after upload.
    
    Why st.cache_data?
    Streamlit runs the script from top to bottom on every user interaction.
    Caching ensures we don't re-run this cleaning process unless the input 'df' changes.
    """
    # 1. COPY-ON-WRITE: Always copy the DataFrame.
    # If we modify the original cached 'df' directly, it can bypass Streamlit's cache tracking
    # and cause unpredictable state bugs in other parts of the application.
    cleaned = df.copy()
    
    if cleaned.empty:
        return cleaned

    # 2. STRING NORMALIZATION
    # We iterate over every column. If it's a text-based column ('object' type),
    # we clean up stray whitespaces and standardize placeholder strings representing missing values.
    for column in cleaned.columns:
        if cleaned[column].dtype == object:
            # .astype(str) ensures all values are treated as string type.
            # .str.strip() removes leading and trailing spaces (e.g., " sales " -> "sales").
            cleaned[column] = cleaned[column].astype(str).str.strip()
            
            # Text files often represent missing values as strings like "nan", "None", or empty string "".
            # We map these string placeholders to NumPy's NaN (Not a Number) representation,
            # which pandas recognizes natively as empty cells.
            cleaned[column] = cleaned[column].replace({"nan": np.nan, "None": np.nan, "": np.nan})

    # 3. NUMERICAL TYPE COERCION
    # Obvious financial/currency columns are often imported as text (e.g., "$1,200.00").
    # We identify them by common keywords and attempt to convert them to numbers.
    for column in cleaned.columns:
        if column.lower() in {"gross", "price", "cost", "amount", "revenue"}:
            try:
                # Remove commas used as thousands separators (e.g., "1,200" -> "1200").
                cleaned[column] = cleaned[column].astype(str).str.replace(",", "", regex=False)
                
                # pd.to_numeric converts strings to numbers (integers/floats).
                # errors="coerce" tells pandas: if a cell cannot be parsed (e.g., "unknown"),
                # set it to NaN instead of raising a crash.
                cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
            except Exception:
                continue

    # 4. DUPLICATE REMOVAL & INDEX RESET
    # We drop identical rows to prevent bias in visualizations or machine learning.
    # drop_duplicates() preserves the original row indices (which leaves gaps, e.g., 0, 1, 3, 4).
    # reset_index(drop=True) discards the old index and creates a continuous 0, 1, 2... sequence.
    return cleaned.drop_duplicates().reset_index(drop=True)
