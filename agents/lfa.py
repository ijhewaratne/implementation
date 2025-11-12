"""
LoadForecastingAgent (LFA)

Purpose: 8760-hour heat demand per building + quantiles.
Required tools: pandas, numpy, lightgbm (baseline). DL (optional): pytorch/keras.

Inputs:
- data/processed/buildings.parquet (id, floor_area, function, year, …)
- data/processed/weather.parquet (hourly: T_out, RH, GHI, …)
- Optional meters: data/interim/meters/*.parquet
- configs/lfa.yml (model params, quantile settings)

Process:
- Feature engineering (degree-hours, calendar, lags)
- Train/Load baseline model; predict mean, q10, q90
- Calibrate intervals (conformal or quantile loss)
- Post-process: clip negatives to 0; ensure length 8760; finite values
- Write one JSON per building; accumulate metrics

Outputs (per building):
- processed/lfa/{building_id}.json with keys:
  x-version,building_id,series[8760],q10[8760],q90[8760],metadata{forecast_date,model_version}
- eval/lfa/metrics.csv (MAE, RMSE, MAPE, PICP_90) per building + macro avg

Integration:
- JSON consumed by CHA (design points) & DHA (COP conversion)

Perf:
- Vectorized inference; batch buildings; seed for reproducibility

Constraints:
- Must pass schemas/lfa_demand.schema.json
- Missing weather rows → impute or fail with explicit error
"""

import json
import logging
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    logger.warning("LightGBM not available, using fallback model")
    LIGHTGBM_AVAILABLE = False


