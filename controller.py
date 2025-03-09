import multiprocessing
from ML_component.fraud_detection_ml import detect_fraud_ml
from login_anomalies_component.login_anomaly_detection import detect_login_anomalies
from withdrawl_anomalies_component.withdrawl_anomaly_detection import detect_withdrawal_anomalies

def process_transaction(data):
    """Handles parallel fraud detection processing for a transaction request."""

    # Create a dictionary to store results
    results = multiprocessing.Manager().dict()

    # Define fraud detection processes
    processes = [
        multiprocessing.Process(target=detect_fraud_ml, args=(data, results)),
        multiprocessing.Process(target=detect_login_anomalies, args=(data, results))
    ]

    # Add withdrawal fraud detection if the transaction type is 'withdrawal'
    if data.get("transaction_type") == "withdrawal":
        processes.append(multiprocessing.Process(target=detect_withdrawal_anomalies, args=(data, results)))

    # Start all processes
    for process in processes:
        process.start()

    # Wait for all processes to finish
    for process in processes:
        process.join()

    # Return aggregated results
    return dict(results)
