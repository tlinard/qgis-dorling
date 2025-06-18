"""
    From Dorling pseudocode
    Dorling, D. (2011). Area Cartograms : Their Use and Creation. In M. Dodge, R. Kitchin, & C. Perkins (Éds.), The Map Reader (1ʳᵉ éd., p. 252‑260). Wiley. https://doi.org/10.1002/9780470979587.ch33
    
    - Repulsion is computed between all overlapping circles.
    - Attraction is computed between neighbours based on border length and relative position.
    - Forces are combined and smoothed using a friction factor.
    - Positions (x, y) are updated accordingly.
"""

import time

def compute_dorling(centroid_dict, neighbours_table, friction = 0.25, ratio = 0.4):

    start_time = time.time()
    
    # for i in range (50):
    #     dorling_iterations(centroid_table, neighbours_table, friction, ratio)

    end_time = time.time()
    print(f"[DorlingCartogram] Dorling iterations completed in {end_time - start_time:.2f} seconds")
    return

def dorling_iterations(centroid_dict, neighbours_table, friction = 0.25, ratio = 0.4):
    return