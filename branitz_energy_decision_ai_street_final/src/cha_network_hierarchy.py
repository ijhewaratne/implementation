"""
CHA Network Hierarchy Manager - Network Structure and Flow Path Management

This module manages the network hierarchy, pipe categorization, and flow path
tracing for intelligent pipe sizing in district heating networks.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

from __future__ import annotations
import json
import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Set
from dataclasses import dataclass
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


@dataclass
class NetworkNode:
    """Network node representation."""
    node_id: str
    node_type: str  # 'plant', 'junction', 'building'
    coordinates: Tuple[float, float]
    elevation_m: float
    pressure_bar: float
    temperature_c: float
    connected_pipes: List[str]


@dataclass
class NetworkPipe:
    """Network pipe representation."""
    pipe_id: str
    start_node: str
    end_node: str
    length_m: float
    diameter_m: float
    pipe_category: str
    pipe_type: str  # 'supply', 'return', 'service'
    material: str
    insulation: str
    building_served: Optional[str]
    street_id: Optional[str]
    flow_direction: str


@dataclass
class NetworkHierarchy:
    """Network hierarchy structure."""
    level: int
    name: str
    pipes: List[str]
    total_length_m: float
    total_flow_kg_s: float
    average_diameter_m: float
    cost_eur: float


class CHANetworkHierarchyManager:
    """
    Network Hierarchy Manager for District Heating Networks.
    
    Manages network structure, pipe categorization, flow path tracing,
    and hierarchy-based pipe sizing.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the network hierarchy manager.
        
        Args:
            config: Configuration dictionary with network parameters
        """
        self.config = config
        
        # Network structure
        self.network_graph = nx.DiGraph()
        self.nodes: Dict[str, NetworkNode] = {}
        self.pipes: Dict[str, NetworkPipe] = {}
        
        # Hierarchy levels
        self.hierarchy_levels = {
            1: {'name': 'Service Connections', 'min_flow_kg_s': 0, 'max_flow_kg_s': 2},
            2: {'name': 'Street Distribution', 'min_flow_kg_s': 2, 'max_flow_kg_s': 10},
            3: {'name': 'Area Distribution', 'min_flow_kg_s': 10, 'max_flow_kg_s': 30},
            4: {'name': 'Main Distribution', 'min_flow_kg_s': 30, 'max_flow_kg_s': 80},
            5: {'name': 'Primary Main', 'min_flow_kg_s': 80, 'max_flow_kg_s': 200}
        }
        
        # Pipe categories
        self.pipe_categories = {
            'service_connection': {
                'diameter_range_m': (0.025, 0.050),
                'typical_length_m': 50,
                'material': 'steel_or_plastic',
                'insulation': 'required'
            },
            'distribution_pipe': {
                'diameter_range_m': (0.063, 0.150),
                'typical_length_m': 200,
                'material': 'steel',
                'insulation': 'required'
            },
            'main_pipe': {
                'diameter_range_m': (0.200, 0.400),
                'typical_length_m': 1000,
                'material': 'steel',
                'insulation': 'required'
            }
        }
        
        print(f"✅ Network Hierarchy Manager initialized")
        print(f"   Hierarchy Levels: {len(self.hierarchy_levels)}")
        print(f"   Pipe Categories: {len(self.pipe_categories)}")
    
    def load_network_data(self, cha_output_dir: str) -> bool:
        """
        Load network data from CHA output files.
        
        Args:
            cha_output_dir: Directory containing CHA output files
        
        Returns:
            success: True if loading successful
        """
        try:
            cha_dir = Path(cha_output_dir)
            
            # Load supply pipes
            supply_pipes_df = pd.read_csv(cha_dir / "supply_pipes.csv")
            self._load_pipes(supply_pipes_df, 'supply')
            
            # Load return pipes
            return_pipes_df = pd.read_csv(cha_dir / "return_pipes.csv")
            self._load_pipes(return_pipes_df, 'return')
            
            # Load service connections
            service_connections_df = pd.read_csv(cha_dir / "service_connections.csv")
            self._load_service_connections(service_connections_df)
            
            # Build network graph
            self._build_network_graph()
            
            print(f"✅ Network data loaded successfully")
            print(f"   Nodes: {len(self.nodes)}")
            print(f"   Pipes: {len(self.pipes)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load network data: {e}")
            return False
    
    def _load_pipes(self, pipes_df: pd.DataFrame, pipe_type: str) -> None:
        """Load pipes from DataFrame."""
        for _, row in pipes_df.iterrows():
            pipe_id = f"{pipe_type}_{row.get('street_id', 'unknown')}_{row.get('building_served', 'unknown')}"
            
            # Parse node coordinates
            start_node = self._parse_node_coordinates(row['start_node'])
            end_node = self._parse_node_coordinates(row['end_node'])
            
            # Create pipe
            pipe = NetworkPipe(
                pipe_id=pipe_id,
                start_node=start_node,
                end_node=end_node,
                length_m=row['length_m'],
                diameter_m=row.get('diameter_m', 0.1),  # Default diameter
                pipe_category='unknown',  # Will be determined later
                pipe_type=pipe_type,
                material='steel',
                insulation='polyurethane',
                building_served=row.get('building_served'),
                street_id=row.get('street_id'),
                flow_direction=row.get('flow_direction', 'unknown')
            )
            
            self.pipes[pipe_id] = pipe
    
    def _load_service_connections(self, service_df: pd.DataFrame) -> None:
        """Load service connections from DataFrame."""
        for _, row in service_df.iterrows():
            pipe_id = f"service_{row['building_id']}_{row['pipe_type']}"
            
            # Parse coordinates
            start_node = f"building_{row['building_id']}"
            end_node = f"connection_{row['building_id']}"
            
            # Create service connection pipe
            pipe = NetworkPipe(
                pipe_id=pipe_id,
                start_node=start_node,
                end_node=end_node,
                length_m=row.get('distance_to_street', 20),  # Default 20m
                diameter_m=0.032,  # Default DN 32
                pipe_category='service_connection',
                pipe_type=row['pipe_type'],
                material='steel',
                insulation='polyurethane',
                building_served=row['building_id'],
                street_id=row.get('street_segment_id'),
                flow_direction=row.get('flow_direction', 'unknown')
            )
            
            self.pipes[pipe_id] = pipe
    
    def _parse_node_coordinates(self, node_str: str) -> str:
        """Parse node coordinates string to node ID."""
        if isinstance(node_str, str) and node_str.startswith('('):
            # Extract coordinates from string like "(x, y)"
            coords = node_str.strip('()').split(',')
            if len(coords) == 2:
                x, y = float(coords[0].strip()), float(coords[1].strip())
                return f"node_{x:.1f}_{y:.1f}"
        return str(node_str)
    
    def _build_network_graph(self) -> None:
        """Build network graph from pipes and nodes."""
        # Add nodes
        for pipe in self.pipes.values():
            # Add start node
            if pipe.start_node not in self.nodes:
                self.nodes[pipe.start_node] = NetworkNode(
                    node_id=pipe.start_node,
                    node_type=self._determine_node_type(pipe.start_node),
                    coordinates=(0, 0),  # Will be updated with actual coordinates
                    elevation_m=0,
                    pressure_bar=2.0,
                    temperature_c=40,
                    connected_pipes=[]
                )
            
            # Add end node
            if pipe.end_node not in self.nodes:
                self.nodes[pipe.end_node] = NetworkNode(
                    node_id=pipe.end_node,
                    node_type=self._determine_node_type(pipe.end_node),
                    coordinates=(0, 0),  # Will be updated with actual coordinates
                    elevation_m=0,
                    pressure_bar=2.0,
                    temperature_c=40,
                    connected_pipes=[]
                )
            
            # Add pipe to graph
            self.network_graph.add_edge(
                pipe.start_node,
                pipe.end_node,
                pipe_id=pipe.pipe_id,
                length=pipe.length_m,
                diameter=pipe.diameter_m,
                pipe_type=pipe.pipe_type
            )
            
            # Update node connections
            self.nodes[pipe.start_node].connected_pipes.append(pipe.pipe_id)
            self.nodes[pipe.end_node].connected_pipes.append(pipe.pipe_id)
    
    def _determine_node_type(self, node_id: str) -> str:
        """Determine node type from node ID."""
        if 'plant' in node_id.lower():
            return 'plant'
        elif 'building' in node_id.lower():
            return 'building'
        else:
            return 'junction'
    
    def categorize_pipes(self, flow_data: Dict[str, float]) -> None:
        """
        Categorize pipes based on flow rates.
        
        Args:
            flow_data: Flow rates per pipe
        """
        for pipe_id, pipe in self.pipes.items():
            flow_rate_kg_s = flow_data.get(pipe_id, 0.0)
            
            # Determine pipe category based on flow rate
            if flow_rate_kg_s < 2.0:
                pipe.pipe_category = 'service_connection'
            elif flow_rate_kg_s < 20.0:
                pipe.pipe_category = 'distribution_pipe'
            else:
                pipe.pipe_category = 'main_pipe'
            
            # Update pipe in graph
            if self.network_graph.has_edge(pipe.start_node, pipe.end_node):
                self.network_graph[pipe.start_node][pipe.end_node]['pipe_category'] = pipe.pipe_category
    
    def trace_flow_paths(self, building_id: str) -> Dict[str, List[str]]:
        """
        Trace flow paths from plant to building.
        
        Args:
            building_id: Building ID to trace paths for
        
        Returns:
            flow_paths: Dictionary with supply and return paths
        """
        flow_paths = {
            'supply_path': [],
            'return_path': []
        }
        
        # Find plant node
        plant_node = None
        for node_id, node in self.nodes.items():
            if node.node_type == 'plant':
                plant_node = node_id
                break
        
        if not plant_node:
            print(f"⚠️ Plant node not found")
            return flow_paths
        
        # Find building node
        building_node = f"building_{building_id}"
        if building_node not in self.nodes:
            print(f"⚠️ Building node {building_node} not found")
            return flow_paths
        
        # Trace supply path (plant to building)
        try:
            supply_path = nx.shortest_path(self.network_graph, plant_node, building_node)
            flow_paths['supply_path'] = supply_path
        except nx.NetworkXNoPath:
            print(f"⚠️ No supply path found from plant to building {building_id}")
        
        # Trace return path (building to plant)
        try:
            return_path = nx.shortest_path(self.network_graph, building_node, plant_node)
            flow_paths['return_path'] = return_path
        except nx.NetworkXNoPath:
            print(f"⚠️ No return path found from building {building_id} to plant")
        
        return flow_paths
    
    def create_network_hierarchy(self, flow_data: Dict[str, float]) -> Dict[int, NetworkHierarchy]:
        """
        Create network hierarchy based on flow rates.
        
        Args:
            flow_data: Flow rates per pipe
        
        Returns:
            hierarchy: Network hierarchy structure
        """
        hierarchy = {}
        
        for level, level_info in self.hierarchy_levels.items():
            # Find pipes in this level
            level_pipes = []
            total_length = 0.0
            total_flow = 0.0
            total_cost = 0.0
            diameters = []
            
            for pipe_id, pipe in self.pipes.items():
                flow_rate_kg_s = flow_data.get(pipe_id, 0.0)
                
                if level_info['min_flow_kg_s'] <= flow_rate_kg_s < level_info['max_flow_kg_s']:
                    level_pipes.append(pipe_id)
                    total_length += pipe.length_m
                    total_flow += flow_rate_kg_s
                    diameters.append(pipe.diameter_m)
                    
                    # Estimate cost (simplified)
                    cost_per_m = 50 + (pipe.diameter_m * 1000) * 2  # EUR per meter
                    total_cost += cost_per_m * pipe.length_m
            
            # Calculate average diameter
            average_diameter = np.mean(diameters) if diameters else 0.0
            
            # Create hierarchy level
            hierarchy[level] = NetworkHierarchy(
                level=level,
                name=level_info['name'],
                pipes=level_pipes,
                total_length_m=total_length,
                total_flow_kg_s=total_flow,
                average_diameter_m=average_diameter,
                cost_eur=total_cost
            )
        
        return hierarchy
    
    def find_critical_paths(self, flow_data: Dict[str, float]) -> List[Dict]:
        """
        Find critical paths in the network.
        
        Args:
            flow_data: Flow rates per pipe
        
        Returns:
            critical_paths: List of critical path information
        """
        critical_paths = []
        
        # Find pipes with high flow rates
        high_flow_pipes = [
            (pipe_id, flow) for pipe_id, flow in flow_data.items() 
            if flow > 50.0  # High flow threshold
        ]
        
        for pipe_id, flow_rate in high_flow_pipes:
            if pipe_id in self.pipes:
                pipe = self.pipes[pipe_id]
                
                # Trace path for this pipe
                path_info = {
                    'pipe_id': pipe_id,
                    'flow_rate_kg_s': flow_rate,
                    'length_m': pipe.length_m,
                    'diameter_m': pipe.diameter_m,
                    'pipe_category': pipe.pipe_category,
                    'criticality_score': flow_rate * pipe.length_m,  # Simple criticality metric
                    'upstream_pipes': self._find_upstream_pipes(pipe_id),
                    'downstream_pipes': self._find_downstream_pipes(pipe_id)
                }
                
                critical_paths.append(path_info)
        
        # Sort by criticality score
        critical_paths.sort(key=lambda x: x['criticality_score'], reverse=True)
        
        return critical_paths
    
    def _find_upstream_pipes(self, pipe_id: str) -> List[str]:
        """Find upstream pipes for a given pipe."""
        if pipe_id not in self.pipes:
            return []
        
        pipe = self.pipes[pipe_id]
        upstream_pipes = []
        
        # Find pipes connected to start node
        for other_pipe_id, other_pipe in self.pipes.items():
            if other_pipe.end_node == pipe.start_node:
                upstream_pipes.append(other_pipe_id)
        
        return upstream_pipes
    
    def _find_downstream_pipes(self, pipe_id: str) -> List[str]:
        """Find downstream pipes for a given pipe."""
        if pipe_id not in self.pipes:
            return []
        
        pipe = self.pipes[pipe_id]
        downstream_pipes = []
        
        # Find pipes connected to end node
        for other_pipe_id, other_pipe in self.pipes.items():
            if other_pipe.start_node == pipe.end_node:
                downstream_pipes.append(other_pipe_id)
        
        return downstream_pipes
    
    def analyze_network_connectivity(self) -> Dict:
        """
        Analyze network connectivity.
        
        Returns:
            connectivity_analysis: Network connectivity information
        """
        analysis = {
            'is_connected': nx.is_weakly_connected(self.network_graph),
            'number_of_components': nx.number_weakly_connected_components(self.network_graph),
            'components': [],
            'isolated_nodes': [],
            'critical_nodes': []
        }
        
        # Find connected components
        components = list(nx.weakly_connected_components(self.network_graph))
        for i, component in enumerate(components):
            analysis['components'].append({
                'component_id': i,
                'size': len(component),
                'nodes': list(component)
            })
        
        # Find isolated nodes
        isolated_nodes = list(nx.isolates(self.network_graph))
        analysis['isolated_nodes'] = isolated_nodes
        
        # Find critical nodes (high degree)
        node_degrees = dict(self.network_graph.degree())
        critical_nodes = [
            node for node, degree in node_degrees.items() 
            if degree > 5  # High connectivity threshold
        ]
        analysis['critical_nodes'] = critical_nodes
        
        return analysis
    
    def export_network_hierarchy(self, hierarchy: Dict[int, NetworkHierarchy], 
                               output_path: str) -> None:
        """
        Export network hierarchy to JSON file.
        
        Args:
            hierarchy: Network hierarchy structure
            output_path: Output file path
        """
        export_data = {
            'hierarchy_levels': {},
            'summary': {
                'total_levels': len(hierarchy),
                'total_pipes': sum(len(level.pipes) for level in hierarchy.values()),
                'total_length_m': sum(level.total_length_m for level in hierarchy.values()),
                'total_flow_kg_s': sum(level.total_flow_kg_s for level in hierarchy.values()),
                'total_cost_eur': sum(level.cost_eur for level in hierarchy.values())
            }
        }
        
        # Export hierarchy levels
        for level, level_info in hierarchy.items():
            export_data['hierarchy_levels'][str(level)] = {
                'name': level_info.name,
                'pipe_count': len(level_info.pipes),
                'total_length_m': level_info.total_length_m,
                'total_flow_kg_s': level_info.total_flow_kg_s,
                'average_diameter_m': level_info.average_diameter_m,
                'cost_eur': level_info.cost_eur,
                'pipes': level_info.pipes
            }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Network hierarchy exported to {output_path}")


# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    config = {
        'network_analysis': True,
        'connectivity_check': True,
        'critical_path_analysis': True
    }
    
    # Create network hierarchy manager
    hierarchy_manager = CHANetworkHierarchyManager(config)
    
    # Load network data (example)
    success = hierarchy_manager.load_network_data("processed/cha")
    
    if success:
        # Example flow data
        flow_data = {
            'service_building_1_supply_service': 0.5,
            'service_building_2_supply_service': 0.8,
            'supply_street_1_building_1': 5.0,
            'supply_street_2_building_2': 8.0,
            'supply_main_1_unknown': 25.0
        }
        
        # Categorize pipes
        hierarchy_manager.categorize_pipes(flow_data)
        
        # Create network hierarchy
        hierarchy = hierarchy_manager.create_network_hierarchy(flow_data)
        
        # Analyze connectivity
        connectivity = hierarchy_manager.analyze_network_connectivity()
        
        # Find critical paths
        critical_paths = hierarchy_manager.find_critical_paths(flow_data)
        
        # Export results
        hierarchy_manager.export_network_hierarchy(hierarchy, "test_network_hierarchy.json")
        
        # Print summary
        print(f"\n📊 Network Hierarchy Summary:")
        print(f"   Total Levels: {len(hierarchy)}")
        print(f"   Total Pipes: {sum(len(level.pipes) for level in hierarchy.values())}")
        print(f"   Total Length: {sum(level.total_length_m for level in hierarchy.values()):.0f} m")
        print(f"   Total Flow: {sum(level.total_flow_kg_s for level in hierarchy.values()):.2f} kg/s")
        print(f"   Total Cost: €{sum(level.cost_eur for level in hierarchy.values()):.0f}")
        print(f"   Connectivity: {'Connected' if connectivity['is_connected'] else 'Disconnected'}")
        print(f"   Critical Paths: {len(critical_paths)}")
