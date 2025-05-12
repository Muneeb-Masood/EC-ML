# """
# geospatial_clustering.py - Fraud detection through geographical transaction clustering
# """

# # Standard library imports
# import json
# import os
# import logging

# # Third-party imports
# import numpy as np
# from sklearn.cluster import DBSCAN
# from geopy.distance import geodesic

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Load configuration
# CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
# with open(CONFIG_PATH) as f:
#     CLUSTER_CONFIG = json.load(f)["geospatial_clustering"]

# class GeospatialClusterAnalyzer:
#     """
#     Analyzes geographical transaction clusters using DBSCAN algorithm
#     with configurable parameters from config.json
#     """
    
#     def __init__(self):
#         algo_params = CLUSTER_CONFIG["algorithm_parameters"]
#         self.eps_km = algo_params["eps_km"]
#         self.min_samples = algo_params["min_samples"]
#         self.buffer_percentage = algo_params["buffer_percentage"]
#         self.earth_radius_km = 6371

#         output_settings = CLUSTER_CONFIG["output_settings"]
#         self.coord_precision = output_settings["coordinate_precision"]
#         self.radius_precision = output_settings["radius_precision"]
#         self.density_precision = output_settings["density_precision"]

#         validation_params = CLUSTER_CONFIG["validation"]
#         self.abs_density_threshold = validation_params["absolute_density_threshold"]
#         self.rel_density_multiplier = validation_params["relative_density_multiplier"]

#     def _calculate_cluster_metrics(self, cluster_points):
#         if not cluster_points:
#             return None

#         try:
#             points = np.array(cluster_points)
#             centroid = points.mean(axis=0).tolist()
            
#             max_distance = max(
#                 geodesic(centroid, point).km 
#                 for point in cluster_points
#             )

#             area = np.pi * (max_distance ** 2)
#             density = len(cluster_points) / (area or 0.1)

#             return {
#                 "latitude_center": round(centroid[0], self.coord_precision),
#                 "longitude_center": round(centroid[1], self.coord_precision),
#                 "radius_km": round(max_distance, self.radius_precision),
#                 "density_per_km2": round(density, self.density_precision),
#                 "transaction_count": len(cluster_points)
#             }
#         except Exception as e:
#             logger.error(f"Cluster metric calculation failed: {str(e)}")
#             return None

#     def analyze_transaction_clusters(self, all_transactions, current_transaction):
#         try:
#             coords = np.radians(all_transactions)
#             eps_rad = self.eps_km / self.earth_radius_km
            
#             db = DBSCAN(
#                 eps=eps_rad,
#                 min_samples=self.min_samples,
#                 metric='haversine',
#                 algorithm='ball_tree'
#             ).fit(coords)

#             clusters = []
#             cluster_map = {}

#             for label in set(db.labels_):
#                 if label == -1:
#                     continue

#                 cluster_mask = db.labels_ == label
#                 cluster_points = [all_transactions[i] for i in np.where(cluster_mask)[0]]
                
#                 if cluster_info := self._calculate_cluster_metrics(cluster_points):
#                     cluster_info['label'] = int(label)
#                     clusters.append(cluster_info)
#                     cluster_map[label] = cluster_info

#             # Calculate baseline density from non-outlier clusters
#             valid_clusters = [c for c in clusters 
#                              if c["density_per_km2"] < self.abs_density_threshold]
#             baseline_density = float(np.median(
#                 [c["density_per_km2"] for c in valid_clusters]
#             )) if valid_clusters else 0.0

#             # Add fraud flags with native Python booleans
#             for cluster in clusters:
#                 absolute = cluster["density_per_km2"] > self.abs_density_threshold
#                 relative = cluster["density_per_km2"] > (baseline_density * self.rel_density_multiplier)
                
#                 cluster["is_suspicious"] = bool(absolute or relative)  # Convert to native bool
#                 cluster["suspicious_reason"] = (
#                     f"Absolute threshold exceeded ({self.abs_density_threshold})" if absolute else
#                     f"Relative threshold ({self.rel_density_multiplier}x baseline)" if relative else "Normal"
#                 )

