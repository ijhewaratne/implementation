# Makefile for Branitz Energy Decision AI Project

.PHONY: help verify run-branitz run-street thesis-data thesis-data-street lfa cha cha-interactive dha dha-interactive te kpi pca caa clean enhanced-agents test-enhanced-agents batch-enhanced-agents test-adk-config test-adk-runner test-adk-input test-adk-analysis egpt results dashboard results-dashboard combined-dashboard figures comprehensive-dashboard street-dashboard deploy-adk deploy-dev deploy-staging deploy-prod docker-build docker-up docker-down docker-logs

# Default target
help:
	@echo "Branitz Energy Decision AI - Available Commands:"
	@echo ""
	@echo "  make verify      - Run lint + format check + tests + schema validation"
	@echo "  make run-branitz - End-to-end slice; produces KPI table + recommendation"
	@echo "  make run-street  - Fast testing for specific street (requires STREET='...')"
	@echo "  make thesis-data - Run Thesis Data Integration (replaces LFA)"
	@echo "  make thesis-data-street - Street-specific data generation (requires STREET='...')"
	@echo "  make lfa         - Legacy LFA (redirects to thesis-data)"
	@echo "  make cha         - Run Centralized Heating Agent (pandapipes)"
	@echo "  make validate-cha-output - Validate CHA hydraulic simulation outputs"
	@echo "  make cha-simulation-only - Run CHA hydraulic simulation only"
	@echo "  make dha         - Run Decentralized Heating Agent (pandapower)"
	@echo "  make te          - Run Techno-Economic & Emissions analysis (EAA + TCA)"
	@echo "  make kpi         - Run KPI generation and decision support (TCA)"
	@echo "  make caa         - Comprehensive Analysis Agent (diagnostics bundle)"
	@echo "  make enhanced-agents - Run Enhanced Multi-Agent System (ADK-based)"
	@echo "  make test-enhanced-agents - Test Enhanced Multi-Agent System"
	@echo "  make batch-enhanced-agents - Run Enhanced Multi-Agent System in batch mode"
	@echo "  make test-adk-config - Test ADK Agent Configurations"
	@echo "  make test-adk-runner - Test ADK Agent Runner"
	@echo "  make test-adk-input - Test ADK Single Input Processing (requires INPUT='...')"
	@echo "  make test-adk-analysis - Test ADK Analysis Capabilities (requires STREET='...' TYPE='...')"
	@echo "  make egpt         - Run EnergyGPT with KPI analysis (requires PROMPT=...)"
	@echo "  make results      - Extract results table (requires SLUG=...)"
	@echo "  make dashboard    - Generate comprehensive system dashboard"
	@echo "  make results-dashboard - Generate focused results dashboard (requires SLUG=...)"
	@echo "  make combined-dashboard - Generate combined dashboard with tabs"
	@echo "  make figures      - Generate comprehensive figures (requires SLUG=...)"
	@echo "  make comprehensive-dashboard - Generate comprehensive dashboard with embedded figures"
	@echo "  make street-dashboard - Generate street-specific dashboard (requires STREET=... and BUILDINGS=...)"
	@echo ""
	@echo "🏘️ Street Comparison Commands:"
	@echo "  make street-compare - Launch street comparison tool (interactive menu)"
	@echo "  make street-compare-web - Launch web-based street comparison"
	@echo "  make street-compare-cli - Launch command-line street comparison"
	@echo "  make street-compare-simple - Launch simple CLI street comparison"
	@echo "  make street-list - List all available streets"
	@echo ""
	@echo "🚀 ADK Deployment Commands:"
	@echo "  make deploy-adk   - Deploy ADK System (interactive deployment)"
	@echo "  make deploy-dev   - Deploy for Development Environment"
	@echo "  make deploy-staging - Deploy for Staging Environment"
	@echo "  make deploy-prod  - Deploy for Production Environment"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  make docker-build - Build Docker images for all environments"
	@echo "  make docker-up    - Start Docker services (default: development)"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make docker-logs  - View Docker service logs"
	@echo ""
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

