import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.ops import nearest_points
from shapely.geometry import LineString

import os
import argparse


def main():
    # Parse command line arguments for output directory
    parser = argparse.ArgumentParser(description="Generate network visualization")
    parser.add_argument(
        "--output_dir", default="results_test/", help="Output directory for results"
    )
    args = parser.parse_args()

    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        print(f"Error: Output directory '{output_dir}' does not exist.")
        return

    # --- Part 1: Load Your Data Files ---

    # Load the building footprints
    buildings_file = os.path.join(output_dir, "buildings_prepared.geojson")
    if not os.path.exists(buildings_file):
        print(f"Error: Buildings file not found at '{buildings_file}'")
        return

    buildings_gdf = gpd.read_file(buildings_file)

    # Load the street map file
    street_filepath = os.path.join(output_dir, "streets.geojson")

    try:
        street_gdf = gpd.read_file(street_filepath)
    except Exception as e:
        print(f"Error loading street file: {e}")
        print("Please make sure the path is correct and the file exists.")
        return

    # Proceed only if both files were loaded successfully
    if buildings_gdf.empty:
        print("Error: Buildings file is empty.")
        return

    # --- Part 2: Prepare Data and Calculate Network ---

    # Project both layers to the same projected CRS for accuracy
    print(f"Projecting layers to a suitable local CRS...")
    utm_crs = buildings_gdf.estimate_utm_crs()
    buildings_proj = buildings_gdf.to_crs(utm_crs)
    street_proj = street_gdf.to_crs(utm_crs)
    print(f"Layers projected to: {utm_crs}")

    # Combine all street segments into one continuous line for calculations
    street_line = street_proj.geometry.union_all()

    # Calculate the service line connections
    connection_lines = []
    for _, building in buildings_proj.iterrows():
        building_polygon = building.geometry

        # Find the two nearest points between the building edge and the street line
        p_building, p_street = nearest_points(building_polygon, street_line)

        # Create a line connecting these two points
        connection_lines.append(LineString([p_building, p_street]))

    # Create a new GeoDataFrame for the connection lines
    connections_gdf = gpd.GeoDataFrame(geometry=connection_lines, crs=utm_crs)
    print(f"Successfully calculated {len(connections_gdf)} service connections.")

    # --- Part 3: Plot Everything on the Map ---

    fig, ax = plt.subplots(figsize=(12, 12))

    # Plot layers from bottom to top by controlling the call order

    # 1. Plot the main street line (bottom layer)
    street_proj.plot(ax=ax, color="black", linewidth=3, label="Main Street")

    # 2. Plot buildings on top of the street
    buildings_proj.plot(ax=ax, color="lightgrey", edgecolor="black")

    # 3. Plot the new service connection lines on top of buildings
    connections_gdf.plot(ax=ax, color="red", linewidth=1.5, label="Service Connections")

    ax.set_title("Network Connections from Buildings to Street")
    ax.set_axis_off()
    ax.set_aspect("equal", adjustable="box")  # Ensure correct aspect ratio
    plt.legend()
    plt.tight_layout()

    # Save the plot
    plot_filename = os.path.join(output_dir, "network_visualization.png")
    plt.savefig(plot_filename, dpi=300, bbox_inches="tight")
    print(f"Network visualization saved to: {plot_filename}")

    # Also save as PDF for vector format
    pdf_filename = os.path.join(output_dir, "network_visualization.pdf")
    plt.savefig(pdf_filename, bbox_inches="tight")
    print(f"Network visualization saved to: {pdf_filename}")

    plt.show()

    # --- Part 4: Export the Network for JOSM (see Part 2 of explanation) ---

    # Define output file paths
    output_connections_path = os.path.join(output_dir, "service_connections.geojson")
    output_buildings_path = os.path.join(output_dir, "buildings_projected.geojson")
    output_street_path = os.path.join(output_dir, "street_projected.geojson")

    # Export the calculated connection lines
    connections_gdf.to_file(output_connections_path, driver="GeoJSON")

    # Also export the projected buildings and street for context in JOSM
    buildings_proj.to_file(output_buildings_path, driver="GeoJSON")
    street_proj.to_file(output_street_path, driver="GeoJSON")

    print(f"\nSuccessfully exported network files for JOSM:")
    print(f"- Connections: {output_connections_path}")
    print(f"- Buildings: {output_buildings_path}")
    print(f"- Street: {output_street_path}")


if __name__ == "__main__":
    main()
