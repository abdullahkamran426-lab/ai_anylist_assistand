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

Educational Note for Students:
-----------------------------
This module represents a complete automated machine learning (AutoML) workflow:
1. Problem Type Detection: We determine if we are performing:
   - Classification: Predicting a category (discrete group, e.g., Yes/No, Dog/Cat/Bird).
   - Regression: Predicting a continuous number (numerical value, e.g., Salary, Temperature).
2. Data Preprocessing (Imputation + Scaling):
   - Imputation: Replacing missing values (NaN) with estimated ones. We use the Median
     for numeric values (less affected by outliers) and the Most Frequent value for categories.
   - Scaling: Modifying numerical features to have a mean of 0 and standard deviation of 1.
     This is critical for algorithms like KNN or Logistic Regression that are sensitive to scale.
   - One-Hot Encoding: Turning text categories into binary indicator columns.
3. Estimator Pipeline: Chaining preprocessing and models together using scikit-learn Pipelines.
   This avoids "data leakage" (accidentally using test set metadata during training).
4. Model Comparison (Racing): We train and cross-validate multiple models to select the one
   with the highest performance.
5. Evaluation Metrics: We calculate performance metrics on a separate test set.
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
    RandomForestClassifier,
    RandomForestRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
)
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor


def detect_prediction_problem(df, target_column):
    """
    Guess whether the problem is Classification or Regression.
    
    Rule of thumb:
    - If the target column is text, it must be classification.
    - If the target column is numeric, but only has 10 or fewer distinct values
      (e.g., [0, 1] or survey responses 1-5), we treat it as classification.
    - If it's numeric with more than 10 unique values, we treat it as regression.
    """
    target = df[target_column]
    if pd.api.types.is_numeric_dtype(target):
        return "classification" if target.nunique() <= 10 else "regression"
    return "classification"


def _build_preprocessor(features):
    """
    Create a preprocessor (ColumnTransformer) that handles clean-up steps automatically.
    
    What is a preprocessor?
    It splits features into numeric and categorical types, applies appropriate transformations
    to each type, and then glues the processed columns back together.
    
    Transformations:
    - Numeric:
      1. SimpleImputer(strategy="median"): Fills missing values with the median of the column.
      2. StandardScaler(): Centers data around 0 with unit variance.
    - Categorical:
      1. SimpleImputer(strategy="most_frequent"): Fills missing values with the most common category.
      2. OneHotEncoder(handle_unknown="ignore"): Converts categories to binary columns.
         "ignore" handles unseen categories during prediction.
    """
    # Group columns by data type
    numeric_features = features.select_dtypes(include=np.number).columns.tolist()
    categorical_features = features.select_dtypes(exclude=np.number).columns.tolist()

    # Step-by-step pipeline for numeric columns
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    
    # Step-by-step pipeline for categorical columns
    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    
    # Combine transformations into a single object
    return ColumnTransformer(transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features),
    ])


