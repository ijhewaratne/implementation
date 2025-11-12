"""
Enhanced Tools with Physics Models and Pipe Catalog Integration

This module provides enhanced tools for the multi-agent system that integrate:
1. Pipe catalog extraction from Excel files
2. Physics models for fluid dynamics and heat transfer
3. Advanced district heating network analysis
4. Comprehensive optimization capabilities
"""

import json
import os
import subprocess
import sys
import yaml
from adk.api.tool import tool
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.ops import nearest_points
from shapely.geometry import LineString, Point
import networkx as nx
from scipy.spatial import distance_matrix
import pandas as pd
import glob
import numpy as np
import folium
from pathlib import Path
from pyproj import Transformer
import random
import time
from shapely.strtree import STRtree
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import the new physics models and pipe catalog modules
try:
    from optimize.physics_models import (
        reynolds, swamee_jain_f, segment_hydraulics, segment_heat_loss_W,
        PI, G, DEFAULT_EPSILON
    )
    from scripts.build_pipe_catalog import PipeCatalogBuilder
    PHYSICS_AND_CATALOG_AVAILABLE = True
    print("✅ Physics models and pipe catalog modules loaded successfully")
except ImportError as e:
    print(f"⚠️ Warning: Could not import physics models or pipe catalog: {e}")
    PHYSICS_AND_CATALOG_AVAILABLE = False

# Import existing tools
try:
    from simple_enhanced_tools import (
        get_all_street_names, 
        get_building_ids_for_street,
        list_available_results,
        analyze_kpi_report
    )
    EXISTING_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Could not import existing tools: {e}")
    EXISTING_TOOLS_AVAILABLE = False


@tool
def extract_pipe_catalog_from_excel(
    excel_file_path: str = "Technikkatalog_Wärmeplanung_Version_1.1_August24_CC-BY.xlsx",
    config_path: str = "configs/pipe_catalog_mapping.yaml",
    output_path: str = "data/catalogs/pipe_catalog.csv",
    preview_path: str = "data/catalogs/pipe_catalog_preview.json"
) -> str:
    """
    Extract pipe catalog data from Excel file using the robust extraction system.
    
    This tool uses the PipeCatalogBuilder to scan Excel files, detect headers heuristically,
    find columns by keywords, normalize EU/US numbers, and extract pipe data into a standardized schema.
    
    Args:
        excel_file_path: Path to the Excel file containing pipe catalog data
        config_path: Path to YAML configuration file with keyword mappings
        output_path: Path for output CSV file
        preview_path: Path for preview JSON file with metadata
    
    Returns:
        Summary of extraction results including number of records and sheets processed
    """
    if not PHYSICS_AND_CATALOG_AVAILABLE:
        return "❌ Physics models and pipe catalog modules not available"
    
    try:
        # Initialize the pipe catalog builder
        builder = PipeCatalogBuilder(config_path)
        
        # Build the pipe catalog
        result = builder.build_pipe_catalog(
            xlsx_path=excel_file_path,
            output_path=output_path,
            preview_path=preview_path
        )
        
        if result['status'] == 'success':
            summary = f"""
✅ Pipe Catalog Extraction Successful!

📊 Results:
- Total records extracted: {result['records']}
- Sheets processed: {result['sheets_processed']}
- Output file: {result['output_path']}
- Preview file: {preview_path}

📈 Sheet Statistics:
"""
            for sheet, count in result['sheet_statistics'].items():
                if count > 0:
                    summary += f"  • {sheet}: {count} records\n"
            
            summary += f"""
🎯 Available pipe specifications for district heating network optimization!
💡 Use 'analyze_pipe_catalog' to explore the extracted data.
"""
            return summary
        else:
            return f"❌ Extraction failed: {result['status']}"
            
    except Exception as e:
        return f"❌ Error during pipe catalog extraction: {str(e)}"


