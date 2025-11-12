"""
CHA Flow Calculation Engine - Heat Demand to Mass Flow Rate Conversion

This module implements flow rate calculations from heat demand data,
including peak hour analysis and network flow aggregation.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

from __future__ import annotations
import json
import math
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


@dataclass
class FlowCalculationResult:
    """Result of flow calculation."""
    building_id: str
    peak_heat_demand_kw: float
    mass_flow_kg_s: float
    volume_flow_m3_s: float
    peak_hour: int
    annual_heat_demand_mwh: float
    design_hour_heat_demand_kw: float
    design_hour_mass_flow_kg_s: float


@dataclass
class NetworkFlowResult:
    """Result of network flow aggregation."""
    pipe_id: str
    pipe_category: str
    aggregated_flow_kg_s: float
    building_count: int
    peak_hour: int
    flow_path: List[str]
    upstream_pipes: List[str]
    downstream_pipes: List[str]


class CHAFlowCalculationEngine:
    """
    Flow Calculation Engine for District Heating Networks.
    
    Converts heat demand data to mass flow rates and aggregates flows
    through the network hierarchy.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the flow calculation engine.
        
        Args:
            config: Configuration dictionary with flow calculation parameters
        """
        self.config = config
        
        # Water properties at 70°C
        self.water_density_kg_m3 = 977.8
        self.water_specific_heat_j_per_kgk = 4180
        
        # Temperature settings
        self.supply_temperature_c = config.get('supply_temperature_c', 70)
        self.return_temperature_c = config.get('return_temperature_c', 40)
        self.temperature_difference_k = self.supply_temperature_c - self.return_temperature_c
        
        # Design parameters
        self.design_hour_method = config.get('design_hour_method', 'peak_hour')  # 'peak_hour' or 'top_n_hours'
        self.top_n_hours = config.get('top_n_hours', 10)
        self.design_full_load_hours = config.get('design_full_load_hours', 2000)
        
        # Flow calculation parameters
        self.safety_factor = config.get('safety_factor', 1.1)
        self.diversity_factor = config.get('diversity_factor', 0.8)
        
        print(f"✅ Flow Calculation Engine initialized")
        print(f"   Supply Temperature: {self.supply_temperature_c}°C")
        print(f"   Return Temperature: {self.return_temperature_c}°C")
        print(f"   Temperature Difference: {self.temperature_difference_k}K")
        print(f"   Design Method: {self.design_hour_method}")
    
    def heat_demand_to_mass_flow(self, heat_demand_kw: float) -> float:
        """
        Convert heat demand to mass flow rate.
        
        Formula: Q = m * cp * ΔT
        Therefore: m = Q / (cp * ΔT)
        
        Args:
            heat_demand_kw: Heat demand in kW
        
        Returns:
            mass_flow_kg_s: Mass flow rate in kg/s
        """
        if heat_demand_kw <= 0:
            return 0.0
        
        # Convert kW to W
        heat_demand_w = heat_demand_kw * 1000
        
        # Calculate mass flow rate
        mass_flow_kg_s = heat_demand_w / (self.water_specific_heat_j_per_kgk * self.temperature_difference_k)
        
        return mass_flow_kg_s
    
    def mass_flow_to_volume_flow(self, mass_flow_kg_s: float) -> float:
        """
        Convert mass flow rate to volume flow rate.
        
        Args:
            mass_flow_kg_s: Mass flow rate in kg/s
        
        Returns:
            volume_flow_m3_s: Volume flow rate in m³/s
        """
        return mass_flow_kg_s / self.water_density_kg_m3
    
    def calculate_building_flows(self, lfa_data: Dict[str, Dict]) -> Dict[str, FlowCalculationResult]:
        """
        Calculate flow rates for all buildings from LFA data.
        
        Args:
            lfa_data: LFA heat demand data per building
        
        Returns:
            building_flows: Flow calculation results per building
        """
        building_flows = {}
        
        for building_id, heat_data in lfa_data.items():
            # Get heat demand series
            heat_series = heat_data.get('series', [])
            if not heat_series:
                print(f"⚠️ No heat demand data for building {building_id}")
                continue
            
            # Calculate peak heat demand
            peak_heat_demand_kw = max(heat_series)
            peak_hour = heat_series.index(peak_heat_demand_kw)
            
            # Calculate annual heat demand
            annual_heat_demand_kwh = sum(heat_series)
            annual_heat_demand_mwh = annual_heat_demand_kwh / 1000
            
            # Calculate design hour heat demand
            if self.design_hour_method == 'peak_hour':
                design_hour_heat_demand_kw = peak_heat_demand_kw
            elif self.design_hour_method == 'top_n_hours':
                # Get top N hours and use average
                top_n_heat_demands = sorted(heat_series, reverse=True)[:self.top_n_hours]
                design_hour_heat_demand_kw = np.mean(top_n_heat_demands)
            else:
                design_hour_heat_demand_kw = peak_heat_demand_kw
            
            # Apply safety factor
            design_hour_heat_demand_kw *= self.safety_factor
            
            # Calculate mass flow rates
            peak_mass_flow_kg_s = self.heat_demand_to_mass_flow(peak_heat_demand_kw)
            design_hour_mass_flow_kg_s = self.heat_demand_to_mass_flow(design_hour_heat_demand_kw)
            
            # Create result
            result = FlowCalculationResult(
                building_id=building_id,
                peak_heat_demand_kw=peak_heat_demand_kw,
                mass_flow_kg_s=design_hour_mass_flow_kg_s,  # Use design hour for sizing
                volume_flow_m3_s=self.mass_flow_to_volume_flow(design_hour_mass_flow_kg_s),
                peak_hour=peak_hour,
                annual_heat_demand_mwh=annual_heat_demand_mwh,
                design_hour_heat_demand_kw=design_hour_heat_demand_kw,
                design_hour_mass_flow_kg_s=design_hour_mass_flow_kg_s
            )
            
            building_flows[building_id] = result
        
        print(f"✅ Calculated flows for {len(building_flows)} buildings")
        return building_flows
    
    def aggregate_network_flows(self, building_flows: Dict[str, FlowCalculationResult], 
                              network_topology: Dict) -> Dict[str, NetworkFlowResult]:
        """
        Aggregate flows through network hierarchy.
        
        Args:
            building_flows: Flow calculation results per building
            network_topology: Network structure with pipe connections
        
        Returns:
            network_flows: Aggregated flow results per pipe
        """
        network_flows = {}
        
        # Create flow aggregation map
        flow_aggregation_map = self._create_flow_aggregation_map(network_topology)
        
        # Aggregate flows for each pipe
        for pipe_id, pipe_info in flow_aggregation_map.items():
            # Get buildings connected to this pipe
            connected_buildings = pipe_info['connected_buildings']
            
            # Aggregate flows from connected buildings
            aggregated_flow_kg_s = 0.0
            building_count = 0
            peak_hour = 0
            
            for building_id in connected_buildings:
                if building_id in building_flows:
                    building_flow = building_flows[building_id]
                    aggregated_flow_kg_s += building_flow.mass_flow_kg_s
                    building_count += 1
                    peak_hour = max(peak_hour, building_flow.peak_hour)
            
            # Apply diversity factor for multiple buildings
            if building_count > 1:
                diversity_factor = self._calculate_diversity_factor(building_count)
                aggregated_flow_kg_s *= diversity_factor
            
            # Determine pipe category based on flow rate
            pipe_category = self._determine_pipe_category(aggregated_flow_kg_s)
            
            # Create network flow result
            result = NetworkFlowResult(
                pipe_id=pipe_id,
                pipe_category=pipe_category,
                aggregated_flow_kg_s=aggregated_flow_kg_s,
                building_count=building_count,
                peak_hour=peak_hour,
                flow_path=pipe_info['flow_path'],
                upstream_pipes=pipe_info['upstream_pipes'],
                downstream_pipes=pipe_info['downstream_pipes']
            )
            
            network_flows[pipe_id] = result
        
        print(f"✅ Aggregated flows for {len(network_flows)} pipes")
        return network_flows
    
    def _create_flow_aggregation_map(self, network_topology: Dict) -> Dict:
        """
        Create flow aggregation map from network topology.
        
        Args:
            network_topology: Network structure
        
        Returns:
            flow_aggregation_map: Map of pipe connections and flow paths
        """
        flow_aggregation_map = {}
        
        # Analyze service connections
        service_connections = network_topology.get('service_connections', [])
        for service in service_connections:
            building_id = service['building_id']
            pipe_id = f"service_{building_id}"
            
            flow_aggregation_map[pipe_id] = {
                'connected_buildings': [building_id],
                'flow_path': [pipe_id],
                'upstream_pipes': [],
                'downstream_pipes': []
            }
        
        # Analyze supply pipes
        supply_pipes = network_topology.get('supply_pipes', [])
        for pipe in supply_pipes:
            pipe_id = pipe.get('pipe_id', f"supply_{pipe.get('street_id', 'unknown')}")
            building_served = pipe.get('building_served', 0)
            
            # Find connected buildings
            connected_buildings = []
            if building_served is not None:
                connected_buildings.append(str(building_served))
            
            # Determine flow path
            flow_path = self._trace_flow_path(pipe_id, network_topology)
            
            flow_aggregation_map[pipe_id] = {
                'connected_buildings': connected_buildings,
                'flow_path': flow_path,
                'upstream_pipes': self._find_upstream_pipes(pipe_id, network_topology),
                'downstream_pipes': self._find_downstream_pipes(pipe_id, network_topology)
            }
        
        return flow_aggregation_map
    
    def _trace_flow_path(self, pipe_id: str, network_topology: Dict) -> List[str]:
        """Trace flow path for a pipe."""
        # Simplified flow path tracing
        # In a real implementation, this would trace from plant to building
        return [pipe_id]
    
    def _find_upstream_pipes(self, pipe_id: str, network_topology: Dict) -> List[str]:
        """Find upstream pipes for a given pipe."""
        # Simplified upstream pipe finding
        return []
    
    def _find_downstream_pipes(self, pipe_id: str, network_topology: Dict) -> List[str]:
        """Find downstream pipes for a given pipe."""
        # Simplified downstream pipe finding
        return []
    
    def _calculate_diversity_factor(self, building_count: int) -> float:
        """
        Calculate diversity factor based on number of buildings.
        
        Args:
            building_count: Number of buildings connected
        
        Returns:
            diversity_factor: Diversity factor (0.0 to 1.0)
        """
        if building_count <= 1:
            return 1.0
        elif building_count <= 5:
            return 0.9
        elif building_count <= 10:
            return 0.8
        elif building_count <= 20:
            return 0.7
        else:
            return 0.6
    
    def _determine_pipe_category(self, flow_rate_kg_s: float) -> str:
        """
        Determine pipe category based on flow rate.
        
        Args:
            flow_rate_kg_s: Mass flow rate in kg/s
        
        Returns:
            pipe_category: Pipe category name
        """
        if flow_rate_kg_s < 2.0:
            return 'service_connection'
        elif flow_rate_kg_s < 20.0:
            return 'distribution_pipe'
        else:
            return 'main_pipe'
    
    def calculate_peak_hour_flows(self, lfa_data: Dict[str, Dict]) -> Dict[int, float]:
        """
        Calculate system-wide flows for each hour.
        
        Args:
            lfa_data: LFA heat demand data per building
        
        Returns:
            hourly_flows: System-wide flow rates per hour
        """
        hourly_flows = {}
        
        # Initialize hourly flows
        for hour in range(8760):
            hourly_flows[hour] = 0.0
        
        # Aggregate flows for each hour
        for building_id, heat_data in lfa_data.items():
            heat_series = heat_data.get('series', [])
            if not heat_series:
                continue
            
            for hour, heat_demand_kw in enumerate(heat_series):
                if hour < 8760:  # Ensure within year range
                    mass_flow_kg_s = self.heat_demand_to_mass_flow(heat_demand_kw)
                    hourly_flows[hour] += mass_flow_kg_s
        
        return hourly_flows
    
    def find_peak_hours(self, hourly_flows: Dict[int, float], top_n: int = 10) -> List[int]:
        """
        Find top N peak hours.
        
        Args:
            hourly_flows: System-wide flow rates per hour
            top_n: Number of peak hours to find
        
        Returns:
            peak_hours: List of peak hour indices
        """
        # Sort hours by flow rate
        sorted_hours = sorted(hourly_flows.items(), key=lambda x: x[1], reverse=True)
        
        # Get top N hours
        peak_hours = [hour for hour, flow in sorted_hours[:top_n]]
        
        return peak_hours
    
    def export_flow_results(self, building_flows: Dict[str, FlowCalculationResult], 
                          network_flows: Dict[str, NetworkFlowResult], 
                          output_path: str) -> None:
        """
        Export flow calculation results to JSON file.
        
        Args:
            building_flows: Building flow results
            network_flows: Network flow results
            output_path: Output file path
        """
        export_data = {
            'building_flows': {},
            'network_flows': {},
            'summary': {
                'total_buildings': len(building_flows),
                'total_pipes': len(network_flows),
                'total_flow_kg_s': sum(flow.aggregated_flow_kg_s for flow in network_flows.values()),
                'supply_temperature_c': self.supply_temperature_c,
                'return_temperature_c': self.return_temperature_c,
                'temperature_difference_k': self.temperature_difference_k
            }
        }
        
        # Export building flows
        for building_id, result in building_flows.items():
            export_data['building_flows'][building_id] = {
                'peak_heat_demand_kw': result.peak_heat_demand_kw,
                'mass_flow_kg_s': result.mass_flow_kg_s,
                'volume_flow_m3_s': result.volume_flow_m3_s,
                'peak_hour': result.peak_hour,
                'annual_heat_demand_mwh': result.annual_heat_demand_mwh,
                'design_hour_heat_demand_kw': result.design_hour_heat_demand_kw,
                'design_hour_mass_flow_kg_s': result.design_hour_mass_flow_kg_s
            }
        
        # Export network flows
        for pipe_id, result in network_flows.items():
            export_data['network_flows'][pipe_id] = {
                'pipe_category': result.pipe_category,
                'aggregated_flow_kg_s': result.aggregated_flow_kg_s,
                'building_count': result.building_count,
                'peak_hour': result.peak_hour,
                'flow_path': result.flow_path,
                'upstream_pipes': result.upstream_pipes,
                'downstream_pipes': result.downstream_pipes
            }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Flow calculation results exported to {output_path}")


# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    config = {
        'supply_temperature_c': 70,
        'return_temperature_c': 40,
        'design_hour_method': 'peak_hour',
        'top_n_hours': 10,
        'design_full_load_hours': 2000,
        'safety_factor': 1.1,
        'diversity_factor': 0.8
    }
    
    # Create flow calculation engine
    flow_engine = CHAFlowCalculationEngine(config)
    
    # Example LFA data
    lfa_data = {
        'building_1': {
            'series': [10.5, 12.3, 8.7, 15.2, 9.1] + [8.0] * 8755  # 8760 hours
        },
        'building_2': {
            'series': [8.2, 9.1, 7.5, 11.8, 8.9] + [7.5] * 8755
        }
    }
    
    # Calculate building flows
    building_flows = flow_engine.calculate_building_flows(lfa_data)
    
    # Example network topology
    network_topology = {
        'service_connections': [
            {'building_id': 'building_1'},
            {'building_id': 'building_2'}
        ],
        'supply_pipes': [
            {'pipe_id': 'supply_1', 'building_served': 'building_1'},
            {'pipe_id': 'supply_2', 'building_served': 'building_2'}
        ]
    }
    
    # Aggregate network flows
    network_flows = flow_engine.aggregate_network_flows(building_flows, network_topology)
    
    # Export results
    flow_engine.export_flow_results(building_flows, network_flows, "test_flow_results.json")
    
    # Print summary
    print(f"\n📊 Flow Calculation Summary:")
    print(f"   Total Buildings: {len(building_flows)}")
    print(f"   Total Pipes: {len(network_flows)}")
    print(f"   Total Flow: {sum(flow.aggregated_flow_kg_s for flow in network_flows.values()):.2f} kg/s")
