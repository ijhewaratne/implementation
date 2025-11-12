# Heat Pump LV Grid Analysis - System Diagram

## 📐 **System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                     MV GRID (20 kV)                              │
│                      (Infinite Bus)                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   TRANSFORMER   │
                    │   0.63 MVA      │
                    │   20 kV → 0.4 kV│
                    │   6% impedance  │
                    └────────┬────────┘
                             │
                             ▼
        ┌─────────────────────────────────────┐
        │     LV DISTRIBUTION GRID            │
        │     0.4 kV (400V three-phase)       │
        │                                     │
        │  ┌─────┐    ┌─────┐    ┌─────┐    │
        │  │ Bus │───▶│ Bus │───▶│ Bus │    │
        │  │  A  │    │  B  │    │  C  │    │
        │  └──┬──┘    └──┬──┘    └──┬──┘    │
        │     │          │          │        │
        │     │          │          │        │
        │  ┌──▼──┐    ┌──▼──┐    ┌──▼──┐    │
        │  │ Bus │───▶│ Bus │───▶│ Bus │    │
        │  │  D  │    │  E  │    │  F  │    │
        │  └──┬──┘    └──┬──┘    └──┬──┘    │
        │     │          │          │        │
        │     ▼          ▼          ▼        │
        │  ┌────┐    ┌────┐    ┌────┐       │
        │  │Load│    │Load│    │ HP │       │
        │  │Base│    │ HP │    │ HP │       │
        │  └────┘    └────┘    └────┘       │
        └─────────────────────────────────────┘

  Each line: Cable 4×150mm², R=0.206Ω/km, Max=270A
```

---

## 🔄 **Load Calculation Flow**

```
Step 1: Base Load
┌─────────────────────────────────┐
│ gebaeude_lastphasenV2.json      │
│ Building ID → Load Profile      │
│ (e.g., 0.76 MW winter peak)     │
└───────────┬─────────────────────┘
            │
            ▼
┌─────────────────────────────────┐
│ Auto-detect units: MW or kW     │
│ Multiply: 0.76 MW × 1000 =      │
│           760 kW                │
└───────────┬─────────────────────┘
            │
            ▼
Step 2: Add Heat Pump Load
┌─────────────────────────────────┐
│ HP Thermal Power: 6.0 kW_th     │
│ COP: 2.8                         │
│ Calc: P_elec = 6.0 / 2.8        │
│       P_elec = 2.14 kW          │
└───────────┬─────────────────────┘
            │
            ▼
┌─────────────────────────────────┐
│ TOTAL LOAD:                     │
│ 760 kW (base) + 2.14 kW (HP)    │
│ = 762.14 kW                     │
└───────────┬─────────────────────┘
            │
            ▼
Step 3: Phase Distribution
┌─────────────────────────────────┐
│ 3-Phase (Balanced):             │
│ Phase A: 762.14 / 3 = 254.05 kW │
│ Phase B: 762.14 / 3 = 254.05 kW │
│ Phase C: 762.14 / 3 = 254.05 kW │
│                                 │
│ Single-Phase (Unbalanced):      │
│ Phase A: 762.14 kW              │
│ Phase B: 0 kW                   │
│ Phase C: 0 kW                   │
└───────────┬─────────────────────┘
            │
            ▼
Step 4: Attach to Grid
┌─────────────────────────────────┐
│ Find nearest LV bus to building │
│ Create asymmetric_load element  │
│ per phase (A, B, C)             │
└─────────────────────────────────┘
```

---

## ⚡ **Voltage Calculation**

```
Transformer Output: 400 V (1.0 pu)
                    ↓
                [Line 1]
                R = 0.206 Ω/km × 0.5 km
                I = 100 A
                ΔV = I × R × L
                   = 100 × 0.103
                   = 10.3 V
                    ↓
              Bus B: 389.7 V (0.974 pu)
                    ↓
                [Line 2]
                ΔV = 15 A × 0.206 × 0.3
                   = 0.93 V
                    ↓
              Bus C: 388.8 V (0.972 pu)

VOLTAGE VIOLATION IF: V < 0.90 pu (360 V)
```

---

## 🔍 **Current Flow Calculation**

```
Bus A (Load: 254 kW)
                    ↓
Line Current I = P / (√3 × V × cos φ)
              = 254,000 / (√3 × 400 × 1.0)
              = 367 A

MAX CURRENT: 270 A
LOADING: 367 / 270 × 100% = 136%