@tool
def analyze_pipe_catalog(
    catalog_path: str = "data/catalogs/pipe_catalog.csv"
) -> str:
    """
    Analyze the extracted pipe catalog and provide insights for network design.
    
    Args:
        catalog_path: Path to the pipe catalog CSV file
    
    Returns:
        Analysis of available pipe specifications with recommendations
    """
    if not PHYSICS_AND_CATALOG_AVAILABLE:
        return "❌ Physics models and pipe catalog modules not available"
    
    try:
        # Load the pipe catalog
        df = pd.read_csv(catalog_path)
        
        if df.empty:
            return "❌ Pipe catalog is empty or not found"
        
        # Analyze the data
        analysis = f"""
📋 Pipe Catalog Analysis

📊 Dataset Overview:
- Total pipe specifications: {len(df)}
- Available diameters: {sorted(df['dn'].unique())}
- Diameter range: {df['dn'].min()} - {df['dn'].max()} mm
- Cost range: {df['cost_eur_per_m'].min():.0f} - {df['cost_eur_per_m'].max():.0f} €/m

🔧 Technical Specifications:
- Inner diameter range: {df['d_inner_m'].min():.3f} - {df['d_inner_m'].max():.3f} m
- Thermal conductivity range: {df['u_wpermk'].min():.3f} - {df['u_wpermk'].max():.3f} W/mK
- Heat loss range: {df['w_loss_w_per_m'].min():.1f} - {df['w_loss_w_per_m'].max():.1f} W/m

💰 Cost Analysis:
- Average cost: {df['cost_eur_per_m'].mean():.0f} €/m
- Cost per diameter category:
"""
        
        # Cost analysis by diameter
        for dn in sorted(df['dn'].unique()):
            dn_data = df[df['dn'] == dn]
            avg_cost = dn_data['cost_eur_per_m'].mean()
            analysis += f"  • DN{dn}: {avg_cost:.0f} €/m\n"
        
        analysis += f"""
🎯 Recommendations:
- Use DN25-DN100 for distribution networks
- Use DN150-DN400 for transmission networks
- Consider thermal conductivity for insulation selection
- Factor in heat losses for energy efficiency calculations

💡 Next steps: Use 'optimize_district_heating_network' with specific street requirements.
"""
        
        return analysis
        
    except Exception as e:
        return f"❌ Error analyzing pipe catalog: {str(e)}"


@tool
def calculate_pipe_hydraulics(
    flow_rate_m3s: float,
    pipe_diameter_mm: float,
    pipe_length_m: float,
    fluid_density_kgm3: float = 1000.0,
    fluid_viscosity_Pas: float = 0.001,
    pipe_roughness_m: float = None,
    minor_loss_coefficient: float = 0.0
) -> str:
    """
    Calculate hydraulic parameters for a pipe segment using physics models.
    
    Args:
        flow_rate_m3s: Volumetric flow rate [m³/s]
        pipe_diameter_mm: Pipe diameter [mm]
        pipe_length_m: Pipe segment length [m]
        fluid_density_kgm3: Fluid density [kg/m³], defaults to water
        fluid_viscosity_Pas: Dynamic viscosity [Pa·s], defaults to water
        pipe_roughness_m: Pipe roughness [m], defaults to steel
        minor_loss_coefficient: Minor loss coefficient, defaults to 0
    
    Returns:
        Detailed hydraulic analysis results
    """
    if not PHYSICS_AND_CATALOG_AVAILABLE:
        return "❌ Physics models not available"
    
    try:
        # Convert diameter from mm to m
        pipe_diameter_m = pipe_diameter_mm / 1000.0
        
        # Use default roughness if not provided
        if pipe_roughness_m is None:
            pipe_roughness_m = DEFAULT_EPSILON
        
        # Calculate hydraulic parameters
        velocity, pressure_drop, head_loss = segment_hydraulics(
            V_dot=flow_rate_m3s,
            d_inner=pipe_diameter_m,
            L=pipe_length_m,
            rho=fluid_density_kgm3,
            mu=fluid_viscosity_Pas,
            epsilon=pipe_roughness_m,
            K_minor=minor_loss_coefficient
        )
        
        # Calculate Reynolds number
        Re = reynolds(fluid_density_kgm3, velocity, pipe_diameter_m, fluid_viscosity_Pas)
        
        # Determine flow regime
        if Re < 2300:
            flow_regime = "Laminar"
        elif Re < 4000:
            flow_regime = "Transitional"
        else:
            flow_regime = "Turbulent"
        
        results = f"""
🔧 Pipe Hydraulic Analysis

📏 Input Parameters:
- Flow rate: {flow_rate_m3s:.3f} m³/s
- Pipe diameter: {pipe_diameter_mm} mm ({pipe_diameter_m:.3f} m)
- Pipe length: {pipe_length_m} m
- Fluid density: {fluid_density_kgm3} kg/m³
- Fluid viscosity: {fluid_viscosity_Pas} Pa·s
- Pipe roughness: {pipe_roughness_m:.2e} m
- Minor loss coefficient: {minor_loss_coefficient}

📊 Results:
- Flow velocity: {velocity:.3f} m/s
- Reynolds number: {Re:.0f} ({flow_regime} flow)
- Pressure drop: {pressure_drop:.0f} Pa ({pressure_drop/1000:.1f} kPa)
- Head loss: {head_loss:.2f} m

⚡ Energy Considerations:
- Dynamic pressure: {0.5 * fluid_density_kgm3 * velocity**2:.0f} Pa
- Friction factor: {swamee_jain_f(pipe_roughness_m, pipe_diameter_m, Re):.4f}

💡 Recommendations:
- Ensure pressure drop is within acceptable limits
- Consider pump requirements for head loss
- Verify flow regime for design assumptions
"""
        
        return results
        
    except Exception as e:
        return f"❌ Error in hydraulic calculation: {str(e)}"


