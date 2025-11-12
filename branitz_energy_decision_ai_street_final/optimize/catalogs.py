from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import pandas as pd


@dataclass
class PipeType:
    dn: int
    d_inner_m: Optional[float]
    d_outer_m: Optional[float]
    u_wpermk: Optional[float]
    w_loss_w_per_m: Optional[float]
    cost_eur_per_m: Optional[float]


def load_pipe_catalog(csv_path: str = "data/catalogs/pipe_catalog.csv") -> List[PipeType]:
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(f"Pipe catalog not found: {csv_path}")
    df = pd.read_csv(csv_path)
    out: List[PipeType] = []
    for _, r in df.iterrows():
        out.append(
            PipeType(
                dn=int(r["dn"]),
                d_inner_m=(float(r["d_inner_m"]) if pd.notna(r["d_inner_m"]) else None),
                d_outer_m=(float(r["d_outer_m"]) if pd.notna(r["d_outer_m"]) else None),
                u_wpermk=(float(r["u_wpermk"]) if pd.notna(r["u_wpermk"]) else None),
                w_loss_w_per_m=(
                    float(r["w_loss_w_per_m"]) if pd.notna(r["w_loss_w_per_m"]) else None
                ),
                cost_eur_per_m=(
                    float(r["cost_eur_per_m"]) if pd.notna(r["cost_eur_per_m"]) else None
                ),
            )
        )
    # Sort by DN
    out.sort(key=lambda x: x.dn)
    return out
