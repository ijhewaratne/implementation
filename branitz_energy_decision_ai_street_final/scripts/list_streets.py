#!/usr/bin/env python3
"""
List available streets from KPI data.
"""

import json
from pathlib import Path

def main():
    kpi_dir = Path('processed/kpi')
    
    if not kpi_dir.exists():
        print('❌ No KPI data found')
        return
    
    streets = []
    for kpi_file in kpi_dir.glob('kpi_report_*.json'):
        if kpi_file.name != 'kpi_summary.json':
            street_name = kpi_file.stem.replace('kpi_report_', '')
            if street_name:
                streets.append(street_name)
    
    if streets:
        for i, street in enumerate(sorted(streets), 1):
            print(f'  {i}. {street}')
        print(f'Total: {len(streets)} streets available')
    else:
        print('❌ No KPI data found')

if __name__ == '__main__':
    main()