@tool
def calculate_pipe_heat_loss(
    pipe_diameter_mm: float,
    pipe_length_m: float,
    fluid_temperature_c: float,
    soil_temperature_c: float,
    u_value_Wm2K: float = None,
    heat_loss_per_meter_Wm: float = None,
    use_direct_mode: bool = False
) -> str:
    """
    Calculate heat loss from a pipe segment using physics models.
    
    Args:
        pipe_diameter_mm: Outer pipe diameter [mm]
        pipe_length_m: Pipe segment length [m]
        fluid_temperature_c: Fluid temperature [°C]
        soil_temperature_c: Soil temperature [°C]
        u_value_Wm2K: U-value [W/m²K] (for U-value mode)
        heat_loss_per_meter_Wm: Heat loss per meter [W/m] (for direct mode)
        use_direct_mode: If True, use direct W/m mode; if False, use U-value mode
    
    Returns:
        Detailed heat loss analysis results
    """
    if not PHYSICS_AND_CATALOG_AVAILABLE:
        return "❌ Physics models not available"
    
    try:
        # Convert diameter from mm to m
        pipe_diameter_m = pipe_diameter_mm / 1000.0
        
        if use_direct_mode:
            if heat_loss_per_meter_Wm is None:
                return "❌ Heat loss per meter must be provided for direct mode"
            
            total_heat_loss = segment_heat_loss_W(
                U_or_Wpm=heat_loss_per_meter_Wm,
                d_outer=pipe_diameter_m,
                T_f=fluid_temperature_c,
                T_soil=soil_temperature_c,
                L=pipe_length_m,
                is_direct_Wpm=True
            )
            
            mode_info = f"Direct mode: {heat_loss_per_meter_Wm} W/m"
        else:
            if u_value_Wm2K is None:
                return "❌ U-value must be provided for U-value mode"
            
            total_heat_loss = segment_heat_loss_W(
                U_or_Wpm=u_value_Wm2K,
                d_outer=pipe_diameter_m,
                T_f=fluid_temperature_c,
                T_soil=soil_temperature_c,
                L=pipe_length_m,
                is_direct_Wpm=False
            )
            
            mode_info = f"U-value mode: {u_value_Wm2K} W/m²K"
        
        # Calculate surface area per meter
        surface_area_per_m = PI * pipe_diameter_m
        
        # Temperature difference
        delta_T = fluid_temperature_c - soil_temperature_c
        
        # Determine if heating or cooling
        if total_heat_loss > 0:
            heat_direction = "Heat loss (heating)"
        else:
            heat_direction = "Heat gain (cooling)"
        
        results = f"""
🔥 Pipe Heat Loss Analysis

📏 Input Parameters:
- Pipe diameter: {pipe_diameter_mm} mm ({pipe_diameter_m:.3f} m)
- Pipe length: {pipe_length_m} m
- Fluid temperature: {fluid_temperature_c} °C
- Soil temperature: {soil_temperature_c} °C
- Temperature difference: {delta_T} K
- {mode_info}

📊 Results:
- Surface area per meter: {surface_area_per_m:.3f} m²/m
- Total heat loss: {total_heat_loss:.0f} W ({heat_direction})
- Heat loss per meter: {total_heat_loss/pipe_length_m:.1f} W/m

⚡ Energy Impact:
- Heat loss per km: {total_heat_loss/pipe_length_m*1000:.0f} W/km
- Annual heat loss (assuming 8760 hours): {total_heat_loss*8760/1000:.0f} kWh/year

💡 Recommendations:
- Consider insulation for high heat losses
- Factor in heat losses for system efficiency
- Account for seasonal temperature variations
"""
        
        return results
        
    except Exception as e:
        return f"❌ Error in heat loss calculation: {str(e)}"


