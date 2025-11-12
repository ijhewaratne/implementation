# 🔧 Fix: Interactive Maps Not Working in HTML Dashboards

**Issue:** Interactive maps are not embedded in HTML dashboards  
**Root Cause:** No interactive maps have been generated yet  
**Solution:** Generate interactive maps first, then create HTML dashboards

---

## 🔍 Problem Analysis

### **What's Happening:**
1. HTML dashboards are generated successfully ✅
2. HTML dashboards look for interactive maps to embed 🔍
3. **No interactive maps exist yet** ❌
4. HTML dashboards show fallback message instead of map ⚠️

### **Current State:**
```
results_test/visualizations/
├── html_dashboards/            ✅ 4 HTML dashboards exist
│   ├── Test_DH_Dashboard_dh_html_dashboard.html
│   └── ...
└── interactive/                ❌ NO MAPS (directory empty/missing)
    └── (no files)
```

---

## 🛠️ **SOLUTION: 2-Step Process**

### **Step 1: Generate Interactive Maps First**

The HTML dashboard tool automatically looks for interactive maps, but you must generate them first using `create_interactive_map()`.

**Through Agent System:**
```bash
# First, generate the interactive map
"create interactive map for Parkstrasse_DH"
→ Generates: results_test/visualizations/interactive/Parkstrasse_DH_dh_interactive.html

# Then, create the HTML dashboard
"create HTML dashboard for Parkstrasse_DH"
→ Embeds the map automatically!
```

**Direct Python:**
```python
from src.visualization import InteractiveMapGenerator
from src.dashboards import HTMLDashboardGenerator

# Step 1: Generate interactive map
map_gen = InteractiveMapGenerator()
map_file = map_gen.create_dh_interactive_map(
    scenario_name="Parkstrasse_DH",
    buildings_gdf=buildings_gdf,
    kpi=kpi_data
)

# Step 2: Generate HTML dashboard (will embed the map)
dashboard_gen = HTMLDashboardGenerator()
html_file = dashboard_gen.create_dh_html_dashboard(
    kpi=kpi_data,
    scenario_name="Parkstrasse_DH",
    metadata={'street_name': 'Parkstrasse'},
    map_file=map_file  # Pass the map file path
)
```

---

## 🎯 **Quick Fix for Existing Dashboards**

If you already have HTML dashboards but no embedded maps:

### **Option 1: Regenerate with Maps** (Recommended)

```bash
# 1. Generate interactive map
"create interactive map for Parkstrasse_DH"

# 2. Regenerate HTML dashboard
"create HTML dashboard for Parkstrasse_DH"
```

The HTML dashboard tool will automatically:
- Search for interactive maps in `results_test/visualizations/interactive/`
- Find the map matching the scenario name
- Embed it via iframe

### **Option 2: Manual Path Specification**

If maps are in a different location, specify the path:

```python
from src.dashboards import HTMLDashboardGenerator

dashboard_gen = HTMLDashboardGenerator()
html_file = dashboard_gen.create_dh_html_dashboard(
    kpi=kpi_data,
    scenario_name="Parkstrasse_DH",
    metadata={'street_name': 'Parkstrasse'},
    map_file="/path/to/your/interactive_map.html"  # Explicit path
)
```

---

## 📝 **Understanding the Behavior**

### **Current Logic in `html_dashboard.py`:**

```python
def _create_map_embed_section(self, map_file: Optional[str], title: str) -> str:
    """Create HTML section for embedded map."""
    
    if not map_file or not Path(map_file).exists():
        # FALLBACK MESSAGE (what you're seeing now)
        return f"""
        <div class="section">
            <h3 class="section-title">🗺️ {title}</h3>
            <div class="info-box">
                <p>⚠️ Interactive map not available. 
                   Generate map first using <code>create_interactive_map()</code></p>
            </div>
        </div>
"""
    
    # If map exists, embed it via iframe
    return f"""
        <div class="section">
            <h3 class="section-title">🗺️ {title}</h3>
            <div class="map-container">
                <iframe src="{map_src}" width="100%" height="600px"></iframe>
            </div>
        </div>
"""
```

---

## ✅ **Recommended Workflow**

### **Complete Visualization Workflow:**

```bash
# 1. Run simulation
"analyze district heating for Parkstrasse"
→ Generates simulation results

# 2. Create interactive map
"create interactive map for Parkstrasse_DH"
→ Generates: Parkstrasse_DH_dh_interactive.html

# 3. Create summary dashboard (optional)
"create dashboard for Parkstrasse_DH"
→ Generates: Parkstrasse_DH_dh_summary_dashboard.png

# 4. Create HTML dashboard (embeds map + charts)
"create HTML dashboard for Parkstrasse_DH"
→ Generates comprehensive HTML with embedded map and PNG dashboard as chart
```

