from ML_component.fraud_detection_ml import detect_fraud_ml
from login_anomalies_component.login_anomaly_detection import detect_login_anomalies
from withdrawal_anomalies_component.withdrawal_anomaly_detection import detect_withdrawal_anomalies
from geospacial_clustering_component.detect_geospatial_clusters import detect_geospatial_clusters
from final_decision_component.make_final_decision import make_final_decision

def process_transaction(data):
    """Handles fraud detection processing for a transaction request."""

    # Initialize results dictionary
    results = {}

    # Run fraud detection models sequentially
    detect_fraud_ml(data, results)
    detect_login_anomalies(data, results)

    # Run withdrawal fraud detection only if the transaction is a withdrawal
    if data.get("transaction_type") == "withdrawal":
        detect_withdrawal_anomalies(data, results)

    detect_geospatial_clusters(data, results)

    make_final_decision(data, results)

    # Return results dictionary
    return results
