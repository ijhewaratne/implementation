# 📋 CHA Schema Documentation

## 🎯 **Overview**

This directory contains JSON schemas for the CHA (Centralized Heating Agent) system, defining the structure and validation rules for all data formats used throughout the system. These schemas ensure data integrity, enable validation, and provide clear contracts for system integration.

---

## 📁 **Schema Files**

### **1. `cha_output.schema.json`**
**Purpose**: Complete contract for CHA hydraulic simulation output with thermal simulation, pump power calculations, and standards compliance validation.

**Key Features**:
- Hydraulic simulation results (velocity, pressure, flow rates)
- Thermal simulation results (temperature profiles, heat losses)
- Pump power calculations and efficiency metrics
- Standards compliance validation (EN 13941, DIN 1988, VDI 2067)
- Network topology and component data
- Comprehensive metadata and simulation information

**Version**: 2.0.0
**Schema ID**: `https://branitz.ai/schemas/cha_output.schema.json`

### **2. `kpi_summary.schema.json`**
**Purpose**: Contract for end-to-end scenario KPIs including economic, technical, and environmental metrics.

**Key Features**:
- Economic metrics (CAPEX, OPEX, LCoH, NPV, payback period)
- Technical metrics (efficiency, performance, reliability)
- Environmental metrics (emissions, sustainability)
- Recommendation and decision support data
- Project information and metadata

**Version**: 2.0.0
**Schema ID**: `https://branitz.ai/schemas/kpi_summary.schema.json`

### **3. `lfa_demand.schema.json`**
**Purpose**: Schema for Load Forecasting Agent demand data with 8760h series and statistical quantiles.

**Key Features**:
- 8760-hour heat demand series
- Statistical quantiles (q10, q50, q90)
- Building metadata and characteristics
- Time series validation and constraints

**Version**: 1.0.0
**Schema ID**: `https://branitz.ai/schemas/lfa_demand.schema.json`

---

## 🔧 **Schema Usage**

### **Basic Validation**

```python
import json
import jsonschema
from pathlib import Path

def validate_cha_output(data, schema_path="schemas/cha_output.schema.json"):
    """Validate CHA output data against schema."""
    # Load schema
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    # Validate data
    try:
        jsonschema.validate(data, schema)
        print("✅ Data is valid against schema")
        return True
    except jsonschema.ValidationError as e:
        print(f"❌ Validation error: {e.message}")
        return False
    except jsonschema.SchemaError as e:
        print(f"❌ Schema error: {e.message}")
        return False

# Example usage
cha_output = {
    "metadata": {
        "simulation_timestamp": "2024-01-15T10:30:00Z",
        "pandapipes_version": "0.8.0",
        "convergence_status": "converged"
    },
    # ... rest of the data
}

validate_cha_output(cha_output)
```

### **Using CHA Schema Validator**

```python
from src.cha_schema_validator import CHASchemaValidator

# Initialize validator
validator = CHASchemaValidator()

# Validate single file
result = validator.validate_file("processed/cha/cha_output.json")
if result['valid']:
    print("✅ File is valid")
else:
    print(f"❌ Validation errors: {result['errors']}")

# Validate directory
results = validator.validate_directory("processed/cha/")
print(f"Valid files: {results['valid_files']}")
print(f"Invalid files: {results['invalid_files']}")
```

---

## 📊 **CHA Output Schema Details**

### **Required Fields**

The CHA output schema requires the following top-level fields:

```json
{
  "metadata": { /* Simulation metadata */ },
  "nodes": { /* Network nodes data */ },
  "pipes": { /* Network pipes data */ },
  "kpis": { /* Key performance indicators */ },
  "compliance": { /* Standards compliance */ },
  "crs": { /* Coordinate reference system */ },
  "units": { /* Unit definitions */ }
}
```

### **Metadata Structure**

```json
{
  "metadata": {
    "simulation_timestamp": "2024-01-15T10:30:00Z",
    "pandapipes_version": "0.8.0",
    "convergence_status": "converged",
    "total_iterations": 15,
    "simulation_duration_s": 45.2,
    "thermal_simulation_enabled": true,
    "auto_resize_enabled": true,
    "network_size": {
      "junctions": 150,
      "pipes": 200,
      "sources": 1,
      "sinks": 75
    }
  }
}
```