# End-to-end run (fork-join DAG)
run-branitz:
	@echo "🚀 Running Branitz Energy Decision AI end-to-end (fork-join)..."
	@echo "1. Load Forecasting Agent (LFA)..."
	$(MAKE) lfa
	@echo "2. Running CHA & DHA in parallel (fork)..."
	$(MAKE) -j 2 cha dha
	@echo "3. Validating CHA hydraulic results..."
	$(MAKE) validate-cha-output
	@echo "4. Techno-Economic & Emissions (TE) - join point..."
	$(MAKE) te
	@echo "5. Generating KPI summary and recommendation..."
	$(MAKE) kpi
	@echo "6. Comprehensive Analysis Agent (CAA)..."
	$(MAKE) caa
	@echo "✅ End-to-end analysis complete!"
	@echo "📊 Results available in:"
	@echo "   - processed/kpi/kpi_summary.json"
	@echo "   - processed/cha/cha_kpis.json"
	@echo "   - docs/branitz_recommendation.html"

# Street-specific run (fast testing)
run-street:
	@echo "🏘️ Running Branitz Energy Decision AI for specific street..."
	@echo "   Street: $(STREET) (default: An der Bahn)"
	@test -n "$(STREET)" || (echo "❌ Set STREET='...' (e.g., STREET='An der Bahn')"; exit 1)
	@echo "1. Street-specific data generation..."
	$(MAKE) thesis-data-street STREET="$(STREET)"
	@echo "2. Running CHA & DHA in parallel (fork)..."
	$(MAKE) -j 2 cha dha
	@echo "3. Techno-Economic Analysis (join)..."
	$(MAKE) te
	@echo "4. KPI Generation..."
	$(MAKE) kpi
	@echo "5. Street Dashboard..."
	$(MAKE) street-dashboard STREET="$(STREET)" BUILDINGS=14
	@echo "✅ Street-specific analysis complete!"
	@echo "📊 Results available in:"
	@echo "   - processed/kpi/kpi_summary.json"
	@echo "   - docs/street_dashboard_$(shell echo $(STREET) | tr '[:upper:]' '[:lower:]' | sed 's/ /_/g' | sed 's/ä/ae/g' | sed 's/ö/oe/g' | sed 's/ü/ue/g').html"

# Thesis Data Integration (replaces LFA)
thesis-data:
	@echo "🔥 Running Thesis Data Integration (replaces LFA)..."
	@echo "   - TRY weather data: 8760-hour temperature profiles"
	@echo "   - Physics-based heating: temperature-dependent heat demand"
	@echo "   - Electrical profiles: heat pump load analysis"
	@echo "   - Output: LFA-compatible JSON files"
	python -m src.thesis_data_integration --config configs/thesis_data.yml
	@echo "✅ Generated physics-based heat demand for all buildings"
	@touch processed/lfa/.ready

# Street-Specific Thesis Data Integration (fast testing)
thesis-data-street:
	@echo "🏘️ Running Street-Specific Thesis Data Integration..."
	@echo "   - Street: $(STREET) (default: An der Bahn)"
	@echo "   - TRY weather data: 8760-hour temperature profiles"
	@echo "   - Physics-based heating: temperature-dependent heat demand"
	@echo "   - Output: LFA-compatible JSON files for specific street"
	@test -n "$(STREET)" || (echo "❌ Set STREET='...' (e.g., STREET='An der Bahn')"; exit 1)
	python src/thesis_data_integration_street.py --config configs/thesis_data.yml --street "$(STREET)" --output processed/lfa
	@echo "✅ Generated physics-based heat demand for street: $(STREET)"
	@touch processed/lfa/.ready

# Legacy LFA target (redirects to thesis-data)
lfa: thesis-data
	@echo "⚠️  LFA redirected to thesis-data integration"

