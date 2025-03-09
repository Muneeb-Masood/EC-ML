from flask import Flask, request, jsonify
from controller import process_transaction
import logging

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@app.route('/detect_fraud', methods=['POST'])
def detect_fraud():
    try:
        # Ensure request contains JSON
        if not request.is_json:
            logging.warning("Received non-JSON request")
            return jsonify({"error": "Request must be in JSON format"}), 400
        
        data = request.get_json()

        # Validate required fields
        required_fields = ["transaction_type"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            logging.warning(f"Missing required fields: {missing_fields}")
            return jsonify({"error": f"Missing fields: {missing_fields}"}), 400

        # Special validation: If transaction type is "withdrawal", "withdrawal_data" must be present
        if data["transaction_type"] == "withdrawal" and "withdrawal_data" not in data:
            logging.warning("Withdrawal transaction missing 'withdrawal_data'")
            return jsonify({"error": "Missing 'withdrawal_data' for withdrawal transaction"}), 400

        # Log received request
        logging.info(f"Received fraud detection request: {data}")

        # Process transaction using the central controller
        response = process_transaction(data)

        # Return standardized response
        return jsonify({"status": "success", "fraud_analysis": response}), 200

    except Exception as e:
        logging.error(f"Internal Server Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
