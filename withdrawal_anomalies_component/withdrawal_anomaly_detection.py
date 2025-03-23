import logging
import json
import os

# Get the directory of the current script (ensures it works even if called from a different location)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# Load JSON configuration
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

# Read constants from JSON
LARGE_WITHDRAWAL_THRESHOLD = config.get("LARGE_WITHDRAWAL_THRESHOLD", 0.5)
MAX_DAILY_WITHDRAWALS = config.get("MAX_DAILY_WITHDRAWALS", 15)
MAX_LAUNDERING_THRESHOLD = config.get("MAX_LAUNDERING_THRESHOLD", 6.0)
MAX_DAILY_FAILED_WITHDRAWALS = config.get("MAX_DAILY_FAILED_WITHDRAWALS", 10)


def detect_withdrawal_anomalies(data, results):
    """Detects withdrawal anomalies using predefined rules."""
    try:
        withdrawal_data = data.get("withdrawal_data", {})

        if not withdrawal_data:
            results["withdrawal_anomalies"] = {}
            return

        # Extract fields safely
        try:
            current_wallet_balance = float(withdrawal_data.get("current_wallet_balance", 0))  
            withdrawal_amount = float(withdrawal_data.get("withdrawal_amount", 0))  
            conversion_rate = float(withdrawal_data.get("conversion_rate", 1))  
            avg_withdrawal_frequency_14d = float(withdrawal_data.get("avg_withdrawal_frequency_14d", 0))
            withdrawals_24h = int(withdrawal_data.get("withdrawals_24h", 0))
            failed_withdrawals_24h = int(withdrawal_data.get("failed_withdrawals_24h", 0))
        except ValueError:
            logging.error("Invalid data types in withdrawal_data")
            results["withdrawal_anomalies"] = {"error": "Invalid data types in withdrawal_data"}
            return

        # Ensure values are non-negative
        if any(value < 0 for value in [current_wallet_balance, withdrawal_amount, avg_withdrawal_frequency_14d, failed_withdrawals_24h]):
            logging.warning("Negative values found in withdrawal_data")
            results["withdrawal_anomalies"] = {"error": "Negative values detected in withdrawal_data"}
            return

        # Convert balance from ether to the withdrawal currency
        current_balance_converted = current_wallet_balance * conversion_rate  

        # 1️⃣ Large Withdrawal Score (Scaled)
        large_withdrawal_score = (
            min(withdrawal_amount / (LARGE_WITHDRAWAL_THRESHOLD * current_balance_converted), 1.0) 
            if current_balance_converted > 0 else 0.0
        )

        # 2️⃣ Withdrawals Limit Score (Binary)
        withdrawals_limit_flag = int(withdrawals_24h >= MAX_DAILY_WITHDRAWALS)

        # 3️⃣ Money Laundering Score (Scaled)
        money_laundering_score = min(avg_withdrawal_frequency_14d / MAX_LAUNDERING_THRESHOLD, 1.0)

        # 4️⃣ Failed Withdrawals Score (Binary)
        failed_withdrawals_limit_flag = int(failed_withdrawals_24h >= MAX_DAILY_FAILED_WITHDRAWALS)

        # Store Results
        results["withdrawal_anomalies"] = {
            "large_withdrawal_score": round(large_withdrawal_score, 2),
            "money_laundering_score": round(money_laundering_score, 2),
            "withdrawals_limit_flag": withdrawals_limit_flag,
            "failed_withdrawals_limit_flag": failed_withdrawals_limit_flag
        }
    
    except Exception as e:
        logging.error(f"Error in detect_withdrawal_anomalies: {str(e)}", exc_info=True)
        results["withdrawal_anomalies"] = {"error": str(e)}