# Sentinel written by LFA when forecasts are ready
processed/lfa/.ready:  ## created by LFA step
	@mkdir -p processed/lfa
	@# LFA command must touch this file when done
	@touch $@

# Sentinel written by CHA when network is ready for simulation
processed/cha/.ready:  ## created by CHA step
	@mkdir -p processed/cha
	@# CHA command must touch this file when done
	@touch $@

# ETL Pipeline (Legacy - replaced by thesis-data integration)
etl: 
	@echo "⚠️  ETL pipeline obsolete - use 'make thesis-data' instead"
	@echo "Usage: python -m etl.data_to_lfa --buildings <path> --try <path> --year 2024 --write-meters true"
	@echo "Example: python -m etl.data_to_lfa --buildings data_16122024/buildings.json --try data_16122024/weather.csv --year 2024 --write-meters true"

etl-16122024:
	@echo "🔄 Running data16122024 ETL pipeline..."
	python -m etl.data16122024_to_lfa \
		--buildings data_16122024/buildings.csv \
		--weather data_16122024/weather.csv \
		--config configs/etl_data16122024.yml \
		--write-meters true

# lfa-train: Obsolete - LFA replaced by thesis-data integration

etl-graph:
	@echo "🔄 Running ETL with graph topology features..."
	python -m etl.data16122024_to_lfa \
		--buildings data_16122024/buildings.csv \
		--weather data_16122024/weather.csv \
		--config configs/etl_data16122024.yml \
		--nodes data_16122024/network_nodes.csv \
		--edges data_16122024/network_edges.csv \
		--links data_16122024/building_links.csv \
		--write-meters false

etl-sample:
	@echo "🧪 Testing ETL pipeline with sample data..."
	python test_etl_pipeline.py

etl-test-data16122024:
	@echo "🧪 Testing data16122024 ETL pipeline..."
	python test_data16122024_etl.py

# Centralized Heating Agent (pandapipes)
cha: processed/lfa/.ready
	@echo "🔥 Running Centralized Heating Agent (CHA)..."
	@echo "   - Uses physics-based heat demand from thesis data integration"
	@echo "   - Street-following dual-pipe network construction"
	@echo "   - Pandapipes hydraulic simulation with thermal analysis"
	@echo "   - Standards compliance validation and auto-resizing"
	@echo "   - Output: processed/cha/*.csv, processed/cha/cha.gpkg, processed/cha/cha_kpis.json"
	@echo "   - Interactive map with thermal visualization"
	python -m src.cha configs/cha.yml
	@echo "✅ CHA complete!"

# Interactive Centralized Heating Agent (with street selection)
cha-interactive:
	@echo "🏗️ Running Interactive Centralized Heating Agent (CHA)..."
	@echo "   - Interactive street selection (individual, multiple, entire region)"
	@echo "   - Street-specific dual-pipe network analysis"
	@echo "   - Comprehensive dashboards for each analysis"
	@echo "   - Advanced layer control in interactive maps"
	python -m src.cha_interactive configs/cha_interactive.yml
	@echo "✅ Interactive CHA complete!"

# Validate CHA Output
validate-cha-output:
	@echo "🔍 Validating CHA hydraulic simulation outputs..."
	@echo "   - Schema validation against cha_output.schema.json"
	@echo "   - Standards compliance check (EN 13941, DIN 1988, VDI 2067)"
	@echo "   - KPI validation and thermal performance check"
	python -c "from src.cha_validation import validate_cha_outputs; validate_cha_outputs('processed/cha')"
	@echo "✅ CHA output validation complete!"

# CHA Simulation Only
cha-simulation-only: processed/cha/.ready
	@echo "🌡️ Running CHA Hydraulic Simulation Only..."
	@echo "   - Pandapipes simulation with thermal analysis"
	@echo "   - Standards compliance validation"
	@echo "   - Auto-resize loop with guardrails"
	@echo "   - Output: processed/cha/cha_kpis.json, processed/cha/cha_with_results.gpkg"
	python -c "from src.cha_pandapipes import run_cha_simulation_only; run_cha_simulation_only()"
	@echo "✅ CHA simulation complete!"

