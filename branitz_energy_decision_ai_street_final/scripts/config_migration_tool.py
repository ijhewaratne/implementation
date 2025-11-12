#!/usr/bin/env python3
"""
CHA Configuration Migration Tool - Standalone Script

This script provides a comprehensive configuration migration and validation tool
for the CHA system, including:
- Configuration migration between versions
- Configuration validation
- Template generation
- Batch processing
- Migration reporting
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cha_config_migration import CHAConfigMigrationTool
from cha_backward_compatible_config import CHABackwardCompatibleConfigLoader

def list_configurations(config_dir: str = "configs") -> None:
    """List all configuration files with their status."""
    print("📋 CHA Configuration Files")
    print("=" * 50)
    
    migration_tool = CHAConfigMigrationTool(config_dir)
    configs = migration_tool.list_configs()
    
    if not configs:
        print("No configuration files found.")
        return
    
    for config in configs:
        status_icon = "✅" if config['valid'] else "❌"
        print(f"{status_icon} {config['name']}")
        print(f"   Version: {config['version']}")
        print(f"   Path: {config['path']}")
        print(f"   Size: {config['size_bytes']} bytes")
        print(f"   Modified: {config['modified']}")
        
        if config['errors']:
            print("   Errors:")
            for error in config['errors']:
                print(f"     - {error}")
        
        if config['warnings']:
            print("   Warnings:")
            for warning in config['warnings']:
                print(f"     - {warning}")
        
        print()

def validate_configuration(config_path: str, verbose: bool = False) -> bool:
    """Validate a configuration file."""
    print(f"🔍 Validating Configuration: {config_path}")
    print("=" * 50)
    
    migration_tool = CHAConfigMigrationTool()
    result = migration_tool.validate_config(config_path)
    
    if result.valid:
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration is invalid")
        for error in result.errors:
            print(f"   - {error}")
    
    if result.warnings:
        print("⚠️  Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")
    
    if result.suggestions:
        print("💡 Suggestions:")
        for suggestion in result.suggestions:
            print(f"   - {suggestion}")
    
    if verbose:
        print(f"\n📊 Validation Details:")
        print(f"   Config Path: {result.config_path}")
        print(f"   Timestamp: {result.timestamp}")
        print(f"   Errors: {len(result.errors)}")
        print(f"   Warnings: {len(result.warnings)}")
        print(f"   Suggestions: {len(result.suggestions)}")
    
    return result.valid

def migrate_configuration(source_path: str, target_path: str, 
                        migration_type: str = "auto", backup: bool = True) -> bool:
    """Migrate a configuration file."""
    print(f"🔄 Migrating Configuration")
    print(f"   Source: {source_path}")
    print(f"   Target: {target_path}")
    print(f"   Type: {migration_type}")
    print("=" * 50)
    
    migration_tool = CHAConfigMigrationTool()
    result = migration_tool.migrate_config(source_path, target_path, migration_type)
    
    if result.success:
        print("✅ Migration successful")
        if result.backup_created:
            print(f"📁 Backup created: {result.backup_path}")
    else:
        print("❌ Migration failed")
        for error in result.errors:
            print(f"   - {error}")
    
    if result.warnings:
        print("⚠️  Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")
    
    print(f"\n📊 Migration Details:")
    print(f"   Success: {result.success}")
    print(f"   Timestamp: {result.timestamp}")
    print(f"   Backup Created: {result.backup_created}")
    print(f"   Changes: {len(result.changes)}")
    
    return result.success

def create_template(template_name: str, template_type: str = "cha_intelligent_sizing") -> str:
    """Create a configuration template."""
    print(f"📝 Creating Template: {template_name}")
    print(f"   Type: {template_type}")
    print("=" * 50)
    
    migration_tool = CHAConfigMigrationTool()
    template_path = migration_tool.create_config_template(template_name, template_type)
    
    print(f"✅ Template created: {template_path}")
    return template_path

def batch_migrate(config_dir: str = "configs", target_dir: str = None, 
                 migration_type: str = "auto") -> Dict[str, Any]:
    """Perform batch migration of all configuration files."""
    print("🔄 Batch Migration")
    print(f"   Source Directory: {config_dir}")
    print(f"   Target Directory: {target_dir or config_dir + '_migrated'}")
    print(f"   Migration Type: {migration_type}")
    print("=" * 50)
    
    migration_tool = CHAConfigMigrationTool(config_dir)
    configs = migration_tool.list_configs()
    
    if target_dir:
        target_path = Path(target_dir)
        target_path.mkdir(exist_ok=True)
    else:
        target_path = Path(config_dir + '_migrated')
        target_path.mkdir(exist_ok=True)
    
    results = {
        'total_configs': len(configs),
        'successful_migrations': 0,
        'failed_migrations': 0,
        'migration_results': []
    }
    
    for config in configs:
        if config['name'].startswith('.') or 'backup' in config['name'] or 'template' in config['name']:
            continue
        
        source_path = config['path']
        target_path_file = target_path / f"{config['name']}_migrated"
        
        print(f"\n📁 Processing: {config['name']}")
        
        try:
            success = migrate_configuration(str(source_path), str(target_path_file), migration_type)
            
            if success:
                results['successful_migrations'] += 1
                print(f"✅ Migrated: {config['name']}")
            else:
                results['failed_migrations'] += 1
                print(f"❌ Failed: {config['name']}")
            
            results['migration_results'].append({
                'source': str(source_path),
                'target': str(target_path_file),
                'success': success,
                'version': config['version']
            })
            
        except Exception as e:
            results['failed_migrations'] += 1
            print(f"❌ Error migrating {config['name']}: {e}")
            results['migration_results'].append({
                'source': str(source_path),
                'target': str(target_path_file),
                'success': False,
                'error': str(e),
                'version': config['version']
            })
    
    print(f"\n📊 Batch Migration Summary:")
    print(f"   Total Configs: {results['total_configs']}")
    print(f"   Successful: {results['successful_migrations']}")
    print(f"   Failed: {results['failed_migrations']}")
    print(f"   Success Rate: {(results['successful_migrations'] / results['total_configs'] * 100):.1f}%")
    
    return results

def generate_migration_report(config_dir: str = "configs", output_path: str = None) -> str:
    """Generate a comprehensive migration report."""
    print("📊 Generating Migration Report")
    print("=" * 50)
    
    migration_tool = CHAConfigMigrationTool(config_dir)
    report_path = migration_tool.generate_migration_report(output_path)
    
    print(f"✅ Migration report generated: {report_path}")
    return report_path

def check_compatibility(config_path: str) -> None:
    """Check configuration compatibility."""
    print(f"🔍 Checking Compatibility: {config_path}")
    print("=" * 50)
    
    try:
        loader = CHABackwardCompatibleConfigLoader(config_path)
        
        print(f"📁 Configuration: {config_path}")
        print(f"🔧 Version: {loader.get_version()}")
        print(f"✅ Compatible: {loader.is_compatible()}")
        
        compatibility_info = loader.get_compatibility_info()
        if compatibility_info:
            print(f"📅 Compatibility Timestamp: {compatibility_info.get('compatibility_timestamp', 'N/A')}")
            print(f"🔄 Original Version: {compatibility_info.get('original_version', 'N/A')}")
        
        missing_sections = loader.get_missing_sections()
        if missing_sections:
            print(f"⚠️  Missing Sections: {', '.join(missing_sections)}")
        else:
            print("✅ All required sections present")
        
        recommendations = loader.get_upgrade_recommendations()
        if recommendations:
            print("\n💡 Upgrade Recommendations:")
            for rec in recommendations:
                print(f"   - {rec}")
        
    except Exception as e:
        print(f"❌ Error checking compatibility: {e}")

def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description='CHA Configuration Migration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all configurations
  python scripts/config_migration_tool.py list

  # Validate a configuration
  python scripts/config_migration_tool.py validate configs/cha.yml

  # Migrate a configuration
  python scripts/config_migration_tool.py migrate configs/cha.yml configs/cha_migrated.yml

  # Create a template
  python scripts/config_migration_tool.py template my_template

  # Batch migrate all configurations
  python scripts/config_migration_tool.py batch-migrate

  # Generate migration report
  python scripts/config_migration_tool.py report

  # Check compatibility
  python scripts/config_migration_tool.py compatibility configs/cha.yml
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all configuration files')
    list_parser.add_argument('--config-dir', default='configs', help='Configuration directory')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a configuration file')
    validate_parser.add_argument('config_path', help='Path to configuration file')
    validate_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate a configuration file')
    migrate_parser.add_argument('source_path', help='Source configuration file')
    migrate_parser.add_argument('target_path', help='Target configuration file')
    migrate_parser.add_argument('--migration-type', default='auto', 
                               choices=['auto', 'cha_v1_to_cha_v2', 'cha_v2_to_cha_intelligent_sizing'],
                               help='Migration type')
    migrate_parser.add_argument('--no-backup', action='store_true', help='Skip backup creation')
    
    # Template command
    template_parser = subparsers.add_parser('template', help='Create a configuration template')
    template_parser.add_argument('template_name', help='Template name')
    template_parser.add_argument('--template-type', default='cha_intelligent_sizing',
                                choices=['cha_v1', 'cha_v2', 'cha_intelligent_sizing'],
                                help='Template type')
    
    # Batch migrate command
    batch_parser = subparsers.add_parser('batch-migrate', help='Batch migrate all configurations')
    batch_parser.add_argument('--config-dir', default='configs', help='Source configuration directory')
    batch_parser.add_argument('--target-dir', help='Target configuration directory')
    batch_parser.add_argument('--migration-type', default='auto',
                             choices=['auto', 'cha_v1_to_cha_v2', 'cha_v2_to_cha_intelligent_sizing'],
                             help='Migration type')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate migration report')
    report_parser.add_argument('--config-dir', default='configs', help='Configuration directory')
    report_parser.add_argument('--output', help='Output file path')
    
    # Compatibility command
    compat_parser = subparsers.add_parser('compatibility', help='Check configuration compatibility')
    compat_parser.add_argument('config_path', help='Path to configuration file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'list':
            list_configurations(args.config_dir)
        
        elif args.command == 'validate':
            success = validate_configuration(args.config_path, args.verbose)
            return 0 if success else 1
        
        elif args.command == 'migrate':
            success = migrate_configuration(args.source_path, args.target_path, 
                                          args.migration_type, not args.no_backup)
            return 0 if success else 1
        
        elif args.command == 'template':
            create_template(args.template_name, args.template_type)
        
        elif args.command == 'batch-migrate':
            batch_migrate(args.config_dir, args.target_dir, args.migration_type)
        
        elif args.command == 'report':
            generate_migration_report(args.config_dir, args.output)
        
        elif args.command == 'compatibility':
            check_compatibility(args.config_path)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
