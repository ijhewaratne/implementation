# Entities & Components Implemented

## Overview
This is **NOT an agent-based modeling (ABM) system**. It's a **physics-based simulation** using `pandapower` and `pandapipes`. There are **no autonomous agents making decisions**.

However, the system **models several physical entities/components** that interact through physics equations.

---

## 🔥 **DISTRICT HEATING GRID ENTITIES**

### **1. Power Plant (CHP Station)**
**Location**: Cottbus CHP power station (51.7602, 14.37)  
**Function**: Heat source and pressure boundary condition

**Implementation**:
- **Supply ext_grid**: Supplies hot water (85°C, 3.0 bar)
- **Return ext_grid**: Receives cooled water (55°C, 2.5 bar)
- **Pressure differential**: 0.5 bar drives circulation

**Code Reference**:
```528:535:dh_build_and_map.py
pps.create_ext_grid(net, junction=jid2idx_S[PLANT_JUNCTION_ID], 
                   p_bar=SUPPLY_PLANT_PRESSURE, t_k=SUPPLY_TEMP_C+273.15, 
                   name="Plant_Supply")

pps.create_ext_grid(net, junction=jid2idx_R[PLANT_JUNCTION_ID], 
                   p_bar=RETURN_PLANT_PRESSURE, t_k=RETURN_TEMP_C+273.15, 
                   name="Plant_Return")
```

---

### **2. Junctions (Network Nodes)**
**Function**: Connection points in the network

**Types**:
- **Supply Junctions** (`..._S`): Hot water distribution nodes
- **Return Junctions** (`..._R`): Cooled water collection nodes

**Properties**:
- Pressure (bar)
- Temperature (Kelvin)
- Geographic coordinates (lat/lon)

**Code Reference**:
```476:481:dh_build_and_map.py
for j in sampled_junctions:
    jid2idx_S[j["id"]] = pps.create_junction(net, pn_bar=3.0, tfluid_k=SUPPLY_TEMP_C + 273.15,
                                            name=f'{j["id"]}_S')
    jid2idx_R[j["id"]] = pps.create_junction(net, pn_bar=2.6, tfluid_k=RETURN_TEMP_C + 273.15,
                                            name=f'{j["id"]}_R')
```

---

### **3. Pipes**
**Function**: Transport water between junctions

**Properties**:
- **Length** (km): Calculated from coordinates
- **Diameter** (m): Pipe cross-section
- **Roughness** (mm): Inner surface roughness
- **Heat loss coefficient** (W/m²·K): Ambient heat exchange

**Types**:
- **Supply pipes**: Carry hot water from plant
- **Return pipes**: Carry cooled water to plant

**Code Reference**:
```556:575:dh_build_and_map.py
pps.create_pipe_from_parameters(net, jid2idx_S[p["from"]], jid2idx_S[p["to"]],
                               length_km=L_km, diameter_m=d_m, k_mm=k_mm,
                               alpha_w_per_m2k=alpha, name=p["id"])
```

---

### **4. Buildings**
**Function**: Physical structures with heat demand

**Properties**:
- **Building ID**: Unique identifier
- **Coordinates**: Latitude/longitude
- **Address**: Street name (for filtering)
- **Heat Demand**: Annual heating requirement (kWh/a) → Peak (kW)

**Code Reference**:
```408:416:dh_build_and_map.py
for b in brec:
    q = bid2q.get(b["id"])
    if not q: 
        continue
    j,_ = nearest_junction(junctions, b["lat"], b["lon"])
    mdot = mdot_from_q(q,dT,cp)
    consumers.append({"building_id":b["id"],"junction_id":j["id"],"q_kw":q,"mdot_kg_s":mdot})
```

---

### **5. Consumers (Heat Exchangers)**
**Function**: Extract heat from district heating network

**Implementation**: **Sinks + Sources** (instead of heat exchangers for convergence)

- **Sink** (supply junction): Removes hot water at calculated mass flow
- **Source** (return junction): Injects cooled water back

**Mass Flow Calculation**:
```
mdot = Q_heat / (cp × ΔT)
where:
  Q_heat = heat demand (W)
  cp = specific heat capacity (4180 J/kg·K)
  ΔT = temperature difference (30 K)
```

