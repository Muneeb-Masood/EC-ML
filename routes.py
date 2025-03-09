# app.py (Flask App Entry Point)
from flask import Flask, request, jsonify
from loginAnomalies.controller import detect_login_anomalies

app = Flask(__name__)

@app.route("/", methods=["GET"])
def detect_anomalies():
    data = request.get_json()
    response = detect_login_anomalies(data)
    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)
