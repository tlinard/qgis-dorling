import math
import time
from math import hypot
from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsSpatialIndex
)

def preprocessing(input_layer, field_name):
    """
    Full preprocessing pipeline: generates centroid_dict and neighbours_list.
    """
    start_time = time.time()

    centroid_dict = create_centroid_dict(input_layer, field_name)
    neighbours_list = create_neighbours_list(input_layer)
    add_scaled_radius(centroid_dict, neighbours_list)

    end_time = time.time()
    print(f"[DorlingCartogram] Preprocessing completed in {end_time - start_time:.2f} seconds")

    return centroid_dict, neighbours_list

def create_centroid_dict(input_layer, field_name):
    """
    Creates a dictionary of centroids:
    { fid: { 'x': x, 'y': y, 'radius_raw': r_raw, 'radius_scaled': 0.0, 'xvec': 0.0, 'yvec': 0.0 } }
    """
    centroid_dict = {}

    for feat in input_layer.getFeatures():
        fid = int(feat.id())
        geom = feat.geometry()
        if not geom:
            continue

        centroid = geom.centroid().asPoint()
        x, y = centroid.x(), centroid.y()
        value = feat[field_name]
        radius_raw = math.sqrt(value / math.pi) if value and value > 0 else 0.0

        centroid_dict[fid] = {
            'x': x,
            'y': y,
            'radius_raw': radius_raw,
            'radius_scaled': 0.0,
            'xvec': 0.0,
            'yvec': 0.0
        }

    return centroid_dict

def create_neighbours_list(layer):
    """
    Creates a list of neighbouring polygon pairs:
    [ (region_id, neighbour_id, shared_border_length), ... ]
    """
    index = QgsSpatialIndex()
    feature_dict = {}

    # Build spatial index + feature lookup
    for feat in layer.getFeatures():
        index.insertFeature(feat)
        feature_dict[feat.id()] = feat

    neighbours_list = []
    seen_pairs = set()

    # Loop over each polygon
    for id1, feat1 in feature_dict.items():
        geom1 = feat1.geometry()
        candidate_ids = index.intersects(geom1.boundingBox())

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

                neighbours_list.append((id1, id2, shared_border_length))

    return neighbours_list

def compute_scale_factor(centroid_dict, neighbours_list):
    """
    Compute scale factor (same logic as Geopandas version):
    - iterate over unique neighbor pairs
    - accumulate tdist / tradius
    """
    tdist = 0.0
    tradius = 0.0

    for id1, id2, _length in neighbours_list:
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

def add_scaled_radius(centroid_dict, neighbours_list):
    """
    Compute scaled radius and update centroid_dict in-place.
    """
    scale = compute_scale_factor(centroid_dict, neighbours_list)
    print(f"[DorlingCartogram] Scale factor = {scale:.6f}")

    for fid, props in centroid_dict.items():
        props['radius_scaled'] = props['radius_raw'] * scale

    return centroid_dict