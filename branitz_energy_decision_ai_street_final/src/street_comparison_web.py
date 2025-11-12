#!/usr/bin/env python3
"""
Web-based Street Comparison Tool
Simple HTTP server for street comparison interface
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import webbrowser
import threading
import time

class StreetComparisonWeb:
    """Web-based street comparison tool"""
    
    def __init__(self, data_dir: str = "processed", port: int = 8080):
        self.data_dir = Path(data_dir)
        self.kpi_dir = self.data_dir / "kpi"
        self.port = port
        
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
    
    def generate_html(self, selected_street: str = None) -> str:
        """Generate HTML interface"""
        
        streets = self.get_available_streets()
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Street Comparison Tool</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .selector {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .results {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        select {{
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }}
        button {{
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }}
        button:hover {{
            background: #5a6fd8;
        }}
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .comparison-table th,
        .comparison-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        .comparison-table th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        .hp-row {{ background-color: #e3f2fd; }}
        .dh-row {{ background-color: #fff3e0; }}
        .better {{ background-color: #c8e6c9; font-weight: bold; }}
        .recommendation {{
            background: #e8f5e8;
            border: 2px solid #4caf50;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            text-align: center;
        }}
        .recommendation.dh {{
            background: #e3f2fd;
            border-color: #2196f3;
        }}
        .recommendation.hp {{
            background: #fff3e0;
            border-color: #ff9800;
        }}
        .metric {{
            display: inline-block;
            margin: 10px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
            min-width: 150px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
        .loading {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏘️ Street Comparison Tool</h1>
        <p>Compare District Heating vs Heat Pump KPIs</p>
    </div>
    
    <div class="selector">
        <h3>Select a Street:</h3>
        <form method="GET">
            <select name="street" onchange="this.form.submit()">
                <option value="">Choose a street...</option>
"""
        
        for street in streets:
            selected = "selected" if street == selected_street else ""
            html += f'                <option value="{street}" {selected}>{street}</option>\n'
        
        html += """
            </select>
        </form>
    </div>
    
    <div class="results">
"""
        
        if selected_street:
            data = self.load_street_data(selected_street)
            if data:
                html += self._generate_comparison_html(selected_street, data)
            else:
                html += f'<div class="loading">❌ No data found for {selected_street}</div>'
        else:
            html += '<div class="loading">👆 Please select a street above to see the comparison</div>'
        
        html += """
    </div>
    
    <script>
        // Auto-refresh every 30 seconds if no street selected
        if (!window.location.search.includes('street=')) {
            setTimeout(() => {
                window.location.reload();
            }, 30000);
        }
    </script>
</body>
</html>
"""
        
        return html
    
    def _generate_comparison_html(self, street_name: str, data: Dict) -> str:
        """Generate comparison HTML for a street"""
        
        hp_metrics = data.get('hp_metrics', {})
        dh_metrics = data.get('dh_metrics', {})
        
        html = f"""
        <h2>📊 Analysis for: {street_name}</h2>
        
        <div style="display: flex; justify-content: space-around; margin: 20px 0;">
            <div class="metric">
                <div class="metric-value">{hp_metrics.get('lcoh_eur_per_mwh', 0):.1f}</div>
                <div class="metric-label">HP LCOH (€/MWh)</div>
            </div>
            <div class="metric">
                <div class="metric-value">{dh_metrics.get('lcoh_eur_per_mwh', 0):.1f}</div>
                <div class="metric-label">DH LCOH (€/MWh)</div>
            </div>
        </div>
        
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Heat Pump</th>
                    <th>District Heating</th>
                    <th>Better Option</th>
                </tr>
            </thead>
            <tbody>
"""
        
        metrics = {
            'LCOH (€/MWh)': 'lcoh_eur_per_mwh',
            'CO2 Emissions (t/a)': 'co2_t_per_a',
            'CAPEX (€)': 'capex_eur',
            'OPEX (€/year)': 'opex_eur',
            'Energy Costs (€/year)': 'energy_costs_eur'
        }
        
        dh_wins = 0
        hp_wins = 0
        
        for metric_name, key in metrics.items():
            hp_value = hp_metrics.get(key, 0)
            dh_value = dh_metrics.get(key, 0)
            
            if hp_value > 0 and dh_value > 0:
                if dh_value < hp_value:
                    better = "DH ✅"
                    dh_wins += 1
                    better_class = "better"
                else:
                    better = "HP ✅"
                    hp_wins += 1
                    better_class = "better"
            else:
                better = "N/A"
                better_class = ""
            
            html += f"""
                <tr class="{better_class}">
                    <td><strong>{metric_name}</strong></td>
                    <td class="hp-row">{hp_value:,.0f}</td>
                    <td class="dh-row">{dh_value:,.0f}</td>
                    <td>{better}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
"""
        
        # Recommendation
        if dh_wins > hp_wins:
            recommendation_class = "dh"
            recommendation_text = "💚 DISTRICT HEATING RECOMMENDED"
            recommendation_details = f"DH wins in {dh_wins} out of {len(metrics)} metrics"
        elif hp_wins > dh_wins:
            recommendation_class = "hp"
            recommendation_text = "💙 HEAT PUMP RECOMMENDED"
            recommendation_details = f"HP wins in {hp_wins} out of {len(metrics)} metrics"
        else:
            recommendation_class = ""
            recommendation_text = "⚖️ TIE - Both options are competitive"
            recommendation_details = "Both options perform similarly"
        
        html += f"""
        <div class="recommendation {recommendation_class}">
            <h3>{recommendation_text}</h3>
            <p>{recommendation_details}</p>
"""
        
        # Key insight
        hp_lcoh = hp_metrics.get('lcoh_eur_per_mwh', 0)
        dh_lcoh = dh_metrics.get('lcoh_eur_per_mwh', 0)
        
        if hp_lcoh > 0 and dh_lcoh > 0:
            if dh_lcoh < hp_lcoh:
                savings = hp_lcoh - dh_lcoh
                savings_pct = (savings / hp_lcoh) * 100
                html += f"<p><strong>💰 DH saves {savings:.1f} €/MWh ({savings_pct:.1f}% cheaper)</strong></p>"
            else:
                savings = dh_lcoh - hp_lcoh
                savings_pct = (savings / dh_lcoh) * 100
                html += f"<p><strong>💰 HP saves {savings:.1f} €/MWh ({savings_pct:.1f}% cheaper)</strong></p>"
        
        html += """
        </div>
"""
        
        return html


class StreetComparisonHandler(BaseHTTPRequestHandler):
    """HTTP request handler for street comparison"""
    
    def do_GET(self):
        """Handle GET requests"""
        
        # Parse URL
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        selected_street = query_params.get('street', [None])[0]
        
        # Generate HTML
        web_tool = StreetComparisonWeb()
        html = web_tool.generate_html(selected_street)
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def start_server(port: int = 8080):
    """Start the web server"""
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, StreetComparisonHandler)
    
    print(f"🌐 Street Comparison Tool started!")
    print(f"📱 Open your browser and go to: http://localhost:{port}")
    print("🛑 Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped!")
        httpd.shutdown()


def main():
    """Main function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Street Comparison Web Tool")
    parser.add_argument("--port", type=int, default=8080, help="Port to run server on")
    parser.add_argument("--open-browser", action="store_true", help="Open browser automatically")
    
    args = parser.parse_args()
    
    # Open browser in a separate thread
    if args.open_browser:
        def open_browser():
            time.sleep(1)  # Wait for server to start
            webbrowser.open(f"http://localhost:{args.port}")
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
    
    start_server(args.port)


if __name__ == "__main__":
    main()
