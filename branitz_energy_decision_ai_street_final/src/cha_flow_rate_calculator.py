"""
CHA Flow Rate Calculator - Streamlined Flow Rate Calculation Engine

This module implements a focused flow rate calculation engine for district heating networks,
specifically designed to work with LFA data and network topology.

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
class FlowRateResult:
    """Result of flow rate calculation."""
    building_id: str
    peak_hour: int
    peak_heat_demand_kw: float
    mass_flow_rate_kg_s: float
    volume_flow_rate_m3_s: float
    annual_heat_demand_mwh: float
    design_hour_heat_demand_kw: float
    design_hour_mass_flow_kg_s: float


@dataclass
class PipeSegmentFlow:
    """Flow rate for a pipe segment."""
    pipe_id: str
    start_node: str
    end_node: str
    aggregated_flow_kg_s: float
    building_count: int
    peak_hour: int
    pipe_category: str
    flow_path: List[str]


@dataclass
class NetworkFlowDistribution:
    """Network flow distribution result."""
    total_flow_kg_s: float
    pipe_segments: Dict[str, PipeSegmentFlow]
    building_flows: Dict[str, FlowRateResult]
    peak_hours: List[int]
    flow_hierarchy: Dict[str, List[str]]


class CHAFlowRateCalculator:
    """
    Flow Rate Calculator for District Heating Networks.
    
    Calculates mass flow rates from heat demand data and aggregates flows
    through network topology for intelligent pipe sizing.
    """
    
    def __init__(self, lfa_data: dict):
        """
        Initialize the flow rate calculator.
        
        Args:
            lfa_data: LFA heat demand data per building
        """
        self.lfa_data = lfa_data
        
        # Water properties
        self.cp_water = 4180  # J/kg·K (specific heat capacity)
        self.delta_t = 30  # K (70°C - 40°C temperature difference)
        self.water_density_kg_m3 = 977.8  # kg/m³ at 70°C
        
        # Flow calculation parameters
        self.safety_factor = 1.1  # Safety factor for design
        self.diversity_factor = 0.8  # Diversity factor for multiple buildings
        
        # Results storage
        self.building_flows: Dict[str, FlowRateResult] = {}
        self.pipe_segment_flows: Dict[str, PipeSegmentFlow] = {}
        self.network_flow_distribution: Optional[NetworkFlowDistribution] = None
        
        print(f"✅ CHA Flow Rate Calculator initialized")
        print(f"   Buildings: {len(lfa_data)}")
        print(f"   Water Properties: cp={self.cp_water} J/kg·K, ΔT={self.delta_t}K")
        print(f"   Safety Factor: {self.safety_factor}")
    
    def calculate_building_flow_rate(self, building_id: str, peak_hour: int) -> float:
        """
        Calculate mass flow rate for a building at peak hour.
        
        Args:
            building_id: Building identifier
            peak_hour: Hour index (0-8759) for peak demand
        
        Returns:
            mass_flow_rate_kg_s: Mass flow rate in kg/s
        """
        if building_id not in self.lfa_data:
            print(f"⚠️ Building {building_id} not found in LFA data")
            return 0.0
        
        heat_data = self.lfa_data[building_id]
        heat_series = heat_data.get('series', [])
        
        if not heat_series or peak_hour >= len(heat_series):
            print(f"⚠️ Invalid peak hour {peak_hour} for building {building_id}")
            return 0.0
        
        # Get heat demand at peak hour
        heat_demand_kw = heat_series[peak_hour]
        
        # Convert to mass flow rate: m = Q / (cp * ΔT)
        # Q in kW, convert to W: Q * 1000
        # m = (Q * 1000) / (cp * ΔT)
        mass_flow_rate_kg_s = (heat_demand_kw * 1000) / (self.cp_water * self.delta_t)
        
        return mass_flow_rate_kg_s
    
    def calculate_all_building_flows(self) -> Dict[str, FlowRateResult]:
        """
        Calculate flow rates for all buildings.
        
        Returns:
            building_flows: Dictionary of flow rate results per building
        """
        print(f"📊 Calculating flow rates for {len(self.lfa_data)} buildings...")
        
        for building_id, heat_data in self.lfa_data.items():
            heat_series = heat_data.get('series', [])
            
            if not heat_series:
                print(f"⚠️ No heat demand data for building {building_id}")
                continue
            
            # Find peak heat demand and hour
            peak_heat_demand_kw = max(heat_series)
            peak_hour = heat_series.index(peak_heat_demand_kw)
            
            # Calculate annual heat demand
            annual_heat_demand_kwh = sum(heat_series)
            annual_heat_demand_mwh = annual_heat_demand_kwh / 1000
            
            # Calculate design hour heat demand (with safety factor)
            design_hour_heat_demand_kw = peak_heat_demand_kw * self.safety_factor
            
            # Calculate mass flow rates
            peak_mass_flow_kg_s = self.calculate_building_flow_rate(building_id, peak_hour)
            design_hour_mass_flow_kg_s = (design_hour_heat_demand_kw * 1000) / (self.cp_water * self.delta_t)
            
            # Calculate volume flow rate
            volume_flow_rate_m3_s = design_hour_mass_flow_kg_s / self.water_density_kg_m3
            
            # Create result
            result = FlowRateResult(
                building_id=building_id,
                peak_hour=peak_hour,
                peak_heat_demand_kw=peak_heat_demand_kw,
                mass_flow_rate_kg_s=design_hour_mass_flow_kg_s,  # Use design hour for sizing
                volume_flow_rate_m3_s=volume_flow_rate_m3_s,
                annual_heat_demand_mwh=annual_heat_demand_mwh,
                design_hour_heat_demand_kw=design_hour_heat_demand_kw,
                design_hour_mass_flow_kg_s=design_hour_mass_flow_kg_s
            )
            
            self.building_flows[building_id] = result
        
        print(f"✅ Calculated flows for {len(self.building_flows)} buildings")
        return self.building_flows
    
    def aggregate_flow_rates(self, pipe_segments: list) -> dict:
        """
        Aggregate flow rates for each pipe segment.
        
        Args:
            pipe_segments: List of pipe segment information
        
        Returns:
            aggregated_flows: Dictionary of aggregated flow rates per pipe segment
        """
        print(f"🔄 Aggregating flow rates for {len(pipe_segments)} pipe segments...")
        
        aggregated_flows = {}
        
        for segment in pipe_segments:
            pipe_id = segment.get('pipe_id', f"pipe_{len(aggregated_flows)}")
            start_node = segment.get('start_node', 'unknown')
            end_node = segment.get('end_node', 'unknown')
            connected_buildings = segment.get('connected_buildings', [])
            pipe_category = segment.get('pipe_category', 'unknown')
            flow_path = segment.get('flow_path', [])
            
            # Aggregate flows from connected buildings
            total_flow_kg_s = 0.0
            building_count = 0
            peak_hour = 0
            
            for building_id in connected_buildings:
                if building_id in self.building_flows:
                    building_flow = self.building_flows[building_id]
                    total_flow_kg_s += building_flow.mass_flow_rate_kg_s
                    building_count += 1
                    peak_hour = max(peak_hour, building_flow.peak_hour)
            
            # Apply diversity factor for multiple buildings
            if building_count > 1:
                diversity_factor = self._calculate_diversity_factor(building_count)
                total_flow_kg_s *= diversity_factor
            
            # Create pipe segment flow result
            pipe_flow = PipeSegmentFlow(
                pipe_id=pipe_id,
                start_node=start_node,
                end_node=end_node,
                aggregated_flow_kg_s=total_flow_kg_s,
                building_count=building_count,
                peak_hour=peak_hour,
                pipe_category=pipe_category,
                flow_path=flow_path
            )
            
            aggregated_flows[pipe_id] = pipe_flow
            self.pipe_segment_flows[pipe_id] = pipe_flow
        
        print(f"✅ Aggregated flows for {len(aggregated_flows)} pipe segments")
        return aggregated_flows
    
    def calculate_network_flow_distribution(self, network_topology: dict) -> dict:
        """
        Calculate flow rates throughout the network.
        
        Args:
            network_topology: Network topology information
        
        Returns:
            network_flow_distribution: Complete network flow distribution
        """
        print(f"🌐 Calculating network flow distribution...")
        
        # First calculate all building flows
        if not self.building_flows:
            self.calculate_all_building_flows()
        
        # Extract pipe segments from network topology
        pipe_segments = self._extract_pipe_segments(network_topology)
        
        # Aggregate flow rates for pipe segments
        aggregated_flows = self.aggregate_flow_rates(pipe_segments)
        
        # Calculate total system flow
        total_flow_kg_s = sum(flow.aggregated_flow_kg_s for flow in aggregated_flows.values())
        
        # Find peak hours across all buildings
        peak_hours = list(set(flow.peak_hour for flow in self.building_flows.values()))
        peak_hours.sort()
        
        # Create flow hierarchy
        flow_hierarchy = self._create_flow_hierarchy(aggregated_flows, network_topology)
        
        # Create network flow distribution result
        self.network_flow_distribution = NetworkFlowDistribution(
            total_flow_kg_s=total_flow_kg_s,
            pipe_segments=aggregated_flows,
            building_flows=self.building_flows,
            peak_hours=peak_hours,
            flow_hierarchy=flow_hierarchy
        )
        
        print(f"✅ Network flow distribution calculated")
        print(f"   Total Flow: {total_flow_kg_s:.2f} kg/s")
        print(f"   Pipe Segments: {len(aggregated_flows)}")
        print(f"   Peak Hours: {len(peak_hours)}")
        
        return {
            'total_flow_kg_s': total_flow_kg_s,
            'pipe_segments': aggregated_flows,
            'building_flows': self.building_flows,
            'peak_hours': peak_hours,
            'flow_hierarchy': flow_hierarchy
        }
    
    def _extract_pipe_segments(self, network_topology: dict) -> list:
        """Extract pipe segments from network topology."""
        pipe_segments = []
        
        # Extract from supply pipes
        supply_pipes = network_topology.get('supply_pipes', [])
        for pipe in supply_pipes:
            segment = {
                'pipe_id': f"supply_{pipe.get('street_id', 'unknown')}_{pipe.get('building_served', 'unknown')}",
                'start_node': pipe.get('start_node', 'unknown'),
                'end_node': pipe.get('end_node', 'unknown'),
                'connected_buildings': [str(pipe.get('building_served', 'unknown'))],
                'pipe_category': self._determine_pipe_category(pipe),
                'flow_path': [pipe.get('start_node', 'unknown'), pipe.get('end_node', 'unknown')]
            }
            pipe_segments.append(segment)
        
        # Extract from return pipes
        return_pipes = network_topology.get('return_pipes', [])
        for pipe in return_pipes:
            segment = {
                'pipe_id': f"return_{pipe.get('street_id', 'unknown')}_{pipe.get('building_served', 'unknown')}",
                'start_node': pipe.get('start_node', 'unknown'),
                'end_node': pipe.get('end_node', 'unknown'),
                'connected_buildings': [str(pipe.get('building_served', 'unknown'))],
                'pipe_category': self._determine_pipe_category(pipe),
                'flow_path': [pipe.get('start_node', 'unknown'), pipe.get('end_node', 'unknown')]
            }
            pipe_segments.append(segment)
        
        # Extract from service connections
        service_connections = network_topology.get('service_connections', [])
        for service in service_connections:
            segment = {
                'pipe_id': f"service_{service.get('building_id', 'unknown')}_{service.get('pipe_type', 'unknown')}",
                'start_node': service.get('connection_x', 'unknown'),
                'end_node': service.get('building_x', 'unknown'),
                'connected_buildings': [str(service.get('building_id', 'unknown'))],
                'pipe_category': 'service_connection',
                'flow_path': [service.get('connection_x', 'unknown'), service.get('building_x', 'unknown')]
            }
            pipe_segments.append(segment)
        
        return pipe_segments
    
    def _determine_pipe_category(self, pipe: dict) -> str:
        """Determine pipe category based on pipe information."""
        # Simple categorization based on pipe type and length
        pipe_type = pipe.get('pipe_type', 'unknown')
        length_m = pipe.get('length_m', 0)
        
        if pipe_type == 'service':
            return 'service_connection'
        elif length_m < 200:
            return 'distribution_pipe'
        else:
            return 'main_pipe'
    
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
    
    def _create_flow_hierarchy(self, aggregated_flows: dict, network_topology: dict) -> dict:
        """Create flow hierarchy structure."""
        hierarchy = {
            'service_connections': [],
            'distribution_pipes': [],
            'main_pipes': []
        }
        
        for pipe_id, flow in aggregated_flows.items():
            category = flow.pipe_category
            if category in hierarchy:
                hierarchy[category].append(pipe_id)
        
        return hierarchy
    
    def get_flow_summary(self) -> dict:
        """Get summary of flow calculations."""
        if not self.building_flows:
            return {}
        
        total_buildings = len(self.building_flows)
        total_flow_kg_s = sum(flow.mass_flow_rate_kg_s for flow in self.building_flows.values())
        total_annual_heat_mwh = sum(flow.annual_heat_demand_mwh for flow in self.building_flows.values())
        
        # Calculate statistics
        flow_rates = [flow.mass_flow_rate_kg_s for flow in self.building_flows.values()]
        avg_flow_kg_s = np.mean(flow_rates) if flow_rates else 0
        max_flow_kg_s = max(flow_rates) if flow_rates else 0
        min_flow_kg_s = min(flow_rates) if flow_rates else 0
        
        return {
            'total_buildings': total_buildings,
            'total_flow_kg_s': total_flow_kg_s,
            'total_annual_heat_mwh': total_annual_heat_mwh,
            'average_flow_kg_s': avg_flow_kg_s,
            'max_flow_kg_s': max_flow_kg_s,
            'min_flow_kg_s': min_flow_kg_s,
            'safety_factor': self.safety_factor,
            'diversity_factor': self.diversity_factor
        }
    
    def export_flow_results(self, output_path: str) -> None:
        """
        Export flow calculation results to JSON file.
        
        Args:
            output_path: Output file path
        """
        export_data = {
            'summary': self.get_flow_summary(),
            'building_flows': {},
            'pipe_segment_flows': {},
            'network_flow_distribution': None
        }
        
        # Export building flows
        for building_id, result in self.building_flows.items():
            export_data['building_flows'][building_id] = {
                'peak_hour': result.peak_hour,
                'peak_heat_demand_kw': result.peak_heat_demand_kw,
                'mass_flow_rate_kg_s': result.mass_flow_rate_kg_s,
                'volume_flow_rate_m3_s': result.volume_flow_rate_m3_s,
                'annual_heat_demand_mwh': result.annual_heat_demand_mwh,
                'design_hour_heat_demand_kw': result.design_hour_heat_demand_kw,
                'design_hour_mass_flow_kg_s': result.design_hour_mass_flow_kg_s
            }
        
        # Export pipe segment flows
        for pipe_id, flow in self.pipe_segment_flows.items():
            export_data['pipe_segment_flows'][pipe_id] = {
                'start_node': flow.start_node,
                'end_node': flow.end_node,
                'aggregated_flow_kg_s': flow.aggregated_flow_kg_s,
                'building_count': flow.building_count,
                'peak_hour': flow.peak_hour,
                'pipe_category': flow.pipe_category,
                'flow_path': flow.flow_path
            }
        
        # Export network flow distribution
        if self.network_flow_distribution:
            export_data['network_flow_distribution'] = {
                'total_flow_kg_s': self.network_flow_distribution.total_flow_kg_s,
                'peak_hours': self.network_flow_distribution.peak_hours,
                'flow_hierarchy': self.network_flow_distribution.flow_hierarchy
            }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Flow calculation results exported to {output_path}")
    
    def print_flow_summary(self) -> None:
        """Print summary of flow calculations."""
        summary = self.get_flow_summary()
        
        if not summary:
            print("⚠️ No flow calculations available")
            return
        
        print(f"\n📊 FLOW RATE CALCULATION SUMMARY")
        print(f"=" * 50)
        print(f"🏗️ BUILDINGS:")
        print(f"   Total Buildings: {summary['total_buildings']}")
        print(f"   Total Flow: {summary['total_flow_kg_s']:.2f} kg/s")
        print(f"   Total Annual Heat: {summary['total_annual_heat_mwh']:.1f} MWh")
        print(f"")
        print(f"⚡ FLOW STATISTICS:")
        print(f"   Average Flow: {summary['average_flow_kg_s']:.4f} kg/s")
        print(f"   Maximum Flow: {summary['max_flow_kg_s']:.4f} kg/s")
        print(f"   Minimum Flow: {summary['min_flow_kg_s']:.4f} kg/s")
        print(f"")
        print(f"🔧 PARAMETERS:")
        print(f"   Safety Factor: {summary['safety_factor']}")
        print(f"   Diversity Factor: {summary['diversity_factor']}")
        print(f"   Water Properties: cp={self.cp_water} J/kg·K, ΔT={self.delta_t}K")


# Example usage and testing
if __name__ == "__main__":
    # Example LFA data
    lfa_data = {
        'building_1': {
            'series': [10.0, 12.0, 8.0, 15.0, 9.0] + [8.0] * 8755  # 8760 hours
        },
        'building_2': {
            'series': [8.0, 10.0, 7.0, 12.0, 8.5] + [7.5] * 8755
        },
        'building_3': {
            'series': [12.0, 14.0, 10.0, 16.0, 11.0] + [9.0] * 8755
        }
    }
    
    # Create flow rate calculator
    flow_calculator = CHAFlowRateCalculator(lfa_data)
    
    # Test individual building flow calculation
    building_1_flow = flow_calculator.calculate_building_flow_rate('building_1', 3)  # Peak hour 3
    print(f"Building 1 flow at peak hour 3: {building_1_flow:.4f} kg/s")
    
    # Calculate all building flows
    building_flows = flow_calculator.calculate_all_building_flows()
    
    # Example network topology
    network_topology = {
        'supply_pipes': [
            {'pipe_id': 'supply_1', 'start_node': 'plant', 'end_node': 'junction_1', 'building_served': 1, 'street_id': 'street_1', 'length_m': 100},
            {'pipe_id': 'supply_2', 'start_node': 'junction_1', 'end_node': 'junction_2', 'building_served': 2, 'street_id': 'street_2', 'length_m': 150}
        ],
        'return_pipes': [
            {'pipe_id': 'return_1', 'start_node': 'junction_1', 'end_node': 'plant', 'building_served': 1, 'street_id': 'street_1', 'length_m': 100},
            {'pipe_id': 'return_2', 'start_node': 'junction_2', 'end_node': 'junction_1', 'building_served': 2, 'street_id': 'street_2', 'length_m': 150}
        ],
        'service_connections': [
            {'building_id': 1, 'connection_x': 100, 'building_x': 120, 'pipe_type': 'supply_service'},
            {'building_id': 2, 'connection_x': 200, 'building_x': 220, 'pipe_type': 'supply_service'}
        ]
    }
    
    # Calculate network flow distribution
    network_flows = flow_calculator.calculate_network_flow_distribution(network_topology)
    
    # Print summary
    flow_calculator.print_flow_summary()
    
    # Export results
    flow_calculator.export_flow_results("test_flow_results.json")
    
    print(f"\n🎉 Flow Rate Calculator testing completed successfully!")
