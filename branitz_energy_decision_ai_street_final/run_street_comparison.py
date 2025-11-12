#!/usr/bin/env python3
"""
Street Comparison Launcher
Simple launcher for different street comparison interfaces
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    
    print("🔍 Checking dependencies...")
    
    # Check if we're in the right directory
    if not Path("processed/kpi").exists():
        print("❌ No KPI data found. Please run the analysis first.")
        return False
    
    # Check Python packages
    try:
        import json
        print("✅ JSON module available")
    except ImportError:
        print("❌ JSON module not available")
        return False
    
    # Check for optional dependencies
    try:
        import streamlit
        print("✅ Streamlit available (for web interface)")
    except ImportError:
        print("⚠️ Streamlit not available (web interface disabled)")
    
    return True

def show_menu():
    """Show the main menu"""
    
    print("\n🏘️ Street Comparison Tool")
    print("=" * 40)
    print("Choose an interface:")
    print()
    print("1. 📱 Web Interface (Recommended)")
    print("2. 💻 Command Line Interface")
    print("3. 🖥️  Simple CLI Tool")
    print("4. 📊 List Available Streets")
    print("5. ❓ Help")
    print("6. 🚪 Exit")
    print()

def run_web_interface():
    """Run the web interface"""
    
    try:
        import streamlit as st
        print("🚀 Starting Streamlit web interface...")
        print("📱 The interface will open in your browser")
        print("🛑 Press Ctrl+C to stop")
        
        # Run streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/street_comparison_tool.py",
            "--server.port", "8501",
            "--server.headless", "true"
        ])
        
    except ImportError:
        print("❌ Streamlit not available. Trying simple web server...")
        run_simple_web_server()

def run_simple_web_server():
    """Run the simple web server"""
    
    print("🚀 Starting simple web server...")
    print("📱 Open your browser and go to: http://localhost:8080")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        subprocess.run([sys.executable, "src/street_comparison_web.py", "--open-browser"])
    except KeyboardInterrupt:
        print("\n👋 Web server stopped!")

def run_cli_interface():
    """Run the command line interface"""
    
    print("🚀 Starting command line interface...")
    print("🛑 Press Ctrl+C to exit")
    
    try:
        subprocess.run([sys.executable, "src/street_comparison_tool.py"])
    except KeyboardInterrupt:
        print("\n👋 CLI stopped!")

def run_simple_cli():
    """Run the simple CLI tool"""
    
    print("🚀 Starting simple CLI tool...")
    print("🛑 Press Ctrl+C to exit")
    
    try:
        subprocess.run([sys.executable, "src/simple_street_selector.py"])
    except KeyboardInterrupt:
        print("\n👋 Simple CLI stopped!")

def list_streets():
    """List available streets"""
    
    print("📋 Available Streets:")
    print("=" * 30)
    
    kpi_dir = Path("processed/kpi")
    if not kpi_dir.exists():
        print("❌ No KPI data found")
        return
    
    streets = []
    for kpi_file in kpi_dir.glob("kpi_report_*.json"):
        if kpi_file.name != "kpi_summary.json":
            street_name = kpi_file.stem.replace("kpi_report_", "")
            if street_name:
                streets.append(street_name)
    
    if not streets:
        print("❌ No street data available")
        return
    
    for i, street in enumerate(sorted(streets), 1):
        print(f"  {i}. {street}")
    
    print(f"\nTotal: {len(streets)} streets available")

def show_help():
    """Show help information"""
    
    print("\n❓ Help - Street Comparison Tool")
    print("=" * 40)
    print()
    print("This tool allows you to compare District Heating (DH) vs")
    print("Heat Pump (HP) KPIs for different streets.")
    print()
    print("Available interfaces:")
    print()
    print("📱 Web Interface:")
    print("  - Interactive web-based interface")
    print("  - Visual charts and comparisons")
    print("  - Easy to use")
    print()
    print("💻 Command Line Interface:")
    print("  - Full-featured CLI with charts")
    print("  - Good for detailed analysis")
    print()
    print("🖥️  Simple CLI Tool:")
    print("  - Basic command-line interface")
    print("  - Quick comparisons")
    print("  - No external dependencies")
    print()
    print("📊 List Available Streets:")
    print("  - Shows all streets with available data")
    print()
    print("The tool compares these metrics:")
    print("  - LCOH (Levelized Cost of Heat)")
    print("  - CO2 Emissions")
    print("  - CAPEX (Capital Expenditure)")
    print("  - OPEX (Operational Expenditure)")
    print("  - Energy Costs")
    print()
    print("For more information, see the documentation.")

def main():
    """Main function"""
    
    print("🏘️ Street Comparison Tool Launcher")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependencies check failed. Please install required packages.")
        return
    
    # Main menu loop
    while True:
        show_menu()
        
        try:
            choice = input("Enter your choice (1-6): ").strip()
            
            if choice == '1':
                run_web_interface()
            elif choice == '2':
                run_cli_interface()
            elif choice == '3':
                run_simple_cli()
            elif choice == '4':
                list_streets()
            elif choice == '5':
                show_help()
            elif choice == '6':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-6.")
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
