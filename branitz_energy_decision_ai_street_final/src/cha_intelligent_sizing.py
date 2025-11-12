"""
CHA Intelligent Sizing - Main Integration Module

This module integrates all pipe sizing components to provide intelligent
pipe sizing for district heating networks with standards compliance.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

from __future__ import annotations
import json
import yaml
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import warnings

# Import our pipe sizing modules
from src.cha_pipe_sizing import CHAPipeSizingEngine, PipeSizingResult
from src.cha_flow_calculation import CHAFlowCalculationEngine, FlowCalculationResult, NetworkFlowResult
from src.cha_network_hierarchy import CHANetworkHierarchyManager, NetworkHierarchy
from src.cha_standards_compliance import CHAStandardsComplianceEngine, ComplianceResult, StandardsSummary

warnings.filterwarnings("ignore")


class CHAIntelligentSizing:
    """
    Main Intelligent Sizing System for District Heating Networks.
    
    Integrates flow calculation, pipe sizing, network hierarchy management,
    and standards compliance to provide comprehensive pipe sizing solutions.
    """
    
    def __init__(self, config_path: str = "configs/cha_intelligent_sizing.yml"):
        """
        Initialize the intelligent sizing system.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.flow_engine = CHAFlowCalculationEngine(self.config.get('flow_calculation', {}))
        self.sizing_engine = CHAPipeSizingEngine(self.config.get('pipe_sizing', {}))
        self.hierarchy_manager = CHANetworkHierarchyManager(self.config.get('network_hierarchy', {}))
        self.compliance_engine = CHAStandardsComplianceEngine(self.config.get('standards_compliance', {}))
        
        # Results storage
        self.building_flows: Dict[str, FlowCalculationResult] = {}
        self.network_flows: Dict[str, NetworkFlowResult] = {}
        self.pipe_sizing_results: Dict[str, PipeSizingResult] = {}
        self.compliance_results: Dict[str, ComplianceResult] = {}
        self.network_hierarchy: Dict[int, NetworkHierarchy] = {}
        
        print(f"✅ CHA Intelligent Sizing System initialized")
        print(f"   Configuration: {config_path}")
        print(f"   Components: Flow Engine, Sizing Engine, Hierarchy Manager, Compliance Engine")
    
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️ Configuration file {self.config_path} not found, using defaults")
            return self._get_default_config()
        except Exception as e:
            print(f"⚠️ Error loading configuration: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Get default configuration."""
        return {
            'flow_calculation': {
                'supply_temperature_c': 70,
                'return_temperature_c': 40,
                'design_hour_method': 'peak_hour',
                'top_n_hours': 10,
                'design_full_load_hours': 2000,
                'safety_factor': 1.1,
                'diversity_factor': 0.8
            },
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
            'network_hierarchy': {
                'network_analysis': True,
                'connectivity_check': True,
                'critical_path_analysis': True
            },
            'standards_compliance': {
                'standards_enabled': ['EN_13941', 'DIN_1988', 'VDI_2067', 'Local_Codes'],
                'severity_thresholds': {
                    'critical': 0.5,
                    'high': 0.3,
                    'medium': 0.2,
                    'low': 0.1
                }
            }
        }
    
    def run_complete_sizing(self, lfa_data: Dict[str, Dict], 
                          cha_output_dir: str = "processed/cha") -> Dict:
        """
        Run complete intelligent sizing process.
        
        Args:
            lfa_data: LFA heat demand data per building
            cha_output_dir: Directory containing CHA network data
        
        Returns:
            results: Complete sizing results
        """
        print(f"\n🚀 Starting Complete Intelligent Sizing Process")
        print(f"   Buildings: {len(lfa_data)}")
        print(f"   Network Data: {cha_output_dir}")
        
        try:
            # Step 1: Calculate building flows
            print(f"\n📊 Step 1: Calculating Building Flows")
            self.building_flows = self.flow_engine.calculate_building_flows(lfa_data)
            print(f"   ✅ Calculated flows for {len(self.building_flows)} buildings")
            
            # Step 2: Load network data
            print(f"\n🌐 Step 2: Loading Network Data")
            network_loaded = self.hierarchy_manager.load_network_data(cha_output_dir)
            if not network_loaded:
                raise Exception("Failed to load network data")
            print(f"   ✅ Network data loaded successfully")
            
            # Step 3: Aggregate network flows
            print(f"\n🔄 Step 3: Aggregating Network Flows")
            # Convert building flows to flow data for aggregation
            flow_data = {building_id: result.mass_flow_kg_s 
                        for building_id, result in self.building_flows.items()}
            self.network_flows = self.flow_engine.aggregate_network_flows(
                self.building_flows, 
                self.hierarchy_manager.network_graph
            )
            print(f"   ✅ Aggregated flows for {len(self.network_flows)} pipes")
            
            # Step 4: Categorize pipes
            print(f"\n🏷️ Step 4: Categorizing Pipes")
            self.hierarchy_manager.categorize_pipes(flow_data)
            print(f"   ✅ Pipes categorized by flow rates")
            
            # Step 5: Size pipes
            print(f"\n📏 Step 5: Sizing Pipes")
            self.pipe_sizing_results = self._size_all_pipes()
            print(f"   ✅ Sized {len(self.pipe_sizing_results)} pipes")
            
            # Step 6: Validate compliance
            print(f"\n✅ Step 6: Validating Standards Compliance")
            self.compliance_results = self._validate_all_pipes()
            print(f"   ✅ Validated compliance for {len(self.compliance_results)} pipes")
            
            # Step 7: Create network hierarchy
            print(f"\n🏗️ Step 7: Creating Network Hierarchy")
            self.network_hierarchy = self.hierarchy_manager.create_network_hierarchy(flow_data)
            print(f"   ✅ Created {len(self.network_hierarchy)} hierarchy levels")
            
            # Step 8: Generate summary
            print(f"\n📋 Step 8: Generating Summary")
            summary = self._generate_summary()
            print(f"   ✅ Summary generated")
            
            print(f"\n🎉 Complete Intelligent Sizing Process Finished Successfully!")
            
            return {
                'building_flows': self.building_flows,
                'network_flows': self.network_flows,
                'pipe_sizing_results': self.pipe_sizing_results,
                'compliance_results': self.compliance_results,
                'network_hierarchy': self.network_hierarchy,
                'summary': summary
            }
            
        except Exception as e:
            print(f"❌ Error in complete sizing process: {e}")
            raise
    
    def _size_all_pipes(self) -> Dict[str, PipeSizingResult]:
        """Size all pipes in the network."""
        sizing_results = {}
        
        for pipe_id, network_flow in self.network_flows.items():
            # Get pipe information from hierarchy manager
            if pipe_id in self.hierarchy_manager.pipes:
                pipe = self.hierarchy_manager.pipes[pipe_id]
                
                # Size the pipe
                result = self.sizing_engine.size_pipe(
                    flow_rate_kg_s=network_flow.aggregated_flow_kg_s,
                    length_m=pipe.length_m,
                    pipe_category=network_flow.pipe_category
                )
                
                sizing_results[pipe_id] = result
        
        return sizing_results
    
    def _validate_all_pipes(self) -> Dict[str, ComplianceResult]:
        """Validate compliance for all pipes."""
        compliance_results = {}
        
        for pipe_id, sizing_result in self.pipe_sizing_results.items():
            # Prepare pipe data for compliance validation
            pipe_data = {
                'pipe_id': pipe_id,
                'velocity_ms': sizing_result.velocity_ms,
                'pressure_drop_pa_per_m': sizing_result.pressure_drop_pa_per_m,
                'diameter_m': sizing_result.diameter_m,
                'pipe_category': self.network_flows[pipe_id].pipe_category,
                'temperature_supply_c': 70,
                'temperature_return_c': 40,
                'pressure_bar': 6,
                'safety_factor': 2.5,
                'payback_period_years': 10,
                'lifecycle_cost_eur_per_mwh': 40
            }
            
            # Validate compliance
            result = self.compliance_engine.validate_pipe_compliance(pipe_data)
            compliance_results[pipe_id] = result
        
        return compliance_results
    
    def _generate_summary(self) -> Dict:
        """Generate comprehensive summary of sizing results."""
        # Calculate totals
        total_buildings = len(self.building_flows)
        total_pipes = len(self.pipe_sizing_results)
        total_flow_kg_s = sum(result.aggregated_flow_kg_s for result in self.network_flows.values())
        total_length_m = sum(result.length_m for result in self.pipe_sizing_results.values())
        total_cost_eur = sum(result.total_cost_eur for result in self.pipe_sizing_results.values())
        
        # Calculate compliance statistics
        compliant_pipes = sum(1 for result in self.compliance_results.values() if result.overall_compliant)
        compliance_rate = compliant_pipes / total_pipes if total_pipes > 0 else 0.0
        
        # Calculate pipe category distribution
        category_distribution = {}
        for result in self.network_flows.values():
            category = result.pipe_category
            if category not in category_distribution:
                category_distribution[category] = 0
            category_distribution[category] += 1
        
        # Calculate diameter distribution
        diameter_distribution = {}
        for result in self.pipe_sizing_results.values():
            diameter = result.diameter_nominal
            if diameter not in diameter_distribution:
                diameter_distribution[diameter] = 0
            diameter_distribution[diameter] += 1
        
        # Calculate violation statistics
        total_violations = sum(len(result.violations) for result in self.compliance_results.values())
        violations_by_severity = {}
        for result in self.compliance_results.values():
            for violation in result.violations:
                severity = violation.severity
                if severity not in violations_by_severity:
                    violations_by_severity[severity] = 0
                violations_by_severity[severity] += 1
        
        return {
            'overview': {
                'total_buildings': total_buildings,
                'total_pipes': total_pipes,
                'total_flow_kg_s': total_flow_kg_s,
                'total_length_m': total_length_m,
                'total_cost_eur': total_cost_eur
            },
            'compliance': {
                'compliant_pipes': compliant_pipes,
                'non_compliant_pipes': total_pipes - compliant_pipes,
                'compliance_rate': compliance_rate,
                'total_violations': total_violations,
                'violations_by_severity': violations_by_severity
            },
            'distribution': {
                'pipe_categories': category_distribution,
                'diameters': diameter_distribution
            },
            'performance': {
                'average_velocity_ms': sum(result.velocity_ms for result in self.pipe_sizing_results.values()) / total_pipes if total_pipes > 0 else 0,
                'average_pressure_drop_bar': sum(result.pressure_drop_bar for result in self.pipe_sizing_results.values()) / total_pipes if total_pipes > 0 else 0,
                'average_cost_per_m_eur': total_cost_eur / total_length_m if total_length_m > 0 else 0
            }
        }
    
    def export_results(self, output_dir: str = "processed/cha_intelligent_sizing") -> None:
        """
        Export all results to files.
        
        Args:
            output_dir: Output directory for results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📁 Exporting Results to {output_dir}")
        
        # Export building flows
        self.flow_engine.export_flow_results(
            self.building_flows, 
            self.network_flows, 
            output_path / "flow_results.json"
        )
        
        # Export pipe sizing results
        sizing_results_list = list(self.pipe_sizing_results.values())
        self.sizing_engine.export_sizing_results(
            sizing_results_list,
            output_path / "pipe_sizing_results.json"
        )
        
        # Export compliance results
        compliance_results_list = list(self.compliance_results.values())
        network_summary = self.compliance_engine.validate_network_compliance(compliance_results_list)
        self.compliance_engine.export_compliance_results(
            compliance_results_list,
            network_summary,
            output_path / "compliance_results.json"
        )
        
        # Export network hierarchy
        self.hierarchy_manager.export_network_hierarchy(
            self.network_hierarchy,
            output_path / "network_hierarchy.json"
        )
        
        # Export summary
        summary = self._generate_summary()
        with open(output_path / "summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"   ✅ All results exported successfully")
    
    def get_recommendations(self) -> List[str]:
        """Get recommendations based on analysis results."""
        recommendations = []
        
        # Check compliance issues
        non_compliant_pipes = [result for result in self.compliance_results.values() 
                              if not result.overall_compliant]
        
        if non_compliant_pipes:
            recommendations.append(f"⚠️ {len(non_compliant_pipes)} pipes have compliance violations")
            
            # Check for critical violations
            critical_violations = []
            for result in non_compliant_pipes:
                for violation in result.violations:
                    if violation.severity == 'critical':
                        critical_violations.append(violation)
            
            if critical_violations:
                recommendations.append(f"🚨 {len(critical_violations)} critical violations require immediate attention")
        
        # Check cost optimization opportunities
        high_cost_pipes = [result for result in self.pipe_sizing_results.values() 
                          if result.cost_per_m_eur > 100]
        
        if high_cost_pipes:
            recommendations.append(f"💰 {len(high_cost_pipes)} pipes have high costs - consider optimization")
        
        # Check velocity issues
        high_velocity_pipes = [result for result in self.pipe_sizing_results.values() 
                              if result.velocity_ms > 2.0]
        
        if high_velocity_pipes:
            recommendations.append(f"⚡ {len(high_velocity_pipes)} pipes have high velocities - consider larger diameters")
        
        # Check pressure drop issues
        high_pressure_drop_pipes = [result for result in self.pipe_sizing_results.values() 
                                   if result.pressure_drop_bar > 0.5]
        
        if high_pressure_drop_pipes:
            recommendations.append(f"🔧 {len(high_pressure_drop_pipes)} pipes have high pressure drops - consider larger diameters")
        
        return recommendations
    
    def print_summary(self) -> None:
        """Print comprehensive summary of results."""
        summary = self._generate_summary()
        
        print(f"\n📊 INTELLIGENT SIZING SUMMARY")
        print(f"=" * 50)
        
        # Overview
        overview = summary['overview']
        print(f"\n🏗️ NETWORK OVERVIEW:")
        print(f"   Buildings: {overview['total_buildings']}")
        print(f"   Pipes: {overview['total_pipes']}")
        print(f"   Total Flow: {overview['total_flow_kg_s']:.2f} kg/s")
        print(f"   Total Length: {overview['total_length_m']:.0f} m")
        print(f"   Total Cost: €{overview['total_cost_eur']:.0f}")
        
        # Compliance
        compliance = summary['compliance']
        print(f"\n✅ COMPLIANCE:")
        print(f"   Compliant Pipes: {compliance['compliant_pipes']}/{overview['total_pipes']}")
        print(f"   Compliance Rate: {compliance['compliance_rate']:.1%}")
        print(f"   Total Violations: {compliance['total_violations']}")
        if compliance['violations_by_severity']:
            print(f"   Violations by Severity: {compliance['violations_by_severity']}")
        
        # Distribution
        distribution = summary['distribution']
        print(f"\n📊 DISTRIBUTION:")
        print(f"   Pipe Categories: {distribution['pipe_categories']}")
        print(f"   Diameters: {distribution['diameters']}")
        
        # Performance
        performance = summary['performance']
        print(f"\n⚡ PERFORMANCE:")
        print(f"   Average Velocity: {performance['average_velocity_ms']:.2f} m/s")
        print(f"   Average Pressure Drop: {performance['average_pressure_drop_bar']:.3f} bar")
        print(f"   Average Cost: €{performance['average_cost_per_m_eur']:.1f}/m")
        
        # Recommendations
        recommendations = self.get_recommendations()
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print(f"\n✅ No major issues found - system is well-designed!")


# Example usage and testing
if __name__ == "__main__":
    # Create intelligent sizing system
    intelligent_sizing = CHAIntelligentSizing()
    
    # Example LFA data
    lfa_data = {
        'building_1': {
            'series': [10.5, 12.3, 8.7, 15.2, 9.1] + [8.0] * 8755  # 8760 hours
        },
        'building_2': {
            'series': [8.2, 9.1, 7.5, 11.8, 8.9] + [7.5] * 8755
        },
        'building_3': {
            'series': [12.1, 14.5, 10.2, 16.8, 11.3] + [9.5] * 8755
        }
    }
    
    try:
        # Run complete sizing process
        results = intelligent_sizing.run_complete_sizing(lfa_data)
        
        # Print summary
        intelligent_sizing.print_summary()
        
        # Export results
        intelligent_sizing.export_results()
        
        print(f"\n🎉 Intelligent Sizing Process Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Error in intelligent sizing process: {e}")
        import traceback
        traceback.print_exc()
