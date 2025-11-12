#!/usr/bin/env python3
"""
Demonstration of the ETL Pipeline for LoadForecastingAgent

This script shows how the ETL pipeline processes building data and generates
physics-based synthetic labels for the LFA.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json


def create_sample_building_data():
    """Create sample building data for demonstration."""
    buildings = []
    
    for i in range(5):
        building = {
            'oi': f'B{i:03d}',
            'gebaeudefunktion': 'residential',
            'nutzflaeche': 100.0 + i * 20.0,
            'wandflaeche': 150.0 + i * 30.0,
            'dachflaeche': 110.0 + i * 22.0,
            'volumen': 300.0 + i * 60.0,
            'hoehe': 3.0 + (i % 3) * 0.5,
            'U_Aussenwand': 1.5 - (i % 3) * 0.2,
            'U_Dach': 0.3 - (i % 3) * 0.05,
            'U_Boden': 0.5 - (i % 3) * 0.1,
            'U_Fenster': 1.3 - (i % 3) * 0.1,
            'fensterflaechenanteil': 0.15 + (i % 3) * 0.05,
            'innentemperatur': 20.0,
            'n': 0.5 + (i % 3) * 0.1,
            'sanierungszustand': ['unsaniert', 'teilsaniert', 'vollsaniert'][i % 3],
            'baujahr': 1990 + (i % 3) * 10
        }
        buildings.append(building)
    
    return pd.DataFrame(buildings)


def compute_physics_coefficients(df):
    """
    Compute physics coefficients from building data.
    
    This is a simplified version of the physics computation from the ETL pipeline.
    """
    df = df.copy()
    
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
    
    return df


def generate_synthetic_weather():
    """Generate sample weather data for demonstration."""
    start_date = pd.Timestamp('2024-01-01')
    timestamps = pd.date_range(start=start_date, periods=24, freq='H')  # 24 hours for demo
    
    # Simple temperature pattern
    hours = np.arange(24)
    base_temp = 10.0
    daily_variation = 3.0 * np.cos(2 * np.pi * hours / 24)
    noise = np.random.normal(0, 1, 24)
    
    temperatures = base_temp + daily_variation + noise
    
    weather_data = {
        'timestamp': timestamps,
        'T_out': temperatures,
        'RH': 60.0 + 10.0 * np.sin(2 * np.pi * hours / 24),
        'GHI': np.maximum(0, 500 * np.sin(np.pi * (hours - 6) / 12))
    }
    
    return pd.DataFrame(weather_data)


def calculate_heat_demand(building, weather_df):
    """
    Calculate heat demand using DIN formula.
    
    P_h(t) = (H_tr + H_ve) * (T_in - T_out(t)) * sanierungs_faktor
    """
    T_in = building['innentemperatur']
    H_tr = building['H_tr']
    H_ve = building['H_ve']
    sanierungs_faktor = building['sanierungs_faktor']
    
    heat_demand = []
    for _, row in weather_df.iterrows():
        T_out = row['T_out']
        
        # DIN heat demand formula (in W)
        P_h = (H_tr + H_ve) * (T_in - T_out) * sanierungs_faktor
        
        # Clip at 0 (no cooling) and convert to kW
        P_h = max(0.0, P_h) / 1000.0
        
        heat_demand.append({
            'timestamp': row['timestamp'],
            'demand_kw': P_h
        })
    
    return pd.DataFrame(heat_demand)


def main():
    """Main demonstration function."""
    print("🏗️ ETL Pipeline Demonstration")
    print("=" * 50)
    
    # 1. Create sample building data
    print("\n1. 📊 Creating sample building data...")
    buildings_df = create_sample_building_data()
    print(f"   Created {len(buildings_df)} buildings")
    print(f"   Sample building: {buildings_df.iloc[0]['oi']}")
    print(f"   Floor area: {buildings_df.iloc[0]['nutzflaeche']:.1f} m²")
    print(f"   U-value (wall): {buildings_df.iloc[0]['U_Aussenwand']:.2f} W/m²K")
    
    # 2. Compute physics coefficients
    print("\n2. ⚙️ Computing physics coefficients...")
    buildings_with_physics = compute_physics_coefficients(buildings_df)
    
    # Show physics coefficients for first building
    building = buildings_with_physics.iloc[0]
    print(f"   Building {building['oi']}:")
    print(f"     H_tr (transmission): {building['H_tr']:.1f} W/K")
    print(f"     H_ve (ventilation): {building['H_ve']:.1f} W/K")
    print(f"     Sanierungsfaktor: {building['sanierungs_faktor']:.2f}")
    
    # 3. Generate weather data
    print("\n3. 🌤️ Generating weather data...")
    weather_df = generate_synthetic_weather()
    print(f"   Generated {len(weather_df)} hours of weather data")
    print(f"   Temperature range: {weather_df['T_out'].min():.1f}°C to {weather_df['T_out'].max():.1f}°C")
    
    # 4. Calculate heat demand
    print("\n4. 🔥 Calculating heat demand...")
    heat_demand_df = calculate_heat_demand(building, weather_df)
    print(f"   Generated {len(heat_demand_df)} hours of heat demand")
    print(f"   Demand range: {heat_demand_df['demand_kw'].min():.3f} to {heat_demand_df['demand_kw'].max():.3f} kW")
    
    # 5. Show sample results
    print("\n5. 📈 Sample results (first 6 hours):")
    print(heat_demand_df.head(6).to_string(index=False))
    
    # 6. Summary statistics
    print("\n6. 📊 Summary statistics:")
    print(f"   Total heat demand: {heat_demand_df['demand_kw'].sum():.2f} kWh")
    print(f"   Average heat demand: {heat_demand_df['demand_kw'].mean():.3f} kW")
    print(f"   Peak heat demand: {heat_demand_df['demand_kw'].max():.3f} kW")
    
    print("\n✅ ETL Pipeline demonstration completed!")
    print("\nThis demonstrates:")
    print("  • Building data normalization")
    print("  • Physics coefficient computation (H_tr, H_ve, sanierungs_faktor)")
    print("  • Weather data processing")
    print("  • DIN-style heat demand calculation")
    print("  • Synthetic label generation for LFA training")


if __name__ == "__main__":
    main()







