from __future__ import annotations
import pandas as pd
import pandapower as pp

def build_simple_feeder_net(v_kv: float = 0.4, length_km: float = 0.2,
                            r_ohm_per_km: float = 0.4, x_ohm_per_km: float = 0.08) -> pp.pandapowerNet:
    net = pp.create_empty_network()
    b_slack = pp.create_bus(net, vn_kv=v_kv)
    b_load  = pp.create_bus(net, vn_kv=v_kv)
    pp.create_ext_grid(net, bus=b_slack, vm_pu=1.0)
    pp.create_line_from_parameters(net, b_slack, b_load, length_km=length_km,
                                   r_ohm_per_km=r_ohm_per_km, x_ohm_per_km=x_ohm_per_km,
                                   c_nf_per_km=0.0, max_i_ka=0.4)
    pp.create_load(net, bus=b_load, p_mw=0.0, q_mvar=0.0, name="agg")
    return net

def run_loadflow_for_hours(feeder_loads: pd.DataFrame, v_limits: tuple[float,float]) -> pd.DataFrame:
    df = feeder_loads.copy()
    df["v_min_pu"] = 1.0; df["v_max_pu"] = 1.0
    for (feeder_id), grp in df.groupby("feeder_id"):
        net = build_simple_feeder_net()
        for h, row in grp.iterrows():
            net.load.at[0, "p_mw"] = float(row["p_kw"]) / 1000.0
            pp.runpp(net)
            vpu = net.res_bus["vm_pu"]
            df.at[h, "v_min_pu"] = float(vpu.min())
            df.at[h, "v_max_pu"] = float(vpu.max())
    return df
