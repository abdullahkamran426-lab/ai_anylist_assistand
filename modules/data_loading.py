"""
Data Loading
============
Everything that turns raw uploaded bytes into a pandas DataFrame:
content hashing (used as a cache key by the Upload page) and
format-dispatching load_data() for CSV, Excel, JSON, TSV/TXT, and Parquet.

No cleaning or analysis logic lives here — see data_cleaning.py and
statistics.py for that. Keeping I/O isolated means this module has the
narrowest dependency footprint (just pandas + streamlit's cache decorator),
so it's cheap to import from anywhere without pulling in matplotlib/sklearn.
"""

import hashlib
import io

import pandas as pd
import streamlit as st


def compute_file_hash(file_bytes):
    """Stable MD5 hash of an uploaded file's raw bytes — used as a cache key
    so re-uploading the same file doesn't re-parse it."""
    return hashlib.md5(file_bytes).hexdigest()


@st.cache_data
def load_data(file_bytes, filename="dataset"):
    """Load CSV, Excel, JSON, TSV, or Parquet bytes into a pandas DataFrame.

    Dispatches on the file extension in `filename`; CSV/TSV additionally
    fall back through a few common encodings since uploaded files aren't
    guaranteed to be UTF-8.

    Args:
        file_bytes: raw bytes of the uploaded file (e.g. from
                    st.file_uploader(...).getvalue()).
        filename:   original filename, used only to pick the parser —
                    defaults to "dataset" (treated as CSV) if omitted.
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
