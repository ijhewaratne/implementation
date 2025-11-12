"""
Schema Versioning Test

Enforces that schema changes are documented in MIGRATIONS.md.
This prevents accidental schema changes without proper documentation.
"""

import json
import re
import pathlib
import pytest

# Schema files to check
SCHEMAS = ["schemas/lfa_demand.schema.json", "schemas/kpi_summary.schema.json"]


def extract_version(schema_path):
    """Extract x-version from a schema file."""
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        return schema.get("x-version")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to read schema {schema_path}: {e}")


def test_schema_versions_have_migrations():
    """Test that all schema versions are documented in MIGRATIONS.md."""
    migrations_path = pathlib.Path("MIGRATIONS.md")

    if not migrations_path.exists():
        pytest.fail("MIGRATIONS.md not found. Create it with initial schema versions.")

    try:
        migrations_content = migrations_path.read_text(encoding="utf-8")
    except Exception as e:
        pytest.fail(f"Failed to read MIGRATIONS.md: {e}")

    for schema_path in SCHEMAS:
        schema_file = pathlib.Path(schema_path)
        if not schema_file.exists():
            pytest.fail(f"Schema file not found: {schema_path}")

        version = extract_version(schema_path)
        if not version:
            pytest.fail(f"Schema {schema_path} missing x-version field")

        # Check for migration entry
        # Pattern: ## filename vX.Y.Z
        filename = schema_file.name
        pattern = rf"^##\s+{re.escape(filename)}\s+v{re.escape(version)}$"

        if not re.search(pattern, migrations_content, flags=re.MULTILINE):
            pytest.fail(
                f"Missing MIGRATIONS.md entry for {filename} v{version}. "
                f"Add: '## {filename} v{version}' to MIGRATIONS.md"
            )


def test_schema_versions_are_semver():
    """Test that schema versions follow semantic versioning."""
    for schema_path in SCHEMAS:
        version = extract_version(schema_path)
        if not version:
            pytest.fail(f"Schema {schema_path} missing x-version field")

        # Check semver pattern: X.Y.Z
        if not re.match(r"^\d+\.\d+\.\d+$", version):
            pytest.fail(
                f"Schema {schema_path} version '{version}' is not valid semver. "
                f"Expected format: X.Y.Z"
            )


def test_schema_files_exist():
    """Test that all expected schema files exist."""
    for schema_path in SCHEMAS:
        if not pathlib.Path(schema_path).exists():
            pytest.fail(f"Required schema file not found: {schema_path}")


def test_migrations_file_exists():
    """Test that MIGRATIONS.md exists."""
    if not pathlib.Path("MIGRATIONS.md").exists():
        pytest.fail("MIGRATIONS.md not found. Create it with initial entries for all schemas.")
