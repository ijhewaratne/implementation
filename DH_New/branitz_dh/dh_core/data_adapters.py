"""
Data adapters for handling various data sources and formats in the DH project.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging
import geopandas as gpd

from .config import Config


class DataAdapter:
    """Adapter for handling data input/output operations."""
    
    def __init__(self, config: Config):
        """Initialize data adapter.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.data_dirs = config.data_dirs
        self.logger = logging.getLogger(__name__)
        
        # Ensure directories exist
        config.ensure_dirs()
    
    def load_csv(self, filename: str, **kwargs) -> pd.DataFrame:
        """Load CSV file from inputs directory.
        
        Args:
            filename: Name of CSV file
            **kwargs: Additional arguments for pd.read_csv
            
        Returns:
            Loaded DataFrame
        """
        filepath = self.data_dirs["inputs"] / filename
        if not filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        
        self.logger.info(f"Loading CSV: {filepath}")
        return pd.read_csv(filepath, **kwargs)
    
    def save_csv(self, df: pd.DataFrame, filename: str, **kwargs) -> Path:
        """Save DataFrame as CSV to outputs directory.
        
        Args:
            df: DataFrame to save
            filename: Output filename
            **kwargs: Additional arguments for df.to_csv
            
        Returns:
            Path to saved file
        """
        filepath = self.data_dirs["outputs"] / filename
        self.logger.info(f"Saving CSV: {filepath}")
        df.to_csv(filepath, index=False, **kwargs)
        return filepath
    
    def load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON file from inputs directory.
        
        Args:
            filename: Name of JSON file
            
        Returns:
            Loaded JSON data
        """
        filepath = self.data_dirs["inputs"] / filename
        if not filepath.exists():
            raise FileNotFoundError(f"JSON file not found: {filepath}")
        
        self.logger.info(f"Loading JSON: {filepath}")
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def save_json(self, data: Dict[str, Any], filename: str) -> Path:
        """Save data as JSON to outputs directory.
        
        Args:
            data: Data to save
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        filepath = self.data_dirs["outputs"] / filename
        self.logger.info(f"Saving JSON: {filepath}")
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return filepath
    
    def load_catalog(self, catalog_name: str) -> Dict[str, Any]:
        """Load data catalog from catalogs directory.
        
        Args:
            catalog_name: Name of catalog file (without extension)
            
        Returns:
            Catalog data
        """
        catalog_path = self.data_dirs["catalogs"] / f"{catalog_name}.json"
        if not catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found: {catalog_path}")
        
        self.logger.info(f"Loading catalog: {catalog_path}")
        with open(catalog_path, 'r') as f:
            return json.load(f)
    
    def save_catalog(self, catalog_data: Dict[str, Any], catalog_name: str) -> Path:
        """Save data catalog to catalogs directory.
        
        Args:
            catalog_data: Catalog data to save
            catalog_name: Name of catalog
            
        Returns:
            Path to saved catalog
        """
        catalog_path = self.data_dirs["catalogs"] / f"{catalog_name}.json"
        self.logger.info(f"Saving catalog: {catalog_path}")
        with open(catalog_path, 'w') as f:
            json.dump(catalog_data, f, indent=2, ensure_ascii=False)
        return catalog_path
    
    def get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key.
        
        Args:
            cache_key: Unique cache identifier
            
        Returns:
            Path to cache file
        """
        return self.data_dirs["cache"] / f"{cache_key}.json"
    
    def load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Load data from cache.
        
        Args:
            cache_key: Cache identifier
            
        Returns:
            Cached data or None if not found
        """
        cache_path = self.get_cache_path(cache_key)
        if cache_path.exists():
            self.logger.info(f"Loading from cache: {cache_path}")
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None
    
    def save_to_cache(self, data: Dict[str, Any], cache_key: str) -> Path:
        """Save data to cache.
        
        Args:
            data: Data to cache
            cache_key: Cache identifier
            
        Returns:
            Path to cached file
        """
        cache_path = self.get_cache_path(cache_key)
        self.logger.info(f"Saving to cache: {cache_path}")
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return cache_path
    
    def list_inputs(self) -> List[Path]:
        """List all files in inputs directory.
        
        Returns:
            List of input file paths
        """
        return list(self.data_dirs["inputs"].glob("*"))
    
    def list_outputs(self) -> List[Path]:
        """List all files in outputs directory.
        
        Returns:
            List of output file paths
        """
        return list(self.data_dirs["outputs"].glob("*"))


def project_to_meters(gdf, epsg: int = 25833):
    """
    Project GeoDataFrame to a meter-based coordinate system.
    
    Args:
        gdf: GeoDataFrame to project
        epsg: EPSG code for target coordinate system (default: 25833 - UTM Zone 33N)
        
    Returns:
        Projected GeoDataFrame
    """
    return gdf.to_crs(epsg)


