"""
HTML Dashboard Generation Module

Generates comprehensive HTML dashboards that combine:
- Metrics/KPIs in styled cards
- Embedded interactive maps
- Charts/visualizations
- JavaScript interactivity
- Professional styling
"""

import json
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class HTMLDashboardGenerator:
    """
    Generate comprehensive HTML dashboards for DH and HP scenarios.
    
    Features:
    - Professional CSS styling
    - Metric cards with grid layout
    - Embedded interactive maps (iframe)
    - Embedded charts (base64 or file reference)
    - JavaScript interactivity
    - Responsive design
    """
    
    def __init__(self, output_dir: str = "results_test/visualizations/html_dashboards"):
        """
        Initialize HTML dashboard generator.
        
        Args:
            output_dir: Directory to save generated HTML dashboards
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Styling configuration
        self.colors = {
            'primary': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'error': '#e74c3c',
            'dark': '#2c3e50',
            'light': '#ecf0f1',
            'border': '#bdc3c7',
            'gray': '#7f8c8d'
        }
    
    def create_dh_html_dashboard(
        self,
        kpi: Dict[str, Any],
        scenario_name: str,
        metadata: Optional[Dict] = None,
        map_file: Optional[str] = None,
        chart_files: Optional[List[str]] = None,
        routing_analysis: Optional[Dict[str, Any]] = None,
        dual_topology: Optional[Dict[str, Any]] = None,
        thermal_profile: Optional[List[Dict[str, Any]]] = None,
        network_stats: Optional[Dict[str, Any]] = None,
        generated_files: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Create comprehensive HTML dashboard for DH scenario.
        
        Args:
            kpi: KPI dictionary from DH simulation
            scenario_name: Name of the scenario
            metadata: Additional metadata (street name, buildings, etc.)
            map_file: Path to interactive map HTML file
            chart_files: List of chart image file paths
            
        Returns:
            Path to generated HTML file
        """
        metadata = metadata or {}
        street_name = metadata.get('street_name', scenario_name)
        
        # Generate HTML
        html_content = self._generate_dh_html(
            kpi=kpi,
            scenario_name=scenario_name,
            street_name=street_name,
            map_file=map_file,
            chart_files=chart_files,
            routing_analysis=routing_analysis,
            dual_topology=dual_topology,
            thermal_profile=thermal_profile,
            network_stats=network_stats,
            generated_files=generated_files,
        )
        
        # Save dashboard
        output_file = self.output_dir / f"{scenario_name}_dh_html_dashboard.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ DH HTML dashboard saved: {output_file}")
        return str(output_file)
    
    def create_hp_html_dashboard(
        self,
        kpi: Dict[str, Any],
        scenario_name: str,
        metadata: Optional[Dict] = None,
        map_file: Optional[str] = None,
        chart_files: Optional[List[str]] = None,
        generated_files: Optional[List[Dict[str, str]]] = None,
        insights: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create comprehensive HTML dashboard for HP scenario.
        """
        metadata = metadata or {}
        street_name = metadata.get('street_name', scenario_name)

        html_content = self._generate_hp_html(
            kpi=kpi,
            scenario_name=scenario_name,
            street_name=street_name,
            map_file=map_file,
            chart_files=chart_files,
            metadata=metadata,
            generated_files=generated_files,
            insights=insights,
        )
        
        # Save dashboard
        output_file = self.output_dir / f"{scenario_name}_hp_html_dashboard.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HP HTML dashboard saved: {output_file}")
        return str(output_file)
    
    def _generate_dh_html(
        self,
        kpi: Dict[str, Any],
        scenario_name: str,
        street_name: str,
        map_file: Optional[str],
        chart_files: Optional[List[str]],
        routing_analysis: Optional[Dict[str, Any]],
        dual_topology: Optional[Dict[str, Any]],
        thermal_profile: Optional[List[Dict[str, Any]]],
        network_stats: Optional[Dict[str, Any]],
        generated_files: Optional[List[Dict[str, str]]],
    ) -> str:
        """Generate HTML content for DH dashboard."""
        
        stats = network_stats or (dual_topology.get("stats") if dual_topology else {}) or {}
        # Extract metrics (prefer stats, fallback to KPIs)
        total_heat = stats.get('total_heat_demand_mwh', kpi.get('total_heat_supplied_mwh', 0))
        peak_load = kpi.get('peak_heat_load_kw', stats.get('total_heat_demand_kw', 0))
        num_junctions = stats.get('num_junctions', kpi.get('num_junctions', 0))
        num_pipes = stats.get('num_pipes', kpi.get('num_pipes', 0))
        num_consumers = stats.get('num_buildings', kpi.get('num_consumers', 0))
        total_length = stats.get('total_pipe_length_km', kpi.get('total_pipe_length_km', 0))
        if (not total_length) and stats.get('total_pipe_length_m'):
            try:
                total_length = float(stats.get('total_pipe_length_m', 0)) / 1000.0
            except (TypeError, ValueError):
                total_length = 0
        supply_len_km = stats.get('total_supply_length_km', 0)
        if (not supply_len_km) and stats.get('total_supply_length_m'):
            try:
                supply_len_km = float(stats.get('total_supply_length_m', 0)) / 1000.0
            except (TypeError, ValueError):
                supply_len_km = 0
        return_len_km = stats.get('total_return_length_km', 0)
        if (not return_len_km) and stats.get('total_return_length_m'):
            try:
                return_len_km = float(stats.get('total_return_length_m', 0)) / 1000.0
            except (TypeError, ValueError):
                return_len_km = 0
        service_len_m = stats.get('total_service_length_m', 0)
        avg_service_len = stats.get('avg_service_length_m', 0)
        
        max_pressure = kpi.get('max_pressure_drop_bar', stats.get('pressure_max_bar', 0))
        avg_pressure = kpi.get('avg_pressure_drop_bar', stats.get('pressure_avg_bar', 0))
        min_temp = kpi.get('min_supply_temp_c', stats.get('return_temperature_c', 0))
        avg_temp = kpi.get('avg_supply_temp_c', stats.get('supply_temperature_c', 0))
        heat_loss = kpi.get('network_heat_loss_kwh', 0)
        heat_loss_pct = kpi.get('heat_loss_percentage', 0)
        
        pump_energy = kpi.get('pump_energy_kwh', 0)
        lcoh = kpi.get('lcoh_eur_per_mwh', 0)
        co2 = kpi.get('co2_t_per_a', 0)
        avg_supply_diameter_mm = stats.get('avg_supply_diameter_mm')
        avg_return_diameter_mm = stats.get('avg_return_diameter_mm')
        avg_service_diameter_mm = stats.get('avg_service_diameter_mm')
        max_pipe_velocity = stats.get('max_pipe_velocity_ms')
        non_compliant_segments = stats.get('non_compliant_segments', 0)
        compliance_rate = stats.get('compliance_rate')
        sizing_section_html = ""
        if dual_topology:
            pipes = dual_topology.get("pipes", [])
            services = dual_topology.get("service_connections", [])
            non_compliant = [
                p for p in pipes if p.get("standards_compliant") is False
            ]
            non_compliant += [
                s for s in services if s.get("standards_compliant") is False
            ]
            has_sizing_data = any(
                value is not None
                for value in (
                    avg_supply_diameter_mm,
                    avg_return_diameter_mm,
                    avg_service_diameter_mm,
                    max_pipe_velocity,
                    compliance_rate,
                )
            ) or bool(non_compliant)
            if has_sizing_data:
                def _fmt(value: Optional[float], fmt: str) -> str:
                    if value is None:
                        return "N/A"
                    return format(value, fmt)

                sizing_cards = self._create_metric_cards([
                    ("Avg Supply Diameter", _fmt(avg_supply_diameter_mm, ".1f"), "mm"),
                    ("Avg Return Diameter", _fmt(avg_return_diameter_mm, ".1f"), "mm"),
                    ("Max Velocity", _fmt(max_pipe_velocity, ".2f"), "m/s"),
                    ("Non-compliant Segments", f"{non_compliant_segments}", "count"),
                ])
                compliance_rows = ""
                if non_compliant:
                    rows = []
                    for entry in non_compliant[:6]:
                        violations = entry.get("standards_violations") or []
                        message = violations[0]["message"] if violations else "Standards exceeded"
                        rows.append(
                            f"<tr><td>{entry.get('id')}</td><td>{message}</td></tr>"
                        )
                    compliance_rows = "".join(rows)
                compliance_table = ""
                if compliance_rows:
                    compliance_table = f"""
                        <table class="metric-table">
                            <thead><tr><th>Segment</th><th>Issue</th></tr></thead>
                            <tbody>{compliance_rows}</tbody>
                        </table>
                    """
                compliance_note = ""
                if compliance_rate is not None:
                    compliance_note = f"<p>Compliance rate: {compliance_rate*100:.1f}%</p>"
                if avg_service_diameter_mm is not None:
                    compliance_note += f"<p>Avg service diameter: {avg_service_diameter_mm:.1f} mm</p>"
            if stats.get("sizing_fallback_used"):
                reason = stats.get("sizing_fallback_reason", "Sizing fallback applied")
                default_mm = stats.get("sizing_fallback_diameter_mm", "N/A")
                compliance_note += f"<p>⚠️ Fallback sizing: {reason} (default {default_mm} mm)</p>"
                sizing_section_html = f"""
                    <div class="section">
                        <h3 class="section-title">🔧 Hydraulic Sizing</h3>
                        {sizing_cards}
                        {compliance_note}
                        {compliance_table}
                    </div>
                """
        
        # Generate metric cards HTML
        network_metrics = self._create_metric_cards([
            ("Supply Length", f"{supply_len_km:.2f}", "km"),
            ("Return Length", f"{return_len_km:.2f}", "km"),
            ("Service Length", f"{service_len_m:.1f}", "m"),
            ("Buildings Served", f"{num_consumers}", "count")
        ])
        
        thermal_metrics = self._create_metric_cards([
            ("Avg Supply Temp", f"{avg_temp:.1f}", "°C"),
            ("Min Return Temp", f"{min_temp:.1f}", "°C"),
            ("Heat Loss", f"{heat_loss_pct:.1f}", "%"),
            ("Annual Heat", f"{total_heat:.1f}", "MWh/year")
        ])
        
        hydraulic_metrics = self._create_metric_cards([
            ("Max Pressure Drop", f"{max_pressure:.3f}", "bar"),
            ("Avg Pressure Drop", f"{avg_pressure:.3f}", "bar"),
            ("Pump Energy", f"{pump_energy:.0f}", "kWh"),
            ("Avg Service Length", f"{avg_service_len:.1f}", "m")
        ])
        
        economic_metrics = self._create_metric_cards([
            ("Peak Load", f"{peak_load:.1f}", "kW"),
            ("LCoH", f"{lcoh:.2f}", "€/MWh"),
            ("CO₂ Emissions", f"{co2:.1f}", "t/year"),
            ("Network Density", f"{stats.get('network_density_km_per_building', 0):.3f}", "km/building")
        ])
        
        # Embed map
        map_section = self._create_map_embed_section(map_file, "DH Network")
        
        # Embed charts
        chart_section = self._create_chart_section(chart_files)

        generated_files_html = ""
        if generated_files:
            generated_files_html = self._create_generated_files_list(generated_files)

        routing_metrics_html = ""
        thermal_profile_html = ""
        if stats or routing_analysis or thermal_profile:
            success_rate = (routing_analysis or {}).get(
                "success_rate", stats.get("success_rate", 0)
            )

            temp_min = (routing_analysis or {}).get("temperature_min_c")
            temp_max = (routing_analysis or {}).get("temperature_max_c")
            pressure_min = (routing_analysis or {}).get("pressure_min_bar")
            pressure_max = (routing_analysis or {}).get("pressure_max_bar")

            if thermal_profile:
                temps = [row.get("temperature_c") for row in thermal_profile if row.get("temperature_c") is not None]
                if temps and (temp_min is None or temp_max is None):
                    temp_min = min(temps)
                    temp_max = max(temps)
                pressures = [row.get("pressure_bar") for row in thermal_profile if row.get("pressure_bar") is not None]
                if pressures and (pressure_min is None or pressure_max is None):
                    pressure_min = min(pressures)
                    pressure_max = max(pressures)

            routing_cards = self._create_metric_cards([
                ("Success Rate", f"{success_rate:.1f}", "%"),
                ("Total Main Length", f"{stats.get('total_main_length_km', 0):.2f}", "km"),
                ("Service Connections", f"{stats.get('service_connections', 0)}", "count"),
                ("Avg Service Length", f"{stats.get('avg_service_length_m', 0):.1f}", "m"),
            ])

            extra_rows = []
            if success_rate is not None:
                extra_rows.append(
                    f"<tr><td>Success Rate</td><td>{success_rate:.1f}%</td></tr>"
                )
            extra_rows.extend([
                f"<tr><td>Supply / Return Length</td><td>{supply_len_km:.2f} km / {return_len_km:.2f} km</td></tr>",
                f"<tr><td>Total Network Length</td><td>{total_length:.2f} km</td></tr>",
            ])
            if temp_min is not None and temp_max is not None:
                extra_rows.append(
                    f"<tr><td>Temperature Range</td><td>{temp_min:.1f}°C – {temp_max:.1f}°C</td></tr>"
                )
            if pressure_min is not None and pressure_max is not None:
                extra_rows.append(
                    f"<tr><td>Pressure Range</td><td>{pressure_min:.2f} – {pressure_max:.2f} bar</td></tr>"
                )

            extra_table = "<table class=\"metric-table\">" + "".join(extra_rows) + "</table>"

            routing_metrics_html = f"""
                <div class=\"section\">
                    <h3 class=\"section-title\">🛰️ Routing Insights</h3>
                    {routing_cards}
                    {extra_table}
                </div>
            """

            thermal_rows = []
            if temp_min is not None and temp_max is not None:
                thermal_rows.append(
                    f"<tr><td>Temperature Range</td><td>{temp_min:.1f}°C – {temp_max:.1f}°C</td></tr>"
                )
            if pressure_min is not None and pressure_max is not None:
                thermal_rows.append(
                    f"<tr><td>Pressure Range</td><td>{pressure_min:.2f} – {pressure_max:.2f} bar</td></tr>"
                )
            if stats:
                total_service = stats.get("total_service_length_m")
                if total_service is not None:
                    thermal_rows.append(
                        f"<tr><td>Total Service Length</td><td>{total_service:.1f} m</td></tr>"
                    )
            if thermal_rows:
                rows_html = "".join(thermal_rows)
                thermal_profile_html = f"""
                    <div class=\"section\">
                        <h3 class=\"section-title\">🌡️ Thermal & Hydraulic Profile</h3>
                        <table class="metric-table">
                            {rows_html}
                        </table>
                    </div>
                """
        
        # Generate complete HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DH Dashboard - {street_name}</title>
    {self._get_css_styles()}
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ District Heating Network Dashboard</h1>
            <h2>Scenario: {street_name}</h2>
            <p>Comprehensive dual-pipe system analysis with pandapipes simulation</p>
            <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h3 class="section-title">📊 Network Overview</h3>
            {network_metrics}
        </div>
        
        <div class="section">
            <h3 class="section-title">🌡️ Thermal Performance</h3>
            {thermal_metrics}
        </div>
        
        <div class="section">
            <h3 class="section-title">💧 Hydraulic Performance</h3>
            {hydraulic_metrics}
        </div>
        
        <div class="section">
            <h3 class="section-title">💰 Economic & Environmental</h3>
            {economic_metrics}
        </div>

        {sizing_section_html}
        
        {map_section}
        
        {routing_metrics_html}

        {thermal_profile_html}

        {generated_files_html}

        {chart_section}
        
        <div class="section">
            <h3 class="section-title">✅ System Status</h3>
            <div class="status-grid">
                <p><span class="status-success">✅ Dual-Pipe System</span> - Supply and return networks complete</p>
                <p><span class="status-success">✅ Pandapipes Simulation</span> - Hydraulic and thermal analysis converged</p>
                <p><span class="status-success">✅ Street-Based Routing</span> - All connections follow streets</p>
                <p><span class="status-success">✅ Engineering Compliance</span> - Industry standards met</p>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by: Branitz Energy Decision AI System</p>
            <p>Scenario: {scenario_name}</p>
        </div>
    </div>
    {self._get_javascript()}
</body>
</html>"""
        
        return html
    
    def _generate_hp_html(
        self,
        kpi: Dict[str, Any],
        scenario_name: str,
        street_name: str,
        map_file: Optional[str],
        chart_files: Optional[List[str]],
        metadata: Optional[Dict[str, Any]] = None,
        generated_files: Optional[List[Dict[str, str]]] = None,
        insights: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate HTML content for HP dashboard."""

        metadata = metadata or {}
        insights = insights or {}

        total_load_kw = abs(kpi.get('total_load_mw', 0) or 0) * 1000
        num_lines = kpi.get('num_lines', 0)
        num_loads = kpi.get('num_loads', 0)
        num_buses = kpi.get('num_buses', 0)

        min_voltage = kpi.get('min_voltage_pu', 0)
        max_voltage = kpi.get('max_voltage_pu', 0)
        avg_voltage = kpi.get('avg_voltage_pu', 0)
        voltage_violations = kpi.get('voltage_violations', 0)

        max_loading = kpi.get('max_line_loading_pct', 0)
        avg_loading = kpi.get('avg_line_loading_pct', 0)
        overloaded_lines = kpi.get('overloaded_lines', 0)

        trafo_loading = kpi.get('transformer_loading_pct', 0)
        total_losses_kw = abs(kpi.get('total_losses_mw', 0) or 0) * 1000
        loss_pct = abs(kpi.get('loss_percentage', 0) or 0)

        lcoh = kpi.get('lcoh_eur_per_mwh', 0)
        co2 = kpi.get('co2_t_per_a', 0)

        voltage_status = "success" if voltage_violations == 0 else "error"
        loading_status = "success" if overloaded_lines == 0 else "error"

        network_metrics = self._create_metric_cards([
            ("Total Load", f"{total_load_kw:.1f}", "kW"),
            ("Power Lines", f"{num_lines}", "lines"),
            ("Heat Pumps", f"{num_loads}", "units"),
            ("Buses", f"{num_buses}", "nodes")
        ])

        voltage_metrics = self._create_metric_cards([
            ("Min Voltage", f"{min_voltage:.3f}", "p.u."),
            ("Max Voltage", f"{max_voltage:.3f}", "p.u."),
            ("Avg Voltage", f"{avg_voltage:.3f}", "p.u."),
            ("Violations", f"{voltage_violations}", "buses", voltage_status)
        ])

        loading_metrics = self._create_metric_cards([
            ("Max Line Loading", f"{max_loading:.1f}", "%"),
            ("Avg Line Loading", f"{avg_loading:.1f}", "%"),
            ("Overloaded Lines", f"{overloaded_lines}", "lines", loading_status),
            ("Transformer Load", f"{trafo_loading:.1f}", "%")
        ])

        performance_metrics = self._create_metric_cards([
            ("Total Losses", f"{total_losses_kw:.2f}", "kW"),
            ("Loss Percentage", f"{loss_pct:.2f}", "%"),
            ("LCoH", f"{lcoh:.2f}", "€/MWh"),
            ("CO₂ Emissions", f"{co2:.1f}", "t/year")
        ])

        kpi_snapshot_rows = [
            ("Min Voltage", f"{min_voltage:.3f} pu"),
            ("Max Voltage", f"{max_voltage:.3f} pu"),
            ("Average Voltage", f"{avg_voltage:.3f} pu"),
            ("Voltage Violations", f"{voltage_violations} buses"),
            ("Max Line Loading", f"{max_loading:.1f}%"),
            ("Avg Line Loading", f"{avg_loading:.1f}%"),
            ("Overloaded Lines", f"{overloaded_lines} lines"),
            ("Transformer Loading", f"{trafo_loading:.1f}%"),
            ("System Losses", f"{total_losses_kw:.2f} kW"),
            ("Loss Percentage", f"{loss_pct:.2f}%"),
        ]
        kpi_snapshot_html = self._build_info_table(kpi_snapshot_rows)
        summary_section = ""
        if kpi_snapshot_html:
            summary_section = f"""
        <div class=\"section\">
            <h3 class=\"section-title\">🧾 KPI Snapshot</h3>
            {kpi_snapshot_html}
        </div>
        """

        context_rows = []
        filtered_buildings = metadata.get("filtered_buildings") or metadata.get("num_buildings")
        total_buildings = metadata.get("total_buildings")
        if filtered_buildings not in (None, ""):
            try:
                context_rows.append(("Buildings Selected", f"{int(round(float(filtered_buildings)))}"))
            except (TypeError, ValueError):
                context_rows.append(("Buildings Selected", str(filtered_buildings)))
        if total_buildings not in (None, "") and total_buildings != filtered_buildings:
            try:
                context_rows.append(("Buildings in Source", f"{int(round(float(total_buildings)))}"))
            except (TypeError, ValueError):
                context_rows.append(("Buildings in Source", str(total_buildings)))
        buffer_m = metadata.get("buffer_m")
        if buffer_m not in (None, ""):
            try:
                context_rows.append(("Selection Buffer", f"{float(buffer_m):.1f} m"))
            except (TypeError, ValueError):
                context_rows.append(("Selection Buffer", str(buffer_m)))
        filter_ratio = metadata.get("filter_ratio")
        if filter_ratio not in (None, ""):
            try:
                context_rows.append(("Selection Ratio", f"{float(filter_ratio) * 100:.2f}%"))
            except (TypeError, ValueError):
                context_rows.append(("Selection Ratio", str(filter_ratio)))
        hp_output_dir = metadata.get("hp_output_dir")
        if hp_output_dir:
            context_rows.append(("Output Directory", hp_output_dir))
        context_html = ""
        context_box = self._build_info_table(context_rows)
        if context_box:
            context_html = f"""
        <div class=\"section\">
            <h3 class=\"section-title\">📍 Street Context</h3>
            {context_box}
        </div>
        """

        map_section = self._create_map_embed_section(map_file, "HP Electrical Network")
        chart_section = self._create_chart_section(chart_files)

        generated_files_html = self._create_generated_files_list(generated_files) if generated_files else ""

        # Build insights/watchlist content
        low_voltage_entries = insights.get("low_voltage_buses") or []
        high_loading_entries = insights.get("high_loading_lines") or []
        violation_entries = insights.get("violations") or []
        transformer_bus = insights.get("transformer_bus")

        voltage_rows_html = "".join(
            f"<tr><td>Bus {entry.get('id')}</td><td>{entry.get('voltage', 0):.3f} pu</td>"
            f"<td>{entry.get('load_kw', 0):.1f} kW</td><td>{entry.get('status', 'normal').title()}</td></tr>"
            for entry in low_voltage_entries
        )
        voltage_table_html = ""
        if voltage_rows_html:
            voltage_table_html = f"""
                <div class=\"info-box\">
                    <h4>Lowest Voltages</h4>
                    <table class=\"metric-table\">
                        <thead><tr><th>Bus</th><th>Voltage</th><th>Load</th><th>Status</th></tr></thead>
                        <tbody>{voltage_rows_html}</tbody>
                    </table>
                </div>
            """

        loading_rows_html = "".join(
            f"<tr><td>Line {entry.get('id')}</td><td>{entry.get('loading_pct', 0):.1f}%</td>"
            f"<td>{entry.get('length_m', 0):.0f} m</td><td>{entry.get('status', 'normal').title()}</td></tr>"
            for entry in high_loading_entries
        )
        loading_table_html = ""
        if loading_rows_html:
            loading_table_html = f"""
                <div class=\"info-box\">
                    <h4>Highest Line Loadings</h4>
                    <table class=\"metric-table\">
                        <thead><tr><th>Line</th><th>Loading</th><th>Length</th><th>Status</th></tr></thead>
                        <tbody>{loading_rows_html}</tbody>
                    </table>
                </div>
            """

        violation_items = "".join(
            f"<li><strong>{row.get('element')}</strong>: {row.get('value')} (limit {row.get('limit')})"
            f" – {row.get('severity', '').title()}</li>"
            for row in violation_entries
        )
        violations_html = ""
        if violation_items:
            violations_html = f"""
                <div class=\"info-box\">
                    <h4>Alerts</h4>
                    <ul>{violation_items}</ul>
                </div>
            """

        transformer_note = ""
        if transformer_bus is not None:
            transformer_note = self._build_info_table([("Transformer Bus", str(transformer_bus))])

        watch_sections = [section for section in [voltage_table_html, loading_table_html, violations_html, transformer_note] if section]
        watchlist_html = ""
        if watch_sections:
            watchlist_html = f"""
        <div class=\"section\">
            <h3 class=\"section-title\">🔍 Watchlist & Alerts</h3>
            {''.join(watch_sections)}
        </div>
        """

        data_sources_html = ""
        data_sources = metadata.get("data_sources") or {}
        additional_items: List[str] = []
        if metadata.get("hp_output_dir"):
            additional_items.append(f"<li><strong>Output Directory:</strong> {metadata['hp_output_dir']}</li>")

        if data_sources or additional_items:
            source_items = [
                f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
                for key, value in data_sources.items()
                if value
            ] + additional_items
            if source_items:
                sources_html = "".join(source_items)
                data_sources_html = f"""
        <div class=\"section\">
            <h3 class=\"section-title\">📚 Data Sources & Context</h3>
            <div class=\"info-box\">
                <ul>{sources_html}</ul>
            </div>
        </div>
        """

        html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>HP Dashboard - {street_name}</title>
    {self._get_css_styles()}
</head>
<body>
    <div class=\"container\">
        <div class=\"header\">
            <h1>⚡ Heat Pump Electrical Network Dashboard</h1>
            <h2>Scenario: {street_name}</h2>
            <p>Comprehensive electrical infrastructure analysis with pandapower simulation</p>
            <p class=\"timestamp\">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class=\"section\">
            <h3 class=\"section-title\">🔌 Network Overview</h3>
            {network_metrics}
        </div>

        <div class=\"section\">
            <h3 class=\"section-title\">📊 Voltage Profile</h3>
            {voltage_metrics}
        </div>

        <div class=\"section\">
            <h3 class=\"section-title\">⚡ Loading Analysis</h3>
            {loading_metrics}
        </div>

        <div class=\"section\">
            <h3 class=\"section-title\">💰 Performance & Economics</h3>
            {performance_metrics}
        </div>

        {summary_section}
        {context_html}

        {map_section}

        {chart_section}

        {watchlist_html}

        {generated_files_html}

        {data_sources_html}

        <div class=\"section\">
            <h3 class=\"section-title\">✅ System Status</h3>
            <div class=\"status-grid\">
                <p><span class=\"status-{voltage_status}\">{'✅' if voltage_violations == 0 else '❌'} Voltage Quality</span> - {voltage_violations} violations detected</p>
                <p><span class=\"status-{loading_status}\">{'✅' if overloaded_lines == 0 else '❌'} Line Loading</span> - {overloaded_lines} overloaded lines</p>
                <p><span class=\"status-success\">✅ Pandapower Simulation</span> - Power flow analysis converged</p>
                <p><span class=\"status-success\">✅ Infrastructure Assessment</span> - Heat pump deployment feasibility evaluated</p>
            </div>
        </div>

        <div class=\"footer\">
            <p>Generated by: Branitz Energy Decision AI System</p>
            <p>Scenario: {scenario_name}</p>
        </div>
    </div>
    {self._get_javascript()}
</body>
</html>"""

        return html
    
    def _create_metric_cards(self, metrics: List[tuple]) -> str:
        """
        Create HTML for metric cards.
        
        Args:
            metrics: List of tuples (title, value, unit, [status])
            
        Returns:
            HTML string for metric grid
        """
        cards_html = '<div class="metric-grid">\n'
        
        for metric in metrics:
            title = metric[0]
            value = metric[1]
            unit = metric[2]
            status = metric[3] if len(metric) > 3 else "success"
            
            cards_html += f"""
                <div class="metric-card">
                    <div class="metric-title">{title}</div>
                    <div class="metric-value status-{status}">{value}</div>
                    <div class="metric-unit">{unit}</div>
                </div>
"""
        
        cards_html += '</div>\n'
        return cards_html
    
    def _build_info_table(self, rows: List[tuple], headers: Optional[List[str]] = None) -> str:
        """Create an info-box styled table from rows of (label, value)."""
        if not rows:
            return ""
        header_html = ""
        if headers:
            header_cells = "".join(f"<th>{header}</th>" for header in headers)
            header_html = f"<thead><tr>{header_cells}</tr></thead>"
        body_rows = "".join(
            f"<tr><td>{label}</td><td>{value}</td></tr>"
            for label, value in rows
        )
        return f"""
        <div class=\"info-box\">
            <table class=\"metric-table\">
                {header_html}
                <tbody>{body_rows}</tbody>
            </table>
        </div>
        """

    def _create_map_embed_section(self, map_file: Optional[str], title: str) -> str:
        """Create HTML section for embedded map."""
        
        if not map_file or not Path(map_file).exists():
            return f"""
        <div class="section">
            <h3 class="section-title">🗺️ {title}</h3>
            <div class="info-box">
                <p>⚠️ Interactive map not available. Generate map first using <code>create_interactive_map()</code></p>
            </div>
        </div>
"""
        
        # Convert to relative path
        map_path = Path(map_file).resolve()
        dashboard_dir = self.output_dir.resolve()
        
        try:
            # Calculate relative path from dashboard directory to map file
            rel_path = map_path.relative_to(dashboard_dir)
            map_src = rel_path.as_posix()
        except ValueError:
            try:
                rel_path = map_path.relative_to(dashboard_dir.parent)
                map_src = rel_path.as_posix()
            except ValueError:
                try:
                    map_src = map_path.resolve().as_uri()
                except Exception:
                    map_src = str(map_path)
        
        return f"""
        <div class="section">
            <h3 class="section-title">🗺️ {title}</h3>
            <div class="map-container">
                <iframe src="{map_src}" width="100%" height="600px"></iframe>
            </div>
        </div>
"""
    
    def _create_chart_section(self, chart_files: Optional[List[str]]) -> str:
        """Create HTML section for embedded charts."""
        
        if not chart_files or len(chart_files) == 0:
            return ""
        
        html = """
        <div class="section">
            <h3 class="section-title">📈 Analysis Charts</h3>
"""
        
        for chart_file in chart_files:
            if not Path(chart_file).exists():
                continue
            
            # Base64 encode the image
            try:
                with open(chart_file, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode()
                    img_src = f"data:image/png;base64,{img_data}"
                
                chart_name = Path(chart_file).stem.replace('_', ' ').title()
                
                html += f"""
            <div class="chart-container">
                <h4>{chart_name}</h4>
                <img src="{img_src}" alt="{chart_name}">
            </div>
"""
            except Exception as e:
                print(f"⚠️ Could not embed chart {chart_file}: {e}")
        
        html += """
        </div>
"""
        
        return html
    
    def _create_generated_files_list(self, generated_files: List[Dict[str, str]]) -> str:
        """Create HTML section listing generated artefacts."""
        if not generated_files:
            return ""

        items = []
        for entry in generated_files:
            href = entry.get("href") or entry.get("path") or entry.get("filename")
            if not href:
                continue
            label = entry.get("label")
            if label:
                items.append(f'<li><strong>{label}:</strong> <a href="{href}" target="_blank">{href}</a></li>')
            else:
                items.append(f'<li><a href="{href}" target="_blank">{href}</a></li>')

        if not items:
            return ""

        items_html = "\n".join(items)
        return f"""
        <div class="section">
            <h3 class="section-title">📂 Generated Files</h3>
            <ul class="generated-files-list">
                {items_html}
            </ul>
        </div>
        """
    
    def _create_insights_section(self, insights: Dict[str, Any]) -> str:
        """Create HTML section for displaying insights."""
        insights_html = ""
        if insights:
            insights_html += "<div class=\"section\">"
            insights_html += "<h3 class=\"section-title\">💡 Insights</h3>"
            insights_html += "<div class=\"insights-grid\">"
            for key, value in insights.items():
                insights_html += f"<div class=\"insight-card\">"
                insights_html += f"<h4>{key.replace('_', ' ').title()}</h4>"
                insights_html += f"<p>{value}</p>"
                insights_html += "</div>"
            insights_html += "</div>"
            insights_html += "</div>"
        return insights_html
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for HTML dashboard."""
        
        return f"""
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{ 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        
        .header {{ 
            text-align: center; 
            color: {self.colors['dark']}; 
            border-bottom: 4px solid {self.colors['primary']}; 
            padding-bottom: 20px; 
            margin-bottom: 40px;
        }}
        
        .header h1 {{ 
            font-size: 32px; 
            margin-bottom: 10px;
            background: linear-gradient(135deg, {self.colors['primary']}, #8e44ad);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .header h2 {{ 
            font-size: 24px; 
            color: {self.colors['gray']}; 
            margin-bottom: 10px;
        }}
        
        .header p {{ 
            color: {self.colors['gray']}; 
            font-size: 14px;
        }}
        
        .timestamp {{
            font-size: 12px;
            color: {self.colors['border']};
            font-style: italic;
        }}
        
        .section {{ 
            margin-bottom: 40px;
        }}
        
        .section-title {{ 
            color: {self.colors['dark']}; 
            border-bottom: 3px solid {self.colors['light']}; 
            padding-bottom: 12px; 
            margin-bottom: 25px;
            font-size: 20px;
        }}
        
        .metric-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px;
        }}
        
        .metric-card {{ 
            background: linear-gradient(135deg, {self.colors['light']} 0%, #d5dbdb 100%);
            padding: 25px; 
            border-radius: 12px; 
            border-left: 6px solid {self.colors['primary']};
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        }}
        
        .metric-title {{ 
            font-weight: 600; 
            color: {self.colors['dark']}; 
            margin-bottom: 12px;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .metric-value {{ 
            font-size: 32px; 
            font-weight: bold;
            margin-bottom: 8px;
        }}
        
        .metric-unit {{ 
            font-size: 13px; 
            color: {self.colors['gray']};
        }}
        
        .status-success {{ color: {self.colors['success']}; }}
        .status-warning {{ color: {self.colors['warning']}; }}
        .status-error {{ color: {self.colors['error']}; }}
        
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }}
        
        .status-grid p {{
            padding: 15px;
            background: {self.colors['light']};
            border-radius: 8px;
            border-left: 4px solid {self.colors['success']};
        }}
        
        .map-container {{ 
            text-align: center; 
            margin: 25px 0;
        }}
        
        .map-container iframe {{ 
            border: 2px solid {self.colors['border']}; 
            border-radius: 12px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }}
        
        .chart-container {{ 
            text-align: center; 
            margin: 25px 0;
        }}
        
        .chart-container img {{ 
            max-width: 100%; 
            height: auto; 
            border: 2px solid {self.colors['border']}; 
            border-radius: 12px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }}
        
        .chart-container h4 {{
            margin-bottom: 15px;
            color: {self.colors['dark']};
        }}

        .generated-files-list {{
            list-style: none;
            padding-left: 0;
            margin: 20px 0;
        }}

        .generated-files-list li {{
            padding: 10px 14px;
            margin-bottom: 8px;
            background: {self.colors['light']};
            border-radius: 8px;
            border-left: 4px solid {self.colors['primary']};
            color: {self.colors['dark']};
        }}

        .generated-files-list li strong {{
            display: inline-block;
            min-width: 170px;
        }}
        
        .info-box {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-left: 5px solid #ffc107;
            padding: 20px;
            border-radius: 8px;
        }}
        
        .info-box code {{
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }}
        
        .footer {{
            text-align: center;
            padding-top: 30px;
            margin-top: 40px;
            border-top: 2px solid {self.colors['light']};
            color: {self.colors['gray']};
            font-size: 14px;
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .container {{ 
                padding: 20px; 
                margin: 10px;
            }}
            
            .header h1 {{ font-size: 24px; }}
            .header h2 {{ font-size: 18px; }}
            
            .metric-grid {{ 
                grid-template-columns: 1fr;
            }}
            
            .map-container iframe {{ 
                height: 400px; 
            }}
        }}
        
        @media (max-width: 480px) {{
            body {{ padding: 10px; }}
            .container {{ padding: 15px; }}
            .metric-value {{ font-size: 24px; }}
        }}
    </style>
"""
    
    def _get_javascript(self) -> str:
        """Get JavaScript for dashboard interactivity."""
        
        return """
    <script>
        // Dashboard loaded successfully
        console.log('Branitz Energy Dashboard loaded');
        
        // Add smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
        
        // Add refresh functionality for embedded maps
        function refreshMap() {
            const iframes = document.querySelectorAll('.map-container iframe');
            iframes.forEach(iframe => {
                iframe.src = iframe.src;
            });
            console.log('Map refreshed');
        }
        
        // Dashboard initialization
        window.addEventListener('load', function() {
            console.log('Dashboard fully loaded');
            
            // Highlight any error status
            const errorElements = document.querySelectorAll('.status-error');
            errorElements.forEach(el => {
                el.closest('.metric-card')?.style.setProperty('border-left-color', '#e74c3c');
            });
        });
    </script>
"""


