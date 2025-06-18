import time
import numpy as np

def compute_dorling(layer, neighbours_table, friction = 0.25, ratio = 0.4):

    start_time = time.time()

    centroid_table = create_centroid_table(layer)
    print(centroid_table)
    
    # for i in range (50):
    #     dorling_iterations(centroid_table, neighbours_table, friction, ratio)

    # change_centroids_positions(layer, centroid_table)

    end_time = time.time()
    print(f"[DorlingCartogram] Dorling iterations completed in {end_time - start_time:.2f} seconds")
    return

def create_centroid_table(layer, scaled_radius_field="radius_scaled"):
    """
    Create a numpy array representing centroids for Dorling iterations.

    Each row = [x, y, radius, x_vector, y_vector]
    Initial vectors are 0.

    Args:
        layer (QgsVectorLayer): The centroid layer (with scaled radius field).
        scaled_radius_field (str): Name of the field with scaled radius (default 'radius_scaled').

    Returns:
        np.ndarray: Array of shape (N, 5)
    """

    # Determine indices of fields
    radius_idx = layer.fields().indexFromName(scaled_radius_field)

    # Build list of features
    features = list(layer.getFeatures())
    n = len(features)

    # Create empty numpy array: [x, y, radius, x_vector, y_vector]
    centroid_table = np.zeros((n, 5), dtype=float)

    for i, feat in enumerate(features):
        geom = feat.geometry()
        if not geom:
            continue

        pt = geom.asPoint()
        radius = feat[radius_idx]

        centroid_table[i, 0] = pt.x()
        centroid_table[i, 1] = pt.y()
        centroid_table[i, 2] = radius
        centroid_table[i, 3] = 0.0  # x_vector
        centroid_table[i, 4] = 0.0  # y_vector

    return centroid_table

def dorling_iterations(layer, neighbours_table, friction = 0.25, ratio = 0.4):
    # apply dorling iterations based on Dorling's algorithm
    return

def change_centroids_positions(layer, centroid_table):
    # apply new positions to layer
    return