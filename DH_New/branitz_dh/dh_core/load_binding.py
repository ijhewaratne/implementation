import pandas as pd, geopandas as gpd

def load_design_loads_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    assert {"building_id","Q_design_kW"}.issubset(df.columns)
    df["building_id"] = df["building_id"].astype(str)
    return df

def match_loads_to_addresses_by_roundrobin(loads_df: pd.DataFrame,
                                           addr_gdf: gpd.GeoDataFrame,
                                           n_points: int = 200) -> gpd.GeoDataFrame:
    """
    Temporary binder because building_id != address oid in your data.
    Distributes loads across the first n_points address markers, with each load
    distributed to multiple addresses for better network coverage.
    """
    addr = addr_gdf.copy()
    if len(addr) > n_points:
        addr = addr.iloc[:n_points].copy()
    addr["Q_design_kW"] = 0.0
    if len(addr)==0 or len(loads_df)==0: 
        return addr
    
    # Distribute each load across multiple addresses
    total_load = loads_df["Q_design_kW"].sum()
    load_per_address = total_load / len(addr)
    
    # Assign equal load to each address
    addr["Q_design_kW"] = load_per_address
    
    return addr