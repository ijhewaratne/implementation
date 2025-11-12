# Results — system
_Generated 2025-09-04T10:20:18.034812Z_

## Summary Table

| Metric | Value | Source |
|---|---:|---|
| LFA buildings | NA | processed/lfa/system |
| LFA annual heat | NA | processed/lfa/system |
| CHA total length | NA | processed/cha/system/segments.csv |
| CHA supply / return | NA | segments.csv |
| CHA mean velocity | NA | segments.csv |
| CHA max Δp | NA | segments.csv |
| CHA EN 13941 violations | NA | eval/cha/system/hydraulics_check.csv |
| DHA feeder max utilization | NA | processed/dha/system/feeder_loads.csv |
| DHA voltage violations | NA | eval/dha/system/violations.csv |
| LCoH (mean, 95% CI) | NA | eval/te/system/summary.csv |
| CO₂ (mean, 95% CI) | NA | eval/te/system/summary.csv |
| Sample size N | NA | eval/te/system/mc.parquet |
| KPI decision | NA | processed/kpi/system/kpi_summary.json |
| KPI rationale | NA | kpi_summary.json |
| Pump power | NA | kpi_summary.json |
| DH losses | NA | kpi_summary.json |
| Forecast RMSE | NA | kpi_summary.json |
| Forecast PICP90 | NA | kpi_summary.json |
| ΔT (K) | 30 | configs/eaa.yml |
| cp (J/kg·K) | 4180 | configs/eaa.yml |
| Design hours | 2000 | configs/eaa.yml |
| Convergence | NA | eval/cha/system/sim.json |
| Runtime (s) | NA | eval/cha/system/sim.json |
| COP model | constant | configs/dha.yml |
| Peak P_el | NA | configs/dha.yml + LFA data |

## Notes
- Values shown as `NA` were not found in the expected files.