"""
Test LFA integration with graph/topology features.

This module tests that the LoadForecastingAgent properly includes
topology features in its feature engineering and training process.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, List

import pandas as pd
import pytest

from agents.lfa import LoadForecastingAgent


def create_sample_buildings_with_topology() -> pd.DataFrame:
    """Create sample building data with topology features."""
    return pd.DataFrame({
        'building_id': ['building_001', 'building_002'],
        'id': ['building_001', 'building_002'],
        'function': ['residential', 'commercial'],
        'floor_area': [120.0, 200.0],
        'volume': [300.0, 500.0],
        'height': [2.5, 3.0],
        'year': [1990, 2000],
        'H_tr': [150.0, 200.0],
        'H_ve': [50.0, 75.0],
        'sanierungs_faktor': [0.71, 0.30],
        'T_in': [20.0, 20.0],
        'n': [0.5, 0.5],
        # Topology features
        'substation_id': ['sub_001', 'sub_002'],
        'feeder_id': ['feeder_001', 'feeder_002'],
        'road_distance_m': [25.0, 35.0],
        'hydraulic_distance_m': [30.0, 45.0],
        'topo_hops': [2, 3],
        'node_degree': [3, 4],
        'betweenness_centrality': [0.1, 0.2],
        'edge_count_to_substation': [2, 3]
    })


def create_sample_weather_168h() -> pd.DataFrame:
    """Create sample weather data for 168 hours (1 week)."""
    import numpy as np
    from datetime import datetime, timedelta
    
    start_date = datetime(2024, 1, 1)
    timestamps = [start_date + timedelta(hours=i) for i in range(168)]
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'T_out': np.random.normal(10.0, 5.0, 168),  # Temperature around 10°C
        'RH': np.random.uniform(60.0, 80.0, 168),   # Relative humidity
        'GHI': np.random.uniform(0.0, 500.0, 168)   # Global horizontal irradiance
    }).set_index('timestamp')


def create_lfa_config_with_topology() -> Dict:
    """Create LFA configuration with topology features enabled."""
    return {
        "seed": 42,
        "model_version": "lfa-v1.0.0",
        "buildings_path": "data/processed/buildings.parquet",
        "weather_path": "data/processed/weather.parquet",
        "meters_dir": "data/interim/meters",
        "output_dir": "processed/lfa",
        "metrics_path": "eval/lfa/metrics.csv",
        "labels": {
            "source": "physics"
        },
        "model_params": {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.9
        },
        "quantiles": [0.1, 0.5, 0.9],
        "lag_hours": [1, 24, 168],
        "degree_day_base": 15.0
    }


def test_topology_features_in_feature_columns():
    """Test that topology features are included in self.feature_columns."""
    print("\n📊 Testing topology features in feature columns...")
    
    buildings_df = create_sample_buildings_with_topology()
    weather_df = create_sample_weather_168h()
    config = create_lfa_config_with_topology()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Save sample data
        buildings_path = temp_dir_path / "buildings.parquet"
        weather_path = temp_dir_path / "weather.parquet"
        meters_dir = temp_dir_path / "meters"
        output_dir = temp_dir_path / "output"
        
        buildings_df.to_parquet(buildings_path)
        weather_df.to_parquet(weather_path)
        meters_dir.mkdir()
        output_dir.mkdir()
        
        # Update config paths
        config["buildings_path"] = str(buildings_path)
        config["weather_path"] = str(weather_path)
        config["meters_dir"] = str(meters_dir)
        config["output_dir"] = str(output_dir)
        config["metrics_path"] = str(temp_dir_path / "metrics.csv")
        
        # Initialize LFA
        lfa = LoadForecastingAgent(config)
        
        # Load data and engineer features
        buildings_loaded, weather_loaded, meters_loaded = lfa.load_data()
        features_df = lfa.engineer_features(weather_loaded, buildings_loaded)
        training_df = lfa.generate_synthetic_training_data(features_df, buildings_loaded)
        
        # Train models (this sets self.feature_columns)
        lfa.train_models(training_df)
        
        # Check that topology features are in feature_columns
        topology_features = ['substation_id', 'feeder_id', 'road_distance_m', 'hydraulic_distance_m',
                           'topo_hops', 'node_degree', 'betweenness_centrality', 'edge_count_to_substation']
        
        found_topology_features = [f for f in topology_features if f in lfa.feature_columns]
        
        print(f"   Found topology features in feature_columns: {found_topology_features}")
        print(f"   Total feature_columns: {len(lfa.feature_columns)}")
        
        # Should have at least some topology features
        assert len(found_topology_features) > 0, f"No topology features found in feature_columns. Available: {lfa.feature_columns}"
        
        # Check that categorical features are properly encoded
        if 'substation_id' in lfa.feature_columns:
            assert 'substation_id' in lfa.category_maps, "substation_id should have category mapping"
        
        if 'feeder_id' in lfa.feature_columns:
            assert 'feeder_id' in lfa.category_maps, "feeder_id should have category mapping"
        
        print(f"✅ Topology features in feature_columns test passed: {len(found_topology_features)} features found")


if __name__ == "__main__":
    test_topology_features_in_feature_columns()