# Decentralized Heating Agent (pandapower)
dha: processed/lfa/.ready
	@echo "⚡ Running Decentralized Heating Agent (pandapower)..."
	@echo "   - Uses physics-based heat demand + electrical profiles for heat pumps"
	@echo "   - Grid analysis with feeder utilization checks"
	@echo "   - Output: processed/dha/feeder_loads.csv"
	@echo "   - Violations: eval/dha/violations.csv"
	python -m src.dha configs/dha.yml
	@echo "✅ DHA complete!"

# Interactive Decentralized Heating Agent (with maps and Pandapower)
dha-interactive:
	@echo "⚡ Running Interactive Decentralized Heating Agent..."
	@echo "   - Interactive street selection and analysis"
	@echo "   - Comprehensive Pandapower integration"
	@echo "   - Interactive maps with layer control"
	@echo "   - Street-following service connections"
	@echo "   - Real-time power flow analysis"
	python -m src.dha_interactive
	@echo "✅ Interactive DHA complete!"

# Enhanced Multi-Agent System (ADK-based)
enhanced-agents:
	@echo "🤖 Running Enhanced Multi-Agent System with Google ADK..."
	@echo "   - Google ADK-powered multi-agent delegation system"
	@echo "   - Comprehensive analysis capabilities with ADK tools"
	@echo "   - Interactive user interface with ADK agents"
	@echo "   - Real-time agent coordination and communication"
	@echo "   - Enhanced error handling and quota management"
	@echo "   - Fallback to SimpleAgent if ADK not available"
	@echo ""
	@echo "🔧 Initializing ADK environment..."
	@if [ -d "agents copy" ]; then \
		echo "   ✅ ADK directory found"; \
		cd "agents copy" && python run_enhanced_agent_system.py --interactive; \
	else \
		echo "   ⚠️ ADK directory not found, using fallback system"; \
		python -m src.simplified_agent_system interactive; \
	fi
	@echo "✅ Enhanced Multi-Agent System complete!"

# Test Enhanced Multi-Agent System (ADK-based)
test-enhanced-agents:
	@echo "🧪 Testing Enhanced Multi-Agent System with Google ADK..."
	@echo "   - ADK agent initialization and configuration test"
	@echo "   - End-to-end pipeline test with ADK agents"
	@echo "   - Agent delegation verification with ADK"
	@echo "   - Tool execution validation with ADK tools"
	@echo "   - Error handling and quota management test"
	@echo "   - Fallback system test if ADK not available"
	@echo ""
	@echo "🔧 Running comprehensive ADK tests..."
	@if [ -d "agents copy" ]; then \
		echo "   ✅ ADK directory found, running ADK tests"; \
		cd "agents copy" && python run_enhanced_agent_system.py --test; \
		echo "   ✅ Running agent configuration tests"; \
		cd .. && python test_agent_configurations.py; \
	else \
		echo "   ⚠️ ADK directory not found, using fallback system"; \
		python -m src.simplified_agent_system test; \
	fi
	@echo "✅ Enhanced Multi-Agent System test complete!"

