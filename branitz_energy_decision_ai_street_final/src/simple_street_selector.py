#!/usr/bin/env python3
"""
Simple Street Selector for DH vs HP Comparison
Command-line tool for quick street comparison
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

class SimpleStreetSelector:
    """Simple command-line street selector"""
    
    def __init__(self, data_dir: str = "processed"):
        self.data_dir = Path(data_dir)
        self.kpi_dir = self.data_dir / "kpi"
        
    def get_available_streets(self) -> List[str]:
        """Get list of available streets"""
        streets = []
        
        if self.kpi_dir.exists():
            for kpi_file in self.kpi_dir.glob("kpi_report_*.json"):
                if kpi_file.name != "kpi_summary.json":
                    street_name = kpi_file.stem.replace("kpi_report_", "")
                    if street_name:
                        streets.append(street_name)
        
        return sorted(streets)
    
    def load_street_data(self, street_name: str) -> Optional[Dict]:
        """Load KPI data for a street"""
        kpi_file = self.kpi_dir / f"kpi_report_{street_name}.json"
        
        if not kpi_file.exists():
            return None
            
        try:
            with open(kpi_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading data for {street_name}: {e}")
            return None
    
    def compare_street(self, street_name: str) -> None:
        """Compare DH vs HP for a street"""
        
        data = self.load_street_data(street_name)
        if not data:
            print(f"❌ No data found for {street_name}")
            return
        
        print(f"\n🏘️  Street: {street_name}")
        print("=" * 60)
        
        hp_metrics = data.get('hp_metrics', {})
        dh_metrics = data.get('dh_metrics', {})
        
        # Key metrics comparison
        metrics = {
            'LCOH (€/MWh)': ('lcoh_eur_per_mwh', 'Lower is better'),
            'CO2 Emissions (t/a)': ('co2_t_per_a', 'Lower is better'),
            'CAPEX (€)': ('capex_eur', 'Lower is better'),
            'OPEX (€/year)': ('opex_eur', 'Lower is better'),
            'Energy Costs (€/year)': ('energy_costs_eur', 'Lower is better')
        }
        
        print(f"{'Metric':<25} {'Heat Pump':<15} {'District Heating':<15} {'Better':<10}")
        print("-" * 65)
        
        dh_wins = 0
        hp_wins = 0
        
        for metric_name, (key, _) in metrics.items():
            hp_value = hp_metrics.get(key, 0)
            dh_value = dh_metrics.get(key, 0)
            
            if hp_value > 0 and dh_value > 0:
                if dh_value < hp_value:
                    better = "DH ✅"
                    dh_wins += 1
                else:
                    better = "HP ✅"
                    hp_wins += 1
            else:
                better = "N/A"
            
            print(f"{metric_name:<25} {hp_value:<15,.0f} {dh_value:<15,.0f} {better:<10}")
        
        # Overall recommendation
        print("\n" + "=" * 60)
        print("🎯 RECOMMENDATION:")
        
        if dh_wins > hp_wins:
            print("💚 DISTRICT HEATING is recommended")
            print(f"   DH wins in {dh_wins} out of {len(metrics)} metrics")
        elif hp_wins > dh_wins:
            print("💙 HEAT PUMP is recommended")
            print(f"   HP wins in {hp_wins} out of {len(metrics)} metrics")
        else:
            print("⚖️  TIE - Both options are competitive")
        
        # Key insight
        hp_lcoh = hp_metrics.get('lcoh_eur_per_mwh', 0)
        dh_lcoh = dh_metrics.get('lcoh_eur_per_mwh', 0)
        
        if hp_lcoh > 0 and dh_lcoh > 0:
            if dh_lcoh < hp_lcoh:
                savings = hp_lcoh - dh_lcoh
                print(f"💰 DH saves {savings:.1f} €/MWh ({((savings/hp_lcoh)*100):.1f}% cheaper)")
            else:
                savings = dh_lcoh - hp_lcoh
                print(f"💰 HP saves {savings:.1f} €/MWh ({((savings/dh_lcoh)*100):.1f}% cheaper)")
        
        print("=" * 60)
    
    def interactive_mode(self):
        """Run in interactive mode"""
        
        streets = self.get_available_streets()
        
        if not streets:
            print("❌ No street data available. Please run the analysis first.")
            return
        
        print("🏘️  Simple Street Selector")
        print("=" * 40)
        print(f"Available streets: {len(streets)}")
        
        while True:
            print("\nOptions:")
            print("1. List all streets")
            print("2. Compare specific street")
            print("3. Compare all streets")
            print("4. Exit")
            
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == '1':
                print("\nAvailable streets:")
                for i, street in enumerate(streets, 1):
                    print(f"  {i}. {street}")
            
            elif choice == '2':
                print("\nAvailable streets:")
                for i, street in enumerate(streets, 1):
                    print(f"  {i}. {street}")
                
                try:
                    street_choice = input("\nEnter street name or number: ").strip()
                    
                    # Try to parse as number
                    try:
                        street_num = int(street_choice)
                        if 1 <= street_num <= len(streets):
                            selected_street = streets[street_num - 1]
                        else:
                            print("❌ Invalid number")
                            continue
                    except ValueError:
                        selected_street = street_choice
                        if selected_street not in streets:
                            print("❌ Street not found")
                            continue
                    
                    self.compare_street(selected_street)
                    
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
            
            elif choice == '3':
                print("\n🔄 Comparing all streets...")
                for street in streets:
                    self.compare_street(street)
                    input("\nPress Enter to continue to next street...")
            
            elif choice == '4':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice")


def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        # Command line mode
        street_name = sys.argv[1]
        selector = SimpleStreetSelector()
        selector.compare_street(street_name)
    else:
        # Interactive mode
        selector = SimpleStreetSelector()
        selector.interactive_mode()


if __name__ == "__main__":
    main()
