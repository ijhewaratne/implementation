"""
12-Panel Summary Dashboard Generator.

Creates comprehensive summary dashboards with:
- Key Performance Indicators
- Network topology visualization
- Service connection analysis
- Efficiency metrics
- Hydraulic/electrical performance
- Cost indicators
- Technical specifications

Adapted from street_final_copy_3/01_create_summary_dashboard.py
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

# Import our color palette
import sys
sys.path.append(str(Path(__file__).parent.parent))
from visualization.colormaps import NETWORK_COLORS


class SummaryDashboard:
    """
    Create comprehensive 12-panel summary dashboards.
    
    Supports both DH and HP scenarios with scenario-specific panels.
    """
    
    def __init__(self, output_dir: str = "results_test/visualizations/dashboards"):
        """
        Initialize the summary dashboard generator.
        
        Args:
            output_dir: Directory to save generated dashboards
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set plotting style
        plt.style.use("default")
        sns.set_palette("husl")
    
    def create_dh_summary(
        self,
        kpi: Dict[str, Any],
        scenario_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create 12-panel summary dashboard for DH scenario.
        
        Args:
            kpi: KPI dictionary from simulation results
            scenario_name: Name of the scenario
            metadata: Optional metadata dictionary
        
        Returns:
            Path to saved PNG file
        """
        # Create figure with 12 subplots (3 rows × 4 columns)
        fig = plt.figure(figsize=(24, 18))
        
        # Main title
        fig.suptitle(
            f"District Heating Network - Summary Dashboard\n{scenario_name}",
            fontsize=20,
            fontweight="bold",
            y=0.98
        )
        
        # Row 1: Overview Metrics
        ax1 = plt.subplot(3, 4, 1)
        self._plot_dh_kpi_summary(ax1, kpi)
        
        ax2 = plt.subplot(3, 4, 2)
        self._plot_network_topology(ax2, kpi, network_type="DH")
        
        ax3 = plt.subplot(3, 4, 3)
        self._plot_thermal_performance(ax3, kpi)
        
        ax4 = plt.subplot(3, 4, 4)
        self._plot_heat_demand_distribution(ax4, kpi)
        
        # Row 2: Network Analysis
        ax5 = plt.subplot(3, 4, 5)
        self._plot_hydraulic_performance(ax5, kpi)
        
        ax6 = plt.subplot(3, 4, 6)
        self._plot_network_metrics(ax6, kpi, network_type="DH")
        
        ax7 = plt.subplot(3, 4, 7)
        self._plot_efficiency_indicators(ax7, kpi, network_type="DH")
        
        ax8 = plt.subplot(3, 4, 8)
        self._plot_pipe_analysis(ax8, kpi)
        
        # Row 3: Economics & Summary
        ax9 = plt.subplot(3, 4, 9)
        self._plot_technical_specifications(ax9, kpi, network_type="DH")
        
        ax10 = plt.subplot(3, 4, 10)
        self._plot_performance_scores(ax10, kpi, network_type="DH")
        
        ax11 = plt.subplot(3, 4, 11)
        self._plot_heat_loss_analysis(ax11, kpi)
        
        ax12 = plt.subplot(3, 4, 12)
        self._plot_summary_statistics(ax12, kpi, scenario_name, network_type="DH")
        
        plt.tight_layout()
        
        # Save
        save_path = self.output_dir / f"{scenario_name}_dh_summary_dashboard.png"
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        
        print(f"✅ DH summary dashboard saved: {save_path}")
        return str(save_path)
    
    def create_hp_summary(
        self,
        kpi: Dict[str, Any],
        scenario_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create 12-panel summary dashboard for HP scenario.
        
        Args:
            kpi: KPI dictionary from simulation results
            scenario_name: Name of the scenario
            metadata: Optional metadata dictionary
        
        Returns:
            Path to saved PNG file
        """
        # Create figure with 12 subplots
        fig = plt.figure(figsize=(24, 18))
        
        # Main title
        fig.suptitle(
            f"Heat Pump Network - Summary Dashboard\n{scenario_name}",
            fontsize=20,
            fontweight="bold",
            y=0.98
        )
        
        # Row 1: Overview Metrics
        ax1 = plt.subplot(3, 4, 1)
        self._plot_hp_kpi_summary(ax1, kpi)
        
        ax2 = plt.subplot(3, 4, 2)
        self._plot_network_topology(ax2, kpi, network_type="HP")
        
        ax3 = plt.subplot(3, 4, 3)
        self._plot_voltage_profile(ax3, kpi)
        
        ax4 = plt.subplot(3, 4, 4)
        self._plot_load_distribution(ax4, kpi)
        
        # Row 2: Network Analysis
        ax5 = plt.subplot(3, 4, 5)
        self._plot_line_loading(ax5, kpi)
        
        ax6 = plt.subplot(3, 4, 6)
        self._plot_network_metrics(ax6, kpi, network_type="HP")
        
        ax7 = plt.subplot(3, 4, 7)
        self._plot_efficiency_indicators(ax7, kpi, network_type="HP")
        
        ax8 = plt.subplot(3, 4, 8)
        self._plot_transformer_analysis(ax8, kpi)
        
        # Row 3: Economics & Summary
        ax9 = plt.subplot(3, 4, 9)
        self._plot_technical_specifications(ax9, kpi, network_type="HP")
        
        ax10 = plt.subplot(3, 4, 10)
        self._plot_performance_scores(ax10, kpi, network_type="HP")
        
        ax11 = plt.subplot(3, 4, 11)
        self._plot_violation_analysis(ax11, kpi)
        
        ax12 = plt.subplot(3, 4, 12)
        self._plot_summary_statistics(ax12, kpi, scenario_name, network_type="HP")
        
        plt.tight_layout()
        
        # Save
        save_path = self.output_dir / f"{scenario_name}_hp_summary_dashboard.png"
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        
        print(f"✅ HP summary dashboard saved: {save_path}")
        return str(save_path)
    
    # ========================================================================
    # DH-Specific Panel Methods
    # ========================================================================
    
    def _plot_dh_kpi_summary(self, ax, kpi):
        """Plot DH key performance indicators."""
        metrics = [
            "Heat Supply\n(MWh)",
            "Pipe Length\n(km)",
            "Consumers",
            "Peak Load\n(kW)"
        ]
        values = [
            kpi.get("total_heat_supplied_mwh", 0),
            kpi.get("total_pipe_length_km", 0),
            kpi.get("num_consumers", 0),
            kpi.get("peak_heat_load_kw", 0)
        ]
        
        colors = ["#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
        bars = ax.bar(metrics, values, color=colors, alpha=0.8)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(values) * 0.01 if max(values) > 0 else 0.1,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=10
            )
        
        ax.set_title("Key Performance Indicators", fontsize=12, fontweight="bold")
        ax.set_ylabel("Value")
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, alpha=0.3, axis="y")
    
    def _plot_thermal_performance(self, ax, kpi):
        """Plot thermal performance metrics."""
        temps = ["Supply\nMin", "Supply\nAvg", "Return\nMin", "Return\nAvg"]
        values = [
            kpi.get("min_supply_temp_c", 0),
            kpi.get("avg_supply_temp_c", 0),
            kpi.get("min_return_temp_c", 0),
            kpi.get("avg_return_temp_c", 0)
        ]
        
        colors = [NETWORK_COLORS['supply_pipe'], NETWORK_COLORS['supply_pipe'],
                  NETWORK_COLORS['return_pipe'], NETWORK_COLORS['return_pipe']]
        bars = ax.bar(temps, values, color=colors, alpha=0.7)
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 2,
                f"{value:.1f}°C",
                ha="center",
                va="bottom",
                fontsize=9
            )
        
        ax.set_title("Thermal Performance", fontsize=12, fontweight="bold")
        ax.set_ylabel("Temperature (°C)")
        ax.grid(True, alpha=0.3, axis="y")
    
    def _plot_hydraulic_performance(self, ax, kpi):
        """Plot hydraulic performance metrics."""
        metrics = ["Max ΔP\n(bar)", "Avg ΔP\n(bar)", "Pump Energy\n(kWh)"]
        values = [
            kpi.get("max_pressure_drop_bar", 0),
            kpi.get("avg_pressure_drop_bar", 0),
            kpi.get("pump_energy_kwh", 0) / 100  # Scale for visibility
        ]
        
        colors = ["#e74c3c", "#f39c12", "#3498db"]
        bars = ax.bar(metrics, values, color=colors, alpha=0.8)
        
        labels = [
            f"{kpi.get('max_pressure_drop_bar', 0):.3f}",
            f"{kpi.get('avg_pressure_drop_bar', 0):.3f}",
            f"{kpi.get('pump_energy_kwh', 0):.0f}"
        ]
        
        for bar, label in zip(bars, labels):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(values) * 0.02 if max(values) > 0 else 0.01,
                label,
                ha="center",
                va="bottom",
                fontsize=9
            )
        
        ax.set_title("Hydraulic Performance", fontsize=12, fontweight="bold")
        ax.set_ylabel("Value")
        ax.grid(True, alpha=0.3, axis="y")
    
    def _plot_heat_loss_analysis(self, ax, kpi):
        """Plot heat loss analysis."""
        loss_kwh = kpi.get("network_heat_loss_kwh", 0)
        loss_pct = kpi.get("heat_loss_percentage", 0)
        total_heat_kwh = kpi.get("total_heat_supplied_mwh", 0) * 1000
        
        # Pie chart
        if total_heat_kwh > 0:
            delivered = total_heat_kwh - loss_kwh
            sizes = [delivered, loss_kwh]
            labels = [f"Delivered\n({delivered:.0f} kWh)", f"Losses\n({loss_kwh:.0f} kWh)"]
            colors = [NETWORK_COLORS['normal'], NETWORK_COLORS['critical']]
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title(f"Heat Loss Analysis\nTotal: {loss_pct:.1f}%", fontsize=12, fontweight="bold")
        else:
            ax.text(0.5, 0.5, "No heat loss data", ha="center", va="center", transform=ax.transAxes)
            ax.set_title("Heat Loss Analysis", fontsize=12, fontweight="bold")
    
    def _plot_pipe_analysis(self, ax, kpi):
        """Plot pipe network analysis."""
        metrics = ["Junctions", "Pipes", "Total Length\n(km)"]
        values = [
            kpi.get("num_junctions", 0),
            kpi.get("num_pipes", 0),
            kpi.get("total_pipe_length_km", 0)
        ]
        
        colors = ["#3498db", "#e74c3c", "#2ecc71"]
        bars = ax.bar(metrics, values, color=colors, alpha=0.8)
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(values) * 0.02 if max(values) > 0 else 0.1,
                f"{value:.0f}",
                ha="center",
                va="bottom",
                fontsize=9
            )
        
        ax.set_title("Network Components", fontsize=12, fontweight="bold")
        ax.set_ylabel("Count / Length")
        ax.grid(True, alpha=0.3, axis="y")
    
    # ========================================================================
    # HP-Specific Panel Methods
    # ========================================================================
    
    def _plot_hp_kpi_summary(self, ax, kpi):
        """Plot HP key performance indicators."""
        metrics = [
            "Total Load\n(MW)",
            "Lines",
            "Loads",
            "Losses\n(%)"
        ]
        values = [
            kpi.get("total_load_mw", 0),
            kpi.get("num_lines", 0),
            kpi.get("num_loads", 0),
            kpi.get("loss_percentage", 0)
        ]
        
        colors = ["#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
        bars = ax.bar(metrics, values, color=colors, alpha=0.8)
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(values) * 0.02 if max(values) > 0 else 0.1,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=10
            )
        
        ax.set_title("Key Performance Indicators", fontsize=12, fontweight="bold")
        ax.set_ylabel("Value")
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, alpha=0.3, axis="y")
    
    def _plot_voltage_profile(self, ax, kpi):
        """Plot voltage profile metrics."""
        metrics = ["Min V\n(pu)", "Avg V\n(pu)", "Max V\n(pu)"]
        values = [
            kpi.get("min_voltage_pu", 0),
            kpi.get("avg_voltage_pu", 0),
            kpi.get("max_voltage_pu", 0)
        ]
        
        # Color code by acceptability
        colors = []
        for v in values:
            if v < 0.95 or v > 1.05:
                colors.append(NETWORK_COLORS['critical'])
            elif v < 0.98 or v > 1.02:
                colors.append(NETWORK_COLORS['warning'])
            else:
                colors.append(NETWORK_COLORS['normal'])
        
        bars = ax.bar(metrics, values, color=colors, alpha=0.8)
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.01,
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=9
            )
        
        # Add acceptable range lines
        ax.axhline(y=0.95, color='red', linestyle='--', alpha=0.5, linewidth=1)
        ax.axhline(y=1.05, color='red', linestyle='--', alpha=0.5, linewidth=1)
        
        ax.set_title("Voltage Profile", fontsize=12, fontweight="bold")
        ax.set_ylabel("Voltage (pu)")
        ax.set_ylim([0.9, 1.1])
        ax.grid(True, alpha=0.3, axis="y")
    
    def _plot_line_loading(self, ax, kpi):
        """Plot line loading metrics."""
        metrics = ["Max Loading\n(%)", "Avg Loading\n(%)", "Overloaded\nLines"]
        values = [
            kpi.get("max_line_loading_pct", 0),
            kpi.get("avg_line_loading_pct", 0),
            kpi.get("overloaded_lines", 0)
        ]
        
        colors = [
            NETWORK_COLORS['critical'] if values[0] > 100 else NETWORK_COLORS['warning'] if values[0] > 80 else NETWORK_COLORS['normal'],
            NETWORK_COLORS['warning'] if values[1] > 60 else NETWORK_COLORS['normal'],
            NETWORK_COLORS['critical'] if values[2] > 0 else NETWORK_COLORS['normal']
        ]
        
        bars = ax.bar(metrics, values, color=colors, alpha=0.8)
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(values) * 0.02 if max(values) > 0 else 1,
                f"{value:.1f}",
                ha="center",
                va="bottom",
                fontsize=9
            )
        
        ax.set_title("Line Loading", fontsize=12, fontweight="bold")
        ax.set_ylabel("Value")
        ax.grid(True, alpha=0.3, axis="y")
    
    def _plot_transformer_analysis(self, ax, kpi):
        """Plot transformer analysis."""
        loading = kpi.get("transformer_loading_pct", 0)
        overloaded = kpi.get("transformer_overloaded", False)
        
        # Gauge-style visualization
        color = NETWORK_COLORS['critical'] if overloaded else NETWORK_COLORS['warning'] if loading > 80 else NETWORK_COLORS['normal']
        
        bars = ax.barh(["Transformer\nLoading"], [loading], color=color, alpha=0.8)
        
        ax.text(loading + 2, 0, f"{loading:.1f}%", va="center", fontsize=12, fontweight="bold")
        ax.axvline(x=100, color='red', linestyle='--', alpha=0.5, linewidth=2, label="Max Capacity")
        
        ax.set_title("Transformer Analysis", fontsize=12, fontweight="bold")
        ax.set_xlabel("Loading (%)")
        ax.set_xlim([0, max(120, loading + 10)])
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="x")
    
    def _plot_violation_analysis(self, ax, kpi):
        """Plot violation analysis."""
        voltage_violations = kpi.get("voltage_violations", 0)
        overloaded_lines = kpi.get("overloaded_lines", 0)
        transformer_overloaded = 1 if kpi.get("transformer_overloaded", False) else 0
        
        metrics = ["Voltage\nViolations", "Overloaded\nLines", "Transformer\nOverload"]
        values = [voltage_violations, overloaded_lines, transformer_overloaded]
        
        colors = [NETWORK_COLORS['critical'] if v > 0 else NETWORK_COLORS['normal'] for v in values]
        bars = ax.bar(metrics, values, color=colors, alpha=0.8)
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.1,
                f"{int(value)}",
                ha="center",
                va="bottom",
                fontsize=12,
                fontweight="bold"
            )
        
        ax.set_title("Violation Analysis", fontsize=12, fontweight="bold")
        ax.set_ylabel("Count")
        ax.grid(True, alpha=0.3, axis="y")
    
    def _plot_load_distribution(self, ax, kpi):
        """Plot load distribution."""
        total_load_mw = kpi.get("total_load_mw", 0)
        total_losses_mw = kpi.get("total_losses_mw", 0)
        delivered_mw = total_load_mw - total_losses_mw
        
        # Pie chart
        if total_load_mw > 0:
            sizes = [delivered_mw, total_losses_mw]
            labels = [f"Delivered\n({delivered_mw:.4f} MW)", f"Losses\n({total_losses_mw:.4f} MW)"]
            colors = [NETWORK_COLORS['normal'], NETWORK_COLORS['critical']]
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.2f%%', startangle=90)
            ax.set_title("Load Distribution", fontsize=12, fontweight="bold")
        else:
            ax.text(0.5, 0.5, "No load data", ha="center", va="center", transform=ax.transAxes)
            ax.set_title("Load Distribution", fontsize=12, fontweight="bold")
    
    # ========================================================================
    # Common Panel Methods
    # ========================================================================
    
    def _plot_network_topology(self, ax, kpi, network_type="DH"):
        """Plot network topology schematic."""
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        
        if network_type == "DH":
            # Plant
            ax.scatter(5, 8, s=300, color=NETWORK_COLORS['chp_plant'], marker="s",
                      edgecolors="black", linewidth=2, label="CHP Plant")
            
            # Main network
            ax.plot([2, 8], [6, 6], color=NETWORK_COLORS['supply_pipe'],
                   linewidth=4, alpha=0.8, label="Main Network")
            
            # Service connections
            for i in range(7):
                x = 2 + i * 1
                ax.plot([x, x], [6, 4], color=NETWORK_COLORS['service_connection'],
                       linewidth=2, alpha=0.8, linestyle="--")
                ax.scatter(x, 4, s=100, color=NETWORK_COLORS['heat_consumer'], alpha=0.7)
            
            # Plant connection
            ax.plot([5, 5], [8, 6], color=NETWORK_COLORS['supply_pipe'], linewidth=3, alpha=0.8)
        else:  # HP
            # Substation
            ax.scatter(5, 8, s=300, color=NETWORK_COLORS['substation'], marker="s",
                      edgecolors="black", linewidth=2, label="Substation")
            
            # Power lines
            ax.plot([2, 8], [6, 6], color=NETWORK_COLORS['power_line'],
                   linewidth=4, alpha=0.8, label="Power Lines")
            
            # HP loads
            for i in range(7):
                x = 2 + i * 1
                ax.plot([x, x], [6, 4], color=NETWORK_COLORS['power_line'],
                       linewidth=2, alpha=0.6)
                ax.scatter(x, 4, s=100, color=NETWORK_COLORS['hp_load'], alpha=0.7)
            
            # Substation connection
            ax.plot([5, 5], [8, 6], color=NETWORK_COLORS['power_line'], linewidth=3, alpha=0.8)
        
        ax.set_title("Network Topology", fontsize=12, fontweight="bold")
        ax.set_xlabel("Schematic Representation")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_aspect("equal")
    
    def _plot_heat_demand_distribution(self, ax, kpi):
        """Plot heat demand distribution (DH)."""
        total_heat = kpi.get("total_heat_supplied_mwh", 0)
        num_consumers = kpi.get("num_consumers", 0)
        
        if num_consumers > 0:
            avg_heat = total_heat / num_consumers
            
            labels = ["Total Heat\nDemand", "Average per\nConsumer"]
            sizes = [total_heat, avg_heat]
            colors = ["#ff6b6b", "#4ecdc4"]
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title(f"Heat Demand Distribution\n({total_heat:.2f} MWh total)", 
                        fontsize=12, fontweight="bold")
        else:
            ax.text(0.5, 0.5, "No consumer data", ha="center", va="center", transform=ax.transAxes)
            ax.set_title("Heat Demand Distribution", fontsize=12, fontweight="bold")
    
    def _plot_network_metrics(self, ax, kpi, network_type="DH"):
        """Plot network metrics."""
        if network_type == "DH":
            metrics = ["Junctions", "Pipes", "Consumers"]
            values = [
                kpi.get("num_junctions", 0),
                kpi.get("num_pipes", 0),
                kpi.get("num_consumers", 0)
            ]
        else:  # HP
            metrics = ["Buses", "Lines", "Loads"]
            values = [
                kpi.get("num_buses", 0),
                kpi.get("num_lines", 0),
                kpi.get("num_loads", 0)
            ]
        
        colors = ["#3498db", "#e74c3c", "#2ecc71"]
        bars = ax.bar(metrics, values, color=colors, alpha=0.8)
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(values) * 0.02 if max(values) > 0 else 0.5,
                f"{int(value)}",
                ha="center",
                va="bottom",
                fontsize=10
            )
        
        ax.set_title("Network Metrics", fontsize=12, fontweight="bold")
        ax.set_ylabel("Count")
        ax.grid(True, alpha=0.3, axis="y")
    
    def _plot_efficiency_indicators(self, ax, kpi, network_type="DH"):
        """Plot efficiency indicators."""
        if network_type == "DH":
            heat_loss_pct = kpi.get("heat_loss_percentage", 0)
            efficiency = 100 - heat_loss_pct
            
            metrics = ["Network\nEfficiency", "Heat\nLosses"]
            values = [efficiency, heat_loss_pct]
            colors = [NETWORK_COLORS['normal'], NETWORK_COLORS['critical']]
        else:  # HP
            loss_pct = kpi.get("loss_percentage", 0)
            efficiency = 100 - loss_pct
            
            metrics = ["Grid\nEfficiency", "Losses"]
            values = [efficiency, loss_pct]
            colors = [NETWORK_COLORS['normal'], NETWORK_COLORS['critical']]
        
        bars = ax.bar(metrics, values, color=colors, alpha=0.8)
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 2,
                f"{value:.1f}%",
                ha="center",
                va="bottom",
                fontsize=10
            )
        
        ax.set_title("Efficiency Indicators", fontsize=12, fontweight="bold")
        ax.set_ylabel("Percentage (%)")
        ax.set_ylim([0, 105])
        ax.grid(True, alpha=0.3, axis="y")
    
    def _plot_technical_specifications(self, ax, kpi, network_type="DH"):
        """Plot technical specifications."""
        ax.axis("off")
        
        if network_type == "DH":
            specs_text = "Technical Specifications\n\n"
            specs_text += f"Supply Temperature: {kpi.get('avg_supply_temp_c', 0):.1f}°C\n"
            specs_text += f"Return Temperature: {kpi.get('min_return_temp_c', 0):.1f}°C\n"
            specs_text += f"Max Pressure Drop: {kpi.get('max_pressure_drop_bar', 0):.3f} bar\n"
            specs_text += f"Total Pipe Length: {kpi.get('total_pipe_length_km', 0):.2f} km\n"
            specs_text += f"Number of Junctions: {kpi.get('num_junctions', 0)}\n"
            specs_text += f"Number of Pipes: {kpi.get('num_pipes', 0)}\n"
            specs_text += f"Heat Consumers: {kpi.get('num_consumers', 0)}\n"
        else:  # HP
            specs_text = "Technical Specifications\n\n"
            specs_text += f"Voltage Range: {kpi.get('min_voltage_pu', 0):.3f} - {kpi.get('max_voltage_pu', 0):.3f} pu\n"
            specs_text += f"Max Line Loading: {kpi.get('max_line_loading_pct', 0):.1f}%\n"
            specs_text += f"Total Load: {kpi.get('total_load_mw', 0):.4f} MW\n"
            specs_text += f"Total Losses: {kpi.get('total_losses_mw', 0):.4f} MW\n"
            specs_text += f"Number of Buses: {kpi.get('num_buses', 0)}\n"
            specs_text += f"Number of Lines: {kpi.get('num_lines', 0)}\n"
            specs_text += f"HP Loads: {kpi.get('num_loads', 0)}\n"
        
        ax.text(
            0.05,
            0.95,
            specs_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            family="monospace",
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.8)
        )
    
    def _plot_performance_scores(self, ax, kpi, network_type="DH"):
        """Plot performance scores."""
        if network_type == "DH":
            # Calculate scores based on DH performance
            thermal_score = min(100, 100 - kpi.get("heat_loss_percentage", 10))
            hydraulic_score = min(100, (1 - kpi.get("max_pressure_drop_bar", 1) / 2) * 100)
            efficiency_score = thermal_score
            
            scores = ["Thermal\nPerformance", "Hydraulic\nPerformance", "Overall\nEfficiency"]
            values = [thermal_score, hydraulic_score, efficiency_score]
        else:  # HP
            # Calculate scores based on HP performance
            voltage_score = 100 if kpi.get("voltage_violations", 0) == 0 else 50
            loading_score = min(100, (1 - kpi.get("max_line_loading_pct", 0) / 100) * 100)
            efficiency_score = 100 - kpi.get("loss_percentage", 0)
            
            scores = ["Voltage\nProfile", "Line\nLoading", "Grid\nEfficiency"]
            values = [voltage_score, loading_score, efficiency_score]
        
        colors = [NETWORK_COLORS['normal'] if v > 80 else 
                 NETWORK_COLORS['warning'] if v > 60 else 
                 NETWORK_COLORS['critical'] for v in values]
        
        bars = ax.barh(scores, values, color=colors, alpha=0.8)
        
        for bar, value in zip(bars, values):
            width = bar.get_width()
            ax.text(
                width + 2,
                bar.get_y() + bar.get_height() / 2.0,
                f"{value:.0f}%",
                ha="left",
                va="center",
                fontsize=10,
                fontweight="bold"
            )
        
        ax.set_title("Performance Scores", fontsize=12, fontweight="bold")
        ax.set_xlabel("Score (%)")
        ax.set_xlim([0, 110])
        ax.grid(True, alpha=0.3, axis="x")
    
    def _plot_summary_statistics(self, ax, kpi, scenario_name, network_type="DH"):
        """Plot summary statistics."""
        ax.axis("off")
        
        if network_type == "DH":
            summary_text = f"Summary - {scenario_name}\n\n"
            summary_text += "═" * 40 + "\n\n"
            summary_text += f"📊 Total Heat Demand: {kpi.get('total_heat_supplied_mwh', 0):.2f} MWh\n"
            summary_text += f"🏗️ Consumers: {kpi.get('num_consumers', 0)}\n"
            summary_text += f"📏 Network Length: {kpi.get('total_pipe_length_km', 0):.2f} km\n"
            summary_text += f"🌡️ Supply Temp: {kpi.get('avg_supply_temp_c', 0):.1f}°C\n"
            summary_text += f"💧 Max Pressure Drop: {kpi.get('max_pressure_drop_bar', 0):.3f} bar\n"
            summary_text += f"📉 Heat Losses: {kpi.get('heat_loss_percentage', 0):.1f}%\n"
            summary_text += f"⚡ Pump Energy: {kpi.get('pump_energy_kwh', 0):.0f} kWh\n\n"
            summary_text += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        else:  # HP
            summary_text = f"Summary - {scenario_name}\n\n"
            summary_text += "═" * 40 + "\n\n"
            summary_text += f"📊 Total Load: {kpi.get('total_load_mw', 0):.4f} MW\n"
            summary_text += f"🏗️ HP Loads: {kpi.get('num_loads', 0)}\n"
            summary_text += f"📏 Grid Lines: {kpi.get('num_lines', 0)}\n"
            summary_text += f"⚡ Voltage: {kpi.get('min_voltage_pu', 0):.3f} - {kpi.get('max_voltage_pu', 0):.3f} pu\n"
            summary_text += f"📈 Max Line Loading: {kpi.get('max_line_loading_pct', 0):.1f}%\n"
            summary_text += f"📉 Grid Losses: {kpi.get('loss_percentage', 0):.2f}%\n"
            summary_text += f"⚠️ Violations: {kpi.get('voltage_violations', 0)}\n\n"
            summary_text += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        
        ax.text(
            0.05,
            0.95,
            summary_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            family="monospace",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.9)
        )