**Code Reference**:
```641:649:dh_build_and_map.py
pps.create_sink(net, jid2idx_S[c["junction_id"]], 
               mdot_kg_per_s=mdot, 
               name=f"{c['building_id']}_Sink")

pps.create_source(net, jid2idx_R[c["junction_id"]], 
                 mdot_kg_per_s=mdot, 
                 name=f"{c['building_id']}_Source")
```

---

## ⚡ **LOW-VOLTAGE (LV) GRID ENTITIES**

### **1. MV Grid (Medium Voltage)**
**Function**: External power source (infinite bus)

**Properties**:
- **Voltage**: 20 kV
- **Short-circuit capacity**: 1000 MVA
- **Impedance ratio**: R/X = 0.1

**Code Reference**:
```244:249:street_hp_lv_sim.py
b_mv = pp.create_bus(net, vn_kv=20.0, name="MV")
pp.create_ext_grid(net, bus=b_mv, vm_pu=1.02, name="MV Slack", 
                  s_sc_max_mva=1000.0, s_sc_min_mva=1000.0, 
                  rx_max=0.1, rx_min=0.1,
```

---

### **2. MV/LV Transformer**
**Function**: Steps down voltage from 20 kV to 0.4 kV

**Properties**:
- **Rating**: 0.63 MVA (630 kVA)
- **Voltages**: 20 kV → 0.4 kV
- **Impedance**: 6% short-circuit voltage
- **Vector Group**: Dyn (delta-star with grounded neutral)

**Code Reference**:
```264:271:street_hp_lv_sim.py
pp.create_transformer_from_parameters(
    net, hv_bus=b_mv, lv_bus=b_lv_ref,
    sn_mva=0.63, vn_hv_kv=20.0, vn_lv_kv=0.4,
    vk_percent=6.0, vkr_percent=0.5,
    pfe_kw=1.0, i0_percent=0.1, 
    vector_group="Dyn",
```

---

### **3. LV Buses (Busbars)**
**Function**: Connection points in LV distribution network

**Properties**:
- **Voltage**: 0.4 kV (400V three-phase)
- **Geographic coordinates**: For spatial mapping
- **Per-phase voltages**: Separate A, B, C phase voltages

**Code Reference**:
```238:239:street_hp_lv_sim.py
for nid, nd in id_to_node.items():
    nodeid_to_bus[nid] = pp.create_bus(net, vn_kv=vn_kv, geodata=(nd["lon"], nd["lat"]), name=f"n{nid}")
```

---

### **4. LV Lines/Cables**
**Function**: Transport electricity between buses

**Properties**:
- **Type**: Copper 4×150 mm²
- **Resistance**: 0.206 Ω/km
- **Reactance**: 0.080 Ω/km
- **Capacitance**: 210 nF/km
- **Maximum Current**: 270 A per phase
- **Length**: Calculated from coordinates

**Code Reference**:
```286:291:street_hp_lv_sim.py
pp.create_line_from_parameters(
    net, nodeid_to_bus[u], nodeid_to_bus[v], length_km=seg_len_km,
    r_ohm_per_km=0.206, x_ohm_per_km=0.080, c_nf_per_km=210, max_i_ka=0.27,
    r0_ohm_per_km=0.206, x0_ohm_per_km=0.080, c0_nf_per_km=210,
```

---

### **5. Buildings (LV Grid)**
**Function**: Physical structures with electrical loads

**Properties**:
- **Building ID**: Unique identifier
- **Coordinates**: For mapping to nearest LV bus
- **Base Load**: Existing electrical consumption (kW or MW)
- **Heat Pump Load**: Additional load from HP electrification

**Code Reference**:
```376:381:street_hp_lv_sim.py
building_to_bus = {}
for b in buildings:
    nid, _ = nearest_node_id(id_to_node, b["lat"], b["lon"])
    if nid is not None and nid in nodeid_to_bus:
        building_to_bus[b["id"]] = nodeid_to_bus[nid]
```

---

### **6. Base Electrical Loads**
**Function**: Existing electricity consumption (before HPs)

**Properties**:
- **Load Profile**: Time-series data per scenario
- **Scenario**: e.g., `winter_werktag_abendspitze` (winter weekday evening peak)
- **Power Factor**: Typically 0.95
- **Units**: Auto-detected (kW or MW)