### **KPIs Structure**

```json
{
  "kpis": {
    "hydraulic": {
      "max_velocity_ms": 1.8,
      "max_pressure_drop_pa_per_m": 400,
      "pump_power_kw": 150,
      "total_flow_kg_s": 154.5
    },
    "thermal": {
      "thermal_efficiency": 0.88,
      "total_thermal_loss_kw": 5.0,
      "temperature_drop_c": 12.0,
      "heat_transfer_coefficient_avg": 0.6
    },
    "economic": {
      "capex_eur": 50000.0,
      "opex_eur_per_year": 5000.0,
      "lcoh_eur_per_mwh": 485.2,
      "payback_period_years": 8.5
    }
  }
}
```

### **Compliance Structure**

```json
{
  "compliance": {
    "overall_compliant": true,
    "standards_checked": ["EN_13941", "DIN_1988", "VDI_2067"],
    "violations": [],
    "warnings": [],
    "en13941": {
      "compliant": true,
      "violations": [],
      "details": {
        "velocity_compliance": true,
        "pressure_drop_compliance": true,
        "thermal_efficiency_compliance": true
      }
    }
  }
}
```

---

## 🔍 **Validation Examples**

### **Valid CHA Output Example**

```json
{
  "metadata": {
    "simulation_timestamp": "2024-01-15T10:30:00Z",
    "pandapipes_version": "0.8.0",
    "convergence_status": "converged",
    "total_iterations": 15,
    "simulation_duration_s": 45.2,
    "thermal_simulation_enabled": true,
    "auto_resize_enabled": true,
    "network_size": {
      "junctions": 150,
      "pipes": 200,
      "sources": 1,
      "sinks": 75
    }
  },
  "nodes": {
    "junctions": [
      {
        "id": 1,
        "p_bar": 6.0,
        "t_k": 353.15,
        "x": 52.5200,
        "y": 13.4050
      }
    ],
    "sources": [
      {
        "id": 1,
        "p_bar": 6.0,
        "t_k": 353.15,
        "mdot_kg_per_s": 100.0
      }
    ],
    "sinks": [
      {
        "id": 1,
        "p_bar": 2.0,
        "t_k": 323.15,
        "mdot_kg_per_s": 25.0
      }
    ]
  },
  "pipes": [
    {
      "id": 1,
      "from_node": 1,
      "to_node": 2,
      "length_km": 0.5,
      "diameter_m": 0.2,
      "v_mean_m_per_s": 1.5,
      "p_from_bar": 6.0,
      "p_to_bar": 5.8,
      "mdot_kg_per_s": 25.0,
      "t_from_k": 353.15,
      "t_to_k": 352.15,
      "alpha_w_per_m2k": 0.6,
      "text_k": 283.15
    }
  ],
  "kpis": {
    "hydraulic": {
      "max_velocity_ms": 1.8,
      "max_pressure_drop_pa_per_m": 400,
      "pump_power_kw": 150,
      "total_flow_kg_s": 154.5
    },
    "thermal": {
      "thermal_efficiency": 0.88,
      "total_thermal_loss_kw": 5.0,
      "temperature_drop_c": 12.0,
      "heat_transfer_coefficient_avg": 0.6
    },
    "economic": {
      "capex_eur": 50000.0,
      "opex_eur_per_year": 5000.0,
      "lcoh_eur_per_mwh": 485.2,
      "payback_period_years": 8.5
    }
  },
  "compliance": {
    "overall_compliant": true,
    "standards_checked": ["EN_13941", "DIN_1988", "VDI_2067"],
    "violations": [],
    "warnings": []
  },
  "crs": {
    "type": "EPSG",
    "code": 4326
  },
  "units": {
    "pressure": "bar",
    "temperature": "K",
    "flow_rate": "kg/s",
    "length": "km",
    "diameter": "m",
    "velocity": "m/s",
    "power": "kW",
    "energy": "kWh"
  }
}
```

### **Invalid CHA Output Examples**

