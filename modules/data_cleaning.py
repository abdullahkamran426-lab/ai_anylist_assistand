"""
Data Cleaning
=============
The baseline auto-clean pipeline applied automatically right after upload
(see data_loading.py). This is intentionally conservative: it only fixes
things that are unambiguous formatting noise (stray whitespace, "nan"-as-
text, obvious currency columns, exact duplicate rows) — it never guesses
at semantic fixes, since those belong in the interactive Clean Data page
where the user explicitly chooses a strategy.
"""

import numpy as np
import pandas as pd
import streamlit as st


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
