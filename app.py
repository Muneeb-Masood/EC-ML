from flask import Flask, request, jsonify
from controller import process_transaction
from validation_logic import validate_request
import logging

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@app.route('/detect_fraud', methods=['POST'])
def detect_fraud():
    try:
        # Ensure request header contains Content-Type: application/json
        if request.content_type != "application/json":
            reason = "Missing or incorrect 'Content-Type' header. Expected 'application/json'."
            logging.warning(reason)
            return jsonify({"error": "Invalid Content-Type", "reason": reason}), 400

        # Ensure request contains JSON body
        data = request.get_json()
        if not data:
            reason = "Received non-JSON request or empty body"
            logging.warning(reason)
            return jsonify({"error": "Request must be in JSON format", "reason": reason}), 400

        # Validate request using external validation function
        validation_error = validate_request(data)
        if validation_error:
            logging.warning(validation_error[0]["reason"])
            return jsonify(validation_error[0]), validation_error[1]

        # Log received request
        logging.info(f"Received fraud detection request")

        # Process transaction using the central controller
        response = process_transaction(data)

        # Return standardized response
        return jsonify(response), 200

    except Exception as e:
        reason = f"Unexpected error: {str(e)}"
        logging.error(reason, exc_info=True)
        return jsonify({"error": "Internal Server Error", "reason": reason}), 500


if __name__ == '__main__':
    app.run(debug=True)
