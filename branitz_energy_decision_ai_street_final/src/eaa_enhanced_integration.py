"""
Enhanced EAA Integration - Intelligent Pipe Sizing Integration

This module enhances the Economics Analysis Agent (EAA) to integrate with the
intelligent pipe sizing system for more accurate economic calculations.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

from __future__ import annotations
import json
import math
import os
import glob
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

# Import our enhanced components
from cha_pipe_sizing import CHAPipeSizingEngine
from cha_enhanced_config_loader import CHAEnhancedConfigLoader
from cha_enhanced_pandapipes import CHAEnhancedPandapipesSimulator

@dataclass
class EnhancedEAAConfig:
    """Enhanced EAA configuration with pipe sizing integration."""
    # Basic EAA parameters
    n_samples: int = 1000
    seed: int = 42
    cp_water_j_per_kgk: float = 4180
    delta_t_k: float = 30
    design_full_load_hours: float = 2000
    discount_rate: float = 0.06
    lifetime_years: int = 25
    pump_efficiency: float = 0.75
    elec_price_eur_per_kwh: float = 0.22
    grid_co2_kg_per_kwh: float = 0.35
    opex_fraction_of_capex: float = 0.02
    om_fixed_eur_per_mwh: float = 4.0
    annual_heat_mwh_fallback: float = 10000.0
    
    # Enhanced pipe sizing integration
    enable_intelligent_sizing: bool = True
    sizing_engine_config: Dict[str, Any] = field(default_factory=dict)
    cost_optimization_enabled: bool = True
    detailed_cost_breakdown: bool = True
    
    # Paths
    paths: Dict[str, str] = field(default_factory=dict)


@dataclass
class PipeCostBreakdown:
    """Detailed pipe cost breakdown."""
    pipe_id: str
    diameter_m: float
    diameter_nominal: str
    length_m: float
    cost_per_m_eur: float
    total_cost_eur: float
    pipe_category: str
    material_cost_eur: float
    installation_cost_eur: float
    insulation_cost_eur: float


@dataclass
class EnhancedEconomicResult:
    """Enhanced economic analysis result."""
    # Basic economic metrics
    lcoh_eur_per_mwh: float
    co2_kg_per_mwh: float
    annual_pumping_kwh: float
    annual_heat_mwh: float
    
    # Enhanced pipe sizing metrics
    total_pipe_capex_eur: float
    total_pump_power_kw: float
    sizing_accuracy_rate: float
    cost_optimization_savings_eur: float
    
    # Detailed breakdowns
    pipe_cost_breakdown: List[PipeCostBreakdown]
    cost_optimization_analysis: Dict[str, Any]
    
    # Monte Carlo results
    mc_results: pd.DataFrame
    summary_statistics: pd.DataFrame


class EnhancedEAAIntegration:
    """
    Enhanced EAA integration with intelligent pipe sizing system.
    
    Provides more accurate economic calculations by integrating with the
    intelligent pipe sizing system for proper cost calculations and
    optimization analysis.
    """
    
    def __init__(self, config: EnhancedEAAConfig, 
                 sizing_engine: Optional[CHAPipeSizingEngine] = None,
                 config_loader: Optional[CHAEnhancedConfigLoader] = None):
        """
        Initialize enhanced EAA integration.
        
        Args:
            config: Enhanced EAA configuration
            sizing_engine: CHA pipe sizing engine instance
            config_loader: Enhanced configuration loader instance
        """
        self.config = config
        self.sizing_engine = sizing_engine
        self.config_loader = config_loader
        
        # Initialize sizing engine if not provided
        if not self.sizing_engine and config.enable_intelligent_sizing:
            sizing_config = config.sizing_engine_config or {
                'max_velocity_ms': 2.0,
                'min_velocity_ms': 0.1,
                'max_pressure_drop_pa_per_m': 5000,
                'pipe_roughness_mm': 0.1
            }
            self.sizing_engine = CHAPipeSizingEngine(sizing_config)
        
        print(f"✅ Enhanced EAA Integration initialized")
        print(f"   Intelligent sizing: {config.enable_intelligent_sizing}")
        print(f"   Cost optimization: {config.cost_optimization_enabled}")
        print(f"   Detailed breakdown: {config.detailed_cost_breakdown}")
    
    def calculate_pipe_capex_with_sizing(self, network_data: dict) -> float:
        """
        Calculate pipe capital costs with proper sizing.
        
        Args:
            network_data: Network data with pipe information
        
        Returns:
            total_cost: Total pipe capital cost in EUR
        """
        print(f"💰 Calculating pipe CAPEX with intelligent sizing...")
        
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
            
            # Get cost from sizing engine if available
            if self.sizing_engine:
                # Map pipe category to sizing engine format
                mapped_category = self._map_pipe_category(pipe_category)
                cost_per_m = self.sizing_engine.calculate_pipe_cost(
                    diameter_m, length_m, mapped_category
                ) / length_m  # Convert total cost to per-meter cost
            else:
                # Fallback to simple cost model
                cost_per_m = self._get_fallback_pipe_cost(diameter_m, pipe_category)
            
            pipe_cost = cost_per_m * length_m
            total_cost += pipe_cost
            
            print(f"   Pipe {pipe.get('pipe_id', 'unknown')}: {diameter_m*1000:.0f}mm, {length_m:.1f}m, €{pipe_cost:.0f}")
        
        print(f"✅ Total pipe CAPEX: €{total_cost:.0f}")
        return total_cost
    
    def calculate_pump_energy_with_sizing(self, network_data: dict) -> float:
        """
        Calculate pump energy with sized pipes.
        
        Args:
            network_data: Network data with pipe information
        
        Returns:
            pump_power_w: Total pump power in watts
        """
        print(f"⚡ Calculating pump energy with sized pipes...")
        
        # Use actual pressure drops from sized network
        total_pressure_drop_pa = 0.0
        total_flow_rate_kg_s = 0.0
        
        # Get all pipes from network data
        all_pipes = []
        all_pipes.extend(network_data.get('supply_pipes', []))
        all_pipes.extend(network_data.get('return_pipes', []))
        
        for pipe in all_pipes:
            # Get pressure drop and flow rate
            pressure_drop_pa_per_m = pipe.get('pressure_drop_pa_per_m', 0.0)
            length_m = pipe.get('length_m', 100.0)
            flow_rate_kg_s = pipe.get('aggregated_flow_kg_s', 0.0)
            
            # Calculate total pressure drop for this pipe
            pipe_pressure_drop_pa = pressure_drop_pa_per_m * length_m
            
            total_pressure_drop_pa += pipe_pressure_drop_pa
            total_flow_rate_kg_s += flow_rate_kg_s
        
        # Calculate pump power
        if total_flow_rate_kg_s > 0:
            # Convert flow rate from kg/s to m³/s (assuming water density ~1000 kg/m³)
            flow_rate_m3s = total_flow_rate_kg_s / 1000.0
            
            # Calculate hydraulic power
            hydraulic_power_w = total_pressure_drop_pa * flow_rate_m3s
            
            # Calculate pump power with efficiency
            pump_power_w = hydraulic_power_w / max(self.config.pump_efficiency, 1e-6)
        else:
            pump_power_w = 0.0
        
        print(f"✅ Total pump power: {pump_power_w/1000:.1f} kW")
        return pump_power_w
    
    def generate_enhanced_kpis(self, network_data: dict, 
                             pipe_capex: float, pump_power: float) -> Dict[str, Any]:
        """
        Generate enhanced KPIs with sizing data.
        
        Args:
            network_data: Network data with pipe information
            pipe_capex: Total pipe capital cost
            pump_power: Total pump power
        
        Returns:
            enhanced_kpis: Enhanced KPI dictionary
        """
        print(f"📊 Generating enhanced KPIs with sizing data...")
        
        # Calculate sizing accuracy
        sizing_accuracy = self._calculate_sizing_accuracy(network_data)
        
        # Calculate cost optimization potential
        cost_optimization = self._calculate_cost_optimization(network_data, pipe_capex)
        
        # Calculate network efficiency metrics
        network_efficiency = self._calculate_network_efficiency(network_data, pump_power)
        
        enhanced_kpis = {
            'sizing_accuracy': sizing_accuracy,
            'cost_optimization': cost_optimization,
            'network_efficiency': network_efficiency,
            'pipe_capex_eur': pipe_capex,
            'pump_power_kw': pump_power / 1000.0,
            'total_network_length_m': sum(pipe.get('length_m', 0) for pipe in 
                                        network_data.get('supply_pipes', []) + 
                                        network_data.get('return_pipes', [])),
            'average_pipe_diameter_mm': np.mean([pipe.get('diameter_m', 0.1) * 1000 
                                               for pipe in network_data.get('supply_pipes', []) + 
                                               network_data.get('return_pipes', [])]),
            'pipe_count': len(network_data.get('supply_pipes', []) + 
                            network_data.get('return_pipes', []))
        }
        
        print(f"✅ Enhanced KPIs generated")
        return enhanced_kpis
    
    def run_enhanced_analysis(self, network_data: dict, 
                            cha_csv_path: str = "processed/cha/segments.csv",
                            dha_csv_path: str = "processed/dha/feeder_loads.csv",
                            lfa_dir: str = "processed/lfa") -> EnhancedEconomicResult:
        """
        Run enhanced economic analysis with intelligent pipe sizing.
        
        Args:
            network_data: Network data with pipe information
            cha_csv_path: Path to CHA segments CSV
            dha_csv_path: Path to DHA feeder loads CSV
            lfa_dir: Path to LFA directory
        
        Returns:
            result: Enhanced economic analysis result
        """
        print(f"🧮 Running enhanced economic analysis...")
        
        # Calculate pipe CAPEX with intelligent sizing
        pipe_capex = self.calculate_pipe_capex_with_sizing(network_data)
        
        # Calculate pump energy with sized pipes
        pump_power = self.calculate_pump_energy_with_sizing(network_data)
        
        # Generate enhanced KPIs
        enhanced_kpis = self.generate_enhanced_kpis(network_data, pipe_capex, pump_power)
        
        # Load existing data for Monte Carlo analysis
        df_cha = pd.read_csv(cha_csv_path) if Path(cha_csv_path).exists() else pd.DataFrame()
        df_dha = pd.read_csv(dha_csv_path) if Path(dha_csv_path).exists() else pd.DataFrame()
        
        # Calculate annual heat demand
        annual_heat_mwh = self._calculate_annual_heat_demand(lfa_dir)
        
        # Run Monte Carlo analysis
        mc_results, summary_stats = self._run_monte_carlo_analysis(
            pipe_capex, pump_power, annual_heat_mwh
        )
        
        # Generate detailed cost breakdown
        pipe_cost_breakdown = self._generate_pipe_cost_breakdown(network_data)
        
        # Generate cost optimization analysis
        cost_optimization_analysis = self._generate_cost_optimization_analysis(
            network_data, pipe_capex
        )
        
        result = EnhancedEconomicResult(
            lcoh_eur_per_mwh=float(summary_stats.loc[0, 'mean']),
            co2_kg_per_mwh=float(summary_stats.loc[1, 'mean']),
            annual_pumping_kwh=(pump_power / 1000.0) * self.config.design_full_load_hours,
            annual_heat_mwh=annual_heat_mwh,
            total_pipe_capex_eur=pipe_capex,
            total_pump_power_kw=pump_power / 1000.0,
            sizing_accuracy_rate=enhanced_kpis['sizing_accuracy']['accuracy_rate'],
            cost_optimization_savings_eur=cost_optimization_analysis.get('potential_savings', 0.0),
            pipe_cost_breakdown=pipe_cost_breakdown,
            cost_optimization_analysis=cost_optimization_analysis,
            mc_results=mc_results,
            summary_statistics=summary_stats
        )
        
        print(f"✅ Enhanced economic analysis completed")
        return result
    
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
        # Simple cost model based on diameter
        if diameter_m < 0.10:
            return 450.0
        elif diameter_m < 0.20:
            return 600.0
        else:
            return 800.0
    
    def _calculate_sizing_accuracy(self, network_data: dict) -> Dict[str, Any]:
        """Calculate sizing accuracy metrics."""
        all_pipes = []
        all_pipes.extend(network_data.get('supply_pipes', []))
        all_pipes.extend(network_data.get('return_pipes', []))
        
        properly_sized = 0
        undersized = 0
        oversized = 0
        
        for pipe in all_pipes:
            velocity = pipe.get('velocity_ms', 0.0)
            max_velocity = 2.0  # Default constraint
            min_velocity = 0.5  # Default constraint
            
            if min_velocity <= velocity <= max_velocity:
                properly_sized += 1
            elif velocity > max_velocity:
                oversized += 1
            else:
                undersized += 1
        
        total_pipes = len(all_pipes)
        accuracy_rate = properly_sized / total_pipes if total_pipes > 0 else 0.0
        
        return {
            'total_pipes': total_pipes,
            'properly_sized': properly_sized,
            'undersized': undersized,
            'oversized': oversized,
            'accuracy_rate': accuracy_rate
        }
    
    def _calculate_cost_optimization(self, network_data: dict, current_capex: float) -> Dict[str, Any]:
        """Calculate cost optimization potential."""
        # Simple optimization analysis
        all_pipes = []
        all_pipes.extend(network_data.get('supply_pipes', []))
        all_pipes.extend(network_data.get('return_pipes', []))
        
        # Calculate potential savings from diameter optimization
        potential_savings = 0.0
        optimization_recommendations = []
        
        for pipe in all_pipes:
            diameter_m = pipe.get('diameter_m', 0.1)
            length_m = pipe.get('length_m', 100.0)
            velocity = pipe.get('velocity_ms', 0.0)
            
            # If velocity is too low, we could use a smaller diameter
            if velocity < 0.5:
                # Estimate 20% cost reduction for smaller diameter
                current_cost = self._get_fallback_pipe_cost(diameter_m, 'distribution_pipes') * length_m
                potential_savings += current_cost * 0.2
                optimization_recommendations.append(
                    f"Pipe {pipe.get('pipe_id', 'unknown')}: Consider smaller diameter for cost optimization"
                )
        
        return {
            'potential_savings': potential_savings,
            'savings_percentage': (potential_savings / current_capex * 100) if current_capex > 0 else 0.0,
            'recommendations': optimization_recommendations
        }
    
    def _calculate_network_efficiency(self, network_data: dict, pump_power: float) -> Dict[str, Any]:
        """Calculate network efficiency metrics."""
        all_pipes = []
        all_pipes.extend(network_data.get('supply_pipes', []))
        all_pipes.extend(network_data.get('return_pipes', []))
        
        total_length = sum(pipe.get('length_m', 0) for pipe in all_pipes)
        total_flow = sum(pipe.get('aggregated_flow_kg_s', 0) for pipe in all_pipes)
        
        # Calculate efficiency metrics
        power_per_meter = pump_power / total_length if total_length > 0 else 0.0
        power_per_flow = pump_power / total_flow if total_flow > 0 else 0.0
        
        return {
            'total_length_m': total_length,
            'total_flow_kg_s': total_flow,
            'power_per_meter_w_per_m': power_per_meter,
            'power_per_flow_w_per_kg_s': power_per_flow,
            'network_efficiency': 1.0 / (1.0 + power_per_flow / 1000.0)  # Simple efficiency metric
        }
    
    def _calculate_annual_heat_demand(self, lfa_dir: str) -> float:
        """Calculate annual heat demand from LFA data."""
        files = sorted(glob.glob(os.path.join(lfa_dir, "*.json")))
        if not files:
            return self.config.annual_heat_mwh_fallback
        
        total_kwh = 0.0
        for f in files:
            try:
                data = json.loads(Path(f).read_text())
                series = data.get("series") or []
                total_kwh += float(np.nansum(series))
            except Exception:
                continue
        
        return total_kwh / 1000.0  # Convert to MWh
    
    def _run_monte_carlo_analysis(self, pipe_capex: float, pump_power: float, 
                                annual_heat_mwh: float) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Run Monte Carlo analysis for economic uncertainty."""
        np.random.seed(self.config.seed)
        n = int(self.config.n_samples)
        
        # Sample multipliers
        capex_mult = np.random.lognormal(mean=0.0, sigma=0.15, size=n)
        elec_price = np.random.lognormal(mean=np.log(self.config.elec_price_eur_per_kwh), sigma=0.10, size=n)
        grid_ci = np.random.lognormal(mean=np.log(self.config.grid_co2_kg_per_kwh), sigma=0.10, size=n)
        
        # Calculate annuity factor
        ann_fac = (self.config.discount_rate * (1 + self.config.discount_rate) ** self.config.lifetime_years) / \
                 (((1 + self.config.discount_rate) ** self.config.lifetime_years) - 1)
        
        # Calculate costs
        ann_capex = pipe_capex * ann_fac * capex_mult
        annual_pumping_kwh = (pump_power / 1000.0) * self.config.design_full_load_hours
        pumping_cost = annual_pumping_kwh * elec_price
        opex_fixed = pipe_capex * self.config.opex_fraction_of_capex + \
                    (self.config.om_fixed_eur_per_mwh * annual_heat_mwh)
        
        # Calculate LCoH and CO2
        lcoh_eur_per_mwh = (ann_capex + pumping_cost + opex_fixed) / max(annual_heat_mwh, 1e-9)
        co2_kg_per_mwh = (annual_pumping_kwh * grid_ci) / max(annual_heat_mwh, 1e-9)
        
        # Create Monte Carlo results
        mc_results = pd.DataFrame({
            "lcoh_eur_per_mwh": lcoh_eur_per_mwh,
            "co2_kg_per_mwh": co2_kg_per_mwh,
        })
        
        # Create summary statistics
        def p(x, q): return float(np.percentile(x, q))
        summary_stats = pd.DataFrame({
            "metric": ["lcoh_eur_per_mwh", "co2_kg_per_mwh"],
            "mean": [float(np.mean(lcoh_eur_per_mwh)), float(np.mean(co2_kg_per_mwh))],
            "median": [float(np.median(lcoh_eur_per_mwh)), float(np.median(co2_kg_per_mwh))],
            "p2_5": [p(lcoh_eur_per_mwh, 2.5), p(co2_kg_per_mwh, 2.5)],
            "p97_5": [p(lcoh_eur_per_mwh, 97.5), p(co2_kg_per_mwh, 97.5)],
            "annual_pumping_kwh": [annual_pumping_kwh, annual_pumping_kwh],
            "annual_heat_mwh": [annual_heat_mwh, annual_heat_mwh]
        })
        
        return mc_results, summary_stats
    
    def _generate_pipe_cost_breakdown(self, network_data: dict) -> List[PipeCostBreakdown]:
        """Generate detailed pipe cost breakdown."""
        breakdown = []
        
        all_pipes = []
        all_pipes.extend(network_data.get('supply_pipes', []))
        all_pipes.extend(network_data.get('return_pipes', []))
        all_pipes.extend(network_data.get('service_connections', []))
        
        for pipe in all_pipes:
            diameter_m = pipe.get('diameter_m', 0.1)
            length_m = pipe.get('length_m', 100.0)
            pipe_category = pipe.get('pipe_category', 'distribution_pipes')
            
            # Calculate costs
            if self.sizing_engine:
                mapped_category = self._map_pipe_category(pipe_category)
                total_cost = self.sizing_engine.calculate_pipe_cost(diameter_m, length_m, mapped_category)
                cost_per_m = total_cost / length_m
            else:
                cost_per_m = self._get_fallback_pipe_cost(diameter_m, pipe_category)
                total_cost = cost_per_m * length_m
            
            # Estimate cost breakdown (simplified)
            material_cost = total_cost * 0.6
            installation_cost = total_cost * 0.3
            insulation_cost = total_cost * 0.1
            
            breakdown.append(PipeCostBreakdown(
                pipe_id=pipe.get('pipe_id', 'unknown'),
                diameter_m=diameter_m,
                diameter_nominal=f"DN {int(diameter_m * 1000)}",
                length_m=length_m,
                cost_per_m_eur=cost_per_m,
                total_cost_eur=total_cost,
                pipe_category=pipe_category,
                material_cost_eur=material_cost,
                installation_cost_eur=installation_cost,
                insulation_cost_eur=insulation_cost
            ))
        
        return breakdown
    
    def _generate_cost_optimization_analysis(self, network_data: dict, current_capex: float) -> Dict[str, Any]:
        """Generate cost optimization analysis."""
        optimization = self._calculate_cost_optimization(network_data, current_capex)
        
        return {
            'current_capex_eur': current_capex,
            'potential_savings_eur': optimization['potential_savings'],
            'savings_percentage': optimization['savings_percentage'],
            'optimization_recommendations': optimization['recommendations'],
            'optimization_feasibility': 'high' if optimization['savings_percentage'] > 10 else 'medium' if optimization['savings_percentage'] > 5 else 'low'
        }
    
    def export_enhanced_results(self, result: EnhancedEconomicResult, output_path: str) -> None:
        """Export enhanced economic results to JSON file."""
        export_data = {
            'basic_metrics': {
                'lcoh_eur_per_mwh': result.lcoh_eur_per_mwh,
                'co2_kg_per_mwh': result.co2_kg_per_mwh,
                'annual_pumping_kwh': result.annual_pumping_kwh,
                'annual_heat_mwh': result.annual_heat_mwh
            },
            'enhanced_metrics': {
                'total_pipe_capex_eur': result.total_pipe_capex_eur,
                'total_pump_power_kw': result.total_pump_power_kw,
                'sizing_accuracy_rate': result.sizing_accuracy_rate,
                'cost_optimization_savings_eur': result.cost_optimization_savings_eur
            },
            'pipe_cost_breakdown': [
                {
                    'pipe_id': pipe.pipe_id,
                    'diameter_mm': pipe.diameter_m * 1000,
                    'diameter_nominal': pipe.diameter_nominal,
                    'length_m': pipe.length_m,
                    'cost_per_m_eur': pipe.cost_per_m_eur,
                    'total_cost_eur': pipe.total_cost_eur,
                    'pipe_category': pipe.pipe_category,
                    'material_cost_eur': pipe.material_cost_eur,
                    'installation_cost_eur': pipe.installation_cost_eur,
                    'insulation_cost_eur': pipe.insulation_cost_eur
                }
                for pipe in result.pipe_cost_breakdown
            ],
            'cost_optimization_analysis': result.cost_optimization_analysis,
            'monte_carlo_summary': result.summary_statistics.to_dict('records')
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Enhanced economic results exported to {output_path}")
    
    def print_enhanced_summary(self, result: EnhancedEconomicResult) -> None:
        """Print enhanced economic analysis summary."""
        print(f"\n💰 ENHANCED ECONOMIC ANALYSIS SUMMARY")
        print(f"=" * 50)
        
        print(f"📊 BASIC METRICS:")
        print(f"   LCoH: €{result.lcoh_eur_per_mwh:.2f}/MWh")
        print(f"   CO2: {result.co2_kg_per_mwh:.2f} kg/MWh")
        print(f"   Annual Pumping: {result.annual_pumping_kwh:.0f} kWh")
        print(f"   Annual Heat: {result.annual_heat_mwh:.0f} MWh")
        
        print(f"")
        print(f"🏗️ ENHANCED METRICS:")
        print(f"   Pipe CAPEX: €{result.total_pipe_capex_eur:.0f}")
        print(f"   Pump Power: {result.total_pump_power_kw:.1f} kW")
        print(f"   Sizing Accuracy: {result.sizing_accuracy_rate:.1%}")
        print(f"   Cost Optimization Savings: €{result.cost_optimization_savings_eur:.0f}")
        
        print(f"")
        print(f"📋 PIPE COST BREAKDOWN:")
        for pipe in result.pipe_cost_breakdown[:5]:  # Show first 5
            print(f"   {pipe.pipe_id}: {pipe.diameter_nominal}, {pipe.length_m:.1f}m, €{pipe.total_cost_eur:.0f}")
        if len(result.pipe_cost_breakdown) > 5:
            print(f"   ... and {len(result.pipe_cost_breakdown) - 5} more pipes")
        
        print(f"")
        print(f"💡 COST OPTIMIZATION:")
        opt_analysis = result.cost_optimization_analysis
        print(f"   Potential Savings: €{opt_analysis.get('potential_savings_eur', 0):.0f}")
        print(f"   Savings Percentage: {opt_analysis.get('savings_percentage', 0):.1f}%")
        print(f"   Feasibility: {opt_analysis.get('optimization_feasibility', 'unknown')}")


# Example usage and testing
if __name__ == "__main__":
    # Create enhanced EAA configuration
    config = EnhancedEAAConfig(
        enable_intelligent_sizing=True,
        cost_optimization_enabled=True,
        detailed_cost_breakdown=True
    )
    
    # Create pipe sizing engine
    from cha_pipe_sizing import CHAPipeSizingEngine
    sizing_engine = CHAPipeSizingEngine({
        'max_velocity_ms': 2.0,
        'min_velocity_ms': 0.1,
        'max_pressure_drop_pa_per_m': 5000,
        'pipe_roughness_mm': 0.1
    })
    
    # Create enhanced EAA integration
    enhanced_eaa = EnhancedEAAIntegration(config, sizing_engine)
    
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
        # Test enhanced EAA integration
        print(f"🧪 Testing enhanced EAA integration...")
        
        # Run enhanced analysis
        result = enhanced_eaa.run_enhanced_analysis(network_data)
        
        # Print summary
        enhanced_eaa.print_enhanced_summary(result)
        
        # Export results
        enhanced_eaa.export_enhanced_results(result, "enhanced_eaa_results.json")
        
        print(f"\n🎉 Enhanced EAA integration testing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in enhanced EAA integration: {e}")
        import traceback
        traceback.print_exc()
