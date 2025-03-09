import datetime
from geopy.distance import geodesic

def detect_login_anomalies(data, results):
    """
    Detects login anomalies based on:
    1. Excessive logins from the same device (last 3 days).
    2. Excessive unique account logins from the same device (last 24 hours).
    3. Unlikely travel logins (based on travel speed between last user login and current login).

    Extracts required data from "login_data" in request JSON.
    Updates 'results' dict with calculated scores.
    """

    login_data = data.get("login_data", {})

    # Extract session details
    session = login_data.get("session", {})
    user_id = session.get("userId")
    device_id = session.get("deviceId")
    latitude = float(session.get("latitude", 0))
    longitude = float(session.get("longitude", 0))
    timestamp_str = session.get("timestamp")

    # Extract device history (last 3 days)
    device_history = login_data.get("device_history_last_3_days", [])

    # Extract last login session of the same user
    last_user_login = login_data.get("last_user_login", {})

    # Convert timestamps to datetime objects
    try:
        session_time = datetime.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        last_user_time = datetime.datetime.fromisoformat(last_user_login.get("timestamp", "").replace("Z", "+00:00"))
    except ValueError:
        results["login_anomalies"] = {"error": "Invalid timestamp format"}
        return

    # ---------------- 1. Excessive Logins from the Same Device (Last 3 Days) ----------------
    logins_from_device = sum(1 for entry in device_history if entry.get("deviceId") == device_id)
    excessive_logins_score = min(logins_from_device / 30.0, 1.0)  # Scale: 0 (0 logins) → 0.5 (15 logins) → 1 (30+ logins)

    # ---------------- 2. Excessive Unique Account Logins from Same Device (Last 24 Hours) ----------------
    unique_accounts_on_device = len(set(entry.get("userId") for entry in device_history if entry.get("deviceId") == device_id))
    excessive_unique_accounts_score = min(unique_accounts_on_device / 10.0, 1.0)  # Scale: 0 (1 user) → 0.5 (5 users) → 1 (10+ users)

    # ---------------- 3. Unlikely Travel Detection (Based on Travel Speed) ----------------
    last_latitude = float(last_user_login.get("latitude", 0))
    last_longitude = float(last_user_login.get("longitude", 0))

    # Calculate distance between current and last login locations (in km)
    distance_km = geodesic((latitude, longitude), (last_latitude, last_longitude)).km

    # Calculate time difference in hours
    time_difference_hours = abs((session_time - last_user_time).total_seconds()) / 3600

    travel_speed = 0.0  # Default
    if time_difference_hours > 0:  # Prevent division by zero
        travel_speed = distance_km / time_difference_hours  # km/h

    unlikely_travel_score = min(travel_speed / 1200.0, 1.0)  # Scale: 0 (0 km/h) → 0.5 (600 km/h) → 1 (1200+ km/h)

    # ---------------- Store Results ----------------
    results["login_anomalies"] = {
        "excessive_logins_from_same_device_score": round(excessive_logins_score, 2),
        "excessive_unique_account_logins_from_same_device_score": round(excessive_unique_accounts_score, 2),
        "unlikely_travel_score": round(unlikely_travel_score, 2)
    }
