
# Allowed transaction types
ALLOWED_TRANSACTION_TYPES = {"withdrawal", "transfer", "deposit"}

# Required fields for transaction validation
REQUIRED_TRANSACTION_FIELDS = {"transaction_id", "user_id", "transaction_type"}

# Required fields for transaction_data validation
REQUIRED_TRANSACTION_DATA_FIELDS = {
    "Avg min between sent tnx",
    "Avg min between received tnx",
    "Time Diff between first and last (Mins)",
    "Unique Received From Addresses",
    "min value received",
    "max value received",
    "avg val received",
    "min val sent",
    "avg val sent",
    "total transactions (including tnx to create contract)",
    "total ether received",
    "total ether balance",
}

# Required fields for login validation
REQUIRED_SESSION_FIELDS = {"userId", "deviceId", "timestamp", "latitude", "longitude"}
REQUIRED_LAST_USER_LOGIN_FIELDS = {"userId", "timestamp", "latitude", "longitude"}

# Required fields for withdrawal validation
REQUIRED_WITHDRAWAL_FIELDS = {
    "current_wallet_balance",
    "withdrawal_amount",
    "conversion_rate",
    "avg_withdrawal_frequency_14d",
    "withdrawals_24h",
    "failed_withdrawals_24h",
}


def validate_request(data):
    """Validates the incoming fraud detection request."""
    if not isinstance(data, dict):
        return {"error": "Request must be in JSON format", "reason": "Received non-JSON request"}, 400

    # Validate required top-level fields
    missing_fields = [field for field in REQUIRED_TRANSACTION_FIELDS if field not in data]
    if missing_fields:
        return {
            "error": f"Missing required fields: {missing_fields}",
            "reason": f"Missing fields at top level: {missing_fields}",
        }, 400

    transaction_type = data["transaction_type"]

    # Validate transaction type
    if transaction_type not in ALLOWED_TRANSACTION_TYPES:
        reason = f"Invalid 'transaction_type': {transaction_type}. Allowed: {list(ALLOWED_TRANSACTION_TYPES)}"
        return {"error": "Invalid 'transaction_type'", "reason": reason}, 400

    # Validate transaction_data
    transaction_data = data.get("transaction_data")
    if not transaction_data:
        return {
            "error": "Missing 'transaction_data'",
            "reason": "Transaction data is required for fraud analysis",
        }, 400

    missing_txn_fields = [field for field in REQUIRED_TRANSACTION_DATA_FIELDS if field not in transaction_data]
    if missing_txn_fields:
        reason = f"Missing fields in 'transaction_data': {missing_txn_fields}"
        return {"error": "Missing fields in 'transaction_data'", "reason": reason}, 400

    # Validate login data (mandatory for all transactions)
    login_validation_error = validate_login_data(data.get("login_data"))
    if login_validation_error:
        return login_validation_error

    # Validate withdrawal-specific data if transaction is a withdrawal
    if transaction_type == "withdrawal":
        withdrawal_validation_error = validate_withdrawal_data(data.get("withdrawal_data"))
        if withdrawal_validation_error:
            return withdrawal_validation_error

    return None  # No errors


def validate_login_data(login_data):
    """Validates login-related fraud detection fields (Required for all transactions)."""
    if not login_data:
        return {"error": "Missing 'login_data'", "reason": "Login data is required for all transactions"}, 400

    # Validate session fields
    session = login_data.get("session")
    if not session:
        return {"error": "Missing 'session' in 'login_data'", "reason": "Session data is required"}, 400

    missing_session_fields = [field for field in REQUIRED_SESSION_FIELDS if field not in session]
    if missing_session_fields:
        reason = f"Missing fields in 'session': {missing_session_fields}"
        return {"error": "Missing fields in 'session'", "reason": reason}, 400

    # Validate last user login fields
    last_user_login = login_data.get("last_user_login")
    if not last_user_login:
        return {"error": "Missing 'last_user_login' in 'login_data'", "reason": "Last user login data is required"}, 400

    missing_last_login_fields = [field for field in REQUIRED_LAST_USER_LOGIN_FIELDS if field not in last_user_login]
    if missing_last_login_fields:
        reason = f"Missing fields in 'last_user_login': {missing_last_login_fields}"
        return {"error": "Missing fields in 'last_user_login'", "reason": reason}, 400

    # Validate device history format
    device_history = login_data.get("device_history_last_3_days", [])
    if not isinstance(device_history, list):
        reason = "'device_history_last_3_days' must be a list"
        return {"error": "'device_history_last_3_days' must be a list", "reason": reason}, 400

    # Ensure latitude & longitude are valid numbers
    try:
        float(session["latitude"])
        float(session["longitude"])
        float(last_user_login["latitude"])
        float(last_user_login["longitude"])
    except ValueError:
        reason = "Invalid latitude or longitude format in 'session' or 'last_user_login'"
        return {"error": "Invalid latitude or longitude", "reason": reason}, 400

    return None  # No errors


def validate_withdrawal_data(withdrawal_data):
    """Validates withdrawal-specific fraud detection fields."""
    if not withdrawal_data:
        return {
            "error": "Missing 'withdrawal_data' for withdrawal transaction",
            "reason": "Withdrawal data is required for withdrawals",
        }, 400

    missing_withdrawal_fields = [field for field in REQUIRED_WITHDRAWAL_FIELDS if field not in withdrawal_data]
    if missing_withdrawal_fields:
        reason = f"Missing fields in 'withdrawal_data': {missing_withdrawal_fields}"
        return {"error": "Missing fields in 'withdrawal_data'", "reason": reason}, 400

    return None  # No errors
