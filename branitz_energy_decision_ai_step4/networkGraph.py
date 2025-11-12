import networkx as nx
import matplotlib.pyplot as plt
import shapely.wkt

graphml_file = "results/branitz_network.graphml"
output_image = "branitz_network_plot.png"

G = nx.read_graphml(graphml_file)

# Build position dictionary (only nodes with valid Point geometry)
pos = {}
for n, data in G.nodes(data=True):
    geom_wkt = data.get('geometry')
    if geom_wkt:
        try:
            geom = shapely.wkt.loads(geom_wkt)
            if hasattr(geom, 'x') and hasattr(geom, 'y'):
                pos[n] = (geom.x, geom.y)
        except Exception:
            continue



nodelist = list(pos.keys())
edges_to_draw = [(u, v) for u, v in G.edges() if u in pos and v in pos]
print(f"Total edges in graph: {G.number_of_edges()}")
print(f"Edges with both endpoints having position: {len(edges_to_draw)}")

plt.figure(figsize=(12, 12))
nx.draw_networkx_edges(G, pos, edgelist=edges_to_draw, edge_color='gray', alpha=0.3)
nx.draw_networkx_nodes(G, pos, nodelist=nodelist, node_size=5, node_color='blue', alpha=0.7)
plt.title("Branitz Network: Nodes and Edges")
plt.axis("equal")

# Save to file
plt.savefig(output_image, dpi=300, bbox_inches='tight')
print(f"Network plot saved as {output_image}")

plt.show()
