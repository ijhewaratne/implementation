#!/usr/bin/env python3
"""
Street Comparison Tool for DH vs HP Analysis
Interactive tool to select a street and compare DH vs HP KPIs
"""

import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import yaml
from typing import Dict, List, Optional, Tuple
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class StreetComparisonTool:
    """Interactive tool for comparing DH vs HP KPIs by street"""
    
    def __init__(self, data_dir: str = "processed"):
        self.data_dir = Path(data_dir)
        self.kpi_dir = self.data_dir / "kpi"
        self.lfa_dir = self.data_dir / "lfa"
        self.cha_dir = self.data_dir / "cha"
        self.dha_dir = self.data_dir / "dha"
        
        # Load available streets
        self.available_streets = self._load_available_streets()
        
    def _load_available_streets(self) -> List[str]:
        """Load list of available streets from KPI files"""
        streets = []
        
        if self.kpi_dir.exists():
            for kpi_file in self.kpi_dir.glob("kpi_report_*.json"):
                if kpi_file.name != "kpi_summary.json":
                    # Extract street name from filename
                    street_name = kpi_file.stem.replace("kpi_report_", "")
                    if street_name:  # Skip empty names
                        streets.append(street_name)
        
        return sorted(streets)
    
    def load_street_kpis(self, street_name: str) -> Optional[Dict]:
        """Load KPI data for a specific street"""
        kpi_file = self.kpi_dir / f"kpi_report_{street_name}.json"
        
        if not kpi_file.exists():
            return None
            
        try:
            with open(kpi_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading KPI data for {street_name}: {e}")
            return None
    
    def load_summary_kpis(self) -> Optional[Dict]:
        """Load summary KPI data"""
        summary_file = self.kpi_dir / "kpi_summary.json"
        
        if not summary_file.exists():
            return None
            
        try:
            with open(summary_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading summary KPI data: {e}")
            return None
    
    def create_comparison_chart(self, street_data: Dict) -> go.Figure:
        """Create comparison chart for DH vs HP metrics"""
        
        # Extract metrics
        hp_metrics = street_data.get('hp_metrics', {})
        dh_metrics = street_data.get('dh_metrics', {})
        
        # Define metrics to compare
        metrics = {
            'LCOH (€/MWh)': ('lcoh_eur_per_mwh', 'Lower is better'),
            'CO2 Emissions (t/a)': ('co2_t_per_a', 'Lower is better'),
            'CAPEX (€)': ('capex_eur', 'Lower is better'),
            'OPEX (€/year)': ('opex_eur', 'Lower is better'),
            'Energy Costs (€/year)': ('energy_costs_eur', 'Lower is better')
        }
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=list(metrics.keys()),
            specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}, {"type": "indicator"}]]
        )
        
        # Add bar charts for each metric
        for i, (metric_name, (key, description)) in enumerate(metrics.items()):
            row = (i // 3) + 1
            col = (i % 3) + 1
            
            hp_value = hp_metrics.get(key, 0)
            dh_value = dh_metrics.get(key, 0)
            
            fig.add_trace(
                go.Bar(
                    name='Heat Pump',
                    x=['Heat Pump'],
                    y=[hp_value],
                    marker_color='lightblue',
                    showlegend=(i == 0)
                ),
                row=row, col=col
            )
            
            fig.add_trace(
                go.Bar(
                    name='District Heating',
                    x=['District Heating'],
                    y=[dh_value],
                    marker_color='orange',
                    showlegend=(i == 0)
                ),
                row=row, col=col
            )
        
        # Add recommendation indicator
        recommendation = self._get_recommendation(hp_metrics, dh_metrics)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=recommendation['score'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Recommendation"},
                delta={'reference': 50},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': recommendation['color']},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 100], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ),
            row=2, col=3
        )
        
        fig.update_layout(
            height=600,
            title=f"DH vs HP Comparison - {street_data.get('street_name', 'Unknown Street')}",
            showlegend=True
        )
        
        return fig
    
    def _get_recommendation(self, hp_metrics: Dict, dh_metrics: Dict) -> Dict:
        """Calculate recommendation score and color"""
        
        # Simple scoring based on LCOH (primary metric)
        hp_lcoh = hp_metrics.get('lcoh_eur_per_mwh', 0)
        dh_lcoh = dh_metrics.get('lcoh_eur_per_mwh', 0)
        
        if hp_lcoh == 0 and dh_lcoh == 0:
            return {'score': 50, 'color': 'gray', 'text': 'No data'}
        
        if dh_lcoh < hp_lcoh:
            # DH is better
            score = min(100, 50 + (hp_lcoh - dh_lcoh) / dh_lcoh * 50)
            return {'score': score, 'color': 'green', 'text': 'DH Recommended'}
        else:
            # HP is better
            score = max(0, 50 - (dh_lcoh - hp_lcoh) / hp_lcoh * 50)
            return {'score': score, 'color': 'red', 'text': 'HP Recommended'}
    
    def create_summary_table(self, street_data: Dict) -> pd.DataFrame:
        """Create summary comparison table"""
        
        hp_metrics = street_data.get('hp_metrics', {})
        dh_metrics = street_data.get('dh_metrics', {})
        
        # Define metrics with units
        metrics = {
            'LCOH': ('lcoh_eur_per_mwh', '€/MWh'),
            'CO2 Emissions': ('co2_t_per_a', 't/a'),
            'CAPEX': ('capex_eur', '€'),
            'OPEX': ('opex_eur', '€/year'),
            'Energy Costs': ('energy_costs_eur', '€/year')
        }
        
        # Create comparison table
        data = []
        for metric_name, (key, unit) in metrics.items():
            hp_value = hp_metrics.get(key, 0)
            dh_value = dh_metrics.get(key, 0)
            
            # Calculate difference
            if hp_value > 0 and dh_value > 0:
                diff_pct = ((dh_value - hp_value) / hp_value) * 100
                better = "DH" if dh_value < hp_value else "HP"
            else:
                diff_pct = 0
                better = "N/A"
            
            data.append({
                'Metric': metric_name,
                'Unit': unit,
                'Heat Pump': f"{hp_value:,.0f}" if hp_value > 0 else "N/A",
                'District Heating': f"{dh_value:,.0f}" if dh_value > 0 else "N/A",
                'Difference (%)': f"{diff_pct:+.1f}%" if diff_pct != 0 else "N/A",
                'Better Option': better
            })
        
        return pd.DataFrame(data)
    
    def run_streamlit_app(self):
        """Run the Streamlit web application"""
        
        st.set_page_config(
            page_title="Street Comparison Tool",
            page_icon="🏘️",
            layout="wide"
        )
        
        st.title("🏘️ Street Comparison Tool")
        st.markdown("Compare District Heating vs Heat Pump KPIs for different streets")
        
        # Sidebar for street selection
        st.sidebar.header("Street Selection")
        
        if not self.available_streets:
            st.error("No street data available. Please run the analysis first.")
            return
        
        selected_street = st.sidebar.selectbox(
            "Select a street:",
            self.available_streets,
            index=0
        )
        
        # Load and display data
        street_data = self.load_street_kpis(selected_street)
        
        if not street_data:
            st.error(f"No KPI data found for {selected_street}")
            return
        
        # Display street information
        st.header(f"📊 Analysis for: {selected_street}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Analysis Date",
                street_data.get('analysis_date', 'Unknown')[:10]
            )
        
        with col2:
            hp_lcoh = street_data.get('hp_metrics', {}).get('lcoh_eur_per_mwh', 0)
            st.metric(
                "HP LCOH",
                f"{hp_lcoh:.1f} €/MWh"
            )
        
        with col3:
            dh_lcoh = street_data.get('dh_metrics', {}).get('lcoh_eur_per_mwh', 0)
            st.metric(
                "DH LCOH",
                f"{dh_lcoh:.1f} €/MWh"
            )
        
        # Create comparison chart
        st.subheader("📈 Comparison Chart")
        fig = self.create_comparison_chart(street_data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Create summary table
        st.subheader("📋 Summary Table")
        summary_df = self.create_summary_table(street_data)
        st.dataframe(summary_df, use_container_width=True)
        
        # Recommendation
        st.subheader("🎯 Recommendation")
        hp_metrics = street_data.get('hp_metrics', {})
        dh_metrics = street_data.get('dh_metrics', {})
        recommendation = self._get_recommendation(hp_metrics, dh_metrics)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Recommendation",
                recommendation['text'],
                delta=f"Score: {recommendation['score']:.0f}/100"
            )
        
        with col2:
            # Show key advantages
            hp_lcoh = hp_metrics.get('lcoh_eur_per_mwh', 0)
            dh_lcoh = dh_metrics.get('lcoh_eur_per_mwh', 0)
            
            if dh_lcoh < hp_lcoh:
                savings = hp_lcoh - dh_lcoh
                st.success(f"💚 DH saves {savings:.1f} €/MWh compared to HP")
            else:
                savings = dh_lcoh - hp_lcoh
                st.info(f"💙 HP saves {savings:.1f} €/MWh compared to DH")
        
        # Additional information
        st.subheader("ℹ️ Additional Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Heat Pump Metrics:**")
            for key, value in hp_metrics.items():
                st.write(f"- {key.replace('_', ' ').title()}: {value:,.0f}")
        
        with col2:
            st.markdown("**District Heating Metrics:**")
            for key, value in dh_metrics.items():
                st.write(f"- {key.replace('_', ' ').title()}: {value:,.0f}")
        
        # Footer
        st.markdown("---")
        st.markdown("**Note:** This analysis is based on current KPI data. For the most up-to-date analysis, please run the complete system workflow.")


def main():
    """Main function to run the street comparison tool"""
    
    # Check if running in Streamlit
    try:
        import streamlit as st
        tool = StreetComparisonTool()
        tool.run_streamlit_app()
    except ImportError:
        print("Streamlit not available. Running in command-line mode...")
        run_cli_mode()


def run_cli_mode():
    """Run in command-line mode"""
    
    tool = StreetComparisonTool()
    
    print("🏘️ Street Comparison Tool - CLI Mode")
    print("=" * 50)
    
    if not tool.available_streets:
        print("❌ No street data available. Please run the analysis first.")
        return
    
    print(f"Available streets: {', '.join(tool.available_streets)}")
    print()
    
    # Interactive selection
    while True:
        try:
            print("Select a street (or 'quit' to exit):")
            for i, street in enumerate(tool.available_streets, 1):
                print(f"  {i}. {street}")
            
            choice = input("\nEnter choice (number or name): ").strip()
            
            if choice.lower() in ['quit', 'exit', 'q']:
                break
            
            # Try to parse as number
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(tool.available_streets):
                    selected_street = tool.available_streets[choice_num - 1]
                else:
                    print("❌ Invalid choice number")
                    continue
            except ValueError:
                # Try to match by name
                selected_street = choice
                if selected_street not in tool.available_streets:
                    print("❌ Street not found")
                    continue
            
            # Load and display data
            street_data = tool.load_street_kpis(selected_street)
            
            if not street_data:
                print(f"❌ No KPI data found for {selected_street}")
                continue
            
            print(f"\n📊 Analysis for: {selected_street}")
            print("=" * 50)
            
            # Display summary table
            summary_df = tool.create_summary_table(street_data)
            print(summary_df.to_string(index=False))
            
            # Display recommendation
            hp_metrics = street_data.get('hp_metrics', {})
            dh_metrics = street_data.get('dh_metrics', {})
            recommendation = tool._get_recommendation(hp_metrics, dh_metrics)
            
            print(f"\n🎯 Recommendation: {recommendation['text']} (Score: {recommendation['score']:.0f}/100)")
            
            # Show key metrics
            hp_lcoh = hp_metrics.get('lcoh_eur_per_mwh', 0)
            dh_lcoh = dh_metrics.get('lcoh_eur_per_mwh', 0)
            
            if dh_lcoh < hp_lcoh:
                savings = hp_lcoh - dh_lcoh
                print(f"💚 DH saves {savings:.1f} €/MWh compared to HP")
            else:
                savings = dh_lcoh - hp_lcoh
                print(f"💙 HP saves {savings:.1f} €/MWh compared to DH")
            
            print("\n" + "=" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
