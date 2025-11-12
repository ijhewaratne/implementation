"""
CHA Cost-Benefit Analyzer - Comprehensive Economic Impact Analysis

This module provides comprehensive cost-benefit analysis for district heating networks,
evaluating the impact of proper pipe sizing on economic performance, hydraulic efficiency,
and overall system optimization.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

from __future__ import annotations
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd

# Import our enhanced components
from cha_pipe_sizing import CHAPipeSizingEngine
from cha_enhanced_config_loader import CHAEnhancedConfigLoader
from eaa_enhanced_integration import EnhancedEAAIntegration, EnhancedEAAConfig

@dataclass
class CostBenefitResult:
    """Cost-benefit analysis result."""
    # CAPEX Analysis
    capex_impact: Dict[str, Any]
    
    # OPEX Analysis
    opex_impact: Dict[str, Any]
    
    # Hydraulic Improvement
    hydraulic_improvement: Dict[str, Any]
    
    # Economic Metrics
    economic_metrics: Dict[str, Any]
    
    # Recommendations
    recommendations: List[str]
    
    # Summary
    summary: Dict[str, Any]


@dataclass
class PipeSizingComparison:
    """Comparison between fixed and sized pipe networks."""
    pipe_id: str
    fixed_diameter_m: float
    sized_diameter_m: float
    fixed_cost_eur: float
    sized_cost_eur: float
    cost_difference_eur: float
    cost_percentage_change: float
    hydraulic_improvement: Dict[str, Any]


@dataclass
class EconomicImpactAnalysis:
    """Economic impact analysis result."""
    total_capex_impact_eur: float
    total_opex_impact_eur: float
    total_hydraulic_benefit_eur: float
    net_benefit_eur: float
    payback_period_years: float
    net_present_value_eur: float
    internal_rate_of_return: float
    benefit_cost_ratio: float


class CHACostBenefitAnalyzer:
    """
    Comprehensive cost-benefit analyzer for district heating networks.
    
    Evaluates the economic impact of proper pipe sizing on CAPEX, OPEX,
    hydraulic performance, and overall system optimization.
    """
    
    def __init__(self, sizing_engine: CHAPipeSizingEngine, 
                 config_loader: Optional[CHAEnhancedConfigLoader] = None,
                 enhanced_eaa: Optional[EnhancedEAAIntegration] = None):
        """
        Initialize the cost-benefit analyzer.
        
        Args:
            sizing_engine: CHA pipe sizing engine instance
            config_loader: Enhanced configuration loader instance
            enhanced_eaa: Enhanced EAA integration instance
        """
        self.sizing_engine = sizing_engine
        self.config_loader = config_loader
        self.enhanced_eaa = enhanced_eaa
        
        # Default economic parameters
        self.discount_rate = 0.06
        self.lifetime_years = 25
        self.electricity_price_eur_per_kwh = 0.22
        self.pump_efficiency = 0.75
        
        print(f"✅ CHA Cost-Benefit Analyzer initialized")
        print(f"   Sizing engine: {'Available' if sizing_engine else 'Not available'}")
        print(f"   Config loader: {'Available' if config_loader else 'Not available'}")
        print(f"   Enhanced EAA: {'Available' if enhanced_eaa else 'Not available'}")
    
    def analyze_pipe_sizing_impact(self, network_data: dict) -> dict:
        """
        Analyze cost-benefit impact of proper pipe sizing.
        
        Args:
            network_data: Network data with pipe information
        
        Returns:
            analysis: Comprehensive cost-benefit analysis result
        """
        print(f"💰 Analyzing pipe sizing impact on cost-benefit...")
        
        analysis = {
            'capex_impact': {},
            'opex_impact': {},
            'hydraulic_improvement': {},
            'economic_metrics': {},
            'recommendations': []
        }
        
        # Compare fixed vs. sized network costs
        fixed_cost = self.calculate_fixed_diameter_cost(network_data)
        sized_cost = self.calculate_sized_network_cost(network_data)
        
        # Analyze CAPEX impact
        analysis['capex_impact'] = self._analyze_capex_impact(network_data, fixed_cost, sized_cost)
        
        # Analyze OPEX impact
        analysis['opex_impact'] = self._analyze_opex_impact(network_data, fixed_cost, sized_cost)
        
        # Analyze hydraulic improvement
        analysis['hydraulic_improvement'] = self._analyze_hydraulic_improvement(network_data)
        
        # Calculate economic metrics
        analysis['economic_metrics'] = self._calculate_economic_metrics(analysis)
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        print(f"✅ Pipe sizing impact analysis completed")
        return analysis
    
    def calculate_fixed_diameter_cost(self, network_data: dict) -> float:
        """
        Calculate cost for fixed diameter network (baseline).
        
        Args:
            network_data: Network data with pipe information
        
        Returns:
            total_cost: Total cost for fixed diameter network
        """
        print(f"📊 Calculating fixed diameter network cost...")
        
        total_cost = 0.0
        fixed_diameter = 0.1  # Default fixed diameter (100mm)
        
        # Get all pipes from network data
        all_pipes = []
        all_pipes.extend(network_data.get('supply_pipes', []))
        all_pipes.extend(network_data.get('return_pipes', []))
        all_pipes.extend(network_data.get('service_connections', []))
        
        for pipe in all_pipes:
            length_m = pipe.get('length_m', 100.0)
            pipe_category = pipe.get('pipe_category', 'distribution_pipes')
            
            # Calculate cost with fixed diameter
            if self.sizing_engine:
                mapped_category = self._map_pipe_category(pipe_category)
                cost_per_m = self.sizing_engine.calculate_pipe_cost(
                    fixed_diameter, 1.0, mapped_category
                )  # Cost per meter
            else:
                cost_per_m = self._get_fallback_pipe_cost(fixed_diameter, pipe_category)
            
            pipe_cost = cost_per_m * length_m
            total_cost += pipe_cost
        
        print(f"✅ Fixed diameter network cost: €{total_cost:.0f}")
        return total_cost
    
    def calculate_sized_network_cost(self, network_data: dict) -> float:
        """
        Calculate cost for sized network (optimized).
        
        Args:
            network_data: Network data with pipe information
        
        Returns:
            total_cost: Total cost for sized network
        """
        print(f"📊 Calculating sized network cost...")
        
        total_cost = 0.0
        
        # Get all pipes from network data
        all_pipes = []
        all_pipes.extend(network_data.get('supply_pipes', []))
        all_pipes.extend(network_data.get('return_pipes', []))
        all_pipes.extend(network_data.get('service_connections', []))
        
        for pipe in all_pipes:
            diameter_m = pipe.get('diameter_m', 0.1)
            length_m = pipe.get('length_m', 100.0)
            pipe_category = pipe.get('pipe_category', 'distribution_pipes')
            
            # Calculate cost with sized diameter
            if self.sizing_engine:
                mapped_category = self._map_pipe_category(pipe_category)
                cost_per_m = self.sizing_engine.calculate_pipe_cost(
                    diameter_m, 1.0, mapped_category
                )  # Cost per meter
            else:
                cost_per_m = self._get_fallback_pipe_cost(diameter_m, pipe_category)
            
            pipe_cost = cost_per_m * length_m
            total_cost += pipe_cost
        
        print(f"✅ Sized network cost: €{total_cost:.0f}")
        return total_cost
    
    def analyze_comprehensive_cost_benefit(self, network_data: dict) -> CostBenefitResult:
        """
        Perform comprehensive cost-benefit analysis.
        
        Args:
            network_data: Network data with pipe information
        
        Returns:
            result: Comprehensive cost-benefit analysis result
        """
        print(f"🧮 Performing comprehensive cost-benefit analysis...")
        
        # Analyze pipe sizing impact
        sizing_impact = self.analyze_pipe_sizing_impact(network_data)
        
        # Perform detailed pipe comparison
        pipe_comparison = self._perform_pipe_comparison(network_data)
        
        # Calculate economic impact
        economic_impact = self._calculate_economic_impact(sizing_impact)
        
        # Generate summary
        summary = self._generate_analysis_summary(sizing_impact, economic_impact)
        
        result = CostBenefitResult(
            capex_impact=sizing_impact['capex_impact'],
            opex_impact=sizing_impact['opex_impact'],
            hydraulic_improvement=sizing_impact['hydraulic_improvement'],
            economic_metrics=sizing_impact['economic_metrics'],
            recommendations=sizing_impact['recommendations'],
            summary=summary
        )
        
        print(f"✅ Comprehensive cost-benefit analysis completed")
        return result
    
    def _analyze_capex_impact(self, network_data: dict, fixed_cost: float, sized_cost: float) -> Dict[str, Any]:
        """Analyze CAPEX impact of pipe sizing."""
        cost_difference = sized_cost - fixed_cost
        cost_percentage_change = (cost_difference / fixed_cost * 100) if fixed_cost > 0 else 0
        
        # Analyze by pipe category
        category_analysis = self._analyze_capex_by_category(network_data)
        
        return {
            'fixed_cost_eur': fixed_cost,
            'sized_cost_eur': sized_cost,
            'cost_difference_eur': cost_difference,
            'cost_percentage_change': cost_percentage_change,
            'category_analysis': category_analysis,
            'cost_effectiveness': 'positive' if cost_difference < 0 else 'negative' if cost_difference > 0 else 'neutral'
        }
    
    def _analyze_opex_impact(self, network_data: dict, fixed_cost: float, sized_cost: float) -> Dict[str, Any]:
        """Analyze OPEX impact of pipe sizing."""
        # Calculate pump energy for both scenarios
        fixed_pump_energy = self._calculate_pump_energy_fixed(network_data)
        sized_pump_energy = self._calculate_pump_energy_sized(network_data)
        
        # Calculate annual OPEX difference
        annual_opex_difference = (sized_pump_energy - fixed_pump_energy) * self.electricity_price_eur_per_kwh
        
        # Calculate lifetime OPEX impact
        lifetime_opex_impact = self._calculate_lifetime_opex_impact(annual_opex_difference)
        
        return {
            'fixed_pump_energy_kwh': fixed_pump_energy,
            'sized_pump_energy_kwh': sized_pump_energy,
            'annual_opex_difference_eur': annual_opex_difference,
            'lifetime_opex_impact_eur': lifetime_opex_impact,
            'opex_improvement': 'positive' if annual_opex_difference < 0 else 'negative' if annual_opex_difference > 0 else 'neutral'
        }
    
    def _analyze_hydraulic_improvement(self, network_data: dict) -> Dict[str, Any]:
        """Analyze hydraulic improvement benefits."""
        # Calculate hydraulic metrics for sized network
        hydraulic_metrics = self._calculate_hydraulic_metrics(network_data)
        
        # Calculate efficiency improvements
        efficiency_improvements = self._calculate_efficiency_improvements(network_data)
        
        # Calculate reliability improvements
        reliability_improvements = self._calculate_reliability_improvements(network_data)
        
        return {
            'hydraulic_metrics': hydraulic_metrics,
            'efficiency_improvements': efficiency_improvements,
            'reliability_improvements': reliability_improvements,
            'overall_improvement': 'positive' if efficiency_improvements.get('overall_efficiency_gain', 0) > 0 else 'neutral'
        }
    
    def _calculate_economic_metrics(self, analysis: dict) -> Dict[str, Any]:
        """Calculate comprehensive economic metrics."""
        capex_impact = analysis['capex_impact']
        opex_impact = analysis['opex_impact']
        
        # Calculate net benefit
        net_benefit = -capex_impact['cost_difference_eur'] + opex_impact['lifetime_opex_impact_eur']
        
        # Calculate payback period
        payback_period = self._calculate_payback_period(
            capex_impact['cost_difference_eur'],
            opex_impact['annual_opex_difference_eur']
        )
        
        # Calculate NPV
        npv = self._calculate_npv(
            capex_impact['cost_difference_eur'],
            opex_impact['annual_opex_difference_eur']
        )
        
        # Calculate IRR
        irr = self._calculate_irr(
            capex_impact['cost_difference_eur'],
            opex_impact['annual_opex_difference_eur']
        )
        
        # Calculate benefit-cost ratio
        bcr = self._calculate_benefit_cost_ratio(
            opex_impact['lifetime_opex_impact_eur'],
            capex_impact['cost_difference_eur']
        )
        
        return {
            'net_benefit_eur': net_benefit,
            'payback_period_years': payback_period,
            'net_present_value_eur': npv,
            'internal_rate_of_return': irr,
            'benefit_cost_ratio': bcr,
            'economic_viability': 'viable' if npv > 0 and bcr > 1 else 'not_viable'
        }
    
    def _generate_recommendations(self, analysis: dict) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        capex_impact = analysis['capex_impact']
        opex_impact = analysis['opex_impact']
        economic_metrics = analysis['economic_metrics']
        
        # CAPEX recommendations
        if capex_impact['cost_percentage_change'] > 10:
            recommendations.append("Consider optimizing pipe sizing to reduce CAPEX costs")
        elif capex_impact['cost_percentage_change'] < -10:
            recommendations.append("Current pipe sizing provides significant CAPEX savings")
        
        # OPEX recommendations
        if opex_impact['annual_opex_difference_eur'] < -1000:
            recommendations.append("Pipe sizing provides significant OPEX savings through reduced pumping energy")
        elif opex_impact['annual_opex_difference_eur'] > 1000:
            recommendations.append("Consider optimizing pipe sizing to reduce OPEX costs")
        
        # Economic viability recommendations
        if economic_metrics['economic_viability'] == 'viable':
            recommendations.append("Pipe sizing optimization is economically viable and recommended")
        else:
            recommendations.append("Pipe sizing optimization may not be economically viable - consider alternatives")
        
        # Payback period recommendations
        if economic_metrics['payback_period_years'] < 5:
            recommendations.append("Excellent payback period - implement sizing optimization immediately")
        elif economic_metrics['payback_period_years'] < 10:
            recommendations.append("Good payback period - consider implementing sizing optimization")
        else:
            recommendations.append("Long payback period - evaluate other optimization opportunities")
        
        return recommendations
    
    def _perform_pipe_comparison(self, network_data: dict) -> List[PipeSizingComparison]:
        """Perform detailed comparison between fixed and sized pipes."""
        comparisons = []
        fixed_diameter = 0.1  # Default fixed diameter
        
        # Get all pipes from network data
        all_pipes = []
        all_pipes.extend(network_data.get('supply_pipes', []))
        all_pipes.extend(network_data.get('return_pipes', []))
        all_pipes.extend(network_data.get('service_connections', []))
        
        for pipe in all_pipes:
            pipe_id = pipe.get('pipe_id', 'unknown')
            sized_diameter = pipe.get('diameter_m', 0.1)
            length_m = pipe.get('length_m', 100.0)
            pipe_category = pipe.get('pipe_category', 'distribution_pipes')
            
            # Calculate costs
            if self.sizing_engine:
                mapped_category = self._map_pipe_category(pipe_category)
                fixed_cost = self.sizing_engine.calculate_pipe_cost(fixed_diameter, length_m, mapped_category)
                sized_cost = self.sizing_engine.calculate_pipe_cost(sized_diameter, length_m, mapped_category)
            else:
                fixed_cost = self._get_fallback_pipe_cost(fixed_diameter, pipe_category) * length_m
                sized_cost = self._get_fallback_pipe_cost(sized_diameter, pipe_category) * length_m
            
            cost_difference = sized_cost - fixed_cost
            cost_percentage_change = (cost_difference / fixed_cost * 100) if fixed_cost > 0 else 0
            
            # Calculate hydraulic improvement
            hydraulic_improvement = self._calculate_pipe_hydraulic_improvement(pipe, fixed_diameter, sized_diameter)
            
            comparisons.append(PipeSizingComparison(
                pipe_id=pipe_id,
                fixed_diameter_m=fixed_diameter,
                sized_diameter_m=sized_diameter,
                fixed_cost_eur=fixed_cost,
                sized_cost_eur=sized_cost,
                cost_difference_eur=cost_difference,
                cost_percentage_change=cost_percentage_change,
                hydraulic_improvement=hydraulic_improvement
            ))
        
        return comparisons
    
    def _calculate_economic_impact(self, sizing_impact: dict) -> EconomicImpactAnalysis:
        """Calculate comprehensive economic impact."""
        capex_impact = sizing_impact['capex_impact']
        opex_impact = sizing_impact['opex_impact']
        economic_metrics = sizing_impact['economic_metrics']
        
        return EconomicImpactAnalysis(
            total_capex_impact_eur=capex_impact['cost_difference_eur'],
            total_opex_impact_eur=opex_impact['lifetime_opex_impact_eur'],
            total_hydraulic_benefit_eur=0.0,  # Placeholder for hydraulic benefits
            net_benefit_eur=economic_metrics['net_benefit_eur'],
            payback_period_years=economic_metrics['payback_period_years'],
            net_present_value_eur=economic_metrics['net_present_value_eur'],
            internal_rate_of_return=economic_metrics['internal_rate_of_return'],
            benefit_cost_ratio=economic_metrics['benefit_cost_ratio']
        )
    
    def _generate_analysis_summary(self, sizing_impact: dict, economic_impact: EconomicImpactAnalysis) -> Dict[str, Any]:
        """Generate comprehensive analysis summary."""
        return {
            'analysis_type': 'comprehensive_cost_benefit',
            'total_capex_impact_eur': economic_impact.total_capex_impact_eur,
            'total_opex_impact_eur': economic_impact.total_opex_impact_eur,
            'net_benefit_eur': economic_impact.net_benefit_eur,
            'payback_period_years': economic_impact.payback_period_years,
            'economic_viability': sizing_impact['economic_metrics']['economic_viability'],
            'recommendation_count': len(sizing_impact['recommendations']),
            'analysis_timestamp': pd.Timestamp.now().isoformat()
        }
    
    # Helper methods
    def _map_pipe_category(self, pipe_category: str) -> str:
        """Map pipe category from network data format to sizing engine format."""
        category_mapping = {
            'service_connections': 'service_connection',
            'distribution_pipes': 'distribution_pipe',
            'main_pipes': 'main_pipe',
            'service_connection': 'service_connection',
            'distribution_pipe': 'distribution_pipe',
            'main_pipe': 'main_pipe'
        }
        return category_mapping.get(pipe_category, 'distribution_pipe')
    
    def _get_fallback_pipe_cost(self, diameter_m: float, pipe_category: str) -> float:
        """Get fallback pipe cost when sizing engine is not available."""
        if diameter_m < 0.10:
            return 450.0
        elif diameter_m < 0.20:
            return 600.0
        else:
            return 800.0
    
    def _analyze_capex_by_category(self, network_data: dict) -> Dict[str, Any]:
        """Analyze CAPEX impact by pipe category."""
        category_analysis = {}
        
        for category in ['service_connections', 'distribution_pipes', 'main_pipes']:
            pipes = network_data.get(category, [])
            if pipes:
                fixed_cost = sum(self._get_fallback_pipe_cost(0.1, category) * pipe.get('length_m', 100) for pipe in pipes)
                sized_cost = sum(self._get_fallback_pipe_cost(pipe.get('diameter_m', 0.1), category) * pipe.get('length_m', 100) for pipe in pipes)
                
                category_analysis[category] = {
                    'pipe_count': len(pipes),
                    'fixed_cost_eur': fixed_cost,
                    'sized_cost_eur': sized_cost,
                    'cost_difference_eur': sized_cost - fixed_cost,
                    'cost_percentage_change': ((sized_cost - fixed_cost) / fixed_cost * 100) if fixed_cost > 0 else 0
                }
        
        return category_analysis
    
    def _calculate_pump_energy_fixed(self, network_data: dict) -> float:
        """Calculate pump energy for fixed diameter network."""
        # Simplified calculation - in practice, this would use hydraulic simulation
        total_length = sum(pipe.get('length_m', 100) for pipe in 
                          network_data.get('supply_pipes', []) + 
                          network_data.get('return_pipes', []))
        return total_length * 0.5  # Simplified energy calculation
    
    def _calculate_pump_energy_sized(self, network_data: dict) -> float:
        """Calculate pump energy for sized network."""
        # Use actual pressure drops from sized network
        total_energy = 0.0
        for pipe in network_data.get('supply_pipes', []) + network_data.get('return_pipes', []):
            pressure_drop = pipe.get('pressure_drop_pa_per_m', 1000)
            length_m = pipe.get('length_m', 100)
            flow_rate = pipe.get('aggregated_flow_kg_s', 0.5)
            
            # Simplified energy calculation
            energy = (pressure_drop * length_m * flow_rate) / (1000 * self.pump_efficiency)
            total_energy += energy
        
        return total_energy / 1000  # Convert to kWh
    
    def _calculate_lifetime_opex_impact(self, annual_opex_difference: float) -> float:
        """Calculate lifetime OPEX impact."""
        # Calculate present value of annual OPEX difference over lifetime
        pv_factor = (1 - (1 + self.discount_rate) ** (-self.lifetime_years)) / self.discount_rate
        return annual_opex_difference * pv_factor
    
    def _calculate_payback_period(self, capex_difference: float, annual_opex_difference: float) -> float:
        """Calculate payback period in years."""
        if annual_opex_difference == 0:
            return float('inf')
        return abs(capex_difference / annual_opex_difference)
    
    def _calculate_npv(self, capex_difference: float, annual_opex_difference: float) -> float:
        """Calculate Net Present Value."""
        pv_factor = (1 - (1 + self.discount_rate) ** (-self.lifetime_years)) / self.discount_rate
        return -capex_difference + (annual_opex_difference * pv_factor)
    
    def _calculate_irr(self, capex_difference: float, annual_opex_difference: float) -> float:
        """Calculate Internal Rate of Return (simplified)."""
        if annual_opex_difference == 0:
            return 0.0
        
        # Simplified IRR calculation
        payback_period = self._calculate_payback_period(capex_difference, annual_opex_difference)
        if payback_period == float('inf'):
            return 0.0
        
        # Approximate IRR based on payback period
        return 1.0 / payback_period
    
    def _calculate_benefit_cost_ratio(self, lifetime_benefits: float, capex_difference: float) -> float:
        """Calculate Benefit-Cost Ratio."""
        if capex_difference == 0:
            return float('inf') if lifetime_benefits > 0 else 0.0
        return lifetime_benefits / abs(capex_difference)
    
    def _calculate_hydraulic_metrics(self, network_data: dict) -> Dict[str, Any]:
        """Calculate hydraulic performance metrics."""
        all_pipes = network_data.get('supply_pipes', []) + network_data.get('return_pipes', [])
        
        if not all_pipes:
            return {}
        
        velocities = [pipe.get('velocity_ms', 0) for pipe in all_pipes]
        pressure_drops = [pipe.get('pressure_drop_pa_per_m', 0) for pipe in all_pipes]
        
        return {
            'average_velocity_ms': np.mean(velocities),
            'max_velocity_ms': max(velocities),
            'min_velocity_ms': min(velocities),
            'average_pressure_drop_pa_per_m': np.mean(pressure_drops),
            'max_pressure_drop_pa_per_m': max(pressure_drops),
            'min_pressure_drop_pa_per_m': min(pressure_drops)
        }
    
    def _calculate_efficiency_improvements(self, network_data: dict) -> Dict[str, Any]:
        """Calculate efficiency improvements from sizing."""
        # Simplified efficiency calculation
        hydraulic_metrics = self._calculate_hydraulic_metrics(network_data)
        
        # Calculate efficiency based on velocity and pressure drop
        avg_velocity = hydraulic_metrics.get('average_velocity_ms', 0)
        avg_pressure_drop = hydraulic_metrics.get('average_pressure_drop_pa_per_m', 0)
        
        # Simple efficiency metric (higher velocity, lower pressure drop = better efficiency)
        efficiency_score = avg_velocity / max(avg_pressure_drop / 1000, 1e-6)
        
        return {
            'efficiency_score': efficiency_score,
            'overall_efficiency_gain': efficiency_score - 1.0,  # Compared to baseline
            'velocity_optimization': 'optimal' if 1.0 <= avg_velocity <= 2.0 else 'suboptimal',
            'pressure_optimization': 'optimal' if avg_pressure_drop <= 3000 else 'suboptimal'
        }
    
    def _calculate_reliability_improvements(self, network_data: dict) -> Dict[str, Any]:
        """Calculate reliability improvements from sizing."""
        # Simplified reliability calculation
        hydraulic_metrics = self._calculate_hydraulic_metrics(network_data)
        
        # Calculate reliability based on velocity and pressure drop constraints
        avg_velocity = hydraulic_metrics.get('average_velocity_ms', 0)
        avg_pressure_drop = hydraulic_metrics.get('average_pressure_drop_pa_per_m', 0)
        
        # Reliability score based on constraint compliance
        velocity_reliability = 1.0 if 0.5 <= avg_velocity <= 3.0 else 0.5
        pressure_reliability = 1.0 if avg_pressure_drop <= 5000 else 0.5
        
        overall_reliability = (velocity_reliability + pressure_reliability) / 2
        
        return {
            'overall_reliability': overall_reliability,
            'velocity_reliability': velocity_reliability,
            'pressure_reliability': pressure_reliability,
            'reliability_improvement': overall_reliability - 0.8  # Compared to baseline
        }
    
    def _calculate_pipe_hydraulic_improvement(self, pipe: dict, fixed_diameter: float, sized_diameter: float) -> Dict[str, Any]:
        """Calculate hydraulic improvement for a specific pipe."""
        # Simplified hydraulic improvement calculation
        velocity = pipe.get('velocity_ms', 0)
        pressure_drop = pipe.get('pressure_drop_pa_per_m', 0)
        
        return {
            'velocity_ms': velocity,
            'pressure_drop_pa_per_m': pressure_drop,
            'hydraulic_efficiency': velocity / max(pressure_drop / 1000, 1e-6),
            'constraint_compliance': 'compliant' if 0.5 <= velocity <= 3.0 and pressure_drop <= 5000 else 'non_compliant'
        }
    
    def export_cost_benefit_analysis(self, result: CostBenefitResult, output_path: str) -> None:
        """Export cost-benefit analysis to JSON file."""
        export_data = {
            'capex_impact': result.capex_impact,
            'opex_impact': result.opex_impact,
            'hydraulic_improvement': result.hydraulic_improvement,
            'economic_metrics': result.economic_metrics,
            'recommendations': result.recommendations,
            'summary': result.summary
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Cost-benefit analysis exported to {output_path}")
    
    def print_cost_benefit_summary(self, result: CostBenefitResult) -> None:
        """Print comprehensive cost-benefit analysis summary."""
        print(f"\n💰 COST-BENEFIT ANALYSIS SUMMARY")
        print(f"=" * 50)
        
        print(f"📊 CAPEX IMPACT:")
        capex = result.capex_impact
        print(f"   Fixed Cost: €{capex['fixed_cost_eur']:.0f}")
        print(f"   Sized Cost: €{capex['sized_cost_eur']:.0f}")
        print(f"   Cost Difference: €{capex['cost_difference_eur']:.0f}")
        print(f"   Percentage Change: {capex['cost_percentage_change']:.1f}%")
        print(f"   Cost Effectiveness: {capex['cost_effectiveness']}")
        
        print(f"")
        print(f"⚡ OPEX IMPACT:")
        opex = result.opex_impact
        print(f"   Fixed Pump Energy: {opex['fixed_pump_energy_kwh']:.0f} kWh")
        print(f"   Sized Pump Energy: {opex['sized_pump_energy_kwh']:.0f} kWh")
        print(f"   Annual OPEX Difference: €{opex['annual_opex_difference_eur']:.0f}")
        print(f"   Lifetime OPEX Impact: €{opex['lifetime_opex_impact_eur']:.0f}")
        print(f"   OPEX Improvement: {opex['opex_improvement']}")
        
        print(f"")
        print(f"🌊 HYDRAULIC IMPROVEMENT:")
        hydraulic = result.hydraulic_improvement
        print(f"   Overall Improvement: {hydraulic['overall_improvement']}")
        if 'efficiency_improvements' in hydraulic:
            eff = hydraulic['efficiency_improvements']
            print(f"   Efficiency Score: {eff.get('efficiency_score', 0):.3f}")
            print(f"   Overall Efficiency Gain: {eff.get('overall_efficiency_gain', 0):.3f}")
        
        print(f"")
        print(f"📈 ECONOMIC METRICS:")
        economic = result.economic_metrics
        print(f"   Net Benefit: €{economic['net_benefit_eur']:.0f}")
        print(f"   Payback Period: {economic['payback_period_years']:.1f} years")
        print(f"   Net Present Value: €{economic['net_present_value_eur']:.0f}")
        print(f"   Internal Rate of Return: {economic['internal_rate_of_return']:.1%}")
        print(f"   Benefit-Cost Ratio: {economic['benefit_cost_ratio']:.2f}")
        print(f"   Economic Viability: {economic['economic_viability']}")
        
        print(f"")
        print(f"💡 RECOMMENDATIONS:")
        for i, recommendation in enumerate(result.recommendations, 1):
            print(f"   {i}. {recommendation}")


# Example usage and testing
if __name__ == "__main__":
    # Create pipe sizing engine
    from cha_pipe_sizing import CHAPipeSizingEngine
    
    sizing_engine = CHAPipeSizingEngine({
        'max_velocity_ms': 2.0,
        'min_velocity_ms': 0.1,
        'max_pressure_drop_pa_per_m': 5000,
        'pipe_roughness_mm': 0.1
    })
    
    # Create cost-benefit analyzer
    analyzer = CHACostBenefitAnalyzer(sizing_engine)
    
    # Example network data
    network_data = {
        'supply_pipes': [
            {
                'pipe_id': 'supply_1',
                'diameter_m': 0.1,
                'length_m': 100,
                'aggregated_flow_kg_s': 0.5,
                'pressure_drop_pa_per_m': 1000,
                'velocity_ms': 1.5,
                'pipe_category': 'distribution_pipes'
            }
        ],
        'return_pipes': [
            {
                'pipe_id': 'return_1',
                'diameter_m': 0.1,
                'length_m': 100,
                'aggregated_flow_kg_s': 0.5,
                'pressure_drop_pa_per_m': 1000,
                'velocity_ms': 1.5,
                'pipe_category': 'distribution_pipes'
            }
        ],
        'service_connections': [
            {
                'pipe_id': 'service_1',
                'diameter_m': 0.05,
                'length_m': 10,
                'aggregated_flow_kg_s': 0.1,
                'pressure_drop_pa_per_m': 2000,
                'velocity_ms': 1.0,
                'pipe_category': 'service_connections'
            }
        ]
    }
    
    try:
        # Test cost-benefit analyzer
        print(f"🧪 Testing cost-benefit analyzer...")
        
        # Perform comprehensive analysis
        result = analyzer.analyze_comprehensive_cost_benefit(network_data)
        
        # Print summary
        analyzer.print_cost_benefit_summary(result)
        
        # Export results
        analyzer.export_cost_benefit_analysis(result, "cost_benefit_analysis.json")
        
        print(f"\n🎉 Cost-benefit analyzer testing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in cost-benefit analyzer: {e}")
        import traceback
        traceback.print_exc()