#### **Missing Required Field**
```json
{
  "metadata": {
    "simulation_timestamp": "2024-01-15T10:30:00Z"
    // Missing required fields: pandapipes_version, convergence_status
  }
}
```
**Error**: `'pandapipes_version' is a required property`

#### **Invalid Data Type**
```json
{
  "metadata": {
    "simulation_timestamp": "2024-01-15T10:30:00Z",
    "pandapipes_version": 0.8,  // Should be string, not number
    "convergence_status": "converged"
  }
}
```
**Error**: `0.8 is not of type 'string'`

#### **Invalid Enum Value**
```json
{
  "metadata": {
    "simulation_timestamp": "2024-01-15T10:30:00Z",
    "pandapipes_version": "0.8.0",
    "convergence_status": "successful"  // Should be one of: converged, max_iterations, failed
  }
}
```
**Error**: `'successful' is not one of ['converged', 'max_iterations', 'failed']`

---

## 🔗 **Integration Guidelines**

### **1. Schema Validation in CHA System**

```python
from src.cha_validation import CHAValidationSystem
from src.cha_schema_validator import CHASchemaValidator

class CHAOutputGenerator:
    def __init__(self):
        self.validator = CHAValidationSystem()
        self.schema_validator = CHASchemaValidator()
    
    def generate_output(self, simulation_results):
        """Generate validated CHA output."""
        # Create output data
        output_data = self._create_output_data(simulation_results)
        
        # Validate against schema
        schema_result = self.schema_validator.validate_data(output_data)
        if not schema_result['valid']:
            raise ValueError(f"Schema validation failed: {schema_result['errors']}")
        
        # Validate standards compliance
        compliance_result = self.validator.validate_standards_compliance(output_data)
        if not compliance_result['overall_compliant']:
            print(f"Warning: Standards compliance issues: {compliance_result['violations']}")
        
        return output_data
```

### **2. Schema Validation in EAA Integration**

```python
def validate_cha_hydraulic_output(cha_output_path):
    """Validate CHA hydraulic output for EAA integration."""
    from src.cha_schema_validator import CHASchemaValidator
    
    validator = CHASchemaValidator()
    result = validator.validate_file(cha_output_path)
    
    if not result['valid']:
        raise ValueError(f"CHA output validation failed: {result['errors']}")
    
    # Check for required hydraulic data
    with open(cha_output_path, 'r') as f:
        data = json.load(f)
    
    required_hydraulic_fields = [
        'kpis.hydraulic.max_velocity_ms',
        'kpis.hydraulic.max_pressure_drop_pa_per_m',
        'kpis.hydraulic.pump_power_kw'
    ]
    
    for field in required_hydraulic_fields:
        if not _field_exists(data, field):
            raise ValueError(f"Missing required hydraulic field: {field}")
    
    return True

def _field_exists(data, field_path):
    """Check if nested field exists in data."""
    keys = field_path.split('.')
    current = data
    for key in keys:
        if key not in current:
            return False
        current = current[key]
    return True
```

### **3. Schema Validation in TCA Integration**

```python
def validate_cha_for_tca(cha_output_path):
    """Validate CHA output for TCA integration."""
    from src.cha_schema_validator import CHASchemaValidator
    
    validator = CHASchemaValidator()
    result = validator.validate_file(cha_output_path)
    
    if not result['valid']:
        raise ValueError(f"CHA output validation failed: {result['errors']}")
    
    # Load and validate data
    with open(cha_output_path, 'r') as f:
        data = json.load(f)
    
    # Validate thermal metrics for TCA
    thermal_metrics = data.get('kpis', {}).get('thermal', {})
    required_thermal_fields = [
        'thermal_efficiency',
        'total_thermal_loss_kw',
        'temperature_drop_c'
    ]
    
    for field in required_thermal_fields:
        if field not in thermal_metrics:
            raise ValueError(f"Missing required thermal field: {field}")
        
        value = thermal_metrics[field]
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"Invalid thermal field value: {field} = {value}")
    
    return True
```

### **4. Schema Version Management**

