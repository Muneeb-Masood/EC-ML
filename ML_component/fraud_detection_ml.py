import os
import joblib
import pandas as pd
import numpy as np
# import lightgbm
#import sklearn


# define the log transform function
def log_transform_df(X):
    X = X.copy()
    for col in X.columns:
        X[col] = X[col].apply(lambda x: np.log(x) if x > 0 else 0)
    return X


# Load the model and preprocessor
MODEL_PATH = os.path.join(os.path.dirname(__file__), "lightGBM_fraud_model_final.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.pkl")


with open(MODEL_PATH, "rb") as model_file:
    model = joblib.load(model_file)

with open(SCALER_PATH, "rb") as scaler_file:
    scaler = joblib.load(scaler_file)

def detect_fraud_ml(request_data, results):
    """
    Detects fraud probability using a trained LightGBM model.
    
    Args:
        request_data (dict): The request JSON containing transaction data.
        results (dict): A multiprocessing-safe dictionary to store the fraud score.
    
    Returns:
        None (updates the results dictionary)
    """

    # Extract transaction data
    transaction_data = request_data.get("transaction_data")

    # Ensure the required data is present
    if not transaction_data:
        results["ML_fraud_score"] = None  # Indicate missing data
        return

    try:
        # Convert to DataFrame with correct column names
        df = pd.DataFrame([transaction_data])

        # log transform data
        df = log_transform_df(df)

        # Scale data
        npArray_processed = scaler.transform(df)

        # Predict fraud probability
        fraud_probability = model.predict_proba(npArray_processed)[:, 1][0]

        # Store result
        results["ML_fraud_score"] = round(fraud_probability, 4)  # Keep 4 decimal places

    except Exception as e:
        results["ML_fraud_score"] = None  # Indicate an error
        print(f"Error in ML fraud detection: {e}")
