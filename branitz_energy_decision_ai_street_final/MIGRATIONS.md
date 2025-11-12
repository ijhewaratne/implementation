# Schema Migrations

This document tracks changes to JSON schemas used in the Branitz Energy Decision AI project.
Each schema change must be documented here with version bumps and migration notes.

## kpi_summary.schema.json v1.0.0
- Initial contract for end-to-end scenario KPIs
- Defines required fields: x-version, scenario_name, created_utc, metrics, decision, sources
- Metrics include: lcoh_eur_per_mwh, co2_kg_per_mwh, dh_losses_pct, pump_kw, feeder_max_utilization_pct, forecast_rmse, forecast_picp_90
- Decision includes: recommended_option (DH/HP/Hybrid/Inconclusive), rationale
- Impact: All KPI writers must emit these exact fields
- Migration: Initial version, no migration needed

## lfa_demand.schema.json v1.0.0
- Initial contract for Load Forecasting Agent demand data
- Defines 8760h heat series with quantiles q10, q90
- Required fields: x-version, building_id, series, q10, q90, metadata
- Metadata includes: forecast_date, model_version
- Impact: All LFA writers must emit 8760-length arrays and metadata
- Migration: Initial version, no migration needed

---

## Migration Guidelines

### When to Bump Version
- **Patch (X.Y.Z+1)**: Bug fixes, clarifications, non-breaking changes
- **Minor (X.Y+1.0)**: New optional fields, backward-compatible additions
- **Major (X+1.0.0)**: Breaking changes, removed fields, type changes

### Required Migration Notes
For each version change, document:
1. **What changed**: Added/removed fields, type changes, new requirements
2. **Why**: Rationale for the change
3. **Impact**: Which writers/readers are affected
4. **Migration steps**: How to update code to handle the change

### Example Migration Entry
```
## schema_name.schema.json v1.1.0
- Added metrics.peak_hour_utc (ISO 8601 date-time)
- Rationale: downstream report requires timestamp of worst feeder utilization
- Impact: update KPI writer and readers; old files remain valid if field is optional
- Migration: add field in writer; handle missing in reader with fallback
``` 