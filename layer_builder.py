from qgis.core import (
    QgsProperty,
    QgsSingleSymbolRenderer,
    QgsSymbol,
    QgsUnitTypes
)

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