def _candidate_models(problem):
    """
    Define candidate estimators to compare.
    
    We compare 5 diverse models:
    - Logistic/Linear Regression: Simple, interpretable baseline models.
    - Decision Tree: Simple tree rules. Prone to overfitting but very visual.
    - Random Forest: Ensemble (collection) of decision trees using bagging to reduce variance.
    - Gradient Boosting: Ensemble of sequential decision trees using boosting to reduce bias.
    - K-Nearest Neighbors: Instance-based classification/regression based on feature distance.
    """
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
    """
    AutoML entry point.
    
    Steps:
    1. Removes any rows where target is missing.
    2. Splits dataset into features (X) and target (y).
    3. Splits data into Train (75%) and Test (25%) sets.
       - Classification uses "stratification" to ensure target classes are balanced across splits.
    4. Automatically builds the preprocessing step based on X_train's columns.
    5. Iterates through all candidate models, trains them, and evaluates them.
       - Evaluates using Cross-Validation (3-fold) on the training set.
       - Evaluates on the held-out Test set.
    6. Selects the overall best model based on the test set score.
    7. Returns the best model pipeline, metrics, comparison logs, and feature importances.
    """
    if target_column not in df.columns:
        raise ValueError("Target column not found")
    if df[target_column].isna().all():
        raise ValueError("Target column has no usable values")

    # 1. Clean data: drop rows missing the target variable
    working = df.dropna(subset=[target_column]).copy()
    if len(working) < 10:
        raise ValueError(f"The dataset must have at least 10 rows after removing missing target values to train a model (currently has {len(working)}).")

    # 2. Separate features (X) and target (y)
    X = working.drop(columns=[target_column])
    if X.shape[1] == 0:
        raise ValueError("The dataset has no feature columns (excluding the target column) to train the model on.")

    # Cast all non-numeric columns to strings to prevent comparison errors during imputation/encoding
    for col in X.columns:
        if not pd.api.types.is_numeric_dtype(X[col]):
            X[col] = X[col].astype(str)

    y = working[target_column]
    problem = detect_prediction_problem(working, target_column)

    # 3. Train-Test Split
    # Stratify balances classes (e.g., ensuring 20% positive cases in both training and test sets).
    # It requires at least 2 samples per class. If it fails (e.g. rare class has 1 sample), we split without stratification.
    try:
        stratify = y if (problem == "classification" and y.nunique() > 1) else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=stratify
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    # 4. Prepare preprocessors and select metrics
    preprocessor = _build_preprocessor(X_train)
    candidates = _candidate_models(problem)
    scoring = "accuracy" if problem == "classification" else "r2"

    comparison = []
    best_name, best_pipeline, best_preds, best_score = None, None, None, -np.inf

    # 5. Model Racing loop
    for name, estimator in candidates.items():
        # Wrap preprocessing and the model into a single scikit-learn Pipeline
        pipeline = Pipeline(steps=[("preprocess", preprocessor), ("model", estimator)])
        try:
            # Fit model
            pipeline.fit(X_train, y_train)
            preds = pipeline.predict(X_test)

            # Cross-Validation: Splits train set into 3 groups, trains on 2, tests on 1, rotates 3 times.
            try:
                cv_score = float(np.mean(cross_val_score(pipeline, X_train, y_train, cv=3, scoring=scoring)))
            except Exception:
                cv_score = float("nan")

            # Calculate performance metrics
            if problem == "classification":
                row = {
                    "model": name,
                    "accuracy": round(float(accuracy_score(y_test, preds)), 4),
                    "f1_score": round(float(f1_score(y_test, preds, average="weighted")), 4),
                    "cv_score": round(cv_score, 4) if not np.isnan(cv_score) else None,
                }
                primary = row["accuracy"]  # Best classifier has highest accuracy
            else:
                row = {
                    "model": name,
                    "mae": round(float(mean_absolute_error(y_test, preds)), 4),
                    "rmse": round(float(np.sqrt(mean_squared_error(y_test, preds))), 4),
                    "r2_score": round(float(r2_score(y_test, preds)), 4),
                    "cv_score": round(cv_score, 4) if not np.isnan(cv_score) else None,
                }
                primary = row["r2_score"]  # Best regressor has highest R2 score (R-squared)

            comparison.append(row)
            
            # Select the winning model
            if primary > best_score:
                best_score, best_name, best_pipeline, best_preds = primary, name, pipeline, preds
        except Exception as exc:
            # Allow individual models to fail without crashing the whole application
            comparison.append({"model": name, "error": str(exc)})

    # Raise exception if no models could be fit
    if best_pipeline is None:
        errors = [f"{c['model']}: {c['error']}" for c in comparison if "error" in c]
        error_msg = "No candidate model could be trained successfully on this data."
        if errors:
            error_msg += " Detailed errors: " + "; ".join(errors)
        raise ValueError(error_msg)

    # 6. Format metrics of the best model
    if problem == "classification":
        metrics = {
            "problem": problem,
            "best_model": best_name,
            "accuracy": round(float(accuracy_score(y_test, best_preds)), 4),
            "f1": round(float(f1_score(y_test, best_preds, average="weighted")), 4),
            # Confusion matrix describes True Negatives, False Positives, False Negatives, True Positives
            "confusion_matrix": confusion_matrix(y_test, best_preds).tolist(),
            "labels": sorted(y_test.unique().tolist(), key=str),
        }
    else:
        metrics = {
            "problem": problem,
            "best_model": best_name,
            "mae": round(float(mean_absolute_error(y_test, best_preds)), 4),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, best_preds))), 4),
            # R2 describes the proportion of variance explained by features (1.0 is perfect)
            "r2": round(float(r2_score(y_test, best_preds)), 4),
            "actual": [float(v) for v in y_test.tolist()],
            "predicted": [float(v) for v in best_preds],
        }

    # 7. Extract Feature Importance (if supported by winning model)
    feature_importance = []
    fitted_model = best_pipeline.named_steps["model"]
    if hasattr(fitted_model, "feature_importances_"):
        try:
            # Get one-hot encoded feature names out
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
    """
    Run prediction for a single row.
    Takes sample_row as a dictionary of {column_name: value} and passes it through the pipeline.
    """
    return model.predict(pd.DataFrame([sample_row]))[0]


def save_prediction_model(model, path):
    """Serialize a fitted pipeline to disk with joblib."""
    joblib.dump(model, path)


def load_prediction_model(path):
    """Load a previously saved joblib pipeline."""
    return joblib.load(path)


def forecast_regression_series(series, periods=5):
    """
    Very simple linear-trend forecast.
    
    Logic:
    - We fit a simple Linear Regression model (y = m * x + c) where:
      - X is the index / step number (0, 1, 2, 3...)
      - y is the value of the numeric series
    - Extrapolates future values by predicting future steps (length, length+1...).
    """
    values = np.array(series.dropna()).astype(float)
    if len(values) < 2:
        return [float(values[-1])] * periods if len(values) else [0.0] * periods

    # Create index steps
    x = np.arange(len(values)).reshape(-1, 1)
    
    # Fit line
    model = LinearRegression().fit(x, values)
    
    # Define future steps
    future_x = np.arange(len(values), len(values) + periods).reshape(-1, 1)
    preds = model.predict(future_x)
    return [round(float(v), 2) for v in preds]
