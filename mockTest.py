import pandas as pd
import requests
import json
import time
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# Configuration
CSV_PATH = "./synthetic_transaction_data.csv"
API_URL = "http://127.0.0.1:5000/detect_fraud"
THRESHOLD = 0.92  # threshold to decide fraud based on ML_fraud_score
DELAY_SECONDS = 0.2  # delay between API calls

# Load synthetic data
df = pd.read_csv(CSV_PATH)

# Sample request template (other fields remain constant)
sample_request = {
    "transaction_id": "",
    "user_id": "",
    "transaction_type": "withdrawal",
    "transaction_data": {},  # to be filled per row
    "login_data": {
        "session": {
            "userId": "user789",
            "deviceId": "device909",
            "timestamp": "2025-03-09T09:00:00Z",
            "latitude": "12.32",
            "longitude": "120.3"
        },
        "device_history_last_3_days": [
            { "userId": "user126", "deviceId": "device909", "timestamp": "2025-03-09T08:00:00Z" }
        ],
        "last_user_login": {
            "userId": "user789",
            "timestamp": "2025-03-09T08:30:00Z",
            "latitude": "12.32",
            "longitude": "122.3"
        }
    },
    "withdrawal_data": {
        "current_wallet_balance": "2",
        "withdrawal_amount": "1000",
        "conversion_rate": "2000",
        "avg_withdrawal_frequency_14d": "0.428",
        "withdrawals_24h": "3",
        "failed_withdrawals_24h": "0"
    },
    "geospacial_transaction_data_2d": []
}

# Prepare to collect results
actuals = []
scores = []

# Iterate over each row in the CSV
for idx, row in df.iterrows():
    # Fill transaction_data from CSV row (exclude the 'fraud' column)
    txn_data = row.drop("fraud").astype(float).to_dict()
    
    # Build request for this transaction
    req = sample_request.copy()
    req["transaction_id"] = f"txn_{idx}"
    req["user_id"] = f"user_{idx}"
    req["transaction_data"] = txn_data
    
    # Send POST request
    try:
        response = requests.post(API_URL, json=req)
        response.raise_for_status()
        result = response.json()
        score = result.get("ML_fraud_score", 0.0)
    except Exception as e:
        print(f"Error for index {idx}: {e}")
        score = 0.0
    
    # Store actual label and score
    actuals.append(int(row["fraud"]))
    scores.append(score)
    
    # Delay to avoid overwhelming the API
    time.sleep(DELAY_SECONDS)

# Convert scores to binary predictions using threshold
predictions = [1 if s >= THRESHOLD else 0 for s in scores]

# Compute metrics
accuracy = accuracy_score(actuals, predictions)
conf_mat = confusion_matrix(actuals, predictions)
report = classification_report(actuals, predictions)

# Output results
print("=== Fraud Detection Model Evaluation ===")
print(f"Total samples: {len(df)}")
print(f"Accuracy: {accuracy:.4f}")
print("\nConfusion Matrix:")
print(conf_mat)
print("\nClassification Report:")
print(report)
