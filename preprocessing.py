from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProject
)
from PyQt5.QtCore import QVariant

def create_centroid_layer(input_layer, field_name):
    """
    Creates a new point layer containing centroids of the input polygon layer with an attribute from the original layer.

    Args:
        input_layer (QgsVectorLayer): The input polygon layer.
        field_name (str): The name of the field to retain.

    Returns:
        QgsVectorLayer: A new memory layer containing centroid points with attributes.
    """
    crs = input_layer.crs().authid()
    centroid_layer = QgsVectorLayer(f"Point?crs={crs}", "dorling", "memory")
    provider = centroid_layer.dataProvider()

    input_field = input_layer.fields().field(field_name)
    provider.addAttributes([input_field])
    centroid_layer.updateFields()

    features = []
    for feature in input_layer.getFeatures():
        geom = feature.geometry()
        if not geom:
            continue
        centroid = geom.centroid().asPoint()
        value = feature[field_name]

        new_feat = QgsFeature(feature.id())
        new_feat.setGeometry(QgsGeometry.fromPointXY(centroid))
        new_feat.setAttributes([value])
        features.append(new_feat)

    provider.addFeatures(features)
    centroid_layer.updateExtents()

    return centroid_layer

def create_neighbours_table(layer):
    """
    Creates a table of neighboring polygons with shared border lengths from a polygon layer.

    Args:
        layer (QgsVectorLayer): The input polygon layer.

    Returns:
        QgsVectorLayer: A memory layer representing the relationships between neighboring regions.
    """
    fields = QgsFields()
    fields.append(QgsField("region_id", QVariant.Int))
    fields.append(QgsField("neighbor_id", QVariant.Int))
    fields.append(QgsField("length", QVariant.Double))

    relation_layer = QgsVectorLayer("None", "region_neighbors", "memory")
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

def compute_scale_factor(centroid_layer, neighbours_table):
    pass