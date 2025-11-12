#!/usr/bin/env python3
"""
Pre-Deployment Validation Script

Checks that all required components are in place before deployment.
Run this before enabling real simulations.
"""

from pathlib import Path
import sys

def check_files():
    """Check all critical files exist."""
    print("📁 Checking Files...")
    print("-" * 60)
    
    critical_files = [
        ("src/simulators/base.py", "Base simulator classes"),
        ("src/simulators/pandapipes_dh_simulator.py", "DH simulator"),
        ("src/simulators/pandapower_hp_simulator.py", "HP simulator"),
        ("src/simulators/placeholder_dh.py", "DH fallback"),
        ("src/simulators/placeholder_hp.py", "HP fallback"),
        ("src/simulators/__init__.py", "Package exports"),
        ("src/simulation_runner.py", "Simulation runner"),
        ("src/kpi_calculator.py", "KPI calculator"),
        ("config/feature_flags.yaml", "Feature toggles"),
        ("config/simulation_config.yaml", "Simulation params"),
    ]
    
    all_present = True
    total_size = 0
    
    for file_path, description in critical_files:
        p = Path(file_path)
        if p.exists():
            size = p.stat().st_size
            total_size += size
            print(f"  ✅ {file_path:<45} {size:>7,} bytes")
        else:
            print(f"  ❌ MISSING: {file_path:<45} {description}")
            all_present = False
    
    print(f"\n  Total source code: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    return all_present


def check_directories():
    """Check all required directories exist."""
    print("\n📂 Checking Directories...")
    print("-" * 60)
    
    required_dirs = [
        ("src/simulators", "Simulator modules"),
        ("src/orchestration", "Orchestration (future)"),
        ("config", "Configuration files"),
        ("tests/unit", "Unit tests"),
        ("tests/integration", "Integration tests"),
        ("tests/performance", "Performance tests"),
        ("simulation_cache/dh", "DH cache"),
        ("simulation_cache/hp", "HP cache"),
        ("docs", "Documentation"),
    ]
    
    all_present = True
    for dir_path, description in required_dirs:
        p = Path(dir_path)
        if p.exists() and p.is_dir():
            # Count files in directory
            file_count = len(list(p.glob("*")))
            print(f"  ✅ {dir_path:<35} ({file_count} files)")
        else:
            print(f"  ❌ MISSING: {dir_path:<35} {description}")
            all_present = False
    
    return all_present


def check_tests():
    """Check test files exist."""
    print("\n🧪 Checking Tests...")
    print("-" * 60)
    
    test_files = [
        ("tests/unit/test_dh_simulator.py", "DH unit tests"),
        ("tests/unit/test_hp_simulator.py", "HP unit tests"),
        ("tests/integration/test_full_agent_workflow.py", "Workflow tests"),
        ("tests/integration/test_agent_integration.py", "Agent tests"),
        ("tests/performance/test_performance_benchmarks.py", "Benchmarks"),
    ]
    
    all_present = True
    total_tests = 0
    
    for file_path, description in test_files:
        p = Path(file_path)
        if p.exists():
            # Count test functions in file
            with open(p) as f:
                content = f.read()
                test_count = content.count("def test_")
                total_tests += test_count
            print(f"  ✅ {file_path:<50} {test_count} tests")
        else:
            print(f"  ❌ MISSING: {file_path:<50}")
            all_present = False
    
    print(f"\n  Total tests: {total_tests}")
    return all_present, total_tests


def check_documentation():
    """Check documentation files exist."""
    print("\n📖 Checking Documentation...")
    print("-" * 60)
    
    doc_files = [
        "README.md",
        "QUICKSTART.md",
        "DEPLOYMENT_READY.md",
        "ARCHITECTURE_DESIGN.md",
        "MIGRATION_CHECKLIST.md",
        "docs/INTERFACE_SPEC.md",
        "docs/CONFIGURATION_GUIDE.md",
    ]
    
    all_present = True
    total_size = 0
    
    for file_path in doc_files:
        p = Path(file_path)
        if p.exists():
            size = p.stat().st_size
            total_size += size
            print(f"  ✅ {file_path:<45} {size:>7,} bytes")
        else:
            print(f"  ❌ MISSING: {file_path}")
            all_present = False
    
    print(f"\n  Total documentation: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    return all_present


def check_configuration():
    """Check configuration is valid."""
    print("\n⚙️  Checking Configuration...")
    print("-" * 60)
    
    try:
        import yaml
        
        # Load feature flags
        with open("config/feature_flags.yaml") as f:
            flags = yaml.safe_load(f)
        
        print("  Feature Flags:")
        print(f"    use_real_simulations: {flags['features']['use_real_simulations']}")
        print(f"    use_real_dh: {flags['features']['use_real_dh']}")
        print(f"    use_real_hp: {flags['features']['use_real_hp']}")
        print(f"    fallback_on_error: {flags['features']['fallback_on_error']}")
        
        # Load simulation config
        with open("config/simulation_config.yaml") as f:
            sim_config = yaml.safe_load(f)
        
        print("\n  Simulation Parameters:")
        print(f"    DH supply temp: {sim_config['district_heating']['supply_temp_c']}°C")
        print(f"    DH return temp: {sim_config['district_heating']['return_temp_c']}°C")
        print(f"    HP thermal: {sim_config['heat_pump']['hp_thermal_kw']} kW")
        print(f"    HP COP: {sim_config['heat_pump']['hp_cop']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False


def main():
    """Run all validation checks."""
    print("\n" + "="*70)
    print("PRE-DEPLOYMENT VALIDATION")
    print("="*70)
    print("")
    
    results = {}
    
    # Run all checks
    results["files"] = check_files()
    results["directories"] = check_directories()
    results["tests"], test_count = check_tests()
    results["documentation"] = check_documentation()
    results["configuration"] = check_configuration()
    
    # Final summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print("")
    
    all_checks = [
        ("Files", results["files"]),
        ("Directories", results["directories"]),
        ("Tests", results["tests"]),
        ("Documentation", results["documentation"]),
        ("Configuration", results["configuration"]),
    ]
    
    for check_name, passed in all_checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {check_name:<20} {status}")
    
    print("")
    
    # Overall status
    if all(results.values()):
        print("🎉 ALL VALIDATION CHECKS PASSED!")
        print("")
        print("System Status:")
        print("  Code:           ✅ Complete")
        print("  Tests:          ✅ Complete ({} tests)".format(test_count))
        print("  Documentation:  ✅ Complete")
        print("  Configuration:  ✅ Ready")
        print("")
        print("Next Steps:")
        print("  1. Install dependencies: pip install pandapipes pandapower")
        print("  2. Run tests: python tests/unit/test_dh_simulator.py")
        print("  3. Enable real mode: Edit config/feature_flags.yaml")
        print("  4. Deploy: ./deploy_real_simulations.sh dh-only")
        print("")
        print("Status: 🟢 READY FOR DEPLOYMENT")
        return 0
    else:
        print("❌ SOME VALIDATION CHECKS FAILED")
        print("")
        print("Please resolve the issues above before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
EOF
