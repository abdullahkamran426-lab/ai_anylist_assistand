import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
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
    
    # Validate result is a dictionary
    if result is None or not isinstance(result, dict):
        st.error("Invalid prediction result format. Please retrain the model.")
        return
    
    st.markdown("### 🏆 Best model")
    st.info(f"{result.get('best_model_name', 'Unknown')} • Problem type: {result.get('problem', 'Unknown')}")

    if "metrics" in result and result["best_model_name"] in result["metrics"]:
        metrics = result["metrics"][result["best_model_name"]]
        cols = st.columns(len(metrics))
        for col, (name, value) in zip(cols, metrics.items()):
            col.metric(name, f"{value:.4f}")

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

    if "cross_val_scores" in result and result["cross_val_scores"] is not None:
        st.markdown("### 📈 Cross-validation scores")
        cv_scores = result["cross_val_scores"]
        
        # Display as bar chart
        if len(cv_scores) > 0:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(range(1, len(cv_scores) + 1), cv_scores, color='steelblue', alpha=0.7)
            ax.set_xlabel('Fold')
            ax.set_ylabel('Score')
            ax.set_title('Cross-Validation Scores')
            ax.set_ylim([0, 1])
            ax.axhline(y=np.mean(cv_scores), color='red', linestyle='--', label=f'Mean: {np.mean(cv_scores):.4f}')
            ax.legend()
            st.pyplot(fig)
            plt.close(fig)
            
            # Show statistics
            col1, col2, col3 = st.columns(3)
            col1.metric("Mean", f"{np.mean(cv_scores):.4f}")
            col2.metric("Std", f"{np.std(cv_scores):.4f}")
            col3.metric("Min", f"{np.min(cv_scores):.4f}")
            
            # Also show raw values in expander
            with st.expander("View raw scores"):
                st.write(cv_scores)
        else:
            st.info("No cross-validation scores available")

    if st.button("Save trained model"):
        try:
            if "best_model" in result:
                path = save_model(result["best_model"], filename="trained_model.pkl")
                with open(path, "rb") as fh:
                    st.download_button("Download model", fh, file_name="trained_model.pkl", mime="application/octet-stream")
            else:
                st.error("No trained model found. Please retrain the model.")
        except Exception as e:
            st.error(f"Error saving model: {str(e)}")

    st.markdown("---")
    st.subheader("📝 Make a prediction")
    
    if "X" not in result:
        st.error("Feature data not available. Please retrain the model.")
        return
        
    X = result["X"]
    user_data = {}
    for col in X.columns:
        if pd.api.types.is_numeric_dtype(X[col]):
            user_data[col] = st.number_input(col, value=float(X[col].median()), key=f"pred_input_{col}")
        else:
            options = sorted([value for value in X[col].dropna().unique().tolist() if pd.notna(value)])
            user_data[col] = st.selectbox(col, options, key=f"pred_select_{col}")

    if st.button("Predict"):
        try:
            if "best_model" in result:
                input_df = pd.DataFrame([user_data])
                prediction = predict(result["best_model"], input_df)[0]
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
            forecast = forecast_series(df[forecast_col].dropna(), periods=periods)
            st.line_chart(forecast)
    else:
        st.info("No numeric columns available for forecasting.")
