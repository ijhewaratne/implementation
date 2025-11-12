"""
DH vs HP Comparison Dashboard Generator.

Creates side-by-side comparison dashboards with:
- Economic metrics (LCoH, CAPEX, OPEX)
- Environmental metrics (CO2 emissions)
- Technical feasibility scores
- Performance comparisons
- Network efficiency metrics

Provides decision support for choosing between DH and HP scenarios.
"""

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


class ComparisonDashboard:
    """
    Create DH vs HP comparison dashboards.
    
    Generates visual comparisons to support decision-making between
    district heating and heat pump scenarios.
    """
    
    def __init__(self, output_dir: str = "results_test/visualizations/dashboards"):
        """
        Initialize the comparison dashboard generator.
        
        Args:
            output_dir: Directory to save generated dashboards
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set plotting style
        plt.style.use("default")
        sns.set_palette("husl")
    
    def create_comparison(
        self,
        dh_kpi: Dict[str, Any],
        hp_kpi: Dict[str, Any],
        dh_scenario_name: str,
        hp_scenario_name: str
    ) -> str:
        """
        Create comprehensive DH vs HP comparison dashboard.
        
        Args:
            dh_kpi: KPI dictionary from DH simulation
            hp_kpi: KPI dictionary from HP simulation
            dh_scenario_name: Name of DH scenario
            hp_scenario_name: Name of HP scenario
        
        Returns:
            Path to saved PNG file
        """
        # Create figure with 6 comparison panels (2 rows × 3 columns)
        global fig
        fig = plt.figure(figsize=(18, 12))
        
        # Main title
        fig.suptitle(
            f"Scenario Comparison: District Heating vs Heat Pumps\n"
            f"DH: {dh_scenario_name} | HP: {hp_scenario_name}",
            fontsize=18,
            fontweight="bold",
            y=0.98
        )
        
        # Row 1: Economic & Environmental
        ax1 = plt.subplot(2, 3, 1)
        self._plot_lcoh_comparison(ax1, dh_kpi, hp_kpi)
        
        ax2 = plt.subplot(2, 3, 2)
        self._plot_co2_comparison(ax2, dh_kpi, hp_kpi)
        
        ax3 = plt.subplot(2, 3, 3)
        self._plot_cost_breakdown(ax3, dh_kpi, hp_kpi)
        
        # Row 2: Technical & Performance
        ax4 = plt.subplot(2, 3, 4)
        self._plot_technical_metrics(ax4, dh_kpi, hp_kpi)
        
        ax5 = plt.subplot(2, 3, 5)
        self._plot_efficiency_comparison(ax5, dh_kpi, hp_kpi)
        
        ax6 = plt.subplot(2, 3, 6)
        self._plot_recommendation(ax6, dh_kpi, hp_kpi)
        
        plt.tight_layout()
        
        # Save
        save_path = self.output_dir / f"comparison_{dh_scenario_name}_vs_{hp_scenario_name}.png"
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        
        print(f"✅ Comparison dashboard saved: {save_path}")
        return str(save_path)
    
    # ========================================================================
    # Comparison Panel Methods
    # ========================================================================
    
    def _plot_lcoh_comparison(self, ax, dh_kpi, hp_kpi):
        """Plot Levelized Cost of Heat comparison."""
        scenarios = ["District\nHeating", "Heat\nPumps"]
        
        # Get LCoH values (assume from parent KPI calculation)
        # These would typically be calculated by kpi_calculator.py
        dh_lcoh = dh_kpi.get("lcoh_eur_per_mwh", 0)
        hp_lcoh = hp_kpi.get("lcoh_eur_per_mwh", 0)
        
        values = [dh_lcoh, hp_lcoh]
        colors = [NETWORK_COLORS['supply_pipe'], NETWORK_COLORS['lv_bus']]
        
        bars = ax.bar(scenarios, values, color=colors, alpha=0.8, width=0.6)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(values) * 0.02 if max(values) > 0 else 1,
                f"{value:.1f}€/MWh",
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=12
            )
        
        # Highlight winner
        if dh_lcoh > 0 and hp_lcoh > 0:
            winner_idx = np.argmin(values)
            bars[winner_idx].set_edgecolor(NETWORK_COLORS['normal'])
            bars[winner_idx].set_linewidth(3)
        
        ax.set_title("Levelized Cost of Heat (LCoH)", fontsize=13, fontweight="bold")
        ax.set_ylabel("Cost (€/MWh)")
        ax.grid(True, alpha=0.3, axis="y")
    
    def _plot_co2_comparison(self, ax, dh_kpi, hp_kpi):
        """Plot CO2 emissions comparison."""
        scenarios = ["District\nHeating", "Heat\nPumps"]
        
        # Get CO2 values
        dh_co2 = dh_kpi.get("co2_t_per_a", 0)
        hp_co2 = hp_kpi.get("co2_t_per_a", 0)
        
        values = [dh_co2, hp_co2]
        colors = [NETWORK_COLORS['supply_pipe'], NETWORK_COLORS['lv_bus']]
        
        bars = ax.bar(scenarios, values, color=colors, alpha=0.8, width=0.6)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(values) * 0.02 if max(values) > 0 else 1,
                f"{value:.1f} t/a",
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=12
            )
        
        # Highlight winner (lower is better)
        if dh_co2 > 0 and hp_co2 > 0:
            winner_idx = np.argmin(values)
            bars[winner_idx].set_edgecolor(NETWORK_COLORS['normal'])
            bars[winner_idx].set_linewidth(3)
        
        ax.set_title("Annual CO₂ Emissions", fontsize=13, fontweight="bold")
        ax.set_ylabel("Emissions (t CO₂/year)")
        ax.grid(True, alpha=0.3, axis="y")
    
    def _plot_cost_breakdown(self, ax, dh_kpi, hp_kpi):
        """Plot cost breakdown comparison."""
        # Simplified cost breakdown (would be more detailed in production)
        categories = ["CAPEX", "OPEX", "Energy"]
        
        # DH costs (estimated based on network size)
        dh_capex = dh_kpi.get("total_pipe_length_km", 0) * 800  # €800/meter * 1000m/km
        dh_opex = dh_capex * 0.01 * 20  # 1% per year for 20 years
        dh_energy = dh_kpi.get("total_heat_supplied_mwh", 0) * 1000 * 0.07  # biomass price
        
        # HP costs (estimated based on number of loads)
        hp_capex = hp_kpi.get("num_loads", 0) * 14000  # €14,000 per HP
        hp_opex = hp_capex * 0.01 * 20
        hp_energy = hp_kpi.get("total_load_mw", 0) * 8760 * 1000 * 0.35  # electricity price
        
        dh_costs = [dh_capex, dh_opex, dh_energy]
        hp_costs = [hp_capex, hp_opex, hp_energy]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, dh_costs, width, label="District Heating",
                      color=NETWORK_COLORS['supply_pipe'], alpha=0.8)
        bars2 = ax.bar(x + width/2, hp_costs, width, label="Heat Pumps",
                      color=NETWORK_COLORS['lv_bus'], alpha=0.8)
        
        ax.set_title("Cost Breakdown Comparison", fontsize=13, fontweight="bold")
        ax.set_ylabel("Cost (€)")
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")
        
        # Format y-axis for large numbers
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k' if x >= 1000 else f'{x:.0f}'))
    
    def _plot_technical_metrics(self, ax, dh_kpi, hp_kpi):
        """Plot technical metrics comparison."""
        # Normalize different metrics to 0-100 scale for comparison
        
        # DH metrics (normalized)
        dh_thermal_eff = 100 - dh_kpi.get("heat_loss_percentage", 10)
        dh_hydraulic = min(100, (1 - dh_kpi.get("max_pressure_drop_bar", 1) / 2) * 100)
        dh_reliability = 95  # Assumed high for DH
        
        # HP metrics (normalized)
        hp_voltage = 100 if hp_kpi.get("voltage_violations", 0) == 0 else 60
        hp_loading = min(100, (1 - hp_kpi.get("max_line_loading_pct", 0) / 100) * 100)
        hp_reliability = 90  # Slightly lower for HP (more components)
        
        metrics = ["Efficiency", "Network\nPerformance", "Reliability"]
        dh_values = [dh_thermal_eff, dh_hydraulic, dh_reliability]
        hp_values = [hp_voltage, hp_loading, hp_reliability]
        
        x = np.arange(len(metrics))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, dh_values, width, label="District Heating",
                      color=NETWORK_COLORS['supply_pipe'], alpha=0.8)
        bars2 = ax.bar(x + width/2, hp_values, width, label="Heat Pumps",
                      color=NETWORK_COLORS['lv_bus'], alpha=0.8)
        
        ax.set_title("Technical Performance Comparison", fontsize=13, fontweight="bold")
        ax.set_ylabel("Score (0-100)")
        ax.set_xticks(x)
        ax.set_xticklabels(metrics)
        ax.set_ylim([0, 105])
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")
    
    def _plot_efficiency_comparison(self, ax, dh_kpi, hp_kpi):
        """Plot efficiency comparison (pie charts)."""
        # Create 2 pie charts side by side
        
        # DH efficiency
        dh_heat_loss = dh_kpi.get("heat_loss_percentage", 10)
        dh_delivered = 100 - dh_heat_loss
        
        # HP efficiency
        hp_loss = hp_kpi.get("loss_percentage", 3)
        hp_delivered = 100 - hp_loss
        
        # Create subplots within this panel
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        
        # Clear the current axes and create two subaxes
        ax.axis("off")
        
        # Create manual positioning for two pie charts
        ax_dh = fig.add_axes([ax.get_position().x0, ax.get_position().y0 + 0.05,
                              ax.get_position().width / 2.2, ax.get_position().height - 0.1])
        ax_hp = fig.add_axes([ax.get_position().x0 + ax.get_position().width / 2,
                              ax.get_position().y0 + 0.05,
                              ax.get_position().width / 2.2, ax.get_position().height - 0.1])
        
        # DH pie chart
        colors_dh = [NETWORK_COLORS['normal'], NETWORK_COLORS['critical']]
        ax_dh.pie([dh_delivered, dh_heat_loss],
                  labels=[f"Delivered\n{dh_delivered:.1f}%", f"Losses\n{dh_heat_loss:.1f}%"],
                  colors=colors_dh, autopct='%1.1f%%', startangle=90)
        ax_dh.set_title("DH Efficiency", fontsize=11, fontweight="bold")
        
        # HP pie chart
        colors_hp = [NETWORK_COLORS['normal'], NETWORK_COLORS['critical']]
        ax_hp.pie([hp_delivered, hp_loss],
                  labels=[f"Delivered\n{hp_delivered:.1f}%", f"Losses\n{hp_loss:.1f}%"],
                  colors=colors_hp, autopct='%1.1f%%', startangle=90)
        ax_hp.set_title("HP Efficiency", fontsize=11, fontweight="bold")
        
        # Add main title
        ax.text(0.5, 0.95, "Network Efficiency Comparison",
                ha="center", va="top", fontsize=13, fontweight="bold",
                transform=ax.transAxes)
    
    def _plot_recommendation(self, ax, dh_kpi, hp_kpi):
        """Plot recommendation summary."""
        ax.axis("off")
        
        # Calculate scores
        dh_economic = self._calculate_economic_score(dh_kpi)
        dh_environmental = self._calculate_environmental_score(dh_kpi)
        dh_technical = self._calculate_technical_score(dh_kpi, "DH")
        dh_total = (dh_economic + dh_environmental + dh_technical) / 3
        
        hp_economic = self._calculate_economic_score(hp_kpi)
        hp_environmental = self._calculate_environmental_score(hp_kpi)
        hp_technical = self._calculate_technical_score(hp_kpi, "HP")
        hp_total = (hp_economic + hp_environmental + hp_technical) / 3
        
        # Determine recommendation
        if dh_total > hp_total:
            recommendation = "DISTRICT HEATING"
            winner_color = NETWORK_COLORS['supply_pipe']
            difference = dh_total - hp_total
        else:
            recommendation = "HEAT PUMPS"
            winner_color = NETWORK_COLORS['lv_bus']
            difference = hp_total - dh_total
        
        # Create recommendation text
        rec_text = "RECOMMENDATION\n\n"
        rec_text += "═" * 40 + "\n\n"
        rec_text += f"Preferred Solution:\n"
        rec_text += f"  → {recommendation}\n\n"
        rec_text += f"Overall Scores:\n"
        rec_text += f"  District Heating: {dh_total:.1f}/100\n"
        rec_text += f"  Heat Pumps: {hp_total:.1f}/100\n\n"
        rec_text += f"Margin: {difference:.1f} points\n\n"
        rec_text += "Score Breakdown:\n"
        rec_text += f"  Economic:\n"
        rec_text += f"    DH: {dh_economic:.1f} | HP: {hp_economic:.1f}\n"
        rec_text += f"  Environmental:\n"
        rec_text += f"    DH: {dh_environmental:.1f} | HP: {hp_environmental:.1f}\n"
        rec_text += f"  Technical:\n"
        rec_text += f"    DH: {dh_technical:.1f} | HP: {hp_technical:.1f}\n\n"
        rec_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        
        ax.text(
            0.05,
            0.95,
            rec_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            family="monospace",
            bbox=dict(boxstyle="round", facecolor=winner_color, alpha=0.3, edgecolor=winner_color, linewidth=2)
        )
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _calculate_economic_score(self, kpi: Dict[str, Any]) -> float:
        """Calculate economic score (0-100, higher is better)."""
        lcoh = kpi.get("lcoh_eur_per_mwh", 100)
        
        # Lower LCoH is better, normalize around typical range (50-150 €/MWh)
        if lcoh <= 0:
            return 50
        
        score = max(0, min(100, (150 - lcoh) / 100 * 100))
        return score
    
    def _calculate_environmental_score(self, kpi: Dict[str, Any]) -> float:
        """Calculate environmental score (0-100, higher is better)."""
        co2 = kpi.get("co2_t_per_a", 100)
        
        # Lower CO2 is better, normalize around typical range (0-100 t/year)
        if co2 <= 0:
            return 50
        
        score = max(0, min(100, (100 - co2) / 100 * 100))
        return score
    
    def _calculate_technical_score(self, kpi: Dict[str, Any], network_type: str) -> float:
        """Calculate technical score (0-100, higher is better)."""
        if network_type == "DH":
            # DH technical score based on efficiency and hydraulics
            heat_loss = kpi.get("heat_loss_percentage", 10)
            pressure_drop = kpi.get("max_pressure_drop_bar", 1)
            
            efficiency_score = 100 - heat_loss
            hydraulic_score = min(100, (1 - pressure_drop / 2) * 100)
            
            score = (efficiency_score + hydraulic_score) / 2
        else:  # HP
            # HP technical score based on voltage and loading
            voltage_violations = kpi.get("voltage_violations", 0)
            max_loading = kpi.get("max_line_loading_pct", 0)
            
            voltage_score = 100 if voltage_violations == 0 else 60
            loading_score = min(100, (1 - max_loading / 100) * 100)
            
            score = (voltage_score + loading_score) / 2
        
        return max(0, min(100, score))
    
    def _plot_technical_comparison(self, ax, dh_kpi, hp_kpi):
        """Plot technical characteristics comparison."""
        # Key technical differences
        characteristics = ["Network\nLength", "Components", "Complexity", "Maintenance"]
        
        # Normalize values for comparison (0-100)
        dh_length = min(100, dh_kpi.get("total_pipe_length_km", 0) * 10)  # Scaled
        dh_components = min(100, dh_kpi.get("num_junctions", 0) + dh_kpi.get("num_pipes", 0))
        dh_complexity = 70  # Moderate complexity
        dh_maintenance = 60  # Higher maintenance needs
        
        hp_length = 20  # Minimal piping
        hp_components = min(100, hp_kpi.get("num_buses", 0) + hp_kpi.get("num_lines", 0))
        hp_complexity = 50  # Lower complexity
        hp_maintenance = 80  # Lower maintenance
        
        dh_values = [dh_length, dh_components, dh_complexity, dh_maintenance]
        hp_values = [hp_length, hp_components, hp_complexity, hp_maintenance]
        
        x = np.arange(len(characteristics))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, dh_values, width, label="District Heating",
                      color=NETWORK_COLORS['supply_pipe'], alpha=0.8)
        bars2 = ax.bar(x + width/2, hp_values, width, label="Heat Pumps",
                      color=NETWORK_COLORS['lv_bus'], alpha=0.8)
        
        ax.set_title("Technical Characteristics", fontsize=13, fontweight="bold")
        ax.set_ylabel("Normalized Score")
        ax.set_xticks(x)
        ax.set_xticklabels(characteristics)
        ax.set_ylim([0, 105])
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")


# Make fig accessible to _plot_efficiency_comparison
# This is a workaround for the nested axes creation
fig = None

