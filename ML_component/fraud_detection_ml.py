import os
import joblib
import pandas as pd
import numpy as np
# import lightgbm
# import sklearn

# Define log transformation function
def log_transform_df(X):
    X = X.copy()
    for col in X.columns:
        X[col] = X[col].apply(lambda x: np.log(x) if x > 0 else 0)
    return X

# Load the trained model and scaler
MODEL_PATH = os.path.join(os.path.dirname(__file__), "lightGBM_fraud_model_final_modified.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "modified_scaler.pkl")

with open(MODEL_PATH, "rb") as model_file:
    model = joblib.load(model_file)

# Ensure compatibility for CPU-based execution
if hasattr(model, "set_params"):
    model.set_params(n_jobs=-1)

with open(SCALER_PATH, "rb") as scaler_file:
    scaler = joblib.load(scaler_file)

def detect_fraud_ml(request_data, results):
    """
    Detects fraudulent transactions using a trained LightGBM model.

    Args:
        request_data (dict): JSON request containing transaction data.
        results (dict): A multiprocessing-safe dictionary to store the fraud score.

    Returns:
        None (updates the results dictionary with the fraud probability score).
    """

    # Extract transaction data from the request
    transaction_data = request_data.get("transaction_data")

    # If transaction data is missing, return None as the fraud score
    if not transaction_data:
        results["ML_fraud_score"] = None
        return

    try:
        # Convert transaction data to a DataFrame
        df = pd.DataFrame([transaction_data])

        # Define expected feature names (ensuring correct order)
        feature_names = [
            "Avg min between sent tnx", "Avg min between received tnx",
            "Time Diff between first and last (Mins)", "Unique Received From Addresses",
            "min value received", "max value received", "avg val received",
            "min val sent", "avg val sent",
            "total transactions (including tnx to create contract)",
            "total ether received", "total ether balance"
        ]

        # Validate if all expected features are present in the input data
        if set(feature_names) != set(df.columns):
            raise ValueError(f"Feature mismatch! Expected: {feature_names}, Got: {df.columns}")

        # Apply log transformation to the data
        df = log_transform_df(df)

        # Scale the transformed data
        npArray_processed = scaler.transform(df)

        # Convert back to a DataFrame with correct column names
        df_processed = pd.DataFrame(npArray_processed, columns=feature_names)

        # Predict fraud probability using the trained LightGBM model
        fraud_probability = model.predict_proba(df_processed)[:, 1][0]

        # Store the fraud probability in the results dictionary (rounded to 4 decimal places)
        results["ML_fraud_score"] = round(fraud_probability, 4)

    except ValueError as ve:
        print(f"ValueError in ML fraud detection: {ve}")
        results["ML_fraud_score"] = None
    except Exception as e:
        print(f"Unexpected error in ML fraud detection: {e}")
        results["ML_fraud_score"] = None