**Result:**
- ✅ Interactive map (standalone)
- ✅ PNG dashboard (high-res)
- ✅ HTML dashboard with embedded map + chart

---

## 🔧 **Alternative: Auto-Generate Maps**

### **Enable Auto-Generation in Config:**

Edit `config/feature_flags.yaml`:

```yaml
features:
  # ... other flags
  auto_generate_visualizations: true  # Enable auto-generation
  enable_html_dashboards: true
  auto_generate_html_dashboards: true  # Auto-generate HTML too
```

**With this enabled:**
```bash
# Just run the simulation
"analyze district heating for Parkstrasse"

# Everything is generated automatically:
# ✅ Simulation results
# ✅ Interactive map (auto)
# ✅ PNG dashboard (auto)
# ✅ HTML dashboard with embedded map (auto)
```

---

## 🎨 **Enhanced HTML Dashboard Tool**

### **Option: Make it More Robust**

If you want the HTML dashboard to automatically generate missing maps, we can enhance it:

```python
# Enhanced version of create_html_dashboard in energy_tools.py

@tool
def create_html_dashboard(scenario_name: str, dashboard_type: str = "auto", 
                         auto_generate_map: bool = True) -> str:
    """
    Creates comprehensive HTML dashboard.
    
    Args:
        scenario_name: Scenario name
        dashboard_type: "auto", "dh", or "hp"
        auto_generate_map: If True, generates interactive map if missing
    """
    # ... existing code ...
    
    # NEW: Auto-generate map if missing
    if auto_generate_map and not map_file:
        print("  ℹ️  No interactive map found. Generating now...")
        from src.visualization import InteractiveMapGenerator
        map_gen = InteractiveMapGenerator()
        
        if dashboard_type == "dh":
            map_file = map_gen.create_dh_interactive_map(...)
        elif dashboard_type == "hp":
            map_file = map_gen.create_hp_interactive_map(...)
        
        print(f"  ✅ Interactive map generated: {map_file}")
    
    # Continue with dashboard generation...
```

---

## 📋 **Troubleshooting Checklist**

- [ ] **Simulation results exist?**
  - Check: `simulation_outputs/{scenario}_results.json`
  
- [ ] **Interactive map generated?**
  - Check: `results_test/visualizations/interactive/{scenario}*.html`
  
- [ ] **HTML dashboard created?**
  - Check: `results_test/visualizations/html_dashboards/{scenario}*.html`
  
- [ ] **Map path correct in dashboard tool?**
  - The tool searches: `results_test/visualizations/interactive/`
  
- [ ] **File permissions OK?**
  - Ensure directories are writable

---

## ✅ **Quick Fix Commands**

```bash
# Navigate to project
cd "/Users/ishanthahewaratne/Documents/Research/branitz_energy_decision_ai_street_final/untitled folder/branitz_energy_decision_ai_street_agents"

# Activate environment
conda activate branitz_env

# Run complete workflow for a test scenario
python -c "
from src.visualization import InteractiveMapGenerator
from src.dashboards import HTMLDashboardGenerator
import json

# Load sample data
with open('simulation_outputs/test_results.json', 'r') as f:
    result = json.load(f)

# Generate interactive map
map_gen = InteractiveMapGenerator()
map_file = map_gen.create_dh_interactive_map(
    scenario_name='TestScenario',
    buildings_gdf=None,  # Load your buildings
    kpi=result['kpi']
)

# Generate HTML dashboard with embedded map
dashboard_gen = HTMLDashboardGenerator()
html_file = dashboard_gen.create_dh_html_dashboard(
    kpi=result['kpi'],
    scenario_name='TestScenario',
    map_file=map_file
)

print(f'✅ Complete! HTML dashboard with embedded map: {html_file}')
"
```

---

## 🎯 **Summary**

**Problem:** HTML dashboards show "Interactive map not available" message  
**Cause:** No interactive maps have been generated  
**Solution:** Generate interactive maps before creating HTML dashboards

**Two-Step Fix:**
1. `"create interactive map for [scenario]"` ← Generate map first
2. `"create HTML dashboard for [scenario]"` ← Then create dashboard

**Or:** Enable auto-generation in `config/feature_flags.yaml`

---

**Status:** ✅ Working as designed (fallback behavior)  
**Fix:** Generate maps first, then dashboards will embed them automatically

