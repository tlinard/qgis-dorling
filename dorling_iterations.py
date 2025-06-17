def create_dorling_layer(input_layer, field_name):
    """
    Creates a Dorling cartogram layer from the input polygon layer and a specified field.

    Args:
        input_layer (QgsVectorLayer): The input polygon layer.
        field_name (str): The field based on which the Dorling cartogram is generated.

    Returns:
        QgsVectorLayer: A new Dorling cartogram layer.
    """
    centroid_layer = create_centroid_layer(input_layer, field_name)
    # return set_symbol_size(centroid_layer, field_name)
    return centroid_layer