#             # Find current transaction's cluster
#             current_in_cluster = False
#             current_cluster_info = None
#             current_label = db.labels_[-1]

#             if current_label != -1 and current_label in cluster_map:
#                 cluster = cluster_map[current_label]
#                 centroid = (cluster["latitude_center"], cluster["longitude_center"])
#                 distance = geodesic(centroid, current_transaction).km
#                 buffer_radius = cluster["radius_km"] * (1 + self.buffer_percentage)
                
#                 if distance <= buffer_radius:
#                     current_in_cluster = True
#                     current_cluster_info = {
#                         "cluster_number": f"cluster{clusters.index(cluster) + 1}",
#                         "density": float(cluster["density_per_km2"]),
#                         "distance_km": round(distance, self.radius_precision)
#                     }

#             # Build result with explicit type conversions
#             result = {
#                 "clusters_identified": int(len(clusters)),
#                 "this_transaction_is_in_cluster": bool(current_in_cluster),  # Convert to native bool
#                 "baseline_density": float(baseline_density)
#             }

#             for i, cluster in enumerate(clusters, 1):
#                 result[f"cluster{i}_info"] = {
#                     key: (float(value) if isinstance(value, (float, np.floating)) else
#                           bool(value) if isinstance(value, (bool, np.bool_)) else  # Handle numpy bools
#                           value)
#                     for key, value in cluster.items()
#                 }

#             if current_in_cluster and current_cluster_info:
#                 result.update({
#                     "transaction_cluster_number": str(current_cluster_info["cluster_number"]),
#                     "transaction_cluster_density": float(current_cluster_info["density"]),
#                     "distance_from_cluster_center_km": float(current_cluster_info["distance_km"])
#                 })

#             return result

#         except Exception as e:
#             logger.error(f"Clustering failed: {str(e)}", exc_info=True)
#             return {"clustering_error": str(e)}

# def detect_geospatial_clusters(data, results):
#     try:
#         geo_data = data.get("geospacial_transaction_data_2d", [])
#         session = data["login_data"]["session"]
#         current_lat = float(session["latitude"])
#         current_lon = float(session["longitude"])
        
#         all_transactions = []
#         for point in geo_data:
#             try:
#                 lat = float(point["latitude"])
#                 lon = float(point["longitude"])
#                 all_transactions.append((lat, lon))
#             except (KeyError, ValueError) as e:
#                 logger.warning(f"Invalid coordinate: {point} - {str(e)}")
        
#         all_transactions.append((current_lat, current_lon))
        
#         analyzer = GeospatialClusterAnalyzer()
#         cluster_info = analyzer.analyze_transaction_clusters(
#             all_transactions, 
#             (current_lat, current_lon)
#         )
        
#         # Ensure all values are JSON serializable
#         results["clusters_info"] = json.loads(json.dumps(cluster_info, default=str))

