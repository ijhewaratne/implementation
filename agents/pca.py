from __future__ import annotations
import glob
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yaml

# ---------- Utilities ----------

REQUIRED_COLS = [
    "dn",
    "d_inner_m",
    "d_outer_m",
    "u_wpermk",
    "w_loss_w_per_m",
    "cost_eur_per_m",
]

def _load_yaml(p: Path) -> dict:
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _select_column(df: pd.DataFrame, spec: dict, canon_name: str) -> pd.Series:
    """
    Find a column by keywords/aliases and convert unit to SI if configured.
    Expected keys in spec: {keywords: [..], unit: 'm'|'mm'|None}
    """
    cols_lower = {c.lower(): c for c in df.columns}
    series = None
    for kw in spec.get("keywords", []):
        if kw.lower() in cols_lower:
            series = df[cols_lower[kw.lower()]]
            break
    if series is None:
        default_val = spec.get("default")
        if default_val is not None:
            return pd.Series(np.full(len(df), default_val), index=df.index, name=canon_name, dtype="float64")
        raise KeyError(f"Missing required column for '{canon_name}' (keywords: {spec.get('keywords')})")

    # Unit normalization
    unit = spec.get("unit")
    s = pd.to_numeric(series, errors="coerce")
    if unit == "mm":
        s = s / 1000.0
    elif unit in (None, "m", "W/mK", "W_per_mK", "EUR_per_m"):
        pass
    else:
        raise ValueError(f"Unsupported unit for '{canon_name}': {unit}")
    s.name = canon_name
    return s.astype("float64")

def _process_sheet(df_raw: pd.DataFrame, colmap: dict) -> pd.DataFrame:
    # Build canonical DataFrame with required columns only (extras dropped)
    out = pd.DataFrame(index=df_raw.index)
    for canon in REQUIRED_COLS:
        out[canon] = _select_column(df_raw, colmap[canon], canon)

    # Derived column (for QC / visibility); not required in canonical output
    out["wall_thickness_m"] = (out["d_outer_m"] - out["d_inner_m"]) / 2.0
    return out

def _validate_and_qc(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return (df_valid, df_qc) with reasons for dropped rows."""
    qc_rows: List[Dict] = []
    idx = df.index

    # Invalid geometry
    invalid_geom = (df["d_outer_m"] <= df["d_inner_m"]) | (df["d_inner_m"] <= 0) | (df["d_outer_m"] <= 0)
    for i in idx[invalid_geom]:
        qc_rows.append({"index": int(i), "reason": "invalid_diameter", "dn": df.at[i, "dn"]})

    # Non-positive cost
    invalid_cost = df["cost_eur_per_m"] <= 0
    for i in idx[invalid_cost]:
        qc_rows.append({"index": int(i), "reason": "nonpositive_cost", "dn": df.at[i, "dn"]})

    # Drop invalids
    valid = ~(invalid_geom | invalid_cost)
    df_valid = df.loc[valid].copy()

    # Deduplicate by dn (keep lowest cost)
    if "dn" not in df_valid.columns:
        raise KeyError("Missing required column 'dn' in canonical frame after validation.")
    # Sort so first per-dn is the lowest cost
    df_valid.sort_values(["dn", "cost_eur_per_m"], ascending=[True, True], inplace=True, kind="mergesort")
    keep_idx = df_valid.drop_duplicates(subset=["dn"], keep="first").index
    dup_idx = df_valid.index.difference(keep_idx)
    for i in dup_idx:
        qc_rows.append({"index": int(i), "reason": "duplicate_dn_higher_cost", "dn": df_valid.at[i, "dn"]})
    df_valid = df_valid.loc[keep_idx].sort_values("dn").reset_index(drop=True)

    df_qc = pd.DataFrame(qc_rows, columns=["index", "dn", "reason"])
    return df_valid, df_qc

# ---------- Public API ----------

def run(config: dict) -> dict:
    """
    Normalize vendor Excel -> canonical catalog.csv and QC report.
    Config keys:
      input_dir: str (default 'data/raw/catalogs')
      mapping: str (default 'configs/catalog_map.yml')
      output_catalog: str (default 'processed/pca/catalog.csv')
      output_qc: str (default 'eval/pca/catalog_qc.csv')
      sheets: optional list of sheet names (else all sheets)
    """
    input_dir = Path(config.get("input_dir", "data/raw/catalogs"))
    mapping_path = Path(config.get("mapping", "configs/catalog_map.yml"))
    out_catalog = Path(config.get("output_catalog", "processed/pca/catalog.csv"))
    out_qc = Path(config.get("output_qc", "eval/pca/catalog_qc.csv"))
    sheets_filter = config.get("sheets")

    colmap = _load_yaml(mapping_path)
    # Ensure mapping provides all required canonical fields
    missing = [c for c in REQUIRED_COLS if c not in colmap]
    if missing:
        raise KeyError(f"Mapping file missing canonical entries: {missing}")

    files = sorted(glob.glob(str(input_dir / "*.xlsx")))
    if not files:
        raise FileNotFoundError(f"No Excel files found in {input_dir}")

    frames: List[pd.DataFrame] = []
    qc_frames: List[pd.DataFrame] = []

    for fp in files:
        try:
            xls = pd.ExcelFile(fp, engine="openpyxl")
        except Exception as e:
            raise RuntimeError(f"Failed to open {fp}: {e}") from e

        sheet_names = sheets_filter or xls.sheet_names
        for sh in sheet_names:
            try:
                df_raw = xls.parse(sh)
                # Normalize header
                df_raw.columns = [str(c).strip() for c in df_raw.columns]
                df_can = _process_sheet(df_raw, colmap)
                df_ok, df_qc = _validate_and_qc(df_can)
                if not df_ok.empty:
                    frames.append(df_ok)
                if not df_qc.empty:
                    df_qc["file"] = Path(fp).name
                    df_qc["sheet"] = sh
                    qc_frames.append(df_qc)
            except KeyError as ke:
                # Missing required mapped column: fail fast as per spec
                raise
            except Exception as e:
                # Treat as QC failure for this sheet
                qc_frames.append(pd.DataFrame([{"index": -1, "dn": None, "reason": f"sheet_error:{e}", "file": Path(fp).name, "sheet": sh}]))

    if not frames:
        raise RuntimeError("After validation, no valid catalog rows remain.")

    catalog = pd.concat(frames, ignore_index=True)
    qc = pd.concat(qc_frames, ignore_index=True) if qc_frames else pd.DataFrame(columns=["index","dn","reason","file","sheet"])

    out_catalog.parent.mkdir(parents=True, exist_ok=True)
    out_qc.parent.mkdir(parents=True, exist_ok=True)
    catalog.to_csv(out_catalog, index=False)
    qc.to_csv(out_qc, index=False)

    return {
        "status": "ok",
        "catalog_rows": int(len(catalog)),
        "qc_rows": int(len(qc)),
        "catalog_path": str(out_catalog),
        "qc_path": str(out_qc),
    }

if __name__ == "__main__":
    # Minimal CLI bridge: python -m agents.pca --config configs/pca.yml
    import argparse, sys, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=str, default=None)
    args = ap.parse_args()
    cfg = {}
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    res = run(cfg or {})
    print(json.dumps(res, indent=2))

