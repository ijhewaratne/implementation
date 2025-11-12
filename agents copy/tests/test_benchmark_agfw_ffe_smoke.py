"""
Smoke test for AGFW/FfE benchmarking.
"""

import pandas as pd
from pathlib import Path
from validation.benchmark_agfw_ffe import generate_benchmark_report


def test_benchmark_report_smoke(tmp_path):
    """Test benchmark report generation with sample data."""
    df = pd.DataFrame(
        {"scenario": ["a", "b", "c"], "lcoh": [50.0, 55.0, 52.0], "npv": [-1.5e6, -1.6e6, -1.4e6]}
    )
    out = tmp_path / "bench.html"
    p = generate_benchmark_report(df, str(out), {"lcoh_ref": (40, 60), "npv_ref": (-2e6, -1e6)})
    text = Path(p).read_text(encoding="utf-8")
    assert "AGFW" in text and "FfE" in text
    assert "Benchmark" in text