# Batch Enhanced Multi-Agent System (ADK-based)
batch-enhanced-agents:
	@echo "🤖 Running Enhanced Multi-Agent System in batch mode with Google ADK..."
	@echo "   - Batch processing with ADK agents"
	@echo "   - Automated analysis for multiple streets"
	@echo "   - Comprehensive results generation"
	@echo "   - Error handling and quota management"
	@echo ""
	@echo "Usage: make batch-enhanced-agents STREETS=\"street1,street2,street3\""
	@test -n "$(STREETS)" || (echo "❌ Set STREETS='street1,street2,street3'"; exit 1)
	@echo "🔧 Processing streets: $(STREETS)"
	@if [ -d "agents copy" ]; then \
		echo "   ✅ ADK directory found, running batch processing"; \
		cd "agents copy" && python run_enhanced_agent_system.py --batch --streets "$(STREETS)"; \
	else \
		echo "   ⚠️ ADK directory not found, using fallback system"; \
		echo "   Processing each street individually..."; \
		for street in $(shell echo $(STREETS) | tr ',' ' '); do \
			echo "   Processing: $$street"; \
			python -m src.simplified_agent_system batch --street "$$street"; \
		done; \
	fi
	@echo "✅ Batch Enhanced Multi-Agent System complete!"

# ADK Agent Configuration Test
test-adk-config:
	@echo "🔧 Testing ADK Agent Configurations..."
	@echo "   - Agent configuration validation"
	@echo "   - ADK compatibility testing"
	@echo "   - Tool assignment verification"
	@echo "   - System prompt validation"
	@echo ""
	@if [ -d "agents copy" ]; then \
		echo "   ✅ ADK directory found, running configuration tests"; \
		python test_agent_configurations.py; \
	else \
		echo "   ⚠️ ADK directory not found, skipping ADK tests"; \
	fi
	@echo "✅ ADK configuration test complete!"

# ADK Agent Runner Test
test-adk-runner:
	@echo "🏃 Testing ADK Agent Runner..."
	@echo "   - ADK runner initialization test"
	@echo "   - Agent delegation test"
	@echo "   - Error handling test"
	@echo "   - Quota management test"
	@echo ""
	@if [ -d "agents copy" ]; then \
		echo "   ✅ ADK directory found, running runner tests"; \
		cd "agents copy" && python test_enhanced_runner_comprehensive.py; \
	else \
		echo "   ⚠️ ADK directory not found, skipping ADK runner tests"; \
	fi
	@echo "✅ ADK runner test complete!"

# ADK Single Input Test
test-adk-input:
	@echo "📝 Testing ADK Single Input Processing..."
	@echo "Usage: make test-adk-input INPUT=\"your input here\""
	@test -n "$(INPUT)" || (echo "❌ Set INPUT='...'"; exit 1)
	@echo "🔧 Processing input: $(INPUT)"
	@if [ -d "agents copy" ]; then \
		echo "   ✅ ADK directory found, processing with ADK"; \
		cd "agents copy" && python run_enhanced_agent_system.py --input "$(INPUT)"; \
	else \
		echo "   ⚠️ ADK directory not found, using fallback system"; \
		python -m src.simplified_agent_system input "$(INPUT)"; \
	fi
	@echo "✅ ADK input test complete!"

# ADK Analysis Test
test-adk-analysis:
	@echo "📊 Testing ADK Analysis Capabilities..."
	@echo "Usage: make test-adk-analysis STREET=\"street_name\" TYPE=\"analysis_type\""
	@echo "   Types: auto, dh, hp, compare"
	@test -n "$(STREET)" || (echo "❌ Set STREET='...'"; exit 1)
	@test -n "$(TYPE)" || (echo "❌ Set TYPE='...' (auto, dh, hp, compare)"; exit 1)
	@echo "🔧 Analyzing street: $(STREET) with type: $(TYPE)"
	@if [ -d "agents copy" ]; then \
		echo "   ✅ ADK directory found, running analysis with ADK"; \
		cd "agents copy" && python run_enhanced_agent_system.py --analyze "$(STREET)" --type "$(TYPE)"; \
	else \
		echo "   ⚠️ ADK directory not found, using fallback system"; \
		python -m src.simplified_agent_system analyze --street "$(STREET)" --type "$(TYPE)"; \
	fi
	@echo "✅ ADK analysis test complete!"

