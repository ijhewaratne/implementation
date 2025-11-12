import pandas as pd

import geopandas as gpd
from shapely.errors import TopologicalError
from pathlib import Path

def clean_building_geoms(gdf, id_col="Gebaeudecode", log_file="results/building_geom_qc.log"):
    """
    Cleans a GeoDataFrame of buildings:
    - Removes rows with missing/empty geometry
    - Drops duplicate IDs
    - Attempts to fix invalid polygons using buffer(0)
    - Logs all issues to a file for QC/audit
    """
    Path(log_file).parent.mkdir(exist_ok=True, parents=True)
    with open(log_file, "w") as logf:
        # Remove missing geometries
        missing_geom = gdf[gdf.geometry.isnull()]
        if not missing_geom.empty:
            logf.write(f"Removed {len(missing_geom)} rows with missing geometry\n")
        gdf = gdf[gdf.geometry.notnull()]

        # Drop duplicate IDs
        if id_col in gdf.columns:
            dupes = gdf[gdf[id_col].duplicated(keep=False)]
            if not dupes.empty:
                logf.write(f"Dropped {len(dupes)} duplicate {id_col}s: {dupes[id_col].tolist()[:10]}...\n")
            gdf = gdf.drop_duplicates(subset=id_col)

        # Fix invalid polygons with buffer(0)
        invalid = gdf[~gdf.is_valid]
        if not invalid.empty:
            logf.write(f"Attempting to fix {len(invalid)} invalid polygons\n")
            fixed = []
            for idx, row in invalid.iterrows():
                try:
                    fixed_geom = row.geometry.buffer(0)
                    fixed.append(fixed_geom)
                except (ValueError, TopologicalError):
                    fixed.append(None)
                    logf.write(f"Polygon at index {idx} could not be fixed\n")
            gdf.loc[invalid.index, 'geometry'] = fixed
            # Remove any that are still invalid after fix
            still_invalid = gdf[~gdf.is_valid]
            if not still_invalid.empty:
                logf.write(f"{len(still_invalid)} polygons still invalid after buffer(0) and will be dropped.\n")
            gdf = gdf[gdf.is_valid]

    return gdf.reset_index(drop=True)

def standardize_id_column(gdf, canonical_id="Gebaeudecode", alternatives=["GebaeudeID", "BuildingID"]):
    """
    Ensures the GeoDataFrame/DataFrame has a unique, consistent ID column.
    Adds/renames if needed, logs and drops duplicates.
    """
    import logging
    from pathlib import Path

    # Try to find an alternative column if canonical is missing
    for alt in alternatives:
        if alt in gdf.columns and canonical_id not in gdf.columns:
            gdf[canonical_id] = gdf[alt]
    # If still missing, create synthetic ID
    if canonical_id not in gdf.columns:
        gdf[canonical_id] = gdf.index.astype(str)

    # Remove and log duplicates
    dupes = gdf[gdf[canonical_id].duplicated(keep=False)]
    if not dupes.empty:
        Path("results").mkdir(exist_ok=True)
        with open("results/duplicate_id_warnings.log", "a") as f:
            for bid in dupes[canonical_id]:
                f.write(f"Duplicate {canonical_id}: {bid}\n")
        gdf = gdf.drop_duplicates(subset=canonical_id)
    return gdf
