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
        input_layer (QgsVectorLayer): Input polygon layer.
        field_name (str): Field used to compute raw radius.

    Returns:
        tuple: (centroid_dict, neighbours_dict)

        - centroid_dict (dict): 
            { fid: { 'x': x, 'y': y, 'perimeter': perimeter, 'radius_raw': r_raw, 'radius_scaled': r_scaled, 'xvec': xvec, 'yvec': yvec } }
        - neighbours_dict (dict): 
            { region_id: { neighbour_id: shared_border_length, ... }, ... }
    """
    start_time = time.time()

    neighbours_dict = create_neighbours_dict(input_layer)

    centroid_dict = create_centroid_dict(input_layer, field_name, neighbours_dict)

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
    """
    # Build spatial index for polygon geometries
    index = QgsSpatialIndex()
    feature_dict = {}

    for feat in layer.getFeatures():
        index.insertFeature(feat)
        feature_dict[feat.id()] = feat

    neighbours_dict = {}
    seen_pairs = set()

    for id1, feat1 in feature_dict.items():
        geom1 = feat1.geometry()
        candidate_ids = index.intersects(geom1.boundingBox())

        if id1 not in neighbours_dict:
            neighbours_dict[id1] = {}

        for id2 in candidate_ids:
            if id2 == id1:
                continue

            pair = tuple(sorted((id1, id2)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            feat2 = feature_dict[id2]
            geom2 = feat2.geometry()

            if geom1.touches(geom2):
                shared_border_length = geom1.intersection(geom2).length()

                neighbours_dict[id1][id2] = shared_border_length
                if id2 not in neighbours_dict:
                    neighbours_dict[id2] = {}
                neighbours_dict[id2][id1] = shared_border_length

    return neighbours_dict

def create_centroid_dict(input_layer, field_name, neighbours_dict):
    """
    Compute centroids and initialize attributes.

    Args:
        input_layer (QgsVectorLayer): Input polygon layer.
        field_name (str): Field used to compute raw radius.
        neighbours_dict (dict): Neighbour pairs (used to compute scale).

    Returns:
        dict: 
            { fid: { 'x': x, 'y': y, 'perimeter': perimeter,'radius_raw': r_raw, 'radius_scaled': r_scaled, 'xvec': xvec, 'yvec': yvec } }
    """
    centroid_dict = {}

    for feat in input_layer.getFeatures():
        fid = int(feat.id())
        geom = feat.geometry()
        if not geom:
            continue

        centroid = geom.centroid().asPoint()
        x, y = centroid.x(), centroid.y()
        perimeter = geom.length()
        value = feat[field_name]
        radius_raw = math.sqrt(value / math.pi) if value and value > 0 else 0.0

        centroid_dict[fid] = {
            'x': x,
            'y': y,
            'perimeter': perimeter,
            'radius_raw': radius_raw,
            'radius_scaled': 0.0,
            'xvec': 0.0,
            'yvec': 0.0
        }

    # Add scaled radius
    scale = compute_scale_factor(centroid_dict, neighbours_dict)
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
    tdist = 0.0
    tradius = 0.0

    for id1, neighbours in neighbours_dict.items():
        for id2, length in neighbours.items():
            if id1 < id2:  # Process each pair only once
                x1 = centroid_dict[id1]['x']
                y1 = centroid_dict[id1]['y']
                r1 = centroid_dict[id1]['radius_raw']

                x2 = centroid_dict[id2]['x']
                y2 = centroid_dict[id2]['y']
                r2 = centroid_dict[id2]['radius_raw']

                dist = math.hypot(x2 - x1, y2 - y1)
                tdist += dist
                tradius += (r1 + r2)

    if tradius == 0:
        return 1.0

    return tdist / tradius