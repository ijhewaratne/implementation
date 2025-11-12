#!/usr/bin/env python3
"""
Generate sample data for LoadForecastingAgent testing.

Creates:
- data/processed/buildings.parquet (building metadata)
- data/processed/weather.parquet (hourly weather data)
- data/interim/meters/ (optional meter data)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import random

def generate_sample_buildings(n_buildings: int = 50) -> pd.DataFrame:
    """Generate sample building data."""
    
    building_types = ['residential', 'commercial', 'office', 'retail', 'school', 'hospital']
    
    buildings_data = []
    
    for i in range(n_buildings):
        building_type = random.choice(building_types)
        
        # Generate realistic building characteristics
        if building_type == 'residential':
            floor_area = random.uniform(80, 200)  # m²
            year_built = random.randint(1960, 2020)
        elif building_type == 'commercial':
            floor_area = random.uniform(500, 2000)
            year_built = random.randint(1980, 2020)
        elif building_type == 'office':
            floor_area = random.uniform(1000, 5000)
            year_built = random.randint(1990, 2020)
        elif building_type == 'retail':
            floor_area = random.uniform(200, 1000)
            year_built = random.randint(1985, 2020)
        elif building_type == 'school':
            floor_area = random.uniform(2000, 8000)
            year_built = random.randint(1970, 2020)
        elif building_type == 'hospital':
            floor_area = random.uniform(5000, 20000)
            year_built = random.randint(1980, 2020)
        
        buildings_data.append({
            'building_id': f'B{i+1:03d}',
            'floor_area': floor_area,
            'function': building_type,
            'year': year_built,
            'insulation_quality': random.choice(['poor', 'average', 'good', 'excellent']),
            'latitude': random.uniform(51.0, 52.0),  # Berlin area
            'longitude': random.uniform(13.0, 14.0),
            'num_floors': random.randint(1, 8),
            'construction_type': random.choice(['concrete', 'brick', 'wood', 'steel']),
            'heating_system': random.choice(['district_heating', 'gas_boiler', 'heat_pump', 'oil_boiler'])
        })
    
    return pd.DataFrame(buildings_data)

def generate_sample_weather(n_hours: int = 8760) -> pd.DataFrame:
    """Generate sample weather data for one year."""
    
    # Create hourly timestamps
    start_date = datetime(2024, 1, 1)
    timestamps = [start_date + timedelta(hours=i) for i in range(n_hours)]
    
    weather_data = []
    
    for i, timestamp in enumerate(timestamps):
        hour = timestamp.hour
        day_of_year = timestamp.timetuple().tm_yday
        month = timestamp.month
        
        # Base temperature with seasonal variation
        base_temp = 10.0  # Annual average
        seasonal_temp = base_temp + 15.0 * np.sin(2 * np.pi * (day_of_year - 172) / 365)
        
        # Diurnal variation
        diurnal_temp = 5.0 * np.sin(2 * np.pi * (hour - 6) / 24)
        
        # Add some noise
        noise = np.random.normal(0, 2.0)
        
        temperature = seasonal_temp + diurnal_temp + noise
        
        # Relative humidity (inverse relationship with temperature)
        humidity = max(30, min(95, 80 - 0.5 * temperature + np.random.normal(0, 10)))
        
        # Global horizontal irradiance (solar radiation)
        if 6 <= hour <= 18:  # Daylight hours
            # Seasonal and diurnal variation
            max_radiation = 800 * (1 + 0.3 * np.cos(2 * np.pi * (day_of_year - 172) / 365))
            solar_angle = np.sin(np.pi * (hour - 6) / 12)
            ghi = max(0, max_radiation * solar_angle + np.random.normal(0, 50))
        else:
            ghi = 0
        
        # Wind speed
        wind_speed = np.random.exponential(3.0) + np.random.normal(0, 1.0)
        wind_speed = max(0, min(20, wind_speed))
        
        # Precipitation
        if np.random.random() < 0.1:  # 10% chance of rain
            precipitation = np.random.exponential(2.0)
        else:
            precipitation = 0
        
        weather_data.append({
            'timestamp': timestamp,
            'T_out': temperature,
            'RH': humidity,
            'GHI': ghi,
            'wind_speed': wind_speed,
            'precipitation': precipitation,
            'pressure': 1013.25 + np.random.normal(0, 10),  # hPa
            'cloud_cover': np.random.uniform(0, 1)  # 0-1 scale
        })
    
    return pd.DataFrame(weather_data)

def generate_sample_meters(buildings_df: pd.DataFrame, n_hours: int = 8760) -> None:
    """Generate sample meter data for some buildings."""
    
    meters_dir = Path("data/interim/meters")
    meters_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate meter data for a subset of buildings
    sample_buildings = buildings_df.sample(min(10, len(buildings_df)))
    
    for _, building in sample_buildings.iterrows():
        building_id = building['building_id']
        
        # Generate realistic consumption patterns
        base_consumption = building['floor_area'] * 0.1  # kW per m²
        
        meter_data = []
        start_date = datetime(2024, 1, 1)
        
        for hour in range(n_hours):
            timestamp = start_date + timedelta(hours=hour)
            
            # Base consumption with seasonal and diurnal patterns
            seasonal_factor = 1.0 + 0.5 * np.sin(2 * np.pi * (hour // 24 - 172) / 365)
            diurnal_factor = 1.0 + 0.3 * np.sin(2 * np.pi * (hour % 24 - 6) / 24)
            
            consumption = base_consumption * seasonal_factor * diurnal_factor
            
            # Add noise
            consumption += np.random.normal(0, consumption * 0.1)
            consumption = max(0, consumption)
            
            meter_data.append({
                'timestamp': timestamp,
                'building_id': building_id,
                'consumption_kw': consumption,
                'meter_id': f'M{building_id}'
            })
        
        # Save to parquet
        meter_df = pd.DataFrame(meter_data)
        meter_df.to_parquet(meters_dir / f"{building_id}_meter.parquet", index=False)

def main():
    """Generate all sample data."""
    
    print("Generating sample data for LoadForecastingAgent...")
    
    # Create directories
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("data/interim").mkdir(parents=True, exist_ok=True)
    
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    # Generate buildings data
    print("Generating buildings data...")
    buildings_df = generate_sample_buildings(n_buildings=50)
    buildings_df.to_parquet("data/processed/buildings.parquet", index=False)
    print(f"Generated {len(buildings_df)} buildings")
    
    # Generate weather data
    print("Generating weather data...")
    weather_df = generate_sample_weather(n_hours=8760)
    weather_df.to_parquet("data/processed/weather.parquet", index=False)
    print(f"Generated {len(weather_df)} hours of weather data")
    
    # Generate meter data (optional)
    print("Generating meter data...")
    generate_sample_meters(buildings_df, n_hours=8760)
    print("Generated meter data for sample buildings")
    
    print("\nSample data generation complete!")
    print("Files created:")
    print("- data/processed/buildings.parquet")
    print("- data/processed/weather.parquet")
    print("- data/interim/meters/*.parquet")
    
    # Print summary statistics
    print(f"\nSummary:")
    print(f"- Buildings: {len(buildings_df)}")
    print(f"- Weather hours: {len(weather_df)}")
    print(f"- Building types: {buildings_df['function'].value_counts().to_dict()}")
    print(f"- Floor area range: {buildings_df['floor_area'].min():.1f} - {buildings_df['floor_area'].max():.1f} m²")
    print(f"- Temperature range: {weather_df['T_out'].min():.1f} - {weather_df['T_out'].max():.1f} °C")

if __name__ == "__main__":
    main()
