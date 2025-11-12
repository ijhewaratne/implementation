#!/usr/bin/env python3
"""
CHA Convergence Flag Generator
Creates convergence information for CHA simulations.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any


def create_convergence_flag(slug: str, root: Path, converged: bool = True, runtime_s: float = 0.0, solver: str = "pipeflow") -> None:
    """Create convergence flag file for CHA simulation."""
    
    # Determine output path
    if slug:
        output_path = root / "eval" / "cha" / slug / "sim.json"
    else:
        output_path = root / "eval" / "cha" / "sim.json"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create convergence data
    convergence_data = {
        "converged": converged,
        "solver": solver,
        "runtime_s": runtime_s,
        "timestamp": time.time(),
        "slug": slug if slug else "system"
    }
    
    # Write to file
    output_path.write_text(json.dumps(convergence_data, indent=2), encoding="utf-8")
    print(f"✅ Created convergence flag: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Create CHA convergence flag")
    parser.add_argument("--slug", default="", help="Street slug (empty for system)")
    parser.add_argument("--root", default=".", help="Project root directory")
    parser.add_argument("--converged", action="store_true", help="Mark as converged")
    parser.add_argument("--runtime", type=float, default=0.0, help="Runtime in seconds")
    parser.add_argument("--solver", default="pipeflow", help="Solver name")
    
    args = parser.parse_args()
    
    root_path = Path(args.root)
    create_convergence_flag(args.slug, root_path, args.converged, args.runtime, args.solver)


if __name__ == "__main__":
    main()





