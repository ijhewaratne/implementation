#!/usr/bin/env python3
"""
Configuration Migration Script for ADK Integration
Migrates existing configuration files to ADK-compatible format.
"""

import yaml
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

def backup_config(config_path: str) -> str:
    """Create a backup of the configuration file."""
    backup_path = f"{config_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(config_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"❌ Error loading {config_path}: {e}")
        return {}

def save_config(config: Dict[str, Any], config_path: str):
    """Save configuration to YAML file."""
    try:
        with open(config_path, 'w') as f:
            yaml.safe_dump(config, f, default_flow_style=False, indent=2)
        print(f"✅ Saved configuration: {config_path}")
    except Exception as e:
        print(f"❌ Error saving {config_path}: {e}")

def migrate_gemini_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate old Gemini configuration to ADK-compatible format."""
    print("🔄 Migrating Gemini configuration to ADK format...")
    
    # Start with the old configuration
    new_config = old_config.copy()
    
    # Add ADK section if not present
    if 'adk' not in new_config:
        new_config['adk'] = {
            'enabled': True,
            'auto_detect': True,
            'initialization': {
                'timeout': 30,
                'retry_attempts': 3,
                'retry_delay': 5
            },
            'agents': {
                'default': {
                    'model': new_config.get('model', 'gemini-1.5-flash-latest'),
                    'temperature': new_config.get('temperature', 0.7),
                    'max_tokens': new_config.get('max_tokens', 2048),
                    'timeout': 60
                },
                'energy_planner': {
                    'temperature': 0.5,
                    'max_tokens': 1024
                },
                'central_heating': {
                    'temperature': 0.7,
                    'max_tokens': 2048
                },
                'decentralized_heating': {
                    'temperature': 0.7,
                    'max_tokens': 2048
                },
                'comparison': {
                    'temperature': 0.6,
                    'max_tokens': 2048
                },
                'analysis': {
                    'temperature': 0.7,
                    'max_tokens': 2048
                },
                'data_explorer': {
                    'temperature': 0.5,
                    'max_tokens': 1024
                },
                'energy_gpt': {
                    'temperature': 0.8,
                    'max_tokens': 2048
                }
            }
        }
    
    # Add tools section if not present
    if 'tools' not in new_config:
        new_config['tools'] = {
            'execution': {
                'timeout': 120,
                'retry_attempts': 2,
                'retry_delay': 3
            },
            'comprehensive_analysis': {
                'timeout': 300,
                'retry_attempts': 1
            },
            'data_exploration': {
                'timeout': 60,
                'retry_attempts': 2
            }
        }
    
    # Add error handling section if not present
    if 'error_handling' not in new_config:
        new_config['error_handling'] = {
            'quota': {
                'retry_delay': 60,
                'max_retries': 3,
                'exponential_backoff': True
            },
            'network': {
                'retry_delay': 5,
                'max_retries': 3,
                'exponential_backoff': True
            },
            'general': {
                'retry_delay': 2,
                'max_retries': 2,
                'exponential_backoff': False
            }
        }
    
    # Update fallback section
    if 'fallback' not in new_config:
        new_config['fallback'] = {
            'enabled': True,
            'mode': 'simple_agent',
            'simple_agent': {
                'model': new_config.get('model', 'gemini-1.5-flash-latest'),
                'temperature': new_config.get('temperature', 0.7),
                'max_tokens': new_config.get('max_tokens', 2048),
                'timeout': 60
            },
            'rule_based': {
                'delegation_rules': [
                    {'pattern': 'district heating|central heating|cha', 'agent': 'CHA'},
                    {'pattern': 'heat pump|decentralized|dha', 'agent': 'DHA'},
                    {'pattern': 'compare|comparison|scenario', 'agent': 'CA'},
                    {'pattern': 'analyze|analysis|comprehensive', 'agent': 'AA'},
                    {'pattern': 'data|explore|results|streets', 'agent': 'DEA'},
                    {'pattern': 'insights|recommendations|gpt', 'agent': 'EGPT'}
                ]
            }
        }
    else:
        # Update existing fallback configuration
        if 'mode' not in new_config['fallback']:
            new_config['fallback']['mode'] = 'simple_agent'
    
    # Add logging section if not present
    if 'logging' not in new_config:
        new_config['logging'] = {
            'level': 'INFO',
            'destinations': ['console', 'file'],
            'file': {
                'path': 'logs/gemini_adk.log',
                'max_size': '10MB',
                'backup_count': 5
            },
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    
    # Add monitoring section if not present
    if 'monitoring' not in new_config:
        new_config['monitoring'] = {
            'enabled': True,
            'metrics': ['response_time', 'token_usage', 'error_rate', 'quota_usage'],
            'thresholds': {
                'response_time_warning': 10,
                'response_time_error': 30,
                'error_rate_warning': 0.05,
                'error_rate_error': 0.10
            }
        }
    
    # Add security section if not present
    if 'security' not in new_config:
        new_config['security'] = {
            'api_key': {
                'env_var': 'GEMINI_API_KEY',
                'fallback_to_config': True
            },
            'log_requests': False,
            'log_responses': False,
            'privacy': {
                'mask_api_key': True,
                'mask_user_input': False
            }
        }
    
    # Add development section if not present
    if 'development' not in new_config:
        new_config['development'] = {
            'dev_mode': False,
            'testing': {
                'use_mocks': False,
                'test_data_dir': 'test_data',
                'timeout': 30
            }
        }
    
    # Add environments section if not present
    if 'environments' not in new_config:
        new_config['environments'] = {
            'development': {
                'logging': {'level': 'DEBUG'},
                'monitoring': {'enabled': True},
                'fallback': {'enabled': True},
                'development': {'dev_mode': {'enabled': True}}
            },
            'production': {
                'logging': {'level': 'WARNING'},
                'monitoring': {'enabled': True},
                'fallback': {'enabled': True},
                'security': {
                    'log_requests': False,
                    'log_responses': False,
                    'privacy': {'mask_user_input': True}
                }
            },
            'testing': {
                'logging': {'level': 'INFO'},
                'monitoring': {'enabled': False},
                'fallback': {'enabled': True},
                'development': {'testing': {'test_mode': {'enabled': True, 'use_mocks': True}}}
            }
        }
    
    print("✅ Gemini configuration migration completed")
    return new_config

def migrate_config_file(config_path: str, output_path: Optional[str] = None) -> bool:
    """Migrate a single configuration file."""
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    print(f"🔄 Migrating {config_path}...")
    
    # Create backup
    backup_path = backup_config(config_path)
    
    # Load old configuration
    old_config = load_config(config_path)
    if not old_config:
        print(f"❌ Failed to load configuration from {config_path}")
        return False
    
    # Migrate configuration
    if 'gemini_config' in config_path or 'gemini' in config_path:
        new_config = migrate_gemini_config(old_config)
    else:
        print(f"⚠️ Unknown configuration type for {config_path}, skipping migration")
        return False
    
    # Save migrated configuration
    output_path = output_path or config_path
    save_config(new_config, output_path)
    
    print(f"✅ Migration completed: {config_path} -> {output_path}")
    return True

def main():
    """Main migration function."""
    print("🔄 ADK Configuration Migration")
    print("=" * 50)
    
    # Configuration files to migrate
    config_files = [
        "configs/gemini_config.yml",
        "agents copy/configs/gemini_config.yml"
    ]
    
    success_count = 0
    total_count = len(config_files)
    
    for config_file in config_files:
        if os.path.exists(config_file):
            if migrate_config_file(config_file):
                success_count += 1
        else:
            print(f"⚠️ Configuration file not found: {config_file}")
    
    print("\n" + "=" * 50)
    print(f"Migration Summary: {success_count}/{total_count} files migrated successfully")
    
    if success_count == total_count:
        print("🎉 All configuration files migrated successfully!")
        print("\n📋 Next steps:")
        print("1. Review the migrated configuration files")
        print("2. Test the ADK system with: make test-adk-config")
        print("3. Run the ADK runner test: make test-adk-runner")
        return 0
    else:
        print("❌ Some configuration files failed to migrate.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
