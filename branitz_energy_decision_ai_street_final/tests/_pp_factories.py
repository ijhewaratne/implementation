"""
Pandapower factory functions for testing LV feeder analysis.
"""

def build_simple_lv_feeder():
    """
    Build a simple LV feeder network for testing.
    
    Returns:
        dict: FeederModel with keys: net, lv_bus, rating_mva
    """
    import pandapower as pp
    
    net = pp.create_empty_network(sn_mva=0.4)  # LV base
    
    # Create buses
    bus_hv = pp.create_bus(net, vn_kv=20.0, name="MV")
    bus_lv = pp.create_bus(net, vn_kv=0.4, name="LV")
    bus_l1 = pp.create_bus(net, vn_kv=0.4, name="L1")
    
    # Create external grid (slack bus)
    pp.create_ext_grid(net, bus=bus_hv)
    
    # Create transformer
    pp.create_transformer_from_parameters(
        net, hv_bus=bus_hv, lv_bus=bus_lv, sn_mva=0.4, 
        vn_hv_kv=20.0, vn_lv_kv=0.4,
        vk_percent=6.0, vkr_percent=0.8, pfe_kw=0.5, i0_percent=0.2
    )
    
    # Create LV line
    pp.create_line_from_parameters(
        net, from_bus=bus_lv, to_bus=bus_l1,
        length_km=0.05, r_ohm_per_km=0.4, x_ohm_per_km=0.08, 
        c_nf_per_km=220, max_i_ka=0.6
    )
    
    return dict(net=net, lv_bus=bus_l1, rating_mva=0.4) 