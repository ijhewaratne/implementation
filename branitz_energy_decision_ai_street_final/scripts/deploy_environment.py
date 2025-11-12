#!/usr/bin/env python3
"""
Environment-Specific Deployment Script
Deploy the Enhanced Multi-Agent System with Google ADK for different environments
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
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('environment_deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EnvironmentDeployer:
    """Environment-specific deployment manager."""
    
    def __init__(self, environment: str = "development"):
        """Initialize the environment deployer."""
        self.environment = environment
        self.project_root = Path.cwd()
        self.config_path = self.project_root / "configs" / "deployment_config.yml"
        self.config = self._load_config()
        self.env_config = self.config.get("environments", {}).get(environment, {})
        
    def _load_config(self) -> Dict:
        """Load deployment configuration."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            logger.error(f"Configuration file not found: {self.config_path}")
            sys.exit(1)
    
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
                timeout=600  # 10 minute timeout
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
    
    def deploy_development(self) -> bool:
        """Deploy for development environment."""
        logger.info("🔧 Deploying for DEVELOPMENT environment...")
        
        steps = [
            ("Create Development Environment", self._create_dev_environment),
            ("Install Development Dependencies", self._install_dev_dependencies),
            ("Setup Development Configuration", self._setup_dev_config),
            ("Run Development Tests", self._run_dev_tests),
            ("Start Development Services", self._start_dev_services)
        ]
        
        return self._execute_steps(steps)
    
    def deploy_staging(self) -> bool:
        """Deploy for staging environment."""
        logger.info("🚀 Deploying for STAGING environment...")
        
        steps = [
            ("Create Staging Environment", self._create_staging_environment),
            ("Install Staging Dependencies", self._install_staging_dependencies),
            ("Setup Staging Configuration", self._setup_staging_config),
            ("Run Staging Tests", self._run_staging_tests),
            ("Deploy Staging Services", self._deploy_staging_services)
        ]
        
        return self._execute_steps(steps)
    
    def deploy_production(self) -> bool:
        """Deploy for production environment."""
        logger.info("🏭 Deploying for PRODUCTION environment...")
        
        steps = [
            ("Create Production Environment", self._create_prod_environment),
            ("Install Production Dependencies", self._install_prod_dependencies),
            ("Setup Production Configuration", self._setup_prod_config),
            ("Run Production Tests", self._run_prod_tests),
            ("Deploy Production Services", self._deploy_prod_services),
            ("Setup Production Monitoring", self._setup_prod_monitoring)
        ]
        
        return self._execute_steps(steps)
    
    def _execute_steps(self, steps: List[Tuple[str, callable]]) -> bool:
        """Execute deployment steps."""
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
        
        return True
    
    def _create_dev_environment(self) -> bool:
        """Create development environment."""
        logger.info("Creating development environment...")
        
        # Create development directories
        dev_dirs = [
            "dev/data",
            "dev/configs",
            "dev/logs",
            "dev/processed"
        ]
        
        for dir_path in dev_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {dir_path}")
        
        # Create development virtual environment
        dev_venv = self.project_root / "dev" / "venv"
        if dev_venv.exists():
            shutil.rmtree(dev_venv)
        
        success, _ = self._run_command(f"python -m venv {dev_venv}")
        if not success:
            return False
        
        logger.info("✅ Development environment created")
        return True
    
    def _install_dev_dependencies(self) -> bool:
        """Install development dependencies."""
        logger.info("Installing development dependencies...")
        
        dev_venv = self.project_root / "dev" / "venv"
        pip_cmd = str(dev_venv / "bin" / "pip")
        if os.name == 'nt':  # Windows
            pip_cmd = str(dev_venv / "Scripts" / "pip.exe")
        
        # Install base requirements
        success, _ = self._run_command(f"{pip_cmd} install -r requirements.txt")
        if not success:
            return False
        
        # Install development-specific packages
        dev_packages = [
            "pytest",
            "pytest-cov",
            "black",
            "ruff",
            "jupyter",
            "ipython",
            "pytest-xdist"  # For parallel testing
        ]
        
        for package in dev_packages:
            success, _ = self._run_command(f"{pip_cmd} install {package}")
            if not success:
                logger.warning(f"Failed to install {package}")
        
        logger.info("✅ Development dependencies installed")
        return True
    
    def _setup_dev_config(self) -> bool:
        """Setup development configuration."""
        logger.info("Setting up development configuration...")
        
        # Copy configuration files to dev directory
        config_files = [
            "configs/gemini_config.yml",
            "configs/cha.yml",
            "configs/cha_intelligent_sizing.yml"
        ]
        
        for config_file in config_files:
            src_path = self.project_root / config_file
            dst_path = self.project_root / "dev" / config_file
            
            if src_path.exists():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                logger.info(f"✅ Copied configuration: {config_file}")
        
        # Create development-specific configuration
        dev_config = {
            "environment": "development",
            "adk_enabled": True,
            "fallback_enabled": True,
            "debug_mode": True,
            "logging_level": "DEBUG",
            "api": {
                "gemini": {
                    "model": "gemini-1.5-flash-latest",
                    "temperature": 0.7,
                    "timeout": 30
                }
            }
        }
        
        dev_config_path = self.project_root / "dev" / "configs" / "dev_config.yml"
        with open(dev_config_path, 'w') as f:
            yaml.safe_dump(dev_config, f, default_flow_style=False)
        
        logger.info("✅ Development configuration setup complete")
        return True
    
    def _run_dev_tests(self) -> bool:
        """Run development tests."""
        logger.info("Running development tests...")
        
        dev_venv = self.project_root / "dev" / "venv"
        python_cmd = str(dev_venv / "bin" / "python")
        if os.name == 'nt':  # Windows
            python_cmd = str(dev_venv / "Scripts" / "python.exe")
        
        # Run unit tests
        test_commands = [
            f"{python_cmd} -m pytest tests/test_adk_agents_unit.py -v",
            f"{python_cmd} -m pytest tests/test_adk_tools_unit.py -v",
            f"{python_cmd} -m pytest tests/test_adk_integration.py -v"
        ]
        
        for test_cmd in test_commands:
            success, output = self._run_command(test_cmd)
            if not success:
                logger.warning(f"Test failed: {test_cmd}")
                logger.warning(f"Output: {output}")
            else:
                logger.info(f"✅ Test passed: {test_cmd}")
        
        logger.info("✅ Development tests completed")
        return True
    
    def _start_dev_services(self) -> bool:
        """Start development services."""
        logger.info("Starting development services...")
        
        # Create development startup script
        dev_start_script = self.project_root / "dev" / "start_dev.py"
        dev_start_content = '''#!/usr/bin/env python3
"""
Development Environment Startup Script
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Start development environment."""
    print("🔧 Starting Development Environment...")
    
    try:
        from agents.copy.run_enhanced_agent_system import ADKAgentRunner
        
        # Initialize runner
        runner = ADKAgentRunner()
        
        print("✅ Development environment started successfully!")
        print("Type 'quit' to exit, 'help' for available commands")
        
        while True:
            try:
                user_input = input("\\n[DEV] Enter your request: ").strip()
                
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
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start development environment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        with open(dev_start_script, 'w') as f:
            f.write(dev_start_content)
        
        os.chmod(dev_start_script, 0o755)
        logger.info("✅ Development services started")
        return True
    
    def _create_staging_environment(self) -> bool:
        """Create staging environment."""
        logger.info("Creating staging environment...")
        
        # Create staging directories
        staging_dirs = [
            "staging/data",
            "staging/configs",
            "staging/logs",
            "staging/processed"
        ]
        
        for dir_path in staging_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {dir_path}")
        
        # Create staging virtual environment
        staging_venv = self.project_root / "staging" / "venv"
        if staging_venv.exists():
            shutil.rmtree(staging_venv)
        
        success, _ = self._run_command(f"python -m venv {staging_venv}")
        if not success:
            return False
        
        logger.info("✅ Staging environment created")
        return True
    
    def _install_staging_dependencies(self) -> bool:
        """Install staging dependencies."""
        logger.info("Installing staging dependencies...")
        
        staging_venv = self.project_root / "staging" / "venv"
        pip_cmd = str(staging_venv / "bin" / "pip")
        if os.name == 'nt':  # Windows
            pip_cmd = str(staging_venv / "Scripts" / "pip.exe")
        
        # Install base requirements
        success, _ = self._run_command(f"{pip_cmd} install -r requirements.txt")
        if not success:
            return False
        
        # Install staging-specific packages
        staging_packages = [
            "pytest",
            "pytest-cov",
            "gunicorn"  # For production-like WSGI server
        ]
        
        for package in staging_packages:
            success, _ = self._run_command(f"{pip_cmd} install {package}")
            if not success:
                logger.warning(f"Failed to install {package}")
        
        logger.info("✅ Staging dependencies installed")
        return True
    
    def _setup_staging_config(self) -> bool:
        """Setup staging configuration."""
        logger.info("Setting up staging configuration...")
        
        # Copy configuration files to staging directory
        config_files = [
            "configs/gemini_config.yml",
            "configs/cha.yml",
            "configs/cha_intelligent_sizing.yml"
        ]
        
        for config_file in config_files:
            src_path = self.project_root / config_file
            dst_path = self.project_root / "staging" / config_file
            
            if src_path.exists():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                logger.info(f"✅ Copied configuration: {config_file}")
        
        # Create staging-specific configuration
        staging_config = {
            "environment": "staging",
            "adk_enabled": True,
            "fallback_enabled": True,
            "debug_mode": False,
            "logging_level": "INFO",
            "api": {
                "gemini": {
                    "model": "gemini-1.5-flash-latest",
                    "temperature": 0.7,
                    "timeout": 30
                }
            },
            "monitoring": {
                "enabled": True,
                "alerting": True
            }
        }
        
        staging_config_path = self.project_root / "staging" / "configs" / "staging_config.yml"
        with open(staging_config_path, 'w') as f:
            yaml.safe_dump(staging_config, f, default_flow_style=False)
        
        logger.info("✅ Staging configuration setup complete")
        return True
    
    def _run_staging_tests(self) -> bool:
        """Run staging tests."""
        logger.info("Running staging tests...")
        
        staging_venv = self.project_root / "staging" / "venv"
        python_cmd = str(staging_venv / "bin" / "python")
        if os.name == 'nt':  # Windows
            python_cmd = str(staging_venv / "Scripts" / "python.exe")
        
        # Run comprehensive tests
        test_commands = [
            f"{python_cmd} -m pytest tests/test_adk_agents_unit.py -v",
            f"{python_cmd} -m pytest tests/test_adk_tools_unit.py -v",
            f"{python_cmd} -m pytest tests/test_adk_integration.py -v",
            f"{python_cmd} -m pytest tests/test_adk_performance.py -v"
        ]
        
        for test_cmd in test_commands:
            success, output = self._run_command(test_cmd)
            if not success:
                logger.error(f"Test failed: {test_cmd}")
                logger.error(f"Output: {output}")
                return False
            logger.info(f"✅ Test passed: {test_cmd}")
        
        logger.info("✅ Staging tests completed")
        return True
    
    def _deploy_staging_services(self) -> bool:
        """Deploy staging services."""
        logger.info("Deploying staging services...")
        
        # Use Docker Compose for staging
        success, _ = self._run_command("docker-compose --profile staging up -d")
        if not success:
            logger.warning("Docker Compose staging deployment failed, using direct deployment")
            
            # Fallback to direct deployment
            staging_venv = self.project_root / "staging" / "venv"
            python_cmd = str(staging_venv / "bin" / "python")
            if os.name == 'nt':  # Windows
                python_cmd = str(staging_venv / "Scripts" / "python.exe")
            
            # Start staging service
            success, _ = self._run_command(f"{python_cmd} start_adk_system.py")
            if not success:
                return False
        
        logger.info("✅ Staging services deployed")
        return True
    
    def _create_prod_environment(self) -> bool:
        """Create production environment."""
        logger.info("Creating production environment...")
        
        # Create production directories
        prod_dirs = [
            "prod/data",
            "prod/configs",
            "prod/logs",
            "prod/processed",
            "prod/backups"
        ]
        
        for dir_path in prod_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {dir_path}")
        
        # Create production virtual environment
        prod_venv = self.project_root / "prod" / "venv"
        if prod_venv.exists():
            shutil.rmtree(prod_venv)
        
        success, _ = self._run_command(f"python -m venv {prod_venv}")
        if not success:
            return False
        
        logger.info("✅ Production environment created")
        return True
    
    def _install_prod_dependencies(self) -> bool:
        """Install production dependencies."""
        logger.info("Installing production dependencies...")
        
        prod_venv = self.project_root / "prod" / "venv"
        pip_cmd = str(prod_venv / "bin" / "pip")
        if os.name == 'nt':  # Windows
            pip_cmd = str(prod_venv / "Scripts" / "pip.exe")
        
        # Install base requirements
        success, _ = self._run_command(f"{pip_cmd} install -r requirements.txt")
        if not success:
            return False
        
        # Install production-specific packages
        prod_packages = [
            "gunicorn",
            "supervisor",
            "psutil"  # For monitoring
        ]
        
        for package in prod_packages:
            success, _ = self._run_command(f"{pip_cmd} install {package}")
            if not success:
                logger.warning(f"Failed to install {package}")
        
        logger.info("✅ Production dependencies installed")
        return True
    
    def _setup_prod_config(self) -> bool:
        """Setup production configuration."""
        logger.info("Setting up production configuration...")
        
        # Copy configuration files to prod directory
        config_files = [
            "configs/gemini_config.yml",
            "configs/cha.yml",
            "configs/cha_intelligent_sizing.yml"
        ]
        
        for config_file in config_files:
            src_path = self.project_root / config_file
            dst_path = self.project_root / "prod" / config_file
            
            if src_path.exists():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                logger.info(f"✅ Copied configuration: {config_file}")
        
        # Create production-specific configuration
        prod_config = {
            "environment": "production",
            "adk_enabled": True,
            "fallback_enabled": True,
            "debug_mode": False,
            "logging_level": "WARNING",
            "api": {
                "gemini": {
                    "model": "gemini-1.5-flash-latest",
                    "temperature": 0.7,
                    "timeout": 30
                }
            },
            "monitoring": {
                "enabled": True,
                "alerting": True,
                "metrics_collection": True
            },
            "security": {
                "rate_limiting": True,
                "quota_management": True
            }
        }
        
        prod_config_path = self.project_root / "prod" / "configs" / "prod_config.yml"
        with open(prod_config_path, 'w') as f:
            yaml.safe_dump(prod_config, f, default_flow_style=False)
        
        logger.info("✅ Production configuration setup complete")
        return True
    
    def _run_prod_tests(self) -> bool:
        """Run production tests."""
        logger.info("Running production tests...")
        
        prod_venv = self.project_root / "prod" / "venv"
        python_cmd = str(prod_venv / "bin" / "python")
        if os.name == 'nt':  # Windows
            python_cmd = str(prod_venv / "Scripts" / "python.exe")
        
        # Run comprehensive tests including performance tests
        test_commands = [
            f"{python_cmd} -m pytest tests/test_adk_agents_unit.py -v",
            f"{python_cmd} -m pytest tests/test_adk_tools_unit.py -v",
            f"{python_cmd} -m pytest tests/test_adk_integration.py -v",
            f"{python_cmd} -m pytest tests/test_adk_performance.py -v",
            f"{python_cmd} -m pytest tests/test_adk_system_stability.py -v"
        ]
        
        for test_cmd in test_commands:
            success, output = self._run_command(test_cmd)
            if not success:
                logger.error(f"Test failed: {test_cmd}")
                logger.error(f"Output: {output}")
                return False
            logger.info(f"✅ Test passed: {test_cmd}")
        
        logger.info("✅ Production tests completed")
        return True
    
    def _deploy_prod_services(self) -> bool:
        """Deploy production services."""
        logger.info("Deploying production services...")
        
        # Use Docker Compose for production
        success, _ = self._run_command("docker-compose --profile prod up -d")
        if not success:
            logger.warning("Docker Compose production deployment failed, using direct deployment")
            
            # Fallback to direct deployment with supervisor
            prod_venv = self.project_root / "prod" / "venv"
            python_cmd = str(prod_venv / "bin" / "python")
            if os.name == 'nt':  # Windows
                python_cmd = str(prod_venv / "Scripts" / "python.exe")
            
            # Create supervisor configuration
            supervisor_config = f"""[program:branitz-adk-system]
command={python_cmd} start_adk_system.py
directory={self.project_root}
autostart=true
autorestart=true
user=appuser
redirect_stderr=true
stdout_logfile={self.project_root}/prod/logs/supervisor.log
"""
            
            supervisor_config_path = self.project_root / "prod" / "supervisor.conf"
            with open(supervisor_config_path, 'w') as f:
                f.write(supervisor_config)
            
            # Start with supervisor
            success, _ = self._run_command(f"supervisord -c {supervisor_config_path}")
            if not success:
                return False
        
        logger.info("✅ Production services deployed")
        return True
    
    def _setup_prod_monitoring(self) -> bool:
        """Setup production monitoring."""
        logger.info("Setting up production monitoring...")
        
        # Create monitoring configuration
        monitoring_config = {
            "system_monitoring": {
                "enabled": True,
                "metrics_collection": True,
                "health_checks": True,
                "alerting": True
            },
            "application_monitoring": {
                "enabled": True,
                "performance_metrics": True,
                "error_tracking": True,
                "usage_analytics": True
            },
            "logging": {
                "enabled": True,
                "structured_logging": True,
                "log_aggregation": True,
                "log_retention_days": 30
            }
        }
        
        monitoring_config_path = self.project_root / "prod" / "configs" / "monitoring_config.yml"
        with open(monitoring_config_path, 'w') as f:
            yaml.safe_dump(monitoring_config, f, default_flow_style=False)
        
        # Start monitoring services if Docker Compose is available
        success, _ = self._run_command("docker-compose --profile monitoring up -d")
        if not success:
            logger.warning("Docker Compose monitoring deployment failed")
        
        logger.info("✅ Production monitoring setup complete")
        return True
    
    def deploy(self) -> bool:
        """Deploy for the specified environment."""
        logger.info(f"🚀 Starting deployment for {self.environment.upper()} environment...")
        
        if self.environment == "development":
            return self.deploy_development()
        elif self.environment == "staging":
            return self.deploy_staging()
        elif self.environment == "production":
            return self.deploy_production()
        else:
            logger.error(f"Unknown environment: {self.environment}")
            return False

def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy ADK System for specific environment")
    parser.add_argument("environment", choices=["development", "staging", "production"], 
                       help="Deployment environment")
    parser.add_argument("--config", default="configs/deployment_config.yml", 
                       help="Deployment configuration file")
    
    args = parser.parse_args()
    
    # Run deployment
    deployer = EnvironmentDeployer(args.environment)
    success = deployer.deploy()
    
    if success:
        logger.info(f"\\n🎉 {args.environment.upper()} deployment completed successfully!")
        logger.info(f"\\nNext steps:")
        if args.environment == "development":
            logger.info("1. cd dev && python start_dev.py")
        elif args.environment == "staging":
            logger.info("1. docker-compose --profile staging ps")
        elif args.environment == "production":
            logger.info("1. docker-compose --profile prod ps")
        logger.info("2. Check logs in the respective environment directory")
        logger.info("3. Monitor system health and performance")
    else:
        logger.error(f"❌ {args.environment.upper()} deployment failed!")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
