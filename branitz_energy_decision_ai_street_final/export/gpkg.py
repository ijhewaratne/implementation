"""
Consolidated GeoPackage Export

Exports multiple layers to a single GeoPackage file with guarded geopandas import.
"""

from typing import Dict
from pathlib import Path


def export_consolidated_gpkg(layers: Dict[str, "GeoDataFrame"], out_path: str) -> str:
    """
    Export multiple layers to a single GeoPackage file.
    
    Args:
        layers: name -> GeoDataFrame (must share CRS). Requires geopandas; raises ImportError otherwise.
        out_path: Output file path
    
    Returns:
        Absolute path to the created GeoPackage file
    
    Raises:
        ImportError: If geopandas is not available
    """
    try:
        import geopandas as gpd  # noqa: F401
    except Exception as e:
        raise ImportError("GeoPackage export requires geopandas") from e
    
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    
    mode = "w"
    for name, gdf in layers.items():
        gdf.to_file(out, layer=name, driver="GPKG", mode=mode)
        mode = "a"
    
    return str(out.resolve()) 