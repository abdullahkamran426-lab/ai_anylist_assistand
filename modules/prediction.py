import os
import tempfile
from typing import Dict, Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor


def detect_problem_type(df: pd.DataFrame, target: str) -> str:
    """Infer whether the target should be treated as regression or classification."""
    series = df[target]
    if pd.api.types.is_numeric_dtype(series):
        if series.nunique() <= 20:
            return "classification"
        return "regression"
    return "classification"


def prepare_data(df: pd.DataFrame, target: str):
    """Separate features and target and build preprocessing steps."""
    X = df.drop(columns=[target])
    y = df[target]

    categorical = X.select_dtypes(include=["object", "category"]).columns.tolist()
    numerical = X.select_dtypes(exclude=["object", "category"]).columns.tolist()

    numeric_transformer = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    categorical_transformer = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        [
            ("num", numeric_transformer, numerical),
            ("cat", categorical_transformer, categorical),
        ],
        remainder="drop",
    )
    return X, y, preprocessor


def get_models(problem_type: str):
    if problem_type == "regression":
        return {
            "Linear Regression": LinearRegression(),
            "Decision Tree": DecisionTreeRegressor(random_state=42),
            "Random Forest": RandomForestRegressor(random_state=42, n_estimators=200),
        }
    return {
        "Logistic Regression": LogisticRegression(max_iter=4000),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(random_state=42, n_estimators=200),
    }


def _score_model(pipe, X_test, y_test, problem_type: str) -> Dict[str, float]:
    pred = pipe.predict(X_test)
    if problem_type == "regression":
        return {
            "R2": round(float(r2_score(y_test, pred)), 4),
            "MAE": round(float(mean_absolute_error(y_test, pred)), 4),
            "RMSE": round(float(np.sqrt(mean_squared_error(y_test, pred))), 4),
        }
    pred = pred.astype(str)
    y_test = y_test.astype(str)
    return {
        "Accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "Precision": round(float(precision_score(y_test, pred, average="weighted", zero_division=0)), 4),
        "Recall": round(float(recall_score(y_test, pred, average="weighted", zero_division=0)), 4),
        "F1": round(float(f1_score(y_test, pred, average="weighted", zero_division=0)), 4),
    }


def train_models(df: pd.DataFrame, target: str) -> Dict[str, Any]:
    """Train several candidate models and keep the strongest performer."""
    problem_type = detect_problem_type(df, target)
    X, y, preprocessor = prepare_data(df, target)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    models = get_models(problem_type)

    metrics = {}
    best_model = None
    best_name = None
    best_score = -np.inf

    for name, model in models.items():
        pipe = Pipeline([("prep", preprocessor), ("model", model)])
        pipe.fit(X_train, y_train)
        score = _score_model(pipe, X_test, y_test, problem_type)
        metrics[name] = score
        primary_metric = list(score.keys())[0]
        current_value = score[primary_metric]
        if current_value > best_score:
            best_score = current_value
            best_model = pipe
            best_name = name

    cv_scores = []
    try:
        if len(X) >= 10:
            cv_pipe = Pipeline([("prep", preprocessor), ("model", models[best_name])])
            # Use appropriate number of folds based on dataset size
            n_folds = min(5, max(2, len(X) // 3))
            cv_scores = cross_val_score(cv_pipe, X, y, cv=n_folds, 
                                      scoring="accuracy" if problem_type == "classification" else "r2",
                                      n_jobs=-1)
        elif len(X) >= 5:
            # For smaller datasets, use fewer folds
            cv_pipe = Pipeline([("prep", preprocessor), ("model", models[best_name])])
            cv_scores = cross_val_score(cv_pipe, X, y, cv=2, 
                                      scoring="accuracy" if problem_type == "classification" else "r2",
                                      n_jobs=-1)
    except Exception as e:
        # If cross-validation fails, leave empty list
        cv_scores = []

    feature_importance = None
    if best_model is not None:
        try:
            feature_importance = pd.Series(best_model.named_steps["model"].feature_importances_, index=best_model.named_steps["prep"].get_feature_names_out()).sort_values(ascending=False).head(10)
        except Exception:
            feature_importance = None

    confusion = None
    if problem_type == "classification":
        pred = best_model.predict(X_test)
        confusion = confusion_matrix(y_test.astype(str), pred.astype(str)).tolist()

    return {
        "problem": problem_type,
        "best_model": best_model,
        "best_model_name": best_name,
        "metrics": metrics,
        "X": X,
        "y": y,
        "feature_importance": feature_importance,
        "confusion_matrix": confusion,
        "cross_val_scores": cv_scores,
        "target": target,
    }


def save_model(model, filename="trained_model.pkl"):
    path = os.path.join(tempfile.gettempdir(), filename)
    joblib.dump(model, path)
    return path


def predict(model, input_df):
    return model.predict(input_df)


def forecast_series(series: pd.Series, periods: int = 6):
    """Very lightweight forecasting hook for numeric series data."""
    if series.dropna().empty:
        return pd.Series([np.nan] * periods, index=range(1, periods + 1))
    values = pd.Series(series.dropna().astype(float).to_numpy())
    if len(values) < 2:
        return pd.Series([float(values.iloc[0])] * periods, index=range(1, periods + 1))
    trend = values.diff().dropna().mean()
    forecast = []
    for _ in range(periods):
        last_value = values.iloc[-1] + trend
        forecast.append(last_value)
        values = pd.concat([values, pd.Series([last_value])], ignore_index=True)
    return pd.Series(forecast, index=range(1, periods + 1))
