"""
ETL Pipeline: Data to LoadForecastingAgent (LFA)

Converts building data and weather data into the exact format required by LFA,
including physics features and optional synthetic labels.
"""

import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_buildings(src: Union[str, Path]) -> pd.DataFrame:
    """
    Load and normalize building data from various formats.
    
    Args:
        src: Path to building data (JSON/GeoJSON/CSV)
        
    Returns:
        DataFrame with normalized building data
    """
    src_path = Path(src)
    logger.info(f"Loading building data from: {src_path}")
    
    if src_path.suffix.lower() in ['.json', '.geojson']:
        # Load JSON/GeoJSON
        with open(src_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if 'features' in data:  # GeoJSON
            buildings = []
            for feature in data['features']:
                building = feature.get('properties', {})
                building['geometry'] = feature.get('geometry', {})
                buildings.append(building)
            df = pd.DataFrame(buildings)
        else:  # Regular JSON
            df = pd.DataFrame(data)
    else:
        # Load CSV
        df = pd.read_csv(src_path)
    
    logger.info(f"Loaded {len(df)} buildings")
    return normalize_building_data(df)


def normalize_building_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize building data column names and extract required fields.
    
    Args:
        df: Raw building DataFrame
        
    Returns:
        Normalized building DataFrame
    """
    logger.info("Normalizing building data...")
    
    # Create normalized DataFrame
    normalized = pd.DataFrame()
    
    # Map building ID
    id_columns = ['oi', 'building_id', 'id', 'gebaeude_id']
    normalized['building_id'] = _extract_column(df, id_columns, 'building_id')
    
    # Map building function/type
    function_columns = ['gebaeudefunktion', 'building_function', 'function', 'type', 'nutzung']
    normalized['function'] = _extract_column(df, function_columns, 'function')
    
    # Map areas
    area_columns = ['nutzflaeche', 'floor_area', 'area', 'flaeche']
    normalized['floor_area'] = _extract_numeric_column(df, area_columns, 100.0)
    
    wall_area_columns = ['wandflaeche', 'wall_area', 'aussenwand_flaeche']
    normalized['wall_area'] = _extract_numeric_column(df, wall_area_columns, None)
    
    roof_area_columns = ['dachflaeche', 'roof_area', 'dach_flaeche']
    normalized['roof_area'] = _extract_numeric_column(df, roof_area_columns, None)
    
    # Map volumes and dimensions
    volume_columns = ['volumen', 'volume', 'raumvolumen']
    normalized['volume'] = _extract_numeric_column(df, volume_columns, None)
    
    height_columns = ['hoehe', 'height', 'gebaeudehoehe']
    normalized['height'] = _extract_numeric_column(df, height_columns, None)
    
    # Map U-values
    u_wall_columns = ['U_Aussenwand', 'u_wall', 'u_aussenwand', 'u_value_wall']
    normalized['U_Aussenwand'] = _extract_numeric_column(df, u_wall_columns, 1.5)
    
    u_roof_columns = ['U_Dach', 'u_roof', 'u_dach', 'u_value_roof']
    normalized['U_Dach'] = _extract_numeric_column(df, u_roof_columns, 0.3)
    
    u_floor_columns = ['U_Boden', 'u_floor', 'u_boden', 'u_value_floor']
    normalized['U_Boden'] = _extract_numeric_column(df, u_floor_columns, 0.5)
    
    u_window_columns = ['U_Fenster', 'u_window', 'u_fenster', 'u_value_window']
    normalized['U_Fenster'] = _extract_numeric_column(df, u_window_columns, 1.3)
    
    # Map window area ratio
    window_ratio_columns = ['fensterflaechenanteil', 'window_ratio', 'fenster_anteil']
    normalized['fensterflaechenanteil'] = _extract_numeric_column(df, window_ratio_columns, 0.15)
    
    # Map indoor temperature
    temp_columns = ['innentemperatur', 'indoor_temp', 't_in', 'room_temp']
    normalized['innentemperatur'] = _extract_numeric_column(df, temp_columns, 20.0)
    
    # Map air exchange rate
    air_exchange_columns = ['n', 'luftwechselrate', 'air_exchange', 'ventilation_rate']
    normalized['n'] = _extract_numeric_column(df, air_exchange_columns, 0.5)
    
    # Map renovation status
    renovation_columns = ['sanierungszustand', 'renovation_status', 'sanierung']
    normalized['sanierungszustand'] = _extract_column(df, renovation_columns, 'unsaniert')
    
    # Map year built
    year_columns = ['baujahr', 'year_built', 'construction_year', 'year']
    normalized['year'] = _extract_numeric_column(df, year_columns, 1990)
    
    # Validate required fields
    if normalized['building_id'].isna().any():
        raise ValueError("Missing building_id for some buildings")
    
    logger.info(f"Normalized {len(normalized)} buildings")
    return normalized


def _extract_column(df: pd.DataFrame, possible_names: List[str], default: str) -> pd.Series:
    """Extract column using multiple possible names."""
    for name in possible_names:
        if name in df.columns:
            return df[name]
    return pd.Series([default] * len(df))


def _extract_numeric_column(df: pd.DataFrame, possible_names: List[str], default: Optional[float]) -> pd.Series:
    """Extract numeric column using multiple possible names."""
    for name in possible_names:
        if name in df.columns:
            values = pd.to_numeric(df[name], errors='coerce')
            if not values.isna().all():
                return values.fillna(default)
    return pd.Series([default] * len(df))


def compute_physics(df_b: pd.DataFrame) -> pd.DataFrame:
    """
    Compute physics coefficients from building data.
    
    Args:
        df_b: Building DataFrame with U-values and areas
        
    Returns:
        DataFrame with added physics coefficients
    """
    logger.info("Computing physics coefficients...")
    
    df = df_b.copy()
    
    # Compute missing areas if needed
    if df['wall_area'].isna().any():
        logger.warning("Computing wall areas from floor area and height")
        df['wall_area'] = df['floor_area'] * 2.5  # Rough estimate
    
    if df['roof_area'].isna().any():
        logger.warning("Computing roof areas from floor area")
        df['roof_area'] = df['floor_area'] * 1.1  # Slightly larger than floor
    
    if df['volume'].isna().any():
        logger.warning("Computing volumes from floor area and height")
        df['volume'] = df['floor_area'] * df['height'].fillna(3.0)
    
    # Compute window areas
    df['window_area'] = df['floor_area'] * df['fensterflaechenanteil']
    
    # Compute transmission heat loss coefficient H_tr
    df['H_tr'] = (
        df['wall_area'] * df['U_Aussenwand'] +
        df['roof_area'] * df['U_Dach'] +
        df['floor_area'] * df['U_Boden'] +
        df['window_area'] * df['U_Fenster']
    )
    
    # Compute ventilation heat loss coefficient H_ve
    # 0.34 ≈ ρ·c_p of air in Wh/(m³K)
    df['H_ve'] = df['volume'] * df['n'] * 0.34
    
    # Map renovation factor
    renovation_map = {
        'unsaniert': 1.00,
        'teilsaniert': 0.71,
        'vollsaniert': 0.30
    }
    df['sanierungs_faktor'] = df['sanierungszustand'].map(renovation_map).fillna(1.00)
    
    # Validate physics coefficients
    if (df['H_tr'] <= 0).any():
        logger.warning("Some buildings have non-positive H_tr values")
    if (df['H_ve'] <= 0).any():
        logger.warning("Some buildings have non-positive H_ve values")
    
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
    
    df_b.to_parquet(out_file, index=False)
    logger.info(f"Building data written to: {out_file}")


def build_weather(try_path: Union[str, Path], year: int, out_path: str = "data/processed/weather.parquet") -> pd.DataFrame:
    """
    Build weather data for the specified year.
    
    Args:
        try_path: Path to TRY weather data
        year: Target year
        out_path: Output file path
        
    Returns:
        Weather DataFrame with 8760 hourly rows
    """
    logger.info(f"Building weather data for year {year}")
    
    try_path = Path(try_path)
    
    if try_path.suffix.lower() == '.csv':
        # Load CSV weather data
        weather_df = pd.read_csv(try_path)
        
        # Normalize column names
        column_mapping = {
            'T': 'T_out',
            'temperature': 'T_out',
            'temp': 'T_out',
            'humidity': 'RH',
            'relative_humidity': 'RH',
            'radiation': 'GHI',
            'global_radiation': 'GHI',
            'ghi': 'GHI'
        }
        
        weather_df = weather_df.rename(columns=column_mapping)
        
        # Ensure timestamp column exists
        if 'timestamp' not in weather_df.columns:
            if 'date' in weather_df.columns:
                weather_df['timestamp'] = pd.to_datetime(weather_df['date'])
            elif 'time' in weather_df.columns:
                weather_df['timestamp'] = pd.to_datetime(weather_df['time'])
            else:
                # Create hourly timestamps for the year
                start_date = datetime(year, 1, 1)
                weather_df['timestamp'] = pd.date_range(start=start_date, periods=8760, freq='H')
        
        # Ensure we have exactly 8760 rows
        if len(weather_df) != 8760:
            logger.warning(f"Weather data has {len(weather_df)} rows, interpolating to 8760")
            weather_df = _interpolate_weather_to_8760(weather_df, year)
        
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
        
    else:
        # Generate synthetic weather data if no file provided
        logger.warning("No weather file provided, generating synthetic data")
        weather_df = _generate_synthetic_weather(year)
    
    # Write to parquet
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    weather_df.to_parquet(out_file, index=False)
    
    logger.info(f"Weather data written to: {out_file}")
    return weather_df


def _interpolate_weather_to_8760(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Interpolate weather data to exactly 8760 hourly rows."""
    # Create target hourly timestamps
    start_date = datetime(year, 1, 1)
    target_timestamps = pd.date_range(start=start_date, periods=8760, freq='H')
    
    # Set timestamp as index for interpolation
    df = df.set_index('timestamp')
    
    # Reindex to target timestamps and interpolate
    df_interpolated = df.reindex(target_timestamps).interpolate(method='linear')
    
    # Reset index to get timestamp as column
    df_interpolated = df_interpolated.reset_index().rename(columns={'index': 'timestamp'})
    
    return df_interpolated


def _generate_synthetic_weather(year: int) -> pd.DataFrame:
    """Generate synthetic weather data for testing."""
    start_date = datetime(year, 1, 1)
    timestamps = pd.date_range(start=start_date, periods=8760, freq='H')
    
    # Simple temperature pattern
    hours = np.arange(8760)
    base_temp = 10.0  # Base temperature
    seasonal_variation = 10.0 * np.cos(2 * np.pi * hours / (24 * 365))  # Seasonal cycle
    daily_variation = 3.0 * np.cos(2 * np.pi * (hours % 24) / 24)  # Daily cycle
    noise = np.random.normal(0, 2, 8760)  # Random noise
    
    temperatures = base_temp + seasonal_variation + daily_variation + noise
    
    weather_data = {
        'timestamp': timestamps,
        'T_out': temperatures,
        'RH': 60.0 + 20.0 * np.sin(2 * np.pi * hours / (24 * 365)),  # Seasonal humidity
        'GHI': np.maximum(0, 500 * np.sin(np.pi * (hours % 24 - 6) / 12))  # Solar radiation
    }
    
    return pd.DataFrame(weather_data)


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
        building_id = building['building_id']
        
        # Compute hourly heat demand using DIN formula
        # P_h(t) = (H_tr + H_ve) * (T_in - T_out(t)) * sanierungs_faktor
        T_in = building['innentemperatur']
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
    parser = argparse.ArgumentParser(description="ETL Pipeline: Data to LoadForecastingAgent")
    parser.add_argument("--buildings", required=True, help="Path to building data file")
    parser.add_argument("--try", dest="try_path", help="Path to TRY weather data file")
    parser.add_argument("--year", type=int, default=2024, help="Target year for weather data")
    parser.add_argument("--write-meters", type=bool, default=False, help="Generate synthetic meter data")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory")
    
    args = parser.parse_args()
    
    try:
        # Load and process building data
        buildings_df = load_buildings(args.buildings)
        buildings_df = compute_physics(buildings_df)
        
        # Write building data
        buildings_path = Path(args.output_dir) / "buildings.parquet"
        write_buildings_parquet(buildings_df, str(buildings_path))
        
        # Process weather data
        weather_path = Path(args.output_dir) / "weather.parquet"
        weather_df = build_weather(args.try_path, args.year, str(weather_path))
        
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
