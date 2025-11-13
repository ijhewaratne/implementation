#!/usr/bin/env python3
"""
Example Usage of CRS Utilities for Branitz Energy Decision AI

This script demonstrates how to use the CRS utilities module in different scenarios.
"""

import geopandas as gpd
import os
from src import crs_utils, data_preparation


def example_1_basic_crs_check():
    """Example 1: Basic CRS checking and conversion."""
    print("=" * 60)
    print("Example 1: Basic CRS Checking and Conversion")
    print("=" * 60)

    # Load data
    buildings_file = "results_test/buildings_prepared.geojson"
    streets_file = "results_test/streets.geojson"

    if not os.path.exists(buildings_file) or not os.path.exists(streets_file):
        print("❌ Required files not found. Run the pipeline first or use example_2.")
        return

    # Load data
    buildings_gdf = gpd.read_file(buildings_file)
    streets_gdf = gpd.read_file(streets_file)

    # Check CRS information
    buildings_info = crs_utils.check_crs_info(buildings_gdf, "Buildings")
    streets_info = crs_utils.check_crs_info(streets_gdf, "Streets")

    print(f"Buildings CRS: {buildings_info['crs']}")
    print(f"Streets CRS: {streets_info['crs']}")
    print(
        f"Ready for distance calculations: {crs_utils.quick_crs_check(buildings_gdf, streets_gdf)}"
    )

    # Convert to same projected CRS if needed
    if not crs_utils.quick_crs_check(buildings_gdf, streets_gdf):
        print("🔄 Converting to same projected CRS...")
        buildings_proj, streets_proj = crs_utils.ensure_same_crs(buildings_gdf, streets_gdf)
        print(f"✅ Conversion complete!")
        print(f"New Buildings CRS: {buildings_proj.crs}")
        print(f"New Streets CRS: {streets_proj.crs}")
    else:
        print("✅ Data already in compatible projected CRS!")


def example_2_load_and_prepare():
    """Example 2: Load and prepare data with automatic CRS handling."""
    print("\n" + "=" * 60)
    print("Example 2: Load and Prepare Data with Automatic CRS Handling")
    print("=" * 60)

    # Use the integrated function
    try:
        buildings_gdf, edges_gdf, nodes_gdf, graph = data_preparation.load_and_prepare_data(
            buildings_file="data/geojson/hausumringe_with_gebaeudeid.geojson",
            osm_file="data/osm/branitzer_siedlung.osm",
            output_dir="results_test",
            selected_buildings=None,  # Use all buildings
            ensure_projected=True,
        )

        print(f"✅ Successfully loaded and prepared data!")
        print(f"Buildings: {len(buildings_gdf)} features, CRS: {buildings_gdf.crs}")
        if edges_gdf is not None:
            print(f"Streets: {len(edges_gdf)} features, CRS: {edges_gdf.crs}")

        # Demonstrate distance calculations
        distance_calc = crs_utils.get_distance_calculator(buildings_gdf, edges_gdf)
        distances = distance_calc()

        print(f"\n📏 Distance calculation example:")
        for i, result in enumerate(distances[:3]):  # Show first 3
            print(
                f"  Building {result['building_id']}: {result['distance_meters']:.2f} m to nearest street"
            )

    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_custom_crs_conversion():
    """Example 3: Custom CRS conversion."""
    print("\n" + "=" * 60)
    print("Example 3: Custom CRS Conversion")
    print("=" * 60)

    # Load data
    buildings_file = "results_test/buildings_prepared.geojson"
    if not os.path.exists(buildings_file):
        print("❌ Buildings file not found. Run example_2 first.")
        return

    buildings_gdf = gpd.read_file(buildings_file)

    # Show current CRS
    print(f"Current CRS: {buildings_gdf.crs}")

    # Convert to different CRS (e.g., Web Mercator for web mapping)
    web_mercator_crs = "EPSG:3857"
    buildings_web = crs_utils.ensure_projected_crs(buildings_gdf, web_mercator_crs, "Buildings")
    print(f"Converted to Web Mercator: {buildings_web.crs}")

    # Convert back to UTM
    utm_crs = "EPSG:32633"
    buildings_utm = crs_utils.ensure_projected_crs(buildings_web, utm_crs, "Buildings")
    print(f"Converted back to UTM: {buildings_utm.crs}")

    # Save with different CRS
    crs_utils.save_with_crs(buildings_utm, "results_test/buildings_utm_example.geojson")
    print("✅ Saved buildings with UTM CRS")


def example_4_batch_processing():
    """Example 4: Batch processing with CRS handling."""
    print("\n" + "=" * 60)
    print("Example 4: Batch Processing with CRS Handling")
    print("=" * 60)

    # Simulate processing multiple datasets
    datasets = [
        ("buildings_1", "results_test/buildings_prepared.geojson"),
        ("buildings_2", "results_test/buildings_prepared.geojson"),  # Same file for demo
    ]

    target_crs = "EPSG:32633"  # UTM Zone 33N

    for name, file_path in datasets:
        if os.path.exists(file_path):
            print(f"Processing {name}...")
            gdf = gpd.read_file(file_path)

            # Check if conversion needed
            info = crs_utils.check_crs_info(gdf, name)
            if info["needs_conversion"]:
                gdf = crs_utils.ensure_projected_crs(gdf, target_crs, name)
                print(f"  ✅ Converted {name} to {target_crs}")
            else:
                print(f"  ✅ {name} already in projected CRS")
        else:
            print(f"  ❌ File not found: {file_path}")


def main():
    """Run all examples."""
    print("🔍 CRS Utilities Examples for Branitz Energy Decision AI")
    print("=" * 60)

    # Check if we have the required environment
    try:
        import geopandas as gpd

        print("✅ GeoPandas available")
    except ImportError:
        print("❌ GeoPandas not available. Please install it first.")
        return

    # Run examples
    example_1_basic_crs_check()
    example_2_load_and_prepare()
    example_3_custom_crs_conversion()
    example_4_batch_processing()

    print("\n" + "=" * 60)
    print("🎉 All examples completed!")
    print("=" * 60)
    print("\nKey takeaways:")
    print("1. Always check CRS before distance calculations")
    print("2. Use projected CRS (like UTM) for accurate measurements")
    print("3. Ensure both datasets use the same CRS")
    print("4. The crs_utils module handles all the complexity for you")


if __name__ == "__main__":
    main()