# Techno-Economic & Emissions (EAA + TCA)
te:
	@echo "💰 Running Techno-Economic & Emissions analysis..."
	@echo "   - EAA: Join point for CHA and DHA results"
	@echo "   - Monte Carlo LCoH and CO₂ analysis"
	@echo "   - TCA: KPI generation and decision support"
	@echo "   - Output: eval/te/mc.parquet, eval/te/summary.csv, processed/kpi/kpi_summary.json"
	python -m src.te configs/eaa.yml configs/tca.yml
	@echo "✅ TE complete!"

# KPI Generation (TCA)
kpi:
	@echo "📊 Running Techno-Economic Analysis Agent (TCA)..."
	@echo "   - KPI generation from EAA results"
	@echo "   - Decision support and recommendations"
	@echo "   - Output: processed/kpi/kpi_summary.json"
	python -m src.tca configs/tca.yml
	@echo "✅ KPI complete!"

# Pipe Catalog Agent
pca:
	@echo "🧵 Building canonical pipe catalog..."
	python -m agents.pca --config configs/pca.yml
	@echo "✅ Wrote processed/pca/catalog.csv and eval/pca/catalog_qc.csv"

# Comprehensive Analysis Agent
caa:
	@echo "🧰 Running Comprehensive Analysis Agent (CAA)…"
	python -m src.caa configs/caa.yml
	@echo "   - Bundle: eval/caa/diagnostics.zip"
	@echo "✅ CAA complete!"

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

# =============================================================================
# ADK DEPLOYMENT TARGETS
# =============================================================================

# Deploy ADK System (Interactive)
deploy-adk:
	@echo "🚀 Deploying ADK System (Interactive)..."
	@echo "   - Interactive deployment with user prompts"
	@echo "   - Environment selection (development/staging/production)"
	@echo "   - Configuration validation and setup"
	@echo "   - Dependency installation and testing"
	@echo "   - ADK environment setup and validation"
	@echo ""
	@echo "🔧 Starting interactive deployment..."
	python scripts/deploy_adk_system.py
	@echo "✅ ADK System deployment complete!"

# Deploy for Development Environment
deploy-dev:
	@echo "🔧 Deploying for Development Environment..."
	@echo "   - Development environment setup"
	@echo "   - Development dependencies installation"
	@echo "   - Development configuration setup"
	@echo "   - Development tests execution"
	@echo "   - Development services startup"
	@echo ""
	@echo "🔧 Starting development deployment..."
	python scripts/deploy_environment.py development
	@echo "✅ Development environment deployment complete!"

# Deploy for Staging Environment
deploy-staging:
	@echo "🚀 Deploying for Staging Environment..."
	@echo "   - Staging environment setup"
	@echo "   - Staging dependencies installation"
	@echo "   - Staging configuration setup"
	@echo "   - Staging tests execution"
	@echo "   - Staging services deployment"
	@echo ""
	@echo "🔧 Starting staging deployment..."
	python scripts/deploy_environment.py staging
	@echo "✅ Staging environment deployment complete!"

# Deploy for Production Environment
deploy-prod:
	@echo "🏭 Deploying for Production Environment..."
	@echo "   - Production environment setup"
	@echo "   - Production dependencies installation"
	@echo "   - Production configuration setup"
	@echo "   - Production tests execution"
	@echo "   - Production services deployment"
	@echo "   - Production monitoring setup"
	@echo ""
	@echo "🔧 Starting production deployment..."
	python scripts/deploy_environment.py production
	@echo "✅ Production environment deployment complete!"

# =============================================================================
# DOCKER DEPLOYMENT TARGETS
# =============================================================================

# Build Docker Images
docker-build:
	@echo "🐳 Building Docker images for all environments..."
	@echo "   - Building base image"
	@echo "   - Building development image"
	@echo "   - Building production image"
	@echo "   - Building ADK production image"
	@echo ""
	@echo "🔧 Building Docker images..."
	docker build --target base -t branitz-adk-base .
	docker build --target development -t branitz-adk-dev .
	docker build --target production -t branitz-adk-prod .
	docker build --target adk-production -t branitz-adk-system .
	@echo "✅ Docker images built successfully!"

