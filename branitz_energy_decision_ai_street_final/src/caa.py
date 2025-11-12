from __future__ import annotations
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import yaml
from zipfile import ZipFile, ZIP_DEFLATED

@dataclass
class CAAConfig:
    scenario_name: str
    fast: bool
    use_make_run_branitz: bool
    artifacts: List[str]
    out_zip: str
    skip_pipeline: bool = False
    skip_pipeline: bool = False
    skip_pipeline: bool = False
    skip_pipeline: bool = False

def _load_cfg(path: str) -> CAAConfig:
    y = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return CAAConfig(
        scenario_name=y.get("scenario_name", "scenario"),
        fast=bool(y.get("fast", False)),
        use_make_run_branitz=bool(y.get("use_make_run_branitz", True)),
        artifacts=list(y.get("artifacts", [])),
        out_zip=y.get("out_zip", "eval/caa/diagnostics.zip"),
        skip_pipeline=bool(y.get("skip_pipeline", False)),
    )

def _run(cmd: List[str], env=None) -> None:
    print("CAA> ", " ".join(cmd))
    res = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    sys.stdout.write(res.stdout or "")
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")

def _maybe_fast_env(fast: bool):
    # Downstream tools can honor FAST=1 to limit scope (e.g., 5 buildings).
    e = os.environ.copy()
    if fast:
        e["FAST"] = "1"
    return e

def _pipeline(cfg: CAAConfig):
    if cfg.skip_pipeline:
        print("CAA> Skipping pipeline execution (skip_pipeline=true)")
        return
        
    env = _maybe_fast_env(cfg.fast)

    # Prefer a single orchestrator target if present; else call granular steps.
    if cfg.use_make_run_branitz and Path("Makefile").exists():
        _run(["make", "run-branitz"], env=env)
    else:
        # Fallback: run the known targets in order (adjust if your Makefile uses other names)
        _run(["make", "lfa"], env=env)
        _run(["make", "cha"], env=env)
        _run(["make", "dha"], env=env)
        _run(["make", "te"], env=env)
        _run(["make", "kpi"], env=env)
        # Optional: APA sensitivity
        if Path("configs/apa.yml").exists():
            _run(["make", "apa"], env=env)

def _require(path: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return p

def _dod_checks(cfg: CAAConfig):
    # 1) Run repo's schema/data validation script (if present)
    if Path("scripts/validate_json.py").exists():
        _run([sys.executable, "scripts/validate_json.py"])
    # 2) Minimal artifact presence checks
    missing = [p for p in cfg.artifacts if not Path(p).exists()]
    if missing:
        raise RuntimeError(f"DoD failed: missing artifacts: {missing}")

def _manifest(cfg: CAAConfig) -> dict:
    # Small manifest written inside the zip for traceability
    return {
        "scenario_name": cfg.scenario_name,
        "fast": cfg.fast,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git": _git_meta(),
    }

def _git_meta():
    try:
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        return {"commit": rev, "branch": branch}
    except Exception:
        return {"commit": None, "branch": None}

def _zip_diagnostics(cfg: CAAConfig):
    out_path = Path(cfg.out_zip)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(out_path, "w", compression=ZIP_DEFLATED) as z:
        # Add manifest.json
        z.writestr("manifest.json", json.dumps(_manifest(cfg), indent=2))
        # Add artifacts as-is, skip non-existent silently (they were checked already)
        for rel in cfg.artifacts:
            p = Path(rel)
            if p.exists() and p.is_file():
                z.write(p, arcname=str(p))
    print(f"CAA> wrote {out_path}")

def run(config_path: str = "configs/caa.yml") -> dict:
    cfg = _load_cfg(config_path)
    # 0) Optional: skip orchestration for tests/dry-runs
    if cfg.skip_pipeline:
        _dod_checks(cfg)
        _zip_diagnostics(cfg)
        return {"status":"ok","zip":cfg.out_zip,"scenario":cfg.scenario_name,"fast":cfg.fast,"skipped":True}

    # 1) Run pipeline (delegates to orchestrator/Make targets)
    _pipeline(cfg)
    # 2) Enforce DoD (must fail if upstream fails)
    _dod_checks(cfg)
    # 3) Produce diagnostics bundle
    _zip_diagnostics(cfg)
    return {"status":"ok","zip":cfg.out_zip,"scenario":cfg.scenario_name,"fast":cfg.fast}

if __name__ == "__main__":
    import sys, json as _json
    print(_json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "configs/caa.yml"), indent=2))