```python
def check_schema_compatibility(data, required_version="2.0.0"):
    """Check schema version compatibility."""
    schema_version = data.get('metadata', {}).get('schema_version', '1.0.0')
    
    if schema_version != required_version:
        print(f"Warning: Schema version mismatch. Expected {required_version}, got {schema_version}")
        
        # Handle version compatibility
        if schema_version.startswith('1.'):
            print("Converting from schema v1 to v2...")
            data = convert_schema_v1_to_v2(data)
        elif schema_version.startswith('2.'):
            print("Schema version is compatible")
        else:
            raise ValueError(f"Unsupported schema version: {schema_version}")
    
    return data

def convert_schema_v1_to_v2(data):
    """Convert schema v1 to v2 format."""
    # Add new required fields for v2
    if 'compliance' not in data:
        data['compliance'] = {
            'overall_compliant': True,
            'standards_checked': [],
            'violations': [],
            'warnings': []
        }
    
    # Update metadata
    if 'metadata' not in data:
        data['metadata'] = {}
    
    data['metadata']['schema_version'] = '2.0.0'
    
    return data
```

---

## 🚨 **Troubleshooting Common Issues**

### **1. Schema Validation Failures**

#### **Issue: "Required property missing" errors**

**Symptoms**:
```
ValidationError: 'pandapipes_version' is a required property
```

**Solutions**:
```python
# Check required fields
required_fields = [
    'metadata.pandapipes_version',
    'metadata.convergence_status',
    'metadata.simulation_timestamp'
]

def check_required_fields(data):
    """Check if all required fields are present."""
    missing_fields = []
    for field in required_fields:
        if not _field_exists(data, field):
            missing_fields.append(field)
    
    if missing_fields:
        print(f"Missing required fields: {missing_fields}")
        return False
    return True

# Fix missing fields
def fix_missing_fields(data):
    """Add missing required fields with default values."""
    if 'metadata' not in data:
        data['metadata'] = {}
    
    defaults = {
        'pandapipes_version': '0.8.0',
        'convergence_status': 'converged',
        'simulation_timestamp': datetime.now().isoformat()
    }
    
    for field, default_value in defaults.items():
        if field not in data['metadata']:
            data['metadata'][field] = default_value
    
    return data
```

#### **Issue: "Invalid type" errors**

**Symptoms**:
```
ValidationError: 0.8 is not of type 'string'
```

**Solutions**:
```python
def fix_type_errors(data):
    """Fix common type errors in data."""
    # Fix string type errors
    if 'metadata' in data:
        if 'pandapipes_version' in data['metadata']:
            if isinstance(data['metadata']['pandapipes_version'], (int, float)):
                data['metadata']['pandapipes_version'] = str(data['metadata']['pandapipes_version'])
    
    # Fix numeric type errors
    if 'kpis' in data:
        for category in ['hydraulic', 'thermal', 'economic']:
            if category in data['kpis']:
                for field, value in data['kpis'][category].items():
                    if isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                        data['kpis'][category][field] = float(value)
    
    return data
```

#### **Issue: "Invalid enum value" errors**

**Symptoms**:
```
ValidationError: 'successful' is not one of ['converged', 'max_iterations', 'failed']
```

**Solutions**:
```python
def fix_enum_errors(data):
    """Fix enum value errors."""
    enum_mappings = {
        'convergence_status': {
            'successful': 'converged',
            'completed': 'converged',
            'failed': 'failed',
            'timeout': 'max_iterations'
        }
    }
    
    if 'metadata' in data:
        for field, mapping in enum_mappings.items():
            if field in data['metadata']:
                value = data['metadata'][field]
                if value in mapping:
                    data['metadata'][field] = mapping[value]
    
    return data
```

### **2. Schema File Issues**

#### **Issue: Schema file not found**

**Symptoms**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'schemas/cha_output.schema.json'
```

**Solutions**:
```python
import os
from pathlib import Path

