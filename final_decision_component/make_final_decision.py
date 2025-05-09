"""
final_decision.py - Final transaction blocking decision component
"""

import json
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Load config from JSON (same pattern as other components)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(CONFIG_PATH, "r") as file:
        CONFIG = json.load(file)
except Exception as e:
    logger.error(f"Failed to load config: {str(e)}")
    CONFIG = {
        "decision_parameters": {
            "score_thresholds": {
                "ml_fraud": 0.5,
                "unlikely_travel": 0.7,
                "excessive_logins": 0.6,
                "excessive_unique_logins": 0.5,
                "large_withdrawal": 0.4,
                "money_laundering": 0.1
            }
        }
    }

class DecisionMaker:
    """Core decision logic container"""
    
    def __init__(self):
        self.thresholds = CONFIG["decision_parameters"]["score_thresholds"]

    def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Main decision analysis logic"""
        decision = {
            "block_transaction": False,
            "block_reasons": {}
        }
        reasons = []

        try:
            # ML Fraud check
            ml_score = results.get("ML_fraud_score", 0)
            if ml_score >= self.thresholds["ml_fraud"]:
                reasons.append(f"High ML fraud risk (score: {ml_score:.2f})")

            # Geospatial analysis
            cluster_info = results.get("clusters_info", {})
            if cluster_info.get("this_transaction_is_in_cluster", False):
                cluster_num = cluster_info.get("transaction_cluster_number", "")
                cluster = cluster_info.get(f"{cluster_num}_info", {})
                if cluster.get("is_suspicious", False):
                    reasons.append(f"Suspicious cluster: {cluster.get('suspicious_reason', 'Unknown')}")

            # Login anomalies
            login = results.get("login_anomalies", {})
            if login.get("unlikely_travel_score", 0) >= self.thresholds["unlikely_travel"]:
                reasons.append(f"Unlikely travel (score: {login['unlikely_travel_score']:.2f})")
            
            if login.get("excessive_logins_from_same_device_score", 0) >= self.thresholds["excessive_logins"]:
                reasons.append(f"Excessive device logins (score: {login['excessive_logins_from_same_device_score']:.2f})")
                
            if login.get("excessive_unique_account_logins_from_same_device_score", 0) >= self.thresholds["excessive_unique_logins"]:
                reasons.append(f"Multiple account logins (score: {login['excessive_unique_account_logins_from_same_device_score']:.2f})")

            # Withdrawal patterns
            withdrawal = results.get("withdrawal_anomalies", {})
            if withdrawal.get("large_withdrawal_score", 0) >= self.thresholds["large_withdrawal"]:
                reasons.append(f"Large withdrawal (score: {withdrawal['large_withdrawal_score']:.2f})")
                
            if withdrawal.get("money_laundering_score", 0) >= self.thresholds["money_laundering"]:
                reasons.append(f"Money laundering risk (score: {withdrawal['money_laundering_score']:.2f})")
            
            # Withdrawal flags (non-threshold based)
            if withdrawal.get("failed_withdrawals_limit_flag", 0) >= 1:
                reasons.append("Excessive failed withdrawal attempts")
                
            if withdrawal.get("withdrawals_limit_flag", 0) >= 1:
                reasons.append("Withdrawal frequency limit exceeded")

            # Format final output
            if reasons:
                decision["block_transaction"] = True
                decision["block_reasons"] = {str(i+1): reason 
                                           for i, reason in enumerate(reasons[:5])}

        except Exception as e:
            logger.error(f"Decision analysis failed: {str(e)}")
            reasons.append("Decision system error")

        return decision

def make_final_decision(data: Dict, results: Dict) -> None:
    """Public interface matching other components' signature"""
    try:
        decision_maker = DecisionMaker()
        decision = decision_maker._analyze_results(results)
        results.update(decision)
    except Exception as e:
        logger.error(f"Final decision failed: {str(e)}")
        results.update({
            "block_transaction": False,
            "block_reasons": {"0": "Decision system error"}
        })