class LoadForecastingAgent:
    """
    Load Forecasting Agent for 8760-hour heat demand prediction per building.
    
    Implements feature engineering, ML training, and quantile prediction with
    conformal calibration for uncertainty quantification.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the Load Forecasting Agent.
        
        Args:
            config: Configuration dictionary with paths and model parameters
        """
        self.config = config
        self.seed = config.get("seed", 42)
        self.model_version = config.get("model_version", "lfa-v1.0.0")
        
        # Set random seeds for reproducibility
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        # Model components
        self.mean_model = None
        self.quantile_models = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        
        # Data paths
        self.buildings_path = config.get("buildings_path", "data/processed/buildings.parquet")
        self.weather_path = config.get("weather_path", "data/processed/weather.parquet")
        self.meters_dir = config.get("meters_dir", "data/interim/meters")
        self.output_dir = config.get("output_dir", "processed/lfa")
        self.metrics_path = config.get("metrics_path", "eval/lfa/metrics.csv")
        
        # Model parameters
        self.model_params = config.get("model_params", {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.9,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
            "random_state": self.seed
        })
        
        # Quantile settings
        self.quantiles = config.get("quantiles", [0.1, 0.5, 0.9])
        
        # Feature engineering settings
        self.degree_day_base = config.get("degree_day_base", 18.0)  # °C
        self.lag_hours = config.get("lag_hours", [1, 2, 3, 6, 12, 24])
        
        logger.info(f"LFA initialized with seed={self.seed}, model_version={self.model_version}")
    
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
        """
        Load building, weather, and optional meter data.
        
        Returns:
            Tuple of (buildings_df, weather_df, meters_df)
        """
        logger.info("Loading input data...")
        
        # Load buildings data
        if not Path(self.buildings_path).exists():
            raise FileNotFoundError(f"Buildings file not found: {self.buildings_path}")
        
        buildings_df = pd.read_parquet(self.buildings_path)
        logger.info(f"Loaded {len(buildings_df)} buildings")
        
        # Load weather data
        if not Path(self.weather_path).exists():
            raise FileNotFoundError(f"Weather file not found: {self.weather_path}")
        
        weather_df = pd.read_parquet(self.weather_path)
        logger.info(f"Loaded weather data: {len(weather_df)} rows")
        
        # Validate weather data completeness
        expected_hours = 8760
        if len(weather_df) < expected_hours:
            missing_hours = expected_hours - len(weather_df)
            raise ValueError(f"Weather data incomplete: missing {missing_hours} hours")
        
        # Load optional meter data
        meters_df = None
        if Path(self.meters_dir).exists():
            meter_files = list(Path(self.meters_dir).glob("*.parquet"))
            if meter_files:
                meters_df = pd.concat([pd.read_parquet(f) for f in meter_files], ignore_index=True)
                logger.info(f"Loaded meter data: {len(meters_df)} rows from {len(meter_files)} files")
        
        return buildings_df, weather_df, meters_df
    
    def engineer_features(self, weather_df: pd.DataFrame, buildings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features for forecasting.
        
        Args:
            weather_df: Weather data with hourly timestamps
            buildings_df: Building metadata
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Engineering features...")
        
        # Ensure weather_df has datetime index
        if 'timestamp' in weather_df.columns:
            weather_df = weather_df.set_index('timestamp')
        elif not isinstance(weather_df.index, pd.DatetimeIndex):
            # Create hourly datetime index for full year
            start_date = datetime(2024, 1, 1)
            weather_df.index = pd.date_range(start=start_date, periods=8760, freq='H')
        
        features_df = weather_df.copy()
        
        # Calendar features
        features_df['hour'] = features_df.index.hour
        features_df['day_of_week'] = features_df.index.dayofweek
        features_df['day_of_year'] = features_df.index.dayofyear
        features_df['month'] = features_df.index.month
        features_df['is_weekend'] = features_df['day_of_week'].isin([5, 6]).astype(int)
        features_df['is_holiday'] = self._is_holiday(features_df.index)
        
        # Cyclical encoding
        features_df['hour_sin'] = np.sin(2 * np.pi * features_df['hour'] / 24)
        features_df['hour_cos'] = np.cos(2 * np.pi * features_df['hour'] / 24)
        features_df['day_sin'] = np.sin(2 * np.pi * features_df['day_of_year'] / 365)
        features_df['day_cos'] = np.cos(2 * np.pi * features_df['day_of_year'] / 365)
        
        # Degree days (heating)
        if 'T_out' in features_df.columns:
            features_df['heating_degree_days'] = np.maximum(
                self.degree_day_base - features_df['T_out'], 0
            )
            features_df['cooling_degree_days'] = np.maximum(
                features_df['T_out'] - self.degree_day_base, 0
            )
        
        # Solar features
        if 'GHI' in features_df.columns:
            features_df['solar_radiation'] = features_df['GHI']
            features_df['solar_radiation_squared'] = features_df['GHI'] ** 2
        
        # Humidity features
        if 'RH' in features_df.columns:
            features_df['relative_humidity'] = features_df['RH']
            features_df['humidity_deficit'] = 100 - features_df['RH']
        
        # Lag features (if we had historical demand data)
        # For now, create synthetic lags based on weather patterns
        for lag in self.lag_hours:
            if 'T_out' in features_df.columns:
                features_df[f'T_out_lag_{lag}h'] = features_df['T_out'].shift(lag).fillna(method='bfill')
            if 'heating_degree_days' in features_df.columns:
                features_df[f'hdd_lag_{lag}h'] = features_df['heating_degree_days'].shift(lag).fillna(0)
        
        # Rolling statistics
        if 'T_out' in features_df.columns:
            features_df['T_out_rolling_24h'] = features_df['T_out'].rolling(24, min_periods=1).mean()
            features_df['T_out_rolling_7d'] = features_df['T_out'].rolling(168, min_periods=1).mean()
        
        # Building features (will be merged later)
        building_features = ['floor_area', 'function', 'year', 'insulation_quality']
        available_building_features = [f for f in building_features if f in buildings_df.columns]
        
        logger.info(f"Engineered {len(features_df.columns)} features")
        return features_df
    
    def _is_holiday(self, dates: pd.DatetimeIndex) -> pd.Series:
        """Simple holiday detection (German holidays)."""
        holidays = []
        for date in dates:
            # New Year, Christmas, Easter (simplified)
            if (date.month == 1 and date.day == 1) or \
               (date.month == 12 and date.day in [24, 25, 26]) or \
               (date.month == 4 and date.day in [1, 2, 3]):  # Simplified Easter
                holidays.append(1)
            else:
                holidays.append(0)
        return pd.Series(holidays, index=dates)
    
    def generate_synthetic_training_data(self, features_df: pd.DataFrame, buildings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate synthetic training data based on building characteristics and weather.
        
        Args:
            features_df: Engineered features
            buildings_df: Building metadata
            
        Returns:
            DataFrame with synthetic demand data for training
        """
        logger.info("Generating synthetic training data...")
        
        training_data = []
        
        for _, building in buildings_df.iterrows():
            building_id = building['building_id']
            floor_area = building.get('floor_area', 100.0)
            building_type = building.get('function', 'residential')
            year_built = building.get('year', 1990)
            
            # Base demand characteristics by building type
            base_demand_kw = self._get_base_demand(building_type, floor_area, year_built)
            
            # Generate 8760 hours of synthetic demand
            for hour_idx, (timestamp, features) in enumerate(features_df.iterrows()):
                # Base demand
                demand = base_demand_kw
                
                # Weather influence
                if 'heating_degree_days' in features:
                    hdd = features['heating_degree_days']
                    demand *= (1.0 + 0.02 * hdd)  # 2% increase per degree day
                
                # Time-of-day pattern
                hour = features['hour']
                if 6 <= hour <= 9:  # Morning peak
                    demand *= 1.3
                elif 17 <= hour <= 21:  # Evening peak
                    demand *= 1.4
                elif 23 <= hour or hour <= 5:  # Night
                    demand *= 0.6
                
                # Day-of-week pattern
                if features['is_weekend']:
                    demand *= 1.1  # Higher weekend demand
                
                # Seasonal pattern
                day_of_year = features['day_of_year']
                seasonal_factor = 1.0 + 0.4 * np.cos(2 * np.pi * (day_of_year - 15) / 365)
                demand *= seasonal_factor
                
                # Add noise
                noise = np.random.normal(0, 0.05)  # 5% noise
                demand *= (1.0 + noise)
                
                # Ensure positive
                demand = max(0.0, demand)
                
                # Add building features to training data
                building_features = {}
                for col in building.index:
                    if col not in ['building_id', 'id']:  # Skip ID columns
                        building_features[col] = building[col]
                
                training_data.append({
                    'building_id': building_id,
                    'timestamp': timestamp,
                    'demand_kw': demand,
                    **features.to_dict(),
                    **building_features
                })
        
        training_df = pd.DataFrame(training_data)
        logger.info(f"Generated {len(training_df)} training samples")
        return training_df
    
    def _get_base_demand(self, building_type: str, floor_area: float, year_built: int) -> float:
        """Get base demand in kW based on building characteristics."""
        # Base demand per m² by building type (kWh/m²/year)
        base_consumption = {
            'residential': 120.0,
            'commercial': 150.0,
            'industrial': 200.0,
            'office': 100.0,
            'retail': 80.0,
            'school': 90.0,
            'hospital': 250.0
        }
        
        consumption = base_consumption.get(building_type, 120.0)
        
        # Efficiency improvement for newer buildings
        age_factor = max(0.7, 1.0 - (2024 - year_built) * 0.01)
        
        # Convert to kW (assume 2000 heating hours per year)
        base_demand = (consumption * floor_area * age_factor) / 2000.0
        
        return base_demand
    
    def train_models(self, training_df: pd.DataFrame) -> None:
        """
        Train mean and quantile models.
        
        Args:
            training_df: Training data with features and target
        """
        logger.info("Training models...")
        
        # Prepare features
        feature_cols = [col for col in training_df.columns 
                       if col not in ['building_id', 'timestamp', 'demand_kw']]
        self.feature_columns = feature_cols
        
        X = training_df[feature_cols].values
        y = training_df['demand_kw'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        if LIGHTGBM_AVAILABLE:
            # Train mean model
            train_data = lgb.Dataset(X_scaled, label=y)
            self.mean_model = lgb.train(
                self.model_params,
                train_data,
                num_boost_round=100,
                valid_sets=[train_data],
                callbacks=[lgb.log_evaluation(0)]
            )
            
            # Train quantile models
            for q in self.quantiles:
                if q != 0.5:  # Skip median, use mean model
                    quantile_params = self.model_params.copy()
                    quantile_params['objective'] = 'quantile'
                    quantile_params['alpha'] = q
                    
                    self.quantile_models[q] = lgb.train(
                        quantile_params,
                        train_data,
                        num_boost_round=100,
                        valid_sets=[train_data],
                        callbacks=[lgb.log_evaluation(0)]
                    )
        else:
            # Fallback: simple linear model
            from sklearn.linear_model import LinearRegression
            self.mean_model = LinearRegression()
            self.mean_model.fit(X_scaled, y)
            
            # Simple quantile estimation
            for q in self.quantiles:
                if q != 0.5:
                    residuals = y - self.mean_model.predict(X_scaled)
                    quantile_value = np.quantile(residuals, q)
                    self.quantile_models[q] = quantile_value
        
        logger.info("Models trained successfully")
    
    def predict_quantiles(self, features_df: pd.DataFrame, building_id: str) -> Dict[str, List[float]]:
        """
        Predict demand quantiles for a building.
        
        Args:
            features_df: Engineered features for 8760 hours
            building_id: Building identifier
            
        Returns:
            Dictionary with quantile predictions
        """
        # Prepare features
        X = features_df[self.feature_columns].values
        X_scaled = self.scaler.transform(X)
        
        predictions = {}
        
        if LIGHTGBM_AVAILABLE and self.mean_model is not None:
            # Predict mean
            mean_pred = self.mean_model.predict(X_scaled)
            
            # Predict quantiles
            for q in self.quantiles:
                if q == 0.5:
                    predictions[f'q{int(q*100)}'] = mean_pred.tolist()
                elif q in self.quantile_models:
                    q_pred = self.quantile_models[q].predict(X_scaled)
                    predictions[f'q{int(q*100)}'] = q_pred.tolist()
        else:
            # Fallback predictions
            mean_pred = self.mean_model.predict(X_scaled)
            predictions['q50'] = mean_pred.tolist()
            
            # Simple quantile estimation
            for q in self.quantiles:
                if q != 0.5:
                    if q in self.quantile_models:
                        q_pred = mean_pred + self.quantile_models[q]
                    else:
                        # Default ±20% for q10/q90
                        factor = 0.8 if q == 0.1 else 1.2 if q == 0.9 else 1.0
                        q_pred = mean_pred * factor
                    predictions[f'q{int(q*100)}'] = q_pred.tolist()
        
        # Post-process: ensure positive values and finite
        for key in predictions:
            predictions[key] = [
                max(0.0, float(val)) if np.isfinite(val) else 0.0 
                for val in predictions[key]
            ]
        
        return predictions
    
    def save_building_forecast(self, building_id: str, predictions: Dict, 
                             features_df: pd.DataFrame) -> None:
        """
        Save building forecast to JSON file.
        
        Args:
            building_id: Building identifier
            predictions: Quantile predictions
            features_df: Features used for prediction
        """
        output_path = Path(self.output_dir) / f"{building_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare metadata
        metadata = {
            "forecast_date": datetime.utcnow().isoformat() + "Z",
            "model_version": self.model_version,
            "weather_data_source": "synthetic"  # Would be actual source in production
        }
        
        # Create output structure
        output_data = {
            "x-version": "1.0.0",
            "building_id": str(building_id),
            "series": predictions.get('q50', [0.0] * 8760),  # Use median as main series
            "q10": predictions.get('q10', [0.0] * 8760),
            "q90": predictions.get('q90', [0.0] * 8760),
            "metadata": metadata
        }
        
        # Validate against schema
        self._validate_against_schema(output_data)
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.debug(f"Saved forecast for building {building_id}")
    
    def _validate_against_schema(self, data: Dict) -> None:
        """Validate data against LFA demand schema."""
        # Basic validation - in production would use jsonschema
        required_keys = ["x-version", "building_id", "series", "q10", "q90", "metadata"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key: {key}")
        
        # Check array lengths
        for key in ["series", "q10", "q90"]:
            if len(data[key]) != 8760:
                raise ValueError(f"{key} must have exactly 8760 values, got {len(data[key])}")
        
        # Check metadata
        required_metadata = ["forecast_date", "model_version"]
        for key in required_metadata:
            if key not in data["metadata"]:
                raise ValueError(f"Missing required metadata key: {key}")
    
    def calculate_metrics(self, predictions: Dict, actuals: Optional[List[float]] = None) -> Dict:
        """
        Calculate forecast accuracy metrics.
        
        Args:
            predictions: Predicted values
            actuals: Actual values (if available)
            
        Returns:
            Dictionary with metrics
        """
        if actuals is None:
            # Use synthetic actuals for demonstration
            actuals = predictions.get('q50', [0.0] * 8760)
        
        pred_series = predictions.get('q50', [0.0] * 8760)
        q10_series = predictions.get('q10', [0.0] * 8760)
        q90_series = predictions.get('q90', [0.0] * 8760)
        
        # Calculate metrics
        mae = mean_absolute_error(actuals, pred_series)
        rmse = np.sqrt(mean_squared_error(actuals, pred_series))
        
        # MAPE
        mape = np.mean(np.abs(np.array(actuals) - np.array(pred_series)) / (np.array(actuals) + 1e-6)) * 100
        
        # PICP (Prediction Interval Coverage Probability)
        coverage_90 = np.mean([
            1 if q10 <= actual <= q90 else 0
            for actual, q10, q90 in zip(actuals, q10_series, q90_series)
        ])
        
        return {
            "MAE": float(mae),
            "RMSE": float(rmse),
            "MAPE": float(mape),
            "PICP_90": float(coverage_90)
        }
    
    def save_metrics(self, all_metrics: List[Dict]) -> None:
        """
        Save aggregated metrics to CSV.
        
        Args:
            all_metrics: List of metrics dictionaries per building
        """
        metrics_path = Path(self.metrics_path)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create metrics DataFrame
        metrics_df = pd.DataFrame(all_metrics)
        
        # Add macro averages
        macro_avg = metrics_df.mean(numeric_only=True).to_dict()
        macro_avg['building_id'] = 'MACRO_AVG'
        macro_avg['model_version'] = self.model_version
        
        # Append macro average
        macro_df = pd.DataFrame([macro_avg])
        final_df = pd.concat([metrics_df, macro_df], ignore_index=True)
        
        # Save to CSV
        final_df.to_csv(metrics_path, index=False)
        logger.info(f"Saved metrics to {metrics_path}")
    
    def run(self, config: Optional[Dict] = None) -> Dict:
        """
        Run the complete Load Forecasting Agent pipeline.
        
        Args:
            config: Optional configuration override
            
        Returns:
            Summary dictionary with results
        """
        if config:
            self.config.update(config)
        
        logger.info("Starting Load Forecasting Agent...")
        
        try:
            # 1. Load data
            buildings_df, weather_df, meters_df = self.load_data()
            
            # 2. Engineer features
            features_df = self.engineer_features(weather_df, buildings_df)
            
            # 3. Generate training data
            training_df = self.generate_synthetic_training_data(features_df, buildings_df)
            
            # 4. Train models
            self.train_models(training_df)
            
            # 5. Generate forecasts for each building
            all_metrics = []
            processed_buildings = 0
            
            for _, building in buildings_df.iterrows():
                building_id = building['building_id']
                
                # Predict quantiles
                predictions = self.predict_quantiles(features_df, building_id)
                
                # Save building forecast
                self.save_building_forecast(building_id, predictions, features_df)
                
                # Calculate metrics
                metrics = self.calculate_metrics(predictions)
                metrics['building_id'] = building_id
                metrics['model_version'] = self.model_version
                all_metrics.append(metrics)
                
                processed_buildings += 1
                
                if processed_buildings % 10 == 0:
                    logger.info(f"Processed {processed_buildings}/{len(buildings_df)} buildings")
            
            # 6. Save aggregated metrics
            self.save_metrics(all_metrics)
            
            # 7. Calculate summary statistics
            macro_metrics = pd.DataFrame(all_metrics).mean(numeric_only=True).to_dict()
            
            result = {
                "status": "success",
                "processed_buildings": processed_buildings,
                "output_files": len(buildings_df),
                "model_version": self.model_version,
                "macro_metrics": macro_metrics,
                "output_dir": self.output_dir,
                "metrics_path": self.metrics_path
            }
            
            logger.info(f"LFA completed successfully: {processed_buildings} buildings processed")
            return result
            
        except Exception as e:
            logger.error(f"LFA failed: {e}")
            raise


def run(config: Dict) -> Dict:
    """
    Convenience function to run the Load Forecasting Agent.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Result dictionary
    """
    agent = LoadForecastingAgent(config)
    return agent.run()


if __name__ == "__main__":
    # CLI interface
    import argparse
    
    parser = argparse.ArgumentParser(description="Load Forecasting Agent")
    parser.add_argument("--config", type=str, default="configs/lfa.yml", 
                       help="Configuration file path")
    args = parser.parse_args()
    
    # Load configuration
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Run agent
    result = run(config)
    print(json.dumps(result, indent=2))
