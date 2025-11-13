# Enhanced Interactive Street Analysis Workflow

This enhanced workflow allows you to automatically analyze any selected street(s) for district heating network feasibility, generate network plots, and create LLM reports.

## Features

✅ **Interactive Street Selection**: Choose from all available streets in the dataset  
✅ **Automatic Building Extraction**: Extract buildings for selected streets  
✅ **DH Network Simulation**: Run pandapipes simulations automatically  
✅ **Network Plot Generation**: Create visual network plots  
✅ **LLM Report Generation**: Generate comprehensive analysis reports  
✅ **Batch Processing**: Analyze multiple streets in one run  

## Quick Start

### 1. Run the Enhanced Interactive Script

```bash
conda activate branitz_env
python interactive_run_enhanced.py
```

### 2. Select Streets

- The script will show you a list of all available streets
- Use spacebar to select/deselect streets
- Press Enter to confirm your selection

### 3. Automatic Processing

For each selected street, the script will automatically:

1. **Extract Buildings**: Create a GeoJSON file with buildings for that street
2. **Create Scenario**: Generate a DH simulation scenario
3. **Run Simulation**: Execute the pandapipes simulation
4. **Generate Plot**: Create a network visualization
5. **Create Report**: Generate an LLM analysis report

## Output Files

For each analyzed street, you'll get:

### In `street_analysis_outputs/`:
- `buildings_[StreetName].geojson` - Building data for the street
- `scenario_[StreetName].json` - Simulation scenario configuration
- `llm_report_[StreetName].md` - LLM analysis report

### In `simulation_outputs/`:
- `street_[StreetName]_results.json` - Simulation results and KPIs
- `dh_street_[StreetName].png` - Network visualization plot

## Example Output

### LLM Report Structure
```
# District Heating Network Analysis for [Street Name]

## Executive Summary
Brief overview of the analysis

## Simulation Results
- Total Heat Demand: X MWh
- Total Pipe Length: X km
- Number of Buildings: X
- Network Density: X km per building
- Hydraulic Success: Yes/No
- Maximum Pressure Drop: X bar

## Technical Analysis
Detailed technical assessment

## Recommendations
Actionable recommendations based on results

## Next Steps
Suggested follow-up actions
```

### Network Plot Features
- **Red dots**: Supply junctions
- **Blue dots**: Return junctions  
- **Green square**: CHP Plant
- **Orange triangles**: Heat consumers
- **Red lines**: Supply pipes
- **Blue lines**: Return pipes
- **Statistics box**: Key network parameters

## Configuration Options

You can modify the simulation parameters in the `create_street_scenario()` function:

```python
scenario = {
    "name": f"street_{clean_street_name}",
    "description": f"District Heating simulation for {street_name}",
    "type": "DH",
    "params": {
        "supply_temp": 70,        # Supply temperature (°C)
        "return_temp": 40,        # Return temperature (°C)
        "tech": "biomass",        # Technology type
        "main_diameter": 0.4      # Pipe diameter (m)
    },
    "building_file": building_file
}
```

## Requirements

- Python environment with `branitz_env` activated
- Required packages: `pandapipes`, `geopandas`, `matplotlib`, `questionary`
- Building data file: `data/geojson/hausumringe_mit_adressenV3.geojson`

## Troubleshooting

### Common Issues

1. **No buildings found**: Check if the street name exists in the dataset
2. **Simulation fails**: Check if pandapipes is properly installed
3. **Plot generation fails**: Ensure matplotlib is available
4. **Memory issues**: For large streets, consider processing fewer buildings

### Error Messages

- `"No buildings found for [street]"`: Street not in dataset
- `"Simulation failed"`: Check pandapipes installation
- `"Results file not found"`: Simulation didn't complete successfully

## Advanced Usage

### Customizing the LLM Report

You can modify the `generate_llm_report_for_street()` function to:
- Add more KPIs
- Include economic analysis
- Add environmental impact assessment
- Customize the report format

### Batch Processing

To process multiple streets programmatically:

```python
from interactive_run_enhanced import *

# Define streets to process
streets_to_analyze = ["Street A", "Street B", "Street C"]

# Process each street
for street in streets_to_analyze:
    buildings_features = get_buildings_for_streets(geojson_path, [street])
    # ... rest of processing
```

## Performance Notes

- **Small streets** (< 20 buildings): ~30 seconds per street
- **Medium streets** (20-50 buildings): ~1-2 minutes per street  
- **Large streets** (> 50 buildings): ~3-5 minutes per street

The processing time depends on:
- Number of buildings
- Network complexity
- Available computational resources

---

*This enhanced workflow provides a complete automated analysis pipeline for district heating network feasibility assessment.* 