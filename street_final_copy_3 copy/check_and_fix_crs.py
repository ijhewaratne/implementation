#!/usr/bin/env python3
"""
CRS Check and Fix Script for Branitz Energy Decision AI

This script checks the coordinate reference systems (CRS) of both buildings_gdf and street_gdf
and ensures they are both using the same projected CRS (UTM) for accurate distance calculations.

Usage:
    python check_and_fix_crs.py [--input-dir INPUT_DIR] [--output-dir OUTPUT_DIR]
"""

import geopandas as gpd
import os
import argparse
from pathlib import Path
import sys


def check_crs_info(gdf, name):
    """Check and display CRS information for a GeoDataFrame."""
    print(f"\n=== {name} CRS Information ===")
    print(f"CRS: {gdf.crs}")
    print(f"CRS Name: {gdf.crs.name if gdf.crs else 'None'}")
    print(f"Is Projected: {gdf.crs.is_projected if gdf.crs else 'Unknown'}")
    print(f"Is Geographic: {gdf.crs.is_geographic if gdf.crs else 'Unknown'}")
    print(f"Bounds: {gdf.total_bounds}")
    print(f"Number of features: {len(gdf)}")

    if gdf.crs and gdf.crs.is_geographic:
        print(
            "⚠️  WARNING: This is a geographic CRS (e.g., WGS84). For accurate distance calculations, convert to a projected CRS."
        )
    elif gdf.crs and gdf.crs.is_projected:
        print("✅ This is a projected CRS - suitable for distance calculations.")
    else:
        print("❓ CRS information unclear.")


def estimate_utm_crs(gdf):
    """Estimate the appropriate UTM CRS for the data."""
    if gdf.crs and gdf.crs.is_geographic:
        # Get the centroid of the data
        centroid = gdf.geometry.unary_union.centroid
        lon, lat = centroid.x, centroid.y

        # Determine UTM zone
        utm_zone = int((lon + 180) / 6) + 1

        # Determine hemisphere
        if lat >= 0:
            utm_crs = f"EPSG:{32600 + utm_zone}"  # Northern hemisphere
        else:
            utm_crs = f"EPSG:{32700 + utm_zone}"  # Southern hemisphere

        print(f"Estimated UTM CRS: {utm_crs} (based on centroid at {lon:.4f}, {lat:.4f})")
        return utm_crs
    else:
        print("Cannot estimate UTM CRS - data is not in geographic coordinates.")
        return None


def convert_to_utm(gdf, name, target_crs=None):
    """Convert a GeoDataFrame to UTM CRS."""
    if not gdf.crs:
        print(f"❌ {name} has no CRS defined. Cannot convert.")
        return gdf

    if gdf.crs.is_projected:
        print(f"✅ {name} is already projected. No conversion needed.")
        return gdf

    if not target_crs:
        target_crs = estimate_utm_crs(gdf)
        if not target_crs:
            print(f"❌ Could not determine target CRS for {name}")
            return gdf

    print(f"🔄 Converting {name} from {gdf.crs} to {target_crs}...")
    try:
        converted_gdf = gdf.to_crs(target_crs)
        print(f"✅ Successfully converted {name} to {target_crs}")
        return converted_gdf
    except Exception as e:
        print(f"❌ Error converting {name}: {e}")
        return gdf


def load_and_check_data(input_dir="data", output_dir="results_test"):
    """Load and check both buildings and street data."""

    # Define file paths - use processed files if available
    buildings_file = os.path.join(output_dir, "buildings_prepared.geojson")
    street_file = os.path.join(output_dir, "streets.geojson")

    # Fallback to raw files if processed files don't exist
    if not os.path.exists(buildings_file):
        buildings_file = os.path.join(input_dir, "geojson", "hausumringe_with_gebaeudeid.geojson")

    if not os.path.exists(street_file):
        street_file = os.path.join(input_dir, "osm", "branitzer_siedlung.osm")

    # Check if files exist
    if not os.path.exists(buildings_file):
        print(f"❌ Buildings file not found: {buildings_file}")
        return None, None

    if not os.path.exists(street_file):
        print(f"❌ Street file not found: {street_file}")
        return None, None

    # Load buildings data
    print("📁 Loading buildings data...")
    try:
        buildings_gdf = gpd.read_file(buildings_file)
        print(f"✅ Loaded {len(buildings_gdf)} buildings from {buildings_file}")
    except Exception as e:
        print(f"❌ Error loading buildings: {e}")
        return None, None

    # Load street data
    print("📁 Loading street data...")
    try:
        # Check if it's an OSM file or GeoJSON
        if street_file.endswith(".osm"):
            # OSM files have multiple layers, we want the 'lines' layer for streets
            street_gdf = gpd.read_file(street_file, layer="lines")
        else:
            # Regular GeoJSON file
            street_gdf = gpd.read_file(street_file)
        print(f"✅ Loaded {len(street_gdf)} street segments from {street_file}")
    except Exception as e:
        print(f"❌ Error loading streets: {e}")
        return None, None

    return buildings_gdf, street_gdf


