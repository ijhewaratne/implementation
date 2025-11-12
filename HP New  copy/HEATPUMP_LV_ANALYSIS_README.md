# Heat Pump LV Grid Analysis - How It Works

## Overview
This analysis evaluates the impact of heat pump electrification on low-voltage (LV) distribution grids using **3-phase power flow simulation** with `pandapower`.

---

## 🔧 **KEY FACTORS CONSIDERED**

### **1. Network Topology**
```python
# From build_lv_net() function (lines 234-292)
```
- **LV Grid Structure**: Extracted from OpenStreetMap-derived node/way data
- **Bus Network**: Each LV node becomes a bus (busbar/connection point)
- **Line Segments**: Power lines split between consecutive nodes
- **Voltage Level**: 0.4 kV (LV standard in Europe: 400V three-phase)
- **Geographic Mapping**: Each bus has lat/lon coordinates for spatial analysis

**Key Code:**
```234:239:street_hp_lv_sim.py
def build_lv_net(id_to_node: Dict[int,dict], ways: List[dict], buildings: List[dict], vn_kv=0.4):
    net = pp.create_empty_network()
    # Create buses with geodata
    nodeid_to_bus = {}
    for nid, nd in id_to_node.items():
        nodeid_to_bus[nid] = pp.create_bus(net, vn_kv=vn_kv, geodata=(nd["lon"], nd["lat"]), name=f"n{nid}")
```

---

### **2. Cable Characteristics**
```python
# Generic LV cable parameters (line 286-290)
```
**Cable Type**: Copper 4×150 mm² (4-core, 150mm² each phase + neutral)
- **Resistance**: r_ohm_per_km = 0.206 Ω/km (line resistance)
- **Reactance**: x_ohm_per_km = 0.080 Ω/km (inductive reactance)
- **Capacitance**: c_nf_per_km = 210 nF/km (line capacitance)
- **Maximum Current**: max_i_ka = 0.27 kA (270 A per phase)
- **Zero-Sequence**: Same values for earth fault calculations

**Why this matters**: 
- Lower resistance → less voltage drop
- Higher ampacity → can handle more load
- But **longer lines → more voltage drop** (V = I × R × L)

```286:291:street_hp_lv_sim.py
            # Generic LV cable (Cu 4x150 mm²). Replace with your std-types for accuracy.
            pp.create_line_from_parameters(
                net, nodeid_to_bus[u], nodeid_to_bus[v], length_km=seg_len_km,
                r_ohm_per_km=0.206, x_ohm_per_km=0.080, c_nf_per_km=210, max_i_ka=0.27,
                r0_ohm_per_km=0.206, x0_ohm_per_km=0.080, c0_nf_per_km=210,
                name=f"w{w['id']}_{u}-{v}"
```

---

### **3. Transformer Model**
```python
# MV/LV Transformer (lines 264-271)
```
**Transformer Parameters:**
- **Rating**: 0.63 MVA (630 kVA)
- **Voltages**: 20 kV (HV) → 0.4 kV (LV)
- **Short-circuit voltage**: 6% (vk_percent)
- **Load losses**: 0.5% (vkr_percent)
- **No-load losses**: 1 kW
- **Vector Group**: Dyn (delta on HV, star with grounded neutral on LV)

**Why this matters**:
- **630 kVA limit**: Can supply max ~910 A at 0.4 kV per phase
- **6% impedance**: Causes voltage drop under load
- **Dyn connection**: Provides grounding for earth faults

```264:271:street_hp_lv_sim.py
    pp.create_transformer_from_parameters(
        net, hv_bus=b_mv, lv_bus=b_lv_ref,
        sn_mva=0.63, vn_hv_kv=20.0, vn_lv_kv=0.4,
        vk_percent=6.0, vkr_percent=0.5,
        pfe_kw=1.0, i0_percent=0.1, 
        vector_group="Dyn",  # Supported by pandapower 3-phase (Dyn5 not supported)
        vk0_percent=6.0, vkr0_percent=0.5, mag0_percent=100, mag0_rx=0, si0_hv_partial=0.9, name="T1"
    )
```

