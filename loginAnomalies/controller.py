from datetime import datetime

def detect_login_anomalies(data):
    device_history = data.get("device_history", [])  # Already filtered: last week's device history
    user_history = data.get("user_history", [])  # Full login history of the user
    session = data.get("session", [{}])[0]  # Ensure we get a dictionary, avoiding errors

    if not session or "timestamp" not in session:
        return {"error": "Invalid session data"}

    current_time = datetime.strptime(session["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
    
    # Use device_history as-is (last week's logins)
    recent_device_logins = device_history
    
    # 1. Multiple Different Users Logging in from the Same Device Score
    unique_users = len({entry["user_id"] for entry in recent_device_logins})
    if unique_users <= 8:
        multiple_users_score = unique_users / 16  # Scale so 8 users = 0.5
    else:
        multiple_users_score = min(0.5 + ((unique_users - 8) / 16) * 0.5, 1)  # Scale so 16 users = 0.8, max 1
    
    # 2. Excessive Login Frequency from the Same Device Score
    login_count = len(recent_device_logins)
    excessive_login_frequency_score = min(login_count / 20, 1)  # Normalize score (max 1)
    
    # 3. Impossible User Login Score (Based on travel speed)
    user_login_times = sorted(user_history, key=lambda x: x["timestamp"], reverse=True)
    
    if len(user_login_times) > 1:
        last_login = user_login_times[1]  # Previous session of the user
        last_time = datetime.strptime(last_login["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
        time_diff = (current_time - last_time).total_seconds() / 3600  # Convert to hours
        
        last_location = (last_login["latitude"], last_login["longitude"])
        current_location = (session["latitude"], session["longitude"])
        
        distance = haversine_distance(last_location, current_location)  # Use Haversine formula
        speed = distance / time_diff if time_diff > 0 else float("inf")
        impossible_user_login_score = min(speed / 1600, 1)  # Normalize score (max 1 at 1600 km/h)
    else:
        impossible_user_login_score = 0

    return {
        "multiple_users_score": multiple_users_score,
        "excessive_login_frequency_score": excessive_login_frequency_score,
        "impossible_user_login_score": impossible_user_login_score
    }

def haversine_distance(coord1, coord2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371  # Earth radius in km
    lat1, lon1 = map(radians, coord1)
    lat2, lon2 = map(radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c  # Distance in km
