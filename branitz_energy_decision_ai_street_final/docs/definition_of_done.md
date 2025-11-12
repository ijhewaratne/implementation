# Definition of Done (DoD) — Branitz Energy Decision AI

## Overview
This document defines the Definition of Done (DoD) for each agent in the Branitz Energy Decision AI project. Each agent must meet these criteria before being considered complete and production-ready.

## 3.1 Load Forecasting Agent (LFA)

### Deliverable
Per-building 8760h heat series with quantiles q10, q90.

### Output Location
- **Data**: `processed/lfa/{building_id}.json`
- **Metrics**: `eval/lfa/metrics.csv`
- **Plots**: `eval/lfa/plots/*`

### Metrics Required
- MAE (Mean Absolute Error)
- RMSE (Root Mean Square Error)
- MAPE (Mean Absolute Percentage Error)
- PICP(80%) (Prediction Interval Coverage Probability at 80%)
- PICP(90%) (Prediction Interval Coverage Probability at 90%)

### DoD Criteria
1. **Schema Validation**: Each JSON validates against `schemas/lfa_demand.schema.json`
2. **Data Integrity**: Arrays `series`, `q10`, `q90` have length 8760 (floats) and are finite
3. **Metrics File**: Metrics file saved to `eval/lfa/metrics.csv`
4. **Visualization**: Plot(s) saved to `eval/lfa/plots/*`
5. **Error Handling**: If missing/invalid: patch writer or pipeline; do not hand-edit outputs

## 3.2 Centralized Heating Agent (CHA — pandapipes)

### Deliverables
- **CSVs**: losses, Δp, pump_kW in `processed/cha/*.csv`
- **GIS**: `processed/cha/cha.gpkg` (mains, branches, nodes, service areas)

### Design Checks
EN 13941-ish sanity checks:
- Velocity ≤ 1.5 m/s
- ΔT ≥ 30 K (unless justified)

### DoD Criteria
1. **CSV Files**: All CSVs present with non-empty rows and typed columns
2. **Validation Report**: A check report `eval/cha/hydraulics_check.csv` lists any violations (should be empty or justified)
3. **GIS Layers**: GPKG has layers: `mains`, `branches`, `nodes`, `service_areas`

## 3.3 Decentralized Heating Agent (DHA — pandapower)

### Deliverables
- **Load Data**: `processed/dha/feeder_loads.csv` (top-10 peak hours)
- **GIS Flags**: `processed/dha/overloads.gpkg`

### Grid Checks
- Feeder utilization ≤ 80%
- Voltage within configured limits

### DoD Criteria
1. **Violations Report**: Offenders report `eval/dha/violations.csv` generated and (ideally) empty or annotated with mitigation

## 3.4 Techno-Economic & Emissions

### Deliverables
- **LCoH Module**: `src/te/lcoh.py::compute_lcoh()` + unit tests
- **Monte Carlo Results**: N ≥ 500 results in `eval/te/mc.parquet` + `eval/te/summary.csv`

### DoD Criteria
1. **Test Coverage**: Tests for monotonicity and positivity
2. **Summary Quality**: Summary contains mean/median/95% CI; no NaNs or infs

## 3.5 End-to-End Integration

### Deliverables
`make run-branitz` produces:
- **KPI Summary**: `processed/kpi/kpi_summary.json`
- **Recommendation Report**: `docs/branitz_recommendation.html` (or .md/.pdf)

### DoD Criteria
1. **Schema Validation**: `schemas/kpi_summary.schema.json` passes for the KPI JSON
2. **Report Quality**: Report references exact artifacts and dates; links to eval plots

## Quality Assurance

### General Principles
- **Automated Validation**: All outputs must pass schema validation
- **No Hand-Editing**: Fix generators, not generated artifacts
- **Test Coverage**: Each module must have comprehensive unit tests
- **Documentation**: All outputs must be documented and traceable

### Error Handling
- **Graceful Degradation**: System should handle missing data gracefully
- **Clear Error Messages**: Errors should be actionable and specific
- **Logging**: All operations should be logged for debugging

### Performance Requirements
- **Scalability**: System should handle realistic dataset sizes
- **Memory Efficiency**: Avoid memory leaks and excessive resource usage
- **Execution Time**: End-to-end pipeline should complete within reasonable time

## Compliance Standards

### EN 13941 Compliance
- **Velocity Limits**: Maximum velocity ≤ 1.5 m/s
- **Temperature Difference**: ΔT ≥ 30 K (unless justified)
- **Pressure Drops**: Calculated using standard hydraulic formulas

### Grid Standards
- **Feeder Utilization**: Maximum 80% loading
- **Voltage Limits**: Within ±10% of nominal voltage
- **Power Quality**: Harmonic distortion within acceptable limits

### Environmental Standards
- **CO₂ Emissions**: Calculated using approved emission factors
- **Energy Efficiency**: Optimized for minimum energy consumption
- **Renewable Integration**: Support for renewable energy sources

## Validation Workflow

### Pre-Execution Checks
1. **Input Validation**: Verify all input data meets requirements
2. **Schema Compliance**: Ensure input schemas are valid
3. **Resource Availability**: Check required dependencies and resources

### Execution Monitoring
1. **Progress Tracking**: Monitor execution progress and performance
2. **Error Detection**: Identify and log any errors or warnings
3. **Resource Monitoring**: Track memory and CPU usage

### Post-Execution Validation
1. **Output Verification**: Validate all outputs against schemas
2. **Quality Checks**: Verify data quality and completeness
3. **Performance Analysis**: Review execution time and resource usage

## Maintenance and Updates

### Version Control
- **Code Changes**: All changes must be committed to version control
- **Documentation Updates**: Keep documentation synchronized with code
- **Schema Evolution**: Handle schema changes gracefully

### Testing Strategy
- **Unit Tests**: Comprehensive coverage for all functions
- **Integration Tests**: End-to-end workflow validation
- **Regression Tests**: Ensure no regressions in existing functionality

### Deployment
- **Environment Consistency**: Ensure consistent behavior across environments
- **Dependency Management**: Keep dependencies up to date and secure
- **Monitoring**: Implement monitoring for production deployments 