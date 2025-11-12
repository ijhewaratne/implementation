#!/usr/bin/env python3
"""
CHA A/B Testing System

This module provides comprehensive A/B testing capabilities for the CHA Intelligent Pipe Sizing System,
enabling comparison between existing and new sizing approaches, performance evaluation, and statistical analysis.
"""

import os
import json
import yaml
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import hashlib
import statistics
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

class TestStatus(Enum):
    """Status of A/B tests."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TestType(Enum):
    """Types of A/B tests."""
    PIPE_SIZING = "pipe_sizing"
    FLOW_CALCULATION = "flow_calculation"
    NETWORK_ANALYSIS = "network_analysis"
    COST_ANALYSIS = "cost_analysis"
    PERFORMANCE = "performance"
    USER_EXPERIENCE = "user_experience"

@dataclass
class TestVariant:
    """A/B test variant definition."""
    name: str
    description: str
    traffic_percentage: float
    configuration: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TestMetric:
    """A/B test metric definition."""
    name: str
    description: str
    metric_type: str  # "primary", "secondary", "guardrail"
    aggregation: str  # "sum", "mean", "count", "rate"
    target_direction: str  # "increase", "decrease", "neutral"
    minimum_detectable_effect: float = 0.05
    significance_level: float = 0.05
    power: float = 0.8

@dataclass
class TestResult:
    """A/B test result."""
    variant_name: str
    metric_name: str
    value: float
    sample_size: int
    confidence_interval: Tuple[float, float]
    p_value: float
    is_significant: bool
    effect_size: float
    timestamp: datetime

@dataclass
class ABTest:
    """A/B test definition."""
    test_id: str
    name: str
    description: str
    test_type: TestType
    status: TestStatus
    start_date: datetime
    end_date: Optional[datetime]
    variants: List[TestVariant]
    metrics: List[TestMetric]
    target_sample_size: int
    minimum_duration_days: int
    maximum_duration_days: int
    success_criteria: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class CHAABTesting:
    """A/B testing system for CHA."""
    
    def __init__(self, config_path: str = "configs/ab_tests.yml"):
        """Initialize the A/B testing system.
        
        Args:
            config_path: Path to A/B tests configuration file
        """
        self.config_path = config_path
        self.tests: Dict[str, ABTest] = {}
        self.results: Dict[str, List[TestResult]] = {}
        self.logger = logging.getLogger(__name__)
        
        # Load A/B tests configuration
        self._load_tests()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for A/B testing."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_tests(self):
        """Load A/B tests from configuration file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                for test_id, test_config in config.get('ab_tests', {}).items():
                    self.tests[test_id] = self._create_ab_test(test_id, test_config)
                
                self.logger.info(f"Loaded {len(self.tests)} A/B tests from {self.config_path}")
            else:
                self.logger.warning(f"A/B tests configuration file not found: {self.config_path}")
                self._create_default_tests()
                
        except Exception as e:
            self.logger.error(f"Failed to load A/B tests: {e}")
            self._create_default_tests()
    
    def _create_ab_test(self, test_id: str, config: Dict[str, Any]) -> ABTest:
        """Create an A/B test from configuration.
        
        Args:
            test_id: Test identifier
            config: Test configuration
            
        Returns:
            A/B test object
        """
        variants = []
        for variant_config in config.get('variants', []):
            variants.append(TestVariant(
                name=variant_config['name'],
                description=variant_config.get('description', ''),
                traffic_percentage=variant_config['traffic_percentage'],
                configuration=variant_config['configuration'],
                metadata=variant_config.get('metadata', {})
            ))
        
        metrics = []
        for metric_config in config.get('metrics', []):
            metrics.append(TestMetric(
                name=metric_config['name'],
                description=metric_config.get('description', ''),
                metric_type=metric_config.get('metric_type', 'secondary'),
                aggregation=metric_config.get('aggregation', 'mean'),
                target_direction=metric_config.get('target_direction', 'neutral'),
                minimum_detectable_effect=metric_config.get('minimum_detectable_effect', 0.05),
                significance_level=metric_config.get('significance_level', 0.05),
                power=metric_config.get('power', 0.8)
            ))
        
        return ABTest(
            test_id=test_id,
            name=config['name'],
            description=config.get('description', ''),
            test_type=TestType(config.get('test_type', 'pipe_sizing')),
            status=TestStatus(config.get('status', 'draft')),
            start_date=self._parse_datetime(config.get('start_date')),
            end_date=self._parse_datetime(config.get('end_date')),
            variants=variants,
            metrics=metrics,
            target_sample_size=config.get('target_sample_size', 1000),
            minimum_duration_days=config.get('minimum_duration_days', 7),
            maximum_duration_days=config.get('maximum_duration_days', 30),
            success_criteria=config.get('success_criteria', {}),
            metadata=config.get('metadata', {})
        )
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string.
        
        Args:
            datetime_str: Datetime string
            
        Returns:
            Parsed datetime or None
        """
        if not datetime_str:
            return None
        
        try:
            return datetime.fromisoformat(datetime_str)
        except ValueError:
            return None
    
    def _create_default_tests(self):
        """Create default A/B tests."""
        default_tests = {
            'pipe_sizing_comparison': {
                'name': 'Pipe Sizing Method Comparison',
                'description': 'Compare traditional vs. intelligent pipe sizing methods',
                'test_type': 'pipe_sizing',
                'status': 'draft',
                'variants': [
                    {
                        'name': 'traditional',
                        'description': 'Traditional fixed diameter sizing',
                        'traffic_percentage': 50.0,
                        'configuration': {
                            'pipe_sizing_method': 'fixed_diameter',
                            'default_diameter_mm': 100,
                            'enable_intelligent_sizing': False
                        }
                    },
                    {
                        'name': 'intelligent',
                        'description': 'Intelligent pipe sizing with flow-based calculation',
                        'traffic_percentage': 50.0,
                        'configuration': {
                            'pipe_sizing_method': 'intelligent',
                            'enable_intelligent_sizing': True,
                            'max_velocity_ms': 2.0,
                            'min_velocity_ms': 0.1
                        }
                    }
                ],
                'metrics': [
                    {
                        'name': 'pipe_cost_efficiency',
                        'description': 'Cost efficiency of pipe sizing',
                        'metric_type': 'primary',
                        'aggregation': 'mean',
                        'target_direction': 'increase'
                    },
                    {
                        'name': 'hydraulic_performance',
                        'description': 'Hydraulic performance metrics',
                        'metric_type': 'primary',
                        'aggregation': 'mean',
                        'target_direction': 'increase'
                    },
                    {
                        'name': 'sizing_accuracy',
                        'description': 'Accuracy of pipe sizing',
                        'metric_type': 'secondary',
                        'aggregation': 'mean',
                        'target_direction': 'increase'
                    }
                ],
                'target_sample_size': 1000,
                'minimum_duration_days': 7,
                'maximum_duration_days': 30
            },
            'flow_calculation_comparison': {
                'name': 'Flow Calculation Method Comparison',
                'description': 'Compare basic vs. enhanced flow calculation methods',
                'test_type': 'flow_calculation',
                'status': 'draft',
                'variants': [
                    {
                        'name': 'basic',
                        'description': 'Basic flow calculation without safety factors',
                        'traffic_percentage': 50.0,
                        'configuration': {
                            'flow_calculation_method': 'basic',
                            'safety_factor': 1.0,
                            'diversity_factor': 1.0
                        }
                    },
                    {
                        'name': 'enhanced',
                        'description': 'Enhanced flow calculation with safety and diversity factors',
                        'traffic_percentage': 50.0,
                        'configuration': {
                            'flow_calculation_method': 'enhanced',
                            'safety_factor': 1.1,
                            'diversity_factor': 0.8
                        }
                    }
                ],
                'metrics': [
                    {
                        'name': 'flow_accuracy',
                        'description': 'Accuracy of flow calculations',
                        'metric_type': 'primary',
                        'aggregation': 'mean',
                        'target_direction': 'increase'
                    },
                    {
                        'name': 'system_reliability',
                        'description': 'System reliability metrics',
                        'metric_type': 'primary',
                        'aggregation': 'mean',
                        'target_direction': 'increase'
                    }
                ],
                'target_sample_size': 800,
                'minimum_duration_days': 7,
                'maximum_duration_days': 21
            }
        }
        
        for test_id, test_config in default_tests.items():
            self.tests[test_id] = self._create_ab_test(test_id, test_config)
        
        self.logger.info(f"Created {len(self.tests)} default A/B tests")
    
    def assign_user_to_variant(self, test_id: str, user_id: str) -> Optional[str]:
        """Assign a user to a test variant.
        
        Args:
            test_id: Test identifier
            user_id: User identifier
            
        Returns:
            Variant name or None if not assigned
        """
        test = self.tests.get(test_id)
        if not test or test.status != TestStatus.RUNNING:
            return None
        
        # Check if test is within date range
        current_date = datetime.now()
        if test.start_date and current_date < test.start_date:
            return None
        
        if test.end_date and current_date > test.end_date:
            return None
        
        # Assign user to variant based on hash
        user_hash = self._hash_user_id(user_id)
        cumulative_percentage = 0.0
        
        for variant in test.variants:
            cumulative_percentage += variant.traffic_percentage
            if user_hash < cumulative_percentage / 100.0:
                self.logger.info(f"User {user_id} assigned to variant {variant.name} in test {test_id}")
                return variant.name
        
        # Fallback to first variant
        return test.variants[0].name if test.variants else None
    
    def _hash_user_id(self, user_id: str) -> float:
        """Hash user ID to a value between 0 and 1.
        
        Args:
            user_id: User identifier
            
        Returns:
            Hash value between 0 and 1
        """
        hash_obj = hashlib.md5(user_id.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        return (hash_int % 10000) / 10000.0
    
    def record_metric(self, test_id: str, variant_name: str, metric_name: str, 
                     value: float, user_id: Optional[str] = None):
        """Record a metric value for a test variant.
        
        Args:
            test_id: Test identifier
            variant_name: Variant name
            metric_name: Metric name
            value: Metric value
            user_id: User identifier
        """
        test = self.tests.get(test_id)
        if not test:
            self.logger.warning(f"Test {test_id} not found")
            return
        
        # Initialize results if not exists
        if test_id not in self.results:
            self.results[test_id] = []
        
        # Create result record
        result = TestResult(
            variant_name=variant_name,
            metric_name=metric_name,
            value=value,
            sample_size=1,
            confidence_interval=(0.0, 0.0),
            p_value=1.0,
            is_significant=False,
            effect_size=0.0,
            timestamp=datetime.now()
        )
        
        self.results[test_id].append(result)
        self.logger.info(f"Recorded metric {metric_name}={value} for variant {variant_name} in test {test_id}")
    
    def analyze_test_results(self, test_id: str) -> Dict[str, Any]:
        """Analyze A/B test results.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Analysis results
        """
        test = self.tests.get(test_id)
        if not test:
            return {'error': f'Test {test_id} not found'}
        
        if test_id not in self.results:
            return {'error': f'No results found for test {test_id}'}
        
        results = self.results[test_id]
        analysis = {
            'test_id': test_id,
            'test_name': test.name,
            'status': test.status.value,
            'start_date': test.start_date.isoformat() if test.start_date else None,
            'end_date': test.end_date.isoformat() if test.end_date else None,
            'variants': {},
            'overall_conclusion': 'inconclusive',
            'recommendations': []
        }
        
        # Analyze each metric
        for metric in test.metrics:
            metric_results = [r for r in results if r.metric_name == metric.name]
            if not metric_results:
                continue
            
            # Group by variant
            variant_data = {}
            for variant in test.variants:
                variant_results = [r for r in metric_results if r.variant_name == variant.name]
                if variant_results:
                    values = [r.value for r in variant_results]
                    variant_data[variant.name] = {
                        'values': values,
                        'mean': statistics.mean(values),
                        'std': statistics.stdev(values) if len(values) > 1 else 0.0,
                        'count': len(values),
                        'confidence_interval': self._calculate_confidence_interval(values)
                    }
            
            # Statistical analysis
            if len(variant_data) >= 2:
                variant_names = list(variant_data.keys())
                control_variant = variant_names[0]
                treatment_variant = variant_names[1]
                
                control_values = variant_data[control_variant]['values']
                treatment_values = variant_data[treatment_variant]['values']
                
                # T-test
                t_stat, p_value = stats.ttest_ind(treatment_values, control_values)
                
                # Effect size (Cohen's d)
                effect_size = self._calculate_cohens_d(control_values, treatment_values)
                
                # Determine significance
                is_significant = p_value < metric.significance_level
                
                # Determine direction
                control_mean = variant_data[control_variant]['mean']
                treatment_mean = variant_data[treatment_variant]['mean']
                improvement = (treatment_mean - control_mean) / control_mean if control_mean != 0 else 0
                
                analysis['variants'][metric.name] = {
                    'control_variant': control_variant,
                    'treatment_variant': treatment_variant,
                    'control_mean': control_mean,
                    'treatment_mean': treatment_mean,
                    'improvement_percentage': improvement * 100,
                    'p_value': p_value,
                    'is_significant': is_significant,
                    'effect_size': effect_size,
                    'sample_size': len(control_values) + len(treatment_values),
                    'recommendation': self._get_metric_recommendation(
                        metric, improvement, is_significant, effect_size
                    )
                }
        
        # Overall conclusion
        analysis['overall_conclusion'] = self._get_overall_conclusion(analysis['variants'])
        analysis['recommendations'] = self._get_overall_recommendations(analysis['variants'])
        
        return analysis
    
    def _calculate_confidence_interval(self, values: List[float], confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for a list of values.
        
        Args:
            values: List of values
            confidence: Confidence level
            
        Returns:
            Confidence interval tuple
        """
        if len(values) < 2:
            return (values[0], values[0]) if values else (0.0, 0.0)
        
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        n = len(values)
        
        # T-distribution critical value
        alpha = 1 - confidence
        t_critical = stats.t.ppf(1 - alpha/2, n - 1)
        
        margin_error = t_critical * (std / np.sqrt(n))
        
        return (mean - margin_error, mean + margin_error)
    
    def _calculate_cohens_d(self, control_values: List[float], treatment_values: List[float]) -> float:
        """Calculate Cohen's d effect size.
        
        Args:
            control_values: Control group values
            treatment_values: Treatment group values
            
        Returns:
            Cohen's d effect size
        """
        if len(control_values) < 2 or len(treatment_values) < 2:
            return 0.0
        
        control_mean = statistics.mean(control_values)
        treatment_mean = statistics.mean(treatment_values)
        
        control_std = statistics.stdev(control_values)
        treatment_std = statistics.stdev(treatment_values)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((len(control_values) - 1) * control_std**2 + 
                             (len(treatment_values) - 1) * treatment_std**2) / 
                            (len(control_values) + len(treatment_values) - 2))
        
        if pooled_std == 0:
            return 0.0
        
        return (treatment_mean - control_mean) / pooled_std
    
    def _get_metric_recommendation(self, metric: TestMetric, improvement: float, 
                                 is_significant: bool, effect_size: float) -> str:
        """Get recommendation for a metric.
        
        Args:
            metric: Test metric
            improvement: Improvement percentage
            is_significant: Whether the result is statistically significant
            effect_size: Effect size
            
        Returns:
            Recommendation string
        """
        if not is_significant:
            return "No significant difference detected"
        
        if metric.target_direction == "increase":
            if improvement > 0:
                if effect_size > 0.8:
                    return "Strong positive effect - recommend implementation"
                elif effect_size > 0.5:
                    return "Moderate positive effect - consider implementation"
                else:
                    return "Small positive effect - evaluate further"
            else:
                return "Negative effect - do not implement"
        
        elif metric.target_direction == "decrease":
            if improvement < 0:
                if abs(effect_size) > 0.8:
                    return "Strong negative effect - recommend implementation"
                elif abs(effect_size) > 0.5:
                    return "Moderate negative effect - consider implementation"
                else:
                    return "Small negative effect - evaluate further"
            else:
                return "Positive effect - do not implement"
        
        else:  # neutral
            if abs(effect_size) > 0.8:
                return "Strong effect detected - evaluate impact"
            elif abs(effect_size) > 0.5:
                return "Moderate effect detected - evaluate impact"
            else:
                return "Small effect detected - evaluate impact"
    
    def _get_overall_conclusion(self, variants: Dict[str, Any]) -> str:
        """Get overall conclusion for the test.
        
        Args:
            variants: Variant analysis results
            
        Returns:
            Overall conclusion string
        """
        if not variants:
            return "No data available"
        
        significant_metrics = 0
        positive_metrics = 0
        total_metrics = len(variants)
        
        for metric_name, metric_data in variants.items():
            if metric_data['is_significant']:
                significant_metrics += 1
                if metric_data['improvement_percentage'] > 0:
                    positive_metrics += 1
        
        if significant_metrics == 0:
            return "No significant differences detected"
        elif positive_metrics / significant_metrics > 0.7:
            return "Treatment shows positive results"
        elif positive_metrics / significant_metrics < 0.3:
            return "Treatment shows negative results"
        else:
            return "Mixed results - further evaluation needed"
    
    def _get_overall_recommendations(self, variants: Dict[str, Any]) -> List[str]:
        """Get overall recommendations for the test.
        
        Args:
            variants: Variant analysis results
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if not variants:
            recommendations.append("No data available for analysis")
            return recommendations
        
        significant_metrics = 0
        positive_metrics = 0
        strong_effects = 0
        
        for metric_name, metric_data in variants.items():
            if metric_data['is_significant']:
                significant_metrics += 1
                if metric_data['improvement_percentage'] > 0:
                    positive_metrics += 1
                if abs(metric_data['effect_size']) > 0.8:
                    strong_effects += 1
        
        if significant_metrics == 0:
            recommendations.append("Consider extending test duration or increasing sample size")
        elif positive_metrics / significant_metrics > 0.7:
            recommendations.append("Consider implementing treatment variant")
            if strong_effects > 0:
                recommendations.append("Strong effects detected - prioritize implementation")
        elif positive_metrics / significant_metrics < 0.3:
            recommendations.append("Do not implement treatment variant")
        else:
            recommendations.append("Mixed results - conduct additional analysis")
        
        return recommendations
    
    def generate_test_report(self, test_id: str, output_path: Optional[str] = None) -> str:
        """Generate a comprehensive test report.
        
        Args:
            test_id: Test identifier
            output_path: Path to save the report
            
        Returns:
            Path to the generated report
        """
        analysis = self.analyze_test_results(test_id)
        
        if 'error' in analysis:
            self.logger.error(f"Failed to generate report: {analysis['error']}")
            return ""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/ab_test_report_{test_id}_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        self.logger.info(f"Generated test report: {output_path}")
        return output_path
    
    def create_test(self, test_id: str, test_config: Dict[str, Any]) -> bool:
        """Create a new A/B test.
        
        Args:
            test_id: Test identifier
            test_config: Test configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.tests[test_id] = self._create_ab_test(test_id, test_config)
            self.logger.info(f"Created A/B test: {test_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create A/B test {test_id}: {e}")
            return False
    
    def start_test(self, test_id: str) -> bool:
        """Start an A/B test.
        
        Args:
            test_id: Test identifier
            
        Returns:
            True if successful, False otherwise
        """
        test = self.tests.get(test_id)
        if not test:
            self.logger.error(f"Test {test_id} not found")
            return False
        
        if test.status != TestStatus.DRAFT:
            self.logger.error(f"Test {test_id} is not in draft status")
            return False
        
        test.status = TestStatus.RUNNING
        test.start_date = datetime.now()
        
        self.logger.info(f"Started A/B test: {test_id}")
        return True
    
    def stop_test(self, test_id: str) -> bool:
        """Stop an A/B test.
        
        Args:
            test_id: Test identifier
            
        Returns:
            True if successful, False otherwise
        """
        test = self.tests.get(test_id)
        if not test:
            self.logger.error(f"Test {test_id} not found")
            return False
        
        if test.status != TestStatus.RUNNING:
            self.logger.error(f"Test {test_id} is not running")
            return False
        
        test.status = TestStatus.COMPLETED
        test.end_date = datetime.now()
        
        self.logger.info(f"Stopped A/B test: {test_id}")
        return True
    
    def save_tests(self, output_path: Optional[str] = None):
        """Save A/B tests to configuration file.
        
        Args:
            output_path: Path to save configuration file
        """
        if output_path is None:
            output_path = self.config_path
        
        config = {
            'ab_tests': {}
        }
        
        for test_id, test in self.tests.items():
            config['ab_tests'][test_id] = {
                'name': test.name,
                'description': test.description,
                'test_type': test.test_type.value,
                'status': test.status.value,
                'start_date': test.start_date.isoformat() if test.start_date else None,
                'end_date': test.end_date.isoformat() if test.end_date else None,
                'variants': [
                    {
                        'name': variant.name,
                        'description': variant.description,
                        'traffic_percentage': variant.traffic_percentage,
                        'configuration': variant.configuration,
                        'metadata': variant.metadata
                    } for variant in test.variants
                ],
                'metrics': [
                    {
                        'name': metric.name,
                        'description': metric.description,
                        'metric_type': metric.metric_type,
                        'aggregation': metric.aggregation,
                        'target_direction': metric.target_direction,
                        'minimum_detectable_effect': metric.minimum_detectable_effect,
                        'significance_level': metric.significance_level,
                        'power': metric.power
                    } for metric in test.metrics
                ],
                'target_sample_size': test.target_sample_size,
                'minimum_duration_days': test.minimum_duration_days,
                'maximum_duration_days': test.maximum_duration_days,
                'success_criteria': test.success_criteria,
                'metadata': test.metadata
            }
        
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Saved A/B tests to {output_path}")

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CHA A/B Testing System')
    parser.add_argument('--config', default='configs/ab_tests.yml', help='A/B tests configuration file')
    parser.add_argument('--action', choices=['list', 'create', 'start', 'stop', 'analyze', 'assign'], required=True, help='Action to perform')
    parser.add_argument('--test-id', help='Test identifier')
    parser.add_argument('--user-id', help='User identifier')
    parser.add_argument('--test-config', help='Test configuration (JSON format)')
    
    args = parser.parse_args()
    
    # Initialize A/B testing
    ab_testing = CHAABTesting(args.config)
    
    if args.action == 'list':
        tests = ab_testing.tests
        print("📋 A/B Tests:")
        for test_id, test in tests.items():
            print(f"  {test_id}: {test.name} ({test.status.value})")
    
    elif args.action == 'create':
        if not args.test_id or not args.test_config:
            print("Error: --test-id and --test-config are required for create action")
            return 1
        
        try:
            test_config = json.loads(args.test_config)
            success = ab_testing.create_test(args.test_id, test_config)
            if success:
                print(f"✅ Created A/B test: {args.test_id}")
            else:
                print(f"❌ Failed to create A/B test: {args.test_id}")
                return 1
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in test config: {e}")
            return 1
    
    elif args.action == 'start':
        if not args.test_id:
            print("Error: --test-id is required for start action")
            return 1
        
        success = ab_testing.start_test(args.test_id)
        if success:
            print(f"✅ Started A/B test: {args.test_id}")
        else:
            print(f"❌ Failed to start A/B test: {args.test_id}")
            return 1
    
    elif args.action == 'stop':
        if not args.test_id:
            print("Error: --test-id is required for stop action")
            return 1
        
        success = ab_testing.stop_test(args.test_id)
        if success:
            print(f"✅ Stopped A/B test: {args.test_id}")
        else:
            print(f"❌ Failed to stop A/B test: {args.test_id}")
            return 1
    
    elif args.action == 'analyze':
        if not args.test_id:
            print("Error: --test-id is required for analyze action")
            return 1
        
        analysis = ab_testing.analyze_test_results(args.test_id)
        if 'error' in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
            return 1
        
        print(f"📊 A/B Test Analysis: {analysis['test_name']}")
        print(f"   Status: {analysis['status']}")
        print(f"   Conclusion: {analysis['overall_conclusion']}")
        print("   Recommendations:")
        for rec in analysis['recommendations']:
            print(f"     - {rec}")
    
    elif args.action == 'assign':
        if not args.test_id or not args.user_id:
            print("Error: --test-id and --user-id are required for assign action")
            return 1
        
        variant = ab_testing.assign_user_to_variant(args.test_id, args.user_id)
        if variant:
            print(f"✅ User {args.user_id} assigned to variant: {variant}")
        else:
            print(f"❌ User {args.user_id} not assigned to any variant")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
