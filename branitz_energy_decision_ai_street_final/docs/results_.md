# Results — 
_Generated 2025-09-04T10:20:55.454625Z_

## Summary Table

| Metric | Value | Source |
|---|---:|---|
| LFA buildings | 1 | processed/lfa/ |
| LFA annual heat | 43.80 MWh | processed/lfa/ |
| CHA total length | 0.45 km | processed/cha//segments.csv |
| CHA supply / return | NA | segments.csv |
| CHA mean velocity | 0.633 m/s | segments.csv |
| CHA max Δp | 0.040 bar | segments.csv |
| CHA EN 13941 violations | NA | eval/cha//hydraulics_check.csv |
| DHA feeder max utilization | 85.0 % | processed/dha//feeder_loads.csv |
| DHA voltage violations | NA | eval/dha//violations.csv |
| LCoH (mean, 95% CI) | 651.6 [521.7–813.5] €/MWh | eval/te//summary.csv |
| CO₂ (mean, 95% CI) | 2.30 [1.89–2.78] kg/MWh | eval/te//summary.csv |
| Sample size N | 1000 | eval/te//mc.parquet |
| KPI decision | DH | processed/kpi//kpi_summary.json |
| KPI rationale | Feeder utilization 85.0% ≥ 80% threshold. | kpi_summary.json |
| Pump power | 0.11 kW | kpi_summary.json |
| DH losses | 0.00% | kpi_summary.json |
| Forecast RMSE | 0.120 | kpi_summary.json |
| Forecast PICP90 | 0.900 | kpi_summary.json |
| ΔT (K) | 30 | configs/eaa.yml |
| cp (J/kg·K) | 4180 | configs/eaa.yml |
| Design hours | 2000 | configs/eaa.yml |
| Convergence | Yes | eval/cha//sim.json |
| Runtime (s) | 0.38 | eval/cha//sim.json |
| COP model | constant | configs/dha.yml |
| Peak P_el | 1.7 kW | configs/dha.yml + LFA data |

## Notes
- Values shown as `NA` were not found in the expected files.