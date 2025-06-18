import time

def compute_dorling(centroid_dict, neighbours_table, friction = 0.25, ratio = 0.4):

    start_time = time.time()
    
    # for i in range (50):
    #     dorling_iterations(centroid_table, neighbours_table, friction, ratio)

    # change_centroids_positions(layer, centroid_table)

    end_time = time.time()
    print(f"[DorlingCartogram] Dorling iterations completed in {end_time - start_time:.2f} seconds")
    return