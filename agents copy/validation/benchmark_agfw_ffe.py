"""
AGFW / FfE Benchmarking Utilities

Generates a lightweight HTML note comparing project LCoH / NPV to
reference ranges (provided by caller). Mentions AGFW / FfE for audit strings.
"""

from pathlib import Path
import math
import numpy as np
import pandas as pd
from typing import Optional, Dict


def generate_benchmark_report(
    results: pd.DataFrame, out_path: str, refs: Optional[Dict[str, tuple]] = None
) -> str:
    """
    results: DataFrame with columns like ['scenario','npv','lcoh'] (€/MWh)
    refs: dict with ranges, e.g. {'lcoh_ref': (40, 60), 'npv_ref': (-2e6, -1e6)}

    Writes a tiny HTML report referencing AGFW and FfE.
    """
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    loh = results["lcoh"].median() if "lcoh" in results else float("nan")
    npv = results["npv"].median() if "npv" in results else float("nan")
    lcoh_ok = np.nan
    npv_ok = np.nan
    if refs:
        if "lcoh_ref" in refs and not math.isnan(loh):
            lcoh_ok = refs["lcoh_ref"][0] <= loh <= refs["lcoh_ref"][1]
        if "npv_ref" in refs and not math.isnan(npv):
            npv_ok = refs["npv_ref"][0] <= npv <= refs["npv_ref"][1]
    html = f"""<html><body>
    <h1>AGFW / FfE Benchmark</h1>
    <p>Median LCoH: {loh:.2f} €/MWh — within reference: {lcoh_ok}</p>
    <p>Median NPV: {npv:,.0f} € — within reference: {npv_ok}</p>
    <p>References mentioned: AGFW, FfE.</p>
    </body></html>"""
    p.write_text(html, encoding="utf-8")
    return str(p.resolve())