---

### **4. Base Load Profile**
```python
# Load scenarios from gebaeude_lastphasenV2.json (lines 357-374)
```
**Load Data Structure**:
- Per-building base electrical loads
- Time-series scenarios (e.g., winter peak demand)
- Auto-detection of units (kW or MW)

**Current Scenario**: `winter_werktag_abendspitze` (winter weekday evening peak)

```361:374:street_hp_lv_sim.py
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

### **5. Heat Pump Modeling**
```python
# HP load calculation (lines 383-408)
```

**Key Parameters:**

#### **A. Thermal Power**
- `hp_add_kw_th`: 6.0 kW thermal per building
- Typical residential heat pump size

#### **B. Coefficient of Performance (COP)**
- `hp_cop`: 2.8 (worst-case winter COP)
- **Electric power = Thermal power / COP**
- Example: 6 kW thermal ÷ 2.8 = 2.14 kW electric

#### **C. Phase Distribution**
- `hp_three_phase`: True (balanced 3-phase) or False (single-phase)
- **3-phase**: Load split equally across A, B, C phases
- **Single-phase**: All load on phase A (worst-case imbalance)

```383:408:street_hp_lv_sim.py
    # Attach loads (+ HPs)
    num_attached = 0
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
        num_attached += 1
```

---

### **6. Power Flow Calculation**
```python
# 3-phase power flow (line 419)
```

**Solver**: pandapower's `runpp_3ph()`
- **Unbalanced load flow**: Handles asymmetric phase loads
- **Newton-Raphson**: Iterative solution for voltage/current
- **3-phase modeling**: Separate voltage/current per phase

**What it calculates**:
1. **Voltage magnitude** at each bus (per phase: A, B, C)
2. **Line currents** per phase
3. **Power flows** through each line
4. **Transformer loading**

```419:419:street_hp_lv_sim.py
    pp3.runpp_3ph(net, init="auto")
