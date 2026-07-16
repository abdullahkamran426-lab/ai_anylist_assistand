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

Educational Note for Students:
-----------------------------
Machine Learning models (like Linear Regression, Random Forests, etc.) only accept
numbers as input, not text. Therefore, we must convert categorical (text) columns
into numbers. There are two primary techniques demonstrated here:

1. One-Hot Encoding: Creates a new binary (0 or 1) column for every unique value in
   a column. Excellent for categories without order (e.g., Color: Red, Blue, Green).
   *Warning*: If a column has too many unique values (high cardinality, e.g., "Zip Codes"),
   One-Hot Encoding will create hundreds of new columns, slowing down model training.
   
2. Label Encoding: Maps each unique text value to a specific integer (e.g., Red -> 0,
   Blue -> 1, Green -> 2). It keeps the dataset compact, but can mistakenly imply
   an ordinal order (e.g., Green is "greater" than Red because 2 > 0).
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
    Recommend an encoding strategy for every object/category column based on cardinality.
    
    Returns:
        dict: {column_name: {"unique_count": int,
                             "recommended_encoding": "One-Hot Encoding" | "Label Encoding",
                             "reason": str}}
    """
    recommendations = {}
    
    # Select columns that contain text data (object or category data types)
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    
    for col in cat_cols:
        # Count unique non-null values
        unique_count = int(df[col].nunique(dropna=True))
        
        # If number of unique categories is low, recommend One-Hot Encoding
        if unique_count <= ONE_HOT_CARDINALITY_THRESHOLD:
            recommended = "One-Hot Encoding"
            reason = f"Only {unique_count} unique values — one-hot keeps the new column count manageable."
        else:
            # If unique categories are high, recommend Label Encoding to prevent column explosion
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
    One-hot encode the given columns via pandas.get_dummies().
    
    Each original column is replaced with one indicator column per category
    (e.g., Color becomes Color_Red, Color_Blue).
    
    What is the dummy variable trap (drop_first=True)?
    If we have two categories (Male and Female), having both columns is redundant because
    if Male = 0, then Female must be 1. This perfect correlation causes multicollinearity,
    which disrupts linear models. By setting drop_first=True, we drop one category,
    representing it when all other indicators are 0.
    """
    df = df.copy()
    df = pd.get_dummies(df, columns=columns, drop_first=drop_first)
    return df


def apply_label_encoding(df, columns):
    """
    Label-encode the given columns (each category mapped to an integer 0..n-1)
    using scikit-learn's LabelEncoder.

    Returns:
        (df, encoders) — a NEW dataframe with the encoded columns, plus a
        dict of the fitted encoders ({column: LabelEncoder}) so the exact
        same category->integer mapping can be reused later.

    Handling NaN (Missing) Values:
    ------------------------------
    scikit-learn's LabelEncoder cannot handle missing values (NaN) directly and will crash.
    To prevent this, we temporarily fill any missing values with the string "Missing".
    This turns "missingness" into its own explicit category class (mapped to an integer),
    which is a common and robust practice in data science.
    """
    df = df.copy()
    encoders = {}
    for col in columns:
        encoder = LabelEncoder()
        
        # Fill missing values and convert all to string to prevent mixed-type comparison errors during encoding
        series = df[col].fillna("Missing").astype(str)
        df[col] = encoder.fit_transform(series)
        encoders[col] = encoder
        
    return df, encoders