@tool
def optimize_district_heating_network(
    street_name: str,
    total_heat_demand_kW: float,
    supply_temperature_c: float = 80.0,
    return_temperature_c: float = 60.0,
    max_pressure_drop_kPa: float = 50.0,
    soil_temperature_c: float = 10.0
) -> str:
    """
    Optimize district heating network design using physics models and pipe catalog.
    
    Args:
        street_name: Name of the street for network design
        total_heat_demand_kW: Total heat demand [kW]
        supply_temperature_c: Supply temperature [°C]
        return_temperature_c: Return temperature [°C]
        max_pressure_drop_kPa: Maximum allowed pressure drop [kPa]
        soil_temperature_c: Soil temperature [°C]
    
    Returns:
        Optimized network design with pipe selection and performance analysis
    """
    if not PHYSICS_AND_CATALOG_AVAILABLE:
        return "❌ Physics models and pipe catalog not available"
    
    try:
        # Load pipe catalog
        catalog_path = "data/catalogs/pipe_catalog.csv"
        if not os.path.exists(catalog_path):
            return "❌ Pipe catalog not found. Run 'extract_pipe_catalog_from_excel' first."
        
        df = pd.read_csv(catalog_path)
        
        # Calculate flow rate from heat demand
        # Q = m * cp * delta_T
        # m = Q / (cp * delta_T)
        cp_water = 4186  # J/kgK
        delta_T = supply_temperature_c - return_temperature_c
        mass_flow_rate_kgs = (total_heat_demand_kW * 1000) / (cp_water * delta_T)
        
        # Convert to volumetric flow rate (assuming water density = 1000 kg/m³)
        volumetric_flow_rate_m3s = mass_flow_rate_kgs / 1000
        
        # Analyze different pipe diameters
        analysis_results = []
        
        for _, pipe in df.iterrows():
            dn = pipe['dn']
            d_inner_m = pipe['d_inner_m']
            cost_per_m = pipe['cost_eur_per_m']
            u_value = pipe['u_wpermk']
            
            # Calculate hydraulic parameters
            try:
                velocity, pressure_drop, head_loss = segment_hydraulics(
                    V_dot=volumetric_flow_rate_m3s,
                    d_inner=d_inner_m,
                    L=100,  # Assume 100m segment for analysis
                    rho=1000,
                    mu=0.001,
                    epsilon=DEFAULT_EPSILON,
                    K_minor=0.0
                )
                
                # Calculate heat loss
                heat_loss = segment_heat_loss_W(
                    U_or_Wpm=u_value,
                    d_outer=d_inner_m + 0.01,  # Approximate outer diameter
                    T_f=supply_temperature_c,
                    T_soil=soil_temperature_c,
                    L=100,
                    is_direct_Wpm=False
                )
                
                # Check if pressure drop is acceptable
                pressure_drop_kPa = pressure_drop / 1000
                is_acceptable = pressure_drop_kPa <= max_pressure_drop_kPa
                
                analysis_results.append({
                    'dn': dn,
                    'velocity': velocity,
                    'pressure_drop_kPa': pressure_drop_kPa,
                    'heat_loss_W': heat_loss,
                    'cost_per_m': cost_per_m,
                    'is_acceptable': is_acceptable
                })
                
            except Exception as e:
                continue
        
        if not analysis_results:
            return "❌ No suitable pipe diameters found for the given parameters"
        
        # Sort by cost (ascending)
        analysis_results.sort(key=lambda x: x['cost_per_m'])
        
        # Find the most cost-effective acceptable solution
        acceptable_pipes = [p for p in analysis_results if p['is_acceptable']]
        
        if not acceptable_pipes:
            return f"❌ No pipe diameters meet the pressure drop requirement ({max_pressure_drop_kPa} kPa)"
        
        best_pipe = acceptable_pipes[0]
        
        # Generate comprehensive report
        report = f"""
🏗️ District Heating Network Optimization for {street_name}

📊 System Parameters:
- Total heat demand: {total_heat_demand_kW} kW
- Supply temperature: {supply_temperature_c} °C
- Return temperature: {return_temperature_c} °C
- Temperature difference: {delta_T} K
- Mass flow rate: {mass_flow_rate_kgs:.2f} kg/s
- Volumetric flow rate: {volumetric_flow_rate_m3s:.3f} m³/s
- Maximum pressure drop: {max_pressure_drop_kPa} kPa

🎯 Recommended Solution:
- Pipe diameter: DN{best_pipe['dn']}
- Flow velocity: {best_pipe['velocity']:.2f} m/s
- Pressure drop: {best_pipe['pressure_drop_kPa']:.1f} kPa
- Heat loss per 100m: {best_pipe['heat_loss_W']:.0f} W
- Cost per meter: {best_pipe['cost_per_m']:.0f} €/m

📈 Alternative Options:
"""
        
        for i, pipe in enumerate(acceptable_pipes[:5]):
            report += f"  {i+1}. DN{pipe['dn']}: {pipe['pressure_drop_kPa']:.1f} kPa, {pipe['cost_per_m']:.0f} €/m\n"
        
        report += f"""
💡 Design Recommendations:
- Use DN{best_pipe['dn']} for optimal cost-performance balance
- Consider insulation to reduce heat losses
- Implement pressure monitoring at network extremities
- Factor in seasonal temperature variations

⚡ Energy Efficiency:
- Heat loss per km: {best_pipe['heat_loss_W']*10:.0f} W/km
- Annual heat loss: {best_pipe['heat_loss_W']*8760*10/1000:.0f} kWh/km/year

💰 Economic Considerations:
- Pipe cost per km: {best_pipe['cost_per_m']*1000:.0f} €/km
- Consider installation and maintenance costs
"""
        
        return report
        
    except Exception as e:
        return f"❌ Error in network optimization: {str(e)}"