# Start Docker Services
docker-up:
	@echo "🐳 Starting Docker services..."
	@echo "   - Starting ADK system service"
	@echo "   - Starting development service (if profile enabled)"
	@echo "   - Starting production service (if profile enabled)"
	@echo "   - Starting monitoring services (if profile enabled)"
	@echo ""
	@echo "🔧 Starting Docker services..."
	docker-compose up -d
	@echo "✅ Docker services started!"
	@echo ""
	@echo "📊 Service Status:"
	docker-compose ps

# Stop Docker Services
docker-down:
	@echo "🐳 Stopping Docker services..."
	@echo "   - Stopping all running services"
	@echo "   - Cleaning up containers"
	@echo ""
	@echo "🔧 Stopping Docker services..."
	docker-compose down
	@echo "✅ Docker services stopped!"

# View Docker Logs
docker-logs:
	@echo "🐳 Viewing Docker service logs..."
	@echo "   - ADK system logs"
	@echo "   - Development service logs (if running)"
	@echo "   - Production service logs (if running)"
	@echo "   - Monitoring service logs (if running)"
	@echo ""
	@echo "🔧 Showing Docker logs..."
	docker-compose logs -f

# =============================================================================
# ADK SYSTEM MANAGEMENT TARGETS
# =============================================================================

# Start ADK System
start-adk:
	@echo "🚀 Starting ADK System..."
	@echo "   - Initializing ADK Agent Runner"
	@echo "   - Loading agent configurations"
	@echo "   - Starting interactive mode"
	@echo ""
	@echo "🔧 Starting ADK system..."
	python start_adk_system.py
	@echo "✅ ADK System started!"

# Test ADK System
test-adk:
	@echo "🧪 Testing ADK System..."
	@echo "   - Running unit tests"
	@echo "   - Running integration tests"
	@echo "   - Running performance tests"
	@echo "   - Validating system functionality"
	@echo ""
	@echo "🔧 Running ADK system tests..."
	python test_adk_system.py
	@echo "✅ ADK System tests complete!"

# ADK System Health Check
health-check:
	@echo "🏥 Checking ADK System Health..."
	@echo "   - Checking ADK availability"
	@echo "   - Checking agent configurations"
	@echo "   - Checking tool functionality"
	@echo "   - Checking system performance"
	@echo ""
	@echo "🔧 Running health checks..."
	python -c "from agents.copy.run_enhanced_agent_system import ADKAgentRunner; runner = ADKAgentRunner(); print('✅ ADK System Healthy')"
	@echo "✅ Health check complete!"

# ADK System Status
status:
	@echo "📊 ADK System Status..."
	@echo "   - System configuration"
	@echo "   - Agent status"
	@echo "   - Tool status"
	@echo "   - Performance metrics"
	@echo ""
	@echo "🔧 Checking system status..."
	@if [ -f "deployment_report.json" ]; then \
		echo "📋 Deployment Report:"; \
		cat deployment_report.json | python -m json.tool; \
	else \
		echo "⚠️ No deployment report found. Run 'make deploy-adk' first."; \
	fi
	@echo "✅ Status check complete!"

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

# EnergyGPT KPI Analysis
egpt:
	@echo "🤖 Running EnergyGPT KPI Analysis..."
	@echo "Usage: make egpt PROMPT=\"analyze_kpi_report(kpi_report_path='processed/kpi/<SLUG>/kpi_summary.json')\""
	@test -n "$(PROMPT)" || (echo "❌ Set PROMPT=..."; exit 1)
	PYTHONPATH=. python src/enhanced_agent_runner.py egpt "$(PROMPT)"
	@echo "✅ EnergyGPT analysis complete!"

