# ETL Pipeline: Data to LoadForecastingAgent (LFA)

This ETL pipeline converts building data and weather data into the exact format required by the LoadForecastingAgent, including physics features and optional synthetic labels.

## Overview

The ETL pipeline performs the following transformations:

1. **Building Data Processing**: Normalizes building data from various formats (JSON/GeoJSON/CSV) and computes physics coefficients
2. **Weather Data Processing**: Handles weather data and ensures 8760 hourly rows
3. **Synthetic Label Generation**: Creates physics-based heat demand labels using DIN formulas
4. **LFA Integration**: Patches LFA to use physics features and synthetic labels

## Features

### Physics Coefficients
- **H_tr**: Transmission heat loss coefficient (W/K)
- **H_ve**: Ventilation heat loss coefficient (W/K)  
- **sanierungs_faktor**: Renovation factor (0.30-1.00)

### Building Features
- **U-values**: Wall, roof, floor, window thermal transmittance
- **Areas**: Floor, wall, roof, window areas
- **Volume**: Building volume for ventilation calculations
- **Renovation status**: unsaniert/teilsaniert/vollsaniert

### Synthetic Labels
- **DIN heat demand formula**: `P_h(t) = (H_tr + H_ve) * (T_in - T_out(t)) * sanierungs_faktor`
- **Hourly 8760 values**: Complete year of heat demand in kW
- **Physics-based**: Uses actual building characteristics and weather

## Usage

### Command Line Interface

```bash
# Basic usage
python -m etl.data_to_lfa \
  --buildings data_16122024/buildings.json \
  --try data_16122024/weather.csv \
  --year 2024 \
  --write-meters true

# With custom output directory
python -m etl.data_to_lfa \
  --buildings data_16122024/buildings.json \
  --try data_16122024/weather.csv \
  --year 2024 \
  --write-meters true \
  --output-dir data/processed
```

### Programmatic Usage

```python
from etl.data_to_lfa import (
    load_buildings, compute_physics, build_weather, synthesize_labels
)

# Load and process building data
buildings_df = load_buildings("data_16122024/buildings.json")
buildings_with_physics = compute_physics(buildings_df)

# Process weather data
weather_df = build_weather("data_16122024/weather.csv", 2024)

# Generate synthetic labels
synthesize_labels(buildings_with_physics, weather_df, "data/interim/meters")
```

## Input Data Requirements

### Building Data
The pipeline accepts building data in various formats with the following field mappings:

| Required Field | Possible Column Names | Default |
|----------------|---------------------|---------|
| Building ID | `oi`, `building_id`, `id`, `gebaeude_id` | - |
| Function | `gebaeudefunktion`, `building_function`, `function`, `type`, `nutzung` | `function` |
| Floor Area | `nutzflaeche`, `floor_area`, `area`, `flaeche` | 100.0 m² |
| Wall Area | `wandflaeche`, `wall_area`, `aussenwand_flaeche` | Computed |
| Roof Area | `dachflaeche`, `roof_area`, `dach_flaeche` | Computed |
| Volume | `volumen`, `volume`, `raumvolumen` | Computed |
| Height | `hoehe`, `height`, `gebaeudehoehe` | 3.0 m |
| U-values | `U_Aussenwand`, `U_Dach`, `U_Boden`, `U_Fenster` | Standard values |
| Window Ratio | `fensterflaechenanteil`, `window_ratio`, `fenster_anteil` | 0.15 |
| Indoor Temp | `innentemperatur`, `indoor_temp`, `t_in`, `room_temp` | 20.0 °C |
| Air Exchange | `n`, `luftwechselrate`, `air_exchange`, `ventilation_rate` | 0.5 1/h |
| Renovation | `sanierungszustand`, `renovation_status`, `sanierung` | `unsaniert` |
| Year Built | `baujahr`, `year_built`, `construction_year`, `year` | 1990 |

### Weather Data
Weather data should contain:
- **timestamp**: Hourly timestamps (8760 rows for full year)
- **T_out**: Outdoor temperature (°C)
- **RH**: Relative humidity (%) - optional
- **GHI**: Global horizontal irradiance (W/m²) - optional

## Output Files

### Processed Data
- `data/processed/buildings.parquet`: Normalized building data with physics coefficients
- `data/processed/weather.parquet`: Processed weather data (8760 hourly rows)

### Synthetic Labels (Optional)
- `data/interim/meters/{building_id}.parquet`: Hourly heat demand for each building
  - Columns: `timestamp`, `demand_kw`

## Physics Calculations

### Transmission Heat Loss (H_tr)
```
H_tr = Σ(U_i × A_i)
```
Where:
- U_i = thermal transmittance of element i (W/m²K)
- A_i = area of element i (m²)
- Elements: walls, roof, floor, windows

### Ventilation Heat Loss (H_ve)
```
H_ve = V × n × 0.34
```
Where:
- V = building volume (m³)
- n = air exchange rate (1/h)
- 0.34 ≈ ρ·c_p of air (Wh/m³K)

### Renovation Factors
- **unsaniert**: 1.00 (no renovation)
- **teilsaniert**: 0.71 (partial renovation)
- **vollsaniert**: 0.30 (full renovation)

### Heat Demand Formula
```
P_h(t) = (H_tr + H_ve) × (T_in - T_out(t)) × sanierungs_faktor
```
Where:
- P_h(t) = heat demand at time t (W)
- T_in = indoor temperature (°C)
- T_out(t) = outdoor temperature at time t (°C)

## LFA Integration

The LoadForecastingAgent has been patched to:

1. **Use Physics Features**: Include H_tr, H_ve, sanierungs_faktor in training
2. **Physics-Based Labels**: Use DIN formula when physics features are available
3. **Configurable**: Toggle between physics and traditional synthetic labels
4. **Validation**: Ensure physics features are properly joined into training data

### Configuration
Add to `configs/lfa.yml`:
```yaml
# Physics settings
use_physics_labels: true  # Use physics-based synthetic labels when available
```

## Testing

Run the test suite:
```bash
make etl-sample
```

Or test individual components:
```python
python test_etl_pipeline.py
```

## Error Handling

The pipeline includes comprehensive error handling:
- **Missing files**: Clear error messages for missing input files
- **Data validation**: Checks for required columns and data types
- **Physics validation**: Ensures positive values for physics coefficients
- **Weather validation**: Verifies 8760 hourly rows and monotonic timestamps

## Performance

- **Vectorized operations**: Uses pandas for efficient data processing
- **Memory efficient**: Processes data in chunks for large datasets
- **Parallel processing**: Can be extended for parallel building processing

## Dependencies

- pandas >= 1.3.0
- numpy >= 1.20.0
- pyarrow >= 12.0 (for parquet files)

## Contributing

When extending the ETL pipeline:
1. Add new field mappings to `normalize_building_data()`
2. Update physics calculations in `compute_physics()`
3. Add validation in appropriate functions
4. Update tests and documentation







