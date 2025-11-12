#!/usr/bin/env python3
"""
Test script for the data16122024 ETL pipeline.

This script demonstrates how to use the ETL pipeline to process the actual data dataset
and generate the inputs required by the LoadForecastingAgent.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import yaml
from etl.data16122024_to_lfa import (
    load_column_mapping, load_buildings, compute_physics,
    build_weather, synthesize_labels
)


def examine_building_data():
    """Examine the structure of the building data."""
    print("🔍 Examining building data structure...")
    
    building_file = "data/json/output_branitzer_siedlungV11.json"
    
    if not Path(building_file).exists():
        print(f"❌ Building file not found: {building_file}")
        return None
    
    # Load a sample of the data
    with open(building_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get first building
    first_building_id = list(data.keys())[0]
    first_building = data[first_building_id]
    
    print(f"✅ Found {len(data)} buildings")
    print(f"📊 Sample building ID: {first_building_id}")
    print(f"📋 Sample building keys: {list(first_building.keys())}")
    
    # Show some sample values
    print("\n📋 Sample building data:")
    for key, value in list(first_building.items())[:10]:
        if isinstance(value, (str, int, float)):
            print(f"  {key}: {value}")
        elif isinstance(value, list):
            print(f"  {key}: {type(value)} with {len(value)} items")
        else:
            print(f"  {key}: {type(value)}")
    
    return data


def examine_weather_data():
    """Examine the structure of the weather data."""
    print("\n🌤️ Examining weather data structure...")
    
    weather_file = "data/csv/TRY2015_517475143730_Jahr.dat"
    
    if not Path(weather_file).exists():
        print(f"❌ Weather file not found: {weather_file}")
        return None
    
    # Read the header
    with open(weather_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"✅ Weather file found: {weather_file}")
    print(f"📊 File has {len(lines)} lines")
    
    # Show header information
    print("\n📋 Weather file header:")
    for i, line in enumerate(lines[:10]):
        if line.strip():
            print(f"  Line {i+1}: {line.strip()}")
    
    # Try to parse some data lines
    data_lines = []
    for line in lines:
        if line.strip() and not line.startswith('Koordinatensystem') and not line.startswith('Format:'):
            try:
                parts = line.strip().split()
                if len(parts) >= 6:
                    data_lines.append(parts)
                    if len(data_lines) <= 5:  # Show first 5 data lines
                        print(f"  Data line: {parts}")
            except:
                continue
    
    print(f"📊 Found {len(data_lines)} data lines")
    return weather_file


def test_column_mapping():
    """Test the column mapping configuration."""
    print("\n🗺️ Testing column mapping...")
    
    mapping_file = "configs/data16122024_mapping.yml"
    
    if not Path(mapping_file).exists():
        print(f"❌ Mapping file not found: {mapping_file}")
        return None
    
    try:
        mapping = load_column_mapping(mapping_file)
        print(f"✅ Loaded mapping configuration")
        print(f"📋 Building columns: {list(mapping.get('columns', {}).keys())}")
        print(f"📋 Weather columns: {list(mapping.get('weather_columns', {}).keys())}")
        print(f"📋 Defaults: {list(mapping.get('defaults', {}).keys())}")
        return mapping
    except Exception as e:
        print(f"❌ Error loading mapping: {e}")
        return None


def test_building_processing(mapping):
    """Test building data processing."""
    print("\n🏗️ Testing building data processing...")
    
    building_file = "data/json/output_branitzer_siedlungV11.json"
    
    if not Path(building_file).exists():
        print(f"❌ Building file not found: {building_file}")
        return None
    
    try:
        # Load and process a small sample
        buildings_df = load_buildings(building_file, mapping)
        
        # Take first 5 buildings for testing
        sample_buildings = buildings_df.head(5)
        print(f"✅ Loaded {len(buildings_df)} buildings, testing with {len(sample_buildings)}")
        
        # Show sample data
        print(f"📋 Sample building columns: {list(sample_buildings.columns)}")
        print(f"📊 Sample building data:")
        for _, building in sample_buildings.iterrows():
            print(f"  {building['building_id']}: {building['function']} - {building.get('floor_area', 'N/A')} m²")
        
        return sample_buildings
    except Exception as e:
        print(f"❌ Error processing buildings: {e}")
        return None


def test_physics_computation(buildings_df, mapping):
    """Test physics coefficient computation."""
    print("\n⚙️ Testing physics computation...")
    
    try:
        defaults = mapping.get('defaults', {})
        buildings_with_physics = compute_physics(buildings_df, defaults)
        
        print(f"✅ Physics computation successful")
        
        # Show physics coefficients for first building
        building = buildings_with_physics.iloc[0]
        print(f"📊 Building {building['building_id']} physics:")
        print(f"  H_tr (transmission): {building.get('H_tr', 'N/A'):.1f} W/K")
        print(f"  H_ve (ventilation): {building.get('H_ve', 'N/A'):.1f} W/K")
        print(f"  Sanierungsfaktor: {building.get('sanierungs_faktor', 'N/A'):.2f}")
        
        return buildings_with_physics
    except Exception as e:
        print(f"❌ Error computing physics: {e}")
        return None


def test_weather_processing(mapping):
    """Test weather data processing."""
    print("\n🌡️ Testing weather processing...")
    
    weather_file = "data/csv/TRY2015_517475143730_Jahr.dat"
    
    if not Path(weather_file).exists():
        print(f"❌ Weather file not found: {weather_file}")
        return None
    
    try:
        # Process weather data
        weather_df = build_weather(weather_file, 2024, mapping, "temp_weather.parquet")
        
        print(f"✅ Weather processing successful")
        print(f"📊 Weather data shape: {weather_df.shape}")
        print(f"📋 Weather columns: {list(weather_df.columns)}")
        print(f"🌡️ Temperature range: {weather_df['T_out'].min():.1f}°C to {weather_df['T_out'].max():.1f}°C")
        
        # Clean up temp file
        Path("temp_weather.parquet").unlink(missing_ok=True)
        
        return weather_df
    except Exception as e:
        print(f"❌ Error processing weather: {e}")
        return None


def test_synthetic_labels(buildings_df, weather_df):
    """Test synthetic label generation."""
    print("\n📈 Testing synthetic label generation...")
    
    try:
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            synthesize_labels(buildings_df, weather_df, temp_dir)
            
            # Check generated files
            meter_files = list(Path(temp_dir).glob("*.parquet"))
            print(f"✅ Generated {len(meter_files)} meter files")
            
            if meter_files:
                # Test one meter file
                sample_meter = pd.read_parquet(meter_files[0])
                building_id = meter_files[0].stem
                print(f"📊 Sample meter data for {building_id}:")
                print(f"  Shape: {sample_meter.shape}")
                print(f"  Columns: {list(sample_meter.columns)}")
                print(f"  Demand range: {sample_meter['demand_kw'].min():.3f} - {sample_meter['demand_kw'].max():.3f} kW")
                print(f"  Total demand: {sample_meter['demand_kw'].sum():.2f} kWh")
        
        return True
    except Exception as e:
        print(f"❌ Error generating labels: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 Testing data16122024 ETL Pipeline")
    print("=" * 50)
    
    # 1. Examine data structure
    building_data = examine_building_data()
    weather_file = examine_weather_data()
    
    # 2. Test column mapping
    mapping = test_column_mapping()
    if mapping is None:
        print("❌ Cannot proceed without mapping configuration")
        return
    
    # 3. Test building processing
    buildings_df = test_building_processing(mapping)
    if buildings_df is None:
        print("❌ Cannot proceed without building data")
        return
    
    # 4. Test physics computation
    buildings_with_physics = test_physics_computation(buildings_df, mapping)
    if buildings_with_physics is None:
        print("❌ Cannot proceed without physics computation")
        return
    
    # 5. Test weather processing
    weather_df = test_weather_processing(mapping)
    if weather_df is None:
        print("❌ Cannot proceed without weather data")
        return
    
    # 6. Test synthetic labels
    success = test_synthetic_labels(buildings_with_physics, weather_df)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All ETL pipeline tests passed!")
        print("\n🎉 The ETL pipeline is ready to process the data dataset.")
        print("\nNext steps:")
        print("1. Run: python -m etl.data16122024_to_lfa --buildings data/json/output_branitzer_siedlungV11.json --weather data/csv/TRY2015_517475143730_Jahr.dat --mapping configs/data16122024_mapping.yml --write-meters")
        print("2. Use the generated data/processed/buildings.parquet and data/processed/weather.parquet with LFA")
    else:
        print("❌ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