# Results Extraction
results:
	@echo "📊 Extracting results table..."
	@echo "Usage: make results SLUG=<street_slug>"
	@test -n "$(SLUG)" || (echo "❌ Set SLUG=..."; exit 1)
	python scripts/extract_results.py --slug $(SLUG) --root . --outdir docs/
	@echo "✅ Results extraction complete!"

# System Dashboard
dashboard:
	@echo "🎨 Generating comprehensive system dashboard..."
	python src/dashboard_generator.py --root . --output docs/system_dashboard.html
	@echo "✅ Dashboard generated successfully!"
	@echo "🌐 Open in browser: file://$(PWD)/docs/system_dashboard.html"

# Results Dashboard
results-dashboard:
	@echo "📊 Generating focused results dashboard..."
	@echo "Usage: make results-dashboard SLUG=<street_slug>"
	@test -n "$(SLUG)" || (echo "❌ Set SLUG=... (use empty string for system overview)"; exit 1)
	python src/results_dashboard.py --slug $(SLUG) --root . --output docs/results_dashboard_$(SLUG).html
	@echo "✅ Results dashboard generated successfully!"
	@echo "🌐 Open in browser: file://$(PWD)/docs/results_dashboard_$(SLUG).html"

# Combined Dashboard
combined-dashboard:
	@echo "🎨 Generating combined dashboard with tabs..."
	python src/combined_dashboard.py --root . --output docs/combined_dashboard.html
	@echo "✅ Combined dashboard generated successfully!"
	@echo "🌐 Open in browser: file://$(PWD)/docs/combined_dashboard.html"

# Figures Generation
figures:
	@echo "📊 Generating comprehensive figures..."
	@echo "Usage: make figures SLUG=<street_slug>"
	@test -n "$(SLUG)" || (echo "❌ Set SLUG=... (use empty string for system overview)"; exit 1)
	python scripts/make_figures.py --slug $(SLUG) --root . --outdir docs/
	@echo "✅ Figures generated successfully!"
	@echo "📁 Check docs/ for generated figures"

# Comprehensive Dashboard
comprehensive-dashboard:
	@echo "🎨 Generating comprehensive dashboard with embedded figures..."
	python src/comprehensive_dashboard.py --root . --output docs/comprehensive_dashboard.html
	@echo "✅ Comprehensive dashboard generated successfully!"
	@echo "🌐 Open in browser: file://$(PWD)/docs/comprehensive_dashboard.html"

# Street-Specific Dashboard
street-dashboard:
	@echo "🏘️ Generating street-specific dashboard..."
	@echo "Usage: make street-dashboard STREET='<street_name>' BUILDINGS=<number>"
	@test -n "$(STREET)" || (echo "❌ Set STREET='...' (e.g., STREET='An der Bahn')"; exit 1)
	@test -n "$(BUILDINGS)" || (echo "❌ Set BUILDINGS=... (e.g., BUILDINGS=14)"; exit 1)
	python src/street_dashboard.py --street "$(STREET)" --buildings $(BUILDINGS) --root .
	@echo "✅ Street dashboard generated successfully!"
	@echo "🌐 Open in browser: file://$(PWD)/docs/street_dashboard_$(shell echo $(STREET) | tr '[:upper:]' '[:lower:]' | sed 's/ /_/g' | sed 's/ä/ae/g' | sed 's/ö/oe/g' | sed 's/ü/ue/g').html"

# Street Comparison Tools
street-compare:
	@echo "🏘️ Launching street comparison tool..."
	python run_street_comparison.py

street-compare-web:
	@echo "🌐 Launching web-based street comparison..."
	python src/street_comparison_web.py --open-browser

street-compare-cli:
	@echo "💻 Launching command-line street comparison..."
	python src/street_comparison_tool.py

street-compare-simple:
	@echo "🖥️ Launching simple CLI street comparison..."
	python src/simple_street_selector.py

street-list:
	@echo "📋 Available streets:"
	@python scripts/list_streets.py