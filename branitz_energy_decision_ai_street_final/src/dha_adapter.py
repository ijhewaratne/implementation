#!/usr/bin/env python3
"""
DHA Adapter: Converts LFA heat series to electric loads using COP bins
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict
import glob

def load_lfa_series(lfa_glob: str) -> pd.DataFrame:
    """Load LFA series from JSON files and convert to DataFrame."""
    print(f"📁 Loading LFA series from: {lfa_glob}")
    
    # Find all matching files
    files = glob.glob(lfa_glob)
    if not files:
        raise FileNotFoundError(f"No LFA files found matching: {lfa_glob}")
    
    print(f"   Found {len(files)} LFA files")
    
    # Load each file and extract series
    all_series = []
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract building ID from filename
            building_id = Path(file_path).stem
            
            # Get the series data (8760 hours)
            if 'series' in data:
                series = data['series']
                if len(series) == 8760:
                    # Create DataFrame with building_id, hour, q_kw
                    df = pd.DataFrame({
                        'building_id': building_id,
                        'hour': range(8760),
                        'q_kw': series
                    })
                    all_series.append(df)
                else:
                    print(f"   ⚠️ Warning: {building_id} has {len(series)} hours (expected 8760)")
            else:
                print(f"   ⚠️ Warning: {building_id} missing 'series' key")
                
        except Exception as e:
            print(f"   ❌ Error loading {file_path}: {e}")
            continue
    
    if not all_series:
        raise ValueError("No valid LFA series found")
    
    # Combine all series
    result = pd.concat(all_series, ignore_index=True)
    print(f"✅ Loaded {len(result)} building-hour records from {len(all_series)} buildings")
    
    return result

def load_weather_opt(weather_path: Optional[str]) -> Optional[pd.DataFrame]:
    """Load weather data if available."""
    if not weather_path:
        print("   ℹ️ No weather data specified")
        return None
    
    try:
        weather_file = Path(weather_path)
        if weather_file.exists():
            weather = pd.read_parquet(weather_path)
            print(f"✅ Loaded weather data: {len(weather)} records")
            print(f"   Columns: {list(weather.columns)}")
            return weather
        else:
            print(f"   ⚠️ Weather file not found: {weather_path}")
            return None
    except Exception as e:
        print(f"   ❌ Error loading weather: {e}")
        return None

def heat_to_electric_kw(
    lfa_df: pd.DataFrame, 
    weather: Optional[pd.DataFrame], 
    bins: List[Dict], 
    cop_default: float
) -> pd.DataFrame:
    """Convert heat demand to electric load using temperature-dependent COP."""
    print("🔄 Converting heat demand to electric load...")
    
    # Start with heat demand
    result = lfa_df.copy()
    
    if weather is not None and 'T_out_c' in weather.columns:
        print("   Using temperature-dependent COP bins")
        
        # Merge weather data by hour
        result = result.merge(weather[['hour', 'T_out_c']], on='hour', how='left')
        
        # Calculate COP based on temperature bins
        def get_cop_for_temp(temp):
            for bin_info in bins:
                if bin_info['t_min'] <= temp <= bin_info['t_max']:
                    return bin_info['cop']
            return cop_default
        
        # Apply COP calculation
        result['cop'] = result['T_out_c'].apply(get_cop_for_temp)
        
        # Convert heat to electric: P_el = Q_th / COP
        result['p_kw'] = result['q_kw'] / result['cop']
        
        print(f"   Temperature range: {result['T_out_c'].min():.1f}°C to {result['T_out_c'].max():.1f}°C")
        print(f"   COP range: {result['cop'].min():.2f} to {result['cop'].max():.2f}")
        
    else:
        print(f"   Using default COP: {cop_default}")
        
        # Use default COP
        result['cop'] = cop_default
        result['p_kw'] = result['q_kw'] / cop_default
    
    # Clean up and select final columns
    result = result[['building_id', 'hour', 'p_kw', 'cop']].copy()
    
    # Handle any infinite or NaN values
    result = result.replace([np.inf, -np.inf], np.nan)
    result = result.dropna()
    
    print(f"✅ Converted {len(result)} records to electric load")
    print(f"   Total electric demand: {result['p_kw'].sum():.1f} kWh")
    print(f"   Peak electric demand: {result['p_kw'].max():.1f} kW")
    
    return result

if __name__ == "__main__":
    # Test the adapter
    print("🧪 Testing DHA Adapter...")
    
    # Test with sample data
    sample_lfa = pd.DataFrame({
        'building_id': ['B1', 'B2'],
        'hour': [0, 1, 2, 3, 4, 5],
        'q_kw': [10.0, 12.0, 8.0, 15.0, 11.0, 9.0]
    })
    
    sample_weather = pd.DataFrame({
        'hour': [0, 1, 2, 3, 4, 5],
        'T_out_c': [-5.0, -3.0, -1.0, 2.0, 5.0, 8.0]
    })
    
    sample_bins = [
        {'t_min': -10, 't_max': 0, 'cop': 2.5},
        {'t_min': 0, 't_max': 10, 'cop': 3.0}
    ]
    
    result = heat_to_electric_kw(sample_lfa, sample_weather, sample_bins, 3.0)
    print("\n📊 Sample conversion result:")
    print(result)