LINE OVERLOAD! ⚠️
```

---

## 📊 **Results Categories**

```
┌─────────────────────────────────────────────────┐
│ VOLTAGE VIOLATIONS                               │
├─────────────────────────────────────────────────┤
│ Critical: < 0.85 pu (340 V)  ████ Red           │
│ Warning:  0.85-0.90 pu        ███ Orange         │
│ Caution:  0.90-0.95 pu        ██ Yellow          │
│ Good:     > 0.95 pu           █ Green            │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ LINE LOADING VIOLATIONS                          │
├─────────────────────────────────────────────────┤
│ Critical: > 120%              ████ Red           │
│ Critical: 100-120%            ████ Red           │
│ Warning:  50-100%             ███ Orange         │
│ Caution:  25-50%              ██ Yellow          │
│ Good:     < 25%               █ Green            │
└─────────────────────────────────────────────────┘
```

---

## 🎯 **Key Factors Summary**

```
1. CABLE CHARACTERISTICS
   ├─ Cross-section: 150 mm² → 270 A max
   ├─ Resistance: 0.206 Ω/km → voltage drop
   ├─ Length: Longer = worse
   └─ Material: Copper vs aluminum

2. TRANSFORMER LIMITS
   ├─ Capacity: 630 kVA → ~910 A max
   ├─ Impedance: 6% → voltage drop
   └─ Load: High = voltage drop

3. HEAT PUMP IMPACT
   ├─ Power: 6 kW_th ÷ 2.8 COP = 2.14 kW_elec
   ├─ Time: Evening peak synced
   ├─ Location: Far buildings worse
   └─ Phase: Unbalanced = worse

4. GRID TOPOLOGY
   ├─ Distance: Far = low voltage
   ├─ Radial: Tree structure
   ├─ Meshed: Alternative paths
   └─ Taps: Connection points

5. OPERATING CONDITIONS
   ├─ Temperature: Winter worst
   ├─ Daily pattern: Evening peak
   ├─ Season: Heating season
   └─ Simultaneity: All on together
```

---

## 🔧 **Interaction of Factors**

```
LOW VOLTAGE CAN BE CAUSED BY:
┌────────────────────────────────────────┐
│ Factor Combination                     │
├────────────────────────────────────────┤
│ 1. Long distance from transformer      │
│    + High resistance cable             │
│    + High current                      │
│    = Significant voltage drop          │
├────────────────────────────────────────┤
│ 2. Small transformer capacity          │
│    + High total load                   │
│    + 6% impedance                      │
│    = Transformer voltage drop          │
├────────────────────────────────────────┤
│ 3. Single-phase HP connection          │
│    + Concentrated on one phase         │
│    + No phase balancing                │
│    = Phase imbalance                   │
├────────────────────────────────────────┤
│ 4. Simultaneous operation              │
│    + All HPs on at once                │
│    + Evening peak demand               │
│    = Maximum current (worst case)      │
└────────────────────────────────────────┘
```

---

## 📈 **Typical Values**

```
BASE LOAD (Residential):
├─ Lighting: 0.1-0.5 kW
├─ Appliances: 0.5-2 kW
├─ HVAC: 1-5 kW
└─ Total: 2-8 kW per household

HEAT PUMP LOAD:
├─ Thermal power: 6-10 kW
├─ COP (winter): 2.5-3.0
├─ Electric power: 2-4 kW
└─ Additional load: 25-50% increase

CABLE CAPACITY:
├─ 4×150 mm²: 270 A
├─ 4×240 mm²: 400 A
├─ 4×300 mm²: 500 A
└─ Typical residential: 200-300 A

VOLTAGE TARGETS:
├─ Nominal: 400 V
├─ Acceptable: 380-420 V (95-105%)
├─ Warning: 360-380 V (90-95%)
└─ Critical: < 360 V (< 90%)
```     

---

## 🎯 **Why This Analysis Matters**

```
QUESTION: Can we install 6 kW heat pumps in all houses?

ANALYSIS CONSIDERS:
1. Existing load from daily use
2. Additional HP load (2-4 kW)
3. Distance from transformer
4. Cable capacity limits
5. Voltage drop physics
6. Phase balance/imbalance
7. Simultaneity of operation
8. Worst-case conditions (winter)

ANSWER:
- Houses near transformer: ✅ Usually OK
- Houses far away: ⚠️ May need upgrade
- Large clusters: ⚠️ May need upgrade
- Single-phase: ⚠️ Worse than 3-phase
```

---

## 📝 **Summary**

The heat pump LV analysis is a **physics-based simulation** that:

1. ✅ Models the **real electrical network** (cables, transformer, buses)
2. ✅ Adds **heat pump electric loads** to existing demand
3. ✅ Calculates **voltage drops** from current flow × resistance × distance
4. ✅ Checks **constraints** (voltage limits, line capacity)
5. ✅ Identifies **problematic areas** that need grid reinforcement
6. ✅ Provides **geographic visualization** for planning

**Main insight**: Electric heat pumps add significant loads that can violate voltage and current limits, especially in older grids with smaller cables and long distances from transformers.

