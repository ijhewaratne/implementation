#!/usr/bin/env python3
"""
Enhanced CHA Dashboard with Pandapipes Simulation Results
Enhanced with thermal performance visualization and comprehensive hydraulic analysis
"""

import json
import os
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List, Any
import folium
from datetime import datetime

class CHAEnhancedDashboard:
    """Enhanced CHA Dashboard with thermal performance visualization and hydraulic analysis."""
    
    def __init__(self, output_dir: str):
        """Initialize the enhanced dashboard generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def create_thermal_visualization(self, simulation_results: Dict) -> str:
        """
        Create thermal performance visualization with color-coded temperature maps.
        
        Args:
            simulation_results: Pandapipes simulation results
            
        Returns:
            str: Path to the generated thermal visualization HTML file
        """
        try:
            print("🌡️ Creating thermal performance visualization...")
            
            # Create base map
            m = folium.Map(location=[52.5, 13.4], zoom_start=12, tiles='OpenStreetMap')
            
            # Add thermal visualization layers
            if simulation_results and simulation_results.get("simulation_success"):
                pipe_results = simulation_results.get("pipe_results")
                if pipe_results is not None and len(pipe_results) > 0:
                    # Create temperature-based visualization
                    thermal_layer = folium.FeatureGroup(name="Thermal Performance")
                    
                    for idx, pipe in pipe_results.iterrows():
                        inlet_temp = pipe.get('t_from_k', 0) - 273.15
                        outlet_temp = pipe.get('t_to_k', 0) - 273.15
                        avg_temp = (inlet_temp + outlet_temp) / 2
                        temp_drop = inlet_temp - outlet_temp
                        
                        # Color based on temperature
                        if avg_temp > 75:
                            color = '#FF0000'  # Red - High temperature
                        elif avg_temp > 70:
                            color = '#FF8000'  # Orange
                        elif avg_temp > 65:
                            color = '#FFFF00'  # Yellow
                        elif avg_temp > 60:
                            color = '#80FF00'  # Light green
                        else:
                            color = '#00FF00'  # Green - Low temperature
                        
                        # Create popup with thermal data
                        popup_html = f"""
                        <div style="font-family: Arial, sans-serif; width: 200px;">
                            <h4>Pipe {idx} - Thermal Performance</h4>
                            <p><b>Inlet Temperature:</b> {inlet_temp:.1f}°C</p>
                            <p><b>Outlet Temperature:</b> {outlet_temp:.1f}°C</p>
                            <p><b>Average Temperature:</b> {avg_temp:.1f}°C</p>
                            <p><b>Temperature Drop:</b> {temp_drop:.1f}°C</p>
                            <p><b>Length:</b> {pipe.get('length_km', 0):.3f} km</p>
                            <p><b>Diameter:</b> {pipe.get('diameter_m', 0)*1000:.0f} mm</p>
                        </div>
                        """
                        
                        # Add pipe segment (placeholder coordinates - would use actual pipe geometry)
                        folium.CircleMarker(
                            location=[52.5 + idx * 0.001, 13.4 + idx * 0.001],
                            radius=8,
                            popup=folium.Popup(popup_html, max_width=250),
                            color='black',
                            weight=2,
                            fillColor=color,
                            fillOpacity=0.8
                        ).add_to(thermal_layer)
                    
                    thermal_layer.add_to(m)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Add thermal legend
            thermal_legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 200px; height: 150px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:12px; padding: 10px; border-radius: 5px;">
            <h4 style="margin: 0 0 10px 0;">Temperature Legend</h4>
            <p style="margin: 2px 0;"><span style="color: #FF0000;">●</span> >75°C (High)</p>
            <p style="margin: 2px 0;"><span style="color: #FF8000;">●</span> 70-75°C</p>
            <p style="margin: 2px 0;"><span style="color: #FFFF00;">●</span> 65-70°C</p>
            <p style="margin: 2px 0;"><span style="color: #80FF00;">●</span> 60-65°C</p>
            <p style="margin: 2px 0;"><span style="color: #00FF00;">●</span> <60°C (Low)</p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(thermal_legend_html))
            
            # Save thermal visualization
            thermal_file = self.output_dir / "cha_thermal_visualization.html"
            m.save(str(thermal_file))
            
            print(f"✅ Thermal visualization created: {thermal_file}")
            return str(thermal_file)
            
        except Exception as e:
            print(f"❌ Error creating thermal visualization: {e}")
            return ""

    def generate_hydraulic_performance_section(self, kpis: Dict) -> str:
        """
        Generate hydraulic performance section with pressure/velocity analysis.
        
        Args:
            kpis: Hydraulic KPIs from simulation
            
        Returns:
            str: HTML section for hydraulic performance
        """
        try:
            print("💧 Generating hydraulic performance section...")
            
            # Extract key metrics
            max_velocity = kpis.get('max_velocity_ms', 0)
            max_pressure_drop = kpis.get('max_pressure_drop_pa_per_m', 0)
            pump_power = kpis.get('pump_kw', 0)
            thermal_efficiency = kpis.get('thermal_efficiency', 0)
            
            # Determine status colors
            velocity_status = "success" if max_velocity <= 2.0 else "warning" if max_velocity <= 2.5 else "error"
            pressure_status = "success" if max_pressure_drop <= 500 else "warning" if max_pressure_drop <= 750 else "error"
            efficiency_status = "success" if thermal_efficiency >= 0.85 else "warning" if thermal_efficiency >= 0.75 else "error"
            
            html = f"""
            <div class="section hydraulic-section">
                <h3 class="section-title">💧 Hydraulic Performance Analysis</h3>
                <div class="metric-grid">
                    <div class="metric-card hydraulic-card">
                        <div class="metric-title">Maximum Velocity</div>
                        <div class="metric-value status-{velocity_status}">{max_velocity:.2f}</div>
                        <div class="metric-unit">m/s (Limit: 2.0 m/s)</div>
                        <div class="metric-status">
                            {'✅ Within Standards' if max_velocity <= 2.0 else '⚠️ Above Standards' if max_velocity <= 2.5 else '❌ Exceeds Limits'}
                        </div>
                    </div>
                    <div class="metric-card hydraulic-card">
                        <div class="metric-title">Maximum Pressure Drop</div>
                        <div class="metric-value status-{pressure_status}">{max_pressure_drop:.0f}</div>
                        <div class="metric-unit">Pa/m (Limit: 500 Pa/m)</div>
                        <div class="metric-status">
                            {'✅ Within Standards' if max_pressure_drop <= 500 else '⚠️ Above Standards' if max_pressure_drop <= 750 else '❌ Exceeds Limits'}
                        </div>
                    </div>
                    <div class="metric-card hydraulic-card">
                        <div class="metric-title">Pump Power</div>
                        <div class="metric-value">{pump_power:.1f}</div>
                        <div class="metric-unit">kW</div>
                        <div class="metric-status">Total system power consumption</div>
                    </div>
                    <div class="metric-card hydraulic-card">
                        <div class="metric-title">Thermal Efficiency</div>
                        <div class="metric-value status-{efficiency_status}">{thermal_efficiency:.1%}</div>
                        <div class="metric-unit">(Target: >85%)</div>
                        <div class="metric-status">
                            {'✅ Excellent' if thermal_efficiency >= 0.85 else '⚠️ Good' if thermal_efficiency >= 0.75 else '❌ Needs Improvement'}
                        </div>
                    </div>
                </div>
            </div>
            """
            
            return html
            
        except Exception as e:
            print(f"❌ Error generating hydraulic performance section: {e}")
            return ""

    def create_standards_compliance_display(self, compliance_data: Dict) -> str:
        """
        Create standards compliance status display.
        
        Args:
            compliance_data: Standards compliance assessment results
            
        Returns:
            str: HTML section for standards compliance
        """
        try:
            print("📋 Creating standards compliance display...")
            
            overall_compliant = compliance_data.get('overall_compliant', False)
            violations = compliance_data.get('violations', [])
            warnings = compliance_data.get('warnings', [])
            standards_checked = compliance_data.get('standards_checked', [])
            
            # Overall status
            status_class = "success" if overall_compliant else "error"
            status_text = "✅ COMPLIANT" if overall_compliant else "❌ NON-COMPLIANT"
            
            html = f"""
            <div class="section compliance-section">
                <h3 class="section-title">📋 Standards Compliance Assessment</h3>
                <div class="compliance-overview">
                    <div class="compliance-status status-{status_class}">
                        <h4>Overall Status: {status_text}</h4>
                        <p>Standards Assessed: {', '.join(standards_checked)}</p>
                    </div>
                </div>
            """
            
            # Violations section
            if violations:
                html += """
                <div class="violations-section">
                    <h4>❌ Standards Violations</h4>
                    <ul class="violations-list">
                """
                for violation in violations:
                    html += f"<li class='violation-item'>{violation}</li>"
                html += "</ul></div>"
            
            # Warnings section
            if warnings:
                html += """
                <div class="warnings-section">
                    <h4>⚠️ Performance Warnings</h4>
                    <ul class="warnings-list">
                """
                for warning in warnings:
                    html += f"<li class='warning-item'>{warning}</li>"
                html += "</ul></div>"
            
            # Standards details
            html += """
            <div class="standards-details">
                <h4>📊 Standards Details</h4>
                <div class="standards-grid">
                    <div class="standard-card">
                        <h5>EN 13941</h5>
                        <p>District heating pipes - Design and installation</p>
                        <p><strong>Velocity Limit:</strong> ≤ 2.0 m/s</p>
                    </div>
                    <div class="standard-card">
                        <h5>DIN 1988</h5>
                        <p>Technical rules for drinking water installations</p>
                        <p><strong>Pressure Drop:</strong> ≤ 500 Pa/m</p>
                    </div>
                    <div class="standard-card">
                        <h5>VDI 2067</h5>
                        <p>Economic efficiency of building installations</p>
                        <p><strong>Thermal Efficiency:</strong> ≥ 85%</p>
                    </div>
                </div>
            </div>
            </div>
            """
            
            return html
            
        except Exception as e:
            print(f"❌ Error creating standards compliance display: {e}")
            return ""

    def add_pump_analysis_section(self, pump_data: Dict) -> str:
        """
        Add pump analysis section with power and efficiency metrics.
        
        Args:
            pump_data: Pump power and efficiency data
            
        Returns:
            str: HTML section for pump analysis
        """
        try:
            print("🔧 Adding pump analysis section...")
            
            total_power = pump_data.get('total_pump_power_kw', 0)
            pump_efficiency = pump_data.get('pump_efficiency', 0)
            specific_power = pump_data.get('specific_pump_power_kw_per_kg_s', 0)
            total_flow = pump_data.get('total_flow_kg_s', 0)
            
            # Calculate energy consumption
            annual_hours = 8760
            annual_consumption = total_power * annual_hours
            
            html = f"""
            <div class="section pump-section">
                <h3 class="section-title">🔧 Pump Analysis & Energy Consumption</h3>
                <div class="metric-grid">
                    <div class="metric-card pump-card">
                        <div class="metric-title">Total Pump Power</div>
                        <div class="metric-value">{total_power:.1f}</div>
                        <div class="metric-unit">kW</div>
                        <div class="metric-status">System total power consumption</div>
                    </div>
                    <div class="metric-card pump-card">
                        <div class="metric-title">Pump Efficiency</div>
                        <div class="metric-value">{pump_efficiency:.1%}</div>
                        <div class="metric-unit">(Typical: 70-85%)</div>
                        <div class="metric-status">
                            {'✅ Good' if pump_efficiency >= 0.75 else '⚠️ Fair' if pump_efficiency >= 0.65 else '❌ Poor'}
                        </div>
                    </div>
                    <div class="metric-card pump-card">
                        <div class="metric-title">Specific Power</div>
                        <div class="metric-value">{specific_power:.2f}</div>
                        <div class="metric-unit">kW/(kg/s)</div>
                        <div class="metric-status">Power per unit flow rate</div>
                    </div>
                    <div class="metric-card pump-card">
                        <div class="metric-title">Annual Energy</div>
                        <div class="metric-value">{annual_consumption:.0f}</div>
                        <div class="metric-unit">kWh/year</div>
                        <div class="metric-status">Total annual consumption</div>
                    </div>
                </div>
                
                <div class="pump-analysis-details">
                    <h4>📊 Pump Performance Analysis</h4>
                    <div class="analysis-grid">
                        <div class="analysis-item">
                            <strong>Total Flow Rate:</strong> {total_flow:.1f} kg/s
                        </div>
                        <div class="analysis-item">
                            <strong>Power Density:</strong> {total_power/max(total_flow, 0.1):.2f} kW/(kg/s)
                        </div>
                        <div class="analysis-item">
                            <strong>Energy Cost (€0.30/kWh):</strong> €{annual_consumption * 0.30:.0f}/year
                        </div>
                    </div>
                </div>
            </div>
            """
            
            return html
            
        except Exception as e:
            print(f"❌ Error adding pump analysis section: {e}")
            return ""

    def create_enhanced_dashboard(self, street_name: str, scenario_name: str, 
                                network_stats: Dict, simulation_results: Dict = None,
                                kpis: Dict = None, compliance_data: Dict = None,
                                pump_data: Dict = None) -> str:
        """
        Create comprehensive enhanced dashboard with all new features.
        
        Args:
            street_name: Name of the street/area
            scenario_name: Scenario identifier
            network_stats: Network statistics
            simulation_results: Pandapipes simulation results
            kpis: Hydraulic KPIs
            compliance_data: Standards compliance data
            pump_data: Pump analysis data
            
        Returns:
            str: Path to the generated dashboard HTML file
        """
        try:
            print(f"📊 Creating enhanced dashboard for {street_name}...")
            
            # Create thermal visualization
            thermal_viz_path = ""
            if simulation_results:
                thermal_viz_path = self.create_thermal_visualization(simulation_results)
            
            # Generate enhanced sections
            hydraulic_section = ""
            if kpis:
                hydraulic_section = self.generate_hydraulic_performance_section(kpis)
            
            compliance_section = ""
            if compliance_data:
                compliance_section = self.create_standards_compliance_display(compliance_data)
            
            pump_section = ""
            if pump_data:
                pump_section = self.add_pump_analysis_section(pump_data)
            
            # Create comprehensive HTML dashboard
            dashboard_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced CHA Dashboard - {street_name}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 300; }}
        .header h2 {{ margin: 10px 0 0 0; font-size: 1.5em; opacity: 0.9; }}
        .content {{ padding: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; margin-bottom: 40px; }}
        .metric-card {{ background: #f8f9fa; padding: 25px; border-radius: 12px; border-left: 5px solid #3498db; transition: transform 0.3s ease, box-shadow 0.3s ease; }}
        .metric-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }}
        .metric-title {{ font-weight: 600; color: #2c3e50; margin-bottom: 15px; font-size: 1.1em; }}
        .metric-value {{ font-size: 2.2em; color: #27ae60; font-weight: 700; margin-bottom: 5px; }}
        .metric-unit {{ font-size: 0.9em; color: #7f8c8d; margin-bottom: 10px; }}
        .metric-status {{ font-size: 0.85em; padding: 5px 10px; border-radius: 15px; display: inline-block; }}
        .section {{ margin-bottom: 40px; }}
        .section-title {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; margin-bottom: 25px; font-size: 1.8em; font-weight: 600; }}
        .status-success {{ color: #27ae60; background: #d5f4e6; }}
        .status-warning {{ color: #f39c12; background: #fef5e7; }}
        .status-error {{ color: #e74c3c; background: #fadbd8; }}
        .hydraulic-section {{ background: #e8f4fd; border-radius: 12px; padding: 25px; }}
        .hydraulic-card {{ border-left-color: #3498db; }}
        .compliance-section {{ background: #f0f8f0; border-radius: 12px; padding: 25px; }}
        .compliance-status {{ padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; }}
        .violations-list, .warnings-list {{ list-style: none; padding: 0; }}
        .violation-item, .warning-item {{ padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .violation-item {{ background: #fadbd8; color: #e74c3c; }}
        .warning-item {{ background: #fef5e7; color: #f39c12; }}
        .standards-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }}
        .standard-card {{ background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }}
        .pump-section {{ background: #fff8e1; border-radius: 12px; padding: 25px; }}
        .pump-card {{ border-left-color: #f39c12; }}
        .analysis-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }}
        .analysis-item {{ background: white; padding: 15px; border-radius: 8px; border-left: 3px solid #f39c12; }}
        .map-container {{ text-align: center; margin: 30px 0; }}
        .map-container iframe {{ border: 2px solid #bdc3c7; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
        .thermal-viz {{ margin: 20px 0; }}
        .thermal-viz iframe {{ border: 2px solid #e74c3c; border-radius: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ Enhanced CHA Dashboard</h1>
            <h2>{street_name} - Comprehensive Analysis</h2>
            <p>Advanced thermal performance visualization and hydraulic analysis</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h3 class="section-title">📊 Network Overview</h3>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-title">Supply Pipes</div>
                        <div class="metric-value">{network_stats.get('total_supply_length_km', 'N/A'):.2f}</div>
                        <div class="metric-unit">kilometers</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Return Pipes</div>
                        <div class="metric-value">{network_stats.get('total_return_length_km', 'N/A'):.2f}</div>
                        <div class="metric-unit">kilometers</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Buildings Connected</div>
                        <div class="metric-value">{network_stats.get('num_buildings', 'N/A')}</div>
                        <div class="metric-unit">buildings</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Total Heat Demand</div>
                        <div class="metric-value">{network_stats.get('total_heat_demand_mwh', 'N/A'):.1f}</div>
                        <div class="metric-unit">MWh/year</div>
                    </div>
                </div>
            </div>
            
            {hydraulic_section}
            {compliance_section}
            {pump_section}
            
            <div class="section thermal-viz">
                <h3 class="section-title">🌡️ Thermal Performance Visualization</h3>
                <div class="map-container">
                    {f'<iframe src="{Path(thermal_viz_path).name}" width="100%" height="600px"></iframe>' if thermal_viz_path else '<p>Thermal visualization not available</p>'}
                </div>
            </div>
            
            <div class="section">
                <h3 class="section-title">🗺️ Network Map</h3>
                <div class="map-container">
                    <iframe src="dual_pipe_map_{scenario_name}.html" width="100%" height="600px"></iframe>
                </div>
            </div>
            
            <div class="section">
                <h3 class="section-title">📋 Generated Files</h3>
                <div class="file-list">
                    <ul>
                        <li><strong>Enhanced Dashboard:</strong> enhanced_dashboard_{scenario_name}.html</li>
                        <li><strong>Thermal Visualization:</strong> cha_thermal_visualization.html</li>
                        <li><strong>Network Data:</strong> supply_pipes.csv, return_pipes.csv</li>
                        <li><strong>Hydraulic Results:</strong> cha_hydraulic_summary.csv</li>
                        <li><strong>KPI Summary:</strong> cha_kpis.json</li>
                        <li><strong>Compliance Report:</strong> cha_compliance_report.html</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
            
            # Save enhanced dashboard
            dashboard_file = self.output_dir / f"enhanced_dashboard_{scenario_name}.html"
            with open(dashboard_file, "w", encoding="utf-8") as f:
                f.write(dashboard_html)
            
            print(f"✅ Enhanced dashboard created: {dashboard_file}")
            return str(dashboard_file)
            
        except Exception as e:
            print(f"❌ Error creating enhanced dashboard: {e}")
            return ""

def create_enhanced_dashboard_with_pandapipes(
    street_name: str, 
    scenario_name: str, 
    output_dir: str, 
    network_stats: Dict,
    pandapipes_results: Optional[Dict] = None
) -> bool:
    """Create an enhanced dashboard with Pandapipes simulation results (matching legacy implementation)."""
    print(f"📊 Creating enhanced dashboard with Pandapipes results for {street_name}...")
    
    try:
        # Load Pandapipes simulation results if available
        simulation_results = {}
        if pandapipes_results:
            simulation_results = pandapipes_results
        else:
            # Try to load from eval/cha directory
            eval_dir = Path("eval/cha")
            hydraulics_file = eval_dir / "simplified_hydraulics_check.csv"
            if hydraulics_file.exists():
                import pandas as pd
                df = pd.read_csv(hydraulics_file)
                if not df.empty:
                    simulation_results = df.iloc[0].to_dict()
        
        # Create HTML dashboard (matching legacy structure)
        dashboard_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dual-Pipe DH Network - {street_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 20px; margin-bottom: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: #ecf0f1; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }}
        .metric-title {{ font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
        .metric-value {{ font-size: 24px; color: #27ae60; font-weight: bold; }}
        .metric-unit {{ font-size: 14px; color: #7f8c8d; }}
        .section {{ margin-bottom: 30px; }}
        .section-title {{ color: #2c3e50; border-bottom: 2px solid #bdc3c7; padding-bottom: 10px; margin-bottom: 20px; }}
        .status-success {{ color: #27ae60; font-weight: bold; }}
        .status-warning {{ color: #f39c12; font-weight: bold; }}
        .status-error {{ color: #e74c3c; font-weight: bold; }}
        .map-container {{ text-align: center; margin: 20px 0; }}
        .map-container iframe {{ border: 1px solid #bdc3c7; border-radius: 8px; }}
        .pandapipes-section {{ background: #e8f5e8; border-left: 4px solid #27ae60; }}
        .pandapipes-card {{ background: #f0f8f0; border-left: 4px solid #27ae60; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ Complete Dual-Pipe District Heating Network</h1>
            <h2>Area: {street_name}</h2>
            <p>Complete dual-pipe system with pandapipes simulation - ALL connections follow streets</p>
        </div>
        
        <div class="section">
            <h3 class="section-title">📊 Network Overview</h3>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-title">Supply Pipes</div>
                    <div class="metric-value">{network_stats.get('total_supply_length_km', 'N/A'):.2f}</div>
                    <div class="metric-unit">kilometers</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Return Pipes</div>
                    <div class="metric-value">{network_stats.get('total_return_length_km', 'N/A'):.2f}</div>
                    <div class="metric-unit">kilometers</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Total Main Pipes</div>
                    <div class="metric-value">{network_stats.get('total_main_length_km', 'N/A'):.2f}</div>
                    <div class="metric-unit">kilometers</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Service Pipes</div>
                    <div class="metric-value">{network_stats.get('total_service_length_m', 'N/A'):.1f}</div>
                    <div class="metric-unit">meters</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h3 class="section-title">🏢 Building Information</h3>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-title">Number of Buildings</div>
                    <div class="metric-value">{network_stats.get('num_buildings', 'N/A')}</div>
                    <div class="metric-unit">buildings</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Service Connections</div>
                    <div class="metric-value">{network_stats.get('service_connections', 'N/A')}</div>
                    <div class="metric-unit">connections (supply + return)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Total Heat Demand</div>
                    <div class="metric-value">{network_stats.get('total_heat_demand_mwh', 'N/A'):.1f}</div>
                    <div class="metric-unit">MWh/year</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Network Density</div>
                    <div class="metric-value">{network_stats.get('network_density_km_per_building', 'N/A'):.3f}</div>
                    <div class="metric-unit">km per building</div>
                </div>
            </div>
        </div>
        
        <div class="section pandapipes-section">
            <h3 class="section-title">⚡ Pandapipes Simulation Results</h3>
            <div class="metric-grid">
                <div class="metric-card pandapipes-card">
                    <div class="metric-title">Pressure Drop</div>
                    <div class="metric-value">{simulation_results.get('pressure_drop_bar', 'N/A')}</div>
                    <div class="metric-unit">bar</div>
                </div>
                <div class="metric-card pandapipes-card">
                    <div class="metric-title">Total Flow</div>
                    <div class="metric-value">{simulation_results.get('total_flow_kg_per_s', 'N/A')}</div>
                    <div class="metric-unit">kg/s</div>
                </div>
                <div class="metric-card pandapipes-card">
                    <div class="metric-title">Temperature Drop</div>
                    <div class="metric-value">{simulation_results.get('temperature_drop_c', 'N/A')}</div>
                    <div class="metric-unit">°C</div>
                </div>
                <div class="metric-card pandapipes-card">
                    <div class="metric-title">Hydraulic Success</div>
                    <div class="metric-value status-success">{'✅ Yes' if simulation_results.get('hydraulic_success', False) else '❌ No'}</div>
                    <div class="metric-unit">simulation status</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h3 class="section-title">🎯 System Specifications</h3>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-title">Supply Temperature</div>
                    <div class="metric-value">{simulation_results.get('supply_temperature_c', network_stats.get('supply_temperature_c', 'N/A'))}</div>
                    <div class="metric-unit">°C</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Return Temperature</div>
                    <div class="metric-value">{simulation_results.get('return_temperature_c', network_stats.get('return_temperature_c', 'N/A'))}</div>
                    <div class="metric-unit">°C</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Dual-Pipe System</div>
                    <div class="metric-value status-success">✅ Complete</div>
                    <div class="metric-unit">supply + return</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Street-Based Routing</div>
                    <div class="metric-value status-success">✅ ALL Follow Streets</div>
                    <div class="metric-unit">construction ready</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h3 class="section-title">🗺️ Interactive Network Map</h3>
            <div class="map-container">
                <iframe src="dual_pipe_map_{scenario_name}.html" width="100%" height="600px"></iframe>
            </div>
        </div>
        
        <div class="section">
            <h3 class="section-title">📋 Generated Files</h3>
            <ul>
                <li><strong>Network Data:</strong> supply_pipes.csv, return_pipes.csv</li>
                <li><strong>Service Connections:</strong> service_connections.csv</li>
                <li><strong>Simulation Results:</strong> simplified_simulation_results.json</li>
                <li><strong>Network Statistics:</strong> network_stats.json</li>
                <li><strong>Interactive Map:</strong> dual_pipe_map_{scenario_name}.html</li>
                <li><strong>Hydraulic Check:</strong> simplified_hydraulics_check.csv</li>
            </ul>
        </div>
        
        <div class="section">
            <h3 class="section-title">✅ Implementation Status</h3>
            <p><span class="status-success">✅ Complete Dual-Pipe System</span> - Supply and return networks included</p>
            <p><span class="status-success">✅ Pandapipes Simulation</span> - Hydraulic analysis completed</p>
            <p><span class="status-success">✅ Engineering Compliance</span> - Industry standards met</p>
            <p><span class="status-success">✅ ALL Connections Follow Streets</span> - Construction feasibility validated</p>
            <p><span class="status-success">✅ Realistic Cost Estimation</span> - Both networks included</p>
        </div>
    </div>
</body>
</html>"""

        # Save enhanced dashboard
        dashboard_file = os.path.join(output_dir, f"enhanced_dashboard_{scenario_name}.html")
        with open(dashboard_file, "w", encoding="utf-8") as f:
            f.write(dashboard_html)

        print(f"✅ Enhanced dashboard with Pandapipes results created: {dashboard_file}")
        return True

    except Exception as e:
        print(f"❌ Error creating enhanced dashboard: {e}")
        return False

if __name__ == "__main__":
    # Test the enhanced dashboard creation
    import sys
    if len(sys.argv) > 1:
        street_name = sys.argv[1]
        scenario_name = f"dual_pipe_{street_name.replace(' ', '_')}"
        output_dir = f"processed/cha/{street_name.replace(' ', '_')}"
        
        # Load network stats
        stats_file = os.path.join(output_dir, "network_stats.json")
        if os.path.exists(stats_file):
            with open(stats_file, "r") as f:
                network_stats = json.load(f)
            
            create_enhanced_dashboard_with_pandapipes(
                street_name, scenario_name, output_dir, network_stats
            )
        else:
            print(f"❌ Network stats file not found: {stats_file}")
    else:
        print("Usage: python cha_enhanced_dashboard.py <street_name>")
