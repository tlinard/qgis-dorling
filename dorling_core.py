"""
    From Dorling pseudocode
    Dorling, D. (2011). Area Cartograms : Their Use and Creation. In M. Dodge, R. Kitchin, & C. Perkins (Éds.), The Map Reader (1ʳᵉ éd., p. 252‑260). Wiley. https://doi.org/10.1002/9780470979587.ch33
    
    - Repulsion is computed between all overlapping circles.
    - Attraction is computed between neighbours based on border length and relative position.
    - Forces are combined and smoothed using a friction factor.
    - Positions (x, y) are updated accordingly.
"""
import math
import time

from math import hypot

from qgis.core import QgsSpatialIndex, QgsRectangle, QgsFeature, QgsGeometry, QgsPointXY

def compute_dorling(centroid_dict, neighbours_dict, spatial_index ,friction = 0.25, ratio = 0.4):

    start_time = time.time()

    rmax = max(props['radius_scaled'] for props in centroid_dict.values())
    
    for i in range (200):
        dorling_iteration(centroid_dict, neighbours_dict, spatial_index, rmax, friction, ratio)

    end_time = time.time()
    print(f"[DorlingCartogram] Dorling iterations completed in {end_time - start_time:.2f} seconds")
    return

def dorling_iteration(centroid_dict, neighbours_dict, spatial_index, rmax, friction = 0.25, ratio = 0.4):
    """
    One iteration of the Dorling algorithm.

    - Repulsion: computed between all overlapping circles (using spatial index)
    - Attraction: computed between original neighbors (using border length / perimeter)
    - Motion vectors smoothed using friction
    - Positions updated at the end (after loop)

    Args:
        centroid_dict (dict): { fid: { 'x', 'y', 'radius_scaled', 'perimeter', ... } }
        neighbours_dict (dict): { id1: { id2: border_length, ... } }
        spatial_index (QgsSpatialIndex): spatial index of current centroids
        rmax (float): max radius (scaled), used for search window
        friction (float): damping factor
        ratio (float): balance between repulsion / attraction
    """
    
    # --- Iterate over each centroid ---
    for id1, props1 in centroid_dict.items():
        x1, y1 = props1['x'], props1['y']
        perimeter1 = props1['perimeter']
        r1 = props1['radius_scaled']

        xrepel, yrepel = 0.0, 0.0
        xattract, yattract = 0.0, 0.0
        closest = float('inf')
        
        # --- Spatial query: overlapping candidates ---
        search_rect = QgsRectangle(x1 - r1 - rmax, y1 - r1 - rmax, x1 + r1 + rmax, y1 + r1 + rmax)
        nearby_ids = spatial_index.intersects(search_rect)

        # --- Repulsion forces (overlapping only) ---
        for id2 in nearby_ids:
            if id1 == id2:
                continue # ignore self

            props2 = centroid_dict[id2]
            x2, y2 = props2['x'], props2['y']
            r2 = props2['radius_scaled']

            dx = x2 - x1
            dy = y2 - y1

            dist, overlap = circles_overlap(x1, y1, r1, x2, y2, r2)

            if dist < closest:
                closest = dist

            if overlap > 0 and dist > 1e-6:
                factor = overlap / dist
                xrepel -= factor * dx
                yrepel -= factor * dy

        # --- Attraction forces (neighbors only) ---
        if id1 in neighbours_dict:
            for id2, border_length in neighbours_dict[id1].items():
                if id1 == id2:
                    continue # ignore self

                props2 = centroid_dict[id2]
                x2, y2 = props2['x'], props2['y']
                r2 = props2['radius_scaled']

                dx = x2 - x1
                dy = y2 - y1

                dist, overlap = circles_overlap(x1, y1, r1, x2, y2, r2)

                if overlap < 0 and dist > 1e-6:
                    factor = (-overlap * border_length / perimeter1) / dist
                    xattract += factor * dx
                    yattract += factor * dy
        
        # --- Limit repulsion if too large ---
        repdst = math.hypot(xrepel, yrepel)
        if repdst > closest:
            scale = closest / (repdst + 1e-6)
            xrepel *= scale
            yrepel *= scale
            repdst = closest

        # --- Combine forces ---
        xtotal = (1.0 - ratio) * xrepel + ratio * xattract
        ytotal = (1.0 - ratio) * yrepel + ratio * yattract

        # --- Apply friction and update motion vectors ---
        # props1['xvec'] = friction * (props1['xvec'] + xtotal)
        # props1['yvec'] = friction * (props1['yvec'] + ytotal)
        props1['xvec'] = xtotal
        props1['yvec'] = ytotal

    # --- Update positions ---
    for id, props in centroid_dict.items():
        props['x'] += props['xvec']
        props['y'] += props['yvec']

    return

def circles_overlap(x1, y1, r1, x2, y2, r2):
    """
    Computes the distance and overlap between two circles.

    The overlap is defined as:
        overlap = r1 + r2 - distance_between_centers

    - If overlap > 0: the circles overlap.
    - If overlap = 0: the circles are exactly touching.
    - If overlap < 0: the circles are separated.

    Args:
        x1, y1 (float): Coordinates of the center of the first circle.
        r1 (float): Radius of the first circle.
        x2, y2 (float): Coordinates of the center of the second circle.
        r2 (float): Radius of the second circle.

    Returns:
        dist (float): Euclidean distance between the circle centers.
        overlap (float): Amount of overlap between the circles.
    """
    dist = math.hypot(x2 - x1, y2 - y1)
    overlap = r1 + r2 - dist
    return dist, overlap