#     except KeyError as e:
#         logger.warning(f"Missing required field: {str(e)}")
#         results["clusters_info"] = {"error": f"Missing field: {str(e)}"}
#     except Exception as e:
#         logger.error(f"Geospatial processing failed: {str(e)}")
#         results["clusters_info"] = {"error": str(e)}





































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
            
            max_distance = 0.0
            if len(cluster_points) > 1: # Geodesic needs at least one point, centroid itself if 1 point
                max_distance = max(
                    geodesic(centroid, point).km 
                    for point in cluster_points
                )
            elif len(cluster_points) == 1: # If cluster has only one point, radius is 0
                 max_distance = 0.0


            area = np.pi * (max_distance ** 2)
            # Handle area being zero (e.g. single point cluster or all points identical)
            # to prevent division by zero. A very small area can represent high density.
            density = len(cluster_points) / (area if area > 0 else 0.0001) # Use a tiny area if zero

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

            # Determine the starting label for hardcoded clusters to ensure uniqueness
            max_dbscan_label = -1
            if len(db.labels_) > 0 and np.any(db.labels_ != -1):
                max_dbscan_label = int(np.max(db.labels_[db.labels_ != -1]))
            
            current_max_label = max_dbscan_label

            for label in set(db.labels_):
                if label == -1:
                    continue

                cluster_mask = db.labels_ == label
                cluster_points_indices = np.where(cluster_mask)[0]
                # Ensure we don't try to form a cluster from current_transaction if it's the only point
                # and DBSCAN behavior might be unexpected with min_samples=1.
                # However, DBSCAN's min_samples handles this.
                
                cluster_points_list = [all_transactions[i] for i in cluster_points_indices]
                
                if cluster_info := self._calculate_cluster_metrics(cluster_points_list):
                    cluster_info['label'] = int(label)
                    clusters.append(cluster_info)
                    cluster_map[label] = cluster_info

            # Calculate baseline density from non-outlier DBSCAN-detected clusters
            valid_dbscan_clusters = [c for c in clusters 
                                     if c["density_per_km2"] < self.abs_density_threshold]
            baseline_density = float(np.median(
                [c["density_per_km2"] for c in valid_dbscan_clusters]
            )) if valid_dbscan_clusters else 0.0

            # Add fraud flags to DBSCAN-detected clusters
            for cluster in clusters: # This loop is for DBSCAN clusters only at this point
                absolute = cluster["density_per_km2"] > self.abs_density_threshold
                relative = cluster["density_per_km2"] > (baseline_density * self.rel_density_multiplier)
                
                cluster["is_suspicious"] = bool(absolute or relative)
                cluster["suspicious_reason"] = (
                    f"Absolute threshold exceeded ({self.abs_density_threshold})" if absolute else
                    f"Relative threshold ({self.rel_density_multiplier}x baseline)" if relative else "Normal"
                )

            # --- START OF HARDCODED CLUSTER INJECTION ---
            hardcoded_clusters_definitions = [
                { # Karachi - Normal density
                    "latitude_center": 24.8607, "longitude_center": 67.0011,
                    "radius_km": 1.0, "transaction_count": 10 
                },
                { # Lahore - Relatively high density
                    "latitude_center": 31.5204, "longitude_center": 74.3587,
                    "radius_km": 0.5, "transaction_count": 50 
                },
                { # Islamabad - Absolutely high density
                    "latitude_center": 33.6844, "longitude_center": 73.0479,
                    "radius_km": 0.2, "transaction_count": 30 
                }
            ]

            for hc_def in hardcoded_clusters_definitions:
                current_max_label += 1 # Assign a new unique label
                
                hc_area = np.pi * (hc_def["radius_km"] ** 2)
                # Use a tiny area if radius is 0 to avoid division by zero and represent high density
                hc_density = hc_def["transaction_count"] / (hc_area if hc_area > 0 else 0.0001)

                # Determine if suspicious using the baseline_density from DBSCAN clusters
                hc_abs_suspicious = hc_density > self.abs_density_threshold
                # Relative check: only if baseline_density is positive, otherwise any positive density is "infinitely" larger
                hc_rel_suspicious = hc_density > (baseline_density * self.rel_density_multiplier)
                
                hc_is_suspicious = bool(hc_abs_suspicious or hc_rel_suspicious)
                hc_suspicious_reason = "Normal"
                if hc_abs_suspicious:
                    hc_suspicious_reason = f"Absolute threshold exceeded ({self.abs_density_threshold})"
                elif hc_rel_suspicious: # Check this only if not absolute, to give priority to absolute
                    hc_suspicious_reason = f"Relative threshold ({self.rel_density_multiplier}x baseline)"

                hardcoded_cluster = {
                    "latitude_center": round(hc_def["latitude_center"], self.coord_precision),
                    "longitude_center": round(hc_def["longitude_center"], self.coord_precision),
                    "radius_km": round(hc_def["radius_km"], self.radius_precision),
                    "density_per_km2": round(hc_density, self.density_precision),
                    "transaction_count": hc_def["transaction_count"],
                    "label": current_max_label, # Unique label for this hardcoded cluster
                    "is_suspicious": hc_is_suspicious,
                    "suspicious_reason": hc_suspicious_reason
                }
                clusters.append(hardcoded_cluster)
            # --- END OF HARDCODED CLUSTER INJECTION ---


            # Find current transaction's cluster (only considers DBSCAN clusters)
            current_in_cluster = False
            current_cluster_info = None
            # Ensure all_transactions is not empty before trying to access its last element's label
            if all_transactions: # Should always be true as current_transaction is appended
                current_label_index = len(all_transactions) - 1
                if current_label_index < len(db.labels_): # Check if current_transaction was part of fit
                    current_label = db.labels_[current_label_index]

                    if current_label != -1 and current_label in cluster_map:
                        # current_transaction is part of a DBSCAN cluster
                        cluster = cluster_map[current_label] 
                        centroid = (cluster["latitude_center"], cluster["longitude_center"])
                        distance = geodesic(centroid, current_transaction).km
                        buffer_radius = cluster["radius_km"] * (1 + self.buffer_percentage)
                        
                        if distance <= buffer_radius:
                            current_in_cluster = True
                            # Find the index of this cluster in the 'clusters' list for user-friendly numbering
                            # This needs care if clusters list was reordered or hardcoded clusters are mixed in before this point.
                            # Since hardcoded clusters are appended, indices of DBSCAN clusters remain stable if we search early.
                            # However, it's safer to find the index in the *final* clusters list.
                            try:
                                cluster_index_in_final_list = clusters.index(cluster) + 1
                            except ValueError: # Should not happen if cluster is from cluster_map and clusters list
                                cluster_index_in_final_list = "N/A"


                            current_cluster_info = {
                                "cluster_number": f"cluster{cluster_index_in_final_list}",
                                "density": float(cluster["density_per_km2"]),
                                "distance_km": round(distance, self.radius_precision)
                            }
            
            # Build result with explicit type conversions
            result = {
                "clusters_identified": int(len(clusters)), # Now includes hardcoded clusters
                "this_transaction_is_in_cluster": bool(current_in_cluster),
                "baseline_density": float(baseline_density)
            }

            for i, cluster_data in enumerate(clusters, 1): # Iterates over all clusters (DBSCAN + hardcoded)
                result[f"cluster{i}_info"] = {
                    key: (float(value) if isinstance(value, (float, np.floating)) else
                          bool(value) if isinstance(value, (bool, np.bool_)) else
                          int(value) if isinstance(value, (int, np.integer)) else # Ensure int for count and label
                          value)
                    for key, value in cluster_data.items()
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
        # Add historical transactions
        for point in geo_data:
            try:
                lat = float(point["latitude"])
                lon = float(point["longitude"])
                all_transactions.append((lat, lon))
            except (KeyError, ValueError, TypeError) as e: # Added TypeError for point being non-subscriptable
                logger.warning(f"Invalid historical coordinate data: {point} - {str(e)}")
        
        # Add current transaction. It must be added for DBSCAN to potentially label it.
        all_transactions.append((current_lat, current_lon))
        
        if not all_transactions: # Should not happen due to current_transaction
            logger.warning("No transaction data to analyze.")
            results["clusters_info"] = {"error": "No transaction data."}
            return

        analyzer = GeospatialClusterAnalyzer()
        cluster_info = analyzer.analyze_transaction_clusters(
            all_transactions, 
            (current_lat, current_lon) # Pass current transaction coords for distance calculations etc.
        )
        
        # Ensure all values are JSON serializable using a robust method
        # The explicit conversions in analyze_transaction_clusters should mostly handle this
        # but json.dumps with default=str is a final safeguard.
        results["clusters_info"] = json.loads(json.dumps(cluster_info, default=str))

    except KeyError as e:
        logger.warning(f"Missing required field in input data: {str(e)}")
        results["clusters_info"] = {"error": f"Missing field: {str(e)}"}
    except (ValueError, TypeError) as e: # Catch errors from float conversion if session data is bad
        logger.warning(f"Invalid current transaction coordinate data: {str(e)}")
        results["clusters_info"] = {"error": f"Invalid current transaction coordinates: {str(e)}"}
    except Exception as e:
        logger.error(f"Geospatial processing failed: {str(e)}", exc_info=True)
        results["clusters_info"] = {"error": f"Geospatial processing error: {str(e)}"}