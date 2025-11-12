#!/usr/bin/env python3
"""
Smoke test for DHA (Decentralized Heating Agent)
"""

import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import shutil

def test_dha_smoke():
    """Test basic DHA functionality."""
    print("🧪 Testing DHA smoke test...")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        
        # Create test LFA data
        lfa_dir = tmp_path / "processed" / "lfa"
        lfa_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample LFA files (8760 hours)
        sample_series = [10.0 + i * 0.01 for i in range(8760)]  # Varying heat demand
        
        for i in range(3):  # 3 buildings
            building_id = f"building_{i+1}"
            lfa_data = {
                "series": sample_series,
                "q10": [s * 0.9 for s in sample_series],
                "q90": [s * 1.1 for s in sample_series]
            }
            
            with open(lfa_dir / f"{building_id}.json", "w") as f:
                json.dump(lfa_data, f)
        
        # Create test config
        config = {
            "lfa_glob": str(lfa_dir / "*.json"),
            "feeder_topology": "none",  # Will create sample topology
            "weather_parquet": None,
            "cop_bins": [
                {"t_min": -10, "t_max": 0, "cop": 2.5},
                {"t_min": 0, "t_max": 10, "cop": 3.0}
            ],
            "cop_default": 3.0,
            "utilization_threshold": 0.8,
            "v_min_pu": 0.90,
            "v_max_pu": 1.10,
            "out_dir": str(tmp_path / "processed" / "dha"),
            "eval_dir": str(tmp_path / "eval" / "dha"),
            "pandapower_enabled": False,
            "top_n_hours": 5
        }
        
        config_file = tmp_path / "test_dha.yml"
        import yaml
        with open(config_file, "w") as f:
            yaml.dump(config, f)
        
        # Test DHA adapter
        print("   Testing DHA adapter...")
        from src.dha_adapter import load_lfa_series, heat_to_electric_kw
        
        lfa_data = load_lfa_series(str(lfa_dir / "*.json"))
        assert len(lfa_data) == 3 * 8760  # 3 buildings × 8760 hours
        assert "building_id" in lfa_data.columns
        assert "hour" in lfa_data.columns
        assert "q_kw" in lfa_data.columns
        
        # Test heat to electric conversion
        lfa_el = heat_to_electric_kw(lfa_data, None, config["cop_bins"], config["cop_default"])
        assert len(lfa_el) == 3 * 8760
        assert "p_kw" in lfa_el.columns
        assert "cop" in lfa_el.columns
        
        # Test heuristic backend
        print("   Testing DHA heuristic backend...")
        from src.dha_heuristic import run_heuristic_analysis
        
        # Create sample topology
        building_ids = lfa_data['building_id'].unique()
        sample_topo = pd.DataFrame({
            'building_id': building_ids,
            'feeder_id': [f'F{i//2 + 1}' for i in range(len(building_ids))],
            'feeder_rating_kw': [50.0] * len(building_ids)
        })
        
        result = run_heuristic_analysis(
            lfa_el, sample_topo,
            top_n=5, util_thr=0.8,
            v_min_pu=0.90, v_max_pu=1.10
        )
        
        assert len(result) > 0
        assert "utilization_pct" in result.columns
        assert "v_end_pu" in result.columns
        
        print("✅ DHA smoke test passed!")
        return True

if __name__ == "__main__":
    test_dha_smoke()
