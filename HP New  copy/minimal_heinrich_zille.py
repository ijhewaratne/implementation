#!/usr/bin/env python3
"""
Minimal Heinrich-Zille-Straße Heat Grid Simulation
Based on the successful simple_heat_grid.py approach
"""

import pandapipes as pps
import json
from pathlib import Path

def create_minimal_heinrich_zille_network():
    """Create a minimal working heat grid for Heinrich-Zille-Straße"""
    
    # Create empty network
    net = pps.create_empty_network()
    pps.create_fluid_from_lib(net, "water")
    
    # Network parameters
    SUPPLY_TEMP_C = 85.0
    RETURN_TEMP_C = 55.0
    SUPPLY_PRESSURE = 3.0  # bar
    RETURN_PRESSURE = 2.5  # bar
    
    print("Creating minimal Heinrich-Zille-Straße heat grid...")
    
    # Create a simple linear network: Plant -> Street -> Consumers
    # Supply side
    plant_supply = pps.create_junction(net, pn_bar=SUPPLY_PRESSURE, tfluid_k=SUPPLY_TEMP_C+273.15, name="Plant_Supply")
    street_start_supply = pps.create_junction(net, pn_bar=2.9, tfluid_k=SUPPLY_TEMP_C+273.15, name="Street_Start_Supply")
    street_mid_supply = pps.create_junction(net, pn_bar=2.8, tfluid_k=SUPPLY_TEMP_C+273.15, name="Street_Mid_Supply")
    street_end_supply = pps.create_junction(net, pn_bar=2.7, tfluid_k=SUPPLY_TEMP_C+273.15, name="Street_End_Supply")
    
    # Return side
    plant_return = pps.create_junction(net, pn_bar=RETURN_PRESSURE, tfluid_k=RETURN_TEMP_C+273.15, name="Plant_Return")
    street_start_return = pps.create_junction(net, pn_bar=2.6, tfluid_k=RETURN_TEMP_C+273.15, name="Street_Start_Return")
    street_mid_return = pps.create_junction(net, pn_bar=2.7, tfluid_k=RETURN_TEMP_C+273.15, name="Street_Mid_Return")
    street_end_return = pps.create_junction(net, pn_bar=2.8, tfluid_k=RETURN_TEMP_C+273.15, name="Street_End_Return")
    
    # Create pipes: Supply circuit (Plant -> Street)
    pps.create_pipe_from_parameters(net, plant_supply, street_start_supply, 
                                   length_km=0.3, diameter_m=0.2, k_mm=0.1, 
                                   alpha_w_per_m2k=5.0, name="Main_Supply_1")
    pps.create_pipe_from_parameters(net, street_start_supply, street_mid_supply, 
                                   length_km=0.2, diameter_m=0.15, k_mm=0.1, 
                                   alpha_w_per_m2k=5.0, name="Main_Supply_2")
    pps.create_pipe_from_parameters(net, street_mid_supply, street_end_supply, 
                                   length_km=0.2, diameter_m=0.15, k_mm=0.1, 
                                   alpha_w_per_m2k=5.0, name="Main_Supply_3")
    
    # Create pipes: Return circuit (Street -> Plant)
    pps.create_pipe_from_parameters(net, street_end_return, street_mid_return, 
                                   length_km=0.2, diameter_m=0.15, k_mm=0.1, 
                                   alpha_w_per_m2k=5.0, name="Main_Return_3")
    pps.create_pipe_from_parameters(net, street_mid_return, street_start_return, 
                                   length_km=0.2, diameter_m=0.15, k_mm=0.1, 
                                   alpha_w_per_m2k=5.0, name="Main_Return_2")
    pps.create_pipe_from_parameters(net, street_start_return, plant_return, 
                                   length_km=0.3, diameter_m=0.2, k_mm=0.1, 
                                   alpha_w_per_m2k=5.0, name="Main_Return_1")
    
    # Create consumers (sinks and sources) - representing Heinrich-Zille-Straße buildings
    # Calculate mass flow from heat demand: mdot = Q / (cp * dT)
    cp = 4180  # J/kg/K
    dT = SUPPLY_TEMP_C - RETURN_TEMP_C  # 30 K
    
    # Consumer 1: 50 kW heat demand
    mdot1 = 50000 / (cp * dT)  # kg/s
    pps.create_sink(net, street_start_supply, mdot_kg_per_s=mdot1, name="Building1_Sink")
    pps.create_source(net, street_start_return, mdot_kg_per_s=mdot1, name="Building1_Source")
    
    # Consumer 2: 30 kW heat demand
    mdot2 = 30000 / (cp * dT)  # kg/s
    pps.create_sink(net, street_mid_supply, mdot_kg_per_s=mdot2, name="Building2_Sink")
    pps.create_source(net, street_mid_return, mdot_kg_per_s=mdot2, name="Building2_Source")
    
    # Consumer 3: 40 kW heat demand
    mdot3 = 40000 / (cp * dT)  # kg/s
    pps.create_sink(net, street_end_supply, mdot_kg_per_s=mdot3, name="Building3_Sink")
    pps.create_source(net, street_end_return, mdot_kg_per_s=mdot3, name="Building3_Source")
    
    # Create boundary conditions
    pps.create_ext_grid(net, plant_supply, p_bar=SUPPLY_PRESSURE, t_k=SUPPLY_TEMP_C+273.15, name="Plant_Supply_Grid")
    pps.create_ext_grid(net, plant_return, p_bar=RETURN_PRESSURE, t_k=RETURN_TEMP_C+273.15, name="Plant_Return_Grid")
    
    print(f"Network created:")
    print(f"  Junctions: {len(net.junction)}")
    print(f"  Pipes: {len(net.pipe)}")
    print(f"  Sinks: {len(net.sink)}")
    print(f"  Sources: {len(net.source)}")
    print(f"  External grids: {len(net.ext_grid)}")
    
    return net

