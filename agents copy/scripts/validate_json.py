#!/usr/bin/env python3
"""
JSON Schema Validation Script

Validates all JSON files against their respective schemas.
Used by make verify to ensure contract compliance.
"""

import json
import glob
import sys
import os
from pathlib import Path
from jsonschema import validate, Draft202012Validator

# Environment variable for strict validation (fail on empty folders)
STRICT = os.getenv("STRICT_VALIDATION", "0") == "1"


def load_schema(name):
    """Load a JSON schema from the schemas directory."""
    schema_path = Path(f"schemas/{name}.schema.json")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_folder(folder, schema, schema_name):
    """Validate all JSON files in a folder against a schema."""
    errors = []
    folder_path = Path(folder)

    if not folder_path.exists():
        msg = f"⚠️  {folder} does not exist, skipping validation"
        if STRICT:
            raise SystemExit(msg)
        else:
            print(msg)
            return

    json_files = list(folder_path.glob("*.json"))
    if not json_files:
        msg = f"⚠️  No JSON files found in {folder}"
        if STRICT:
            raise SystemExit(msg)
        else:
            print(msg)
            return

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                instance = json.load(f)
            validate(instance=instance, schema=schema, cls=Draft202012Validator)
            print(f"✅ {json_file} - Valid")
        except Exception as e:
            error_msg = f"{json_file}: {e}"
            errors.append(error_msg)
            print(f"❌ {error_msg}")

    if errors:
        raise SystemExit(f"\n❌ Schema validation failed for {schema_name}:\n" + "\n".join(errors))


def main():
    """Main validation function."""
    print("🔍 Starting JSON schema validation...")

    try:
        # Load schemas
        SCHEMAS = {
            "lfa": load_schema("lfa_demand"),
            "kpi": load_schema("kpi_summary"),
        }

        # Validate LFA time series
        print("\n📈 Validating LFA demand data...")
        validate_folder("processed/lfa", SCHEMAS["lfa"], "LFA Demand")

        # Validate KPI summary
        print("\n📊 Validating KPI summary...")
        validate_folder("processed/kpi", SCHEMAS["kpi"], "KPI Summary")

        print("\n✅ All JSON files passed schema validation!")

    except FileNotFoundError as e:
        print(f"❌ Schema file not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Validation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
