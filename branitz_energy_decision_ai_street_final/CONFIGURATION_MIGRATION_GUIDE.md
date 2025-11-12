# 🔄 CHA Configuration Migration Guide

## 🎯 **Overview**

This guide provides comprehensive instructions for migrating CHA (Centralized Heating Agent) configurations from legacy versions to the latest intelligent pipe sizing system. The migration process ensures backward compatibility while enabling new features and capabilities.

---

## 📋 **Migration Overview**

### **Configuration Versions**

The CHA system has evolved through several configuration versions:

1. **CHA v1.0** - Basic configuration with simple pipe sizing
2. **CHA v2.0** - Enhanced configuration with intelligent pipe sizing
3. **CHA v2.1 (Intelligent Sizing)** - Advanced configuration with comprehensive pipe sizing, flow calculation, and standards compliance

### **Migration Paths**

```
CHA v1.0 → CHA v2.0 → CHA v2.1 (Intelligent Sizing)
    ↓           ↓              ↓
Basic      Enhanced      Advanced
Sizing     Sizing        Sizing
```

---

## 🚀 **Quick Migration**

### **Automated Migration**

The easiest way to migrate configurations is using the automated migration tool:

```bash
# Migrate from CHA v1 to v2
python src/cha_config_migration.py --action migrate --source configs/cha.yml --target configs/cha_v2.yml

# Migrate from CHA v2 to Intelligent Sizing
python src/cha_config_migration.py --action migrate --source configs/cha_v2.yml --target configs/cha_intelligent_sizing.yml

# Auto-detect and migrate to latest version
python src/cha_config_migration.py --action migrate --source configs/cha.yml --target configs/cha_latest.yml --migration-type auto
```

### **Validation**

After migration, validate the new configuration:

```bash
# Validate migrated configuration
python scripts/validate_config.py configs/cha_intelligent_sizing.yml

# Validate with detailed report
python scripts/validate_config.py configs/cha_intelligent_sizing.yml --output migration_report.json --format json
```

---

## 📊 **Detailed Migration Steps**

### **Step 1: CHA v1.0 to CHA v2.0**

#### **What Changes**

**New Sections Added:**
- `pipe_sizing` - Intelligent pipe sizing configuration
- `pandapipes` - Enhanced pandapipes simulation settings

**Field Migrations:**
```yaml
# OLD (v1.0)
default_pipe_diameter_m: 0.1
default_pipe_roughness_mm: 0.1
default_mass_flow_kg_s: 0.1
enable_pandapipes_simulation: true

# NEW (v2.0)
pipe_sizing:
  enable_intelligent_sizing: true
  standard_diameters: [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400]
  max_velocity_ms: 2.0
  min_velocity_ms: 0.1
  max_pressure_drop_pa_per_m: 5000

pandapipes:
  enabled: true
  default_diameter_m: 0.1
  default_roughness_mm: 0.1
  default_mass_flow_kg_s: 0.1
```

#### **Migration Process**

1. **Backup Original Configuration**
   ```bash
   cp configs/cha.yml configs/cha_v1_backup.yml
   ```

2. **Run Migration**
   ```bash
   python src/cha_config_migration.py --action migrate --source configs/cha.yml --target configs/cha_v2.yml --migration-type cha_v1_to_cha_v2
   ```

3. **Verify Migration**
   ```bash
   python scripts/validate_config.py configs/cha_v2.yml
   ```

#### **Manual Migration (if needed)**

If automated migration fails, manually update your configuration:

```yaml
# Add to your existing cha.yml
pipe_sizing:
  enable_intelligent_sizing: true
  standard_diameters: [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400]
  max_velocity_ms: 2.0
  min_velocity_ms: 0.1
  max_pressure_drop_pa_per_m: 5000
  water_density_kg_m3: 977.8
  water_specific_heat_j_per_kgk: 4180
  pipe_roughness_mm: 0.1
  pipe_material: "steel"
  insulation_material: "polyurethane"
  insulation_thickness_mm: 30

pandapipes:
  enabled: true
  default_diameter_m: 0.1
  default_roughness_mm: 0.1
  default_mass_flow_kg_s: 0.1
```

### **Step 2: CHA v2.0 to CHA v2.1 (Intelligent Sizing)**

#### **What Changes**

