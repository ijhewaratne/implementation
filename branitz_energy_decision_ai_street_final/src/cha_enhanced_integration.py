"""
CHA Enhanced Integration - Complete Integration with Existing CHA System

This module provides complete integration of the enhanced network builder
with the existing CHA system, replacing hardcoded diameters with intelligent sizing.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

from __future__ import annotations
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

# Import our enhanced components
from src.cha_enhanced_network_builder import CHAEnhancedNetworkBuilder
from src.cha_pipe_sizing import CHAPipeSizingEngine
from src.cha_flow_rate_calculator import CHAFlowRateCalculator

warnings.filterwarnings("ignore")


class CHAEnhancedIntegration:
    """
    Complete integration of enhanced network builder with existing CHA system.
    
    Provides seamless integration of intelligent pipe sizing with network construction,
    replacing hardcoded diameters with flow-based intelligent sizing.
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize the enhanced integration system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        
        # Initialize components
        self.sizing_engine = CHAPipeSizingEngine(self.config.get('pipe_sizing', {}))
        self.network_builder = CHAEnhancedNetworkBuilder(self.sizing_engine)
        self.flow_calculator: Optional[CHAFlowRateCalculator] = None
        
        # Results storage
        self.lfa_data: Dict = {}
        self.flow_rates: Dict = {}
        self.enhanced_network_data: Dict = {}
        
        print(f"✅ CHA Enhanced Integration initialized")
    
    def _get_default_config(self) -> dict:
        """Get default configuration."""
        return {
            'pipe_sizing': {
                'max_velocity_ms': 2.0,
                'min_velocity_ms': 0.1,
                'max_pressure_drop_pa_per_m': 5000,
                'pipe_roughness_mm': 0.1,
                'cost_factors': {
                    'base_cost_per_mm_diameter': 0.5,
                    'installation_factor': 1.5,
                    'insulation_cost_per_m': 15.0,
                    'material_factor': 1.0
                }
            },
            'network_building': {
                'enable_graduated_sizing': True,
                'enable_validation': True,
                'validation_threshold': 0.95
            }
        }
    
    def load_lfa_data(self, lfa_data: Dict) -> bool:
        """
        Load LFA data for flow calculations.
        
        Args:
            lfa_data: LFA heat demand data per building
        
        Returns:
            success: True if loading successful
        """
        try:
            self.lfa_data = lfa_data
            self.flow_calculator = CHAFlowRateCalculator(lfa_data)
            
            print(f"✅ LFA data loaded for {len(lfa_data)} buildings")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load LFA data: {e}")
            return False
    
    def calculate_flow_rates(self) -> bool:
        """
        Calculate flow rates for all buildings.
        
        Returns:
            success: True if calculation successful
        """
        if not self.flow_calculator:
            print("❌ Flow calculator not initialized")
            return False
        
        try:
            # Calculate building flows
            building_flows = self.flow_calculator.calculate_all_building_flows()
            
            # Extract flow rates for network building
            self.flow_rates = {
                building_id: result.mass_flow_rate_kg_s 
                for building_id, result in building_flows.items()
            }
            
            print(f"✅ Flow rates calculated for {len(self.flow_rates)} buildings")
            return True
            
        except Exception as e:
            print(f"❌ Failed to calculate flow rates: {e}")
            return False
    
    def create_enhanced_network(self) -> bool:
        """
        Create enhanced network with intelligent pipe sizing.
        
        Returns:
            success: True if network creation successful
        """
        if not self.flow_rates:
            print("❌ No flow rates available")
            return False
        
        try:
            # Create sized dual-pipe network
            self.enhanced_network_data = self.network_builder.create_sized_dual_pipe_network(self.flow_rates)
            
            # Apply graduated sizing if enabled
            if self.config.get('network_building', {}).get('enable_graduated_sizing', True):
                self.enhanced_network_data = self.network_builder.apply_graduated_sizing(self.enhanced_network_data)
            
            # Validate network sizing if enabled
            if self.config.get('network_building', {}).get('enable_validation', True):
                self.enhanced_network_data = self.network_builder.validate_network_sizing(self.enhanced_network_data)
            
            print(f"✅ Enhanced network created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create enhanced network: {e}")
            return False
    
    def integrate_with_cha_system(self, cha_output_dir: str) -> bool:
        """
        Integrate enhanced network with existing CHA system.
        
        Args:
            cha_output_dir: Directory containing CHA output files
        
        Returns:
            success: True if integration successful
        """
        if not self.enhanced_network_data:
            print("❌ No enhanced network data available")
            return False
        
        try:
            cha_dir = Path(cha_output_dir)
            
            # Create enhanced pipe data files
            self._create_enhanced_pipe_files(cha_dir)
            
            # Create enhanced service connections file
            self._create_enhanced_service_connections_file(cha_dir)
            
            # Create enhanced network summary
            self._create_enhanced_network_summary(cha_dir)
            
            print(f"✅ Enhanced network integrated with CHA system")
            return True
            
        except Exception as e:
            print(f"❌ Failed to integrate with CHA system: {e}")
            return False
    
    def _create_enhanced_pipe_files(self, cha_dir: Path) -> None:
        """Create enhanced pipe data files."""
        # Create enhanced supply pipes CSV
        supply_pipes_data = []
        for pipe in self.enhanced_network_data.get('supply_pipes', []):
            supply_pipes_data.append({
                'pipe_id': pipe['pipe_id'],
                'start_node': pipe['start_node'],
                'end_node': pipe['end_node'],
                'length_m': pipe['length_m'],
                'diameter_m': pipe['diameter_m'],
                'diameter_nominal': pipe['diameter_nominal'],
                'pipe_category': pipe['pipe_category'],
                'pipe_type': pipe['pipe_type'],
                'flow_rate_kg_s': pipe['flow_rate_kg_s'],
                'velocity_ms': pipe['velocity_ms'],
                'pressure_drop_bar': pipe['pressure_drop_bar'],
                'cost_eur': pipe['cost_eur'],
                'material': pipe['material'],
                'insulation': pipe['insulation'],
                'building_served': pipe['building_served'],
                'street_id': pipe['street_id'],
                'flow_direction': pipe['flow_direction'],
                'standards_compliant': len(pipe['violations']) == 0,
                'violations_count': len(pipe['violations'])
            })
        
        supply_df = pd.DataFrame(supply_pipes_data)
        supply_df.to_csv(cha_dir / "enhanced_supply_pipes.csv", index=False)
        
        # Create enhanced return pipes CSV
        return_pipes_data = []
        for pipe in self.enhanced_network_data.get('return_pipes', []):
            return_pipes_data.append({
                'pipe_id': pipe['pipe_id'],
                'start_node': pipe['start_node'],
                'end_node': pipe['end_node'],
                'length_m': pipe['length_m'],
                'diameter_m': pipe['diameter_m'],
                'diameter_nominal': pipe['diameter_nominal'],
                'pipe_category': pipe['pipe_category'],
                'pipe_type': pipe['pipe_type'],
                'flow_rate_kg_s': pipe['flow_rate_kg_s'],
                'velocity_ms': pipe['velocity_ms'],
                'pressure_drop_bar': pipe['pressure_drop_bar'],
                'cost_eur': pipe['cost_eur'],
                'material': pipe['material'],
                'insulation': pipe['insulation'],
                'building_served': pipe['building_served'],
                'street_id': pipe['street_id'],
                'flow_direction': pipe['flow_direction'],
                'standards_compliant': len(pipe['violations']) == 0,
                'violations_count': len(pipe['violations'])
            })
        
        return_df = pd.DataFrame(return_pipes_data)
        return_df.to_csv(cha_dir / "enhanced_return_pipes.csv", index=False)
    
    def _create_enhanced_service_connections_file(self, cha_dir: Path) -> None:
        """Create enhanced service connections file."""
        service_connections_data = []
        for service in self.enhanced_network_data.get('service_connections', []):
            service_connections_data.append({
                'building_id': service['building_id'],
                'connection_x': service['connection_x'],
                'connection_y': service['connection_y'],
                'building_x': service['building_x'],
                'building_y': service['building_y'],
                'distance_to_street': service['distance_to_street'],
                'street_segment_id': service['street_segment_id'],
                'street_name': service['street_name'],
                'heating_load_kw': service['heating_load_kw'],
                'annual_heat_demand_kwh': service['annual_heat_demand_kwh'],
                'building_type': service['building_type'],
                'building_area_m2': service['building_area_m2'],
                'pipe_type': service['pipe_type'],
                'temperature_c': service['temperature_c'],
                'flow_direction': service['flow_direction'],
                'flow_rate_kg_s': self.flow_rates.get(service['building_id'], 0.0)
            })
        
        service_df = pd.DataFrame(service_connections_data)
        service_df.to_csv(cha_dir / "enhanced_service_connections.csv", index=False)
    
    def _create_enhanced_network_summary(self, cha_dir: Path) -> None:
        """Create enhanced network summary file."""
        summary_data = {
            'network_statistics': self.enhanced_network_data.get('network_statistics', {}),
            'sizing_summary': self.enhanced_network_data.get('sizing_summary', {}),
            'validation_result': self.enhanced_network_data.get('validation_result', {}),
            'graduated_sizing': self.enhanced_network_data.get('graduated_sizing', {}),
            'flow_rates': self.flow_rates,
            'lfa_data_summary': {
                'total_buildings': len(self.lfa_data),
                'total_flow_kg_s': sum(self.flow_rates.values()),
                'average_flow_kg_s': sum(self.flow_rates.values()) / len(self.flow_rates) if self.flow_rates else 0
            }
        }
        
        with open(cha_dir / "enhanced_network_summary.json", 'w') as f:
            json.dump(summary_data, f, indent=2)
    
    def run_complete_enhanced_integration(self, lfa_data: Dict, cha_output_dir: str) -> Dict:
        """
        Run complete enhanced integration process.
        
        Args:
            lfa_data: LFA heat demand data per building
            cha_output_dir: Directory containing CHA output files
        
        Returns:
            results: Complete integration results
        """
        print(f"\n🚀 Starting Complete Enhanced Integration Process")
        print(f"   Buildings: {len(lfa_data)}")
        print(f"   CHA Output: {cha_output_dir}")
        
        try:
            # Step 1: Load LFA data
            print(f"\n📊 Step 1: Loading LFA Data")
            if not self.load_lfa_data(lfa_data):
                raise Exception("Failed to load LFA data")
            
            # Step 2: Calculate flow rates
            print(f"\n🔄 Step 2: Calculating Flow Rates")
            if not self.calculate_flow_rates():
                raise Exception("Failed to calculate flow rates")
            
            # Step 3: Create enhanced network
            print(f"\n🏗️ Step 3: Creating Enhanced Network")
            if not self.create_enhanced_network():
                raise Exception("Failed to create enhanced network")
            
            # Step 4: Integrate with CHA system
            print(f"\n🔧 Step 4: Integrating with CHA System")
            if not self.integrate_with_cha_system(cha_output_dir):
                raise Exception("Failed to integrate with CHA system")
            
            print(f"\n🎉 Complete Enhanced Integration Process Finished Successfully!")
            
            return {
                'lfa_data': self.lfa_data,
                'flow_rates': self.flow_rates,
                'enhanced_network_data': self.enhanced_network_data,
                'summary': self._generate_summary()
            }
            
        except Exception as e:
            print(f"❌ Error in enhanced integration process: {e}")
            raise
    
    def _generate_summary(self) -> Dict:
        """Generate summary of integration results."""
        network_stats = self.enhanced_network_data.get('network_statistics', {})
        sizing_summary = self.enhanced_network_data.get('sizing_summary', {})
        validation_result = self.enhanced_network_data.get('validation_result', {})
        
        return {
            'buildings': len(self.lfa_data),
            'flow_rates': len(self.flow_rates),
            'total_flow_kg_s': sum(self.flow_rates.values()),
            'total_pipes': network_stats.get('total_pipes', 0),
            'total_length_m': network_stats.get('total_length_m', 0),
            'total_cost_eur': network_stats.get('total_cost_eur', 0),
            'compliant_pipes': sizing_summary.get('compliant_pipes', 0),
            'compliance_rate': sizing_summary.get('compliance_rate', 0),
            'overall_compliant': validation_result.get('overall_compliant', False),
            'critical_violations': len(validation_result.get('critical_violations', []))
        }
    
    def export_enhanced_results(self, output_path: str) -> None:
        """
        Export enhanced integration results to JSON file.
        
        Args:
            output_path: Output file path
        """
        export_data = {
            'summary': self._generate_summary(),
            'lfa_data': self.lfa_data,
            'flow_rates': self.flow_rates,
            'enhanced_network_data': self.enhanced_network_data
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Enhanced integration results exported to {output_path}")
    
    def print_enhanced_summary(self) -> None:
        """Print comprehensive summary of enhanced integration results."""
        summary = self._generate_summary()
        
        print(f"\n📊 ENHANCED INTEGRATION SUMMARY")
        print(f"=" * 50)
        print(f"🏗️ OVERVIEW:")
        print(f"   Buildings: {summary['buildings']}")
        print(f"   Flow Rates: {summary['flow_rates']}")
        print(f"   Total Flow: {summary['total_flow_kg_s']:.2f} kg/s")
        print(f"   Total Pipes: {summary['total_pipes']}")
        print(f"   Total Length: {summary['total_length_m']:.0f} m")
        print(f"   Total Cost: €{summary['total_cost_eur']:.0f}")
        print(f"")
        print(f"✅ COMPLIANCE:")
        print(f"   Compliant Pipes: {summary['compliant_pipes']}/{summary['total_pipes']}")
        print(f"   Compliance Rate: {summary['compliance_rate']:.1%}")
        print(f"   Overall Compliant: {summary['overall_compliant']}")
        print(f"   Critical Violations: {summary['critical_violations']}")
        
        # Print network builder summary
        if hasattr(self.network_builder, 'print_network_summary'):
            self.network_builder.print_network_summary()


# Example usage and testing
if __name__ == "__main__":
    # Example LFA data
    lfa_data = {
        'building_1': {
            'series': [10.0, 12.0, 8.0, 15.0, 9.0] + [8.0] * 8755
        },
        'building_2': {
            'series': [8.0, 10.0, 7.0, 12.0, 8.5] + [7.5] * 8755
        },
        'building_3': {
            'series': [12.0, 14.0, 10.0, 16.0, 11.0] + [9.0] * 8755
        }
    }
    
    # Create enhanced integration system
    enhanced_integration = CHAEnhancedIntegration()
    
    try:
        # Run complete enhanced integration
        results = enhanced_integration.run_complete_enhanced_integration(
            lfa_data, 
            "processed/cha"
        )
        
        # Print summary
        enhanced_integration.print_enhanced_summary()
        
        # Export results
        enhanced_integration.export_enhanced_results("enhanced_integration_results.json")
        
        print(f"\n🎉 Enhanced Integration Process Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Error in enhanced integration process: {e}")
        import traceback
        traceback.print_exc()
