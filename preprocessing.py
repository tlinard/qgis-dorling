import math
import time
from math import hypot
from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsSpatialIndex, QgsGeometry, QgsPointXY
)

def preprocessing(input_layer, field_name):
    """
    Full preprocessing pipeline: compute centroids and neighbours.

    Args:
        input_layer (QgsVectorLayer): Input polygon layer (regions to be converted into circles).
        field_name (str): Field name used to compute the raw radius of each region (e.g. population, area, etc.).

    Returns:
        centroid_dict (dict): 
            Dictionary storing geometry and radius information for each region.
            Format: 
                { fid: { 
                    'x': x, 
                    'y': y, 
                    'perimeter': perimeter, 
                    'radius_raw': r_raw, 
                    'radius_scaled': r_scaled, 
                    'xvec': xvec, 
                    'yvec': yvec 
                } }

        eighbours_dict (dict): 
            Dictionary of neighboring region pairs with shared border lengths.
            Format: 
                { region_id: { neighbour_id: shared_border_length, ... }, ... }
    """

    # Start the timer to measure execution time
    start_time = time.time()

    # Build the neighbours dictionary
    neighbours_dict = create_neighbours_dict(input_layer)

    # Create the centroid dictionary
    centroid_dict = create_centroid_dict(input_layer, field_name, neighbours_dict)

    # End the timer and display the execution time
    end_time = time.time()
    print(f"[DorlingCartogram] Preprocessing completed in {end_time - start_time:.2f} seconds")

    return centroid_dict, neighbours_dict

def create_neighbours_dict(layer):
    """
    Build a dictionary of neighbouring polygon pairs:
    {
        region_id: { neighbour_id: shared_border_length, ... },
        ...
    }

    Args:
        layer (QgsVectorLayer): A polygon vector layer.

    Returns:
        dict: Neighbour relationship dictionary where each region ID maps
              to a dictionary of adjacent region IDs and their shared border lengths.
    """

    # Build spatial index for polygon geometries
    index = QgsSpatialIndex()
    feature_dict = {} # Dictionary to store features

    # Add each feature to the spatial index
    for feat in layer.getFeatures():
        index.insertFeature(feat)
        feature_dict[feat.id()] = feat

    neighbours_dict = {} # Dictionary to store neighbor relationships
    seen_pairs = set() # Set to keep track of seen pairs

    # --- Loop through each polygon ---
    for id1, feat1 in feature_dict.items():

        # Get the geometry of the current polygon
        geom1 = feat1.geometry()

        # Use bounding box intersection to get nearby candidate polygons
        candidate_ids = index.intersects(geom1.boundingBox())

        # Initialize dictionary entry if not present
        if id1 not in neighbours_dict:
            neighbours_dict[id1] = {}

        # --- Loop and check each candidate to see if it's a true neighbor ---
        for id2 in candidate_ids:
            if id2 == id1:
                continue # Skip self

            pair = tuple(sorted((id1, id2))) # Sort to make pairs unique
            if pair in seen_pairs:
                continue  # Skip already processed pairs
            seen_pairs.add(pair)

            # Get the geometry of the candidate polygon
            feat2 = feature_dict[id2]
            geom2 = feat2.geometry()

            # Check if polygons touch
            if geom1.touches(geom2):
                 # Compute the length of the shared border
                shared_border_length = geom1.intersection(geom2).length()

                # Add neighbor relationship in both directions
                neighbours_dict[id1][id2] = shared_border_length
                if id2 not in neighbours_dict:
                    neighbours_dict[id2] = {}
                neighbours_dict[id2][id1] = shared_border_length

    return neighbours_dict

def create_centroid_dict(input_layer, field_name, neighbours_dict):
    """
    Compute centroids and initialize attributes.

    Each feature's centroid is computed, and initial values are assigned for:
    - Raw radius (based on the input field)
    - Scaled radius (computed after all features are processed)
    - Perimeter (used to weight attraction forces)
    - Vectors (xvec, yvec) for displacement during iterations

    Args:
        input_layer (QgsVectorLayer): Input polygon layer.
        field_name (str): Field used to compute raw radius.
        neighbours_dict (dict): Neighbour pairs (used to compute scale).

    Returns:
        dict: 
            { fid: { 'x': x, 'y': y, 'perimeter': perimeter,'radius_raw': r_raw, 'radius_scaled': r_scaled, 'xvec': xvec, 'yvec': yvec } }
    """

    centroid_dict = {} # Dictionary to store results per feature

    # Iterate through each feature in the input layer
    for feat in input_layer.getFeatures():
        fid = int(feat.id())
        geom = feat.geometry()
        if not geom:
            continue # Skip invalid geometries
        
        # Compute centroid coordinates
        centroid = geom.centroid().asPoint()
        x, y = centroid.x(), centroid.y()

        # Compute perimeter of the polygon (used in attraction force weighting)
        perimeter = geom.length()

        # Get the value from the specified field and compute raw radius
        # The raw radius is proportional to sqrt(value / pi) for area-based scaling
        value = feat[field_name]
        radius_raw = math.sqrt(value / math.pi) if value and value > 0 else 0.0

         # Initialize the centroid entry with elements
        centroid_dict[fid] = {
            'x': x,
            'y': y,
            'perimeter': perimeter,
            'radius_raw': radius_raw,
            'radius_scaled': 0.0, # To be computed after scale factor
            'xvec': 0.0, # Initial velocity vector in x-direction
            'yvec': 0.0 # Initial velocity vector in y-direction
        }

    # Compute and apply scaling factor to raw radii
    scale = compute_scale_factor(centroid_dict, neighbours_dict)

    # Apply scaling to each feature’s radius
    for fid, props in centroid_dict.items():
        props['radius_scaled'] = props['radius_raw'] * scale

    return centroid_dict

def compute_scale_factor(centroid_dict, neighbours_dict):
    """
    Compute scale factor for radius scaling.

    Args:
        centroid_dict (dict): Centroid dictionary.
        neighbours_dict (dict): Neighbour pairs.

    Returns:
        float: scale factor.
    """
    tdist = 0.0 # Sum of distances between neighboring centroids
    tradius = 0.0 # Sum of combined raw radii for neighboring pairs

    # Iterate over all neighbor pairs
    for id1, neighbours in neighbours_dict.items():
        for id2, length in neighbours.items():
            if id1 < id2:  # Process each pair only once

                # Get coordinates and raw radii for both centroids
                x1 = centroid_dict[id1]['x']
                y1 = centroid_dict[id1]['y']
                r1 = centroid_dict[id1]['radius_raw']

                x2 = centroid_dict[id2]['x']
                y2 = centroid_dict[id2]['y']
                r2 = centroid_dict[id2]['radius_raw']

                # Compute Euclidean distance between the centroids
                dist = math.hypot(x2 - x1, y2 - y1)

                # Accumulate total distance and total raw radii
                tdist += dist
                tradius += (r1 + r2)

    # Avoid division by zero: if all radii are zero, use neutral scaling
    if tradius == 0:
        return 1.0

     # Return the scaling factor: average distance divided by average raw radius
    return tdist / tradius