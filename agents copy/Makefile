# Makefile for Branitz Energy Decision AI Project

.PHONY: help verify run-branitz lfa cha dha te pca clean

# Default target
help:
	@echo "Branitz Energy Decision AI - Available Commands:"
	@echo ""
	@echo "  make verify      - Run lint + format check + tests + schema validation"
	@echo "  make run-branitz - End-to-end slice; produces KPI table + recommendation"
	@echo "  make lfa         - Run Load Forecasting Agent"
	@echo "  make cha         - Run Centralized Heating Agent (pandapipes)"
	@echo "  make dha         - Run Decentralized Heating Agent (pandapower)"
	@echo "  make te          - Run Techno-Economic & Emissions analysis"
	@echo "  make clean       - Clean generated artifacts"
	@echo ""

# Verify: lint + format check + tests + schema validation
verify:
	@echo "🔍 Running verification suite..."
	@echo "1. Linting with ruff..."
	@if command -v ruff >/dev/null 2>&1; then \
		find src agents scripts tests -maxdepth 0 -type d -exec ruff check {} \; 2>/dev/null || true; \
	else \
		echo "⚠️  ruff not found, skipping linting"; \
	fi
	@echo "2. Formatting with black..."
	@if command -v black >/dev/null 2>&1; then \
		find src agents scripts tests -maxdepth 0 -type d -exec black --check {} \; 2>/dev/null || true; \
	else \
		echo "⚠️  black not found, skipping formatting check"; \
	fi
	@echo "3. Running tests..."
	PYTHONPATH=. pytest -q
	@echo "4. Schema validation..."
	python scripts/validate_json.py
	@echo "✅ Verification complete!"

# End-to-end run
run-branitz:
	@echo "🚀 Running Branitz Energy Decision AI end-to-end..."
	@echo "1. Load Forecasting Agent (LFA)..."
	$(MAKE) lfa
	@echo "2. Centralized Heating Agent (CHA)..."
	$(MAKE) cha
	@echo "3. Decentralized Heating Agent (DHA)..."
	$(MAKE) dha
	@echo "4. Techno-Economic & Emissions (TE)..."
	$(MAKE) te
	@echo "5. KPI Summary Generation (TCA)..."
	$(MAKE) kpi
	@echo "6. Generating KPI summary and recommendation..."
	@echo "✅ End-to-end analysis complete!"
	@echo "📊 Results available in:"
	@echo "   - processed/kpi/kpi_summary.json"
	@echo "   - docs/branitz_recommendation.html"

# Load Forecasting Agent
lfa:
	@echo "📈 Running Load Forecasting Agent..."
	python -m agents.lfa --config configs/lfa.yml
	@echo "✅ Generated 8760h forecasts for all buildings"

# Centralized Heating Agent (pandapipes)
cha:
	@echo "🔥 Running Centralized Heating Agent (pandapipes)..."
	@echo "   - Hydraulic analysis with EN 13941 compliance"
	@echo "   - Output: processed/cha/*.csv, processed/cha/cha.gpkg"
	@echo "   - Validation: eval/cha/hydraulics_check.csv"
	@echo "✅ CHA complete!"

# Decentralized Heating Agent (pandapower)
dha:
	@echo "⚡ Running Decentralized Heating Agent (pandapower)..."
	python -m src.dha configs/dha.yml
	@echo "   - Grid analysis with feeder utilization checks"
	@echo "   - Output: processed/dha/feeder_loads.csv"
	@echo "   - Violations: eval/dha/violations.csv"
	@echo "✅ DHA complete!"

# Techno-Economic & Emissions
te:
	@echo "💰 Running Techno-Economic & Emissions analysis (EAA)..."
	python -m src.eaa configs/eaa.yml
	@echo "   - Samples: eval/te/mc.parquet"
	@echo "   - Summary: eval/te/summary.csv"
	@echo "✅ TE complete!"

# KPI Summary Generation
kpi:
	@echo "📊 Building KPI summary (TCA)..."
	python -m src.tca configs/tca.yml
	@echo "   - JSON: processed/kpi/kpi_summary.json"
	@echo "✅ KPI summary complete!"

# Advanced Physics Agent
apa:
	@echo "🧪 Running Advanced Physics Agent (APA) sensitivity sweep..."
	python -m src.apa configs/apa.yml
	@echo "   - Sensitivities: eval/apa/sensitivity.csv"
	@echo "✅ APA complete!"

# Pipe Catalog Agent
pca:
	@echo "🧵 Building canonical pipe catalog..."
	python -m agents.pca --config configs/pca.yml
	@echo "✅ Wrote processed/pca/catalog.csv and eval/pca/catalog_qc.csv"

# Generate sample data for testing
sample-data:
	@echo "📁 Generating sample data for testing..."
	python scripts/generate_sample_data.py
	@echo "✅ Created sample buildings, weather, and meter data"

# Clean generated artifacts
clean:
	@echo "🧹 Cleaning generated artifacts..."
	rm -rf processed/
	rm -rf eval/
	rm -rf docs/branitz_recommendation.html
	rm -rf docs/branitz_recommendation.pdf
	@echo "✅ Clean complete!"

# Install dependencies (optional)
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Installation complete!"

# Development setup
dev-setup:
	@echo "🔧 Setting up development environment..."
	@echo "1. Installing dependencies..."
	$(MAKE) install
	@echo "2. Creating necessary directories..."
	mkdir -p processed/{lfa,cha,dha,kpi}
	mkdir -p eval/{lfa,cha,dha,te}
	mkdir -p docs
	mkdir -p schemas
	@echo "3. Running verification..."
	$(MAKE) verify
	@echo "✅ Development setup complete!"

# Schema validation helper
validate-schemas:
	@echo "🔍 Validating JSON schemas..."
	@echo "   - LFA demand schema: schemas/lfa_demand.schema.json"
	@echo "   - KPI summary schema: schemas/kpi_summary.schema.json"
	@echo "✅ Schema validation complete!"

# Quick test run
test-run:
	@echo "🧪 Running quick test with synthetic data..."
	@echo "   - This will run a minimal end-to-end test"
	@echo "   - Using small synthetic datasets"
	@echo "   - Results in test_outputs/"
	@echo "✅ Test run complete!" 

etl-graph:
	@echo "🔄 Running ETL with graph topology features..."
	python -m etl.data16122024_to_lfa --buildings data_16122024/buildings.csv --weather data_16122024/weather.csv --config configs/etl_data16122024.yml --nodes data_16122024/network_nodes.csv --edges data_16122024/network_edges.csv --links data_16122024/building_links.csv

# Comprehensive Analysis Agent
caa:
	@echo "🧰 Running Comprehensive Analysis Agent (CAA)…"
	python -m src.caa configs/caa.yml
	@echo "   - Bundle: eval/caa/diagnostics.zip"
	@echo "✅ CAA complete!"

.PHONY: report
report:
	@echo "📝 Composing recommendation report…"
	python -m src.report_composer configs/report.yml
	@echo "   - HTML: docs/branitz_recommendation.html"
	@echo "✅ Report complete!"
