#!/usr/bin/env python3
"""
Simple Heat Grid Simulation for Heinrich-Zille-Straße
A minimal working example to test pandapipes heat grid simulation
"""

import pandapipes as pps
import numpy as np

def create_simple_heat_grid():
    """Create a simple linear heat grid network"""
    
    # Create empty network
    net = pps.create_empty_network()
    pps.create_fluid_from_lib(net, "water")
    
    # Network parameters
    SUPPLY_TEMP_C = 85.0
    RETURN_TEMP_C = 55.0
    SUPPLY_PRESSURE = 3.0  # bar
    RETURN_PRESSURE = 2.5  # bar
    
    print("Creating simple linear heat grid...")
    
    # Create junctions: Plant -> Street -> Consumers
    # Supply side
    plant_supply = pps.create_junction(net, pn_bar=SUPPLY_PRESSURE, tfluid_k=SUPPLY_TEMP_C+273.15, name="Plant_Supply")
    street_supply = pps.create_junction(net, pn_bar=2.8, tfluid_k=SUPPLY_TEMP_C+273.15, name="Street_Supply")
    consumer1_supply = pps.create_junction(net, pn_bar=2.7, tfluid_k=SUPPLY_TEMP_C+273.15, name="Consumer1_Supply")
    consumer2_supply = pps.create_junction(net, pn_bar=2.6, tfluid_k=SUPPLY_TEMP_C+273.15, name="Consumer2_Supply")
    
    # Return side
    plant_return = pps.create_junction(net, pn_bar=RETURN_PRESSURE, tfluid_k=RETURN_TEMP_C+273.15, name="Plant_Return")
    street_return = pps.create_junction(net, pn_bar=2.6, tfluid_k=RETURN_TEMP_C+273.15, name="Street_Return")
    consumer1_return = pps.create_junction(net, pn_bar=2.7, tfluid_k=RETURN_TEMP_C+273.15, name="Consumer1_Return")
    consumer2_return = pps.create_junction(net, pn_bar=2.8, tfluid_k=RETURN_TEMP_C+273.15, name="Consumer2_Return")
    
    # Create pipes: Supply circuit
    pps.create_pipe_from_parameters(net, plant_supply, street_supply, 
                                   length_km=0.5, diameter_m=0.2, k_mm=0.1, 
                                   alpha_w_per_m2k=5.0, name="Main_Supply")
    pps.create_pipe_from_parameters(net, street_supply, consumer1_supply, 
                                   length_km=0.1, diameter_m=0.1, k_mm=0.1, 
                                   alpha_w_per_m2k=5.0, name="Branch1_Supply")
    pps.create_pipe_from_parameters(net, consumer1_supply, consumer2_supply, 
                                   length_km=0.1, diameter_m=0.1, k_mm=0.1, 
                                   alpha_w_per_m2k=5.0, name="Branch2_Supply")
    
    # Create pipes: Return circuit
    pps.create_pipe_from_parameters(net, consumer2_return, consumer1_return, 
                                   length_km=0.1, diameter_m=0.1, k_mm=0.1, 
                                   alpha_w_per_m2k=5.0, name="Branch2_Return")
    pps.create_pipe_from_parameters(net, consumer1_return, street_return, 
                                   length_km=0.1, diameter_m=0.1, k_mm=0.1, 
                                   alpha_w_per_m2k=5.0, name="Branch1_Return")
    pps.create_pipe_from_parameters(net, street_return, plant_return, 
                                   length_km=0.5, diameter_m=0.2, k_mm=0.1, 
                                   alpha_w_per_m2k=5.0, name="Main_Return")
    
    # Create sinks and sources (consumers) - more stable than heat exchangers
    # Calculate mass flow from heat demand: mdot = Q / (cp * dT)
    cp = 4180  # J/kg/K
    dT = SUPPLY_TEMP_C - RETURN_TEMP_C  # 30 K
    
    mdot1 = 50000 / (cp * dT)  # kg/s for 50 kW
    mdot2 = 30000 / (cp * dT)  # kg/s for 30 kW
    
    pps.create_sink(net, consumer1_supply, mdot_kg_per_s=mdot1, name="Consumer1_Sink")
    pps.create_source(net, consumer1_return, mdot_kg_per_s=mdot1, name="Consumer1_Source")
    pps.create_sink(net, consumer2_supply, mdot_kg_per_s=mdot2, name="Consumer2_Sink")
    pps.create_source(net, consumer2_return, mdot_kg_per_s=mdot2, name="Consumer2_Source")
    
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
    
    print("\nRunning heat grid simulation...")
    
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
    
    print("\n=== SIMULATION RESULTS ===")
    
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
    print("\nSink Results:")
    for idx, row in net.res_sink.iterrows():
        name = net.sink.loc[idx, 'name']
        mass_flow = row['mdot_kg_per_s']
        print(f"  {name}: ṁ={mass_flow:.3f} kg/s")
    
    print("\nSource Results:")
    for idx, row in net.res_source.iterrows():
        name = net.source.loc[idx, 'name']
        mass_flow = row['mdot_kg_per_s']
        print(f"  {name}: ṁ={mass_flow:.3f} kg/s")

if __name__ == "__main__":
    # Create and run simple heat grid simulation
    net = create_simple_heat_grid()
    
    if run_heat_grid_simulation(net):
        analyze_results(net)
    else:
        print("Simulation failed - check network topology")
