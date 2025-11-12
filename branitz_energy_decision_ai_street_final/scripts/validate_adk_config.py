#!/usr/bin/env python3
"""
ADK Configuration Validation Script
Validates ADK configuration files for proper format and compatibility.
"""

import yaml
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema
from jsonschema import validate, ValidationError

def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading {config_path}: {e}")
        return {}

def validate_gemini_config(config: Dict[str, Any]) -> List[str]:
    """Validate Gemini configuration."""
    errors = []
    
    # Required fields
    required_fields = ['api_key', 'model', 'temperature', 'max_tokens']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate API key
    if 'api_key' in config:
        api_key = config['api_key']
        if not isinstance(api_key, str) or len(api_key) < 10:
            errors.append("Invalid API key format")
    
    # Validate model
    if 'model' in config:
        model = config['model']
        if not isinstance(model, str) or not model.startswith('gemini-'):
            errors.append("Invalid model format - should start with 'gemini-'")
    
    # Validate temperature
    if 'temperature' in config:
        temp = config['temperature']
        if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
            errors.append("Temperature must be between 0 and 2")
    
    # Validate max_tokens
    if 'max_tokens' in config:
        tokens = config['max_tokens']
        if not isinstance(tokens, int) or tokens <= 0:
            errors.append("Max tokens must be a positive integer")
    
    # Validate ADK section if present
    if 'adk' in config:
        adk_errors = validate_adk_section(config['adk'])
        errors.extend([f"ADK.{error}" for error in adk_errors])
    
    return errors

def validate_adk_section(adk_config: Dict[str, Any]) -> List[str]:
    """Validate ADK configuration section."""
    errors = []
    
    # Validate enabled flag
    if 'enabled' in adk_config:
        if not isinstance(adk_config['enabled'], bool):
            errors.append("enabled must be a boolean")
    
    # Validate initialization settings
    if 'initialization' in adk_config:
        init_config = adk_config['initialization']
        if 'timeout' in init_config:
            if not isinstance(init_config['timeout'], (int, float)) or init_config['timeout'] <= 0:
                errors.append("initialization.timeout must be a positive number")
        
        if 'retry_attempts' in init_config:
            if not isinstance(init_config['retry_attempts'], int) or init_config['retry_attempts'] < 0:
                errors.append("initialization.retry_attempts must be a non-negative integer")
    
    # Validate agent settings
    if 'agents' in adk_config:
        agent_errors = validate_agent_settings(adk_config['agents'])
        errors.extend([f"agents.{error}" for error in agent_errors])
    
    return errors

def validate_agent_settings(agent_config: Dict[str, Any]) -> List[str]:
    """Validate agent configuration settings."""
    errors = []
    
    # Validate default settings
    if 'default' in agent_config:
        default_config = agent_config['default']
        if 'temperature' in default_config:
            temp = default_config['temperature']
            if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
                errors.append("default.temperature must be between 0 and 2")
        
        if 'max_tokens' in default_config:
            tokens = default_config['max_tokens']
            if not isinstance(tokens, int) or tokens <= 0:
                errors.append("default.max_tokens must be a positive integer")
    
    # Validate agent-specific settings
    agent_names = ['energy_planner', 'central_heating', 'decentralized_heating', 
                   'comparison', 'analysis', 'data_explorer', 'energy_gpt']
    
    for agent_name in agent_names:
        if agent_name in agent_config:
            agent_specific = agent_config[agent_name]
            if 'temperature' in agent_specific:
                temp = agent_specific['temperature']
                if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
                    errors.append(f"{agent_name}.temperature must be between 0 and 2")
    
    return errors

def validate_tool_config(tool_config: Dict[str, Any]) -> List[str]:
    """Validate tool configuration."""
    errors = []
    
    # Validate execution settings
    if 'execution' in tool_config:
        exec_config = tool_config['execution']
        if 'timeout' in exec_config:
            if not isinstance(exec_config['timeout'], (int, float)) or exec_config['timeout'] <= 0:
                errors.append("execution.timeout must be a positive number")
        
        if 'retry_attempts' in exec_config:
            if not isinstance(exec_config['retry_attempts'], int) or exec_config['retry_attempts'] < 0:
                errors.append("execution.retry_attempts must be a non-negative integer")
    
    return errors

