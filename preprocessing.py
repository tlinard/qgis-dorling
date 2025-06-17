from math import hypot

from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    edit
)
from PyQt5.QtCore import QVariant

def preprocessing(input_layer, field_name):
    centroid_layer = create_centroid_layer(input_layer, field_name)
    neighbours_table = create_neighbours_table(input_layer)
    add_scaled_radius_field(centroid_layer, neighbours_table)
    return centroid_layer, neighbours_table

def create_centroid_layer(input_layer, field_name):
    """
    Creates a new point layer containing centroids of the input polygon layer 
    with an attribute from the original layer and a computed raw radius.

    Args:
        input_layer (QgsVectorLayer): The input polygon layer.
        field_name (str): The name of the field to retain.

    Returns:
        QgsVectorLayer: A new memory layer containing centroid points with attributes.
    """
    import math
    from PyQt5.QtCore import QVariant

    crs = input_layer.crs().authid()
    centroid_layer = QgsVectorLayer(f"Point?crs={crs}", "dorling", "memory")
    provider = centroid_layer.dataProvider()

    input_field = input_layer.fields().field(field_name)
    provider.addAttributes([input_field, QgsField("radius_raw", QVariant.Double)])
    centroid_layer.updateFields()

    features = []
    for feature in input_layer.getFeatures():
        geom = feature.geometry()
        if not geom:
            continue
        centroid = geom.centroid().asPoint()
        value = feature[field_name]
        radius_raw = math.sqrt(value / math.pi) if value and value > 0 else 0.0

        new_feat = QgsFeature(feature.id())
        new_feat.setGeometry(QgsGeometry.fromPointXY(centroid))
        new_feat.setAttributes([value, radius_raw])
        features.append(new_feat)

    provider.addFeatures(features)
    centroid_layer.updateExtents()

    return centroid_layer

def create_neighbours_table(layer):
    """
    Creates a table of neighbouring polygons with shared border lengths from a polygon layer.

    Args:
        layer (QgsVectorLayer): The input polygon layer.

    Returns:
        QgsVectorLayer: A memory layer representing the relationships between neighbouring regions.
    """
    fields = QgsFields()
    fields.append(QgsField("region_id", QVariant.Int))
    fields.append(QgsField("neighbour_id", QVariant.Int))
    fields.append(QgsField("length", QVariant.Double))

    relation_layer = QgsVectorLayer("None", "region_neighbours", "memory")
    relation_layer.dataProvider().addAttributes(fields)
    relation_layer.updateFields()

    features = []
    polygons = list(layer.getFeatures())

    for i, feat1 in enumerate(polygons):
        geom1 = feat1.geometry()
        id1 = feat1.id()

        for j in range(i + 1, len(polygons)):
            feat2 = polygons[j]
            geom2 = feat2.geometry()
            id2 = feat2.id()

            if geom1.touches(geom2):
                shared_border_length = geom1.intersection(geom2).length()

                new_feat = QgsFeature()
                new_feat.setAttributes([id1, id2, shared_border_length])
                features.append(new_feat)

    relation_layer.dataProvider().addFeatures(features)
    relation_layer.updateExtents()

    # QgsProject.instance().addMapLayer(relation_layer)

    return relation_layer

def compute_scale_factor(centroid_layer, neighbours_table, raw_radius_field="radius_raw"):
    """
    Compute the scale factor for adjusting circle sizes in a Dorling cartogram.

    Args:
        centroid_layer (QgsVectorLayer): Point memory layer with coordinates and raw radius field.
        neighbours_table (QgsVectorLayer): Relation layer with 'region_id' and 'neighbour_id' fields.
        raw_radius_field (str): Name of the field containing the unscaled radius (default is 'radius_raw').

    Returns:
        float: The scale factor.
    """
    centroid_dict = {}
    for feat in centroid_layer.getFeatures():
        fid = feat.id()
        geom = feat.geometry()
        if not geom:
            continue
        x, y = geom.asPoint().x(), geom.asPoint().y()
        radius = feat[raw_radius_field]
        centroid_dict[fid] = (x, y, radius)

    tot_dist = 0.0
    tot_radius = 0.0

    for relation in neighbours_table.getFeatures():
        id1 = relation["region_id"]
        id2 = relation["neighbour_id"]

        x1, y1, r1 = centroid_dict[id1]
        x2, y2, r2 = centroid_dict[id2]

        dist = hypot(x2 - x1, y2 - y1)
        tot_dist += dist
        tot_radius += r1 + r2

    if tot_radius == 0:
        return 1.0

    return tot_dist / tot_radius

def add_scaled_radius_field(centroid_layer, neighbours_table, raw_radius_field="radius_raw", scaled_radius_field="radius_scaled"):
    """
    Add a new attribute to the centroid layer containing the scaled radius.

    Args:
        centroid_layer (QgsVectorLayer): Layer with raw radii.
        neighbours_table (QgsVectorLayer): Layer containing neighbour pairs.
        raw_radius_field (str): Name of the field with raw radii.
        scaled_radius_field (str): Name of the field to store scaled radii.
    """
    provider = centroid_layer.dataProvider()

    # Add the new field if it doesn't exist yet
    if scaled_radius_field not in [f.name() for f in centroid_layer.fields()]:
        provider.addAttributes([QgsField(scaled_radius_field, QVariant.Double)])
        centroid_layer.updateFields()

    scaled_idx = centroid_layer.fields().indexFromName(scaled_radius_field)
    raw_idx = centroid_layer.fields().indexFromName(raw_radius_field)

    # Compute the scale factor
    scale = compute_scale_factor(centroid_layer, neighbours_table, raw_radius_field)

    # Update each feature with the scaled radius
    centroid_layer.startEditing()
    for feat in centroid_layer.getFeatures():
        raw_radius = feat[raw_idx]
        scaled_radius = raw_radius * scale
        centroid_layer.changeAttributeValue(feat.id(), scaled_idx, scaled_radius)
    centroid_layer.commitChanges()
        