def run_heat_grid_simulation(net):
    """Run the heat grid simulation"""
    
    print("\nRunning Heinrich-Zille-Straße heat grid simulation...")
    
    try:
        # Run hydraulic calculation first
        print("Step 1: Hydraulic calculation...")
        pps.pipeflow(net, mode="hydraulics", 
                     max_iter_hyd=100, 
                     tol_p=1e-4, 
                     tol_m=1e-5,
                     friction_model="nikuradse")
        print("✓ Hydraulic calculation successful")
        
        # Then thermal calculation
        print("Step 2: Thermal calculation...")
        pps.pipeflow(net, mode="sequential", 
                     max_iter_hyd=100, 
                     max_iter_therm=50,
                     tol_p=1e-4, 
                     tol_m=1e-5,
                     tol_T=1e-2,
                     friction_model="nikuradse")
        print("✓ Heat grid simulation successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Simulation failed: {e}")
        return False

def analyze_results(net):
    """Analyze the simulation results"""
    
    print("\n=== HEINRICH-ZILLE-STRAßE SIMULATION RESULTS ===")
    
    # Junction results
    print("\nJunction Results:")
    for idx, row in net.res_junction.iterrows():
        name = net.junction.loc[idx, 'name']
        temp_c = row['t_k'] - 273.15
        pressure_bar = row['p_bar']
        print(f"  {name}: T={temp_c:.1f}°C, P={pressure_bar:.2f} bar")
    
    # Pipe results
    print("\nPipe Results:")
    for idx, row in net.res_pipe.iterrows():
        name = net.pipe.loc[idx, 'name']
        velocity = row['v_mean_m_per_s']
        mass_flow = row['mdot_from_kg_per_s']
        print(f"  {name}: v={velocity:.2f} m/s, ṁ={mass_flow:.2f} kg/s")
    
    # Sink and Source results
    print("\nConsumer Results:")
    for idx, row in net.res_sink.iterrows():
        name = net.sink.loc[idx, 'name']
        mass_flow = row['mdot_kg_per_s']
        print(f"  {name}: ṁ={mass_flow:.3f} kg/s")
    
    # Calculate total heat demand
    total_heat_kw = 0
    for idx, row in net.res_sink.iterrows():
        mass_flow = row['mdot_kg_per_s']
        heat_kw = mass_flow * 4180 * 30 / 1000  # Q = mdot * cp * dT
        total_heat_kw += heat_kw
    
    print(f"\nTotal Heat Demand: {total_heat_kw:.1f} kW")
    print(f"Total Mass Flow: {sum(net.res_sink['mdot_kg_per_s']):.2f} kg/s")

if __name__ == "__main__":
    # Create and run minimal Heinrich-Zille-Straße heat grid simulation
    net = create_minimal_heinrich_zille_network()
    
    if run_heat_grid_simulation(net):
        analyze_results(net)
        print("\n🎯 Heinrich-Zille-Straße heat grid simulation successful!")
        print("   Ready to scale up to full network!")
    else:
        print("Simulation failed - check network topology")