**New Sections Added:**
- `flow_calculation` - Advanced flow calculation with safety factors
- `network_hierarchy` - Network hierarchy analysis
- `standards_compliance` - Engineering standards compliance
- `output` - Enhanced output configuration
- `validation` - Configuration validation settings
- `performance` - Performance optimization settings
- `logging` - Logging configuration

**Field Migrations:**
```yaml
# OLD (v2.0)
pipe_sizing:
  standard_diameters: [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400]

# NEW (v2.1)
pipe_sizing:
  standard_diameters_mm: [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400]
```

#### **Migration Process**

1. **Backup v2.0 Configuration**
   ```bash
   cp configs/cha_v2.yml configs/cha_v2_backup.yml
   ```

2. **Run Migration**
   ```bash
   python src/cha_config_migration.py --action migrate --source configs/cha_v2.yml --target configs/cha_intelligent_sizing.yml --migration-type cha_v2_to_cha_intelligent_sizing
   ```

3. **Verify Migration**
   ```bash
   python scripts/validate_config.py configs/cha_intelligent_sizing.yml
   ```

#### **Manual Migration (if needed)**

Add the following sections to your v2.0 configuration:

```yaml
# Add to your existing cha_v2.yml
flow_calculation:
  supply_temperature_c: 70
  return_temperature_c: 40
  design_hour_method: "peak_hour"
  top_n_hours: 10
  design_full_load_hours: 2000
  safety_factor: 1.1
  diversity_factor: 0.8
  water_density_kg_m3: 977.8
  water_specific_heat_j_per_kgk: 4180

network_hierarchy:
  network_analysis: true
  connectivity_check: true
  critical_path_analysis: true
  hierarchy_levels:
    1:
      name: "Service Connections"
      min_flow_kg_s: 0
      max_flow_kg_s: 2
    2:
      name: "Street Distribution"
      min_flow_kg_s: 2
      max_flow_kg_s: 10
    3:
      name: "Area Distribution"
      min_flow_kg_s: 10
      max_flow_kg_s: 30
    4:
      name: "Main Distribution"
      min_flow_kg_s: 30
      max_flow_kg_s: 80
    5:
      name: "Primary Main"
      min_flow_kg_s: 80
      max_flow_kg_s: 200

standards_compliance:
  standards_enabled:
    - "EN_13941"
    - "DIN_1988"
    - "VDI_2067"
    - "Local_Codes"
  severity_thresholds:
    critical: 0.5
    high: 0.3
    medium: 0.2
    low: 0.1

output:
  output_dir: "processed/cha_intelligent_sizing"
  export_flow_results: true
  export_pipe_sizing_results: true
  export_compliance_results: true
  export_network_hierarchy: true
  export_summary: true

validation:
  validate_inputs: true
  validate_outputs: true
  check_connectivity: true
  check_standards_compliance: true

performance:
  enable_optimization: true
  parallel_processing: true
  max_workers: 4
  enable_caching: true
  cache_size_mb: 100

logging:
  log_level: "INFO"
  log_file: "logs/cha_intelligent_sizing.log"
  log_format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## 🔧 **Configuration Templates**

### **Creating Templates**

Use the migration tool to create configuration templates:

```bash
# Create CHA v1 template
python src/cha_config_migration.py --action template --template-name cha_v1_template --template-type cha_v1

# Create CHA v2 template
python src/cha_config_migration.py --action template --template-name cha_v2_template --template-type cha_v2

# Create Intelligent Sizing template
python src/cha_config_migration.py --action template --template-name cha_intelligent_sizing_template --template-type cha_intelligent_sizing
```

### **Template Usage**

1. **Copy Template**
   ```bash
   cp configs/templates/cha_intelligent_sizing_template.yml configs/my_project.yml
   ```

2. **Customize Configuration**
   Edit the copied template with your project-specific settings

3. **Validate Configuration**
   ```bash
   python scripts/validate_config.py configs/my_project.yml
   ```

---

## ✅ **Validation and Testing**

### **Configuration Validation**

The validation script checks:
- **Schema Compliance** - Required fields and structure
- **Value Ranges** - Parameter values within acceptable ranges
- **Dependencies** - Cross-parameter dependencies
- **Best Practices** - Configuration optimization recommendations

```bash
# Basic validation
python scripts/validate_config.py configs/cha_intelligent_sizing.yml

