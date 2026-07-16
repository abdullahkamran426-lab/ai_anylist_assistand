import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

from modules.automl import (
    forecast_regression_series,
    predict_with_model,
    save_prediction_model,
    train_prediction_model,
)
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
            result = train_prediction_model(df, target)
        st.session_state["prediction_result"] = result

    if "prediction_result" not in st.session_state:
        return

    result = st.session_state["prediction_result"]
    
    # Validate result is a dictionary
    if result is None or not isinstance(result, dict):
        st.error("Invalid prediction result format. Please retrain the model.")
        return
    
    st.markdown("### 🏆 Best model")
    st.info(f"{result.get('best_model_name', 'Unknown')} • Problem type: {result.get('problem', 'Unknown')}")

    # Handle new automl.py return structure
    if "metrics" in result:
        metrics = result["metrics"]
        if result.get("problem") == "classification":
            # Classification metrics: accuracy, f1, confusion_matrix, labels
            cols = st.columns(3)
            cols[0].metric("Accuracy", f"{metrics.get('accuracy', 0):.4f}")
            cols[1].metric("F1 Score", f"{metrics.get('f1', 0):.4f}")
            cols[2].metric("Problem", metrics.get('problem', 'Unknown'))
        else:
            # Regression metrics: mae, rmse, r2
            cols = st.columns(3)
            cols[0].metric("MAE", f"{metrics.get('mae', 0):.4f}")
            cols[1].metric("RMSE", f"{metrics.get('rmse', 0):.4f}")
            cols[2].metric("R²", f"{metrics.get('r2', 0):.4f}")

    if result.get("feature_importance") is not None:
        st.markdown("### 🔍 Feature importance")
        st.bar_chart(result["feature_importance"])

    if result.get("confusion_matrix") is not None:
        st.markdown("### 🧠 Confusion matrix")
        try:
            cm = result["confusion_matrix"]
            # Handle different confusion matrix formats
            if isinstance(cm, (list, np.ndarray)):
                cm_array = np.array(cm)
                if cm_array.ndim == 2:
                    # Determine appropriate column and index names based on matrix size
                    n_classes = cm_array.shape[0]
                    if n_classes == 2:
                        columns = ["Pred 0", "Pred 1"]
                        index = ["Actual 0", "Actual 1"]
                    else:
                        columns = [f"Pred {i}" for i in range(n_classes)]
                        index = [f"Actual {i}" for i in range(n_classes)]
                    
                    # Create heatmap
                    fig, ax = plt.subplots(figsize=(8, 6))
                    sns.heatmap(cm_array, annot=True, fmt='d', cmap='Blues', 
                                xticklabels=columns, yticklabels=index, ax=ax)
                    ax.set_xlabel('Predicted')
                    ax.set_ylabel('Actual')
                    ax.set_title('Confusion Matrix')
                    st.pyplot(fig)
                    plt.close(fig)
                    
                    # Also show as dataframe for detailed view
                    with st.expander("View as table"):
                        st.dataframe(pd.DataFrame(cm_array, columns=columns, index=index))
                else:
                    st.warning("Confusion matrix has unexpected shape")
                    st.write(cm)
            else:
                st.warning("Confusion matrix has unexpected format")
                st.write(cm)
        except Exception as e:
            st.error(f"Error displaying confusion matrix: {str(e)}")
            st.write("Raw confusion matrix data:")
            st.write(result["confusion_matrix"])

    if "comparison" in result and result["comparison"] is not None:
        st.markdown("### 📈 Model comparison")
        comparison_df = pd.DataFrame(result["comparison"])
        st.dataframe(comparison_df)

    if st.button("Save trained model"):
        try:
            if "model" in result:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp:
                    path = tmp.name
                save_prediction_model(result["model"], path)
                with open(path, "rb") as fh:
                    st.download_button("Download model", fh, file_name="trained_model.pkl", mime="application/octet-stream")
            else:
                st.error("No trained model found. Please retrain the model.")
        except Exception as e:
            st.error(f"Error saving model: {str(e)}")

    st.markdown("---")
    st.subheader("📝 Make a prediction")

    if "feature_columns" not in result:
        st.error("Feature data not available. Please retrain the model.")
        return

    feature_columns = result["feature_columns"]
    user_data = {}
    for col in feature_columns:
        if col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                user_data[col] = st.number_input(col, value=float(df[col].median()), key=f"pred_input_{col}")
            else:
                options = sorted([value for value in df[col].dropna().unique().tolist() if pd.notna(value)])
                user_data[col] = st.selectbox(col, options, key=f"pred_select_{col}")

    if st.button("Predict"):
        try:
            if "model" in result:
                input_df = pd.DataFrame([user_data])
                prediction = predict_with_model(result["model"], user_data)
                st.success(f"Prediction: {prediction}")
            else:
                st.error("No trained model found. Please retrain the model.")
        except Exception as e:
            st.error(f"Error making prediction: {str(e)}")

    st.markdown("---")
    st.subheader("📉 Forecast support")
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    if numeric_columns:
        forecast_col = st.selectbox("Series to forecast", numeric_columns, key="forecast_series")
        periods = st.slider("Forecast horizon", min_value=1, max_value=12, value=6)
        if st.button("Forecast"):
            forecast = forecast_regression_series(df[forecast_col].dropna(), periods=periods)
            st.line_chart(forecast)
    else:
        st.info("No numeric columns available for forecasting.")