def find_schema_file(schema_name):
    """Find schema file in various locations."""
    possible_paths = [
        f"schemas/{schema_name}",
        f"../schemas/{schema_name}",
        f"../../schemas/{schema_name}",
        Path(__file__).parent / "schemas" / schema_name
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError(f"Schema file not found: {schema_name}")

# Use in validation
schema_path = find_schema_file("cha_output.schema.json")
with open(schema_path, 'r') as f:
    schema = json.load(f)
```

#### **Issue: Invalid JSON schema**

**Symptoms**:
```
SchemaError: 'required' is a required property
```

**Solutions**:
```python
def validate_schema_file(schema_path):
    """Validate schema file itself."""
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Check required schema properties
        required_props = ['$schema', 'type', 'properties']
        for prop in required_props:
            if prop not in schema:
                raise ValueError(f"Schema missing required property: {prop}")
        
        # Validate against JSON Schema meta-schema
        jsonschema.validate(schema, jsonschema.Draft7Validator.META_SCHEMA)
        print("✅ Schema file is valid")
        return True
        
    except Exception as e:
        print(f"❌ Schema file error: {e}")
        return False
```

### **3. Performance Issues**

#### **Issue: Slow validation with large datasets**

**Symptoms**:
- Validation takes minutes for large networks
- High memory usage during validation
- System becomes unresponsive

**Solutions**:
```python
def validate_large_dataset_optimized(data, schema):
    """Optimized validation for large datasets."""
    import jsonschema
    
    # Use lazy validation
    validator = jsonschema.Draft7Validator(schema)
    
    # Validate in chunks
    chunk_size = 1000
    errors = []
    
    # Validate metadata first (small and critical)
    try:
        jsonschema.validate(data.get('metadata', {}), schema['properties']['metadata'])
    except jsonschema.ValidationError as e:
        errors.append(e)
    
    # Validate arrays in chunks
    for array_name in ['nodes', 'pipes']:
        if array_name in data:
            array_data = data[array_name]
            if isinstance(array_data, list):
                for i in range(0, len(array_data), chunk_size):
                    chunk = array_data[i:i + chunk_size]
                    try:
                        jsonschema.validate(chunk, schema['properties'][array_name])
                    except jsonschema.ValidationError as e:
                        errors.append(e)
    
    return len(errors) == 0, errors
```

### **4. Integration Issues**

#### **Issue: Schema version conflicts**

**Symptoms**:
- Different components expect different schema versions
- Validation fails due to version mismatch
- Data format incompatibilities

**Solutions**:
```python
def handle_schema_version_conflicts(data, target_version="2.0.0"):
    """Handle schema version conflicts."""
    current_version = data.get('metadata', {}).get('schema_version', '1.0.0')
    
    if current_version == target_version:
        return data
    
    print(f"Converting schema from {current_version} to {target_version}")
    
    # Version-specific conversion logic
    if current_version.startswith('1.') and target_version.startswith('2.'):
        data = convert_v1_to_v2(data)
    elif current_version.startswith('2.') and target_version.startswith('1.'):
        data = convert_v2_to_v1(data)
    else:
        raise ValueError(f"Cannot convert from {current_version} to {target_version}")
    
    # Update version
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['schema_version'] = target_version
    
    return data
```

---

## 📚 **Additional Resources**

### **JSON Schema Documentation**
- [JSON Schema Specification](https://json-schema.org/)
- [JSON Schema Validation](https://json-schema.org/understanding-json-schema/reference/)
- [Python jsonschema Library](https://python-jsonschema.readthedocs.io/)

### **CHA System Documentation**
- [CHA Comprehensive Guide](../CHA_COMPREHENSIVE_GUIDE.md)
- [API Documentation](../API_DOCUMENTATION.md)
- [Developer Guide](../DEVELOPER_GUIDE.md)
- [Troubleshooting Guide](../TROUBLESHOOTING_GUIDE.md)

### **Validation Tools**
- [JSON Schema Validator](https://www.jsonschemavalidator.net/)
- [JSON Lint](https://jsonlint.com/)
- [Schema Validator CLI](https://github.com/Julian/jsonschema)

---

## 🎯 **Conclusion**

This schema documentation provides comprehensive guidance for working with CHA system schemas. The schemas ensure data integrity, enable validation, and provide clear contracts for system integration. For additional support:

1. Check the validation examples for common use cases
2. Use the troubleshooting guide for common issues
3. Refer to the integration guidelines for system integration
4. Contact support with specific schema-related questions

Remember to always validate your data against the appropriate schema before processing or integration.
