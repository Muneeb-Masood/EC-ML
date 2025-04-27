"""
geospatial_clustering.py - Fraud detection through geographical transaction clustering
"""

# Standard library imports
import json
import os
import logging

# Third-party imports
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import geodesic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(CONFIG_PATH) as f:
    CLUSTER_CONFIG = json.load(f)["geospatial_clustering"]

class GeospatialClusterAnalyzer:
    """
    Analyzes geographical transaction clusters using DBSCAN algorithm
    with configurable parameters from config.json
    """
    
    def __init__(self):
        algo_params = CLUSTER_CONFIG["algorithm_parameters"]
        self.eps_km = algo_params["eps_km"]
        self.min_samples = algo_params["min_samples"]
        self.buffer_percentage = algo_params["buffer_percentage"]
        self.earth_radius_km = 6371

        output_settings = CLUSTER_CONFIG["output_settings"]
        self.coord_precision = output_settings["coordinate_precision"]
        self.radius_precision = output_settings["radius_precision"]
        self.density_precision = output_settings["density_precision"]

        validation_params = CLUSTER_CONFIG["validation"]
        self.abs_density_threshold = validation_params["absolute_density_threshold"]
        self.rel_density_multiplier = validation_params["relative_density_multiplier"]

    def _calculate_cluster_metrics(self, cluster_points):
        if not cluster_points:
            return None

        try:
            points = np.array(cluster_points)
            centroid = points.mean(axis=0).tolist()
            
            max_distance = max(
                geodesic(centroid, point).km 
                for point in cluster_points
            )
            
            area = np.pi * (max_distance ** 2)
            density = len(cluster_points) / (area or 0.1)

            return {
                "latitude_center": round(centroid[0], self.coord_precision),
                "longitude_center": round(centroid[1], self.coord_precision),
                "radius_km": round(max_distance, self.radius_precision),
                "density_per_km2": round(density, self.density_precision),
                "transaction_count": len(cluster_points)
            }
        except Exception as e:
            logger.error(f"Cluster metric calculation failed: {str(e)}")
            return None

    def analyze_transaction_clusters(self, all_transactions, current_transaction):
        try:
            coords = np.radians(all_transactions)
            eps_rad = self.eps_km / self.earth_radius_km
            
            db = DBSCAN(
                eps=eps_rad,
                min_samples=self.min_samples,
                metric='haversine',
                algorithm='ball_tree'
            ).fit(coords)

            clusters = []
            cluster_map = {}

            for label in set(db.labels_):
                if label == -1:
                    continue

                cluster_mask = db.labels_ == label
                cluster_points = [all_transactions[i] for i in np.where(cluster_mask)[0]]
                
                if cluster_info := self._calculate_cluster_metrics(cluster_points):
                    cluster_info['label'] = int(label)
                    clusters.append(cluster_info)
                    cluster_map[label] = cluster_info

            # Calculate baseline density from non-outlier clusters
            valid_clusters = [c for c in clusters 
                             if c["density_per_km2"] < self.abs_density_threshold]
            baseline_density = float(np.median(
                [c["density_per_km2"] for c in valid_clusters]
            )) if valid_clusters else 0.0

            # Add fraud flags with native Python booleans
            for cluster in clusters:
                absolute = cluster["density_per_km2"] > self.abs_density_threshold
                relative = cluster["density_per_km2"] > (baseline_density * self.rel_density_multiplier)
                
                cluster["is_suspicious"] = bool(absolute or relative)  # Convert to native bool
                cluster["suspicious_reason"] = (
                    f"Absolute threshold exceeded ({self.abs_density_threshold})" if absolute else
                    f"Relative threshold ({self.rel_density_multiplier}x baseline)" if relative else "Normal"
                )

            # Find current transaction's cluster
            current_in_cluster = False
            current_cluster_info = None
            current_label = db.labels_[-1]

            if current_label != -1 and current_label in cluster_map:
                cluster = cluster_map[current_label]
                centroid = (cluster["latitude_center"], cluster["longitude_center"])
                distance = geodesic(centroid, current_transaction).km
                buffer_radius = cluster["radius_km"] * (1 + self.buffer_percentage)
                
                if distance <= buffer_radius:
                    current_in_cluster = True
                    current_cluster_info = {
                        "cluster_number": f"cluster{clusters.index(cluster) + 1}",
                        "density": float(cluster["density_per_km2"]),
                        "distance_km": round(distance, self.radius_precision)
                    }

            # Build result with explicit type conversions
            result = {
                "clusters_identified": int(len(clusters)),
                "this_transaction_is_in_cluster": bool(current_in_cluster),  # Convert to native bool
                "baseline_density": float(baseline_density)
            }

            for i, cluster in enumerate(clusters, 1):
                result[f"cluster{i}_info"] = {
                    key: (float(value) if isinstance(value, (float, np.floating)) else
                          bool(value) if isinstance(value, (bool, np.bool_)) else  # Handle numpy bools
                          value)
                    for key, value in cluster.items()
                }

            if current_in_cluster and current_cluster_info:
                result.update({
                    "transaction_cluster_number": str(current_cluster_info["cluster_number"]),
                    "transaction_cluster_density": float(current_cluster_info["density"]),
                    "distance_from_cluster_center_km": float(current_cluster_info["distance_km"])
                })

            return result

        except Exception as e:
            logger.error(f"Clustering failed: {str(e)}", exc_info=True)
            return {"clustering_error": str(e)}

def detect_geospatial_clusters(data, results):
    try:
        geo_data = data.get("geospacial_transaction_data_2d", [])
        session = data["login_data"]["session"]
        current_lat = float(session["latitude"])
        current_lon = float(session["longitude"])
        
        all_transactions = []
        for point in geo_data:
            try:
                lat = float(point["latitude"])
                lon = float(point["longitude"])
                all_transactions.append((lat, lon))
            except (KeyError, ValueError) as e:
                logger.warning(f"Invalid coordinate: {point} - {str(e)}")
        
        all_transactions.append((current_lat, current_lon))
        
        analyzer = GeospatialClusterAnalyzer()
        cluster_info = analyzer.analyze_transaction_clusters(
            all_transactions, 
            (current_lat, current_lon)
        )
        
        # Ensure all values are JSON serializable
        results["clusters_info"] = json.loads(json.dumps(cluster_info, default=str))

    except KeyError as e:
        logger.warning(f"Missing required field: {str(e)}")
        results["clusters_info"] = {"error": f"Missing field: {str(e)}"}
    except Exception as e:
        logger.error(f"Geospatial processing failed: {str(e)}")
        results["clusters_info"] = {"error": str(e)}