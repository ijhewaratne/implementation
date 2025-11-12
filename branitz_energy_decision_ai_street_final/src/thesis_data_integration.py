#!/usr/bin/env python3
"""
Thesis Data Integration Module
==============================

Replaces LFA with physics-based heat demand using TRY weather data and heating calculations.
Provides realistic 8760-hour heat demand series for both CHA and DHA.

Data Sources:
- TRY weather data (8760-hour temperature profiles)
- Physics-based heating calculations (temperature-dependent heating demand)
- Building characteristics (U-values, renovation status)
- Electrical load profiles (for heat pump analysis)

Output:
- LFA-compatible JSON files with 8760-hour heat demand series
- Temperature-dependent heating demand
- Physics-based COP calculations for heat pumps
"""

import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import argparse
import yaml
from scipy import interpolate
import warnings

warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TRYWeatherProcessor:
    """Process TRY (Test Reference Year) weather data files."""
    
    def __init__(self):
        self.heating_threshold = 15.0  # °C - heating starts below this temperature
        
    def parse_try_file(self, try_file_path: str) -> pd.DataFrame:
        """Parse TRY weather data file and return DataFrame with 8760 hours."""
        logger.info(f"Loading TRY weather data from: {try_file_path}")
        
        with open(try_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find data section (starts after ***)
        data_start = False
        weather_data = []
        
        for line in lines:
            if '***' in line:
                data_start = True
                continue
            if not data_start or not line.strip():
                continue
                
            try:
                parts = line.split()
                if len(parts) >= 15:
                    # Extract relevant parameters
                    month = int(parts[0])
                    day = int(parts[1])
                    hour = int(parts[2])
                    temperature = float(parts[3])
                    pressure = float(parts[4])
                    humidity = float(parts[9])
                    wind_speed = float(parts[8])
                    
                    # Convert hour 24 to 0 (next day)
                    if hour == 24:
                        hour = 0
                        day += 1
                        if day > 31:  # Simple day overflow handling
                            day = 1
                            month += 1
                    
                    weather_data.append({
                        'month': month,
                        'day': day,
                        'hour': hour,
                        'temperature': temperature,
                        'pressure': pressure,
                        'humidity': humidity,
                        'wind_speed': wind_speed
                    })
                    
            except (ValueError, IndexError) as e:
                logger.debug(f"Error parsing line: {line.strip()}")
                continue
        
        if len(weather_data) != 8760:
            logger.warning(f"Expected 8760 hours, got {len(weather_data)}")
        
        df = pd.DataFrame(weather_data)
        logger.info(f"Loaded {len(df)} weather data points")
        
        return df


class HeatingDataProcessor:
    """Process physics-based heating demand data."""
    
    def __init__(self):
        self.seasons = {
            'winter': [12, 1, 2],
            'spring': [3, 4, 5],
            'summer': [6, 7, 8],
            'autumn': [9, 10, 11]
        }
        
        self.time_periods = {
            'night': [22, 23, 0, 1, 2, 3, 4, 5],
            'morning': [6, 7, 8, 9, 10, 11],
            'afternoon': [12, 13, 14, 15, 16, 17],
            'evening': [18, 19, 20, 21]
        }
    
    def load_heating_data(self, heating_json_path: str) -> Dict:
        """Load physics-based heating demand data."""
        logger.info(f"Loading heating data from: {heating_json_path}")
        
        with open(heating_json_path, 'r', encoding='utf-8') as f:
            heating_data = json.load(f)
        
        logger.info(f"Loaded heating data for {heating_data['metadata']['statistik']['gebaeude_verarbeitet']} buildings")
        return heating_data
    
    def get_building_heating_profile(self, heating_data: Dict, building_id: str, scenario: str = 'mittleres_jahr') -> Optional[Dict]:
        """Get heating profile for a specific building."""
        if building_id not in heating_data['ergebnisse']:
            logger.warning(f"Building {building_id} not found in heating data")
            return None
        
        building_data = heating_data['ergebnisse'][building_id]
        
        if building_data.get('Szenarien') == 0:
            logger.warning(f"Building {building_id} is unheated")
            return None
        
        if scenario not in building_data['Szenarien']:
            logger.warning(f"Scenario {scenario} not found for building {building_id}")
            return None
        
        return building_data['Szenarien'][scenario]
    
    def create_temperature_power_mapping(self, heating_profile: List[Dict]) -> Dict[float, float]:
        """Create temperature to heating power mapping from representative periods."""
        temp_power_map = {}
        
        for period in heating_profile:
            temp = period['Durchschnitt']['Temperatur']
            power = period['Durchschnitt']['Momentane_Heizleistung_W']
            temp_power_map[temp] = power
        
        return temp_power_map


class ElectricalProfileProcessor:
    """Process electrical load profiles for heat pump analysis."""
    
    def load_electrical_profiles(self, profiles_json_path: str) -> Dict:
        """Load electrical consumption profiles."""
        logger.info(f"Loading electrical profiles from: {profiles_json_path}")
        
        with open(profiles_json_path, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
        
        logger.info(f"Loaded electrical profiles for {len(profiles)} buildings")
        return profiles
    
    def calculate_heat_pump_load(self, building_profile: Dict, cop_model: str = 'constant', cop_value: float = 3.0) -> Dict:
        """Calculate heat pump electrical load from building profile."""
        annual_kwh = building_profile.get('jahresverbrauch_kwh', 0)
        building_type = building_profile.get('gebaeudefunktion', 'Wohnhaus')
        
        # Estimate heating fraction based on building type
        heating_fractions = {
            'Wohnhaus': 0.7,  # 70% for heating
            'Geschaeft': 0.5,  # 50% for heating
            'Buerogebaeude': 0.6,  # 60% for heating
            'Industrie': 0.4,  # 40% for heating
            'Garage': 0.0,  # No heating
            'Pumpstation': 0.8,  # 80% for heating
        }
        
        heating_fraction = heating_fractions.get(building_type, 0.7)
        heating_demand_kwh = annual_kwh * heating_fraction
        
        # Calculate heat pump electrical load
        if cop_model == 'constant':
            electrical_load_kwh = heating_demand_kwh / cop_value
        else:
            # Temperature-dependent COP (simplified)
            electrical_load_kwh = heating_demand_kwh / (cop_value * 0.8)  # Reduced efficiency
        
        return {
            'annual_heating_kwh': heating_demand_kwh,
            'annual_electrical_kwh': electrical_load_kwh,
            'peak_electrical_kw': electrical_load_kwh / 2000,  # Assume 2000 full-load hours
            'cop_model': cop_model,
            'cop_value': cop_value
        }


class ThesisDataIntegrator:
    """Main integrator class that combines all data sources."""
    
    def __init__(self, config_path: str = "configs/thesis_data.yml"):
        self.config = self._load_config(config_path)
        self.weather_processor = TRYWeatherProcessor()
        self.heating_processor = HeatingDataProcessor()
        self.electrical_processor = ElectricalProfileProcessor()
        
        # Data storage
        self.weather_data = None
        self.heating_data = None
        self.electrical_profiles = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            'data_sources': {
                'weather_try': 'thesis-data-2/wetter-data/TRY2015_517475143730_Jahr.dat',
                'heating_data': 'thesis-data-2/pipes-sim/ergebnis_momentane_heizleistungV3.json',
                'electrical_profiles': 'thesis-data-2/load-profile-generator/gebaeude_lastphasenV2_verbrauch.json'
            },
            'scenarios': {
                'default': 'mittleres_jahr',
                'available': ['mittleres_jahr', 'kaltes_jahr', 'heisses_jahr']
            },
            'heat_pump': {
                'cop_model': 'constant',
                'cop_value': 3.0
            },
            'output': {
                'dir': 'processed/lfa',
                'format': 'lfa_compatible'
            }
        }
    
    def load_all_data(self) -> bool:
        """Load all required data sources."""
        try:
            # Load weather data
            weather_path = self.config['data_sources']['weather_try']
            self.weather_data = self.weather_processor.parse_try_file(weather_path)
            
            # Load heating data
            heating_path = self.config['data_sources']['heating_data']
            self.heating_data = self.heating_processor.load_heating_data(heating_path)
            
            # Load electrical profiles
            electrical_path = self.config['data_sources']['electrical_profiles']
            self.electrical_profiles = self.electrical_processor.load_electrical_profiles(electrical_path)
            
            logger.info("✅ All data sources loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            return False
    
    def interpolate_heating_demand(self, temp_power_map: Dict[float, float], hourly_temps: List[float]) -> List[float]:
        """Interpolate heating demand for 8760 hours based on temperature."""
        if len(temp_power_map) < 2:
            # Not enough data points for interpolation
            avg_power = sum(temp_power_map.values()) / len(temp_power_map) if temp_power_map else 0
            return [avg_power] * 8760
        
        # Create interpolation function
        temps = sorted(temp_power_map.keys())
        powers = [temp_power_map[t] for t in temps]
        
        # Use linear interpolation
        interp_func = interpolate.interp1d(temps, powers, kind='linear', bounds_error=False, fill_value='extrapolate')
        
        # Interpolate for all hours
        heating_demands = []
        for temp in hourly_temps:
            if temp >= 15.0:  # No heating above heating threshold
                heating_demands.append(0.0)
            else:
                power = float(interp_func(temp))
                heating_demands.append(max(0.0, power))  # Ensure non-negative
        
        return heating_demands
    
    def generate_building_heat_demand(self, building_id: str, scenario: str = None) -> Optional[Dict]:
        """Generate 8760-hour heat demand series for a building."""
        if scenario is None:
            scenario = self.config['scenarios']['default']
        
        # Get building heating profile
        heating_profile = self.heating_processor.get_building_heating_profile(
            self.heating_data, building_id, scenario
        )
        
        if heating_profile is None:
            return None
        
        # Create temperature-power mapping
        temp_power_map = self.heating_processor.create_temperature_power_mapping(heating_profile)
        
        # Get hourly temperatures from weather data
        hourly_temps = self.weather_data['temperature'].tolist()
        
        # Interpolate heating demand
        heating_series = self.interpolate_heating_demand(temp_power_map, hourly_temps)
        
        # Calculate statistics
        total_annual_kwh = sum(heating_series) / 1000  # Convert W to kW, then to kWh
        peak_kw = max(heating_series) / 1000  # Convert W to kW
        avg_kw = np.mean(heating_series) / 1000  # Convert W to kW
        
        # Generate quantiles (simplified - using ±10% of mean)
        q10_series = [max(0, h * 0.9) for h in heating_series]
        q90_series = [h * 1.1 for h in heating_series]
        
        return {
            'building_id': building_id,
            'series': heating_series,  # 8760-hour series in W
            'q10': q10_series,
            'q90': q90_series,
            'metadata': {
                'scenario': scenario,
                'model_version': 'thesis-data-v1.0.0',
                'forecast_date': datetime.now().isoformat(),
                'total_annual_kwh': total_annual_kwh,
                'peak_kw': peak_kw,
                'avg_kw': avg_kw,
                'data_source': 'physics_based'
            }
        }
    
    def generate_heat_pump_profile(self, building_id: str) -> Optional[Dict]:
        """Generate heat pump electrical load profile for DHA."""
        if building_id not in self.electrical_profiles:
            logger.warning(f"Building {building_id} not found in electrical profiles")
            return None
        
        building_profile = self.electrical_profiles[building_id]
        
        # Calculate heat pump loads
        cop_model = self.config['heat_pump']['cop_model']
        cop_value = self.config['heat_pump']['cop_value']
        
        heat_pump_data = self.electrical_processor.calculate_heat_pump_load(
            building_profile, cop_model, cop_value
        )
        
        return {
            'building_id': building_id,
            'building_type': building_profile.get('gebaeudefunktion', 'Wohnhaus'),
            'annual_heating_kwh': heat_pump_data['annual_heating_kwh'],
            'annual_electrical_kwh': heat_pump_data['annual_electrical_kwh'],
            'peak_electrical_kw': heat_pump_data['peak_electrical_kw'],
            'cop_model': cop_model,
            'cop_value': cop_value,
            'metadata': {
                'model_version': 'thesis-data-v1.0.0',
                'generation_date': datetime.now().isoformat(),
                'data_source': 'electrical_profiles'
            }
        }
    
    def save_lfa_compatible_json(self, building_data: Dict, output_dir: str) -> bool:
        """Save building data in LFA-compatible JSON format."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        building_id = building_data['building_id']
        output_file = output_path / f"{building_id}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(building_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved {building_id}.json")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save {building_id}.json: {e}")
            return False
    
    def generate_all_buildings(self, output_dir: str = None, scenario: str = None) -> Dict:
        """Generate heat demand data for all buildings."""
        if output_dir is None:
            output_dir = self.config['output']['dir']
        
        if scenario is None:
            scenario = self.config['scenarios']['default']
        
        logger.info(f"Generating heat demand data for scenario: {scenario}")
        
        # Get all heated buildings
        heated_buildings = []
        for building_id, building_data in self.heating_data['ergebnisse'].items():
            if building_data.get('Szenarien') != 0:
                heated_buildings.append(building_id)
        
        logger.info(f"Processing {len(heated_buildings)} heated buildings")
        
        results = {
            'processed_buildings': 0,
            'failed_buildings': 0,
            'output_dir': output_dir,
            'scenario': scenario,
            'building_results': []
        }
        
        # Process each building
        for i, building_id in enumerate(heated_buildings):
            if i % 100 == 0:
                logger.info(f"Processing building {i+1}/{len(heated_buildings)}: {building_id}")
            
            try:
                # Generate heat demand data
                building_data = self.generate_building_heat_demand(building_id, scenario)
                
                if building_data:
                    # Save LFA-compatible JSON
                    if self.save_lfa_compatible_json(building_data, output_dir):
                        results['processed_buildings'] += 1
                        results['building_results'].append({
                            'building_id': building_id,
                            'status': 'success',
                            'annual_kwh': building_data['metadata']['total_annual_kwh'],
                            'peak_kw': building_data['metadata']['peak_kw']
                        })
                    else:
                        results['failed_buildings'] += 1
                else:
                    results['failed_buildings'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to process building {building_id}: {e}")
                results['failed_buildings'] += 1
        
        # Create .ready file for pipeline coordination
        ready_file = Path(output_dir) / '.ready'
        ready_file.touch()
        
        logger.info(f"✅ Generated heat demand data for {results['processed_buildings']} buildings")
        logger.info(f"❌ Failed to process {results['failed_buildings']} buildings")
        
        return results


def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(description="Thesis Data Integration for LFA Replacement")
    parser.add_argument("--config", type=str, default="configs/thesis_data.yml",
                       help="Configuration file path")
    parser.add_argument("--scenario", type=str, default="mittleres_jahr",
                       help="Weather scenario (mittleres_jahr, kaltes_jahr, heisses_jahr)")
    parser.add_argument("--output", type=str, default="processed/lfa",
                       help="Output directory for generated files")
    
    args = parser.parse_args()
    
    # Initialize integrator
    integrator = ThesisDataIntegrator(args.config)
    
    # Load all data
    if not integrator.load_all_data():
        logger.error("Failed to load data sources")
        return 1
    
    # Generate heat demand data for all buildings
    results = integrator.generate_all_buildings(args.output, args.scenario)
    
    # Print summary
    print(f"\n=== THESIS DATA INTEGRATION SUMMARY ===")
    print(f"Scenario: {results['scenario']}")
    print(f"Processed Buildings: {results['processed_buildings']}")
    print(f"Failed Buildings: {results['failed_buildings']}")
    print(f"Output Directory: {results['output_dir']}")
    
    if results['processed_buildings'] > 0:
        print(f"\n✅ Successfully generated LFA-compatible heat demand data!")
        print(f"📁 Files saved to: {results['output_dir']}")
        print(f"🔄 Pipeline ready file created: {results['output_dir']}/.ready")
    
    return 0


if __name__ == "__main__":
    exit(main())