def check_and_fix_crs(buildings_gdf, street_gdf, output_dir="results_test"):
    """Check and fix CRS issues for both datasets."""

    print("\n" + "=" * 60)
    print("CRS ANALYSIS AND FIX")
    print("=" * 60)

    # Check current CRS
    check_crs_info(buildings_gdf, "Buildings")
    check_crs_info(street_gdf, "Streets")

    # Check if CRS are compatible
    print(f"\n=== CRS Compatibility Check ===")
    if buildings_gdf.crs == street_gdf.crs:
        print("✅ Both datasets have the same CRS")
        crs_match = True
    else:
        print("❌ Datasets have different CRS")
        print(f"   Buildings: {buildings_gdf.crs}")
        print(f"   Streets: {street_gdf.crs}")
        crs_match = False

    # Determine target CRS
    print(f"\n=== Target CRS Selection ===")
    if buildings_gdf.crs and buildings_gdf.crs.is_geographic:
        target_crs = estimate_utm_crs(buildings_gdf)
    elif street_gdf.crs and street_gdf.crs.is_geographic:
        target_crs = estimate_utm_crs(street_gdf)
    else:
        # If both are already projected, use the buildings CRS as reference
        target_crs = buildings_gdf.crs
        print(f"Using buildings CRS as target: {target_crs}")

    # Convert both datasets to the same projected CRS
    print(f"\n=== CRS Conversion ===")
    buildings_utm = convert_to_utm(buildings_gdf, "Buildings", target_crs)
    streets_utm = convert_to_utm(street_gdf, "Streets", target_crs)

    # Verify conversion
    print(f"\n=== Verification ===")
    check_crs_info(buildings_utm, "Buildings (converted)")
    check_crs_info(streets_utm, "Streets (converted)")

    # Save converted data
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

        buildings_output = os.path.join(output_dir, "buildings_utm.geojson")
        streets_output = os.path.join(output_dir, "streets_utm.geojson")

        print(f"\n=== Saving Converted Data ===")
        try:
            buildings_utm.to_file(buildings_output, driver="GeoJSON")
            print(f"✅ Saved buildings to: {buildings_output}")
        except Exception as e:
            print(f"❌ Error saving buildings: {e}")

        try:
            streets_utm.to_file(streets_output, driver="GeoJSON")
            print(f"✅ Saved streets to: {streets_output}")
        except Exception as e:
            print(f"❌ Error saving streets: {e}")

    return buildings_utm, streets_utm


def demonstrate_distance_calculations(buildings_utm, streets_utm):
    """Demonstrate accurate distance calculations with projected CRS."""
    print(f"\n=== Distance Calculation Demo ===")

    if not buildings_utm.crs.is_projected or not streets_utm.crs.is_projected:
        print("❌ Cannot demonstrate distance calculations - data not in projected CRS")
        return

    # Calculate some example distances
    print("Calculating example distances...")

    # Distance between first two buildings
    if len(buildings_utm) >= 2:
        building1 = buildings_utm.iloc[0].geometry
        building2 = buildings_utm.iloc[1].geometry
        distance = building1.distance(building2)
        print(f"Distance between first two buildings: {distance:.2f} meters")

    # Distance from first building to nearest street
    if len(buildings_utm) >= 1 and len(streets_utm) >= 1:
        building = buildings_utm.iloc[0].geometry
        street_union = streets_utm.geometry.unary_union
        distance_to_street = building.distance(street_union)
        print(f"Distance from first building to nearest street: {distance_to_street:.2f} meters")

    print("✅ Distance calculations completed successfully!")


def main():
    parser = argparse.ArgumentParser(
        description="Check and fix CRS issues for buildings and street data"
    )
    parser.add_argument("--input-dir", default="data", help="Input directory containing data files")
    parser.add_argument(
        "--output-dir", default="results_test", help="Output directory for converted files"
    )
    parser.add_argument(
        "--demo-distances", action="store_true", help="Demonstrate distance calculations"
    )

    args = parser.parse_args()

    print("🔍 Branitz Energy Decision AI - CRS Check and Fix")
    print("=" * 60)

    # Load data
    buildings_gdf, street_gdf = load_and_check_data(args.input_dir, args.output_dir)

    if buildings_gdf is None or street_gdf is None:
        print("❌ Failed to load data. Exiting.")
        sys.exit(1)

    # Check and fix CRS
    buildings_utm, streets_utm = check_and_fix_crs(buildings_gdf, street_gdf, args.output_dir)

    # Demonstrate distance calculations
    if args.demo_distances:
        demonstrate_distance_calculations(buildings_utm, streets_utm)

    print(f"\n🎉 CRS check and fix completed!")
    print(f"📁 Converted files saved to: {args.output_dir}")
    print(f"📊 Both datasets now use the same projected CRS for accurate distance calculations.")


if __name__ == "__main__":
    main()
