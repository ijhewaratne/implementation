"""
CRS Utilities for Branitz Energy Decision AI

This module provides utilities for checking and fixing coordinate reference systems
to ensure accurate distance calculations throughout the workflow.
"""

import geopandas as gpd
import os
import warnings
from typing import Tuple, Optional, Union
from pathlib import Path


def check_crs_info(gdf: gpd.GeoDataFrame, name: str = "GeoDataFrame") -> dict:
    """
    Check and return CRS information for a GeoDataFrame.

    Args:
        gdf: GeoDataFrame to check
        name: Name for display purposes

    Returns:
        Dictionary with CRS information
    """
    info = {
        "name": name,
        "crs": gdf.crs,
        "crs_name": gdf.crs.name if gdf.crs else "None",
        "is_projected": gdf.crs.is_projected if gdf.crs else None,
        "is_geographic": gdf.crs.is_geographic if gdf.crs else None,
        "bounds": gdf.total_bounds.tolist() if len(gdf) > 0 else None,
        "num_features": len(gdf),
        "needs_conversion": False,
        "warning": None,
    }

    if gdf.crs and gdf.crs.is_geographic:
        info["needs_conversion"] = True
        info["warning"] = (
            "Geographic CRS detected. Convert to projected CRS for accurate distance calculations."
        )
    elif gdf.crs and gdf.crs.is_projected:
        info["warning"] = "Projected CRS detected - suitable for distance calculations."
    else:
        info["warning"] = "CRS information unclear."

    return info


def estimate_utm_crs(gdf: gpd.GeoDataFrame) -> Optional[str]:
    """
    Estimate the appropriate UTM CRS for the data.

    Args:
        gdf: GeoDataFrame with geographic coordinates

    Returns:
        UTM CRS string (e.g., "EPSG:32633") or None if cannot determine
    """
    if not gdf.crs or not gdf.crs.is_geographic:
        return None

    try:
        # Get the centroid of the data
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            centroid = gdf.geometry.union_all().centroid

        lon, lat = centroid.x, centroid.y

        # Determine UTM zone
        utm_zone = int((lon + 180) / 6) + 1

        # Determine hemisphere
        if lat >= 0:
            utm_crs = f"EPSG:{32600 + utm_zone}"  # Northern hemisphere
        else:
            utm_crs = f"EPSG:{32700 + utm_zone}"  # Southern hemisphere

        return utm_crs
    except Exception:
        return None


def ensure_projected_crs(
    gdf: gpd.GeoDataFrame, target_crs: Optional[str] = None, name: str = "GeoDataFrame"
) -> gpd.GeoDataFrame:
    """
    Ensure a GeoDataFrame is in a projected CRS.

    Args:
        gdf: GeoDataFrame to convert
        target_crs: Target CRS (if None, will estimate UTM)
        name: Name for logging purposes

    Returns:
        GeoDataFrame in projected CRS
    """
    if not gdf.crs:
        raise ValueError(f"{name} has no CRS defined. Cannot convert.")

    if gdf.crs.is_projected:
        return gdf

    if not target_crs:
        target_crs = estimate_utm_crs(gdf)
        if not target_crs:
            raise ValueError(f"Could not determine target CRS for {name}")

    try:
        converted_gdf = gdf.to_crs(target_crs)
        return converted_gdf
    except Exception as e:
        raise ValueError(f"Error converting {name} to {target_crs}: {e}")


