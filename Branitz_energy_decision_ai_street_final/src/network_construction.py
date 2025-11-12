# src/network_construction.py

import networkx as nx
import pandas as pd


def create_network_graph(buildings, street_edges_gdf, street_nodes_gdf, output_graphml=None):
    """
    Build the networkx graph for the street/energy system.
    This corrected version uses the standard 'u' and 'v' columns for edges
    and ensures data is cleaned for GraphML export.

    - buildings: GeoDataFrame (unused in this function but kept for API consistency)
    - street_edges_gdf: GeoDataFrame of street segments (edges)
    - street_nodes_gdf: GeoDataFrame of street intersections (nodes)
    - output_graphml: Optional filename to save the graph.
    Returns: networkx.Graph
    """
    G = nx.Graph()

    # 1. Add nodes from the nodes GeoDataFrame
    # A 'osmid' column is required for unique node identification.
    if "osmid" not in street_nodes_gdf.columns:
        raise ValueError("Street nodes GeoDataFrame must contain an 'osmid' column.")

    for _, row in street_nodes_gdf.iterrows():
        # Build a dictionary of node attributes, excluding the geometry object
        node_attrs = {k: v for k, v in row.items() if k != "geometry"}
        # Explicitly add x and y coordinates from the geometry
        node_attrs["x"] = row.geometry.x
        node_attrs["y"] = row.geometry.y
        G.add_node(row["osmid"], **node_attrs)

    # 2. Add edges using 'u' and 'v' columns
    # This is the primary fix. The original code incorrectly looked for 'from' and 'to'.
    if "u" not in street_edges_gdf.columns or "v" not in street_edges_gdf.columns:
        error_msg = (
            "The street edges GeoDataFrame is missing 'u' or 'v' columns, which are required "
            "to identify the start and end nodes of each street segment. Please ensure the "
            "'data_preparation.py' script generates these columns."
        )
        raise ValueError(error_msg)

    for _, edge_row in street_edges_gdf.iterrows():
        start_node = edge_row["u"]
        end_node = edge_row["v"]

        # Safety check: ensure both nodes exist in the graph before adding the edge
        if G.has_node(start_node) and G.has_node(end_node):
            # Exclude geometry and node identifiers from edge attributes
            edge_attrs = {k: v for k, v in edge_row.items() if k not in ["geometry", "u", "v"]}
            # Ensure edge length from geometry is included if not already present
            if "length" not in edge_attrs:
                edge_attrs["length"] = edge_row.geometry.length

            G.add_edge(start_node, end_node, **edge_attrs)

    # 3. Save the graph if an output path is provided
    if output_graphml:
        # Clean attributes for GraphML compatibility, removing None or NaN values
        for _, data in G.nodes(data=True):
            for k, v in list(data.items()):
                if pd.isna(v):
                    data.pop(k)  # Remove the attribute if the value is null

        for _, _, data in G.edges(data=True):
            for k, v in list(data.items()):
                if pd.isna(v):
                    data.pop(k)  # Remove the attribute if the value is null

        nx.write_graphml(G, output_graphml)
        print(
            f"Successfully created network graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges."
        )

    return G
