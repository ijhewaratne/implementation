"""
Test LFA physics integration.

Tests that the LoadForecastingAgent correctly uses physics features
and generates appropriate outputs with physics-based labels.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import yaml
import json
from datetime import datetime, timedelta

# Import LFA
import sys
sys.path.append('..')
from agents.lfa import LoadForecastingAgent


def create_sample_buildings_with_physics():
    """Create sample building data with physics features."""
    buildings = []
    
    # Building 1: Small residential with physics
    building1 = {
        'id': 'B001',
        'function': 'residential',
        'floor_area': 80.0,
        'wall_area': 120.0,
        'roof_area': 85.0,
        'volume': 240.0,
        'height': 3.0,
        'U_wall': 1.2,
        'U_roof': 0.25,
        'U_floor': 0.4,
        'U_window': 1.1,
        'window_share': 0.15,
        'T_in': 20.0,
        'n': 0.5,
        'sanierungszustand': 'teilsaniert',
        'year': 1995,
        'H_tr': 150.0,  # Pre-computed physics
        'H_ve': 40.8,   # Pre-computed physics
        'sanierungs_faktor': 0.71
    }
    buildings.append(building1)
    
    # Building 2: Large commercial with physics
    building2 = {
        'id': 'B002',
        'function': 'commercial',
        'floor_area': 500.0,
        'wall_area': 600.0,
        'roof_area': 520.0,
        'volume': 1500.0,
        'height': 3.0,
        'U_wall': 0.8,
        'U_roof': 0.2,
        'U_floor': 0.3,
        'U_window': 0.9,
        'window_share': 0.12,
        'T_in': 22.0,
        'n': 0.8,
        'sanierungszustand': 'vollsaniert',
        'year': 2010,
        'H_tr': 600.0,  # Pre-computed physics
        'H_ve': 408.0,  # Pre-computed physics
        'sanierungs_faktor': 0.30
    }
    buildings.append(building2)
    
    return pd.DataFrame(buildings)


def create_sample_weather_168h():
    """Create sample weather data for 168 hours (1 week)."""
    # Create hourly timestamps for 168 hours
    start_date = datetime(2024, 1, 1)
    timestamps = pd.date_range(start=start_date, periods=168, freq='H')
    
    # Generate realistic temperature data
    base_temp = 5.0  # Cold winter temperature
    daily_variation = 8.0 * np.cos(2 * np.pi * (np.arange(168) % 24) / 24)
    weekly_variation = 3.0 * np.cos(2 * np.pi * (np.arange(168) % 168) / 168)
    noise = np.random.normal(0, 1.0, 168)
    
    temperatures = base_temp + daily_variation + weekly_variation + noise
    
    weather_data = {
        'timestamp': timestamps,
        'T_out': temperatures,
        'RH': 70.0 + 10.0 * np.random.random(168),
        'GHI': np.maximum(0, 400.0 * np.sin(np.pi * (np.arange(168) % 24) / 12))
    }
    
    return pd.DataFrame(weather_data)


def create_lfa_config():
    """Create LFA configuration for testing."""
    config = {
        "seed": 42,
        "model_version": "lfa-test-v1.0.0",
        "buildings_path": "temp_buildings.parquet",
        "weather_path": "temp_weather.parquet",
        "meters_dir": "temp_meters",
        "output_dir": "temp_output",
        "metrics_path": "temp_metrics.csv",
        "model_params": {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "num_leaves": 15,  # Smaller for testing
            "learning_rate": 0.1,
            "feature_fraction": 0.9,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
            "random_state": 42
        },
        "quantiles": [0.1, 0.5, 0.9],
        "degree_day_base": 18.0,
        "lag_hours": [1, 2, 3],  # Fewer lags for testing
        "use_physics_labels": True,
        "labels": {
            "source": "physics"  # Use physics-based labels
        }
    }
    return config


def test_lfa_physics_integration():
    """Test LFA with physics features and shortened training."""
    print("🧪 Testing LFA physics integration...")
    
    # Create sample data
    buildings_df = create_sample_buildings_with_physics()
    weather_df = create_sample_weather_168h()
    config = create_lfa_config()
    
    print(f"✅ Created {len(buildings_df)} sample buildings with physics")
    print(f"✅ Created {len(weather_df)} sample weather records (168h)")
    
    # Create temporary files and directories
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
        print("\n🏗️ Initializing LFA...")
        lfa = LoadForecastingAgent(config)
        
        # Check that physics features are detected
        print("\n⚙️ Checking physics feature detection...")
        buildings_loaded, weather_loaded, meters_loaded = lfa.load_data()
        
        physics_features = ['H_tr', 'H_ve', 'sanierungs_faktor']
        available_physics = [f for f in physics_features if f in buildings_loaded.columns]
        assert len(available_physics) == 3, f"Expected 3 physics features, got {len(available_physics)}"
        print(f"✅ Physics features detected: {available_physics}")
        
        # Test feature engineering
        print("\n🔧 Testing feature engineering...")
        features_df = lfa.engineer_features(weather_loaded, buildings_loaded)
        
        # Check that physics features are included in feature columns
        physics_in_features = [f for f in physics_features if f in lfa.feature_columns]
        assert len(physics_in_features) > 0, "Physics features should be in feature columns"
        print(f"✅ Physics features in feature set: {physics_in_features}")
        
        # Test synthetic training data generation
        print("\n📈 Testing synthetic training data generation...")
        training_df = lfa.generate_synthetic_training_data(features_df, buildings_loaded)
        
        assert len(training_df) > 0, "Training data should not be empty"
        assert 'demand_kw' in training_df.columns, "Training data should have demand_kw column"
        assert (training_df['demand_kw'] >= 0).all(), "Demand should be non-negative"
        
        # Check that physics features are in training data
        for feature in physics_features:
            if feature in training_df.columns:
                assert not training_df[feature].isna().all(), f"Physics feature {feature} should not be all NaN"
        
        print(f"✅ Generated {len(training_df)} training samples")
        print(f"   Demand range: {training_df['demand_kw'].min():.3f} - {training_df['demand_kw'].max():.3f} kW")
        
        # Test model training (shortened)
        print("\n🎯 Testing model training...")
        lfa.train(training_df)
        
        assert lfa.mean_model is not None, "Mean model should be trained"
        print("✅ Model training successful")
        
        # Test prediction
        print("\n🔮 Testing prediction...")
        predictions = lfa.predict(features_df, buildings_loaded)
        
        # Check prediction structure
        assert len(predictions) == len(buildings_loaded), "Should have predictions for all buildings"
        
        for building_id, prediction in predictions.items():
            assert 'series' in prediction, f"Prediction for {building_id} should have 'series'"
            assert 'q10' in prediction, f"Prediction for {building_id} should have 'q10'"
            assert 'q90' in prediction, f"Prediction for {building_id} should have 'q90'"
            assert 'metadata' in prediction, f"Prediction for {building_id} should have 'metadata'"
            
            # Check array lengths (should be 168 for our test data)
            series_length = len(prediction['series'])
            assert series_length == 168, f"Series length should be 168, got {series_length}"
            assert len(prediction['q10']) == 168, f"q10 length should be 168"
            assert len(prediction['q90']) == 168, f"q90 length should be 168"
            
            # Check that predictions are reasonable
            assert all(x >= 0 for x in prediction['series']), "Predictions should be non-negative"
            assert all(x >= 0 for x in prediction['q10']), "q10 should be non-negative"
            assert all(x >= 0 for x in prediction['q90']), "q90 should be non-negative"
        
        print(f"✅ Generated predictions for {len(predictions)} buildings")
        print(f"   Sample prediction length: {len(list(predictions.values())[0]['series'])}")
        
        # Test output writing
        print("\n💾 Testing output writing...")
        lfa.write_outputs(predictions)
        
        # Check that output files were created
        output_files = list(output_dir.glob("*.json"))
        assert len(output_files) == len(buildings_loaded), f"Expected {len(buildings_loaded)} output files"
        
        # Test one output file
        sample_output = json.load(open(output_files[0]))
        assert 'x-version' in sample_output, "Output should have x-version"
        assert 'building_id' in sample_output, "Output should have building_id"
        assert 'series' in sample_output, "Output should have series"
        assert 'q10' in sample_output, "Output should have q10"
        assert 'q90' in sample_output, "Output should have q90"
        assert 'metadata' in sample_output, "Output should have metadata"
        
        print(f"✅ Output files written: {len(output_files)} files")
    
    print("\n🎉 All LFA physics integration tests passed!")


if __name__ == "__main__":
    test_lfa_physics_integration()