```

---

### **7. Constraint Checks**

#### **A. Voltage Limits**
- **Standard**: 230V ±6% = 216V to 244V
- **Per-unit (pu)**: 0.94 pu to 1.06 pu
- **Default threshold**: 0.90 pu (207V) for violations

```439:450:street_hp_lv_sim.py
            res = net.res_bus_3ph.loc[b_idx]
            vmin = min(res["vm_a_pu"], res["vm_b_pu"], res["vm_c_pu"])
            feats.append({
                "type":"Feature",
                "geometry":{"type":"Point","coordinates":[float(lon), float(lat)]},
                "properties":{
                    "bus": int(b_idx), "name": bus["name"],
                    "vm_a_pu": float(res["vm_a_pu"]),
                    "vm_b_pu": float(res["vm_b_pu"]),
                    "vm_c_pu": float(res["vm_c_pu"]),
                    "v_min_pu": float(vmin)
                }
```

#### **B. Line Loading**
- **Maximum current**: 270 A (from max_i_ka = 0.27)
- **Loading percentage**: 100 × actual_current / max_current
- **Default threshold**: 100% for violations

```479:491:street_hp_lv_sim.py
            res = net.res_line_3ph.loc[li]
            i_max = float(line["max_i_ka"]) if "max_i_ka" in line else 0.0
            i_a = float(res["i_a_ka"]); i_b = float(res["i_b_ka"]); i_c = float(res["i_c_ka"])
            loading_pct = 100.0*max(i_a, i_b, i_c)/i_max if i_max>0 else 0.0
            feats.append({
                "type":"Feature",
                "geometry":{"type":"LineString","coordinates":[[float(x1), float(y1)], [float(x2), float(y2)]]},
                "properties":{
                    "line": int(li), "name": str(line.get("name","")), "length_km": float(line["length_km"]),
                    "i_a_ka": i_a, "i_b_ka": i_b, "i_c_ka": i_c, "max_i_ka": i_max,
                    "loading_pct": float(loading_pct)
                }
```

---

## 📊 **WHAT THE ANALYSIS OUTPUTS**

### **1. Voltage Violations**
- **Red buses**: Voltage < 0.90 pu
- **Orange buses**: Voltage 0.90-0.95 pu
- **Yellow buses**: Voltage 0.95-1.00 pu
- **Green buses**: Voltage > 1.00 pu

### **2. Line Loading**
- **Red lines**: Loading > 100%
- **Orange lines**: Loading 50-100%
- **Yellow lines**: Loading 25-50%
- **Green lines**: Loading < 25%

### **3. Geographic Visualization**
- Interactive Folium map
- Color-coded by severity
- Tooltips with detailed values

### **4. Violations CSV**
- Critical vs. warning
- Specific values and limits
- Element identification

---

## 🧮 **PHYSICS FORMULAS BEHIND IT**

### **Voltage Drop**
```
ΔV = I × (R × cos φ + X × sin φ) × L
```
Where:
- I = current (A)
- R = line resistance (Ω/km)
- X = line reactance (Ω/km)
- L = line length (km)
- φ = power factor angle

### **Line Loading**
```
Loading % = (I_actual / I_max) × 100
```

### **Transformer Loading**
```
Loading % = (S_actual / S_rated) × 100
```

### **Heat Pump Electric Power**
```
P_elec = P_thermal / COP
```

---

## ⚙️ **CONFIGURATION OPTIONS**

```python
main(
    selected_scenario="winter_werktag_abendspitze",  # Load scenario
    selected_street_name=None,                       # Focus area
    load_unit="MW",                                  # Load units
    hp_add_kw_th=6.0,                                # HP thermal power (kW)
    hp_cop=2.8,                                      # HP COP
    hp_three_phase=True,                             # Balanced vs unbalanced
    limit_to_bbox=None,                              # Geographic bounds
    v_min_limit_pu=0.90,                             # Voltage threshold
    line_loading_limit_pct=100.0                     # Line threshold
)
```

---

## 🎯 **KEY INSIGHTS FROM YOUR RESULTS**

From `violations.csv`:
- **483 violations** detected
- Mostly **undervoltage** (< 0.90 pu)
- Some voltages down to **0.64 pu** (147V)

**Why this happens**:
1. **Large HP loads**: 6 kW thermal ≈ 2.14 kW electric per building
2. **Long LV lines**: High resistance (0.206 Ω/km)
3. **Distance from transformer**: Far buses see biggest voltage drop
4. **Single-phase imbalance**: Creates unequal loading

---

## 🔧 **MITIGATION STRATEGIES**

### **1. Upgrade Cables**
- Larger cross-section → lower resistance
- Example: 4×240 mm² vs 4×150 mm²

### **2. Voltage Regulators**
- On-load tap changers (OLTC)
- Local voltage boost

### **3. Phase Balancing**
- Redistribute single-phase loads
- Rotate HP connections

### **4. Upgrade Transformer**
- Higher capacity (e.g., 1 MVA)
- Lower impedance

### **5. Distributed Generation**
- Solar PV offset
- Battery storage

### **6. Smart Control**
- Time-shifted HP operation
- Load shedding

---

## 📝 **SUMMARY**

The heat pump LV analysis considers:
1. ✅ **Grid topology** (cables, buses, transformer)
2. ✅ **Cable parameters** (R, X, C, ampacity)
3. ✅ **Base loads** (existing electricity demand)
4. ✅ **HP loads** (thermal power ÷ COP)
5. ✅ **Phase distribution** (balanced vs. unbalanced)
6. ✅ **Power flow** (voltage, current, losses)
7. ✅ **Constraints** (voltage limits, line capacity)
8. ✅ **Geographic mapping** (spatial visualization)

**Main constraint**: Voltage drop over distance limits how many heat pumps can be added before grid reinforcement is needed.