**Code Reference**:
```357:374:street_hp_lv_sim.py
with DATA_LOADS.open("r", encoding="utf-8") as f:
    load_scen = json.load(f)

# Unit multiplier with auto-detection
if load_unit is None:  # optional: auto
    import statistics
    # sample some values across buildings
    vals = []
    for i, prof in zip(range(500), load_scen.values()):
        v = float(prof.get(selected_scenario, 0.0))
        vals.append(abs(v))
    med = statistics.median(vals) if vals else 0.0
    # Heuristic: tiny medians likely MW (0.0x); larger ~1–10 are kW
    load_unit = "MW" if med < 0.1 else "kW"
    print(f"Auto-detected load_unit='{load_unit}' (median={med:.3f})")

mult = 1000.0 if load_unit.lower() == "mw" else 1.0
```

---

### **7. Heat Pumps**
**Function**: Electric heating devices (additional load on LV grid)

**Properties**:
- **Thermal Power**: 6.0 kW thermal (typical residential)
- **COP**: 2.8 (coefficient of performance, winter worst-case)
- **Electric Power**: Calculated as `P_elec = P_thermal / COP`
  - Example: 6.0 kW / 2.8 = 2.14 kW electric

**Phase Distribution**:
- **3-phase (balanced)**: Load split equally across A, B, C phases
- **Single-phase (unbalanced)**: All load on phase A (worst-case)

**Code Reference**:
```383:408:street_hp_lv_sim.py
for bid, prof in load_scen.items():
    if bid not in building_to_bus:
        continue
    p_kw = float(prof.get(selected_scenario, 0.0)) * mult
    hp_kw_el = (float(hp_add_kw_th) / float(hp_cop)) if hp_add_kw_th and hp_cop > 0 else 0.0
    p_total_kw = max(p_kw + hp_kw_el, 0.0)

    bus = building_to_bus[bid]
    if hp_three_phase:
        # split evenly among phases (3-phase HP)
        p_phase_mw = (p_total_kw / 3.0) / 1000.0
        pp3.create_asymmetric_load(
            net, bus=bus,
            p_a_mw=p_phase_mw, p_b_mw=p_phase_mw, p_c_mw=p_phase_mw,
            q_a_mvar=0.0, q_b_mvar=0.0, q_c_mvar=0.0, name=f"{bid}"
        )
    else:
        # single-phase worst-case on phase A
        pp3.create_asymmetric_load(
            net, bus=bus,
            p_a_mw=p_total_kw / 1000.0, p_b_mw=0.0, p_c_mw=0.0,
            q_a_mvar=0.0, q_b_mvar=0.0, q_c_mvar=0.0, name=f"{bid}"
        )
```

---

## 📊 **ENTITY INTERACTIONS**

### **District Heating Flow**
```
Plant → Supply Pipes → Junctions → Sinks (Buildings) → Sources → Return Pipes → Plant
```

### **LV Grid Flow**
```
MV Grid → Transformer → LV Buses → Lines → Buildings (Base Load + HP Load)
```

---

## 🔍 **WHAT'S NOT IMPLEMENTED (No Agents)**

❌ **No autonomous agents** making decisions  
❌ **No behavior models** (e.g., occupant behavior, thermostat settings)  
❌ **No optimization agents** (e.g., demand response, price signals)  
❌ **No learning/adaptation** (e.g., reinforcement learning agents)  
❌ **No market mechanisms** (e.g., trading, bidding)

---

## ✅ **WHAT IS IMPLEMENTED (Physics-Based Entities)**

✅ **Physical components** (pipes, cables, transformers, junctions)  
✅ **Load profiles** (time-series demand data)  
✅ **Power flow calculations** (voltage, current, losses)  
✅ **Hydraulic/thermal calculations** (pressure, temperature, flow)  
✅ **Geographic mapping** (spatial representation)  
✅ **Constraint checking** (voltage limits, line loading)

---

## 📝 **Summary**

The system models **physical infrastructure components** and **load entities**, but **NO autonomous agents**. All interactions are governed by **physics equations** (Ohm's law, Kirchhoff's laws, fluid dynamics, heat transfer), not agent decision-making.

**Entities = Components**, not agents in the ABM sense.
