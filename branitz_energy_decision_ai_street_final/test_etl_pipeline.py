#!/usr/bin/env python3
"""
Test script for the ETL pipeline.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

def create_sample_building_data():
    """Create sample building data for testing."""
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

def test_basic_functionality():
    """Test basic ETL functionality."""
    print("🧪 Testing Basic ETL Functionality")
    
    # Create sample data
    buildings_df = create_sample_building_data()
    print(f"   Created {len(buildings_df)} sample buildings")
    
    # Test physics computation
    try:
        from etl.data_to_lfa import compute_physics
        buildings_with_physics = compute_physics(buildings_df)
        print(f"   ✅ Physics computation successful")
        print(f"   Physics features: {[col for col in buildings_with_physics.columns if col in ['H_tr', 'H_ve', 'sanierungs_faktor']]}")
    except Exception as e:
        print(f"   ❌ Physics computation failed: {e}")
    
    print("✅ Basic ETL test completed!")

if __name__ == "__main__":
    test_basic_functionality()
