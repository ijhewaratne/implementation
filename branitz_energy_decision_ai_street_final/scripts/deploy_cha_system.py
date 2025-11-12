#!/usr/bin/env python3
"""
CHA System Deployment Script

This script provides comprehensive deployment automation for the CHA Intelligent Pipe Sizing System,
including feature flag deployment, A/B testing setup, performance monitoring activation, and user feedback system deployment.
"""

import os
import sys
import json
import yaml
import argparse
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cha_feature_flags import CHAFeatureFlags
from cha_ab_testing import CHAABTesting
from cha_performance_monitoring import CHAPerformanceMonitor
from cha_user_feedback import CHAUserFeedback

class CHADeploymentManager:
    """Deployment manager for CHA system."""
    
    def __init__(self, config_dir: str = "configs"):
        """Initialize the deployment manager.
        
        Args:
            config_dir: Configuration directory
        """
        self.config_dir = config_dir
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # Initialize components
        self.feature_flags = None
        self.ab_testing = None
        self.performance_monitor = None
        self.user_feedback = None
        
        # Deployment status
        self.deployment_status = {
            'feature_flags': False,
            'ab_testing': False,
            'performance_monitoring': False,
            'user_feedback': False
        }
    
    def _setup_logging(self):
        """Setup logging for deployment."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/deployment.log'),
                logging.StreamHandler()
            ]
        )
    
    def deploy_feature_flags(self, config_path: str = None) -> bool:
        """Deploy feature flags system.
        
        Args:
            config_path: Path to feature flags configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if config_path is None:
                config_path = os.path.join(self.config_dir, 'feature_flags.yml')
            
            self.logger.info("🚀 Deploying feature flags system...")
            
            # Initialize feature flags
            self.feature_flags = CHAFeatureFlags(config_path)
            
            # Validate configuration
            if not self._validate_feature_flags_config():
                self.logger.error("Feature flags configuration validation failed")
                return False
            
            # Save configuration
            self.feature_flags.save_flags()
            
            self.deployment_status['feature_flags'] = True
            self.logger.info("✅ Feature flags system deployed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deploy feature flags: {e}")
            return False
    
    def deploy_ab_testing(self, config_path: str = None) -> bool:
        """Deploy A/B testing system.
        
        Args:
            config_path: Path to A/B testing configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if config_path is None:
                config_path = os.path.join(self.config_dir, 'ab_tests.yml')
            
            self.logger.info("🧪 Deploying A/B testing system...")
            
            # Initialize A/B testing
            self.ab_testing = CHAABTesting(config_path)
            
            # Validate configuration
            if not self._validate_ab_testing_config():
                self.logger.error("A/B testing configuration validation failed")
                return False
            
            # Start default tests
            self._start_default_ab_tests()
            
            # Save configuration
            self.ab_testing.save_tests()
            
            self.deployment_status['ab_testing'] = True
            self.logger.info("✅ A/B testing system deployed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deploy A/B testing: {e}")
            return False
    
    def deploy_performance_monitoring(self, config_path: str = None) -> bool:
        """Deploy performance monitoring system.
        
        Args:
            config_path: Path to performance monitoring configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if config_path is None:
                config_path = os.path.join(self.config_dir, 'performance_monitoring.yml')
            
            self.logger.info("📊 Deploying performance monitoring system...")
            
            # Initialize performance monitoring
            self.performance_monitor = CHAPerformanceMonitor(config_path)
            
            # Validate configuration
            if not self._validate_performance_monitoring_config():
                self.logger.error("Performance monitoring configuration validation failed")
                return False
            
            # Start monitoring
            self.performance_monitor.start_monitoring()
            
            # Save configuration
            self.performance_monitor.save_config()
            
            self.deployment_status['performance_monitoring'] = True
            self.logger.info("✅ Performance monitoring system deployed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deploy performance monitoring: {e}")
            return False
    
    def deploy_user_feedback(self, config_path: str = None) -> bool:
        """Deploy user feedback system.
        
        Args:
            config_path: Path to user feedback configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if config_path is None:
                config_path = os.path.join(self.config_dir, 'user_feedback.yml')
            
            self.logger.info("💬 Deploying user feedback system...")
            
            # Initialize user feedback
            self.user_feedback = CHAUserFeedback(config_path)
            
            # Validate configuration
            if not self._validate_user_feedback_config():
                self.logger.error("User feedback configuration validation failed")
                return False
            
            # Initialize feedback collection
            self._initialize_feedback_collection()
            
            self.deployment_status['user_feedback'] = True
            self.logger.info("✅ User feedback system deployed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deploy user feedback: {e}")
            return False
    
    def deploy_all(self) -> bool:
        """Deploy all systems.
        
        Returns:
            True if all deployments successful, False otherwise
        """
        self.logger.info("🚀 Starting complete CHA system deployment...")
        
        success = True
        
        # Deploy feature flags
        if not self.deploy_feature_flags():
            success = False
        
        # Deploy A/B testing
        if not self.deploy_ab_testing():
            success = False
        
        # Deploy performance monitoring
        if not self.deploy_performance_monitoring():
            success = False
        
        # Deploy user feedback
        if not self.deploy_user_feedback():
            success = False
        
        if success:
            self.logger.info("🎉 Complete CHA system deployment successful!")
        else:
            self.logger.error("❌ CHA system deployment failed!")
        
        return success
    
    def _validate_feature_flags_config(self) -> bool:
        """Validate feature flags configuration.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            flags = self.feature_flags.list_flags()
            if not flags:
                self.logger.warning("No feature flags found in configuration")
                return False
            
            # Check for required flags
            required_flags = [
                'intelligent_pipe_sizing',
                'enhanced_flow_calculation',
                'network_hierarchy_analysis',
                'standards_compliance'
            ]
            
            flag_names = [flag.name for flag in flags]
            for required_flag in required_flags:
                if required_flag not in flag_names:
                    self.logger.error(f"Required feature flag missing: {required_flag}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Feature flags validation error: {e}")
            return False
    
    def _validate_ab_testing_config(self) -> bool:
        """Validate A/B testing configuration.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            tests = self.ab_testing.tests
            if not tests:
                self.logger.warning("No A/B tests found in configuration")
                return False
            
            # Check for required tests
            required_tests = [
                'pipe_sizing_comparison',
                'flow_calculation_comparison'
            ]
            
            for required_test in required_tests:
                if required_test not in tests:
                    self.logger.error(f"Required A/B test missing: {required_test}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"A/B testing validation error: {e}")
            return False
    
    def _validate_performance_monitoring_config(self) -> bool:
        """Validate performance monitoring configuration.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            thresholds = self.performance_monitor.thresholds
            if not thresholds:
                self.logger.warning("No performance thresholds found in configuration")
                return False
            
            # Check for required thresholds
            required_thresholds = [
                'pipe_sizing_time_ms',
                'network_creation_time_ms',
                'simulation_time_ms',
                'memory_usage_mb',
                'cpu_usage_percent'
            ]
            
            for required_threshold in required_thresholds:
                if required_threshold not in thresholds:
                    self.logger.error(f"Required performance threshold missing: {required_threshold}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Performance monitoring validation error: {e}")
            return False
    
    def _validate_user_feedback_config(self) -> bool:
        """Validate user feedback configuration.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            config = self.user_feedback.config
            if not config:
                self.logger.warning("No user feedback configuration found")
                return False
            
            # Check for required configuration sections
            required_sections = [
                'feedback_categories',
                'sentiment_keywords',
                'priority_keywords'
            ]
            
            for required_section in required_sections:
                if required_section not in config:
                    self.logger.error(f"Required user feedback configuration section missing: {required_section}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"User feedback validation error: {e}")
            return False
    
    def _start_default_ab_tests(self):
        """Start default A/B tests."""
        try:
            # Start pipe sizing comparison test
            if 'pipe_sizing_comparison' in self.ab_testing.tests:
                self.ab_testing.start_test('pipe_sizing_comparison')
                self.logger.info("Started pipe sizing comparison A/B test")
            
            # Start flow calculation comparison test
            if 'flow_calculation_comparison' in self.ab_testing.tests:
                self.ab_testing.start_test('flow_calculation_comparison')
                self.logger.info("Started flow calculation comparison A/B test")
                
        except Exception as e:
            self.logger.error(f"Failed to start default A/B tests: {e}")
    
    def _initialize_feedback_collection(self):
        """Initialize feedback collection."""
        try:
            # Create feedback collection directories
            os.makedirs('data', exist_ok=True)
            os.makedirs('reports', exist_ok=True)
            
            # Initialize feedback analysis
            analysis = self.user_feedback.analyze_feedback()
            self.logger.info(f"Initialized feedback collection with {analysis.total_feedback} existing entries")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize feedback collection: {e}")
    
    def generate_deployment_report(self, output_path: str = None) -> str:
        """Generate deployment report.
        
        Args:
            output_path: Path to save the report
            
        Returns:
            Path to the generated report
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/deployment_report_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        report = {
            'deployment_id': f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'deployment_timestamp': datetime.now().isoformat(),
            'deployment_status': self.deployment_status,
            'components': {
                'feature_flags': {
                    'deployed': self.deployment_status['feature_flags'],
                    'config_path': os.path.join(self.config_dir, 'feature_flags.yml'),
                    'flags_count': len(self.feature_flags.list_flags()) if self.feature_flags else 0
                },
                'ab_testing': {
                    'deployed': self.deployment_status['ab_testing'],
                    'config_path': os.path.join(self.config_dir, 'ab_tests.yml'),
                    'tests_count': len(self.ab_testing.tests) if self.ab_testing else 0
                },
                'performance_monitoring': {
                    'deployed': self.deployment_status['performance_monitoring'],
                    'config_path': os.path.join(self.config_dir, 'performance_monitoring.yml'),
                    'thresholds_count': len(self.performance_monitor.thresholds) if self.performance_monitor else 0
                },
                'user_feedback': {
                    'deployed': self.deployment_status['user_feedback'],
                    'config_path': os.path.join(self.config_dir, 'user_feedback.yml'),
                    'feedback_count': len(self.user_feedback.feedback_entries) if self.user_feedback else 0
                }
            },
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'working_directory': os.getcwd()
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Generated deployment report: {output_path}")
        return output_path
    
    def rollback_deployment(self) -> bool:
        """Rollback deployment.
        
        Returns:
            True if rollback successful, False otherwise
        """
        self.logger.info("🔄 Starting deployment rollback...")
        
        success = True
        
        try:
            # Rollback feature flags
            if self.feature_flags:
                self._rollback_feature_flags()
            
            # Rollback A/B testing
            if self.ab_testing:
                self._rollback_ab_testing()
            
            # Rollback performance monitoring
            if self.performance_monitor:
                self._rollback_performance_monitoring()
            
            # Rollback user feedback
            if self.user_feedback:
                self._rollback_user_feedback()
            
            # Reset deployment status
            self.deployment_status = {
                'feature_flags': False,
                'ab_testing': False,
                'performance_monitoring': False,
                'user_feedback': False
            }
            
            self.logger.info("✅ Deployment rollback completed successfully")
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            success = False
        
        return success
    
    def _rollback_feature_flags(self):
        """Rollback feature flags."""
        try:
            # Disable all feature flags
            flags = self.feature_flags.list_flags()
            for flag in flags:
                self.feature_flags.update_flag(flag.name, {
                    'enabled': False,
                    'status': 'disabled'
                })
            
            self.feature_flags.save_flags()
            self.logger.info("Rolled back feature flags")
            
        except Exception as e:
            self.logger.error(f"Failed to rollback feature flags: {e}")
    
    def _rollback_ab_testing(self):
        """Rollback A/B testing."""
        try:
            # Stop all running tests
            for test_id in self.ab_testing.tests.keys():
                self.ab_testing.stop_test(test_id)
            
            self.logger.info("Rolled back A/B testing")
            
        except Exception as e:
            self.logger.error(f"Failed to rollback A/B testing: {e}")
    
    def _rollback_performance_monitoring(self):
        """Rollback performance monitoring."""
        try:
            # Stop monitoring
            self.performance_monitor.stop_monitoring()
            
            # Generate final report
            report = self.performance_monitor.generate_performance_report()
            self.performance_monitor.save_report(report, 'reports/rollback_performance_report.json')
            
            self.logger.info("Rolled back performance monitoring")
            
        except Exception as e:
            self.logger.error(f"Failed to rollback performance monitoring: {e}")
    
    def _rollback_user_feedback(self):
        """Rollback user feedback."""
        try:
            # Export existing feedback
            self.user_feedback.export_feedback('data/feedback_rollback_backup.json')
            
            self.logger.info("Rolled back user feedback")
            
        except Exception as e:
            self.logger.error(f"Failed to rollback user feedback: {e}")
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get deployment status.
        
        Returns:
            Deployment status dictionary
        """
        return {
            'deployment_status': self.deployment_status,
            'components': {
                'feature_flags': {
                    'deployed': self.deployment_status['feature_flags'],
                    'active': self.feature_flags is not None
                },
                'ab_testing': {
                    'deployed': self.deployment_status['ab_testing'],
                    'active': self.ab_testing is not None
                },
                'performance_monitoring': {
                    'deployed': self.deployment_status['performance_monitoring'],
                    'active': self.performance_monitor is not None
                },
                'user_feedback': {
                    'deployed': self.deployment_status['user_feedback'],
                    'active': self.user_feedback is not None
                }
            }
        }

def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='CHA System Deployment Manager')
    parser.add_argument('--config-dir', default='configs', help='Configuration directory')
    parser.add_argument('--action', choices=['deploy-all', 'deploy-feature-flags', 'deploy-ab-testing', 
                                           'deploy-performance-monitoring', 'deploy-user-feedback', 
                                           'rollback', 'status', 'report'], required=True, help='Action to perform')
    parser.add_argument('--output', help='Output file path for reports')
    
    args = parser.parse_args()
    
    # Initialize deployment manager
    deployment_manager = CHADeploymentManager(args.config_dir)
    
    try:
        if args.action == 'deploy-all':
            success = deployment_manager.deploy_all()
            if success:
                print("🎉 Complete CHA system deployment successful!")
            else:
                print("❌ CHA system deployment failed!")
                return 1
        
        elif args.action == 'deploy-feature-flags':
            success = deployment_manager.deploy_feature_flags()
            if success:
                print("✅ Feature flags deployed successfully!")
            else:
                print("❌ Feature flags deployment failed!")
                return 1
        
        elif args.action == 'deploy-ab-testing':
            success = deployment_manager.deploy_ab_testing()
            if success:
                print("✅ A/B testing deployed successfully!")
            else:
                print("❌ A/B testing deployment failed!")
                return 1
        
        elif args.action == 'deploy-performance-monitoring':
            success = deployment_manager.deploy_performance_monitoring()
            if success:
                print("✅ Performance monitoring deployed successfully!")
            else:
                print("❌ Performance monitoring deployment failed!")
                return 1
        
        elif args.action == 'deploy-user-feedback':
            success = deployment_manager.deploy_user_feedback()
            if success:
                print("✅ User feedback deployed successfully!")
            else:
                print("❌ User feedback deployment failed!")
                return 1
        
        elif args.action == 'rollback':
            success = deployment_manager.rollback_deployment()
            if success:
                print("✅ Deployment rollback completed successfully!")
            else:
                print("❌ Deployment rollback failed!")
                return 1
        
        elif args.action == 'status':
            status = deployment_manager.get_deployment_status()
            print("📊 Deployment Status:")
            for component, info in status['components'].items():
                status_icon = "✅" if info['deployed'] else "❌"
                print(f"  {status_icon} {component}: {'Deployed' if info['deployed'] else 'Not Deployed'}")
        
        elif args.action == 'report':
            report_path = deployment_manager.generate_deployment_report(args.output)
            print(f"📊 Generated deployment report: {report_path}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
