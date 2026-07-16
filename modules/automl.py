"""
AutoML (Prediction Module)
===========================
End-to-end AutoML: detect_prediction_problem() picks classification vs.
regression, train_prediction_model() races 5 candidate models behind a
shared preprocessing pipeline (impute + scale numeric, impute + one-hot
categorical) and keeps the best one, and the rest are small utilities
built around that trained model: single-row prediction, saving/loading
the fitted pipeline with joblib (for the "Download model (.pkl)" button),
and a simple linear-trend forecast for a numeric series.

Nothing here touches Streamlit's UI — this is pure model-training logic,
so the Prediction page in pages.py can call these functions and just
render whatever dict comes back.
"""

import numpy as np
import pandas as pd
import joblib

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
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor


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
    if len(working) < 10:
        raise ValueError(f"The dataset must have at least 10 rows after removing missing target values to train a model (currently has {len(working)}).")

    X = working.drop(columns=[target_column])
    if X.shape[1] == 0:
        raise ValueError("The dataset has no feature columns (excluding the target column) to train the model on.")

    # Cast all non-numeric columns to strings to prevent SimpleImputer/OneHotEncoder errors
    for col in X.columns:
        if not pd.api.types.is_numeric_dtype(X[col]):
            X[col] = X[col].astype(str)

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
        errors = [f"{c['model']}: {c['error']}" for c in comparison if "error" in c]
        error_msg = "No candidate model could be trained successfully on this data."
        if errors:
            error_msg += " Detailed errors: " + "; ".join(errors)
        raise ValueError(error_msg)

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
