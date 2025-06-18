from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsGeometry, QgsField, QgsPointXY,
    QgsProperty, QgsSingleSymbolRenderer, QgsSymbol, QgsUnitTypes
)
from PyQt5.QtCore import QVariant

def create_point_layer(input_layer, centroid_dict, layer_name="dorling"):
    """
    Create a memory point layer from a centroid_dict + original layer attributes.

    Args:
        input_layer (QgsVectorLayer): Original polygon layer (for attributes and CRS).
        centroid_dict (dict): { fid: { 'x': x, 'y': y, 'radius_raw': r_raw, 'radius_scaled': r_scaled, 'xvec': xvec, 'yvec': yvec } }
        layer_name (str): Name for the output memory layer.

    Returns:
        QgsVectorLayer: Point memory layer with centroids and attributes.
    """

    # Create memory point layer
    crs = input_layer.crs().authid()
    point_layer = QgsVectorLayer(f"Point?crs={crs}", layer_name, "memory")
    provider = point_layer.dataProvider()

    # --- Define fields ---
    # Copy original fields
    fields = input_layer.fields().toList()
    # Add Dorling fields
    fields.append(QgsField("radius_scaled", QVariant.Double))
    # fields.append(QgsField("xvec", QVariant.Double))
    # fields.append(QgsField("yvec", QVariant.Double))

    provider.addAttributes(fields)
    point_layer.updateFields()

    # --- Build feature list ---
    input_feat_dict = {feat.id(): feat for feat in input_layer.getFeatures()}

    features = []
    for fid, props in centroid_dict.items():
        if fid not in input_feat_dict:
            continue

        x = props['x']
        y = props['y']
        radius_scaled = props['radius_scaled']
        xvec = props['xvec']
        yvec = props['yvec']

        orig_feat = input_feat_dict[fid]
        orig_attrs = orig_feat.attributes()

        new_feat = QgsFeature()
        new_feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))

        # Combine original attributes + Dorling fields
        new_attrs = orig_attrs + [radius_scaled, xvec, yvec]
        new_feat.setAttributes(new_attrs)

        features.append(new_feat)

    # --- Add features ---
    provider.addFeatures(features)
    point_layer.updateExtents()

    return point_layer

def style_layer(layer, scaled_radius_field="radius_scaled"):
    """
    Apply a simple style to the Dorling centroid layer:
    - Circles with diameter = 2 * scaled_radius
    - In map units

    Args:
        layer (QgsVectorLayer): The centroid layer with 'radius_scaled' field.
        scaled_radius_field (str): Name of the scaled radius field.
    """

    # Create a simple circle symbol
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())

    # Set size property: diameter = 2 * radius_scaled
    size_expr = f"2 * \"{scaled_radius_field}\""
    symbol.setDataDefinedSize(QgsProperty.fromExpression(size_expr))

    # Force unit to be map units (meters if CRS is in meters)
    symbol.symbolLayer(0).setSizeUnit(QgsUnitTypes.RenderMapUnits)

    # Use Single Symbol Renderer
    renderer = QgsSingleSymbolRenderer(symbol)
    layer.setRenderer(renderer)

    # Refresh
    layer.triggerRepaint()

    return
