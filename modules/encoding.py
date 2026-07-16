"""
Encoding
========
Categorical-to-numeric encoding helpers used by the Clean Data page's
"Encoding" panel:
    - get_encoding_recommendations(df)   suggest One-Hot vs Label encoding
                                          per categorical column, based on
                                          how many unique values it has
    - apply_one_hot_encoding(df, ...)    pandas.get_dummies()-based
    - apply_label_encoding(df, ...)      scikit-learn LabelEncoder-based,
                                          also returns the fitted encoders
                                          so the same mapping can be reused
                                          later (e.g. by the Prediction page
                                          to encode a new input row the
                                          same way before scoring it)
"""

import pandas as pd
from sklearn.preprocessing import LabelEncoder

# Cardinality threshold: categorical columns with this many unique values
# or fewer are recommended for one-hot encoding, since the resulting
# column count stays manageable. Columns above this are recommended for
# label encoding instead — one-hot would otherwise explode into too many
# new columns (e.g. a "city" column with 500 unique values).
ONE_HOT_CARDINALITY_THRESHOLD = 10


def get_encoding_recommendations(df):
    """
    Recommend an encoding strategy for every object/category column.

    Returns:
        dict: {column_name: {"unique_count": int,
                              "recommended_encoding": "One-Hot Encoding" | "Label Encoding",
                              "reason": str}}
    """
    recommendations = {}
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    for col in cat_cols:
        unique_count = int(df[col].nunique(dropna=True))
        if unique_count <= ONE_HOT_CARDINALITY_THRESHOLD:
            recommended = "One-Hot Encoding"
            reason = f"Only {unique_count} unique values — one-hot keeps the new column count manageable."
        else:
            recommended = "Label Encoding"
            reason = (f"{unique_count} unique values — one-hot would add {unique_count} new "
                       f"columns, so label encoding is more compact.")
        recommendations[col] = {
            "unique_count": unique_count,
            "recommended_encoding": recommended,
            "reason": reason,
        }
    return recommendations


def apply_one_hot_encoding(df, columns, drop_first=False):
    """
    One-hot encode the given columns via pandas.get_dummies(), replacing
    each original column with one indicator column per category (or
    n-1 columns per category if drop_first=True, to avoid the classic
    multicollinearity "dummy variable trap").

    Returns a NEW dataframe — the `df` passed in is not mutated, matching
    the same copy-don't-mutate convention as the rest of the cleaning
    pipeline (every Clean Data control re-assigns st.session_state.df from
    the return value rather than relying on in-place edits).
    """
    df = df.copy()
    df = pd.get_dummies(df, columns=columns, drop_first=drop_first)
    return df


def apply_label_encoding(df, columns):
    """
    Label-encode the given columns (each category mapped to an integer
    0..n-1), using scikit-learn's LabelEncoder.

    Returns:
        (df, encoders) — a NEW dataframe with the encoded columns, plus a
        dict of the fitted encoders ({column: LabelEncoder}) so the exact
        same category->integer mapping can be reused later — e.g. to encode
        a new row the same way before feeding it to a trained prediction
        model, or to inverse_transform a prediction back to its original
        category label.

    NaN values are temporarily filled with the string "Missing" before
    fitting, since LabelEncoder can't handle NaN directly — this way missing
    values become their own explicit category instead of raising an error
    or silently dropping rows.
    """
    df = df.copy()
    encoders = {}
    for col in columns:
        encoder = LabelEncoder()
        series = df[col].fillna("Missing").astype(str)
        df[col] = encoder.fit_transform(series)
        encoders[col] = encoder
    return df, encoders
