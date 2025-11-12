#!/usr/bin/env python3
"""
CHA Feature Flags System

This module provides a comprehensive feature flag system for the CHA Intelligent Pipe Sizing System,
enabling gradual rollout, A/B testing, and controlled feature deployment.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import hashlib

class FeatureFlagType(Enum):
    """Types of feature flags."""
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    USER_GROUP = "user_group"
    A_B_TEST = "a_b_test"
    TIME_BASED = "time_based"

class FeatureFlagStatus(Enum):
    """Status of feature flags."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ROLLING_OUT = "rolling_out"
    ROLLING_BACK = "rolling_back"

@dataclass
class FeatureFlag:
    """Feature flag definition."""
    name: str
    description: str
    flag_type: FeatureFlagType
    status: FeatureFlagStatus
    enabled: bool
    rollout_percentage: float = 0.0
    user_groups: List[str] = None
    a_b_test_variants: Dict[str, float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.user_groups is None:
            self.user_groups = []
        if self.a_b_test_variants is None:
            self.a_b_test_variants = {}
        if self.metadata is None:
            self.metadata = {}

@dataclass
class FeatureFlagEvaluation:
    """Result of feature flag evaluation."""
    flag_name: str
    enabled: bool
    variant: Optional[str] = None
    reason: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class CHAFeatureFlags:
    """Feature flags system for CHA."""
    
    def __init__(self, config_path: str = "configs/feature_flags.yml"):
        """Initialize the feature flags system.
        
        Args:
            config_path: Path to feature flags configuration file
        """
        self.config_path = config_path
        self.flags: Dict[str, FeatureFlag] = {}
        self.evaluation_cache: Dict[str, FeatureFlagEvaluation] = {}
        self.logger = logging.getLogger(__name__)
        
        # Load feature flags configuration
        self._load_feature_flags()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for feature flags."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_feature_flags(self):
        """Load feature flags from configuration file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                for flag_name, flag_config in config.get('feature_flags', {}).items():
                    self.flags[flag_name] = self._create_feature_flag(flag_name, flag_config)
                
                self.logger.info(f"Loaded {len(self.flags)} feature flags from {self.config_path}")
            else:
                self.logger.warning(f"Feature flags configuration file not found: {self.config_path}")
                self._create_default_flags()
                
        except Exception as e:
            self.logger.error(f"Failed to load feature flags: {e}")
            self._create_default_flags()
    
    def _create_feature_flag(self, name: str, config: Dict[str, Any]) -> FeatureFlag:
        """Create a feature flag from configuration.
        
        Args:
            name: Feature flag name
            config: Feature flag configuration
            
        Returns:
            Feature flag object
        """
        return FeatureFlag(
            name=name,
            description=config.get('description', ''),
            flag_type=FeatureFlagType(config.get('type', 'boolean')),
            status=FeatureFlagStatus(config.get('status', 'disabled')),
            enabled=config.get('enabled', False),
            rollout_percentage=config.get('rollout_percentage', 0.0),
            user_groups=config.get('user_groups', []),
            a_b_test_variants=config.get('a_b_test_variants', {}),
            start_time=self._parse_datetime(config.get('start_time')),
            end_time=self._parse_datetime(config.get('end_time')),
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
    
    def _create_default_flags(self):
        """Create default feature flags."""
        default_flags = {
            'intelligent_pipe_sizing': {
                'description': 'Enable intelligent pipe sizing engine',
                'type': 'boolean',
                'status': 'enabled',
                'enabled': True
            },
            'enhanced_flow_calculation': {
                'description': 'Enable enhanced flow calculation with safety factors',
                'type': 'boolean',
                'status': 'enabled',
                'enabled': True
            },
            'network_hierarchy_analysis': {
                'description': 'Enable network hierarchy analysis',
                'type': 'boolean',
                'status': 'enabled',
                'enabled': True
            },
            'standards_compliance': {
                'description': 'Enable engineering standards compliance checking',
                'type': 'boolean',
                'status': 'enabled',
                'enabled': True
            },
            'performance_optimization': {
                'description': 'Enable performance optimization features',
                'type': 'boolean',
                'status': 'enabled',
                'enabled': True
            },
            'cost_benefit_analysis': {
                'description': 'Enable cost-benefit analysis',
                'type': 'boolean',
                'status': 'enabled',
                'enabled': True
            },
            'advanced_validation': {
                'description': 'Enable advanced validation features',
                'type': 'boolean',
                'status': 'enabled',
                'enabled': True
            },
            'pandapipes_integration': {
                'description': 'Enable enhanced pandapipes integration',
                'type': 'boolean',
                'status': 'enabled',
                'enabled': True
            }
        }
        
        for flag_name, flag_config in default_flags.items():
            self.flags[flag_name] = self._create_feature_flag(flag_name, flag_config)
        
        self.logger.info(f"Created {len(self.flags)} default feature flags")
    
    def is_enabled(self, flag_name: str, user_id: Optional[str] = None, 
                   user_groups: Optional[List[str]] = None, 
                   context: Optional[Dict[str, Any]] = None) -> FeatureFlagEvaluation:
        """Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
            user_id: User identifier for user-based flags
            user_groups: User groups for group-based flags
            context: Additional context for evaluation
            
        Returns:
            Feature flag evaluation result
        """
        # Check cache first
        cache_key = f"{flag_name}:{user_id}:{user_groups}:{context}"
        if cache_key in self.evaluation_cache:
            return self.evaluation_cache[cache_key]
        
        # Get feature flag
        flag = self.flags.get(flag_name)
        if not flag:
            evaluation = FeatureFlagEvaluation(
                flag_name=flag_name,
                enabled=False,
                reason="Feature flag not found"
            )
            self.evaluation_cache[cache_key] = evaluation
            return evaluation
        
        # Evaluate based on flag type
        if flag.flag_type == FeatureFlagType.BOOLEAN:
            evaluation = self._evaluate_boolean_flag(flag, user_id, user_groups, context)
        elif flag.flag_type == FeatureFlagType.PERCENTAGE:
            evaluation = self._evaluate_percentage_flag(flag, user_id, user_groups, context)
        elif flag.flag_type == FeatureFlagType.USER_GROUP:
            evaluation = self._evaluate_user_group_flag(flag, user_id, user_groups, context)
        elif flag.flag_type == FeatureFlagType.A_B_TEST:
            evaluation = self._evaluate_ab_test_flag(flag, user_id, user_groups, context)
        elif flag.flag_type == FeatureFlagType.TIME_BASED:
            evaluation = self._evaluate_time_based_flag(flag, user_id, user_groups, context)
        else:
            evaluation = FeatureFlagEvaluation(
                flag_name=flag_name,
                enabled=False,
                reason="Unknown flag type"
            )
        
        # Cache the result
        self.evaluation_cache[cache_key] = evaluation
        
        # Log evaluation
        self.logger.info(f"Feature flag '{flag_name}' evaluated: {evaluation.enabled} ({evaluation.reason})")
        
        return evaluation
    
    def _evaluate_boolean_flag(self, flag: FeatureFlag, user_id: Optional[str], 
                              user_groups: Optional[List[str]], 
                              context: Optional[Dict[str, Any]]) -> FeatureFlagEvaluation:
        """Evaluate a boolean feature flag.
        
        Args:
            flag: Feature flag to evaluate
            user_id: User identifier
            user_groups: User groups
            context: Additional context
            
        Returns:
            Feature flag evaluation result
        """
        if flag.status == FeatureFlagStatus.DISABLED:
            return FeatureFlagEvaluation(
                flag_name=flag.name,
                enabled=False,
                reason="Flag is disabled"
            )
        
        if flag.status == FeatureFlagStatus.ENABLED:
            return FeatureFlagEvaluation(
                flag_name=flag.name,
                enabled=True,
                reason="Flag is enabled"
            )
        
        # For rolling out/rolling back, check rollout percentage
        if flag.rollout_percentage > 0 and user_id:
            user_hash = self._hash_user_id(user_id)
            if user_hash < flag.rollout_percentage:
                return FeatureFlagEvaluation(
                    flag_name=flag.name,
                    enabled=True,
                    reason=f"User in rollout group ({flag.rollout_percentage}%)"
                )
            else:
                return FeatureFlagEvaluation(
                    flag_name=flag.name,
                    enabled=False,
                    reason=f"User not in rollout group ({flag.rollout_percentage}%)"
                )
        
        return FeatureFlagEvaluation(
            flag_name=flag.name,
            enabled=flag.enabled,
            reason="Default evaluation"
        )
    
    def _evaluate_percentage_flag(self, flag: FeatureFlag, user_id: Optional[str], 
                                 user_groups: Optional[List[str]], 
                                 context: Optional[Dict[str, Any]]) -> FeatureFlagEvaluation:
        """Evaluate a percentage-based feature flag.
        
        Args:
            flag: Feature flag to evaluate
            user_id: User identifier
            user_groups: User groups
            context: Additional context
            
        Returns:
            Feature flag evaluation result
        """
        if flag.status == FeatureFlagStatus.DISABLED:
            return FeatureFlagEvaluation(
                flag_name=flag.name,
                enabled=False,
                reason="Flag is disabled"
            )
        
        if flag.status == FeatureFlagStatus.ENABLED:
            return FeatureFlagEvaluation(
                flag_name=flag.name,
                enabled=True,
                reason="Flag is enabled"
            )
        
        # Check rollout percentage
        if user_id and flag.rollout_percentage > 0:
            user_hash = self._hash_user_id(user_id)
            if user_hash < flag.rollout_percentage:
                return FeatureFlagEvaluation(
                    flag_name=flag.name,
                    enabled=True,
                    reason=f"User in rollout group ({flag.rollout_percentage}%)"
                )
            else:
                return FeatureFlagEvaluation(
                    flag_name=flag.name,
                    enabled=False,
                    reason=f"User not in rollout group ({flag.rollout_percentage}%)"
                )
        
        return FeatureFlagEvaluation(
            flag_name=flag.name,
            enabled=flag.enabled,
            reason="Default evaluation"
        )
    
    def _evaluate_user_group_flag(self, flag: FeatureFlag, user_id: Optional[str], 
                                 user_groups: Optional[List[str]], 
                                 context: Optional[Dict[str, Any]]) -> FeatureFlagEvaluation:
        """Evaluate a user group-based feature flag.
        
        Args:
            flag: Feature flag to evaluate
            user_id: User identifier
            user_groups: User groups
            context: Additional context
            
        Returns:
            Feature flag evaluation result
        """
        if flag.status == FeatureFlagStatus.DISABLED:
            return FeatureFlagEvaluation(
                flag_name=flag.name,
                enabled=False,
                reason="Flag is disabled"
            )
        
        if flag.status == FeatureFlagStatus.ENABLED:
            return FeatureFlagEvaluation(
                flag_name=flag.name,
                enabled=True,
                reason="Flag is enabled"
            )
        
        # Check user groups
        if user_groups and flag.user_groups:
            for user_group in user_groups:
                if user_group in flag.user_groups:
                    return FeatureFlagEvaluation(
                        flag_name=flag.name,
                        enabled=True,
                        reason=f"User in group: {user_group}"
                    )
        
        return FeatureFlagEvaluation(
            flag_name=flag.name,
            enabled=False,
            reason="User not in allowed groups"
        )
    
    def _evaluate_ab_test_flag(self, flag: FeatureFlag, user_id: Optional[str], 
                              user_groups: Optional[List[str]], 
                              context: Optional[Dict[str, Any]]) -> FeatureFlagEvaluation:
        """Evaluate an A/B test feature flag.
        
        Args:
            flag: Feature flag to evaluate
            user_id: User identifier
            user_groups: User groups
            context: Additional context
            
        Returns:
            Feature flag evaluation result
        """
        if flag.status == FeatureFlagStatus.DISABLED:
            return FeatureFlagEvaluation(
                flag_name=flag.name,
                enabled=False,
                reason="A/B test is disabled"
            )
        
        if not user_id or not flag.a_b_test_variants:
            return FeatureFlagEvaluation(
                flag_name=flag.name,
                enabled=flag.enabled,
                reason="No user ID or variants defined"
            )
        
        # Determine variant based on user hash
        user_hash = self._hash_user_id(user_id)
        cumulative_percentage = 0.0
        
        for variant, percentage in flag.a_b_test_variants.items():
            cumulative_percentage += percentage
            if user_hash < cumulative_percentage:
                return FeatureFlagEvaluation(
                    flag_name=flag.name,
                    enabled=True,
                    variant=variant,
                    reason=f"User assigned to variant: {variant}"
                )
        
        # Fallback to control group
        return FeatureFlagEvaluation(
            flag_name=flag.name,
            enabled=False,
            variant="control",
            reason="User assigned to control group"
        )
    
    def _evaluate_time_based_flag(self, flag: FeatureFlag, user_id: Optional[str], 
                                 user_groups: Optional[List[str]], 
                                 context: Optional[Dict[str, Any]]) -> FeatureFlagEvaluation:
        """Evaluate a time-based feature flag.
        
        Args:
            flag: Feature flag to evaluate
            user_id: User identifier
            user_groups: User groups
            context: Additional context
            
        Returns:
            Feature flag evaluation result
        """
        current_time = datetime.now()
        
        # Check if flag is within time window
        if flag.start_time and current_time < flag.start_time:
            return FeatureFlagEvaluation(
                flag_name=flag.name,
                enabled=False,
                reason=f"Flag not yet active (starts at {flag.start_time})"
            )
        
        if flag.end_time and current_time > flag.end_time:
            return FeatureFlagEvaluation(
                flag_name=flag.name,
                enabled=False,
                reason=f"Flag expired (ended at {flag.end_time})"
            )
        
        # Evaluate based on other criteria
        if flag.flag_type == FeatureFlagType.PERCENTAGE:
            return self._evaluate_percentage_flag(flag, user_id, user_groups, context)
        elif flag.flag_type == FeatureFlagType.USER_GROUP:
            return self._evaluate_user_group_flag(flag, user_id, user_groups, context)
        else:
            return FeatureFlagEvaluation(
                flag_name=flag.name,
                enabled=flag.enabled,
                reason="Time-based flag is active"
            )
    
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
    
    def update_flag(self, flag_name: str, updates: Dict[str, Any]):
        """Update a feature flag.
        
        Args:
            flag_name: Name of the feature flag
            updates: Updates to apply
        """
        if flag_name not in self.flags:
            self.logger.warning(f"Feature flag '{flag_name}' not found")
            return
        
        flag = self.flags[flag_name]
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(flag, key):
                setattr(flag, key, value)
        
        # Clear cache
        self.evaluation_cache.clear()
        
        self.logger.info(f"Updated feature flag '{flag_name}'")
    
    def save_flags(self, output_path: Optional[str] = None):
        """Save feature flags to configuration file.
        
        Args:
            output_path: Path to save configuration file
        """
        if output_path is None:
            output_path = self.config_path
        
        config = {
            'feature_flags': {}
        }
        
        for flag_name, flag in self.flags.items():
            config['feature_flags'][flag_name] = {
                'description': flag.description,
                'type': flag.flag_type.value,
                'status': flag.status.value,
                'enabled': flag.enabled,
                'rollout_percentage': flag.rollout_percentage,
                'user_groups': flag.user_groups,
                'a_b_test_variants': flag.a_b_test_variants,
                'start_time': flag.start_time.isoformat() if flag.start_time else None,
                'end_time': flag.end_time.isoformat() if flag.end_time else None,
                'metadata': flag.metadata
            }
        
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Saved feature flags to {output_path}")
    
    def get_flag_status(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get the status of a feature flag.
        
        Args:
            flag_name: Name of the feature flag
            
        Returns:
            Feature flag object or None
        """
        return self.flags.get(flag_name)
    
    def list_flags(self) -> List[FeatureFlag]:
        """List all feature flags.
        
        Returns:
            List of feature flags
        """
        return list(self.flags.values())
    
    def clear_cache(self):
        """Clear the evaluation cache."""
        self.evaluation_cache.clear()
        self.logger.info("Cleared feature flags evaluation cache")

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CHA Feature Flags System')
    parser.add_argument('--config', default='configs/feature_flags.yml', help='Feature flags configuration file')
    parser.add_argument('--action', choices=['list', 'check', 'update', 'save'], required=True, help='Action to perform')
    parser.add_argument('--flag', help='Feature flag name')
    parser.add_argument('--user-id', help='User ID for evaluation')
    parser.add_argument('--user-groups', nargs='+', help='User groups')
    parser.add_argument('--updates', help='Updates to apply (JSON format)')
    
    args = parser.parse_args()
    
    # Initialize feature flags
    feature_flags = CHAFeatureFlags(args.config)
    
    if args.action == 'list':
        flags = feature_flags.list_flags()
        print("📋 Feature Flags:")
        for flag in flags:
            print(f"  {flag.name}: {flag.status.value} ({flag.flag_type.value})")
    
    elif args.action == 'check':
        if not args.flag:
            print("Error: --flag is required for check action")
            return 1
        
        evaluation = feature_flags.is_enabled(args.flag, args.user_id, args.user_groups)
        print(f"🔍 Feature Flag: {evaluation.flag_name}")
        print(f"   Enabled: {evaluation.enabled}")
        print(f"   Variant: {evaluation.variant}")
        print(f"   Reason: {evaluation.reason}")
    
    elif args.action == 'update':
        if not args.flag or not args.updates:
            print("Error: --flag and --updates are required for update action")
            return 1
        
        try:
            updates = json.loads(args.updates)
            feature_flags.update_flag(args.flag, updates)
            print(f"✅ Updated feature flag: {args.flag}")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in updates: {e}")
            return 1
    
    elif args.action == 'save':
        feature_flags.save_flags()
        print("✅ Saved feature flags configuration")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
