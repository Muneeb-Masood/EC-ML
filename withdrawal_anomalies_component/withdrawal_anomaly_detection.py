
def detect_withdrawal_anomalies(data, results):
    """
    Detects anomalies in withdrawal transactions based on predefined rules:
    1. Large withdrawal amount compared to the current wallet balance.
    2. Excessive withdrawals in the last 24 hours.
    3. High withdrawal frequency over the last 14 days (possible money laundering).
    4. Unusual number of failed withdrawal attempts in the last 24 hours.

    Extracts required data from "withdrawal_data" in request JSON.
    Updates 'results' dict with calculated anomaly scores.
    """

    # Extract withdrawal-related data
    withdrawal_data = data.get("withdrawal_data", {})

    if not withdrawal_data:
        results["withdrawal_anomalies"] = {}  # Return empty response if no withdrawal data
        return

    # Extract individual fields
    current_wallet_balance = float(withdrawal_data["current_wallet_balance"])  # Balance in Ether
    withdrawal_amount = float(withdrawal_data["withdrawal_amount"])  # Withdrawal amount in USD
    conversion_rate = float(withdrawal_data["conversion_rate"])  # USD per 1 Ether
    avg_withdrawal_frequency_14d = float(withdrawal_data["avg_withdrawal_frequency_14d"])
    withdrawals_24h = int(withdrawal_data["withdrawals_24h"])
    failed_withdrawals_24h = int(withdrawal_data["failed_withdrawals_24h"])

    # Convert wallet balance to USD
    current_balance_usd = current_wallet_balance * conversion_rate  

    # ---------------- 1. Large Withdrawal Score (Scaled) ----------------
    # Scale: 0 (0% of balance) → 0.5 (25% of balance) → 1 (50%+ of balance)
    large_withdrawal_score = (
        min(withdrawal_amount / (0.5 * current_balance_usd), 1.0) if current_balance_usd > 0 else 0.0
    )

    # ---------------- 2. Withdrawals Limit Score (Binary) ----------------
    # Score = 1 if 15+ withdrawals in last 24 hours, otherwise 0
    withdrawals_limit_score = int(withdrawals_24h >= 15)

    # ---------------- 3. Money Laundering Score (Scaled) ----------------
    # Scale: 0 (0 withdrawals/day) → 0.5 (3 withdrawals/day) → 1 (6+ withdrawals/day)
    money_laundering_score = min(avg_withdrawal_frequency_14d / 6.0, 1.0)

    # ---------------- 4. Failed Withdrawals Score (Scaled) ----------------
    # Scale: 0 (0 failures) → 0.5 (5 failures) → 1 (10+ failures)
    failed_withdrawals_score = min(failed_withdrawals_24h / 10.0, 1.0)

    # ---------------- Store Results ----------------
    results["withdrawal_anomalies"] = {
        "large_withdrawal_score": round(large_withdrawal_score, 2),
        "withdrawals_limit_score": withdrawals_limit_score,
        "money_laundering_score": round(money_laundering_score, 2),
        "failed_withdrawals_score": round(failed_withdrawals_score, 2)
    }