# Detailed validation with report
python scripts/validate_config.py configs/cha_intelligent_sizing.yml --output validation_report.json --format json

# Verbose validation
python scripts/validate_config.py configs/cha_intelligent_sizing.yml --verbose
```

### **Validation Output**

The validation script provides:
- ✅ **Valid/Invalid Status** - Overall configuration validity
- ❌ **Errors** - Critical issues that must be fixed
- ⚠️ **Warnings** - Issues that should be addressed
- 💡 **Recommendations** - Best practice suggestions
- 🔄 **Migration Recommendations** - Upgrade suggestions

### **Testing Migrated Configuration**

1. **Run Unit Tests**
   ```bash
   python -m pytest tests/test_cha_pipe_sizing.py -v
   ```

2. **Run Integration Tests**
   ```bash
   python -m pytest tests/test_cha_integration.py -v
   ```

3. **Test with Sample Data**
   ```bash
   python src/cha_main.py --config configs/cha_intelligent_sizing.yml --test-mode
   ```

---

## 🔍 **Troubleshooting Migration Issues**

### **Common Issues**

#### **1. Missing Required Fields**

**Error**: `Missing required field: pipe_sizing`

**Solution**: Add the missing section to your configuration:
```yaml
pipe_sizing:
  enable_intelligent_sizing: true
  standard_diameters_mm: [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400]
  max_velocity_ms: 2.0
  min_velocity_ms: 0.1
  max_pressure_drop_pa_per_m: 5000
```

#### **2. Invalid Value Ranges**

**Error**: `Value 5.0 is above maximum 3.0 for max_velocity_ms`

**Solution**: Adjust the value to be within the acceptable range:
```yaml
pipe_sizing:
  max_velocity_ms: 2.0  # Reduced from 5.0
```

#### **3. Dependency Violations**

**Error**: `supply_temperature_c must be greater than return_temperature_c`

**Solution**: Ensure temperature values are correct:
```yaml
flow_calculation:
  supply_temperature_c: 70  # Must be > return_temperature_c
  return_temperature_c: 40
```

#### **4. File Path Issues**

**Warning**: `Streets file not found: data/geojson/streets.geojson`

**Solution**: Update file paths to match your data structure:
```yaml
streets_path: "agents copy/data/geojson/strassen_mit_adressenV3.geojson"
buildings_path: "agents copy/data/geojson/hausumringe_mit_adressenV3.geojson"
```

### **Migration Rollback**

If migration causes issues, you can rollback:

1. **Restore Backup**
   ```bash
   cp configs/cha_v1_backup.yml configs/cha.yml
   ```

2. **Verify Rollback**
   ```bash
   python scripts/validate_config.py configs/cha.yml
   ```

---

## 📊 **Migration Best Practices**

### **Before Migration**

1. **Backup Everything**
   ```bash
   # Create full backup
   tar -czf cha_config_backup_$(date +%Y%m%d).tar.gz configs/
   ```

2. **Document Current Settings**
   - Note any custom parameters
   - Document any special configurations
   - Record performance settings

3. **Test in Development**
   - Migrate in development environment first
   - Test with sample data
   - Verify all functionality works

### **During Migration**

1. **Use Automated Tools**
   - Prefer automated migration over manual
   - Validate after each migration step
   - Keep backups of each version

2. **Incremental Migration**
   - Migrate one version at a time
   - Test after each step
   - Don't skip intermediate versions

### **After Migration**

1. **Comprehensive Testing**
   - Run all tests
   - Test with real data
   - Verify performance

2. **Documentation Update**
   - Update project documentation
   - Note any configuration changes
   - Update deployment procedures

3. **Team Communication**
   - Inform team of changes
   - Provide migration instructions
   - Share new configuration templates

---

## 🎯 **Configuration Comparison**

### **Feature Comparison**

| Feature | CHA v1.0 | CHA v2.0 | CHA v2.1 (Intelligent) |
|---------|-----------|----------|------------------------|
| Basic Pipe Sizing | ✅ | ✅ | ✅ |
| Intelligent Sizing | ❌ | ✅ | ✅ |
| Flow Calculation | ❌ | ❌ | ✅ |
| Network Hierarchy | ❌ | ❌ | ✅ |
| Standards Compliance | ❌ | ❌ | ✅ |
| Performance Optimization | ❌ | ❌ | ✅ |
| Advanced Validation | ❌ | ❌ | ✅ |
| Cost-Benefit Analysis | ❌ | ❌ | ✅ |

### **Performance Comparison**

| Metric | CHA v1.0 | CHA v2.0 | CHA v2.1 (Intelligent) |
|--------|-----------|----------|------------------------|
| Pipe Sizing Accuracy | Basic | Good | Excellent |
| Simulation Speed | Fast | Fast | Optimized |
| Memory Usage | Low | Medium | Optimized |
| Configuration Complexity | Simple | Medium | Advanced |
| Feature Completeness | Basic | Enhanced | Complete |

---

## 🚀 **Advanced Migration Scenarios**

### **Custom Configuration Migration**

If you have custom configurations that don't fit standard migration paths:

1. **Analyze Custom Settings**
   ```bash
   python scripts/validate_config.py configs/custom_config.yml --verbose
   ```

2. **Create Custom Migration Mapping**
   ```python
   # Add to migration_mappings in cha_config_migration.py
   'custom_to_intelligent_sizing': {
       'mappings': {
           'custom_pipe_setting': 'pipe_sizing.custom_setting',
           'custom_flow_setting': 'flow_calculation.custom_setting'
       },
       'new_sections': {
           'custom_section': {
               'custom_parameter': 'default_value'
           }
       }
   }
   ```

3. **Run Custom Migration**
   ```bash
   python src/cha_config_migration.py --action migrate --source configs/custom_config.yml --target configs/migrated_config.yml --migration-type custom_to_intelligent_sizing
   ```

### **Batch Migration**

For multiple configurations:

```bash
#!/bin/bash
# Batch migration script

