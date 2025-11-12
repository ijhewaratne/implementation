#!/usr/bin/env python3
"""
Decentralized Heating Agent (DHA) - Main Implementation
Converts LFA heat series to electric loads and analyzes feeder utilization
"""

from __future__ import annotations
import yaml
from pathlib import Path
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

from .dha_adapter import load_lfa_series, load_weather_opt, heat_to_electric_kw
from .dha_heuristic import aggregate_feeder_loads, write_outputs, run_heuristic_analysis

try:
    from .dha_pandapower import run_loadflow_for_hours
    PANDAPOWER_AVAILABLE = True
except ImportError:
    run_loadflow_for_hours = None
    PANDAPOWER_AVAILABLE = False

def top_n_peak_hours(total_system_kw: pd.Series, n: int) -> list[int]:
    """Get top N peak hours from system load."""
    return list(total_system_kw.nlargest(n).index.astype(int))

def run(config_path: str = "configs/dha.yml") -> dict:
    """Run the complete DHA workflow."""
    print("⚡ Running Decentralized Heating Agent (DHA)...")
    print("=" * 60)
    
    # Load configuration
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    
    # Extract configuration parameters
    lfa_glob = cfg.get("lfa_glob", "processed/lfa/*.json")
    topo_path = cfg.get("feeder_topology", "data/processed/feeder_topology.parquet")
    weather_path = cfg.get("weather_parquet")
    bins = cfg.get("cop_bins", [])
    cop_default = float(cfg.get("cop_default", 3.0))
    util_thr = float(cfg.get("utilization_threshold", 0.8))
    v_min_pu = float(cfg.get("v_min_pu", 0.90))
    v_max_pu = float(cfg.get("v_max_pu", 1.10))
    out_dir = cfg.get("out_dir", "processed/dha")
    eval_dir = cfg.get("eval_dir", "eval/dha")
    pp_enabled = bool(cfg.get("pandapower_enabled", False))
    top_n = int(cfg.get("top_n_hours", 10))
    
    print(f"📋 Configuration:")
    print(f"   LFA files: {lfa_glob}")
    print(f"   Topology: {topo_path}")
    print(f"   Weather: {weather_path or 'None'}")
    print(f"   COP bins: {len(bins)} temperature ranges")
    print(f"   Default COP: {cop_default}")
    print(f"   Utilization threshold: {util_thr*100:.0f}%")
    print(f"   Voltage limits: {v_min_pu:.2f} - {v_max_pu:.2f} pu")
    print(f"   Top N hours: {top_n}")
    print(f"   Pandapower enabled: {pp_enabled}")
    
    try:
        # Step 1: Load inputs
        print("\n📁 Step 1: Loading inputs...")
        lfa = load_lfa_series(lfa_glob)
        weather = load_weather_opt(weather_path)
        
        # Check if topology file exists
        if not Path(topo_path).exists():
            print(f"   ⚠️ Topology file not found: {topo_path}")
            print("   Creating sample topology for demonstration...")
            
            # Create sample topology
            building_ids = lfa['building_id'].unique()
            sample_topo = pd.DataFrame({
                'building_id': building_ids,
                'feeder_id': [f'F{i//5 + 1}' for i in range(len(building_ids))],  # Group by 5
                'feeder_rating_kw': [2000.0] * len(building_ids)  # 2 MW per feeder (more realistic)
            })
            topo = sample_topo
            print(f"   ✅ Created sample topology for {len(building_ids)} buildings")
        else:
            topo = pd.read_parquet(topo_path)
            print(f"   ✅ Loaded topology: {len(topo)} building-feeder mappings")
        
        # Step 2: Convert heat to electric
        print("\n🔄 Step 2: Converting heat demand to electric load...")
        lfa_el = heat_to_electric_kw(lfa, weather, bins, cop_default)
        
        # Step 3: Aggregate per feeder & select top-N hours
        print("\n🔌 Step 3: Aggregating feeder loads...")
        agg = aggregate_feeder_loads(lfa_el, topo)
        
        # Select top N peak hours
        total_system = agg.groupby('hour')['p_kw'].sum()
        hours = top_n_peak_hours(total_system, top_n)
        agg_peak = agg[agg['hour'].isin(hours)].copy()
        
        print(f"   Selected top {len(hours)} peak hours: {hours}")
        print(f"   Peak system load: {total_system.loc[hours[0]]:.1f} kW")
        
        # Step 4: Optional pandapower voltage calculation
        if pp_enabled and PANDAPOWER_AVAILABLE and run_loadflow_for_hours is not None:
            print("\n⚡ Step 4: Running pandapower load flow analysis...")
            agg_peak = run_loadflow_for_hours(agg_peak, (v_min_pu, v_max_pu))
        else:
            print("\n⚡ Step 4: Using heuristic voltage calculation...")
            # Use heuristic voltage calculation
            agg_peak['v_drop_pu'] = (agg_peak['utilization_pct'] / 100) * 0.2
            agg_peak['v_end_pu'] = 1.0 - agg_peak['v_drop_pu']
            agg_peak['v_violation'] = (
                (agg_peak['v_end_pu'] < v_min_pu) | 
                (agg_peak['v_end_pu'] > v_max_pu)
            )
        
        # Step 5: Outputs & violations
        print("\n💾 Step 5: Writing outputs...")
        feeder_csv, viol_csv = write_outputs(agg_peak, out_dir, eval_dir, util_thr, v_min_pu, v_max_pu)
        
        # Summary statistics
        print("\n📊 DHA Analysis Summary:")
        print(f"   Buildings analyzed: {len(lfa['building_id'].unique())}")
        print(f"   Feeders: {len(agg_peak['feeder_id'].unique())}")
        print(f"   Peak hours analyzed: {len(hours)}")
        print(f"   Max utilization: {agg_peak['utilization_pct'].max():.1f}%")
        print(f"   Voltage range: {agg_peak['v_end_pu'].min():.3f} - {agg_peak['v_end_pu'].max():.3f} pu")
        
        if 'v_violation' in agg_peak.columns:
            violations = agg_peak['v_violation'].sum()
            print(f"   Voltage violations: {violations}")
        
        util_violations = len(agg_peak[agg_peak['utilization_pct'] > (util_thr * 100)])
        print(f"   Utilization violations: {util_violations}")
        
        print("\n✅ DHA analysis completed successfully!")
        
        return {
            "status": "ok",
            "hours": hours,
            "feeder_loads": feeder_csv,
            "violations": viol_csv,
            "pandapower": bool(pp_enabled and PANDAPOWER_AVAILABLE),
            "buildings_analyzed": len(lfa['building_id'].unique()),
            "feeders": len(agg_peak['feeder_id'].unique()),
            "max_utilization": float(agg_peak['utilization_pct'].max()),
            "voltage_range": [float(agg_peak['v_end_pu'].min()), float(agg_peak['v_end_pu'].max())]
        }
        
    except Exception as e:
        print(f"\n❌ DHA analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import json
    import sys
    
    # Get config path from command line or use default
    cfg = sys.argv[1] if len(sys.argv) > 1 else "configs/dha.yml"
    
    # Run DHA analysis
    result = run(cfg)
    
    # Print result as JSON
    print(json.dumps(result, indent=2))
