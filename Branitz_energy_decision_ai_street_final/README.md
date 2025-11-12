# Branitz Energy Decision AI

A comprehensive energy decision support system for urban planning, focusing on district heating vs. heat pump scenarios for the Branitz settlement.

## Features

- Building energy demand calculation
- Load profile generation
- Network construction and analysis
- Multi-scenario simulation (District Heating vs Heat Pumps)
- KPI calculation and comparison
- AI-powered report generation
- Interactive street selection
- Network visualization

## Setup

### 1. Environment Setup

Create a conda environment and install dependencies:

```bash
conda create -n branitz_env python=3.9
conda activate branitz_env
pip install -r requirements.txt
```

### 2. Environment Variables

For LLM report generation, set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your-api-key-here
```

### 3. Data Files

Ensure the following data files are present:
- `data/geojson/hausumringe_with_gebaeudeid.geojson` - Building footprints
- `data/osm/branitzer_siedlung.osm` - Street network
- `data/json/building_population_resultsV6.json` - Demographics data

## Usage

### Full Pipeline Run

```bash
# Run with main configuration
python main.py --config run_all.yaml

# Run with test configuration (smaller dataset)
python main.py --config run_all_test.yaml
```

### Interactive Run

```bash
# Select specific streets interactively
python interactive_run.py
```

### Visualization

```bash
# Generate network visualization
python graph2.py --output_dir results/

# Extract buildings for specific street
python extract_street_buildings.py
```

## Configuration

### Main Configuration Files

- `run_all.yaml` - Full dataset configuration
- `run_all_test.yaml` - Test configuration with subset of buildings
- `branitz_scenarios.yaml` - Energy scenario definitions

### Key Configuration Options

- `test_mode: true` - Enable test mode with selected buildings
- `selected_buildings: []` - List of building IDs for test mode
- `output_dir: "results/"` - Output directory for results
- `llm_model: "gpt-4o"` - LLM model for report generation

## Output Files

### Main Results
- `buildings_with_demand.geojson` - Buildings with calculated energy demand
- `building_load_profiles.json` - Hourly load profiles
- `branitz_network.graphml` - Network graph
- `scenario_kpis.csv` - Key performance indicators
- `llm_report.md` - AI-generated analysis report

### Visualization Files
- `service_connections.geojson` - Network connections
- `buildings_projected.geojson` - Building geometries
- `street_projected.geojson` - Street network

## Troubleshooting

### Common Issues

1. **Missing API Key**: Set `OPENAI_API_KEY` environment variable
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **File Not Found**: Check data file paths in configuration
4. **Memory Issues**: Use test mode with fewer buildings

### Error Messages

- `Configuration Error`: Check required files exist
- `Missing required packages`: Install missing dependencies
- `Warning: OPENAI_API_KEY not set`: Set environment variable for LLM features

## Development

### Project Structure

```
src/
├── data_preparation.py      # Data loading and preprocessing
├── building_attributes.py   # Demographics and building attributes
├── envelope_and_uvalue.py   # Building envelope calculations
├── demand_calculation.py    # Energy demand calculation
├── profile_generation.py    # Load profile generation
├── network_construction.py  # Network graph creation
├── scenario_manager.py      # Scenario generation
├── simulation_runner.py     # Energy simulations
├── kpi_calculator.py        # Performance indicators
└── llm_reporter.py          # AI report generation
```

### Adding New Features

1. Add new modules to `src/`
2. Update `main.py` pipeline if needed
3. Add configuration options to YAML files
4. Update documentation

## License

This project is for research purposes. Please ensure compliance with data usage agreements.