@tool
def compare_heating_technologies(
    street_name: str,
    heat_demand_kW: float,
    electricity_price_eur_kwh: float = 0.30,
    gas_price_eur_kwh: float = 0.08,
    heat_pump_cop: float = 3.5
) -> str:
    """
    Compare different heating technologies using physics models and economic analysis.
    
    Args:
        street_name: Name of the street for analysis
        heat_demand_kW: Heat demand [kW]
        electricity_price_eur_kwh: Electricity price [€/kWh]
        gas_price_eur_kwh: Gas price [€/kWh]
        heat_pump_cop: Heat pump coefficient of performance
    
    Returns:
        Comprehensive comparison of heating technologies
    """
    try:
        # Calculate annual heat demand
        annual_heat_demand_kwh = heat_demand_kW * 8760  # 8760 hours per year
        
        # Technology 1: Heat Pumps
        hp_electricity_consumption_kwh = annual_heat_demand_kwh / heat_pump_cop
        hp_annual_cost_eur = hp_electricity_consumption_kwh * electricity_price_eur_kwh
        hp_installation_cost_eur = heat_demand_kW * 1500  # Rough estimate: 1500 €/kW
        
        # Technology 2: District Heating (using optimized network)
        dh_heat_loss_percentage = 0.05  # 5% heat loss
        dh_actual_heat_demand_kwh = annual_heat_demand_kwh * (1 + dh_heat_loss_percentage)
        dh_annual_cost_eur = dh_actual_heat_demand_kwh * 0.12  # 12 €/kWh for DH
        dh_installation_cost_eur = heat_demand_kW * 800  # Rough estimate: 800 €/kW
        
        # Technology 3: Gas Boilers
        gas_boiler_efficiency = 0.85
        gas_consumption_kwh = annual_heat_demand_kwh / gas_boiler_efficiency
        gas_annual_cost_eur = gas_consumption_kwh * gas_price_eur_kwh
        gas_installation_cost_eur = heat_demand_kW * 200  # Rough estimate: 200 €/kW
        
        # Calculate 20-year total costs
        years = 20
        hp_total_cost = hp_installation_cost_eur + (hp_annual_cost_eur * years)
        dh_total_cost = dh_installation_cost_eur + (dh_annual_cost_eur * years)
        gas_total_cost = gas_installation_cost_eur + (gas_annual_cost_eur * years)
        
        comparison = f"""
🏭 Heating Technology Comparison for {street_name}

📊 System Parameters:
- Heat demand: {heat_demand_kW} kW
- Annual heat demand: {annual_heat_demand_kwh:,.0f} kWh
- Analysis period: {years} years
- Electricity price: {electricity_price_eur_kwh} €/kWh
- Gas price: {gas_price_eur_kwh} €/kWh

🔧 Technology Analysis:

1️⃣ Heat Pumps (Air Source):
- COP: {heat_pump_cop}
- Annual electricity consumption: {hp_electricity_consumption_kwh:,.0f} kWh
- Annual operating cost: {hp_annual_cost_eur:,.0f} €
- Installation cost: {hp_installation_cost_eur:,.0f} €
- 20-year total cost: {hp_total_cost:,.0f} €

2️⃣ District Heating Network:
- Heat loss: {dh_heat_loss_percentage*100}%
- Annual heat consumption: {dh_actual_heat_demand_kwh:,.0f} kWh
- Annual operating cost: {dh_annual_cost_eur:,.0f} €
- Installation cost: {dh_installation_cost_eur:,.0f} €
- 20-year total cost: {dh_total_cost:,.0f} €

3️⃣ Gas Boilers:
- Efficiency: {gas_boiler_efficiency*100}%
- Annual gas consumption: {gas_consumption_kwh:,.0f} kWh
- Annual operating cost: {gas_annual_cost_eur:,.0f} €
- Installation cost: {gas_installation_cost_eur:,.0f} €
- 20-year total cost: {gas_total_cost:,.0f} €

📈 Cost Comparison (20 years):
- Heat Pumps: {hp_total_cost:,.0f} €
- District Heating: {dh_total_cost:,.0f} €
- Gas Boilers: {gas_total_cost:,.0f} €

🎯 Recommendations:
"""
        
        # Find the most cost-effective option
        costs = [
            ("Heat Pumps", hp_total_cost),
            ("District Heating", dh_total_cost),
            ("Gas Boilers", gas_total_cost)
        ]
        costs.sort(key=lambda x: x[1])
        
        best_option = costs[0]
        comparison += f"- Most cost-effective: {best_option[0]} ({best_option[1]:,.0f} €)\n"
        comparison += f"- Second best: {costs[1][0]} ({costs[1][1]:,.0f} €)\n"
        comparison += f"- Third best: {costs[2][0]} ({costs[2][1]:,.0f} €)\n"
        
        comparison += f"""
💡 Additional Considerations:
- Heat pumps: Best for individual buildings, high efficiency
- District heating: Best for dense urban areas, centralized control
- Gas boilers: Lowest upfront cost, but highest emissions

🌱 Environmental Impact:
- Heat pumps: Low emissions (depends on electricity mix)
- District heating: Medium emissions (depends on heat source)
- Gas boilers: High emissions (fossil fuel)
"""
        
        return comparison
        
    except Exception as e:
        return f"❌ Error in technology comparison: {str(e)}"


# Export all tools for use by agents
__all__ = [
    'extract_pipe_catalog_from_excel',
    'analyze_pipe_catalog', 
    'calculate_pipe_hydraulics',
    'calculate_pipe_heat_loss',
    'optimize_district_heating_network',
    'compare_heating_technologies'
]
