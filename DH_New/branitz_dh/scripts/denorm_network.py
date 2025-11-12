import json, sys, geopandas as gpd
from shapely.geometry import LineString

src = "data/inputs/network_data.json"
dst = "data/inputs/network_denorm.geojson"
if len(sys.argv) > 1: src = sys.argv[1]
if len(sys.argv) > 2: dst = sys.argv[2]

data = json.load(open(src, "r", encoding="utf-8"))
rows = []
b = (data.get("metadata", {}) or {}).get("original_bounds", {})
x0,x1,y0,y1 = b.get("x_min"), b.get("x_max"), b.get("y_min"), b.get("y_max")
def dx(x): return x0 + float(x)*(x1-x0) if x0 is not None else float(x)
def dy(y): return y0 + float(y)*(y1-y0) if y0 is not None else float(y)

# Handle both "pipes" and "nodes/edges" structures
if "pipes" in data:
    for p in data["pipes"]:
        fx,fy = p["from"]["x"], p["from"]["y"]
        tx,ty = p["to"]["x"],   p["to"]["y"]
        rows.append({
            "diameter_m": p.get("diameter"),
            "p_from": p.get("pressure_from"),
            "p_to":   p.get("pressure_to"),
            "pressure_gradient": p.get("pressure_gradient"),
            "vel_ms": p.get("velocity"),
            "geometry": LineString([(dx(fx),dy(fy)), (dx(tx),dy(ty))])
        })
elif "nodes" in data and "edges" in data:
    nodes = {n["id"]: (float(n["x"]), float(n["y"])) for n in data["nodes"]}
    for e in data["edges"]:
        sx, sy = nodes[e["source"]]
        tx, ty = nodes[e["target"]]
        rows.append({
            "diameter_m": e.get("diameter"),
            "p_from": e.get("p_from"),
            "p_to":   e.get("p_to"),
            "pressure_gradient": e.get("pressure_gradient"),
            "vel_ms": e.get("velocity"),
            "geometry": LineString([(dx(sx),dy(sy)), (dx(tx),dy(ty))])
        })
else:
    print("Error: Unknown JSON structure. Expected 'pipes' or 'nodes/edges'.")
    sys.exit(1)
gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
gdf.to_file(dst, driver="GeoJSON")
print(f"Wrote {len(gdf)} lines to {dst}; bounds:", gdf.total_bounds)
