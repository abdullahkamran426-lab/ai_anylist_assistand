import streamlit as st
import pandas as pd

from modules.prediction import (
    train_models,
    save_model,
)
from modules.utils import section


def render_prediction_page():
    section("PREDICTION", "AI Prediction & Forecast")

    df = st.session_state.get("df")

    if df is None:
        st.warning("Please upload a dataset first.")
        return

    st.success(f"Dataset Loaded: {df.shape[0]} rows × {df.shape[1]} columns")

    st.subheader("🎯 Select Target Column")

    target = st.selectbox(
        "Target Column",
        df.columns
    )

    if st.button("🚀 Train Model", use_container_width=True):

        with st.spinner("Training models..."):

            result = train_models(df, target)

        st.session_state["prediction_result"] = result

    if "prediction_result" not in st.session_state:
        return

    result = st.session_state["prediction_result"]

    st.success("Training Complete!")

    st.markdown("## 🏆 Best Model")

    st.info(result["best_model_name"])

    st.markdown("## 📊 Model Performance")

    metrics = result["metrics"][result["best_model_name"]]

    cols = st.columns(len(metrics))

    for i, (k, v) in enumerate(metrics.items()):
        cols[i].metric(k, f"{v:.4f}")

    st.markdown("---")

    if st.button("💾 Save Trained Model"):

        path = save_model(result["best_model"])

        with open(path, "rb") as f:

            st.download_button(
                "⬇ Download Model",
                f,
                file_name="trained_model.pkl",
                mime="application/octet-stream",
                use_container_width=True,
            )

    st.markdown("---")

    st.subheader("📝 Make Prediction")

    X = result["X"]

    user_data = {}

    for col in X.columns:

        if pd.api.types.is_numeric_dtype(X[col]):

            user_data[col] = st.number_input(
                col,
                value=float(X[col].median())
            )

        else:

            user_data[col] = st.selectbox(
                col,
                sorted(X[col].dropna().unique())
            )

    if st.button("🔮 Predict", use_container_width=True):

        input_df = pd.DataFrame([user_data])

        prediction = result["best_model"].predict(input_df)[0]

        st.success(f"Prediction: {prediction}")
