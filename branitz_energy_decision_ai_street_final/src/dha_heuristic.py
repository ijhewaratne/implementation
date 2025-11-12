#!/usr/bin/env python3
"""
DHA Heuristic Backend: Fast feeder load aggregation and analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import warnings

warnings.filterwarnings("ignore")

def aggregate_feeder_loads(lfa_el: pd.DataFrame, topo: pd.DataFrame) -> pd.DataFrame:
    """Aggregate electric loads by feeder and hour."""
    print("🔌 Aggregating feeder loads...")
    
    # Merge topology with electric loads
    merged = lfa_el.merge(topo, on='building_id', how='inner')
    
    if merged.empty:
        raise ValueError("No buildings found in topology after merge")
    
    print(f"   Found {len(merged['building_id'].unique())} buildings in topology")
    print(f"   Found {len(merged['feeder_id'].unique())} feeders")
    
    # Aggregate by feeder and hour
    agg = merged.groupby(['feeder_id', 'hour']).agg({
        'p_kw': 'sum',
        'feeder_rating_kw': 'first'  # Should be same for all buildings on same feeder
    }).reset_index()
    
    # Calculate utilization percentage
    agg['utilization_pct'] = (agg['p_kw'] / agg['feeder_rating_kw']) * 100
    
    # Handle any division by zero or invalid values
    agg = agg.replace([np.inf, -np.inf], np.nan)
    agg = agg.dropna()
    
    print(f"✅ Aggregated {len(agg)} feeder-hour records")
    print(f"   Peak utilization: {agg['utilization_pct'].max():.1f}%")
    print(f"   Average utilization: {agg['utilization_pct'].mean():.1f}%")
    
    return agg

def top_n_peak_hours(total_system_kw: pd.Series, n: int) -> list[int]:
    """Get top N peak hours from system load."""
    return list(total_system_kw.nlargest(n).index.astype(int))

def calculate_heuristic_voltage_drops(
    agg: pd.DataFrame, 
    v_min_pu: float, 
    v_max_pu: float
) -> pd.DataFrame:
    """Calculate heuristic voltage drops based on utilization."""
    print("⚡ Calculating heuristic voltage drops...")
    
    result = agg.copy()
    
    # Improved heuristic: voltage drop based on utilization with bounds
    # For utilization > 100%, cap the voltage drop at reasonable levels
    utilization_pct = result['utilization_pct'].clip(upper=200.0)  # Cap at 200%
    
    # Calculate voltage drop (per unit) - more realistic curve
    # At 0% utilization: 0% drop
    # At 100% utilization: 10% drop  
    # At 200% utilization: 15% drop (capped)
    v_drop_pu = (utilization_pct / 100) * 0.1
    
    # Apply additional penalty for overloading
    overloading_penalty = np.where(utilization_pct > 100, 
                                  (utilization_pct - 100) / 100 * 0.05, 0)
    v_drop_pu += overloading_penalty
    
    # Cap total voltage drop at 20%
    v_drop_pu = v_drop_pu.clip(upper=0.2)
    
    # Calculate voltage at feeder end (per unit)
    result['v_end_pu'] = 1.0 - v_drop_pu
    
    # Flag voltage violations
    result['v_violation'] = (
        (result['v_end_pu'] < v_min_pu) | 
        (result['v_end_pu'] > v_max_pu)
    )
    
    print(f"   Voltage range: {result['v_end_pu'].min():.3f} to {result['v_end_pu'].max():.3f} pu")
    print(f"   Voltage violations: {result['v_violation'].sum()} records")
    
    return result

def write_outputs(
    agg: pd.DataFrame, 
    out_dir: str, 
    eval_dir: str, 
    util_thr: float, 
    v_min_pu: float, 
    v_max_pu: float
) -> Tuple[str, str]:
    """Write output files and return file paths."""
    print("💾 Writing DHA outputs...")
    
    # Create output directories
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    Path(eval_dir).mkdir(parents=True, exist_ok=True)
    
    # Write feeder loads CSV
    feeder_csv = Path(out_dir) / "feeder_loads.csv"
    agg.to_csv(feeder_csv, index=False)
    print(f"   ✅ Feeder loads: {feeder_csv}")
    
    # Identify violations
    util_violations = agg[agg['utilization_pct'] > (util_thr * 100)].copy()
    
    # Add voltage violations if available
    if 'v_violation' in agg.columns:
        v_violations = agg[agg['v_violation']].copy()
        all_violations = pd.concat([util_violations, v_violations], ignore_index=True).drop_duplicates()
    else:
        all_violations = util_violations
    
    # Write violations CSV
    viol_csv = Path(eval_dir) / "violations.csv"
    if not all_violations.empty:
        all_violations.to_csv(viol_csv, index=False)
        print(f"   ⚠️ Violations: {viol_csv} ({len(all_violations)} records)")
    else:
        # Create empty violations file
        pd.DataFrame(columns=agg.columns).to_csv(viol_csv, index=False)
        print(f"   ✅ No violations: {viol_csv}")
    
    return str(feeder_csv), str(viol_csv)

def run_heuristic_analysis(
    lfa_el: pd.DataFrame, 
    topo: pd.DataFrame, 
    top_n: int,
    util_thr: float,
    v_min_pu: float,
    v_max_pu: float
) -> pd.DataFrame:
    """Run complete heuristic analysis workflow."""
    print("🚀 Running DHA heuristic analysis...")
    
    # Step 1: Aggregate feeder loads
    agg = aggregate_feeder_loads(lfa_el, topo)
    
    # Step 2: Select top N peak hours
    total_system = agg.groupby('hour')['p_kw'].sum()
    peak_hours = top_n_peak_hours(total_system, top_n)
    agg_peak = agg[agg['hour'].isin(peak_hours)].copy()
    
    print(f"   Selected top {len(peak_hours)} peak hours: {peak_hours}")
    
    # Step 3: Calculate voltage drops
    agg_peak = calculate_heuristic_voltage_drops(agg_peak, v_min_pu, v_max_pu)
    
    return agg_peak

if __name__ == "__main__":
    # Test the heuristic backend
    print("🧪 Testing DHA Heuristic Backend...")
    
    # Sample data
    sample_lfa_el = pd.DataFrame({
        'building_id': ['B1', 'B1', 'B2', 'B2'],
        'hour': [0, 1, 0, 1],
        'p_kw': [10.0, 12.0, 8.0, 15.0],
        'cop': [3.0, 3.0, 3.0, 3.0]
    })
    
    sample_topo = pd.DataFrame({
        'building_id': ['B1', 'B2'],
        'feeder_id': ['F1', 'F1'],
        'feeder_rating_kw': [50.0, 50.0]
    })
    
    try:
        result = run_heuristic_analysis(
            sample_lfa_el, sample_topo, 
            top_n=2, util_thr=0.8, 
            v_min_pu=0.90, v_max_pu=1.10
        )
        
        print("\n📊 Sample analysis result:")
        print(result)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
