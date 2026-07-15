import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer

from sklearn.model_selection import train_test_split

# Regression
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor

# Classification
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    r2_score,
    mean_absolute_error,
    mean_squared_error,
)


def detect_problem_type(df, target):
    """
    Automatically determine whether the target is
    regression or classification.
    """

    if pd.api.types.is_numeric_dtype(df[target]):

        if df[target].nunique() <= 20:
            return "classification"

        return "regression"

    return "classification"


def prepare_data(df, target):

    X = df.drop(columns=[target])
    y = df[target]

    categorical = X.select_dtypes(include=["object", "category"]).columns
    numerical = X.select_dtypes(exclude=["object", "category"]).columns

    numeric_transformer = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

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
        ]
    )

    return X, y, preprocessor



def get_models(problem_type):

    if problem_type == "regression":

        return {
            "Linear Regression": LinearRegression(),
            "Decision Tree": DecisionTreeRegressor(random_state=42),
            "Random Forest": RandomForestRegressor(
                random_state=42
            ),
        }

    return {
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Decision Tree": DecisionTreeClassifier(
            random_state=42
        ),
        "Random Forest": RandomForestClassifier(
            random_state=42
        ),
    }


def train_models(df, target):

    problem = detect_problem_type(df, target)

    X, y, preprocessor = prepare_data(df, target)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    models = get_models(problem)

    best_model = None
    best_name = None
    best_score = -999

    metrics = {}

    for name, model in models.items():

        pipe = Pipeline(
            [
                ("prep", preprocessor),
                ("model", model),
            ]
        )

        pipe.fit(X_train, y_train)

        pred = pipe.predict(X_test)

        if problem == "regression":

            score = r2_score(y_test, pred)

            metrics[name] = {
                "R2": score,
                "MAE": mean_absolute_error(y_test, pred),
                "RMSE": np.sqrt(mean_squared_error(y_test, pred)),
            }

        else:

            score = accuracy_score(y_test, pred)

            metrics[name] = {
                "Accuracy": score,
                "Precision": precision_score(
                    y_test,
                    pred,
                    average="weighted",
                    zero_division=0,
                ),
                "Recall": recall_score(
                    y_test,
                    pred,
                    average="weighted",
                    zero_division=0,
                ),
                "F1": f1_score(
                    y_test,
                    pred,
                    average="weighted",
                    zero_division=0,
                ),
            }

        if score > best_score:

            best_score = score
            best_model = pipe
            best_name = name

    return {
        "problem": problem,
        "best_model": best_model,
        "best_model_name": best_name,
        "metrics": metrics,
        "X": X,
    }


def save_model(model, filename="trained_model.pkl"):

    joblib.dump(model, filename)

    return filename


def predict(model, input_df):

    return model.predict(input_df)
