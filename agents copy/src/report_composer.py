from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
import markdown as md

def _require(path: str) -> Path:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"ReportComposer: required file missing: {path}")
    return p

def _load_kpi(kpi_json: str) -> Dict[str, Any]:
    return json.loads(_require(kpi_json).read_text(encoding="utf-8"))

def _load_eaa_summary(csv_path: str) -> List[Dict[str, Any]]:
    df = pd.read_csv(_require(csv_path))
    # keep only columns used in the template; no new calculations
    cols = ["metric", "mean", "median", "p2_5", "p97_5"]
    for c in cols:
        if c not in df.columns:
            raise ValueError(f"EAA summary missing column '{c}'")
    return df[cols].to_dict(orient="records")

def _head_csv(csv_path: str, n: int = 5) -> List[Dict[str, Any]]:
    p = Path(csv_path)
    if not p.exists():
        return []
    df = pd.read_csv(p)
    return df.head(n).to_dict(orient="records")

def _validate_artifacts(paths: List[str]) -> List[str]:
    missing = [p for p in paths if not Path(p).exists()]
    if missing:
        raise FileNotFoundError(f"ReportComposer: declared artifacts missing: {missing}")
    return paths

def _render_markdown(template_path: str, context: Dict[str, Any]) -> str:
    loader = FileSystemLoader(str(Path(template_path).parent))
    env = Environment(loader=loader, undefined=StrictUndefined, autoescape=False, trim_blocks=True, lstrip_blocks=True)
    tpl = env.get_template(Path(template_path).name)
    return tpl.render(**context)

def _markdown_to_html(md_text: str) -> str:
    return md.markdown(md_text, extensions=["tables", "toc", "fenced_code"])

def run(config_path: str = "configs/report.yml") -> Dict[str, Any]:
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))

    # Required
    kpi = _load_kpi(cfg["kpi_json"])
    eaa_summary = _load_eaa_summary(cfg["eaa_summary_csv"])

    # Optional tables (only shown if files exist)
    cha_head = _head_csv(cfg.get("cha_segments_csv", "")) if cfg.get("cha_segments_csv") else []
    dha_head = _head_csv(cfg.get("dha_feeders_csv", "")) if cfg.get("dha_feeders_csv") else []

    # Artifacts list (if provided, ALL must exist)
    artifacts = _validate_artifacts(cfg.get("artifacts", [])) if cfg.get("artifacts") else []

    # Template → Markdown
    md_text = _render_markdown(
        cfg["template_md"],
        dict(
            scenario_name=cfg.get("scenario_name", "scenario"),
            kpi=kpi,
            eaa_summary=eaa_summary,
            cha_head=cha_head,
            dha_head=dha_head,
            artifacts=artifacts,
        ),
    )

    # Markdown → HTML
    html = _markdown_to_html(md_text)

    # Write out
    out = Path(cfg.get("out_html", "docs/branitz_recommendation.html"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return {"status": "ok", "out_html": str(out)}

if __name__ == "__main__":
    import sys, json as _json
    print(_json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "configs/report.yml"), indent=2))
