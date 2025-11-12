"""
Test ETL pipeline for data16122024.

Tests the ETL pipeline with synthetic data to ensure physics computation
and synthetic label generation work correctly.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import yaml
from datetime import datetime, timedelta

# Import ETL functions
import sys
sys.path.append('..')
from etl.data16122024_to_lfa import (
    load_config, load_buildings, compute_physics, 
    build_weather, synthesize_labels
)


def create_sample_building_data():
    """Create synthetic building data for testing."""
    buildings = []
    
    # Building 1: Small residential
    building1 = {
        'building_id': 'B001',
        'function': 'residential',
        'floor_area_m2': 80.0,
        'wall_area_m2': 120.0,
        'roof_area_m2': 85.0,
        'volume_m3': 240.0,
        'height_m': 3.0,
        'U_Aussenwand': 1.2,
        'U_Dach': 0.25,
        'U_Boden': 0.4,
        'U_Fenster': 1.1,
        'fensterflaechenanteil': 0.15,
        'T_in_C': 20.0,
        'air_change_n_per_h': 0.5,
        'sanierungszustand': 'teilsaniert',
        'year': 1995
    }
    buildings.append(building1)
    
    # Building 2: Large commercial
    building2 = {
        'building_id': 'B002',
        'function': 'commercial',
        'floor_area_m2': 500.0,
        'wall_area_m2': 600.0,
        'roof_area_m2': 520.0,
        'volume_m3': 1500.0,
        'height_m': 3.0,
        'U_Aussenwand': 0.8,
        'U_Dach': 0.2,
        'U_Boden': 0.3,
        'U_Fenster': 0.9,
        'fensterflaechenanteil': 0.12,
        'T_in_C': 22.0,
        'air_change_n_per_h': 0.8,
        'sanierungszustand': 'vollsaniert',
        'year': 2010
    }
    buildings.append(building2)
    
    return pd.DataFrame(buildings)


def create_sample_weather_data():
    """Create synthetic weather data for testing (8760 hours)."""
    # Create hourly timestamps for one year
    start_date = datetime(2024, 1, 1)
    timestamps = pd.date_range(start=start_date, periods=8760, freq='H')
    
    # Generate realistic temperature data
    base_temp = 10.0  # Base temperature
    seasonal_variation = 15.0 * np.cos(2 * np.pi * np.arange(8760) / 8760)
    daily_variation = 5.0 * np.cos(2 * np.pi * (np.arange(8760) % 24) / 24)
    noise = np.random.normal(0, 2.0, 8760)
    
    temperatures = base_temp + seasonal_variation + daily_variation + noise
    
    weather_data = {
        'timestamp': timestamps,
        'T_out': temperatures,
        'RH': 60.0 + 20.0 * np.random.random(8760),  # 60-80% RH
        'GHI': np.maximum(0, 800.0 * np.sin(np.pi * (np.arange(8760) % 24) / 12))  # Solar radiation
    }
    
    return pd.DataFrame(weather_data)


def create_sample_config():
    """Create sample ETL configuration."""
    config = {
        'defaults': {
            'T_in_C': 20.0,
            'air_change_n_per_h': 0.5,
            'window_share': 0.15,
            'height': 3.0,
            'sanierungs_map': {
                'unsaniert': 1.00,
                'teilsaniert': 0.71,
                'vollsaniert': 0.30
            }
        },
        'buildings_columns': {
            'id': 'building_id',
            'function': 'function',
            'floor_area': 'floor_area_m2',
            'wall_area': 'wall_area_m2',
            'roof_area': 'roof_area_m2',
            'volume': 'volume_m3',
            'height': 'height_m',
            'U_wall': 'U_Aussenwand',
            'U_roof': 'U_Dach',
            'U_floor': 'U_Boden',
            'U_window': 'U_Fenster',
            'window_share': 'fensterflaechenanteil',
            'T_in': 'T_in_C',
            'n': 'air_change_n_per_h',
            'sanierungszustand': 'sanierungszustand',
            'year': 'year'
        },
        'weather_columns': {
            'timestamp': 'timestamp',
            'T_out': 'T_out',
            'RH': 'RH',
            'GHI': 'GHI'
        }
    }
    return config


def test_etl_pipeline():
    """Test the complete ETL pipeline with synthetic data."""
    print("🧪 Testing ETL pipeline with synthetic data...")
    
    # Create sample data
    buildings_df = create_sample_building_data()
    weather_df = create_sample_weather_data()
    config = create_sample_config()
    
    print(f"✅ Created {len(buildings_df)} sample buildings")
    print(f"✅ Created {len(weather_df)} sample weather records")
    
    # Test building data processing
    print("\n🏗️ Testing building data processing...")
    normalized_buildings = normalize_building_data(buildings_df, config)
    assert len(normalized_buildings) == 2
    assert 'id' in normalized_buildings.columns
    assert 'function' in normalized_buildings.columns
    assert 'floor_area' in normalized_buildings.columns
    print("✅ Building data normalization successful")
    
    # Test physics computation
    print("\n⚙️ Testing physics computation...")
    buildings_with_physics = compute_physics(normalized_buildings, config)
    
    # Check physics coefficients
    assert 'H_tr' in buildings_with_physics.columns
    assert 'H_ve' in buildings_with_physics.columns
    assert 'sanierungs_faktor' in buildings_with_physics.columns
    
    # Validate physics coefficients are positive
    assert (buildings_with_physics['H_tr'] > 0).all(), "H_tr should be positive"
    assert (buildings_with_physics['H_ve'] > 0).all(), "H_ve should be positive"
    assert (buildings_with_physics['sanierungs_faktor'] > 0).all(), "sanierungs_faktor should be positive"
    
    print(f"✅ Physics computation successful")
    print(f"   H_tr range: {buildings_with_physics['H_tr'].min():.1f} - {buildings_with_physics['H_tr'].max():.1f} W/K")
    print(f"   H_ve range: {buildings_with_physics['H_ve'].min():.1f} - {buildings_with_physics['H_ve'].max():.1f} W/K")
    print(f"   Sanierungsfaktor: {list(buildings_with_physics['sanierungs_faktor'])}")
    
    # Test weather processing
    print("\n🌡️ Testing weather processing...")
    processed_weather = build_weather_from_df(weather_df, config)
    assert len(processed_weather) == 8760
    assert 'timestamp' in processed_weather.columns
    assert 'T_out' in processed_weather.columns
    assert not processed_weather['T_out'].isna().any()
    print("✅ Weather processing successful")
    
    # Test synthetic label generation
    print("\n📈 Testing synthetic label generation...")
    with tempfile.TemporaryDirectory() as temp_dir:
        synthesize_labels(buildings_with_physics, processed_weather, temp_dir)
        
        # Check generated files
        meter_files = list(Path(temp_dir).glob("*.parquet"))
        assert len(meter_files) == 2, f"Expected 2 meter files, got {len(meter_files)}"
        
        # Test one meter file
        sample_meter = pd.read_parquet(meter_files[0])
        assert len(sample_meter) == 8760, f"Expected 8760 rows, got {len(sample_meter)}"
        assert 'timestamp' in sample_meter.columns
        assert 'demand_kw' in sample_meter.columns
        assert (sample_meter['demand_kw'] >= 0).all(), "Demand should be non-negative"
        
        print(f"✅ Synthetic label generation successful")
        print(f"   Generated {len(meter_files)} meter files")
        print(f"   Sample demand range: {sample_meter['demand_kw'].min():.3f} - {sample_meter['demand_kw'].max():.3f} kW")
    
    print("\n🎉 All ETL pipeline tests passed!")


def normalize_building_data(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Helper function to normalize building data for testing."""
    column_map = config.get('buildings_columns', {})
    normalized = pd.DataFrame()
    
    for target_col, source_col in column_map.items():
        if source_col in df.columns:
            normalized[target_col] = df[source_col]
    
    return normalized


def build_weather_from_df(weather_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Helper function to process weather data for testing."""
    # Apply column mapping
    column_map = config.get('weather_columns', {})
    processed = weather_df.copy()
    
    for target_col, source_col in column_map.items():
        if source_col in processed.columns:
            processed[target_col] = processed[source_col]
    
    # Ensure timestamp is set as index
    if 'timestamp' in processed.columns:
        processed = processed.set_index('timestamp')
    
    return processed


if __name__ == "__main__":
    test_etl_pipeline()
