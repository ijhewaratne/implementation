# Branitz DH - District Heating Network Analysis

A comprehensive framework for district heating network analysis, providing tools for network simulation, thermal modeling, and visualization using pandapipes.

## Project Structure

```
branitz_dh/
├── app/
│   └── main.py                 # Main application entry point
├── dh_core/                    # Core functionality modules
│   ├── config.py              # Configuration management (DHDesign, Paths)
│   ├── data_adapters.py       # Data input/output handling (network, addresses, loads)
│   ├── ppipe_builder.py       # Pandapipes network construction and simulation
│   ├── load_binding.py        # Load assignment and address matching
│   ├── viz.py                 # Network visualization utilities
│   └── costs.py               # Cost tracking and calculation
├── data/                       # Data directories
│   ├── inputs/                # Input data files
│   ├── outputs/               # Output results and visualizations
│   ├── cache/                 # Cached intermediate results
│   └── catalogs/              # Data catalogs and metadata
├── README.md                   # This file
└── environment.yml             # Conda environment specification
```

## Features

### Core Components

- **Configuration Management**: District heating design parameters (DHDesign, Paths)
- **Data Adapters**: Network topology, address points, and building load data loading
- **Network Simulation**: Pandapipes integration for thermal and hydraulic analysis
- **Load Binding**: Building load assignment to network addresses
- **Visualization**: Interactive network maps with temperature/pressure gradients
- **Cost Tracking**: Monitor computational costs for simulation runs

### Key Capabilities

- **Network Analysis**: Load and process district heating network topology
- **Thermal Simulation**: Run pandapipes simulations with building loads
- **Interactive Visualization**: Folium-based maps with gradient visualization
- **Load Management**: Match building loads to network addresses
- **Real-time Controls**: Adjust supply/return temperatures and pipe properties
- **Professional Output**: Generate temperature and pressure gradient maps

## Installation

### Prerequisites

- Python 3.8+
- Conda package manager

### Setup

1. Clone or download the project
2. Create the conda environment:
   ```bash
   conda env create -f environment.yml
   ```
3. Activate the environment:
   ```bash
   conda activate branitz_env
   ```

## Usage

### Basic Usage

```python
from dh_core.config import Config
from dh_core.data_adapters import DataAdapter
from dh_core.ppipe_builder import PipelineBuilder

# Initialize configuration
config = Config()

# Create data adapter
data_adapter = DataAdapter(config)

# Load data
df = data_adapter.load_csv("your_data.csv")

# Build and execute pipeline
pipeline = PipelineBuilder(config)
pipeline.add_step("process_data", your_processing_function)
result = pipeline.execute_sequential({"data": df})
```

### Visualization

```python
from dh_core.viz import Visualizer

visualizer = Visualizer(config)

# Create timeline plot
fig = visualizer.plot_timeline(df, "date_col", "value_col", "My Timeline")

# Create distribution plot
fig = visualizer.plot_distribution(df["column"], "Distribution Analysis")

# Create correlation heatmap
fig = visualizer.plot_correlation_heatmap(df, "Feature Correlations")
```

### Cost Tracking

```python
from dh_core.costs import CostCalculator

cost_calc = CostCalculator(config)

# Track API usage
cost_calc.track_api_call(tokens_used=1000, model="gpt-3.5-turbo")

# Track computation
cost_calc.track_computation(duration_seconds=120, operation="data_processing")

# Get cost summary
summary = cost_calc.get_cost_summary(days=30)
print(f"Total cost: ${summary['total_cost']:.2f}")
```

## Configuration

The system uses a YAML-based configuration file (`config.yaml`) with the following structure:

```yaml
data:
  inputs_dir: "data/inputs"
  outputs_dir: "data/outputs"
  cache_dir: "data/cache"
  catalogs_dir: "data/catalogs"

processing:
  max_workers: 4
  chunk_size: 1000
  enable_caching: true

visualization:
  default_style: "seaborn"
  figure_size: [12, 8]
  save_format: "png"

costs:
  track_costs: true
  currency: "USD"
  cost_per_token: 0.0001
```

## Data Formats

### Supported Input Formats

- **CSV**: Tabular data with automatic type inference
- **JSON**: Structured data with nested objects and arrays
- **Catalogs**: JSON-based metadata catalogs for data organization

### Output Formats

- **CSV**: Processed tabular data
- **JSON**: Structured results and metadata
- **Images**: PNG format for visualizations
- **Cache**: JSON-based intermediate results

## Pipeline System

The pipeline builder supports:

- **Sequential Execution**: Steps executed in order
- **Parallel Execution**: Independent steps run concurrently (planned)
- **Caching**: Automatic caching of intermediate results
- **Validation**: Pipeline dependency validation
- **Error Handling**: Comprehensive error reporting

### Pipeline Example

```python
# Define processing functions
def clean_data(data):
    return data.dropna()

def normalize_data(data):
    return (data - data.mean()) / data.std()

# Build pipeline
pipeline = PipelineBuilder(config)
pipeline.add_step("clean", clean_data, input_keys=["raw_data"], output_keys=["clean_data"])
pipeline.add_step("normalize", normalize_data, input_keys=["clean_data"], output_keys=["normalized_data"])

# Execute with caching
result = pipeline.execute_with_caching(
    initial_data={"raw_data": df},
    cache_key="data_processing_v1"
)
```

## Visualization Types

- **Timeline Plots**: Time-series data visualization
- **Distribution Analysis**: Histograms and box plots
- **Correlation Heatmaps**: Feature relationship analysis
- **Word Clouds**: Text data visualization
- **Network Graphs**: Graph and network analysis
- **Dashboards**: Multi-plot combinations

## Cost Tracking

The system tracks:

- **API Costs**: Token-based pricing for language models
- **Compute Costs**: CPU time and resource usage
- **Storage Costs**: Data storage and caching expenses
- **Session Tracking**: Per-session cost monitoring
- **Historical Reports**: Time-based cost analysis

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or contributions, please:

1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information
4. Contact the maintainers

## Changelog

### Version 1.0.0
- Initial release
- Core pipeline system
- Basic visualization capabilities
- Cost tracking framework
- Configuration management
