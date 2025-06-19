"""
    From Dorling pseudocode
    Dorling, D. (2011). Area Cartograms : Their Use and Creation. In M. Dodge, R. Kitchin, & C. Perkins (Éds.), The Map Reader (1ʳᵉ éd., p. 252‑260). Wiley. https://doi.org/10.1002/9780470979587.ch33
    
    - Repulsion is computed between all overlapping circles.
    - Attraction is computed between neighbours based on border length and relative position.
    - Forces are combined and smoothed using a friction factor.
    - Positions (x, y) are updated accordingly.
"""
import time

from qgis.core import QgsSpatialIndex, QgsRectangle, QgsFeature, QgsGeometry, QgsPointXY

def compute_dorling(centroid_dict, neighbours_table, spatial_index ,friction = 0.25, ratio = 0.4):

    start_time = time.time()
    
    # for i in range (50):
    #     dorling_iterations(centroid_table, neighbours_table, friction, ratio)

    end_time = time.time()
    print(f"[DorlingCartogram] Dorling iterations completed in {end_time - start_time:.2f} seconds")
    return

def dorling_iterations(centroid_dict, neighbours_table, spatial_index, friction = 0.25, ratio = 0.4):

    # Iterate over each centroid
    for id1, props2 in centroid_dict.items():
        x1, y1 = props1['x'], props1['y']
        r1 = props1['radius_scaled']

        xrepel, yrepel = 0.0, 0.0
        xattract, yattract = 0.0, 0.0
        
        # Find possible overlapping circles
        search_rect = QgsRectangle(x1 - r1)
       

    return