def load_network_from_json(json_path: str):
    """
    Reads network_data.json with normalized [0..1] coords + metadata.original_bounds.
    Respects metadata.original_crs if present (defaults to EPSG:25833 for Cottbus).
    Returns WGS84 (EPSG:4326) LineStrings with columns: diameter_m, p_from, p_to, vel_ms.
    """
    import json, numpy as np, geopandas as gpd
    from shapely.geometry import LineString

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []

    def _make_gdf(rows, crs_code):
        gdf = gpd.GeoDataFrame(rows, crs=crs_code)
        return gdf.to_crs(4326)

    if "pipes" in data:
        b = (data.get("metadata", {}) or {}).get("original_bounds", {})
        crs_meta = (data.get("metadata", {}) or {}).get("original_crs", "EPSG:25833")  # <- default for Cottbus
        # Fallback: if bounds look like degrees (abs <= 180/90), treat as EPSG:4326
        if {"x_min","x_max","y_min","y_max"} <= b.keys():
            x0,x1,y0,y1 = b["x_min"], b["x_max"], b["y_min"], b["y_max"]
            if max(abs(x0),abs(x1),abs(y0),abs(y1)) <= 360:
                crs_meta = "EPSG:4326"
            dx = lambda x: x0 + float(x)*(x1-x0)
            dy = lambda y: y0 + float(y)*(y1-y0)
        else:
            # absolute coords already; detect CRS by magnitude
            xs, ys = [], []
            for p in data["pipes"]:
                xs += [p["from"]["x"], p["to"]["x"]]
                ys += [p["from"]["y"], p["to"]["y"]]
            if max(map(abs, xs+ys)) <= 360:
                crs_meta = "EPSG:4326"
            else:
                crs_meta = "EPSG:25833"  # sensible default for DE
            dx = lambda x: float(x)
            dy = lambda y: float(y)

        for p in data["pipes"]:
            fx, fy = p["from"]["x"], p["from"]["y"]
            tx, ty = p["to"]["x"],   p["to"]["y"]
            rows.append({
                "diameter_m": p.get("diameter"),
                "p_from": p.get("pressure_from"),
                "p_to":   p.get("pressure_to"),
                "pressure_gradient": p.get("pressure_gradient"),
                "vel_ms": p.get("velocity"),
                "geometry": LineString([(dx(fx), dy(fy)), (dx(tx), dy(ty))])
            })
        return _make_gdf(rows, crs_meta)

    elif "nodes" in data and "edges" in data:
        # absolute schema; detect CRS by magnitude
        nodes = {n["id"]: (float(n["x"]), float(n["y"])) for n in data["nodes"]}
        xs = [xy[0] for xy in nodes.values()]; ys=[xy[1] for xy in nodes.values()]
        crs_meta = "EPSG:4326" if max(map(abs, xs+ys)) <= 360 else "EPSG:25833"
        for e in data["edges"]:
            sx, sy = nodes[e["source"]]; tx, ty = nodes[e["target"]]
            rows.append({
                "diameter_m": e.get("diameter"),
                "p_from": e.get("p_from"),
                "p_to":   e.get("p_to"),
                "pressure_gradient": e.get("pressure_gradient"),
                "vel_ms": e.get("velocity"),
                "geometry": LineString([(sx, sy), (tx, ty)])
            })
        return _make_gdf(rows, crs_meta)

    else:
        raise ValueError("Unknown network_data.json schema")


def load_addresses_geojson(geojson_path: str) -> 'gpd.GeoDataFrame':
    """
    Load addresses from GeoJSON file.
    
    Args:
        geojson_path: Path to GeoJSON file
        
    Returns:
        GeoDataFrame with address points
    """
    try:
        return gpd.read_file(geojson_path)
    except FileNotFoundError:
        # Create dummy address data if file doesn't exist
        from shapely.geometry import Point
        import numpy as np
        
        # Create sample address points
        dummy_points = []
        dummy_data = []
        
        for i in range(10):
            point = Point(0.001 + i * 0.0001, 0.001 + i * 0.0001)
            dummy_points.append(point)
            dummy_data.append({
                'address_id': f'addr_{i}',
                'street': f'Street {i}',
                'number': i + 1
            })
        
        return gpd.GeoDataFrame(dummy_data, geometry=dummy_points, crs="EPSG:4326")


def load_gebaeudeanalyse(csv_path: str) -> pd.DataFrame:
    """
    Load building analysis data from CSV.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        DataFrame with building analysis data
    """
    try:
        return pd.read_csv(csv_path)
    except FileNotFoundError:
        # Return empty DataFrame if file doesn't exist
        return pd.DataFrame()


def load_uwerte(csv_path: str) -> pd.DataFrame:
    """
    Load U-values from CSV.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        DataFrame with U-values
    """
    try:
        return pd.read_csv(csv_path)
    except FileNotFoundError:
        # Return empty DataFrame if file doesn't exist
        return pd.DataFrame()
