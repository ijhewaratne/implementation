#!/usr/bin/env python3
"""
ADK System Deployment Script
Comprehensive deployment script for the Enhanced Multi-Agent System with Google ADK
"""

import os
import sys
import subprocess
import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ADKSystemDeployer:
    """ADK System Deployment Manager."""
    
    def __init__(self, config_path: str = "configs/deployment_config.yml"):
        """Initialize the ADK System Deployer."""
        self.config_path = config_path
        self.config = self._load_config()
        self.project_root = Path.cwd()
        self.venv_path = self.project_root / "venv"
        self.requirements_path = self.project_root / "requirements.txt"
        
    def _load_config(self) -> Dict:
        """Load deployment configuration."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default configuration
            return {
                "environment": "development",
                "adk_enabled": True,
                "fallback_enabled": True,
                "python_version": "3.9",
                "install_dependencies": True,
                "run_tests": True,
                "validate_config": True,
                "create_venv": True,
                "backup_existing": True
            }
    
    def _run_command(self, command: str, cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """Run a shell command and return success status and output."""
        try:
            logger.info(f"Running command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Command successful: {command}")
                return True, result.stdout
            else:
                logger.error(f"Command failed: {command}")
                logger.error(f"Error output: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return False, "Command timed out"
        except Exception as e:
            logger.error(f"Command exception: {command} - {e}")
            return False, str(e)
    
    def check_prerequisites(self) -> bool:
        """Check system prerequisites."""
        logger.info("🔍 Checking system prerequisites...")
        
        # Check Python version
        python_version = sys.version_info
        required_version = (3, 8)
        if python_version < required_version:
            logger.error(f"Python {required_version[0]}.{required_version[1]}+ required, found {python_version.major}.{python_version.minor}")
            return False
        
        logger.info(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check required commands
        required_commands = ["pip", "git"]
        for cmd in required_commands:
            success, _ = self._run_command(f"which {cmd}")
            if not success:
                logger.error(f"Required command not found: {cmd}")
                return False
            logger.info(f"✅ {cmd} found")
        
        # Check available memory
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.total < 4 * 1024**3:  # 4GB
                logger.warning(f"Low memory detected: {memory.total / 1024**3:.1f}GB (4GB+ recommended)")
            else:
                logger.info(f"✅ Memory: {memory.total / 1024**3:.1f}GB")
        except ImportError:
            logger.warning("psutil not available, cannot check memory")
        
        # Check disk space
        disk_usage = shutil.disk_usage(self.project_root)
        free_gb = disk_usage.free / 1024**3
        if free_gb < 2:  # 2GB
            logger.warning(f"Low disk space: {free_gb:.1f}GB (2GB+ recommended)")
        else:
            logger.info(f"✅ Disk space: {free_gb:.1f}GB free")
        
        return True
    
    def create_virtual_environment(self) -> bool:
        """Create virtual environment."""
        if not self.config.get("create_venv", True):
            logger.info("Skipping virtual environment creation")
            return True
        
        logger.info("🐍 Creating virtual environment...")
        
        # Remove existing venv if backup is enabled
        if self.config.get("backup_existing", True) and self.venv_path.exists():
            backup_path = self.project_root / f"venv_backup_{int(time.time())}"
            logger.info(f"Backing up existing venv to {backup_path}")
            shutil.move(str(self.venv_path), str(backup_path))
        
        # Create new virtual environment
        success, output = self._run_command(f"python -m venv {self.venv_path}")
        if not success:
            logger.error(f"Failed to create virtual environment: {output}")
            return False
        
        logger.info("✅ Virtual environment created")
        return True
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies."""
        if not self.config.get("install_dependencies", True):
            logger.info("Skipping dependency installation")
            return True
        
        logger.info("📦 Installing dependencies...")
        
        # Determine pip command based on environment
        if self.venv_path.exists():
            pip_cmd = str(self.venv_path / "bin" / "pip")
            if os.name == 'nt':  # Windows
                pip_cmd = str(self.venv_path / "Scripts" / "pip.exe")
        else:
            pip_cmd = "pip"
        
        # Upgrade pip first
        success, _ = self._run_command(f"{pip_cmd} install --upgrade pip")
        if not success:
            logger.warning("Failed to upgrade pip, continuing...")
        
        # Install requirements
        if self.requirements_path.exists():
            success, output = self._run_command(f"{pip_cmd} install -r {self.requirements_path}")
            if not success:
                logger.error(f"Failed to install requirements: {output}")
                return False
            logger.info("✅ Dependencies installed from requirements.txt")
        else:
            logger.error("requirements.txt not found")
            return False
        
        # Install ADK-specific dependencies if ADK is enabled
        if self.config.get("adk_enabled", True):
            logger.info("🤖 Installing ADK-specific dependencies...")
            adk_deps = [
                "adk>=0.1.0",
                "google-generativeai>=0.3.0",
                "google-cloud-aiplatform>=1.38.0",
                "google-auth>=2.23.0"
            ]
            
            for dep in adk_deps:
                success, output = self._run_command(f"{pip_cmd} install {dep}")
                if not success:
                    logger.warning(f"Failed to install {dep}: {output}")
        
        logger.info("✅ All dependencies installed")
        return True
    
    def validate_configuration(self) -> bool:
        """Validate system configuration."""
        if not self.config.get("validate_config", True):
            logger.info("Skipping configuration validation")
            return True
        
        logger.info("⚙️ Validating configuration...")
        
        # Check configuration files
        config_files = [
            "configs/gemini_config.yml",
            "configs/cha.yml",
            "configs/cha_intelligent_sizing.yml"
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        yaml.safe_load(f)
                    logger.info(f"✅ Configuration valid: {config_file}")
                except yaml.YAMLError as e:
                    logger.error(f"Invalid YAML in {config_file}: {e}")
                    return False
            else:
                logger.warning(f"Configuration file not found: {config_file}")
        
        # Check API key configuration
        gemini_config_path = self.project_root / "configs/gemini_config.yml"
        if gemini_config_path.exists():
            with open(gemini_config_path, 'r') as f:
                gemini_config = yaml.safe_load(f)
            
            if not gemini_config.get("api_key"):
                logger.warning("Gemini API key not configured")
                if not os.getenv("GEMINI_API_KEY"):
                    logger.warning("GEMINI_API_KEY environment variable not set")
            else:
                logger.info("✅ Gemini API key configured")
        
        logger.info("✅ Configuration validation complete")
        return True
    
    def run_tests(self) -> bool:
        """Run system tests."""
        if not self.config.get("run_tests", True):
            logger.info("Skipping tests")
            return True
        
        logger.info("🧪 Running system tests...")
        
        # Determine python command based on environment
        if self.venv_path.exists():
            python_cmd = str(self.venv_path / "bin" / "python")
            if os.name == 'nt':  # Windows
                python_cmd = str(self.venv_path / "Scripts" / "python.exe")
        else:
            python_cmd = "python"
        
        # Run unit tests
        test_commands = [
            f"{python_cmd} -m pytest tests/test_adk_agents_unit.py -v",
            f"{python_cmd} -m pytest tests/test_adk_tools_unit.py -v",
            f"{python_cmd} -m pytest tests/test_adk_integration.py -v"
        ]
        
        for test_cmd in test_commands:
            success, output = self._run_command(test_cmd)
            if not success:
                logger.error(f"Test failed: {test_cmd}")
                logger.error(f"Output: {output}")
                return False
            logger.info(f"✅ Test passed: {test_cmd}")
        
        logger.info("✅ All tests passed")
        return True
    
    def setup_adk_environment(self) -> bool:
        """Setup ADK-specific environment."""
        if not self.config.get("adk_enabled", True):
            logger.info("ADK disabled, skipping ADK setup")
            return True
        
        logger.info("🤖 Setting up ADK environment...")
        
        # Create ADK directory structure
        adk_dirs = [
            "agents copy/adk",
            "agents copy/configs",
            "processed/cha",
            "processed/dha",
            "processed/kpi",
            "processed/comparison"
        ]
        
        for dir_path in adk_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {dir_path}")
        
        # Copy ADK configuration if it doesn't exist
        adk_config_src = self.project_root / "configs/gemini_config.yml"
        adk_config_dst = self.project_root / "agents copy/configs/gemini_config.yml"
        
        if adk_config_src.exists() and not adk_config_dst.exists():
            shutil.copy2(adk_config_src, adk_config_dst)
            logger.info("✅ Copied ADK configuration")
        
        # Set up environment variables
        env_vars = {
            "GEMINI_API_KEY": "your_gemini_api_key_here",
            "ADK_ENABLED": "true",
            "FALLBACK_ENABLED": "true"
        }
        
        env_file = self.project_root / ".env"
        if not env_file.exists():
            with open(env_file, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            logger.info("✅ Created environment file")
        
        logger.info("✅ ADK environment setup complete")
        return True
    
    def create_deployment_scripts(self) -> bool:
        """Create deployment helper scripts."""
        logger.info("📝 Creating deployment scripts...")
        
        # Create start script
        start_script = self.project_root / "start_adk_system.py"
        start_script_content = '''#!/usr/bin/env python3
"""
Start ADK System Script
Quick start script for the Enhanced Multi-Agent System
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Start the ADK system."""
    print("🚀 Starting Enhanced Multi-Agent System with Google ADK...")
    
    try:
        from agents.copy.run_enhanced_agent_system import ADKAgentRunner
        
        # Initialize runner
        runner = ADKAgentRunner()
        
        # Start interactive mode
        print("✅ ADK System started successfully!")
        print("Type 'quit' to exit, 'help' for available commands")
        
        while True:
            try:
                user_input = input("\\nEnter your request: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    print("Available commands:")
                    print("- Ask about district heating: 'analyze district heating for [street]'")
                    print("- Ask about heat pumps: 'analyze heat pump feasibility for [street]'")
                    print("- Compare scenarios: 'compare heating scenarios for [street]'")
                    print("- Explore data: 'show me all available streets'")
                    print("- Analyze results: 'analyze the available results'")
                    continue
                elif not user_input:
                    continue
                
                # Process the request
                result = runner.delegate_to_agent(user_input)
                
                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"\\n📊 Analysis Results:")
                    print(f"Agent: {result.get('delegated_agent_name', 'Unknown')}")
                    print(f"Response: {result.get('agent_response', 'No response')}")
                    
            except KeyboardInterrupt:
                print("\\nGoodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
    
    except ImportError as e:
        print(f"❌ Failed to import ADK system: {e}")
        print("Please run the deployment script first: python scripts/deploy_adk_system.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start ADK system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        with open(start_script, 'w') as f:
            f.write(start_script_content)
        
        # Make executable
        os.chmod(start_script, 0o755)
        logger.info("✅ Created start script: start_adk_system.py")
        
        # Create test script
        test_script = self.project_root / "test_adk_system.py"
        test_script_content = '''#!/usr/bin/env python3
"""
Test ADK System Script
Quick test script for the Enhanced Multi-Agent System
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Test the ADK system."""
    print("🧪 Testing Enhanced Multi-Agent System with Google ADK...")
    
    try:
        from agents.copy.run_enhanced_agent_system import ADKAgentRunner
        
        # Initialize runner
        runner = ADKAgentRunner()
        
        # Test cases
        test_cases = [
            ("Data exploration", "show me all available streets"),
            ("District heating analysis", "analyze district heating for Parkstraße"),
            ("Heat pump analysis", "analyze heat pump feasibility for Parkstraße"),
            ("Scenario comparison", "compare heating scenarios for Parkstraße"),
            ("Results analysis", "analyze the available results")
        ]
        
        print("\\nRunning test cases...")
        for test_name, test_input in test_cases:
            print(f"\\n📋 Testing: {test_name}")
            print(f"Input: {test_input}")
            
            result = runner.delegate_to_agent(test_input)
            
            if "error" in result:
                print(f"❌ Test failed: {result['error']}")
            else:
                print(f"✅ Test completed successfully")
                print(f"   Agent: {result.get('delegated_agent_name', 'Unknown')}")
                print(f"   Tools executed: {result.get('tools_executed', False)}")
                print(f"   Has errors: {result.get('has_errors', False)}")
        
        print("\\n🎉 All tests completed!")
    
    except ImportError as e:
        print(f"❌ Failed to import ADK system: {e}")
        print("Please run the deployment script first: python scripts/deploy_adk_system.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to test ADK system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        with open(test_script, 'w') as f:
            f.write(test_script_content)
        
        # Make executable
        os.chmod(test_script, 0o755)
        logger.info("✅ Created test script: test_adk_system.py")
        
        return True
    
    def generate_deployment_report(self) -> bool:
        """Generate deployment report."""
        logger.info("📊 Generating deployment report...")
        
        report = {
            "deployment_timestamp": str(Path().cwd()),
            "environment": self.config.get("environment", "development"),
            "adk_enabled": self.config.get("adk_enabled", True),
            "fallback_enabled": self.config.get("fallback_enabled", True),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "project_root": str(self.project_root),
            "virtual_environment": str(self.venv_path) if self.venv_path.exists() else "Not created",
            "configuration_files": [],
            "test_results": "See deployment.log for details"
        }
        
        # Check configuration files
        config_files = [
            "configs/gemini_config.yml",
            "configs/cha.yml",
            "configs/cha_intelligent_sizing.yml",
            "agents copy/configs/gemini_config.yml"
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                report["configuration_files"].append({
                    "file": config_file,
                    "exists": True,
                    "size": config_path.stat().st_size
                })
            else:
                report["configuration_files"].append({
                    "file": config_file,
                    "exists": False
                })
        
        # Save report
        report_path = self.project_root / "deployment_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Deployment report saved: {report_path}")
        return True
    
    def deploy(self) -> bool:
        """Run complete deployment process."""
        logger.info("🚀 Starting ADK System Deployment...")
        
        steps = [
            ("Check Prerequisites", self.check_prerequisites),
            ("Create Virtual Environment", self.create_virtual_environment),
            ("Install Dependencies", self.install_dependencies),
            ("Validate Configuration", self.validate_configuration),
            ("Setup ADK Environment", self.setup_adk_environment),
            ("Run Tests", self.run_tests),
            ("Create Deployment Scripts", self.create_deployment_scripts),
            ("Generate Deployment Report", self.generate_deployment_report)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\\n{'='*50}")
            logger.info(f"Step: {step_name}")
            logger.info(f"{'='*50}")
            
            try:
                success = step_func()
                if not success:
                    logger.error(f"❌ Deployment failed at step: {step_name}")
                    return False
                logger.info(f"✅ {step_name} completed successfully")
            except Exception as e:
                logger.error(f"❌ Deployment failed at step {step_name}: {e}")
                return False
        
        logger.info("\\n" + "="*50)
        logger.info("🎉 ADK System Deployment Completed Successfully!")
        logger.info("="*50)
        logger.info("\\nNext steps:")
        logger.info("1. Configure your Gemini API key in configs/gemini_config.yml")
        logger.info("2. Test the system: python test_adk_system.py")
        logger.info("3. Start the system: python start_adk_system.py")
        logger.info("\\nFor more information, see:")
        logger.info("- API_DOCUMENTATION_ADK_AGENTS.md")
        logger.info("- SYSTEM_ARCHITECTURE_ADK_INTEGRATION.md")
        logger.info("- deployment_report.json")
        
        return True

def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy ADK System")
    parser.add_argument("--config", default="configs/deployment_config.yml", help="Deployment configuration file")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--no-venv", action="store_true", help="Don't create virtual environment")
    parser.add_argument("--environment", choices=["development", "production"], default="development", help="Deployment environment")
    
    args = parser.parse_args()
    
    # Create deployment configuration
    config = {
        "environment": args.environment,
        "adk_enabled": True,
        "fallback_enabled": True,
        "python_version": "3.9",
        "install_dependencies": not args.skip_deps,
        "run_tests": not args.skip_tests,
        "validate_config": True,
        "create_venv": not args.no_venv,
        "backup_existing": True
    }
    
    # Save configuration
    config_path = Path(args.config)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.safe_dump(config, f, default_flow_style=False)
    
    # Run deployment
    deployer = ADKSystemDeployer(args.config)
    success = deployer.deploy()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    import time
    main()
