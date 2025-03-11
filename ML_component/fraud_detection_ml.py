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
MODEL_PATH = os.path.join(os.path.dirname(__file__), "lightGBM_fraud_model_final_modified.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "modified_scaler.pkl")


with open(MODEL_PATH, "rb") as model_file:
    model = joblib.load(model_file)
    model.set_params(device="cpu", n_jobs=-1)  #use all cpu threads

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

                # Define column names
        feature_names = [
            "Avg min between sent tnx", "Avg min between received tnx",
            "Time Diff between first and last (Mins)", "Unique Received From Addresses",
            "min value received", "max value received", "avg val received",
            "min val sent", "avg val sent",
            "total transactions (including tnx to create contract)",
            "total ether received", "total ether balance"
        ]

        # Convert NumPy array to DataFrame
        df_processed = pd.DataFrame(npArray_processed, columns=feature_names)


        # Predict fraud probability
        # fraud_probability = model.predict_proba(df_processed)[:, 1][0]
        fraud_probability = 1 #test

        # Store result
        results["ML_fraud_score"] = round(fraud_probability, 4)  # Keep 4 decimal places

    except Exception as e:
        results["ML_fraud_score"] = None  # Indicate an error
        print(f"Error in ML fraud detection: {e}")
