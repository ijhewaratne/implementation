"""
ETL Pipeline: Data16122024 to LoadForecastingAgent (LFA)

Configurable ETL pipeline that converts building data and weather data from the data16122024 dataset
into the exact format required by the LoadForecastingAgent, including physics features and optional synthetic labels.
"""

import json
import logging
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import argparse
import warnings

# Import graph utilities
from .graph_utils import load_graph, snap_buildings_to_graph, compute_topology_features

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load ETL configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        Dictionary with ETL configuration
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded ETL configuration from: {config_path}")
    return config


def load_buildings(src: Union[str, Path], config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load and normalize building data using configurable column mapping.
    
    Args:
        src: Path to building data file
        config: ETL configuration
        
    Returns:
        DataFrame with normalized building data
    """
    src_path = Path(src)
    logger.info(f"Loading building data from: {src_path}")
    
    # Load data based on file type
    if src_path.suffix.lower() in ['.json', '.geojson']:
        with open(src_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, dict) and any(isinstance(v, dict) for v in data.values()):
            # Object-based JSON
            buildings = []
            for building_id, building_data in data.items():
                building_data['building_id'] = building_id
                buildings.append(building_data)
            df = pd.DataFrame(buildings)
        elif 'features' in data:  # GeoJSON
            buildings = []
            for feature in data['features']:
                building = feature.get('properties', {})
                building['geometry'] = feature.get('geometry', {})
                buildings.append(building)
            df = pd.DataFrame(buildings)
        else:  # Array-based JSON
            df = pd.DataFrame(data)
    else:
        # Load CSV
        df = pd.read_csv(src_path)
    
    logger.info(f"Loaded {len(df)} buildings")
    return normalize_building_data(df, config)


def normalize_building_data(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Normalize building data using configurable column mapping.
    
    Args:
        df: Raw building DataFrame
        config: ETL configuration
        
    Returns:
        Normalized building DataFrame
    """
    logger.info("Normalizing building data...")
    
    # Get column mappings
    column_map = config.get('buildings_columns', {})
    defaults = config.get('defaults', {})
    
    # Create normalized DataFrame
    normalized = pd.DataFrame()
    
    # Apply column mappings
    for target_col, source_col in column_map.items():
        if source_col in df.columns:
            normalized[target_col] = df[source_col]
            logger.debug(f"Mapped {source_col} -> {target_col}")
        else:
            # Check if there's a default value
            if target_col in defaults:
                default_val = defaults[target_col]
                normalized[target_col] = pd.Series([default_val] * len(df))
                logger.warning(f"Column {source_col} not found, using default {default_val} for {target_col}")
            else:
                logger.warning(f"Column {source_col} not found and no default for {target_col}")
    
    # Validate required fields
    required_fields = ['id', 'function', 'floor_area']
    missing_fields = [field for field in required_fields if field not in normalized.columns or normalized[field].isna().all()]
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    # Handle special cases
    if 'window_area' not in normalized.columns and 'window_share' in normalized.columns and 'wall_area' in normalized.columns:
        # Compute window area from window share and wall area
        window_share = normalized['window_share'].fillna(0.15)
        window_share = window_share.clip(0, 0.6)  # Clamp to reasonable range
        normalized['window_area'] = window_share * normalized['wall_area']
        logger.info("Computed window_area from window_share and wall_area")
    
    if 'floor_area_ground' not in normalized.columns and 'floor_area' in normalized.columns:
        # Use floor_area as proxy for floor_area_ground
        normalized['floor_area_ground'] = normalized['floor_area']
        logger.warning("Using floor_area as proxy for floor_area_ground")
    
    logger.info(f"Normalized {len(normalized)} buildings")
    return normalized


def compute_physics(df_b: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Compute physics coefficients from building data.
    
    Args:
        df_b: Building DataFrame with U-values and areas
        config: ETL configuration
        
    Returns:
        DataFrame with added physics coefficients
    """
    logger.info("Computing physics coefficients...")
    
    df = df_b.copy()
    defaults = config.get('defaults', {})
    
    # Apply defaults for missing values
    for field, default_val in defaults.items():
        if field in df.columns and df[field].isna().any():
            df[field] = df[field].fillna(default_val)
            logger.info(f"Applied default {default_val} for missing {field}")
    
    # Ensure all required areas exist
    if 'wall_area' not in df.columns or df['wall_area'].isna().any():
        logger.warning("Computing wall areas from floor area and height")
        height = df.get('height', defaults.get('height', 3.0))
        df['wall_area'] = df['floor_area'] * 2.5  # Rough estimate
    
    if 'roof_area' not in df.columns or df['roof_area'].isna().any():
        logger.warning("Computing roof areas from floor area")
        df['roof_area'] = df['floor_area'] * 1.1  # Slightly larger than floor
    
    if 'volume' not in df.columns or df['volume'].isna().any():
        logger.warning("Computing volumes from floor area and height")
        height = df.get('height', defaults.get('height', 3.0))
        df['volume'] = df['floor_area'] * height
    
    if 'window_area' not in df.columns or df['window_area'].isna().any():
        logger.warning("Computing window areas from floor area")
        window_ratio = df.get('window_share', defaults.get('window_share', 0.15))
        df['window_area'] = df['floor_area'] * window_ratio
    
    # Use floor_area_ground for floor U-value calculation if available
    floor_area_for_u = df.get('floor_area_ground', df['floor_area'])
    
    # Compute transmission heat loss coefficient H_tr
    df['H_tr'] = (
        df['wall_area'] * df['U_wall'] +
        df['roof_area'] * df['U_roof'] +
        floor_area_for_u * df['U_floor'] +
        df['window_area'] * df['U_window']
    )
    
    # Compute ventilation heat loss coefficient H_ve
    # 0.34 ≈ ρ·c_p of air in Wh/(m³K)
    air_exchange = df.get('n', defaults.get('air_change_n_per_h', 0.5))
    df['H_ve'] = df['volume'] * air_exchange * 0.34
    
    # Map renovation factor
    sanierungs_map = defaults.get('sanierungs_map', {
        'unsaniert': 1.00,
        'teilsaniert': 0.71,
        'vollsaniert': 0.30
    })
    df['sanierungs_faktor'] = df['sanierungszustand'].map(sanierungs_map).fillna(1.00)
    
    # Validate physics coefficients
    if (df['H_tr'] <= 0).any():
        logger.warning("Some buildings have non-positive H_tr values")
        df['H_tr'] = df['H_tr'].replace([np.inf, -np.inf], np.nan).fillna(100.0)  # Sensible default
    
    if (df['H_ve'] <= 0).any():
        logger.warning("Some buildings have non-positive H_ve values")
        df['H_ve'] = df['H_ve'].replace([np.inf, -np.inf], np.nan).fillna(10.0)  # Sensible default
    
    logger.info("Physics coefficients computed successfully")
    return df


def write_buildings_parquet(df_b: pd.DataFrame, out_path: str = "data/processed/buildings.parquet") -> None:
    """
    Write building data to parquet file.
    
    Args:
        df_b: Building DataFrame
        out_path: Output file path
    """
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure deterministic sorting
    df_b = df_b.sort_values('id').reset_index(drop=True)
    
    df_b.to_parquet(out_file, index=False)
    logger.info(f"Building data written to: {out_file}")


def build_weather(src: Union[str, Path], config: Dict[str, Any], 
                  out_path: str = "data/processed/weather.parquet") -> pd.DataFrame:
    """
    Build weather data for the specified year.
    
    Args:
        src: Path to weather data file
        config: ETL configuration
        out_path: Output file path
        
    Returns:
        Weather DataFrame with 8760 hourly rows
    """
    logger.info(f"Building weather data from: {src}")
    
    src_path = Path(src)
    
    if src_path.suffix.lower() == '.dat':
        # Handle TRY weather data format
        weather_df = _parse_try_weather(src_path, config)
    elif src_path.suffix.lower() == '.csv':
        # Load CSV weather data
        weather_df = pd.read_csv(src_path)
        
        # Apply column mapping
        column_map = config.get('weather_columns', {})
        for target_col, source_col in column_map.items():
            if source_col in weather_df.columns:
                weather_df[target_col] = weather_df[source_col]
    else:
        raise ValueError(f"Unsupported weather file format: {src_path.suffix}")
    
    # Ensure timestamp column exists and is datetime
    if 'timestamp' not in weather_df.columns:
        if 'date' in weather_df.columns:
            weather_df['timestamp'] = pd.to_datetime(weather_df['date'])
        elif 'time' in weather_df.columns:
            weather_df['timestamp'] = pd.to_datetime(weather_df['time'])
        else:
            # Create hourly timestamps for the year
            year = datetime.now().year
            start_date = datetime(year, 1, 1)
            weather_df['timestamp'] = pd.date_range(start=start_date, periods=8760, freq='H')
    
    # Ensure we have exactly 8760 rows
    if len(weather_df) != 8760:
        if len(weather_df) > 8760:
            # Handle leap year - drop February 29
            weather_df = weather_df[~((weather_df['timestamp'].dt.month == 2) & 
                                    (weather_df['timestamp'].dt.day == 29))]
            if len(weather_df) != 8760:
                raise ValueError(f"Could not adjust to 8760 hours. Current: {len(weather_df)}")
        else:
            logger.warning(f"Weather data has {len(weather_df)} rows, interpolating to 8760")
            weather_df = _interpolate_weather_to_8760(weather_df)
    
    # Ensure required columns exist
    if 'T_out' not in weather_df.columns:
        raise ValueError("Temperature column (T_out) not found in weather data")
    
    # Fill missing optional columns
    if 'RH' not in weather_df.columns:
        weather_df['RH'] = 60.0  # Default relative humidity
    if 'GHI' not in weather_df.columns:
        weather_df['GHI'] = 0.0  # Default global horizontal irradiance
    
    # Validate data
    if weather_df['T_out'].isna().any():
        logger.warning("Filling missing temperature values")
        weather_df['T_out'] = weather_df['T_out'].interpolate(method='linear')
    
    # Ensure monotonic timestamps
    weather_df = weather_df.sort_values('timestamp').reset_index(drop=True)
    
    # Write to parquet
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    weather_df.to_parquet(out_file, index=False)
    
    logger.info(f"Weather data written to: {out_file}")
    return weather_df


def _parse_try_weather(try_path: Path, config: Dict[str, Any]) -> pd.DataFrame:
    """Parse TRY weather data format."""
    logger.info(f"Parsing TRY weather data: {try_path}")
    
    # Read the header to understand the format
    with open(try_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the data section (skip header lines)
    data_lines = []
    for line in lines:
        if line.strip() and not line.startswith('Koordinatensystem') and not line.startswith('Format:'):
            try:
                # Parse fixed-width format
                parts = line.strip().split()
                if len(parts) >= 6:  # At least year, month, day, hour, temperature
                    data_lines.append(parts)
            except:
                continue
    
    # Convert to DataFrame
    weather_data = []
    for parts in data_lines:
        if len(parts) >= 6:
            try:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                hour = int(parts[3])
                temperature = float(parts[4])
                
                timestamp = datetime(year, month, day, hour)
                weather_data.append({
                    'timestamp': timestamp,
                    'T_out': temperature,
                    'RH': 60.0,  # Default
                    'GHI': 0.0   # Default
                })
            except (ValueError, IndexError):
                continue
    
    df = pd.DataFrame(weather_data)
    logger.info(f"Parsed {len(df)} weather records")
    return df


def _interpolate_weather_to_8760(df: pd.DataFrame) -> pd.DataFrame:
    """Interpolate weather data to exactly 8760 hourly rows."""
    # Create target hourly timestamps
    start_date = datetime(df['timestamp'].dt.year.iloc[0], 1, 1)
    target_timestamps = pd.date_range(start=start_date, periods=8760, freq='H')
    
    # Set timestamp as index for interpolation
    df = df.set_index('timestamp')
    
    # Reindex to target timestamps and interpolate
    df_interpolated = df.reindex(target_timestamps).interpolate(method='linear')
    
    # Reset index to get timestamp as column
    df_interpolated = df_interpolated.reset_index().rename(columns={'index': 'timestamp'})
    
    return df_interpolated


def synthesize_labels(df_b: pd.DataFrame, weather_df: pd.DataFrame, out_dir: str = "data/interim/meters") -> None:
    """
    Generate synthetic heat demand labels using DIN-style physics.
    
    Args:
        df_b: Building DataFrame with physics coefficients
        weather_df: Weather DataFrame with hourly temperatures
        out_dir: Output directory for meter data
    """
    logger.info("Generating synthetic heat demand labels...")
    
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Ensure weather data has timestamp index
    if 'timestamp' not in weather_df.columns:
        raise ValueError("Weather data must have 'timestamp' column")
    
    weather_df = weather_df.set_index('timestamp')
    
    for _, building in df_b.iterrows():
        building_id = building['id']
        
        # Compute hourly heat demand using DIN formula
        # P_h(t) = (H_tr + H_ve) * (T_in - T_out(t)) * sanierungs_faktor
        T_in = building['T_in']
        H_tr = building['H_tr']
        H_ve = building['H_ve']
        sanierungs_faktor = building['sanierungs_faktor']
        
        # Calculate heat demand for each hour
        heat_demand = []
        for timestamp, row in weather_df.iterrows():
            T_out = row['T_out']
            
            # DIN heat demand formula (in W)
            P_h = (H_tr + H_ve) * (T_in - T_out) * sanierungs_faktor
            
            # Clip at 0 (no cooling) and convert to kW
            P_h = max(0.0, P_h) / 1000.0
            
            heat_demand.append({
                'timestamp': timestamp,
                'demand_kw': P_h
            })
        
        # Create DataFrame and save
        demand_df = pd.DataFrame(heat_demand)
        building_file = out_path / f"{building_id}.parquet"
        demand_df.to_parquet(building_file, index=False)
        
        logger.debug(f"Generated labels for building {building_id}")
    
    logger.info(f"Synthetic labels written to: {out_path}")


def main():
    """Main ETL pipeline function."""
    parser = argparse.ArgumentParser(description="ETL Pipeline: Data16122024 to LoadForecastingAgent")
    parser.add_argument("--buildings", required=True, help="Path to building data file")
    parser.add_argument("--weather", required=True, help="Path to weather data file")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--write-meters", action='store_true', help="Generate synthetic meter data")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory")
    parser.add_argument("--nodes", help="Path to network nodes CSV file")
    parser.add_argument("--edges", help="Path to network edges CSV file")
    parser.add_argument("--links", help="Path to building-node links CSV file")
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Load and process building data
        buildings_df = load_buildings(args.buildings, config)
        buildings_df = compute_physics(buildings_df, config)
        
        # Process graph topology if network data is available
        if args.nodes and args.edges:
            logger.info("Processing network topology features...")
            try:
                # Load network graph
                G = load_graph(args.nodes, args.edges)
                
                # Snap buildings to graph
                buildings_df = snap_buildings_to_graph(buildings_df, G, args.links)
                
                # Get substation nodes
                substation_nodes = set()
                for node_id, attrs in G.nodes(data=True):
                    if attrs.get('type') == 'substation':
                        substation_nodes.add(node_id)
                
                if not substation_nodes:
                    logger.warning("No substation nodes found in network")
                else:
                    logger.info(f"Found {len(substation_nodes)} substation nodes")
                    
                    # Compute topology features
                    topology_df = compute_topology_features(buildings_df, G, substation_nodes)
                    
                    if not topology_df.empty:
                        # Merge topology features with building data
                        buildings_df = buildings_df.merge(topology_df, on='id', how='left')
                        logger.info("Topology features added to building data")
                    else:
                        logger.warning("No topology features computed")
                        
            except Exception as e:
                logger.error(f"Error processing network topology: {e}")
                logger.info("Continuing without topology features")
        
        # Write building data
        buildings_path = Path(args.output_dir) / "buildings.parquet"
        write_buildings_parquet(buildings_df, str(buildings_path))
        
        # Process weather data
        weather_path = Path(args.output_dir) / "weather.parquet"
        weather_df = build_weather(args.weather, config, str(weather_path))
        
        # Generate synthetic labels if requested
        if args.write_meters:
            meters_dir = Path(args.output_dir).parent / "interim" / "meters"
            synthesize_labels(buildings_df, weather_df, str(meters_dir))
        
        logger.info("ETL pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
