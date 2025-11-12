"""
CHA Flow Integration - Integration with Existing CHA System

This module integrates the flow rate calculator with the existing CHA system,
replacing hardcoded diameters with intelligent flow-based sizing.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

from __future__ import annotations
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

# Import our flow rate calculator
try:
    from src.cha_flow_rate_calculator import CHAFlowRateCalculator, FlowRateResult, PipeSegmentFlow
except ImportError:
    # Fallback for direct execution
    from cha_flow_rate_calculator import CHAFlowRateCalculator, FlowRateResult, PipeSegmentFlow

# Import existing CHA components
try:
    from src.cha_pipe_sizing import CHAPipeSizingEngine
except ImportError:
    # Fallback for direct execution
    from cha_pipe_sizing import CHAPipeSizingEngine

warnings.filterwarnings("ignore")


class CHAFlowIntegration:
    """
    Integration module for flow-based pipe sizing in CHA system.
    
    Integrates the flow rate calculator with existing CHA components
    to provide intelligent pipe sizing based on actual flow rates.
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize the flow integration system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        
        # Initialize components
        self.flow_calculator: Optional[CHAFlowRateCalculator] = None
        self.pipe_sizing_engine = CHAPipeSizingEngine(self.config.get('pipe_sizing', {}))
        
        # Results storage
        self.lfa_data: Dict = {}
        self.building_flows: Dict[str, FlowRateResult] = {}
        self.pipe_segment_flows: Dict[str, PipeSegmentFlow] = {}
        self.sizing_results: Dict = {}
        
        # Mass flow integration components
        self.design_hour: Optional[int] = None
        self.mass_flows: Dict[str, float] = {}
        self.aggregated_flows: Dict[str, float] = {}
        self.flow_balance_validated: bool = False
        
        # Physical constants for mass flow calculation
        self.cp_water = 4180  # J/(kg·K) - specific heat capacity of water
        self.delta_t_design = 30  # K - design temperature difference
        
        print(f"✅ CHA Flow Integration initialized")
    
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
            'flow_calculation': {
                'safety_factor': 1.1,
                'diversity_factor': 0.8
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
            self.building_flows = self.flow_calculator.calculate_all_building_flows()
            
            print(f"✅ Flow rates calculated for {len(self.building_flows)} buildings")
            return True
            
        except Exception as e:
            print(f"❌ Failed to calculate flow rates: {e}")
            return False
    
    def integrate_with_cha_network(self, cha_output_dir: str) -> bool:
        """
        Integrate flow calculations with CHA network data.
        
        Args:
            cha_output_dir: Directory containing CHA output files
        
        Returns:
            success: True if integration successful
        """
        if not self.flow_calculator:
            print("❌ Flow calculator not initialized")
            return False
        
        try:
            cha_dir = Path(cha_output_dir)
            
            # Load CHA network data
            network_topology = self._load_cha_network_data(cha_dir)
            
            # Calculate network flow distribution
            network_flows = self.flow_calculator.calculate_network_flow_distribution(network_topology)
            
            # Extract pipe segment flows
            self.pipe_segment_flows = network_flows.get('pipe_segments', {})
            
            print(f"✅ Integrated with CHA network data")
            print(f"   Pipe segments: {len(self.pipe_segment_flows)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to integrate with CHA network: {e}")
            return False
    
    def _load_cha_network_data(self, cha_dir: Path) -> dict:
        """Load CHA network data from output files."""
        network_topology = {
            'supply_pipes': [],
            'return_pipes': [],
            'service_connections': []
        }
        
        # Load supply pipes
        supply_pipes_file = cha_dir / "supply_pipes.csv"
        if supply_pipes_file.exists():
            supply_df = pd.read_csv(supply_pipes_file)
            network_topology['supply_pipes'] = supply_df.to_dict('records')
        
        # Load return pipes
        return_pipes_file = cha_dir / "return_pipes.csv"
        if return_pipes_file.exists():
            return_df = pd.read_csv(return_pipes_file)
            network_topology['return_pipes'] = return_df.to_dict('records')
        
        # Load service connections
        service_connections_file = cha_dir / "service_connections.csv"
        if service_connections_file.exists():
            service_df = pd.read_csv(service_connections_file)
            network_topology['service_connections'] = service_df.to_dict('records')
        
        return network_topology
    
    def size_pipes_with_flow_rates(self) -> bool:
        """
        Size pipes using calculated flow rates.
        
        Returns:
            success: True if sizing successful
        """
        if not self.pipe_segment_flows:
            print("⚠️ No pipe segment flows available, creating mock pipe segments from building flows")
            # Create mock pipe segments from building flows for testing
            self.pipe_segment_flows = {}
            for building_id, building_flow in self.building_flows.items():
                pipe_id = f"mock_pipe_{building_id}"
                self.pipe_segment_flows[pipe_id] = type('MockPipeSegment', (), {
                    'pipe_id': pipe_id,
                    'aggregated_flow_kg_s': building_flow.mass_flow_rate_kg_s,
                    'pipe_category': 'distribution_pipe'
                })()
        
        try:
            self.sizing_results = {}
            
            for pipe_id, pipe_flow in self.pipe_segment_flows.items():
                # Get pipe length (simplified - in real implementation, load from CHA data)
                length_m = 100.0  # Default length
                
                # Size the pipe
                sizing_result = self.pipe_sizing_engine.size_pipe(
                    flow_rate_kg_s=pipe_flow.aggregated_flow_kg_s,
                    length_m=length_m,
                    pipe_category=pipe_flow.pipe_category
                )
                
                self.sizing_results[pipe_id] = {
                    'pipe_id': pipe_id,
                    'flow_rate_kg_s': pipe_flow.aggregated_flow_kg_s,
                    'length_m': length_m,
                    'pipe_category': pipe_flow.pipe_category,
                    'diameter_m': sizing_result.diameter_m,
                    'diameter_nominal': sizing_result.diameter_nominal,
                    'velocity_ms': sizing_result.velocity_ms,
                    'pressure_drop_bar': sizing_result.pressure_drop_bar,
                    'cost_eur': sizing_result.total_cost_eur,
                    'standards_compliance': sizing_result.standards_compliance,
                    'violations': sizing_result.violations
                }
            
            print(f"✅ Sized {len(self.sizing_results)} pipes with flow rates")
            return True
            
        except Exception as e:
            print(f"❌ Failed to size pipes: {e}")
            return False
    
    def update_cha_pandapipes_integration(self, cha_output_dir: str) -> bool:
        """
        Update CHA pandapipes integration with calculated diameters.
        
        Args:
            cha_output_dir: Directory containing CHA output files
        
        Returns:
            success: True if update successful
        """
        if not self.sizing_results:
            print("❌ No sizing results available")
            return False
        
        try:
            cha_dir = Path(cha_output_dir)
            
            # Create enhanced pipe data with calculated diameters
            enhanced_pipes = []
            
            for pipe_id, sizing_result in self.sizing_results.items():
                enhanced_pipe = {
                    'pipe_id': pipe_id,
                    'diameter_m': sizing_result['diameter_m'],
                    'diameter_nominal': sizing_result['diameter_nominal'],
                    'flow_rate_kg_s': sizing_result['flow_rate_kg_s'],
                    'velocity_ms': sizing_result['velocity_ms'],
                    'pressure_drop_bar': sizing_result['pressure_drop_bar'],
                    'cost_eur': sizing_result['cost_eur'],
                    'pipe_category': sizing_result['pipe_category'],
                    'standards_compliance': sizing_result['standards_compliance'],
                    'violations': sizing_result['violations']
                }
                enhanced_pipes.append(enhanced_pipe)
            
            # Save enhanced pipe data
            enhanced_file = cha_dir / "enhanced_pipe_sizing.json"
            with open(enhanced_file, 'w') as f:
                json.dump(enhanced_pipes, f, indent=2)
            
            print(f"✅ Updated CHA pandapipes integration")
            print(f"   Enhanced pipe data saved to {enhanced_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to update CHA pandapipes integration: {e}")
            return False
    
    def calculate_mass_flows_from_lfa(self, lfa_data: Dict) -> Dict[str, float]:
        """
        Calculate mass flows from LFA heat demand data.
        
        Uses the formula: m_dot = Q_th / (cp * ΔT)
        where:
        - m_dot = mass flow rate (kg/s)
        - Q_th = thermal power (W)
        - cp = specific heat capacity of water (4180 J/(kg·K))
        - ΔT = temperature difference (30 K)
        
        Args:
            lfa_data: LFA heat demand data per building
            
        Returns:
            mass_flows: Dictionary mapping building_id to mass flow rate (kg/s)
        """
        try:
            print("🔄 Calculating mass flows from LFA heat demand data...")
            
            # Select design hour for peak demand
            design_hour = self.select_design_hour(lfa_data)
            self.design_hour = design_hour
            
            mass_flows = {}
            
            for building_id, building_data in lfa_data.items():
                # Get heat demand series
                if 'series' in building_data:
                    heat_demand_series = building_data['series']
                    
                    # Get peak heat demand for design hour
                    if design_hour < len(heat_demand_series):
                        peak_heat_demand_w = heat_demand_series[design_hour] * 1000  # Convert kW to W
                    else:
                        # Fallback to maximum value if design hour exceeds series length
                        peak_heat_demand_w = max(heat_demand_series) * 1000
                else:
                    # Fallback to default heat demand
                    peak_heat_demand_w = building_data.get('peak_heat_demand_kw', 10.0) * 1000
                
                # Calculate mass flow rate: m_dot = Q_th / (cp * ΔT)
                mass_flow_kg_s = peak_heat_demand_w / (self.cp_water * self.delta_t_design)
                
                mass_flows[building_id] = mass_flow_kg_s
                
                print(f"   Building {building_id}: {peak_heat_demand_w/1000:.1f} kW → {mass_flow_kg_s:.3f} kg/s")
            
            self.mass_flows = mass_flows
            
            total_mass_flow = sum(mass_flows.values())
            print(f"✅ Mass flows calculated for {len(mass_flows)} buildings")
            print(f"   Total mass flow: {total_mass_flow:.3f} kg/s")
            print(f"   Design hour: {design_hour}")
            
            return mass_flows
            
        except Exception as e:
            print(f"❌ Error calculating mass flows: {e}")
            return {}
    
    def select_design_hour(self, hourly_demand: Dict) -> int:
        """
        Select design hour from peak demand across all buildings.
        
        Args:
            hourly_demand: Dictionary with building heat demand series
            
        Returns:
            design_hour: Hour index with peak total demand
        """
        try:
            print("🔄 Selecting design hour from peak demand...")
            
            # Calculate total demand for each hour across all buildings
            hourly_totals = {}
            
            for building_id, building_data in hourly_demand.items():
                if 'series' in building_data:
                    series = building_data['series']
                    
                    for hour, demand_kw in enumerate(series):
                        if hour not in hourly_totals:
                            hourly_totals[hour] = 0.0
                        hourly_totals[hour] += demand_kw
            
            if not hourly_totals:
                print("⚠️ No hourly demand data found, using hour 0 as design hour")
                return 0
            
            # Find hour with maximum total demand
            design_hour = max(hourly_totals.keys(), key=lambda h: hourly_totals[h])
            peak_demand_kw = hourly_totals[design_hour]
            
            print(f"   Design hour: {design_hour}")
            print(f"   Peak total demand: {peak_demand_kw:.1f} kW")
            print(f"   Total hours analyzed: {len(hourly_totals)}")
            
            return design_hour
            
        except Exception as e:
            print(f"❌ Error selecting design hour: {e}")
            return 0
    
    def aggregate_upstream_flows(self, pipe_network: Dict) -> Dict[str, float]:
        """
        Aggregate upstream flows for each pipe segment.
        
        Args:
            pipe_network: Network topology with supply pipes and service connections
            
        Returns:
            aggregated_flows: Dictionary mapping pipe_id to aggregated flow rate (kg/s)
        """
        try:
            print("🔄 Aggregating upstream flows for pipe segments...")
            
            aggregated_flows = {}
            
            # Create network graph for flow aggregation
            import networkx as nx
            G = nx.DiGraph()
            
            # Add nodes and edges from supply pipes
            supply_pipes = pipe_network.get('supply_pipes', [])
            service_connections = pipe_network.get('service_connections', [])
            
            # Build network graph
            for pipe in supply_pipes:
                start_node = str(pipe.get('start_node', ''))
                end_node = str(pipe.get('end_node', ''))
                pipe_id = pipe.get('pipe_id', f"{start_node}_{end_node}")
                
                if start_node and end_node:
                    G.add_edge(start_node, end_node, pipe_id=pipe_id)
            
            # Map service connections to building flows
            building_to_node = {}
            for service in service_connections:
                building_id = service.get('building_id', '')
                node_id = str(service.get('end_node', ''))
                if building_id and node_id:
                    building_to_node[building_id] = node_id
            
            # Aggregate flows for each pipe
            for pipe in supply_pipes:
                start_node = str(pipe.get('start_node', ''))
                end_node = str(pipe.get('end_node', ''))
                pipe_id = pipe.get('pipe_id', f"{start_node}_{end_node}")
                
                if not start_node or not end_node:
                    continue
                
                # Find all buildings downstream of this pipe
                downstream_buildings = set()
                
                try:
                    # Get all nodes reachable from end_node
                    if G.has_node(end_node):
                        reachable_nodes = set(nx.descendants(G, end_node))
                        reachable_nodes.add(end_node)
                        
                        # Find buildings connected to reachable nodes
                        for building_id, node_id in building_to_node.items():
                            if node_id in reachable_nodes:
                                downstream_buildings.add(building_id)
                except:
                    # Fallback: if graph traversal fails, use direct connection
                    for building_id, node_id in building_to_node.items():
                        if node_id == end_node:
                            downstream_buildings.add(building_id)
                
                # Sum mass flows from downstream buildings
                total_flow_kg_s = 0.0
                for building_id in downstream_buildings:
                    if building_id in self.mass_flows:
                        total_flow_kg_s += self.mass_flows[building_id]
                
                aggregated_flows[pipe_id] = total_flow_kg_s
                
                if total_flow_kg_s > 0:
                    print(f"   Pipe {pipe_id}: {len(downstream_buildings)} buildings → {total_flow_kg_s:.3f} kg/s")
            
            self.aggregated_flows = aggregated_flows
            
            total_network_flow = sum(aggregated_flows.values())
            print(f"✅ Aggregated flows for {len(aggregated_flows)} pipe segments")
            print(f"   Total network flow: {total_network_flow:.3f} kg/s")
            
            return aggregated_flows
            
        except Exception as e:
            print(f"❌ Error aggregating upstream flows: {e}")
            return {}
    
    def validate_flow_balance(self, total_supply: float, total_demand: float) -> bool:
        """
        Validate flow balance between supply and demand.
        
        Args:
            total_supply: Total supply flow rate (kg/s)
            total_demand: Total demand flow rate (kg/s)
            
        Returns:
            is_balanced: True if flow balance is within acceptable tolerance
        """
        try:
            print("🔄 Validating flow balance...")
            
            # Calculate balance error
            if total_demand > 0:
                balance_error_pct = abs(total_supply - total_demand) / total_demand * 100
            else:
                balance_error_pct = 100.0 if total_supply > 0 else 0.0
            
            # Acceptable tolerance: 5%
            tolerance_pct = 5.0
            is_balanced = balance_error_pct <= tolerance_pct
            
            print(f"   Total supply: {total_supply:.3f} kg/s")
            print(f"   Total demand: {total_demand:.3f} kg/s")
            print(f"   Balance error: {balance_error_pct:.2f}%")
            print(f"   Tolerance: {tolerance_pct}%")
            print(f"   Flow balance: {'✅ PASS' if is_balanced else '❌ FAIL'}")
            
            self.flow_balance_validated = is_balanced
            
            if not is_balanced:
                print(f"⚠️ Flow balance validation failed!")
                print(f"   Consider checking:")
                print(f"   - Building heat demand data accuracy")
                print(f"   - Network topology completeness")
                print(f"   - Service connection mapping")
            
            return is_balanced
            
        except Exception as e:
            print(f"❌ Error validating flow balance: {e}")
            return False
    
    def run_complete_flow_integration(self, lfa_data: Dict, cha_output_dir: str) -> Dict:
        """
        Run complete flow integration process.
        
        Args:
            lfa_data: LFA heat demand data per building
            cha_output_dir: Directory containing CHA output files
        
        Returns:
            results: Complete integration results
        """
        print(f"\n🚀 Starting Complete Flow Integration Process")
        print(f"   Buildings: {len(lfa_data)}")
        print(f"   CHA Output: {cha_output_dir}")
        
        try:
            # Step 1: Load LFA data
            print(f"\n📊 Step 1: Loading LFA Data")
            if not self.load_lfa_data(lfa_data):
                raise Exception("Failed to load LFA data")
            
            # Step 2: Calculate mass flows from LFA
            print(f"\n🔄 Step 2: Calculating Mass Flows from LFA")
            mass_flows = self.calculate_mass_flows_from_lfa(lfa_data)
            if not mass_flows:
                raise Exception("Failed to calculate mass flows")
            
            # Step 3: Integrate with CHA network
            print(f"\n🌐 Step 3: Integrating with CHA Network")
            if not self.integrate_with_cha_network(cha_output_dir):
                raise Exception("Failed to integrate with CHA network")
            
            # Step 4: Aggregate upstream flows
            print(f"\n🔗 Step 4: Aggregating Upstream Flows")
            network_topology = self._load_cha_network_data(Path(cha_output_dir))
            aggregated_flows = self.aggregate_upstream_flows(network_topology)
            if not aggregated_flows:
                raise Exception("Failed to aggregate upstream flows")
            
            # Step 5: Validate flow balance
            print(f"\n⚖️ Step 5: Validating Flow Balance")
            total_demand = sum(mass_flows.values())
            total_supply = sum(aggregated_flows.values())
            if not self.validate_flow_balance(total_supply, total_demand):
                print("⚠️ Flow balance validation failed, but continuing...")
            
            # Step 6: Calculate flow rates (legacy method for compatibility)
            print(f"\n🔄 Step 6: Calculating Flow Rates (Legacy)")
            if not self.calculate_flow_rates():
                raise Exception("Failed to calculate flow rates")
            
            # Step 7: Size pipes with flow rates
            print(f"\n📏 Step 7: Sizing Pipes with Flow Rates")
            if not self.size_pipes_with_flow_rates():
                raise Exception("Failed to size pipes")
            
            # Step 8: Update CHA pandapipes integration
            print(f"\n🔧 Step 8: Updating CHA Pandapipes Integration")
            if not self.update_cha_pandapipes_integration(cha_output_dir):
                raise Exception("Failed to update CHA pandapipes integration")
            
            print(f"\n🎉 Complete Flow Integration Process Finished Successfully!")
            
            return {
                'building_flows': self.building_flows,
                'pipe_segment_flows': self.pipe_segment_flows,
                'sizing_results': self.sizing_results,
                'mass_flows': self.mass_flows,
                'aggregated_flows': self.aggregated_flows,
                'design_hour': self.design_hour,
                'flow_balance_validated': self.flow_balance_validated,
                'summary': self._generate_summary()
            }
            
        except Exception as e:
            print(f"❌ Error in flow integration process: {e}")
            raise
    
    def _generate_summary(self) -> Dict:
        """Generate summary of integration results."""
        summary = {
            'buildings': len(self.building_flows),
            'pipe_segments': len(self.pipe_segment_flows),
            'sized_pipes': len(self.sizing_results),
            'total_flow_kg_s': sum(flow.mass_flow_rate_kg_s for flow in self.building_flows.values()),
            'total_cost_eur': sum(result['cost_eur'] for result in self.sizing_results.values()),
            'compliant_pipes': sum(1 for result in self.sizing_results.values() 
                                 if len(result['violations']) == 0),
            'diameter_distribution': {},
            # New mass flow integration summary
            'mass_flow_integration': {
                'design_hour': self.design_hour,
                'total_mass_flow_kg_s': sum(self.mass_flows.values()) if self.mass_flows else 0.0,
                'total_aggregated_flow_kg_s': sum(self.aggregated_flows.values()) if self.aggregated_flows else 0.0,
                'flow_balance_validated': self.flow_balance_validated,
                'buildings_with_mass_flows': len(self.mass_flows),
                'pipes_with_aggregated_flows': len(self.aggregated_flows)
            }
        }
        
        # Calculate diameter distribution
        for result in self.sizing_results.values():
            diameter = result['diameter_nominal']
            if diameter not in summary['diameter_distribution']:
                summary['diameter_distribution'][diameter] = 0
            summary['diameter_distribution'][diameter] += 1
        
        return summary
    
    def export_integration_results(self, output_path: str) -> None:
        """
        Export integration results to JSON file.
        
        Args:
            output_path: Output file path
        """
        export_data = {
            'summary': self._generate_summary(),
            'building_flows': {},
            'pipe_segment_flows': {},
            'sizing_results': self.sizing_results
        }
        
        # Export building flows
        for building_id, result in self.building_flows.items():
            export_data['building_flows'][building_id] = {
                'peak_hour': result.peak_hour,
                'peak_heat_demand_kw': result.peak_heat_demand_kw,
                'mass_flow_rate_kg_s': result.mass_flow_rate_kg_s,
                'volume_flow_rate_m3_s': result.volume_flow_rate_m3_s,
                'annual_heat_demand_mwh': result.annual_heat_demand_mwh
            }
        
        # Export pipe segment flows
        for pipe_id, flow in self.pipe_segment_flows.items():
            export_data['pipe_segment_flows'][pipe_id] = {
                'start_node': flow.start_node,
                'end_node': flow.end_node,
                'aggregated_flow_kg_s': flow.aggregated_flow_kg_s,
                'building_count': flow.building_count,
                'pipe_category': flow.pipe_category
            }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Integration results exported to {output_path}")
    
    def print_integration_summary(self) -> None:
        """Print summary of integration results."""
        summary = self._generate_summary()
        
        print(f"\n📊 FLOW INTEGRATION SUMMARY")
        print(f"=" * 50)
        print(f"🏗️ OVERVIEW:")
        print(f"   Buildings: {summary['buildings']}")
        print(f"   Pipe Segments: {summary['pipe_segments']}")
        print(f"   Sized Pipes: {summary['sized_pipes']}")
        print(f"   Total Flow: {summary['total_flow_kg_s']:.2f} kg/s")
        print(f"   Total Cost: €{summary['total_cost_eur']:.0f}")
        print(f"")
        print(f"✅ COMPLIANCE:")
        print(f"   Compliant Pipes: {summary['compliant_pipes']}/{summary['sized_pipes']}")
        if summary['sized_pipes'] > 0:
            print(f"   Compliance Rate: {summary['compliant_pipes']/summary['sized_pipes']*100:.1f}%")
        else:
            print(f"   Compliance Rate: N/A (no pipes sized)")
        print(f"")
        print(f"📏 DIAMETER DISTRIBUTION:")
        for diameter, count in summary['diameter_distribution'].items():
            print(f"   {diameter}: {count} pipes")
        
        # Print mass flow integration summary
        mass_flow_info = summary.get('mass_flow_integration', {})
        if mass_flow_info:
            print(f"")
            print(f"🔄 MASS FLOW INTEGRATION:")
            print(f"   Design Hour: {mass_flow_info.get('design_hour', 'N/A')}")
            print(f"   Total Mass Flow: {mass_flow_info.get('total_mass_flow_kg_s', 0.0):.3f} kg/s")
            print(f"   Total Aggregated Flow: {mass_flow_info.get('total_aggregated_flow_kg_s', 0.0):.3f} kg/s")
            print(f"   Flow Balance: {'✅ VALIDATED' if mass_flow_info.get('flow_balance_validated', False) else '❌ FAILED'}")
            print(f"   Buildings with Mass Flows: {mass_flow_info.get('buildings_with_mass_flows', 0)}")
            print(f"   Pipes with Aggregated Flows: {mass_flow_info.get('pipes_with_aggregated_flows', 0)}")


# Example usage and testing
if __name__ == "__main__":
    # Example LFA data
    lfa_data = {
        'building_1': {
            'series': [10.0, 12.0, 8.0, 15.0, 9.0] + [8.0] * 8755
        },
        'building_2': {
            'series': [8.0, 10.0, 7.0, 12.0, 8.5] + [7.5] * 8755
        }
    }
    
    # Create flow integration system
    flow_integration = CHAFlowIntegration()
    
    try:
        # Run complete flow integration
        results = flow_integration.run_complete_flow_integration(
            lfa_data, 
            "processed/cha"
        )
        
        # Print summary
        flow_integration.print_integration_summary()
        
        # Export results
        flow_integration.export_integration_results("flow_integration_results.json")
        
        print(f"\n🎉 Flow Integration Process Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Error in flow integration process: {e}")
        import traceback
        traceback.print_exc()
