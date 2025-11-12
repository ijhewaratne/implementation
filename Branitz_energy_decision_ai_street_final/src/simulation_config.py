# src/simulation_config.py

# Physical constants for energy network simulations

# Water properties (for district heating)
WATER_PROPERTIES = {
    "density_kg_per_m3": 998.2,  # at 20°C
    "dynamic_viscosity_pa_s": 0.001002,  # at 20°C
    "specific_heat_capacity_j_per_kg_k": 4182,  # at 20°C
}

# Pipe specifications for district heating
PIPE_SPECS = {
    "DN100": {
        "diameter_mm": 100,
        "inner_diameter_mm": 96,
        "roughness_mm": 0.1,  # typical for steel pipes
        "max_velocity_m_per_s": 2.0,
        "max_pressure_drop_bar_per_km": 0.5,
    },
    "DN80": {
        "diameter_mm": 80,
        "inner_diameter_mm": 76,
        "roughness_mm": 0.1,
        "max_velocity_m_per_s": 2.0,
        "max_pressure_drop_bar_per_km": 0.8,
    },
    "DN50": {
        "diameter_mm": 50,
        "inner_diameter_mm": 48,
        "roughness_mm": 0.1,
        "max_velocity_m_per_s": 2.0,
        "max_pressure_drop_bar_per_km": 2.0,
    },
    "DN32": {
        "diameter_mm": 32,
        "inner_diameter_mm": 30,
        "roughness_mm": 0.1,
        "max_velocity_m_per_s": 2.0,
        "max_pressure_drop_bar_per_km": 5.0,
    },
}

# Electrical network specifications
ELECTRICAL_SPECS = {
    "low_voltage": {
        "voltage_kv": 0.4,
        "max_current_a": 630,
        "cable_type": "NAYY 4x150 SE",
        "resistance_ohm_per_km": 0.206,
        "reactance_ohm_per_km": 0.08,
    },
    "medium_voltage": {
        "voltage_kv": 10.0,
        "max_current_a": 400,
        "cable_type": "NA2XS2Y 3x150 RM/25",
        "resistance_ohm_per_km": 0.206,
        "reactance_ohm_per_km": 0.08,
    },
}

# Heat pump specifications
HEAT_PUMP_SPECS = {
    "residential": {
        "nominal_power_kw": 8.0,
        "cop_nominal": 3.5,
        "cop_min": 2.0,
        "cop_max": 4.5,
        "electrical_efficiency": 0.95,
    },
    "commercial": {
        "nominal_power_kw": 20.0,
        "cop_nominal": 3.2,
        "cop_min": 1.8,
        "cop_max": 4.0,
        "electrical_efficiency": 0.92,
    },
}

# District heating plant specifications
DH_PLANT_SPECS = {
    "biomass_boiler": {
        "nominal_power_mw": 1.0,
        "efficiency": 0.85,
        "fuel_type": "biomass",
        "emissions_factor_kg_co2_per_mwh": 70,
    },
    "chp_plant": {
        "nominal_power_mw": 2.0,
        "electrical_efficiency": 0.35,
        "thermal_efficiency": 0.45,
        "fuel_type": "natural_gas",
        "emissions_factor_kg_co2_per_mwh": 200,
    },
}

# Simulation parameters
SIMULATION_PARAMS = {
    "convergence_tolerance": 1e-6,
    "max_iterations": 100,
    "temperature_tolerance_k": 0.1,
    "pressure_tolerance_bar": 0.01,
}

# Network topology parameters
NETWORK_PARAMS = {
    "max_pipe_length_m": 1000,  # Maximum pipe length before adding intermediate nodes
    "building_connection_length_m": 50,  # Typical connection length from main to building
    "min_pipe_diameter": "DN32",
    "default_pipe_diameter": "DN50",
    "pressure_limits": {
        "min_bar": 1.0,
        "max_bar": 10.0,
        "nominal_bar": 6.0,
    },
    "temperature_limits": {
        "supply_min_c": 60,
        "supply_max_c": 90,
        "return_min_c": 30,
        "return_max_c": 50,
    },
}
