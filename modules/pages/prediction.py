import pandas as pd
import streamlit as st

from modules.prediction import forecast_series, predict, save_model, train_models
from modules.utils import section


def render_prediction_page():
    section("PREDICTION", "AutoML-style prediction studio")

    df = st.session_state.get("df")
    if df is None:
        st.warning("Please upload a dataset first.")
        return

    st.success(f"Dataset loaded: {df.shape[0]} rows × {df.shape[1]} columns")

    target = st.selectbox("Select target column", df.columns, key="prediction_target")
    if st.button("Train model", type="primary"):
        with st.spinner("Training and comparing models..."):
            result = train_models(df, target)
        st.session_state["prediction_result"] = result

    if "prediction_result" not in st.session_state:
        return

    result = st.session_state["prediction_result"]
    st.markdown("### 🏆 Best model")
    st.info(f"{result['best_model_name']} • Problem type: {result['problem']}")

    metrics = result["metrics"][result["best_model_name"]]
    cols = st.columns(len(metrics))
    for col, (name, value) in zip(cols, metrics.items()):
        col.metric(name, f"{value:.4f}")

    if result.get("feature_importance") is not None:
        st.markdown("### 🔍 Feature importance")
        st.bar_chart(result["feature_importance"])

    if result.get("confusion_matrix") is not None:
        st.markdown("### 🧠 Confusion matrix")
        st.dataframe(pd.DataFrame(result["confusion_matrix"], columns=["Pred 0", "Pred 1"], index=["Actual 0", "Actual 1"]))

    if result.get("cross_val_scores"):
        st.markdown("### 📈 Cross-validation scores")
        st.write(result["cross_val_scores"])

    if st.button("Save trained model"):
        path = save_model(result["best_model"], filename="trained_model.pkl")
        with open(path, "rb") as fh:
            st.download_button("Download model", fh, file_name="trained_model.pkl", mime="application/octet-stream")

    st.markdown("---")
    st.subheader("📝 Make a prediction")
    X = result["X"]
    user_data = {}
    for col in X.columns:
        if pd.api.types.is_numeric_dtype(X[col]):
            user_data[col] = st.number_input(col, value=float(X[col].median()), key=f"pred_input_{col}")
        else:
            options = sorted([value for value in X[col].dropna().unique().tolist() if pd.notna(value)])
            user_data[col] = st.selectbox(col, options, key=f"pred_select_{col}")

    if st.button("Predict"):
        input_df = pd.DataFrame([user_data])
        prediction = predict(result["best_model"], input_df)[0]
        st.success(f"Prediction: {prediction}")

    st.markdown("---")
    st.subheader("📉 Forecast support")
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    if numeric_columns:
        forecast_col = st.selectbox("Series to forecast", numeric_columns, key="forecast_series")
        periods = st.slider("Forecast horizon", min_value=1, max_value=12, value=6)
        if st.button("Forecast"):
            forecast = forecast_series(df[forecast_col].dropna(), periods=periods)
            st.line_chart(forecast)
    else:
        st.info("No numeric columns available for forecasting.")
