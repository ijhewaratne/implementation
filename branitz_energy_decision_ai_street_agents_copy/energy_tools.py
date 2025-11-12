# energy_tools.py
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from functools import lru_cache
from typing import Dict, Any, Optional
import yaml
from adk.api.tool import tool
import pandas as pd
import glob
import re
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.ops import nearest_points
from shapely.geometry import LineString

from src.sizing.cha.cha_adapter import (
    run_cha_sizing_from_topology,
    sizing_outputs_to_serializable,
)
from src.hp.street_workflow import run_hp_street_analysis, list_available_streets
from src.hp.street_selection import DEFAULT_OSM_PATH
def _safe_read_geojson(path: Path | str) -> gpd.GeoDataFrame:
    """Read GeoJSON while tolerating mixed property types."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    gdf = gpd.GeoDataFrame.from_features(features)

    crs_info = (data.get("crs") or {}).get("properties", {}).get("name")
    if crs_info and "CRS84" in crs_info.upper():
        crs = "EPSG:4326"
    elif isinstance(crs_info, str) and crs_info.upper().startswith("EPSG:"):
        crs = crs_info.upper()
    else:
        crs = "EPSG:4326"

    try:
        gdf.set_crs(crs, inplace=True)
    except Exception:
        gdf.crs = crs

    return gdf


def _sanitize_street_dirname(street_name: str) -> str:
    safe = street_name.strip()
    if not safe:
        return "Unknown_Street"
    safe = safe.replace("/", "_")
    safe = safe.replace(" ", "-")
    return safe


def _ensure_street_output_dir(street_name: str) -> Path:
    street_dir = Path("street_analysis_outputs") / _sanitize_street_dirname(street_name)
    street_dir.mkdir(parents=True, exist_ok=True)
    return street_dir


def _legacy_map_name(street_name: str) -> str:
    return f"dual_pipe_map_dual_pipe_{_sanitize_street_dirname(street_name)}.html"


def _legacy_dashboard_name(street_name: str) -> str:
    return f"dual_pipe_dashboard_dual_pipe_{_sanitize_street_dirname(street_name)}.html"


@lru_cache(maxsize=1)
def _load_cha_config() -> Dict[str, Any]:
    """Load CHA sizing configuration."""
    config_path = Path("config") / "cha_sizing.yaml"
    if not config_path.exists():
        return {}
    try:
        with config_path.open("r", encoding="utf-8") as cfg_file:
            data = yaml.safe_load(cfg_file) or {}
            if not isinstance(data, dict):
                return {}
            return data
    except Exception:
        return {}


def _cha_fallback_settings() -> Dict[str, Any]:
    """Return fallback sizing settings with sensible defaults."""
    config = _load_cha_config()
    fallback_cfg = config.get("fallback", {}) if isinstance(config, dict) else {}

    default_diameter_mm = float(fallback_cfg.get("default_diameter_mm", 40.0))
    nominal = fallback_cfg.get("default_nominal") or fallback_cfg.get("default_diameter_dn")
    if not nominal:
        nominal = f"DN{int(round(default_diameter_mm))}"

    return {
        "default_diameter_mm": default_diameter_mm,
        "default_diameter_m": default_diameter_mm / 1000.0,
        "default_nominal": nominal,
        "source_label": fallback_cfg.get("source_label", "CHA_FALLBACK"),
        "note": fallback_cfg.get("note", "Pipe sizing fallback applied"),
        "violation_standard": fallback_cfg.get("violation_standard", "CHA"),
    }


def _apply_sizing_to_topology(topology: Dict, sizing_lookup: Dict, compliance_lookup: Dict) -> None:
    """Inject sizing/compliance metrics into the topology structure."""

    def _apply(target: Dict, pipe_id: str) -> None:
        sizing = sizing_lookup.get(pipe_id)
        if sizing is None:
            return
        target["diameter_m"] = float(sizing.diameter_m)
        target["diameter_dn"] = sizing.diameter_nominal
        target["velocity_ms"] = float(sizing.velocity_ms)
        target["pressure_drop_pa_per_m"] = float(sizing.pressure_drop_pa_per_m)
        target["pressure_drop_bar"] = float(sizing.pressure_drop_bar)
        target.setdefault("sizing_source", "CHA")

        compliance = compliance_lookup.get(pipe_id)
        if compliance is not None:
            target["standards_compliant"] = bool(compliance.overall_compliant)
            target["standards_compliance"] = dict(compliance.standards_compliance)
            target["standards_violations"] = [
                {
                    "standard": v.standard,
                    "violation_type": v.violation_type,
                    "message": v.message,
                    "severity": v.severity,
                    "current_value": v.current_value,
                    "limit_value": v.limit_value,
                }
                for v in getattr(compliance, "violations", [])
            ]
        else:
            target["standards_compliant"] = None
            target["standards_compliance"] = {}
            target["standards_violations"] = []

    compliance_lookup = compliance_lookup or {}

    for pipe in topology.get("pipes", []):
        pipe_id = str(pipe.get("id"))
        _apply(pipe, pipe_id)

    for service in topology.get("service_connections", []):
        building_id = service.get("building_id")
        if building_id is None:
            continue
        service_id = f"service_{building_id}"
        _apply(service, service_id)
        # Mirror sizing for return service connection if present
        if service.get("pipe_type") == "return_service":
            supply_service_id = f"service_{building_id}"
            if service_id != supply_service_id:
                _apply(service, supply_service_id)


def _update_stats_with_sizing(stats: Dict[str, float], topology: Dict) -> None:
    """Augment stats dict with sizing aggregates."""
    supply_diameters = [
        pipe.get("diameter_m")
        for pipe in topology.get("pipes", [])
        if pipe.get("type") == "supply" and pipe.get("diameter_m")
    ]
    return_diameters = [
        pipe.get("diameter_m")
        for pipe in topology.get("pipes", [])
        if pipe.get("type") == "return" and pipe.get("diameter_m")
    ]
    service_diameters = [
        svc.get("diameter_m")
        for svc in topology.get("service_connections", [])
        if svc.get("diameter_m")
    ]

    velocities = [
        pipe.get("velocity_ms")
        for pipe in topology.get("pipes", [])
        if pipe.get("velocity_ms") is not None
    ]
    service_velocities = [
        svc.get("velocity_ms")
        for svc in topology.get("service_connections", [])
        if svc.get("velocity_ms") is not None
    ]

    if supply_diameters:
        stats["avg_supply_diameter_mm"] = float(np.mean(supply_diameters) * 1000.0)
        stats["max_supply_diameter_mm"] = float(np.max(supply_diameters) * 1000.0)
    if return_diameters:
        stats["avg_return_diameter_mm"] = float(np.mean(return_diameters) * 1000.0)
        stats["max_return_diameter_mm"] = float(np.max(return_diameters) * 1000.0)
    if service_diameters:
        stats["avg_service_diameter_mm"] = float(np.mean(service_diameters) * 1000.0)

    if velocities:
        stats["max_pipe_velocity_ms"] = float(np.max(velocities))
    if service_velocities:
        stats["max_service_velocity_ms"] = float(np.max(service_velocities))

    non_compliant_supply = sum(
        1 for pipe in topology.get("pipes", []) if pipe.get("type") == "supply" and pipe.get("standards_compliant") is False
    )
    non_compliant_return = sum(
        1 for pipe in topology.get("pipes", []) if pipe.get("type") == "return" and pipe.get("standards_compliant") is False
    )
    non_compliant_service = sum(
        1 for svc in topology.get("service_connections", []) if svc.get("standards_compliant") is False
    )
    total_segments = (
        len(topology.get("pipes", [])) + len(topology.get("service_connections", []))
    )
    total_non_compliant = non_compliant_supply + non_compliant_return + non_compliant_service
    stats["non_compliant_supply"] = int(non_compliant_supply)
    stats["non_compliant_return"] = int(non_compliant_return)
    stats["non_compliant_services"] = int(non_compliant_service)
    stats["non_compliant_segments"] = int(total_non_compliant)
    if total_segments:
        stats["compliance_rate"] = float(1 - (total_non_compliant / total_segments))


def _apply_sizing_fallback(topology: Dict[str, Any], reason: str, analysis: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """
    Apply configurable fallback sizing when CHA sizing cannot be performed.
    Returns metadata if any segment received fallback sizing; otherwise None.
    """
    settings = _cha_fallback_settings()
    default_m = settings["default_diameter_m"]
    default_dn = settings["default_nominal"]
    source_label = settings["source_label"]
    note = reason or settings["note"]
    violation_standard = settings["violation_standard"]

    stats = topology.setdefault("stats", {})
    segments_flagged: list[str] = []

    def _flag_segment(record: Dict[str, Any], segment_id: str) -> None:
        if record.get("diameter_m"):
            return
        record["diameter_m"] = default_m
        record["diameter_dn"] = default_dn
        record["velocity_ms"] = None
        record["pressure_drop_pa_per_m"] = None
        record["pressure_drop_bar"] = None
        record["sizing_source"] = source_label
        record["sizing_status"] = "fallback"
        record["sizing_note"] = note
        record["standards_compliant"] = False
        record["standards_compliance"] = {"status": "fallback"}
        record["standards_violations"] = [
            {
                "standard": violation_standard,
                "violation_type": "fallback",
                "message": note,
                "severity": "warning",
                "current_value": None,
                "limit_value": None,
            }
        ]
        segments_flagged.append(segment_id)

    for pipe in topology.get("pipes", []):
        segment_id = str(pipe.get("id") or f"pipe_{len(segments_flagged)}")
        _flag_segment(pipe, segment_id)

    for svc in topology.get("service_connections", []):
        building_id = svc.get("building_id")
        pipe_type = svc.get("pipe_type", "service")
        segment_id = f"{building_id}_{pipe_type}"
        _flag_segment(svc, segment_id)

    if not segments_flagged:
        return None

    stats["sizing_fallback_used"] = True
    stats["sizing_fallback_reason"] = note
    stats["sizing_fallback_diameter_mm"] = settings["default_diameter_mm"]
    stats["sizing_fallback_source_label"] = source_label
    stats["sizing_fallback_segments"] = len(segments_flagged)
    stats["sizing_fallback_applied_at"] = datetime.utcnow().isoformat() + "Z"

    if analysis is not None:
        analysis["sizing_fallback_used"] = True
        analysis["sizing_fallback_reason"] = note

    fallback_meta = {
        "status": "fallback",
        "reason": note,
        "default_diameter_mm": settings["default_diameter_mm"],
        "source_label": source_label,
        "segments": segments_flagged,
        "applied_at": stats["sizing_fallback_applied_at"],
    }
    topology.setdefault("sizing_fallbacks", []).append(fallback_meta)
    return fallback_meta


# --- NEW: Visualization Tool ---
@tool
def create_network_visualization(street_name: str, scenario_type: str) -> str:
    """
    Creates and saves a PNG map visualizing the energy network for a given street.
    This tool should be called after the main simulation pipeline has run, as it
    relies on the output files from that pipeline.

    Args:
        street_name: The name of the street to visualize.
        scenario_type: The scenario type ('DH' or 'HP') to label the map correctly.

    Returns:
        A string message indicating success or failure and the path to the saved image.
    """
    print(f"TOOL: Creating visualization for '{street_name}' ({scenario_type})...")

    # Define file paths for the data generated by the main pipeline
    results_dir = "results_test/"
    buildings_path = os.path.join(results_dir, "buildings_prepared.geojson")
    streets_path = os.path.join(results_dir, "streets.geojson")
    output_image_path = os.path.join(
        results_dir, f"network_map_{street_name.replace(' ', '_')}_{scenario_type}.png"
    )

    try:
        # Load the necessary data files
        if not os.path.exists(buildings_path) or not os.path.exists(streets_path):
            return f"Error: Cannot create visualization. Required data files not found in '{results_dir}'."

        buildings_gdf = gpd.read_file(buildings_path)
        street_gdf = gpd.read_file(streets_path)

        # Ensure both layers are in the same projected CRS for accurate plotting
        utm_crs = buildings_gdf.estimate_utm_crs()
        buildings_proj = buildings_gdf.to_crs(utm_crs)
        street_proj = street_gdf.to_crs(utm_crs)

        # Calculate connection lines from buildings to the street
        street_line = street_proj.geometry.unary_union
        connection_lines = []
        for _, building in buildings_proj.iterrows():
            p_building, p_street = nearest_points(building.geometry, street_line)
            connection_lines.append(LineString([p_building, p_street]))
        connections_gdf = gpd.GeoDataFrame(geometry=connection_lines, crs=utm_crs)

        # --- Plotting Logic (from your graph2.py) ---
        fig, ax = plt.subplots(figsize=(12, 12))

        # Plot layers from bottom to top
        street_proj.plot(ax=ax, color="black", linewidth=3, label="Main Street")
        buildings_proj.plot(ax=ax, color="lightgrey", edgecolor="black")
        connections_gdf.plot(ax=ax, color="red", linewidth=1.5, label="Service Connections")

        ax.set_title(f"Energy Network for {street_name} ({scenario_type.upper()})")
        ax.set_axis_off()
        ax.set_aspect("equal", adjustable="box")
        plt.legend()
        plt.tight_layout()

        # Save the figure to a file
        plt.savefig(output_image_path, dpi=300)
        plt.close(fig)  # Close the figure to free up memory

        print(f"TOOL: Visualization saved to {output_image_path}")
        return f"Visualization created successfully. Map saved to: {output_image_path}"

    except Exception as e:
        import traceback

        return f"Error creating visualization: {traceback.format_exc()}"


# --- High-level tools now include the visualization step ---


@tool
def run_complete_dh_analysis(street_name: str) -> str:
    """Runs a complete DH analysis, generates an LLM report, and creates a visualization."""
    print(f"HIGH-LEVEL TOOL: Running complete DH analysis for '{street_name}'...")

    # Step 1: Get building IDs
    building_ids = get_building_ids_for_street.func(street_name)
    if not isinstance(building_ids, list) or not building_ids:
        return f"Could not find any buildings for '{street_name}'. Please try another street."

    # Step 2: Run simulation pipeline
    sim_result = run_simulation_pipeline.func(building_ids, "DH")
    if sim_result["status"] == "error":
        return f"DH simulation failed: {sim_result['message']}"

    # Step 3: Analyze results
    analysis_result = analyze_kpi_report.func(sim_result["kpi_path"])

    # --- NEW Step 4: Create Visualization ---
    print("\n--- Generating Visualization Map ---")
    viz_result = create_network_visualization.func(street_name, "DH")

    return f"{analysis_result}\n\n{viz_result}"

@tool
def run_hp_street_workflow(
    street_name: str,
    scenario_name: str = "hp_with_grid_reinforcement",
    buffer_m: float = 50.0,
    force: bool = False,
) -> str:
    """
    Run the advanced HP street workflow and package key KPIs/artefacts for the user.
    """
    summary = run_hp_street_analysis(
        scenario_name=scenario_name,
        street_name=street_name,
        buffer_m=buffer_m,
        force=force,
    )

    result = summary.get("result", {})
    metadata = result.get("metadata", {})
    kpi = result.get("kpi", {})
    exported = summary.get("exported_files", {})

    street = summary.get("street", street_name)
    min_voltage = kpi.get("min_voltage_pu")
    max_loading = kpi.get("max_line_loading_pct")
    trafo_loading = kpi.get("transformer_loading_pct")
    voltage_violations = kpi.get("voltage_violations", 0)
    overloaded_lines = kpi.get("overloaded_lines", 0)
    total_load_kw = metadata.get("total_load_kw", 0)
    num_buildings = metadata.get("filtered_buildings", summary.get("num_buildings"))

    def _fmt(value: object, digits: int = 3) -> str:
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return str(value)

    lines = [
        f"⚡ Heat pump street analysis complete for **{street}** (`{scenario_name}`).",
        "",
        "### Key KPIs",
        f"- Min voltage: {_fmt(min_voltage)} pu",
        f"- Max line loading: {_fmt(max_loading, 1)} %",
        f"- Transformer loading: {_fmt(trafo_loading, 1)} %",
        f"- Voltage violations: {voltage_violations}",
        f"- Overloaded lines: {overloaded_lines}",
        f"- Connected buildings: {num_buildings or 'N/A'}",
        f"- Total electrical load: {_fmt(total_load_kw, 1)} kW",
        "",
    ]

    if metadata.get("buffer_m") is not None:
        lines.append(f"Selection buffer: {metadata['buffer_m']} m")
    nodes_file = summary.get("nodes_file") or metadata.get("nodes_file")
    if nodes_file:
        lines.append(f"LV nodes file: `{nodes_file}`")
    lines.append("")

    artefact_lines = []
    artefact_map = {
        "buses_results": "Buses GeoJSON",
        "lines_results": "Lines GeoJSON",
        "kpis": "KPI snapshot JSON",
        "violations": "Violations CSV",
        "interactive_map": "Interactive HP map",
    }
    for key, label in artefact_map.items():
        path = exported.get(key) or summary.get(key)
        if path:
            artefact_lines.append(f"- {label}: `{path}`")

    artefact_lines.append(f"- Workflow summary: `{summary.get('results_file')}`")

    if artefact_lines:
        lines.append("### Outputs")
        lines.extend(artefact_lines)

    if voltage_violations or overloaded_lines:
        lines.append("")
        lines.append("⚠️ Review the violations CSV and KPI JSON for detailed remediation guidance.")

    return "\n".join(lines)

@tool
def compare_hp_variants(
    street_name: str,
    baseline_scenario: str = "hp_base_case",
    variant_scenario: str = "hp_with_grid_reinforcement",
    buffer_m: float = 50.0,
    force: bool = False,
) -> str:
    """
    Compare two HP scenarios for the same street (e.g. base grid vs reinforced).
    """
    baseline = run_hp_street_analysis(
        scenario_name=baseline_scenario,
        street_name=street_name,
        buffer_m=buffer_m,
        force=force,
    )
    variant = run_hp_street_analysis(
        scenario_name=variant_scenario,
        street_name=street_name,
        buffer_m=buffer_m,
        force=force,
    )

    def _kpi(summary: Dict[str, Any]) -> Dict[str, Any]:
        return summary.get("result", {}).get("kpi", {}) if summary else {}

    base_kpi = _kpi(baseline)
    var_kpi = _kpi(variant)

    def _fmt(value: Any, digits: int = 3) -> str:
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return str(value)

    def _delta(new: Any, old: Any, digits: int = 3) -> str:
        if new is None or old is None:
            return "N/A"
        try:
            diff = float(new) - float(old)
            sign = "+" if diff >= 0 else ""
            return f"{sign}{diff:.{digits}f}"
        except (TypeError, ValueError):
            return "N/A"

    base_violations = (
        base_kpi.get("voltage_violations", 0) + base_kpi.get("overloaded_lines", 0)
    )
    var_violations = (
        var_kpi.get("voltage_violations", 0) + var_kpi.get("overloaded_lines", 0)
    )

    lines = [
        f"⚖️ HP scenario comparison for **{street_name}**",
        f"- Baseline scenario: `{baseline_scenario}`",
        f"- Variant scenario: `{variant_scenario}`",
        "",
        "### Voltage profile",
        f"- Min voltage (baseline): {_fmt(base_kpi.get('min_voltage_pu'))} pu",
        f"- Min voltage (variant): {_fmt(var_kpi.get('min_voltage_pu'))} pu "
        f"({_delta(var_kpi.get('min_voltage_pu'), base_kpi.get('min_voltage_pu'))})",
        "",
        "### Line loading",
        f"- Max loading (baseline): {_fmt(base_kpi.get('max_line_loading_pct'), 1)} %",
        f"- Max loading (variant): {_fmt(var_kpi.get('max_line_loading_pct'), 1)} % "
        f"({_delta(var_kpi.get('max_line_loading_pct'), base_kpi.get('max_line_loading_pct'), 1)} %)",
        "",
        "### Transformer",
        f"- Loading (baseline): {_fmt(base_kpi.get('transformer_loading_pct'), 1)} %",
        f"- Loading (variant): {_fmt(var_kpi.get('transformer_loading_pct'), 1)} % "
        f"({_delta(var_kpi.get('transformer_loading_pct'), base_kpi.get('transformer_loading_pct'), 1)} %)",
        "",
        "### Violations",
        f"- Baseline: voltage={base_kpi.get('voltage_violations', 0)}, "
        f"lines={base_kpi.get('overloaded_lines', 0)}",
        f"- Variant: voltage={var_kpi.get('voltage_violations', 0)}, "
        f"lines={var_kpi.get('overloaded_lines', 0)}",
    ]

    if base_violations > 0 and var_violations == 0:
        lines.append("✅ Reinforced scenario clears all violations observed in the baseline.")
    elif var_violations < base_violations:
        lines.append("✅ Reinforced scenario reduces the number of violations.")
    elif var_violations > base_violations:
        lines.append("⚠️ Reinforced scenario introduces additional violations—review configuration.")
    else:
        lines.append("ℹ️ No change in violation counts between scenarios.")

    def _artefact_block(summary: Dict[str, Any], label: str) -> List[str]:
        exported = summary.get("exported_files", {})
        items = []
        for key, description in {
            "buses_results": "Buses GeoJSON",
            "lines_results": "Lines GeoJSON",
            "kpis": "KPI JSON",
            "violations": "Violations CSV",
            "interactive_map": "Interactive map",
        }.items():
            path = exported.get(key) or summary.get(key)
            if path:
                items.append(f"  • {description}: `{path}`")
        return [f"**{label} artefacts**:"] + items if items else []

    lines.append("")
    lines.extend(_artefact_block(baseline, "Baseline"))
    lines.extend([""] + _artefact_block(variant, "Variant"))

    if base_kpi and var_kpi:
        load_delta = _delta(var_kpi.get("total_load_mw"), base_kpi.get("total_load_mw"), 4)
        loss_delta = _delta(var_kpi.get("total_losses_mw"), base_kpi.get("total_losses_mw"), 4)
        lines.extend(
            [
                "",
                "### Additional insights",
                f"- Total load delta (MW): {load_delta}",
                f"- Network losses delta (MW): {loss_delta}",
            ]
        )

    lines.append("")
    lines.append("Tip: open both interactive maps to visually compare reinforcement effects.")

    return "\n".join(lines)

@tool
def compare_hp_variants(
    street_name: str,
    base_scenario: str = "hp_base_case",
    variant_scenario: str = "hp_with_grid_reinforcement",
    buffer_m: float = 50.0,
    force: bool = False,
) -> str:
    """
    Run two HP scenarios for the same street and report KPI deltas.
    """
    base_summary = run_hp_street_analysis(
        scenario_name=base_scenario,
        street_name=street_name,
        buffer_m=buffer_m,
        force=force,
    )
    variant_summary = run_hp_street_analysis(
        scenario_name=variant_scenario,
        street_name=street_name,
        buffer_m=buffer_m,
        force=force,
    )

    base_result = base_summary.get("result", {})
    variant_result = variant_summary.get("result", {})
    if not base_result.get("success"):
        return f"Base scenario `{base_scenario}` failed: {base_result.get('error', 'unknown error')}"
    if not variant_result.get("success"):
        return f"Variant scenario `{variant_scenario}` failed: {variant_result.get('error', 'unknown error')}"

    base_kpi = base_result.get("kpi", {})
    variant_kpi = variant_result.get("kpi", {})
    base_meta = base_result.get("metadata", {})
    variant_meta = variant_result.get("metadata", {})

    kpi_keys = [
        "min_voltage_pu",
        "max_line_loading_pct",
        "avg_line_loading_pct",
        "transformer_loading_pct",
        "voltage_violations",
        "overloaded_lines",
        "total_losses_mw",
    ]

    def _float(value: float | int | None) -> float:
        if value is None:
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    diff = {
        key: _float(variant_kpi.get(key)) - _float(base_kpi.get(key))
        for key in kpi_keys
    }

    street_dir = _ensure_street_output_dir(street_name)
    compare_dir = street_dir / "hp" / "variant_comparisons"
    compare_dir.mkdir(parents=True, exist_ok=True)

    base_slug = _sanitize_street_dirname(base_scenario)
    variant_slug = _sanitize_street_dirname(variant_scenario)
    compare_path = compare_dir / f"{base_slug}_vs_{variant_slug}.json"

    comparison_payload = {
        "street": street_name,
        "buffer_m": buffer_m,
        "base": {
            "scenario": base_scenario,
            "kpi": base_kpi,
            "metadata": base_meta,
            "exported_files": base_summary.get("exported_files", {}),
        },
        "variant": {
            "scenario": variant_scenario,
            "kpi": variant_kpi,
            "metadata": variant_meta,
            "exported_files": variant_summary.get("exported_files", {}),
        },
        "difference": diff,
    }
    with compare_path.open("w", encoding="utf-8") as f:
        json.dump(comparison_payload, f, indent=2)

    def _fmt(value: float | int | None, digits: int = 3) -> str:
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return str(value)

    base_min_v = base_kpi.get("min_voltage_pu")
    variant_min_v = variant_kpi.get("min_voltage_pu")
    base_max_load = base_kpi.get("max_line_loading_pct")
    variant_max_load = variant_kpi.get("max_line_loading_pct")

    lines = [
        f"⚖️ HP variant comparison for **{street_name}**:",
        "",
        f"• Base `{base_scenario}` → min voltage {_fmt(base_min_v)} pu, max loading {_fmt(base_max_load, 1)} %, "
        f"violations {base_kpi.get('voltage_violations', 0)} buses / {base_kpi.get('overloaded_lines', 0)} lines.",
        f"• Variant `{variant_scenario}` → min voltage {_fmt(variant_min_v)} pu, max loading {_fmt(variant_max_load, 1)} %, "
        f"violations {variant_kpi.get('voltage_violations', 0)} buses / {variant_kpi.get('overloaded_lines', 0)} lines.",
        "",
        "ΔKPIs (variant − base):",
        f"- Min voltage: {_fmt(diff['min_voltage_pu'])} pu",
        f"- Max line loading: {_fmt(diff['max_line_loading_pct'], 1)} %",
        f"- Transformer loading: {_fmt(diff['transformer_loading_pct'], 1)} %",
        f"- Voltage violations: {diff['voltage_violations']:+.0f}",
        f"- Overloaded lines: {diff['overloaded_lines']:+.0f}",
        "",
        f"📄 Comparison JSON saved to `{compare_path}`",
    ]

    base_exports = base_summary.get("exported_files", {})
    variant_exports = variant_summary.get("exported_files", {})
    if base_exports or variant_exports:
        lines.append("")
        lines.append("Key artefacts:")
        if base_exports:
            lines.append(f"- Base exports: `{base_exports.get('buses_results')}`, `{base_exports.get('lines_results')}`, `{base_exports.get('kpis')}`")
        if variant_exports:
            lines.append(f"- Variant exports: `{variant_exports.get('buses_results')}`, `{variant_exports.get('lines_results')}`, `{variant_exports.get('kpis')}`")

    return "\n".join(lines)


@tool
def run_complete_hp_analysis(street_name: str) -> str:
    """Runs a complete HP analysis, generates an LLM report, and creates a visualization."""
    print(f"HIGH-LEVEL TOOL: Running complete HP analysis for '{street_name}'...")

    # Step 1: Get building IDs
    building_ids = get_building_ids_for_street.func(street_name)
    if not isinstance(building_ids, list) or not building_ids:
        return f"Could not find any buildings for '{street_name}'. Please try another street."

    # Step 2: Run simulation pipeline
    sim_result = run_simulation_pipeline.func(building_ids, "HP")
    if sim_result["status"] == "error":
        return f"HP simulation failed: {sim_result['message']}"

    # Step 3: Analyze results
    analysis_result = analyze_kpi_report.func(sim_result["kpi_path"])

    # --- NEW Step 4: Create Visualization ---
    print("\n--- Generating Visualization Map ---")
    viz_result = create_network_visualization.func(street_name, "HP")

    return f"{analysis_result}\n\n{viz_result}"


# --- Other tools remain the same ---


@tool
def get_all_street_names() -> list[str]:
    """Returns a list of all available street names in the dataset."""
    full_data_geojson = "data/geojson/hausumringe_mit_adressenV3.geojson"
    try:
        with open(full_data_geojson, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return ["Error: Main data file not found."]
    street_names = {
        adr.get("str").strip()
        for feat in data["features"]
        for adr in feat.get("adressen", [])
        if adr.get("str")
    }
    return sorted(list(street_names))


@tool
def list_available_results() -> str:
    """Lists all available result files and their locations."""
    result_dir = "results_test"
    if not os.path.exists(result_dir):
        return "No results directory found."
    files = glob.glob(f"{result_dir}/**", recursive=True)
    if not files:
        return "The results directory is empty."
    output = "=== AVAILABLE RESULT FILES ===\n" + "\n".join(
        [f"• {f}" for f in sorted(files) if os.path.isfile(f)]
    )
    return output


@tool
def get_building_ids_for_street(street_name: str) -> list[str]:
    """Finds and returns a list of building IDs located on a specific street."""
    full_data_geojson = "data/geojson/hausumringe_mit_adressenV3.geojson"
    try:
        with open(full_data_geojson, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return ["Error: Main data file not found."]
    street_set = {street_name.strip().lower()}
    selected_ids = {
        feat.get("gebaeude", {}).get("oi")
        for feat in data["features"]
        for adr in feat.get("adressen", [])
        if adr.get("str")
        and adr.get("str").strip().lower() in street_set
        and feat.get("gebaeude", {}).get("oi")
    }
    return list(selected_ids)


@tool
def run_simulation_pipeline(building_ids: list[str], scenario_type: str) -> dict:
    """Runs the energy simulation pipeline. Returns a dictionary with status and KPI path."""
    base_config_path = "run_all_test.yaml"
    dynamic_config_path = f"config_{scenario_type}_run.yaml"
    try:
        with open(base_config_path, "r") as f:
            config_data = yaml.safe_load(f)
    except FileNotFoundError:
        return {"status": "error", "message": f"Base config not found at '{base_config_path}'"}
    config_data["selected_buildings"] = building_ids
    config_data["scenario_config_file"] = f"scenarios_{scenario_type.lower()}.yaml"
    with open(dynamic_config_path, "w") as f:
        yaml.dump(config_data, f, sort_keys=False)
    try:
        subprocess.run(
            [sys.executable, "main.py", "--config", dynamic_config_path],
            check=True,
            capture_output=True,
            text=True,
        )
        kpi_path = os.path.join(config_data.get("output_dir", "results_test/"), "scenario_kpis.csv")
        return {"status": "success", "kpi_path": kpi_path}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Pipeline failed: {e.stderr}"}


@tool
def analyze_kpi_report(kpi_report_path: str, comparison_prompt: str = "") -> str:
    """Analyzes a KPI report file using an LLM."""
    if not os.path.exists(kpi_report_path):
        return f"Error: KPI report not found at '{kpi_report_path}'"
    try:
        scenario_file = "scenarios_dh.yaml"
        if "hp" in kpi_report_path.lower() or "comparison" in kpi_report_path.lower():
            scenario_file = "scenarios_hp.yaml"  # Needs better logic for comparison
        output_report_file = "results_test/llm_final_report.md"
        with open("run_all_test.yaml", "r") as f:
            main_config = yaml.safe_load(f)
        command = [
            sys.executable,
            "src/llm_reporter.py",
            "--kpis",
            kpi_report_path,
            "--scenarios",
            scenario_file,
            "--output",
            output_report_file,
            "--model",
            main_config.get("llm_model", "gpt-4o"),
            "--api_key",
            main_config.get("openai_api_key", ""),
        ]
        if comparison_prompt:
            command.extend(["--config", json.dumps({"extra_prompt": comparison_prompt})])
        subprocess.run(command, check=True, capture_output=True, text=True)
        with open(output_report_file, "r", encoding="utf-8") as f:
            return f"KPI analysis complete. Here is the summary:\n\n{f.read()}"
    except Exception as e:
        return f"Error analyzing KPI report: {str(e)}"


@tool
def compare_scenarios(street_name: str) -> str:
    """Runs both DH and HP scenarios for a street, then generates a comparative analysis."""
    building_ids = get_building_ids_for_street.func(street_name)
    if not isinstance(building_ids, list) or not building_ids:
        return f"Could not find buildings for '{street_name}'."
    dh_result = run_simulation_pipeline.func(building_ids, "DH")
    if dh_result["status"] == "error":
        return f"Failed to run DH scenario: {dh_result['message']}"
    hp_result = run_simulation_pipeline.func(building_ids, "HP")
    if hp_result["status"] == "error":
        return f"Failed to run HP scenario: {hp_result['message']}"
    dh_kpis = pd.read_csv(dh_result["kpi_path"])
    dh_kpis["scenario_type"] = "DH"
    hp_kpis = pd.read_csv(hp_result["kpi_path"])
    hp_kpis["scenario_type"] = "HP"
    combined_kpis = pd.concat([dh_kpis, hp_kpis], ignore_index=True)
    comparison_kpi_path = "results_test/kpi_comparison.csv"
    combined_kpis.to_csv(comparison_kpi_path, index=False)
    comparison_prompt = "The user wants a direct comparison between the DH and HP scenarios. Please highlight the key trade-offs in terms of cost (LCoH), emissions (CO2), and any other significant differences. Conclude with a clear recommendation based on the data."
    return analyze_kpi_report.func(comparison_kpi_path, comparison_prompt=comparison_prompt)


# =============================================================================
# Advanced Visualization Tools
# =============================================================================

@tool
def create_interactive_map(
    scenario_name: str,
    visualization_type: str = "temperature",
    force_recompute: bool = False,
) -> str:
    """
    Creates an interactive HTML map with color-coded cascading visualizations.
    
    This generates a web-based interactive map that can be opened in any browser,
    featuring:
    - For DH: Temperature cascading gradients (red supply, blue return)
    - For HP: Voltage cascading gradients (green/yellow/red)
    - Clickable network elements with detailed KPIs
    - Hover tooltips
    - Statistics panels
    - Performance dashboards
    
    Args:
        scenario_name: Name of the scenario (e.g., "Parkstrasse_DH" or "Parkstrasse_HP")
        visualization_type: Type of visualization - "temperature" (DH), "voltage" (HP), or "pressure"
    
    Returns:
        Path to the generated HTML file and success message
    """
    print(f"TOOL: Creating interactive map for '{scenario_name}' (type: {visualization_type})...")
    
    try:
        from src.visualization import InteractiveMapGenerator
        from pathlib import Path
        
        # Load simulation results to determine type
        results_file = f"simulation_outputs/{scenario_name}_results.json"
        if not os.path.exists(results_file):
            return f"Error: Simulation results not found at '{results_file}'. Please run the simulation first."
        
        with open(results_file, 'r') as f:
            result = json.load(f)
        
        scenario_type = result.get('type', 'DH')
        kpi = result.get('kpi', {})
        
        # Load buildings if available
        buildings_path = "results_test/buildings_prepared.geojson"
        buildings_gdf = None
        if os.path.exists(buildings_path):
            buildings_gdf = _safe_read_geojson(buildings_path)
        
        # Generate interactive map
        map_gen = InteractiveMapGenerator()
        
        if scenario_type == 'DH':
            routing_dir = Path(f"results_test/routing/{scenario_name}")
            dual_topology = None
            thermal_profile = None
            routing_analysis = None

            if routing_dir.exists():
                dual_topology_path = routing_dir / "dual_topology.json"
                thermal_profile_path = routing_dir / "routing_thermal_profile.json"
                analysis_path = routing_dir / "routing_analysis.csv"

                if dual_topology_path.exists():
                    with open(dual_topology_path, "r", encoding="utf-8") as f:
                        dual_topology = json.load(f)

                if thermal_profile_path.exists():
                    with open(thermal_profile_path, "r", encoding="utf-8") as f:
                        thermal_profile = json.load(f)

                if analysis_path.exists():
                    try:
                        routing_df = pd.read_csv(analysis_path)
                        if not routing_df.empty:
                            routing_analysis = routing_df.iloc[0].to_dict()
                    except Exception:
                        routing_analysis = None

            if dual_topology is None:
                return (
                    "Error: Dual-pipe routing data not found. Run 'optimize_network_routing' first "
                    "to generate the topology and thermal metadata."
                )
            existing_map = Path("results_test/visualizations/interactive") / f"{scenario_name}_dh_interactive.html"
            if existing_map.exists() and not force_recompute:
                street_name = result.get("street_name", scenario_name)
                street_dir = _ensure_street_output_dir(street_name)
                legacy_map_path = street_dir / _legacy_map_name(street_name)
                if legacy_map_path.exists():
                    return (
                        "Interactive DH map already exists; skipping regeneration "
                        "(use force_recompute=True to regenerate)."
                    )

            html_file = map_gen.create_dh_interactive_map(
                scenario_name=scenario_name,
                net=None,
                buildings_gdf=buildings_gdf,
                kpi=kpi,
                dual_topology=dual_topology,
                thermal_profile=thermal_profile,
                routing_analysis=routing_analysis,
            )

            street_name = result.get("street_name", scenario_name)
            street_dir = _ensure_street_output_dir(street_name)
            legacy_map_path = street_dir / _legacy_map_name(street_name)
            try:
                shutil.copy2(html_file, legacy_map_path)
            except Exception as copy_err:
                print(f"⚠️  Unable to copy map to legacy path: {copy_err}")
            msg = "Interactive DH map created with dual-pipe temperature and pressure overlays."
        else:  # HP
            metadata = result.get("metadata", {})
            exported_files = metadata.get("exported_files") or result.get("exported_files") or {}
            buses_path = exported_files.get("buses_results")
            lines_path = exported_files.get("lines_results")
            violations_path = exported_files.get("violations")
            html_file = map_gen.create_hp_interactive_map(
                scenario_name=scenario_name,
                buildings_gdf=buildings_gdf,
                kpi=kpi,
                buses_data=buses_path,
                lines_data=lines_path,
                violations_data=violations_path,
                metadata=metadata,
            )
            msg = f"Interactive HP map created with voltage gradients."
        
        return f"{msg}\nHTML file saved to: {html_file}\n\nYou can open this file in any web browser to explore the network interactively."
    
    except Exception as e:
        import traceback
        return f"Error creating interactive map: {traceback.format_exc()}"


@tool
def create_summary_dashboard(scenario_name: str) -> str:
    """
    Creates a comprehensive 12-panel summary dashboard for a scenario.
    
    This generates a high-resolution (300 DPI) PNG dashboard with:
    - Key Performance Indicators
    - Network topology schematic
    - Performance metrics (thermal/voltage, hydraulic/loading)
    - Efficiency indicators
    - Technical specifications
    - Performance scores
    - Summary statistics
    
    For DH scenarios: Includes thermal performance, hydraulic metrics, heat losses
    For HP scenarios: Includes voltage profile, line loading, transformer analysis
    
    Args:
        scenario_name: Name of the scenario (e.g., "Parkstrasse_DH" or "Parkstrasse_HP")
    
    Returns:
        Path to the generated PNG dashboard and success message
    """
    print(f"TOOL: Creating summary dashboard for '{scenario_name}'...")
    
    try:
        from src.dashboards import SummaryDashboard
        
        # Load simulation results
        results_file = f"simulation_outputs/{scenario_name}_results.json"
        if not os.path.exists(results_file):
            return f"Error: Simulation results not found at '{results_file}'. Please run the simulation first."
        
        with open(results_file, 'r') as f:
            result = json.load(f)
        
        scenario_type = result.get('type', 'DH')
        kpi = result.get('kpi', {})
        metadata = result.get('metadata', {})
        
        # Generate dashboard
        dashboard = SummaryDashboard()
        
        if scenario_type == 'DH':
            png_file = dashboard.create_dh_summary(kpi, scenario_name, metadata)
            msg = f"DH summary dashboard created with 12 comprehensive panels including thermal performance, hydraulic metrics, and heat loss analysis."
        else:  # HP
            png_file = dashboard.create_hp_summary(kpi, scenario_name, metadata)
            msg = f"HP summary dashboard created with 12 comprehensive panels including voltage profile, line loading, and transformer analysis."
        
        return f"{msg}\n\nDashboard saved to: {png_file}\n\nThis 300 DPI PNG is suitable for reports and presentations."
    
    except Exception as e:
        import traceback
        return f"Error creating summary dashboard: {traceback.format_exc()}"


@tool
def create_comparison_dashboard(dh_scenario: str, hp_scenario: str) -> str:
    """
    Creates a DH vs HP comparison dashboard for decision support.
    
    This generates a comprehensive comparison dashboard with:
    - Economic comparison (LCoH, CAPEX, OPEX)
    - Environmental comparison (CO₂ emissions)
    - Technical metrics comparison
    - Efficiency comparison
    - Automated recommendation (winner highlighted)
    
    The dashboard provides clear visual decision support for choosing
    between district heating and heat pump scenarios.
    
    Args:
        dh_scenario: Name of the DH scenario (e.g., "Parkstrasse_DH")
        hp_scenario: Name of the HP scenario (e.g., "Parkstrasse_HP")
    
    Returns:
        Path to the generated comparison dashboard and recommendation
    """
    print(f"TOOL: Creating comparison dashboard: '{dh_scenario}' vs '{hp_scenario}'...")
    
    try:
        from src.dashboards import ComparisonDashboard
        
        # Load DH results
        dh_results_file = f"simulation_outputs/{dh_scenario}_results.json"
        if not os.path.exists(dh_results_file):
            return f"Error: DH results not found at '{dh_results_file}'. Please run DH simulation first."
        
        # Load HP results
        hp_results_file = f"simulation_outputs/{hp_scenario}_results.json"
        if not os.path.exists(hp_results_file):
            return f"Error: HP results not found at '{hp_results_file}'. Please run HP simulation first."
        
        with open(dh_results_file, 'r') as f:
            dh_result = json.load(f)
        
        with open(hp_results_file, 'r') as f:
            hp_result = json.load(f)
        
        dh_kpi = dh_result.get('kpi', {})
        hp_kpi = hp_result.get('kpi', {})
        
        # Add LCoH and CO2 from KPI calculator if available
        kpi_csv_path = "results_test/scenario_kpis.csv"
        if os.path.exists(kpi_csv_path):
            kpi_df = pd.read_csv(kpi_csv_path)
            
            # Find DH row
            dh_row = kpi_df[kpi_df['scenario'] == dh_scenario]
            if not dh_row.empty:
                dh_kpi['lcoh_eur_per_mwh'] = dh_row.iloc[0].get('lcoh_eur_per_mwh', 0)
                dh_kpi['co2_t_per_a'] = dh_row.iloc[0].get('co2_t_per_a', 0)
            
            # Find HP row
            hp_row = kpi_df[kpi_df['scenario'] == hp_scenario]
            if not hp_row.empty:
                hp_kpi['lcoh_eur_per_mwh'] = hp_row.iloc[0].get('lcoh_eur_per_mwh', 0)
                hp_kpi['co2_t_per_a'] = hp_row.iloc[0].get('co2_t_per_a', 0)
        
        # Generate comparison dashboard
        comparison = ComparisonDashboard()
        png_file = comparison.create_comparison(dh_kpi, hp_kpi, dh_scenario, hp_scenario)
        
        # Determine winner for message
        dh_total = (comparison._calculate_economic_score(dh_kpi) + 
                   comparison._calculate_environmental_score(dh_kpi) + 
                   comparison._calculate_technical_score(dh_kpi, "DH")) / 3
        hp_total = (comparison._calculate_economic_score(hp_kpi) + 
                   comparison._calculate_environmental_score(hp_kpi) + 
                   comparison._calculate_technical_score(hp_kpi, "HP")) / 3
        
        if dh_total > hp_total:
            winner = "DISTRICT HEATING"
            margin = dh_total - hp_total
        else:
            winner = "HEAT PUMPS"
            margin = hp_total - dh_total
        
        msg = f"Comparison dashboard created!\n\n"
        msg += f"📊 Overall Scores:\n"
        msg += f"  • District Heating: {dh_total:.1f}/100\n"
        msg += f"  • Heat Pumps: {hp_total:.1f}/100\n\n"
        msg += f"🎯 Recommendation: {winner}\n"
        msg += f"Margin: {margin:.1f} points\n\n"
        msg += f"Dashboard saved to: {png_file}\n\n"
        msg += f"The dashboard includes economic, environmental, and technical comparisons with an automated recommendation."
        
        return msg
    
    except Exception as e:
        import traceback
        return f"Error creating comparison dashboard: {traceback.format_exc()}"


@tool
def create_html_dashboard(
    scenario_name: str,
    dashboard_type: str = "auto",
    force_recompute: bool = False,
) -> str:
    """
    Creates a comprehensive HTML dashboard (web page) for a scenario.
    
    This generates a full-featured HTML web page that combines:
    - Metrics/KPIs in styled cards
    - Embedded interactive map (iframe)
    - Charts/visualizations (base64-encoded)
    - JavaScript interactivity
    - Professional styling
    - Responsive design
    
    The HTML dashboard can be opened in any web browser and provides
    a comprehensive, interactive view of the simulation results.
    
    Args:
        scenario_name: Name of the scenario (e.g., "Parkstrasse_DH", "Parkstrasse_HP")
        dashboard_type: Type of dashboard ("auto", "dh", "hp")
                       "auto" automatically detects from scenario name
    
    Returns:
        Path to the generated HTML dashboard file
    """
    print(f"TOOL: Creating HTML dashboard for '{scenario_name}'...")
    
    try:
        from src.dashboards import HTMLDashboardGenerator
        from pathlib import Path
        
        # Auto-detect type from scenario name
        if dashboard_type == "auto":
            scenario_lower = scenario_name.lower()
            if "_dh" in scenario_lower or "district" in scenario_lower:
                dashboard_type = "dh"
            elif "_hp" in scenario_lower or "heat_pump" in scenario_lower or "heatpump" in scenario_lower:
                dashboard_type = "hp"
            else:
                return f"Error: Cannot auto-detect dashboard type. Please specify 'dh' or 'hp'."
        
        # Load simulation results
        results_file = f"simulation_outputs/{scenario_name}_results.json"
        if not os.path.exists(results_file):
            return f"Error: Simulation results not found at '{results_file}'. Please run simulation first."
        
        with open(results_file, 'r') as f:
            result = json.load(f)
        
        kpi = result.get('kpi', {})
        
        # Extract metadata
        street_name = result.get('street_name', scenario_name)
        metadata = {
            'street_name': street_name,
            'buildings': result.get('num_buildings', 0),
            'timestamp': result.get('timestamp', 'N/A')
        }
        result_metadata = result.get("metadata")
        if isinstance(result_metadata, dict):
            metadata.update(result_metadata)
        
        # Add LCoH and CO2 from KPI calculator if available
        kpi_csv_path = "results_test/scenario_kpis.csv"
        if os.path.exists(kpi_csv_path):
            kpi_df = pd.read_csv(kpi_csv_path)
            row = kpi_df[kpi_df['scenario'] == scenario_name]
            if not row.empty:
                kpi['lcoh_eur_per_mwh'] = row.iloc[0].get('lcoh_eur_per_mwh', 0)
                kpi['co2_t_per_a'] = row.iloc[0].get('co2_t_per_a', 0)
        
        # Find interactive map file
        map_file = None
        interactive_maps_dir = Path("results_test/visualizations/interactive")
        if interactive_maps_dir.exists():
            # Look for map file matching scenario
            map_files = list(interactive_maps_dir.glob(f"{scenario_name}*.html"))
            if map_files:
                map_file = str(map_files[0])
        
        # Find chart files
        chart_files = []
        dashboards_dir = Path("results_test/visualizations/dashboards")
        if dashboards_dir.exists():
            # Look for PNG dashboards (can be embedded as charts)
            png_files = list(dashboards_dir.glob(f"{scenario_name}*.png"))
            chart_files = [str(f) for f in png_files]
        
        routing_analysis = None
        dual_topology = None
        thermal_profile = None
        if dashboard_type == "dh":
            routing_dir = Path(f"results_test/routing/{scenario_name}")
            if routing_dir.exists():
                dual_topology_path = routing_dir / "dual_topology.json"
                thermal_profile_path = routing_dir / "routing_thermal_profile.json"
                analysis_path = routing_dir / "routing_analysis.csv"

                if dual_topology_path.exists():
                    with open(dual_topology_path, "r", encoding="utf-8") as f:
                        dual_topology = json.load(f)
                if thermal_profile_path.exists():
                    with open(thermal_profile_path, "r", encoding="utf-8") as f:
                        thermal_profile = json.load(f)
                if analysis_path.exists():
                    try:
                        routing_df = pd.read_csv(analysis_path)
                        if not routing_df.empty:
                            routing_analysis = routing_df.iloc[0].to_dict()
                    except Exception:
                        routing_analysis = None

        # Create HTML dashboard
        street_dir = _ensure_street_output_dir(street_name)
        legacy_map_name = _legacy_map_name(street_name)
        legacy_map_path = street_dir / legacy_map_name
        legacy_dashboard_name = _legacy_dashboard_name(street_name)
        legacy_dashboard_path = street_dir / legacy_dashboard_name
        street_slug = _sanitize_street_dirname(street_name)
        existing_dashboard = (
            Path("results_test/visualizations/html_dashboards")
            / f"{scenario_name}_dh_html_dashboard.html"
        )
        if (
            not force_recompute
            and legacy_dashboard_path.exists()
            and existing_dashboard.exists()
        ):
            return (
                "HTML dashboard already exists; skipping regeneration (use force_recompute=True to regenerate). "
                "HTML dashboard created previously."
            )

        routing_dir = Path(f"results_test/routing/{scenario_name}")

        generated_file_paths = []
        hp_insights: Optional[Dict[str, Any]] = None
        hp_output_dir: Optional[Path] = None

        def _add_generated(label: str, path: Path):
            if path and path.exists():
                generated_file_paths.append({"label": label, "path": path})

        map_file_path = map_file
        if map_file_path:
            try:
                if legacy_map_path.exists():
                    legacy_map_path.unlink()
                shutil.copy2(map_file_path, legacy_map_path)
            except Exception as copy_err:
                print(f"⚠️  Unable to copy map for dashboard: {copy_err}")
        _add_generated("Interactive Map", legacy_map_path)

        if dashboard_type == "dh":
            _add_generated("Supply Pipes CSV", routing_dir / f"dual_supply_pipes_dual_pipe_{street_slug}.csv")
            _add_generated("Return Pipes CSV", routing_dir / f"dual_return_pipes_dual_pipe_{street_slug}.csv")
            _add_generated("Service Connections CSV", routing_dir / f"dual_service_connections_dual_pipe_{street_slug}.csv")
            _add_generated("Network Statistics", routing_dir / f"dual_network_stats_dual_pipe_{street_slug}.json")
            _add_generated("Simulation Results", routing_dir / f"pandapipes_simulation_results_dual_pipe_{street_slug}.json")
            _add_generated("Thermal Profile", routing_dir / "routing_thermal_profile.json")
            _add_generated("Pipe Sizing Summary", routing_dir / f"dual_pipe_sizing_dual_pipe_{street_slug}.json")
            _add_generated("Markdown Report", routing_dir / f"dual_pipe_report_dual_pipe_{street_slug}.md")
        elif dashboard_type == "hp":
            hp_dir_candidate = street_dir / "hp" / scenario_name
            if hp_dir_candidate.exists():
                hp_output_dir = hp_dir_candidate
            elif map_file_path:
                try:
                    hp_output_dir = Path(map_file_path).resolve().parent
                except Exception:
                    hp_output_dir = None
            if hp_output_dir and hp_output_dir.exists():
                metadata["hp_output_dir"] = str(hp_output_dir)

                def _first_file(pattern: str) -> Optional[Path]:
                    matches = sorted(hp_output_dir.glob(pattern))
                    return matches[0] if matches else None

                buses_file = _first_file("*_buses_results.geojson")
                lines_file = _first_file("*_lines_results.geojson")
                kpi_file = _first_file("*_kpis.json")
                violations_file = _first_file("*_violations.csv")

                if buses_file:
                    _add_generated("Buses GeoJSON", buses_file)
                if lines_file:
                    _add_generated("Lines GeoJSON", lines_file)
                if kpi_file:
                    _add_generated("KPI Summary", kpi_file)
                if violations_file:
                    _add_generated("Violations CSV", violations_file)

                insights: Dict[str, Any] = {}
                if kpi_file:
                    try:
                        with kpi_file.open("r", encoding="utf-8") as f:
                            kpi_summary = json.load(f)
                        if isinstance(kpi_summary, dict):
                            metadata["hp_kpi_summary"] = kpi_summary
                            for key, value in kpi_summary.items():
                                if key not in kpi or kpi.get(key) in (None, 0):
                                    kpi[key] = value
                    except Exception as err:
                        print(f"⚠️  Unable to read KPI summary JSON: {err}")

                if buses_file:
                    try:
                        with buses_file.open("r", encoding="utf-8") as f:
                            bus_data = json.load(f)
                        bus_entries = []
                        transformer_bus_id = None
                        for feature in bus_data.get("features", []):
                            props = feature.get("properties", {}) or {}
                            voltage = props.get("voltage_pu")
                            if voltage is None:
                                continue
                            entry = {
                                "id": props.get("id"),
                                "name": props.get("name"),
                                "voltage": float(voltage),
                                "load_kw": float(props.get("load_kw", 0) or 0),
                                "status": (props.get("voltage_status") or "normal"),
                                "has_load": bool(props.get("has_load")),
                            }
                            bus_entries.append(entry)
                            if props.get("is_transformer"):
                                transformer_bus_id = props.get("id")
                        if bus_entries:
                            filtered = [b for b in bus_entries if b["has_load"] or b["status"].lower() != "normal"]
                            if not filtered:
                                filtered = bus_entries
                            insights["low_voltage_buses"] = sorted(filtered, key=lambda b: b["voltage"])[:6]
                        if transformer_bus_id is not None:
                            insights["transformer_bus"] = transformer_bus_id
                    except Exception as err:
                        print(f"⚠️  Unable to analyze bus GeoJSON: {err}")

                if lines_file:
                    try:
                        with lines_file.open("r", encoding="utf-8") as f:
                            line_data = json.load(f)
                        line_entries = []
                        for feature in line_data.get("features", []):
                            props = feature.get("properties", {}) or {}
                            loading_pct = props.get("loading_pct")
                            if loading_pct is None:
                                continue
                            length_m = props.get("length_m")
                            if length_m is None:
                                length_km = props.get("length_km") or 0
                                length_m = float(length_km) * 1000.0
                            entry = {
                                "id": props.get("id"),
                                "loading_pct": float(loading_pct),
                                "length_m": float(length_m),
                                "status": (props.get("loading_status") or "normal"),
                            }
                            line_entries.append(entry)
                        if line_entries:
                            insights["high_loading_lines"] = sorted(line_entries, key=lambda l: l["loading_pct"], reverse=True)[:6]
                    except Exception as err:
                        print(f"⚠️  Unable to analyze line GeoJSON: {err}")

                if violations_file:
                    try:
                        violations_df = pd.read_csv(violations_file)
                        if not violations_df.empty:
                            insights["violations"] = violations_df.head(10).to_dict("records")
                    except Exception as err:
                        print(f"⚠️  Unable to read violations CSV: {err}")

                if insights:
                    hp_insights = insights

        generator = HTMLDashboardGenerator()
        map_embed_path = None
        if map_file_path:
            try:
                map_embed_path = os.path.relpath(Path(map_file_path), generator.output_dir)
            except ValueError:
                map_embed_path = str(map_file_path)

        generated_files_for_html = []
        for entry in generated_file_paths:
            path_obj = entry.get("path")
            if not path_obj:
                continue
            try:
                rel_path = os.path.relpath(path_obj, generator.output_dir)
            except ValueError:
                rel_path = str(path_obj)
            generated_files_for_html.append(
                {
                    "label": entry.get("label"),
                    "href": rel_path,
                }
            )

        if dashboard_type == "dh":
            html_file = generator.create_dh_html_dashboard(
                kpi,
                scenario_name,
                metadata,
                map_embed_path,
                chart_files,
                routing_analysis=routing_analysis,
                dual_topology=dual_topology,
                thermal_profile=thermal_profile,
                network_stats=dual_topology.get("stats") if dual_topology else None,
                generated_files=generated_files_for_html,
            )
        elif dashboard_type == "hp":
            html_file = generator.create_hp_html_dashboard(
                kpi,
                scenario_name,
                metadata,
                map_embed_path,
                chart_files,
                generated_files=generated_files_for_html,
                insights=hp_insights,
            )
        else:
            return f"Error: Invalid dashboard type '{dashboard_type}'. Use 'dh' or 'hp'."
        
        legacy_dashboard_created = False
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                dashboard_html = f.read()
            legacy_html = dashboard_html
            if map_embed_path:
                legacy_html = legacy_html.replace(str(map_embed_path), legacy_map_name)
            with open(legacy_dashboard_path, "w", encoding="utf-8") as f:
                f.write(legacy_html)
            legacy_dashboard_created = True
        except Exception as copy_err:
            print(f"⚠️  Unable to create legacy dashboard copy: {copy_err}")

        msg = f"HTML dashboard created!\n\n"
        msg += f"📊 Dashboard Type: {dashboard_type.upper()}\n"
        msg += f"📁 File: {html_file}\n\n"
        if legacy_dashboard_created:
            msg += f"📂 Legacy Copy: {legacy_dashboard_path}\n\n"
        msg += f"Features:\n"
        msg += f"  • Comprehensive metrics and KPIs\n"
        
        if map_file:
            msg += f"  • Embedded interactive map\n"
        else:
            msg += f"  • ⚠️ No interactive map found (generate with create_interactive_map())\n"
        
        if chart_files:
            msg += f"  • {len(chart_files)} embedded chart(s)\n"
        
        msg += f"  • Professional styling with responsive design\n"
        msg += f"  • JavaScript interactivity\n\n"
        msg += f"🌐 Open in browser:\n"
        msg += f"  open {html_file}\n\n"
        msg += f"The HTML dashboard provides a comprehensive, interactive web view of the simulation results."
        
        return msg
    
    except Exception as e:
        import traceback
        return f"Error creating HTML dashboard: {traceback.format_exc()}"


@tool
def optimize_network_routing(
    scenario_name: str,
    use_shortest_path: bool = True,
    force_recompute: bool = False,
) -> str:
    """
    Optimize district heating network routing using advanced algorithms.
    
    This tool uses advanced shortest path routing algorithms (migrated from
    street_final_copy_3) to find optimal pipe routes that:
    - Follow street geometries (no routing across open land)
    - Minimize total pipe length
    - Insert virtual nodes at service connection points
    - Calculate exact routing distances
    
    The optimization compares the current radial topology with shortest
    path routing and shows the improvements.
    
    Args:
        scenario_name: Name of the scenario to optimize (e.g., "Parkstrasse_DH")
        use_shortest_path: Use shortest path algorithm (default: True)
    
    Returns:
        Optimization results with before/after comparison
    """
    print(f"TOOL: Optimizing network routing for '{scenario_name}'...")
    
    try:
        from src.routing import (
            create_street_network_with_virtual_nodes,
            find_shortest_paths_from_plant,
            analyze_routing_results,
            transform_plant_coordinates,
            create_path_geometries,
            save_routing_results,
            build_dual_pipe_topology,
        )
        from pathlib import Path
        import pandas as pd
        
        # Check if scenario exists
        results_file = f"simulation_outputs/{scenario_name}_results.json"
        if not os.path.exists(results_file):
            return f"Error: Scenario not found at '{results_file}'. Please run simulation first."
        
        # Load streets and buildings
        streets_file = "results_test/streets.geojson"
        buildings_file = "results_test/buildings_prepared.geojson"
        
        if not os.path.exists(streets_file):
            return f"Error: Streets data not found at '{streets_file}'."
        
        if not os.path.exists(buildings_file):
            return f"Error: Buildings data not found at '{buildings_file}'."
        
        streets_gdf = _safe_read_geojson(streets_file)
        buildings_gdf = _safe_read_geojson(buildings_file)

        target_crs = "EPSG:32633"
        if streets_gdf.crs is None:
            streets_gdf.set_crs("EPSG:4326", inplace=True)
        if buildings_gdf.crs is None:
            buildings_gdf.set_crs("EPSG:4326", inplace=True)

        if streets_gdf.crs != target_crs:
            streets_gdf = streets_gdf.to_crs(target_crs)
        if buildings_gdf.crs != target_crs:
            buildings_gdf = buildings_gdf.to_crs(target_crs)
        
        print(f"  Loaded {len(buildings_gdf)} buildings and {len(streets_gdf)} street segments")
        
        # Get plant location
        plant_x, plant_y = transform_plant_coordinates()
        plant_connection = {"plant_x": plant_x, "plant_y": plant_y}
        
        # Prepare building connections
        building_id_col = "GebaeudeID" if "GebaeudeID" in buildings_gdf.columns else "building_id"
        
        connections_data = []
        for idx_building, building in buildings_gdf.iterrows():
            building_id = building.get(building_id_col, idx_building)
            centroid = building.geometry.centroid
            
            # Find nearest street point (simple version)
            min_dist = float('inf')
            nearest_point = None
            nearest_street = None
            nearest_street_idx = None
            for idx_street, street in streets_gdf.iterrows():
                projected_point = street.geometry.interpolate(street.geometry.project(centroid))
                dist = centroid.distance(projected_point)
                if dist < min_dist:
                    min_dist = dist
                    nearest_point = projected_point
                    nearest_street = street
                    nearest_street_idx = idx_street
            
            connections_data.append({
                "building_id": building_id,
                "building_x": centroid.x,
                "building_y": centroid.y,
                "connection_point_x": nearest_point.x if nearest_point else centroid.x,
                "connection_point_y": nearest_point.y if nearest_point else centroid.y,
                "distance_to_street": min_dist if min_dist != float('inf') else 0,
                "nearest_street_id": getattr(nearest_street, "id", nearest_street_idx) if nearest_street is not None else nearest_street_idx,
                "nearest_street_name": getattr(nearest_street, "name", f"Street_{nearest_street_idx}") if nearest_street is not None else f"Street_{nearest_street_idx}",
            })
        
        connections_df = pd.DataFrame(connections_data)
        
        # Create street network with virtual nodes
        G, virtual_nodes = create_street_network_with_virtual_nodes(
            streets_gdf,
            connections_df,
            plant_connection
        )
        
        # Find shortest paths
        paths = find_shortest_paths_from_plant(G, plant_node="PLANT")
        
        # Analyze routing
        analysis = analyze_routing_results(paths, connections_df)
        
        # Create path geometries
        paths_gdf = create_path_geometries(G, paths, connections_df, plant_connection)
        
        output_dir = f"results_test/routing/{scenario_name}"
        os.makedirs(output_dir, exist_ok=True)

        existing_markers = [
            "dual_network_stats_dual_pipe",
            "dual_supply_pipes_dual_pipe",
            "dual_return_pipes_dual_pipe",
            "dual_service_connections_dual_pipe",
            "dual_pipe_report_dual_pipe",
            "pandapipes_simulation_results_dual_pipe",
        ]
        if not force_recompute:
            all_present = True
            for marker in existing_markers:
                marker_path = Path(output_dir).glob(f"{marker}*.json" if marker.endswith(".json") else f"{marker}*.csv")
                try:
                    next(marker_path)
                except StopIteration:
                    all_present = False
                    break
            if all_present:
                return (
                    "Routing artefacts already exist; skipping recomputation "
                    "(use force_recompute=True to regenerate)."
                )
        
        try:
            with open("config/simulation_config.yaml", "r") as cfg_file:
                sim_config = yaml.safe_load(cfg_file) or {}
                dh_config = sim_config.get("district_heating", {})
        except FileNotFoundError:
            dh_config = {}
        supply_temp = float(dh_config.get("supply_temp_c", 70.0) or 70.0)
        return_temp = float(dh_config.get("return_temp_c", 40.0) or 40.0)
        supply_pressure = float(dh_config.get("supply_pressure_bar", 6.0) or 6.0)

        # Construct dual-pipe topology for visualization/export
        dual_topology = build_dual_pipe_topology(
            buildings_gdf=buildings_gdf,
            streets_gdf=streets_gdf,
            plant_connection=plant_connection,
            supply_temp=supply_temp,
            return_temp=return_temp,
            supply_pressure=supply_pressure,
            analysis=analysis,
            connections_df=connections_df,
        )

        sizing_outputs = None
        sizing_lookup = {}
        compliance_lookup = {}
        sizing_serializable: Dict[str, Any] | None = None
        try:
            sizing_outputs = run_cha_sizing_from_topology(
                dual_topology=dual_topology,
                supply_temp_c=supply_temp,
                return_temp_c=return_temp,
            )
            sizing_serializable = sizing_outputs_to_serializable(sizing_outputs)
            dual_topology["sizing"] = sizing_serializable
            sizing_lookup = sizing_outputs.pipe_sizing
            compliance_lookup = sizing_outputs.compliance
            _apply_sizing_to_topology(dual_topology, sizing_lookup, compliance_lookup)
            _update_stats_with_sizing(dual_topology.get("stats", {}), dual_topology)
            sizing_stats_snapshot = dual_topology.get("stats", {})
            analysis["max_pipe_velocity_ms"] = sizing_stats_snapshot.get("max_pipe_velocity_ms")
            analysis["avg_supply_diameter_mm"] = sizing_stats_snapshot.get("avg_supply_diameter_mm")
            analysis["avg_return_diameter_mm"] = sizing_stats_snapshot.get("avg_return_diameter_mm")
        except Exception as sizing_err:
            print(f"⚠️  Pipe sizing calculation failed: {sizing_err}")
            fallback_meta = _apply_sizing_fallback(
                dual_topology,
                reason=f"CHA sizing failed: {sizing_err}",
                analysis=analysis,
            )
            _update_stats_with_sizing(dual_topology.get("stats", {}), dual_topology)
            sizing_outputs = None
            sizing_serializable = {
                "status": "fallback",
                "reason": str(sizing_err),
                "fallbacks": dual_topology.get("sizing_fallbacks", []),
            }
            dual_topology["sizing"] = sizing_serializable
            sizing_outputs = None

        # Ensure any missing segments receive fallback sizing
        fallback_meta_missing = _apply_sizing_fallback(
            dual_topology,
            reason="Missing CHA sizing for some segments",
            analysis=analysis,
        )
        if fallback_meta_missing:
            _update_stats_with_sizing(dual_topology.get("stats", {}), dual_topology)
            if sizing_serializable is None or sizing_serializable.get("status") == "fallback":
                dual_topology["sizing"] = {
                    "status": "fallback",
                    "reason": fallback_meta_missing["reason"],
                    "fallbacks": dual_topology.get("sizing_fallbacks", []),
                }
                sizing_serializable = dual_topology["sizing"]
            else:
                sizing_serializable["fallbacks"] = dual_topology.get("sizing_fallbacks", [])

        dual_topology_file = os.path.join(output_dir, "dual_topology.json")
        with open(dual_topology_file, "w", encoding="utf-8") as f:
            json.dump(dual_topology, f, indent=2)

        # Thermal and hydraulic profile based on distance from plant
        thermal_profile = []
        for consumer in dual_topology.get("consumers", []):
            building_id = consumer["id"]
            junction_id = consumer["junction_id"]
            junction = next(
                (node for node in dual_topology["junctions"] if node["id"] == junction_id),
                None,
            )
            if junction:
                distance = np.hypot(junction["x"] - plant_connection["plant_x"], junction["y"] - plant_connection["plant_y"])
            else:
                distance = 0.0

            temperature = float(consumer.get("temperature", supply_temp))
            pressure = float(consumer.get("pressure_bar", supply_pressure))

            if building_id in paths:
                paths[building_id]["temperature_c"] = temperature
                paths[building_id]["pressure_bar"] = pressure

            thermal_profile.append(
                {
                    "building_id": building_id,
                    "distance_m": distance,
                    "temperature_c": temperature,
                    "pressure_bar": pressure,
                }
            )

        if thermal_profile:
            thermal_df = pd.DataFrame(thermal_profile)
            thermal_csv = os.path.join(output_dir, "routing_thermal_profile.csv")
            thermal_df.to_csv(thermal_csv, index=False)

            thermal_json = os.path.join(output_dir, "routing_thermal_profile.json")
            with open(thermal_json, "w", encoding="utf-8") as f:
                json.dump(thermal_profile, f, indent=2)

            analysis["temperature_min_c"] = float(thermal_df["temperature_c"].min())
            analysis["temperature_max_c"] = float(thermal_df["temperature_c"].max())
            analysis["pressure_min_bar"] = float(thermal_df["pressure_bar"].min())
            analysis["pressure_max_bar"] = float(thermal_df["pressure_bar"].max())
            analysis["temperature_avg_c"] = float(thermal_df["temperature_c"].mean())
            analysis["pressure_avg_bar"] = float(thermal_df["pressure_bar"].mean())

        # ------------------------------------------------------------------
        # Legacy-style artefact exports
        # ------------------------------------------------------------------
        street_name_from_results = scenario_name
        results_payload_path = Path("simulation_outputs") / f"{scenario_name}_results.json"
        scenario_results_payload = None
        if results_payload_path.exists():
            try:
                with open(results_payload_path, "r", encoding="utf-8") as payload_file:
                    scenario_results_payload = json.load(payload_file)
                    payload_street = scenario_results_payload.get("street_name")
                    if payload_street:
                        street_name_from_results = payload_street
            except Exception as exc:  # pragma: no cover - defensive
                print(f"⚠️  Unable to determine street name from {results_payload_path}: {exc}")

        safe_street_slug = _sanitize_street_dirname(street_name_from_results)
        service_records = dual_topology.get("service_connections", [])

        sizing_summary_path = None
        sizing_summary_path = None
        if sizing_serializable is not None:
            sizing_summary_path = os.path.join(
                output_dir, f"dual_pipe_sizing_dual_pipe_{safe_street_slug}.json"
            )
            try:
                payload = sizing_serializable.copy()
                payload.setdefault("generated_at", datetime.utcnow().isoformat() + "Z")
                with open(sizing_summary_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
            except Exception as sizing_write_err:
                print(f"⚠️  Unable to write sizing summary: {sizing_write_err}")
                sizing_summary_path = None

        def _pipe_records(pipe_type: str):
            records = []
            for pipe in dual_topology.get("pipes", []):
                if pipe.get("type") != pipe_type:
                    continue
                coords = pipe.get("coords") or []
                if len(coords) < 2:
                    continue
                line = LineString(coords)
                start_x, start_y = coords[0]
                end_x, end_y = coords[-1]
                start_node = f"POINT ({start_x} {start_y})"
                end_node = f"POINT ({end_x} {end_y})"
                records.append(
                    {
                        "pipe_id": pipe.get("id"),
                        "pipe_type": pipe_type,
                        "start_x": start_x,
                        "start_y": start_y,
                        "end_x": end_x,
                        "end_y": end_y,
                        "length_m": float(line.length),
                        "temperature_c": pipe.get("temperature_c"),
                        "pressure_bar": pipe.get("pressure_bar"),
                        "building_served": pipe.get("building_id"),
                        "flow_direction": pipe.get("flow_direction"),
                        "follows_street": True,
                        "start_node": start_node,
                        "end_node": end_node,
                        "street_id": pipe.get("street_id", "unknown"),
                        "street_name": pipe.get("street_name", "Unknown Street"),
                        "highway_type": pipe.get("highway_type", "unknown"),
                        "diameter_m": pipe.get("diameter_m"),
                        "diameter_dn": pipe.get("diameter_dn"),
                        "velocity_ms": pipe.get("velocity_ms"),
                        "pressure_drop_pa_per_m": pipe.get("pressure_drop_pa_per_m"),
                        "pressure_drop_bar": pipe.get("pressure_drop_bar"),
                        "standards_compliant": pipe.get("standards_compliant"),
                    }
                )
            return records

        supply_records = _pipe_records("supply")
        return_records = _pipe_records("return")

        supply_filename = f"dual_supply_pipes_dual_pipe_{safe_street_slug}.csv"
        return_filename = f"dual_return_pipes_dual_pipe_{safe_street_slug}.csv"
        service_filename = f"dual_service_connections_dual_pipe_{safe_street_slug}.csv"
        stats_filename = f"dual_network_stats_dual_pipe_{safe_street_slug}.json"
        sim_filename = f"pandapipes_simulation_results_dual_pipe_{safe_street_slug}.json"
        report_filename = f"dual_pipe_report_dual_pipe_{safe_street_slug}.md"

        if supply_records:
            supply_df = pd.DataFrame(supply_records)
            supply_path = os.path.join(output_dir, supply_filename)
            supply_df.to_csv(supply_path, index=False)

        if return_records:
            return_df = pd.DataFrame(return_records)
            return_path = os.path.join(output_dir, return_filename)
            return_df.to_csv(return_path, index=False)

        if service_records:
            service_df = pd.DataFrame(service_records)
            service_path = os.path.join(output_dir, service_filename)
            service_df.to_csv(service_path, index=False)

        stats_path = os.path.join(output_dir, stats_filename)
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(dual_topology.get("stats", {}), f, indent=2)

        sim_results_path = os.path.join(output_dir, sim_filename)
        simulation_summary = {}
        if scenario_results_payload is None and results_payload_path.exists():
            try:
                with open(results_payload_path, "r", encoding="utf-8") as f:
                    scenario_results_payload = json.load(f)
            except Exception:
                scenario_results_payload = None
        if scenario_results_payload is not None:
            kpi = scenario_results_payload.get("kpi", {})
            metadata = scenario_results_payload.get("metadata", {})
            simulation_summary = {
                "success": scenario_results_payload.get("success", False),
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "total_heat_supplied_mwh": kpi.get("total_heat_supplied_mwh"),
                "peak_heat_load_kw": kpi.get("peak_heat_load_kw"),
                "max_pressure_drop_bar": kpi.get("max_pressure_drop_bar"),
                "avg_pressure_drop_bar": kpi.get("avg_pressure_drop_bar"),
                "min_supply_temp_c": kpi.get("min_supply_temp_c"),
                "avg_supply_temp_c": kpi.get("avg_supply_temp_c"),
                "pump_energy_kwh": kpi.get("pump_energy_kwh"),
                "heat_loss_percentage": kpi.get("heat_loss_percentage"),
                "supply_temperature_c": metadata.get(
                    "supply_temp_c", dual_topology["stats"].get("supply_temperature_c")
                ),
                "return_temperature_c": metadata.get(
                    "return_temp_c", dual_topology["stats"].get("return_temperature_c")
                ),
                "num_junctions": dual_topology["stats"].get("num_junctions"),
                "num_pipes": dual_topology["stats"].get("num_pipes"),
                "num_buildings": dual_topology["stats"].get("num_buildings"),
            }
            sizing_stats_snapshot = dual_topology.get("stats", {})
            simulation_summary["max_pipe_velocity_ms"] = sizing_stats_snapshot.get("max_pipe_velocity_ms")
            simulation_summary["avg_supply_diameter_mm"] = sizing_stats_snapshot.get("avg_supply_diameter_mm")
            simulation_summary["avg_return_diameter_mm"] = sizing_stats_snapshot.get("avg_return_diameter_mm")
        sizing_stats_snapshot = dual_topology.get("stats", {})
        simulation_summary.setdefault("max_pipe_velocity_ms", sizing_stats_snapshot.get("max_pipe_velocity_ms"))
        simulation_summary.setdefault("avg_supply_diameter_mm", sizing_stats_snapshot.get("avg_supply_diameter_mm"))
        simulation_summary.setdefault("avg_return_diameter_mm", sizing_stats_snapshot.get("avg_return_diameter_mm"))
        simulation_summary.setdefault("avg_service_diameter_mm", sizing_stats_snapshot.get("avg_service_diameter_mm"))
        if sizing_stats_snapshot.get("sizing_fallback_used"):
            simulation_summary["sizing_fallback_used"] = True
            simulation_summary["sizing_fallback_reason"] = sizing_stats_snapshot.get("sizing_fallback_reason")
            simulation_summary["sizing_fallback_diameter_mm"] = sizing_stats_snapshot.get("sizing_fallback_diameter_mm")
        with open(sim_results_path, "w", encoding="utf-8") as f:
            json.dump(simulation_summary, f, indent=2)

        report_lines = [
            f"# Dual-Pipe District Heating Report: {scenario_name}",
            "",
            f"Generated on {datetime.utcnow().isoformat()}Z",
            "",
            "## Network Overview",
            "",
            f"- Total supply length: {dual_topology['stats'].get('total_supply_length_km', 0):.3f} km",
            f"- Total return length: {dual_topology['stats'].get('total_return_length_km', 0):.3f} km",
            f"- Total service length: {dual_topology['stats'].get('total_service_length_m', 0):.1f} m",
            f"- Buildings served: {dual_topology['stats'].get('num_buildings', 0)}",
            f"- Heat demand (kW): {dual_topology['stats'].get('total_heat_demand_kw', 0):.1f}",
            f"- Heat demand (MWh): {dual_topology['stats'].get('total_heat_demand_mwh', 0):.1f}",
            "",
            "## Simulation Summary",
            "",
            f"- Success: {simulation_summary.get('success', False)}",
            f"- Supply temperature: {simulation_summary.get('supply_temperature_c', 'N/A')} °C",
            f"- Return temperature: {simulation_summary.get('return_temperature_c', 'N/A')} °C",
            f"- Max pressure drop: {simulation_summary.get('max_pressure_drop_bar', 'N/A')} bar",
            f"- Pump energy: {simulation_summary.get('pump_energy_kwh', 'N/A')} kWh",
        ]

        if dual_topology.get("stats", {}).get("sizing_fallback_used"):
            report_lines.extend(
                [
                    "",
                    "### ⚠️ Sizing Fallback Notice",
                    "",
                    f"- Reason: {dual_topology['stats'].get('sizing_fallback_reason', 'Unknown')}",
                    f"- Default diameter applied (mm): {dual_topology['stats'].get('sizing_fallback_diameter_mm', 'N/A')}",
                    f"- Segments affected: {dual_topology['stats'].get('sizing_fallback_segments', 0)}",
                ]
            )
        report_lines.extend(
            [
                "",
                "## Generated Files",
                "",
                f"- {supply_filename}",
                f"- {return_filename}",
                f"- {service_filename}",
                f"- {stats_filename}",
                f"- {sim_filename}",
                f"- dual_pipe_sizing_dual_pipe_{safe_street_slug}.json",
                f"- routing_thermal_profile.json",
                "",
                "## Pipe Sizing Summary",
                "",
                f"- Max pipe velocity: {dual_topology.get('stats', {}).get('max_pipe_velocity_ms', 'N/A')}",
                f"- Avg supply diameter (mm): {dual_topology.get('stats', {}).get('avg_supply_diameter_mm', 'N/A')}",
                f"- Avg return diameter (mm): {dual_topology.get('stats', {}).get('avg_return_diameter_mm', 'N/A')}",
                f"- Avg service diameter (mm): {dual_topology.get('stats', {}).get('avg_service_diameter_mm', 'N/A')}",
            ]
        )
        report_path = os.path.join(output_dir, report_filename)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        # Copy artefacts to legacy street analysis directory
        street_dir = _ensure_street_output_dir(street_name_from_results)
        artefact_sources = [
            Path(output_dir) / "routing_paths.csv",
            Path(output_dir) / "routing_analysis.csv",
            Path(output_dir) / "routing_paths.geojson",
            Path(output_dir) / "routing_thermal_profile.csv",
            Path(output_dir) / "routing_thermal_profile.json",
            Path(output_dir) / supply_filename,
            Path(output_dir) / return_filename,
            Path(output_dir) / service_filename,
            Path(output_dir) / stats_filename,
            Path(output_dir) / sim_filename,
            Path(output_dir) / report_filename,
        ]
        if sizing_summary_path:
            artefact_sources.append(Path(sizing_summary_path))
        for src in artefact_sources:
            if src.exists():
                dest = street_dir / src.name
                try:
                    shutil.copy2(src, dest)
                except Exception as copy_err:
                    print(f"⚠️  Unable to copy {src.name} to street directory: {copy_err}")

        # Save routing results with augmented metadata
        save_routing_results(paths, analysis, paths_gdf, output_dir)
        
        # Create response message
        msg = f"Network routing optimization complete!\n\n"
        msg += f"📊 Routing Analysis for {scenario_name}:\n"
        msg += f"  • Total buildings: {analysis.get('total_buildings', 0)}\n"
        msg += f"  • Successful connections: {analysis.get('successful_connections', 0)}\n"
        msg += f"  • Success rate: {analysis.get('success_rate', 0):.1f}%\n\n"
        
        msg += f"📏 Network Lengths:\n"
        msg += f"  • Total main pipe length: {analysis.get('total_main_pipe_length', 0):.2f} m\n"
        msg += f"  • Total service pipe length: {analysis.get('total_service_pipe_length', 0):.2f} m\n"
        msg += f"  • Total network length: {analysis.get('total_network_length', 0):.2f} m\n"
        msg += f"  • Average main pipe length: {analysis.get('avg_main_pipe_length', 0):.2f} m\n\n"
        
        msg += f"💡 Routing Features:\n"
        msg += f"  • Virtual nodes at service connection points\n"
        msg += f"  • Shortest paths following street network\n"
        msg += f"  • No routing across open land\n"
        msg += f"  • Optimized for minimum pipe length\n\n"
        sizing_stats_snapshot = dual_topology.get("stats", {})
        if sizing_stats_snapshot.get("avg_supply_diameter_mm") is not None:
            msg += f"📐 Pipe Sizing:\n"
            msg += f"  • Avg supply diameter: {sizing_stats_snapshot.get('avg_supply_diameter_mm'):.1f} mm\n"
            if sizing_stats_snapshot.get("avg_return_diameter_mm") is not None:
                msg += f"  • Avg return diameter: {sizing_stats_snapshot.get('avg_return_diameter_mm'):.1f} mm\n"
            if sizing_stats_snapshot.get("avg_service_diameter_mm") is not None:
                msg += f"  • Avg service diameter: {sizing_stats_snapshot.get('avg_service_diameter_mm'):.1f} mm\n"
            if sizing_stats_snapshot.get("max_pipe_velocity_ms") is not None:
                msg += f"  • Max pipe velocity: {sizing_stats_snapshot.get('max_pipe_velocity_ms'):.2f} m/s\n"
            msg += "\n"
        if sizing_stats_snapshot.get("sizing_fallback_used"):
            msg += "⚠️ Pipe sizing fallback applied — inspect hydraulic inputs and CHA configuration.\n\n"
        
        msg += f"📁 Results saved to: {output_dir}/\n"
        msg += f"  • routing_paths.csv - Path data for each building\n"
        msg += f"  • routing_analysis.csv - Network statistics\n"
        msg += f"  • routing_paths.geojson - Path geometries\n"
        msg += f"  • dual_topology.json - Dual-pipe supply/return topology\n"
        msg += f"  • {supply_filename} - Supply main segments\n"
        msg += f"  • {return_filename} - Return main segments\n"
        msg += f"  • {service_filename} - Service connections (supply/return)\n"
        msg += f"  • {stats_filename} - Network statistics summary\n"
        msg += f"  • {sim_filename} - Simulation results snapshot\n"
        if sizing_summary_path:
            msg += f"  • {os.path.basename(sizing_summary_path)} - Pipe sizing summary\n"
        msg += f"  • {report_filename} - Markdown project report\n"
        msg += f"  • street_analysis_outputs/{_sanitize_street_dirname(street_name_from_results)}/ - Legacy-compatible copies\n"
        if thermal_profile:
            msg += f"  • routing_thermal_profile.csv - Temperature & pressure at consumers\n"
            msg += f"  • routing_thermal_profile.json - Machine-readable thermal metadata\n\n"
            msg += f"🌡️ Thermal Profile Summary:\n"
            msg += (
                f"  • Supply setpoint: {supply_temp:.1f}°C → Return setpoint: {return_temp:.1f}°C\n"
            )
            msg += (
                f"  • Consumer temperature range: {analysis['temperature_min_c']:.1f}°C – "
                f"{analysis['temperature_max_c']:.1f}°C (avg {analysis['temperature_avg_c']:.1f}°C)\n"
            )
            msg += (
                f"  • Consumer pressure range: {analysis['pressure_min_bar']:.2f} bar – "
                f"{analysis['pressure_max_bar']:.2f} bar (avg {analysis['pressure_avg_bar']:.2f} bar)\n\n"
            )
        
        msg += f"🎉 Network routing optimized using shortest path algorithms from street_final_copy_3!"
        
        return msg
    
    except Exception as e:
        import traceback
        return f"Error optimizing network routing: {traceback.format_exc()}"
