import osmnx as ox
import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString

# keep OSMnx friendly
ox.settings.use_cache = True
ox.settings.log_console = False
ox.settings.timeout = 180

def _undirect_with_lengths(Gd: nx.MultiDiGraph) -> nx.Graph:
    """
    Convert an OSMnx MultiDiGraph (directed) into an undirected Graph.
    - copy node x/y so we can emit LineStrings
    - for parallel edges keep the shortest 'length'
    - PRESERVE graph attrs incl. CRS (fixes KeyError: 'crs')
    """
    H = nx.Graph()
    # copy graph-level attributes (including CRS)
    H.graph.update(Gd.graph)
    if "crs" not in H.graph:
        H.graph["crs"] = "epsg:4326"

    # copy nodes with coordinates
    for n, data in Gd.nodes(data=True):
        H.add_node(n, x=data.get("x"), y=data.get("y"))

    # collapse edges, keep shortest length
    for u, v, data in Gd.edges(data=True):
        w = data.get("length", 1.0)
        if H.has_edge(u, v):
            if w < H[u][v].get("length", w):
                H[u][v]["length"] = w
        else:
            H.add_edge(u, v, length=w)
    return H

def build_street_graph_around(points_wgs: gpd.GeoDataFrame, dist_m: int = 1500) -> nx.Graph:
    """Download a street graph around your points and return an undirected, length-weighted graph."""
    if points_wgs.empty:
        raise ValueError("No points supplied to build_street_graph_around")
    if points_wgs.crs is None:
        # we expect WGS84 lon/lat here
        points_wgs = points_wgs.set_crs(4326, allow_override=True)
    center = points_wgs.unary_union.convex_hull.centroid
    # drive_service works well for utility planning
    Gd = ox.graph_from_point((center.y, center.x), dist=dist_m, network_type="drive_service", simplify=True)
    return _undirect_with_lengths(Gd)

def snap_points_to_graph(G: nx.Graph, pts: gpd.GeoSeries) -> list[int]:
    """Return nearest node ids for each point (X=lon, Y=lat)."""
    xs = [pt.x for pt in pts.to_list()]
    ys = [pt.y for pt in pts.to_list()]
    return [ox.distance.nearest_nodes(G, X=x, Y=y) for x, y in zip(xs, ys)]

def _steiner_tree(G: nx.Graph, required: set[int]) -> nx.Graph:
    """Steiner tree over required nodes with 'length' weights."""
    for u, v, d in G.edges(data=True):
        if "length" not in d:
            d["length"] = 1.0
    from networkx.algorithms.approximation import steiner_tree
    return steiner_tree(G, terminals=required, weight="length")

def _tree_to_gdf(Gt: nx.Graph) -> gpd.GeoDataFrame:
    rows = []
    for u, v, d in Gt.edges(data=True):
        pu, pv = Gt.nodes[u], Gt.nodes[v]
        rows.append({
            "geometry": LineString([(pu["x"], pu["y"]), (pv["x"], pv["y"])]),
            "length_m": d.get("length", 0.0)
        })
    return gpd.GeoDataFrame(rows, crs="EPSG:4326")

def route_pipes_from_osm(addresses_wgs: gpd.GeoDataFrame,
                         plant_latlon: tuple[float, float],
                         take_n: int = 200,
                         dist_m: int = 1500) -> gpd.GeoDataFrame:
    """
    Build a street-hugging backbone from the plant to a subset of consumer points.
    Returns WGS84 LineStrings with a nominal diameter column.
    """
    if addresses_wgs.crs is None:
        addresses_wgs = addresses_wgs.set_crs(4326, allow_override=True)

    addrs = addresses_wgs.head(max(1, take_n)).copy()
    G = build_street_graph_around(addrs, dist_m=dist_m)

    consumers = snap_points_to_graph(G, addrs.geometry)
    plant_node = ox.distance.nearest_nodes(G, X=float(plant_latlon[1]), Y=float(plant_latlon[0]))

    required = set(consumers) | {plant_node}
    Gt = _steiner_tree(G, required)

    pipes = _tree_to_gdf(Gt)
    pipes["diameter_m"] = 0.15  # nominal until we size hydraulically
    return pipes
