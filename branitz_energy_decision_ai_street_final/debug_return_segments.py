import pandas as pd
from optimize.diameter_optimizer import Segment, DiameterOptimizer
from pathlib import Path

# Create test data
catalog = pd.DataFrame({
    'dn': [100],
    'd_inner_m': [0.100],
    'd_outer_m': [0.120],
    'w_loss_w_per_m': [45.0],
    'u_wpermk': [0.4],
    'cost_eur_per_m': [300.0],
})

segs = [
    Segment('SUP', 100.0, 0.01, 0, 'P1', is_supply=True),
    Segment('RET', 1e6, 0.50, 0, 'P99', is_supply=False),
]

design = dict(T_supply=80, T_return=50, T_soil=10, rho=1000.0, mu=4.5e-4, cp=4180.0,
              eta_pump=1.0, hours=10, v_feasible_target=1.3, v_limit=1.5, deltaT_min=30.0, K_minor=0.0)
econ = dict(price_el=0.25, cost_heat_prod=55.0, years=1, r=0.0, o_and_m_rate=0.0)

# Save catalog
catalog.to_csv('temp_catalog.csv', index=False)

opt = DiameterOptimizer(segs, design, econ, 'temp_catalog.csv')

m = opt.evaluate_quick({'SUP': 100, 'RET': 100})
print('Path stats keys:', list(m['path_stats'].keys()))
print('Path stats:', m['path_stats'])

# Clean up
Path('temp_catalog.csv').unlink(missing_ok=True) 