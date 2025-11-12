from __future__ import annotations
from pathlib import Path
import sys

def run(config_path: str = "configs/eaa.yml", tca_config: str = "configs/tca.yml") -> dict:
    from src import eaa, tca
    eaa_res = eaa.run(config_path)
    tca_res = tca.run(tca_config)
    return {"eaa": eaa_res, "tca": tca_res}

if __name__ == "__main__":
    cfg = sys.argv[1] if len(sys.argv) > 1 else "configs/eaa.yml"
    tcfg = sys.argv[2] if len(sys.argv) > 2 else "configs/tca.yml"
    print(run(cfg, tcfg))