for config in configs/*.yml; do
    if [[ $config != *"backup"* && $config != *"template"* ]]; then
        echo "Migrating $config..."
        python src/cha_config_migration.py --action migrate --source "$config" --target "${config%.yml}_migrated.yml"
        python scripts/validate_config.py "${config%.yml}_migrated.yml"
    fi
done
```

### **Environment-Specific Migration**

Different environments may need different configurations:

```bash
# Development environment
python src/cha_config_migration.py --action migrate --source configs/cha.yml --target configs/cha_dev.yml
# Edit configs/cha_dev.yml for development settings

# Staging environment
python src/cha_config_migration.py --action migrate --source configs/cha.yml --target configs/cha_staging.yml
# Edit configs/cha_staging.yml for staging settings

# Production environment
python src/cha_config_migration.py --action migrate --source configs/cha.yml --target configs/cha_prod.yml
# Edit configs/cha_prod.yml for production settings
```

---

## 📚 **Migration Resources**

### **Tools and Scripts**

- **Migration Tool**: `src/cha_config_migration.py`
- **Validation Script**: `scripts/validate_config.py`
- **Configuration Templates**: `configs/templates/`
- **Migration Reports**: `configs/migration_report_*.json`

### **Documentation**

- **API Documentation**: `API_DOCUMENTATION.md`
- **Implementation Guide**: `PIPE_SIZING_IMPLEMENTATION.md`
- **User Guide**: `USER_GUIDE.md`
- **Developer Guide**: `DEVELOPER_GUIDE.md`

### **Support**

- **Validation Reports**: Check validation output for specific guidance
- **Migration Logs**: Review `configs/migration.log` for detailed information
- **Backup Files**: Use backup files in `configs/backups/` for rollback

---

## 🎯 **Conclusion**

The CHA Configuration Migration Guide provides comprehensive instructions for migrating from legacy configurations to the latest intelligent pipe sizing system. By following this guide, you can:

✅ **Safely migrate** configurations while maintaining functionality  
✅ **Validate** migrated configurations for correctness  
✅ **Optimize** configurations for best performance  
✅ **Troubleshoot** common migration issues  
✅ **Maintain** backward compatibility  

The migration process is designed to be:
- **Safe** - Automatic backups and validation
- **Comprehensive** - Complete feature migration
- **Flexible** - Support for custom configurations
- **Well-documented** - Clear instructions and examples

**Start your migration today and unlock the full potential of the CHA Intelligent Pipe Sizing System!** 🚀

---

*This migration guide is part of the Branitz Energy Decision AI project. For more information, see the main project documentation.*
