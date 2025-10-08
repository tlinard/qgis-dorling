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

def compute_dorling(centroid_dict, neighbours_dict,friction = 0.25, ratio = 0.4, iterations = 200):

    start_time = time.time()

    rmax = max(props['radius_scaled'] for props in centroid_dict.values())
    
    for i in range (iterations):
        spatial_index = create_spatial_index(centroid_dict)
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
        ratio (float): balance between repulsion and attraction (attraction %)
    """

    # Initialize cumulative displacement to monitor convergence
    total_displacement = 0.0
    
    # --- Iterate over each centroid ---
    for id1, props1 in centroid_dict.items():
        # Extract position and geometric properties
        x1, y1 = props1['x'], props1['y']
        perimeter1 = props1['perimeter']
        r1 = props1['radius_scaled']

        # Initialize force vectors for repulsion and attraction
        xrepel, yrepel = 0.0, 0.0
        xattract, yattract = 0.0, 0.0

        # Track the closest neighbor distance for force limiting
        closest = float('inf')
        
        # Define a bounding box to search and retrieve potentially overlapping circles
        search_rect = QgsRectangle(x1 - r1 - rmax, y1 - r1 - rmax, x1 + r1 + rmax, y1 + r1 + rmax)
        nearby_ids = spatial_index.intersects(search_rect)

        # --- Repulsion forces ---
        # Repulsion between overlapping circles to avoid collisions
        # Iterate over all nearby features
        for id2 in nearby_ids:
            # ignore self
            if id1 == id2:
                continue

            # Extract position and geometric properties of nearby circle (id2)
            props2 = centroid_dict[id2]
            x2, y2 = props2['x'], props2['y']
            r2 = props2['radius_scaled']

            # Compute distance and overlap between the two circles
            dx, dy, dist, overlap = circles_overlap(x1, y1, r1, x2, y2, r2)

            # Update the closest neighbor distance
            if dist < closest:
                closest = dist

            # Apply repulsion if overlap exists and distance is valid
            if overlap > 0 and dist > 1e-6:
                factor = overlap / dist
                xrepel -= factor * dx
                yrepel -= factor * dy

        # --- Attraction forces ---
        # Attraction toward original geographic neighbors
        # Iterate over all original neighbors
        if id1 in neighbours_dict:
            for id2, border_length in neighbours_dict[id1].items():
                # ignore self
                if id1 == id2:
                    continue
                
                # Extract position and geometric properties of neighbor circle (id2)
                props2 = centroid_dict[id2]
                x2, y2 = props2['x'], props2['y']
                r2 = props2['radius_scaled']

               # Compute distance and overlap between the two circles
                dx, dy, dist, overlap = circles_overlap(x1, y1, r1, x2, y2, r2)

                 # Apply attraction if circles are too far apart
                if overlap < 0 and dist > 1e-6:
                    factor = (-overlap * border_length / perimeter1) / dist
                    xattract += factor * dx
                    yattract += factor * dy
        
        # --- Limit repulsion forces ---
        # Limit repulsion to closest neighbor
        repdst = math.hypot(xrepel, yrepel)
        if repdst > closest:
            scale = closest / (repdst + 1e-6)
            xrepel *= scale
            yrepel *= scale
            # repdst = closest

        # --- Limit attraction forces ---
        atrdst = math.hypot(xattract, yattract)
        if repdst > 0.0 and atrdst > 1e-6:
            xattract = (repdst * xattract) / (atrdst + 1.0)
            yattract = (repdst * yattract) / (atrdst + 1.0)

        # --- Combine forces ---
        # Weighted sum of repulsion and attraction
        xtotal = (1.0 - ratio) * xrepel + ratio * xattract
        ytotal = (1.0 - ratio) * yrepel + ratio * yattract

        # --- Update motion vectors ---
        # Smooth motion with friction
        props1['xvec'] = friction * (props1['xvec'] + xtotal)
        props1['yvec'] = friction * (props1['yvec'] + ytotal)

    # --- Update positions ---
    for id, props in centroid_dict.items():
        # props['x'] += props['xvec']
        # props['y'] += props['yvec']

        dx = props['xvec']
        dy = props['yvec']
        displacement = math.hypot(dx, dy)
        total_displacement += displacement

        props['x'] += dx
        props['y'] += dy

    print(f"{total_displacement:.2f}")

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
        dx (float): Horizontal distance between the circle centers.
        dy (float): Vertical distance between the circle centers.
        dist (float): Euclidean distance between the circle centers.
        overlap (float): Amount of overlap between the circles.
    """

    dx = x2 - x1
    dy = y2 - y1

    dist = math.hypot(dx, dy)
    overlap = r1 + r2 - dist
    return dx, dy, dist, overlap

def create_spatial_index(centroid_dict):
    """
    Creates a spatial index from centroid_dict points.

    Args :
        centroid_dict (dict): 
            { fid: { 'x': x, 'y': y, 'perimeter': perimeter, 'radius_raw': r_raw, 'radius_scaled': r_scaled, 'xvec': xvec, 'yvec': yvec } }

    Returns:
        QgsSpatialIndex
    """
    index = QgsSpatialIndex()

    for fid, props in centroid_dict.items():
        point_geom = QgsGeometry.fromPointXY(QgsPointXY(props['x'], props['y']))
        feature = QgsFeature()
        feature.setGeometry(point_geom)
        feature.setId(fid)
        index.insertFeature(feature)

    return index