def validate_error_handling(error_config: Dict[str, Any]) -> List[str]:
    """Validate error handling configuration."""
    errors = []
    
    # Validate quota settings
    if 'quota' in error_config:
        quota_config = error_config['quota']
        if 'retry_delay' in quota_config:
            if not isinstance(quota_config['retry_delay'], (int, float)) or quota_config['retry_delay'] <= 0:
                errors.append("quota.retry_delay must be a positive number")
        
        if 'max_retries' in quota_config:
            if not isinstance(quota_config['max_retries'], int) or quota_config['max_retries'] < 0:
                errors.append("quota.max_retries must be a non-negative integer")
    
    return errors

def validate_fallback_config(fallback_config: Dict[str, Any]) -> List[str]:
    """Validate fallback configuration."""
    errors = []
    
    # Validate mode
    if 'mode' in fallback_config:
        valid_modes = ['simple_agent', 'rule_based', 'mock_ai']
        if fallback_config['mode'] not in valid_modes:
            errors.append(f"fallback.mode must be one of: {valid_modes}")
    
    # Validate rule-based settings
    if 'rule_based' in fallback_config:
        rule_config = fallback_config['rule_based']
        if 'delegation_rules' in rule_config:
            rules = rule_config['delegation_rules']
            if not isinstance(rules, list):
                errors.append("fallback.rule_based.delegation_rules must be a list")
            else:
                for i, rule in enumerate(rules):
                    if not isinstance(rule, dict):
                        errors.append(f"fallback.rule_based.delegation_rules[{i}] must be a dictionary")
                    else:
                        required_rule_fields = ['pattern', 'agent']
                        for field in required_rule_fields:
                            if field not in rule:
                                errors.append(f"fallback.rule_based.delegation_rules[{i}] missing required field: {field}")
    
    return errors

def validate_adk_config(config: Dict[str, Any]) -> List[str]:
    """Validate ADK-specific configuration."""
    errors = []
    
    # Validate core ADK settings
    if 'adk' in config:
        adk_errors = validate_adk_section(config['adk'])
        errors.extend([f"adk.{error}" for error in adk_errors])
    
    # Validate performance settings
    if 'performance' in config:
        perf_config = config['performance']
        if 'caching' in perf_config:
            cache_config = perf_config['caching']
            if 'cache_size' in cache_config:
                cache_size = cache_config['cache_size']
                if not isinstance(cache_size, str) or not cache_size.endswith(('MB', 'GB')):
                    errors.append("performance.caching.cache_size must be a string ending with MB or GB")
    
    return errors

def validate_config_file(config_path: str) -> Dict[str, Any]:
    """Validate a configuration file."""
    print(f"🔍 Validating {config_path}...")
    
    config = load_yaml_config(config_path)
    if not config:
        return {"valid": False, "errors": ["Failed to load configuration"]}
    
    errors = []
    
    # Determine config type and validate accordingly
    if 'gemini_config' in config_path or 'gemini' in config_path:
        errors.extend(validate_gemini_config(config))
    elif 'adk_config' in config_path or 'adk' in config_path:
        errors.extend(validate_adk_config(config))
    
    # Validate common sections
    if 'tools' in config:
        tool_errors = validate_tool_config(config['tools'])
        errors.extend([f"tools.{error}" for error in tool_errors])
    
    if 'error_handling' in config:
        error_errors = validate_error_handling(config['error_handling'])
        errors.extend([f"error_handling.{error}" for error in error_errors])
    
    if 'fallback' in config:
        fallback_errors = validate_fallback_config(config['fallback'])
        errors.extend([f"fallback.{error}" for error in fallback_errors])
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "config": config
    }

def main():
    """Main validation function."""
    print("🔧 ADK Configuration Validation")
    print("=" * 50)
    
    # Configuration files to validate
    config_files = [
        "configs/gemini_config.yml",
        "configs/gemini_config_adk.yml",
        "configs/adk_config.yml",
        "agents copy/configs/gemini_config.yml"
    ]
    
    results = {}
    all_valid = True
    
    for config_file in config_files:
        if os.path.exists(config_file):
            result = validate_config_file(config_file)
            results[config_file] = result
            
            if result["valid"]:
                print(f"✅ {config_file}: Valid")
            else:
                print(f"❌ {config_file}: Invalid")
                for error in result["errors"]:
                    print(f"   - {error}")
                all_valid = False
        else:
            print(f"⚠️ {config_file}: Not found")
            results[config_file] = {"valid": False, "errors": ["File not found"]}
            all_valid = False
    
    print("\n" + "=" * 50)
    if all_valid:
        print("🎉 All configuration files are valid!")
        return 0
    else:
        print("❌ Some configuration files have errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