def ensure_same_crs(
    buildings_gdf: gpd.GeoDataFrame, streets_gdf: gpd.GeoDataFrame, target_crs: Optional[str] = None
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Ensure both buildings and streets GeoDataFrames use the same projected CRS.

    Args:
        buildings_gdf: Buildings GeoDataFrame
        streets_gdf: Streets GeoDataFrame
        target_crs: Target CRS (if None, will estimate UTM)

    Returns:
        Tuple of (buildings_gdf, streets_gdf) in the same projected CRS
    """
    # Check current CRS status
    buildings_info = check_crs_info(buildings_gdf, "Buildings")
    streets_info = check_crs_info(streets_gdf, "Streets")

    # Determine target CRS
    if not target_crs:
        if buildings_info["needs_conversion"]:
            target_crs = estimate_utm_crs(buildings_gdf)
        elif streets_info["needs_conversion"]:
            target_crs = estimate_utm_crs(streets_gdf)
        else:
            # Both are already projected, use buildings CRS as reference
            target_crs = buildings_gdf.crs

    if not target_crs:
        raise ValueError("Could not determine appropriate target CRS")

    # Convert both to target CRS
    buildings_proj = ensure_projected_crs(buildings_gdf, target_crs, "Buildings")
    streets_proj = ensure_projected_crs(streets_gdf, target_crs, "Streets")

    return buildings_proj, streets_proj


def load_and_prepare_data(
    buildings_file: Union[str, Path],
    streets_file: Union[str, Path],
    target_crs: Optional[str] = None,
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Load buildings and streets data and ensure they use the same projected CRS.

    Args:
        buildings_file: Path to buildings file
        streets_file: Path to streets file
        target_crs: Target CRS (if None, will estimate UTM)

    Returns:
        Tuple of (buildings_gdf, streets_gdf) in the same projected CRS
    """
    # Load data
    if not os.path.exists(buildings_file):
        raise FileNotFoundError(f"Buildings file not found: {buildings_file}")

    if not os.path.exists(streets_file):
        raise FileNotFoundError(f"Streets file not found: {streets_file}")

    # Load buildings
    buildings_gdf = gpd.read_file(buildings_file)

    # Load streets (handle OSM files)
    if str(streets_file).endswith(".osm"):
        streets_gdf = gpd.read_file(streets_file, layer="lines")
    else:
        streets_gdf = gpd.read_file(streets_file)

    # Ensure same CRS
    buildings_proj, streets_proj = ensure_same_crs(buildings_gdf, streets_gdf, target_crs)

    return buildings_proj, streets_proj


def save_with_crs(
    gdf: gpd.GeoDataFrame, output_file: Union[str, Path], driver: str = "GeoJSON"
) -> None:
    """
    Save a GeoDataFrame with explicit CRS information.

    Args:
        gdf: GeoDataFrame to save
        output_file: Output file path
        driver: File driver (default: "GeoJSON")
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    gdf.to_file(output_file, driver=driver)


def get_distance_calculator(
    buildings_gdf: gpd.GeoDataFrame, streets_gdf: gpd.GeoDataFrame
) -> callable:
    """
    Create a distance calculator function that ensures CRS compatibility.

    Args:
        buildings_gdf: Buildings GeoDataFrame
        streets_gdf: Streets GeoDataFrame

    Returns:
        Function that calculates distances between buildings and streets
    """
    # Ensure both are in the same projected CRS
    buildings_proj, streets_proj = ensure_same_crs(buildings_gdf, streets_gdf)

    def calculate_distances():
        """Calculate distances between buildings and streets."""
        results = []

        for idx, building in buildings_proj.iterrows():
            building_geom = building.geometry
            building_id = building.get("GebaeudeID", f"building_{idx}")

            # Calculate distance to nearest street
            min_distance = float("inf")
            nearest_street = None

            for street_idx, street in streets_proj.iterrows():
                distance = building_geom.distance(street.geometry)
                if distance < min_distance:
                    min_distance = distance
                    nearest_street = street_idx

            results.append(
                {
                    "building_id": building_id,
                    "nearest_street": nearest_street,
                    "distance_meters": min_distance,
                }
            )

        return results

    return calculate_distances


# Convenience function for quick CRS check
def quick_crs_check(buildings_gdf: gpd.GeoDataFrame, streets_gdf: gpd.GeoDataFrame) -> bool:
    """
    Quick check if both GeoDataFrames are ready for distance calculations.

    Args:
        buildings_gdf: Buildings GeoDataFrame
        streets_gdf: Streets GeoDataFrame

    Returns:
        True if both are in the same projected CRS, False otherwise
    """
    if not buildings_gdf.crs or not streets_gdf.crs:
        return False

    if buildings_gdf.crs != streets_gdf.crs:
        return False

    if not buildings_gdf.crs.is_projected:
        return False

    return True
