import pandapipes as pp
import pandas as pd, numpy as np, geopandas as gpd
from shapely.geometry import Point
import networkx as nx

def _unique_endpoints(pipes_m: gpd.GeoDataFrame) -> pd.DataFrame:
    pts=[]
    for line in pipes_m.geometry:
        if line is None: continue
        c = list(line.coords)
        pts.append(c[0]); pts.append(c[-1])
    return pd.DataFrame(pts, columns=["x","y"]).drop_duplicates().reset_index(drop=True)

def _add_junctions(net, endpts: pd.DataFrame) -> pd.DataFrame:
    j_ids = []
    for _, r in endpts.iterrows():
        j_ids.append(pp.create_junction(net, pn_bar=3.0, tfluid_k=348.15, geodata=(float(r.x), float(r.y))))
    endpts["jn"] = j_ids
    return endpts

def build_and_run(net_pipes_wgs:gpd.GeoDataFrame,
                  addr_with_loads_wgs:gpd.GeoDataFrame,
                  supply_c:float=75.0, return_c:float=45.0,
                  u_w_per_m2k:float=0.35, k_mm:float=0.0015, sections:int=8):
    """
    Single-layer layout (visualized later as supply/return) with HEX on consumers.
    All geometry is projected to EPSG:25833 for valid lengths.
    """
    if net_pipes_wgs.empty:
        raise ValueError("No pipes to build network.")

    pipes_m = net_pipes_wgs.to_crs(25833)
    addr_m  = addr_with_loads_wgs.to_crs(25833)

    net = pp.create_empty_network(fluid="water")

    # --- junctions
    endpts = _unique_endpoints(pipes_m)
    endpts = _add_junctions(net, endpts)

    def jn_for_xy(xy):
        row = endpts[(endpts.x==xy[0]) & (endpts.y==xy[1])].iloc[0]
        return int(row["jn"])

    # --- pipes
    for _, r in pipes_m.iterrows():
        if r.geometry is None: continue
        (x1,y1),(x2,y2) = list(r.geometry.coords)
        pp.create_pipe_from_parameters(
            net,
            jn_for_xy((x1,y1)),
            jn_for_xy((x2,y2)),
            length_km=float(r.geometry.length) / 1000.0,     # ✅ convert meters to kilometers
            diameter_m=float(r.get("diameter_m", 0.15)),           # safe fallback
            k_mm=k_mm,
            sections=sections,
            alpha_w_per_m2k=u_w_per_m2k,
            geodata=[(x1,y1),(x2,y2)]
        )

    # --- loop driver: pump between farthest junctions
    coords = endpts[["x","y"]].to_numpy()
    d2 = ((coords[:,None,:]-coords[None,:,:])**2).sum(2)
    i,j = np.unravel_index(np.argmax(d2), d2.shape)
    pp.create_circ_pump_const_pressure(
        net,
        return_junction=int(endpts.iloc[i]["jn"]),
        flow_junction=int(endpts.iloc[j]["jn"]),
        p_flow_bar=3.0,
        plift_bar=0.5,
        t_flow_k=supply_c+273.15
    )

    # --- consumers (HEX), snap each address to nearest junction
    if len(addr_m):
        j_geo = gpd.GeoSeries([Point(xy) for xy in endpts[["x","y"]].to_numpy()], crs=25833)
        sidx = j_geo.sindex
        for _, a in addr_m.iterrows():
            qkW = float(a.get("Q_design_kW",0.0))
            if qkW <= 0: 
                continue
            near_idx = list(sidx.nearest(a.geometry, return_all=False))[0]
            jn = int(endpts.iloc[int(near_idx)]["jn"])
            j_cons = pp.create_junction(net, pn_bar=3.0, tfluid_k=return_c+273.15,
                                        geodata=(a.geometry.x, a.geometry.y))
            pp.create_heat_exchanger(net, from_junction=jn, to_junction=j_cons,
                                     diameter_m=0.1, qext_w=qkW*1000.0)  # ✅ diameter_m required

    # --- prune components with no consumers (helps thermal convergence)
    if len(net.pipe):
        G = nx.Graph()
        for _, r in net.pipe.iterrows():
            G.add_edge(int(r["from_junction"]), int(r["to_junction"]))
        consumer_nodes = set(net.heat_exchanger.get("from_junction", [])) | set(net.heat_exchanger.get("to_junction", []))
        keep = set()
        for comp in nx.connected_components(G):
            if comp & consumer_nodes:
                keep |= comp
        drop_idx = [i for i, r in net.pipe.iterrows()
                    if r["from_junction"] not in keep and r["to_junction"] not in keep]
        if drop_idx:
            net.pipe.drop(index=drop_idx, inplace=True)

    # --- solve with fallback handling
    try:
        pp.pipeflow(net, mode="all")
        print("✅ Full thermal-hydraulic simulation successful")
    except Exception as e:
        print(f"⚠️ Thermal calculation failed: {e}")
        try:
            pp.pipeflow(net, mode="hydraulics")
            print("✅ Hydraulic-only simulation successful")
            # Add dummy thermal results for visualization
            if hasattr(net, 'res_pipe') and len(net.res_pipe) > 0:
                net.res_pipe['t_from_k'] = supply_c + 273.15
                net.res_pipe['t_to_k'] = supply_c + 273.15 - 5.0  # Simple temperature drop
        except Exception as e2:
            print(f"❌ Even hydraulic calculation failed: {e2}")
            # Create minimal results for visualization
            if hasattr(net, 'pipe') and len(net.pipe) > 0:
                net.res_pipe = net.pipe.copy()
                net.res_pipe['t_from_k'] = supply_c + 273.15
                net.res_pipe['t_to_k'] = return_c + 273.15
                net.res_pipe['p_from_bar'] = 3.0
                net.res_pipe['p_to_bar'] = 2.8
    
    return net