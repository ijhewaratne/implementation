#!/usr/bin/env python3
"""
CHA Output Migration Tool

This script migrates CHA outputs from legacy formats to the new enhanced format
with hydraulic simulation, thermal calculations, and comprehensive validation.

Features:
- Convert old CHA outputs to new format
- Validate migration results
- Generate migration reports
- Rollback capabilities
- Batch processing
- Safety mechanisms
"""

import argparse
import json
import yaml
import shutil
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import tempfile
import hashlib
import gzip
import traceback
from dataclasses import dataclass, asdict
import jsonschema
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from cha_schema_validator import CHASchemaValidator
    from cha_validation import CHAValidationSystem
except ImportError:
    print("Warning: CHA validation modules not available. Some features may be limited.")
    CHASchemaValidator = None
    CHAValidationSystem = None


@dataclass
class MigrationResult:
    """Result of a single file migration."""
    file_path: str
    success: bool
    error_message: Optional[str] = None
    migration_time: float = 0.0
    file_size_before: int = 0
    file_size_after: int = 0
    validation_passed: bool = False
    backup_created: bool = False
    backup_path: Optional[str] = None


@dataclass
class MigrationReport:
    """Complete migration report."""
    start_time: str
    end_time: str
    total_files: int
    successful_migrations: int
    failed_migrations: int
    total_migration_time: float
    total_size_before: int
    total_size_after: int
    validation_success_rate: float
    backup_created: bool
    results: List[MigrationResult]
    errors: List[str]
    warnings: List[str]


class CHAOutputMigrator:
    """CHA Output Migration Tool."""
    
    def __init__(self, config_path: str = "configs/cha.yml"):
        """Initialize the migrator."""
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.schema_validator = CHASchemaValidator() if CHASchemaValidator else None
        self.validation_system = CHAValidationSystem() if CHAValidationSystem else None
        
        # Migration settings
        self.migration_config = self.config.get('backward_compatibility', {}).get('migration', {})
        self.safety_config = self.config.get('migration', {}).get('safety', {})
        
        # Backup directory
        self.backup_dir = Path("backups") / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def _load_config(self) -> Dict[str, Any]:
        """Load CHA configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return {}
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging."""
        logger = logging.getLogger('cha_migration')
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = Path("logs") / "migration.log"
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _create_backup(self, file_path: str) -> Optional[str]:
        """Create backup of original file."""
        if not self.safety_config.get('backup_before_migration', True):
            return None
        
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return None
            
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup path
            backup_path = self.backup_dir / source_path.name
            
            # Copy file
            shutil.copy2(source_path, backup_path)
            
            self.logger.info(f"Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def _detect_file_format(self, file_path: str) -> str:
        """Detect the format of the input file."""
        file_path = Path(file_path)
        
        # Check file extension
        if file_path.suffix.lower() == '.json':
            return 'json'
        elif file_path.suffix.lower() == '.csv':
            return 'csv'
        elif file_path.suffix.lower() == '.xml':
            return 'xml'
        elif file_path.suffix.lower() == '.gpkg':
            return 'geopackage'
        else:
            # Try to detect by content
            try:
                with open(file_path, 'r') as f:
                    content = f.read(100)
                    if content.strip().startswith('{'):
                        return 'json'
                    elif content.strip().startswith('<'):
                        return 'xml'
                    else:
                        return 'csv'
            except:
                return 'unknown'
    
    def _load_legacy_data(self, file_path: str, file_format: str) -> Dict[str, Any]:
        """Load legacy data from file."""
        try:
            if file_format == 'json':
                with open(file_path, 'r') as f:
                    return json.load(f)
            elif file_format == 'csv':
                return self._load_legacy_csv(file_path)
            elif file_format == 'xml':
                return self._load_legacy_xml(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
        except Exception as e:
            raise ValueError(f"Failed to load legacy data: {e}")
    
    def _load_legacy_csv(self, file_path: str) -> Dict[str, Any]:
        """Load legacy CSV data."""
        import pandas as pd
        
        try:
            # Try to load as CSV
            df = pd.read_csv(file_path)
            
            # Convert to dictionary format
            data = {
                'metadata': {
                    'simulation_timestamp': datetime.now().isoformat(),
                    'pandapipes_version': '0.8.0',
                    'convergence_status': 'converged',
                    'legacy_format': 'csv',
                    'migrated_at': datetime.now().isoformat()
                },
                'pipes': df.to_dict('records') if not df.empty else [],
                'nodes': {'junctions': [], 'sources': [], 'sinks': []},
                'kpis': {
                    'hydraulic': {},
                    'thermal': {},
                    'economic': {}
                },
                'compliance': {
                    'overall_compliant': True,
                    'standards_checked': [],
                    'violations': [],
                    'warnings': []
                },
                'crs': {'type': 'EPSG', 'code': 4326},
                'units': {
                    'pressure': 'bar',
                    'temperature': 'K',
                    'flow_rate': 'kg/s',
                    'length': 'km',
                    'diameter': 'm',
                    'velocity': 'm/s',
                    'power': 'kW',
                    'energy': 'kWh'
                }
            }
            
            return data
            
        except Exception as e:
            raise ValueError(f"Failed to load CSV data: {e}")
    
    def _load_legacy_xml(self, file_path: str) -> Dict[str, Any]:
        """Load legacy XML data."""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Convert XML to dictionary (simplified)
            data = {
                'metadata': {
                    'simulation_timestamp': datetime.now().isoformat(),
                    'pandapipes_version': '0.8.0',
                    'convergence_status': 'converged',
                    'legacy_format': 'xml',
                    'migrated_at': datetime.now().isoformat()
                },
                'pipes': [],
                'nodes': {'junctions': [], 'sources': [], 'sinks': []},
                'kpis': {
                    'hydraulic': {},
                    'thermal': {},
                    'economic': {}
                },
                'compliance': {
                    'overall_compliant': True,
                    'standards_checked': [],
                    'violations': [],
                    'warnings': []
                },
                'crs': {'type': 'EPSG', 'code': 4326},
                'units': {
                    'pressure': 'bar',
                    'temperature': 'K',
                    'flow_rate': 'kg/s',
                    'length': 'km',
                    'diameter': 'm',
                    'velocity': 'm/s',
                    'power': 'kW',
                    'energy': 'kWh'
                }
            }
            
            # Parse XML elements (simplified)
            for element in root.iter():
                if element.tag == 'pipe':
                    pipe_data = {}
                    for child in element:
                        pipe_data[child.tag] = child.text
                    data['pipes'].append(pipe_data)
            
            return data
            
        except Exception as e:
            raise ValueError(f"Failed to load XML data: {e}")
    
    def _convert_legacy_data(self, legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy data to new format."""
        try:
            # Start with legacy data
            new_data = legacy_data.copy()
            
            # Update metadata
            if 'metadata' not in new_data:
                new_data['metadata'] = {}
            
            new_data['metadata'].update({
                'schema_version': '2.0.0',
                'migrated_at': datetime.now().isoformat(),
                'migration_tool': 'migrate_cha_outputs.py',
                'migration_version': '1.0.0'
            })
            
            # Convert parameter names if needed
            if self.migration_config.get('data_migration', {}).get('convert_units', True):
                new_data = self._convert_parameter_names(new_data)
            
            # Add missing required fields
            new_data = self._add_missing_fields(new_data)
            
            # Validate and fix data types
            new_data = self._fix_data_types(new_data)
            
            # Add enhanced fields
            new_data = self._add_enhanced_fields(new_data)
            
            return new_data
            
        except Exception as e:
            raise ValueError(f"Failed to convert legacy data: {e}")
    
    def _convert_parameter_names(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy parameter names to new format."""
        parameter_mapping = self.config.get('backward_compatibility', {}).get('parameter_mapping', {})
        
        if not parameter_mapping:
            return data
        
        # Convert parameter names in pipes
        if 'pipes' in data and isinstance(data['pipes'], list):
            for pipe in data['pipes']:
                if isinstance(pipe, dict):
                    for old_name, new_name in parameter_mapping.items():
                        if old_name in pipe:
                            pipe[new_name] = pipe.pop(old_name)
        
        return data
    
    def _add_missing_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add missing required fields."""
        # Ensure all required top-level fields exist
        required_fields = ['metadata', 'nodes', 'pipes', 'kpis', 'compliance', 'crs', 'units']
        
        for field in required_fields:
            if field not in data:
                if field == 'nodes':
                    data[field] = {'junctions': [], 'sources': [], 'sinks': []}
                elif field == 'kpis':
                    data[field] = {'hydraulic': {}, 'thermal': {}, 'economic': {}}
                elif field == 'compliance':
                    data[field] = {
                        'overall_compliant': True,
                        'standards_checked': [],
                        'violations': [],
                        'warnings': []
                    }
                elif field == 'crs':
                    data[field] = {'type': 'EPSG', 'code': 4326}
                elif field == 'units':
                    data[field] = {
                        'pressure': 'bar',
                        'temperature': 'K',
                        'flow_rate': 'kg/s',
                        'length': 'km',
                        'diameter': 'm',
                        'velocity': 'm/s',
                        'power': 'kW',
                        'energy': 'kWh'
                    }
                else:
                    data[field] = {}
        
        return data
    
    def _fix_data_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix data types in the data."""
        # Fix metadata fields
        if 'metadata' in data:
            metadata = data['metadata']
            
            # Ensure convergence_status is valid
            if 'convergence_status' in metadata:
                valid_statuses = ['converged', 'max_iterations', 'failed']
                if metadata['convergence_status'] not in valid_statuses:
                    metadata['convergence_status'] = 'converged'
            
            # Ensure numeric fields are numbers
            numeric_fields = ['total_iterations', 'simulation_duration_s']
            for field in numeric_fields:
                if field in metadata:
                    try:
                        metadata[field] = float(metadata[field])
                    except (ValueError, TypeError):
                        metadata[field] = 0.0
        
        # Fix pipe data types
        if 'pipes' in data and isinstance(data['pipes'], list):
            for pipe in data['pipes']:
                if isinstance(pipe, dict):
                    # Fix numeric fields
                    numeric_fields = [
                        'length_km', 'diameter_m', 'v_mean_m_per_s',
                        'p_from_bar', 'p_to_bar', 'mdot_kg_per_s',
                        't_from_k', 't_to_k', 'alpha_w_per_m2k', 'text_k'
                    ]
                    
                    for field in numeric_fields:
                        if field in pipe:
                            try:
                                pipe[field] = float(pipe[field])
                            except (ValueError, TypeError):
                                pipe[field] = 0.0
        
        return data
    
    def _add_enhanced_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add enhanced fields for new format."""
        # Add enhanced metadata
        if 'metadata' not in data:
            data['metadata'] = {}
        
        metadata = data['metadata']
        metadata.update({
            'thermal_simulation_enabled': True,
            'auto_resize_enabled': True,
            'network_size': {
                'junctions': len(data.get('nodes', {}).get('junctions', [])),
                'pipes': len(data.get('pipes', [])),
                'sources': len(data.get('nodes', {}).get('sources', [])),
                'sinks': len(data.get('nodes', {}).get('sinks', []))
            }
        })
        
        # Add enhanced KPIs if missing
        if 'kpis' not in data:
            data['kpis'] = {}
        
        kpis = data['kpis']
        
        # Add hydraulic KPIs
        if 'hydraulic' not in kpis:
            kpis['hydraulic'] = {}
        
        hydraulic = kpis['hydraulic']
        if not hydraulic:
            hydraulic.update({
                'max_velocity_ms': 0.0,
                'max_pressure_drop_pa_per_m': 0.0,
                'pump_power_kw': 0.0,
                'total_flow_kg_s': 0.0
            })
        
        # Add thermal KPIs
        if 'thermal' not in kpis:
            kpis['thermal'] = {}
        
        thermal = kpis['thermal']
        if not thermal:
            thermal.update({
                'thermal_efficiency': 0.85,
                'total_thermal_loss_kw': 0.0,
                'temperature_drop_c': 0.0,
                'heat_transfer_coefficient_avg': 0.6
            })
        
        # Add economic KPIs
        if 'economic' not in kpis:
            kpis['economic'] = {}
        
        economic = kpis['economic']
        if not economic:
            economic.update({
                'capex_eur': 0.0,
                'opex_eur_per_year': 0.0,
                'lcoh_eur_per_mwh': 0.0,
                'payback_period_years': 0.0
            })
        
        return data
    
    def _validate_migrated_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate migrated data."""
        errors = []
        
        try:
            # Schema validation
            if self.schema_validator:
                result = self.schema_validator.validate_data(data)
                if not result['valid']:
                    errors.extend(result['errors'])
            
            # Standards compliance validation
            if self.validation_system:
                compliance_result = self.validation_system.validate_standards_compliance(data)
                if not compliance_result['overall_compliant']:
                    errors.extend(compliance_result['violations'])
            
            # Basic validation
            if 'metadata' not in data:
                errors.append("Missing required field: metadata")
            
            if 'pipes' not in data:
                errors.append("Missing required field: pipes")
            
            if 'kpis' not in data:
                errors.append("Missing required field: kpis")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return False, errors
    
    def _save_migrated_data(self, data: Dict[str, Any], output_path: str) -> None:
        """Save migrated data to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def migrate_file(self, input_path: str, output_path: Optional[str] = None) -> MigrationResult:
        """Migrate a single file."""
        start_time = time.time()
        
        try:
            input_path = Path(input_path)
            if not input_path.exists():
                return MigrationResult(
                    file_path=str(input_path),
                    success=False,
                    error_message="File not found"
                )
            
            # Get file size before migration
            file_size_before = input_path.stat().st_size
            
            # Create backup
            backup_path = self._create_backup(str(input_path))
            
            # Detect file format
            file_format = self._detect_file_format(str(input_path))
            
            # Load legacy data
            legacy_data = self._load_legacy_data(str(input_path), file_format)
            
            # Convert to new format
            new_data = self._convert_legacy_data(legacy_data)
            
            # Validate migrated data
            validation_passed, validation_errors = self._validate_migrated_data(new_data)
            
            if not validation_passed and self.safety_config.get('validate_after_migration', True):
                raise ValueError(f"Validation failed: {validation_errors}")
            
            # Determine output path
            if output_path is None:
                output_path = str(input_path.with_suffix('.json'))
            
            # Save migrated data
            self._save_migrated_data(new_data, output_path)
            
            # Get file size after migration
            file_size_after = Path(output_path).stat().st_size
            
            migration_time = time.time() - start_time
            
            self.logger.info(f"Successfully migrated: {input_path} -> {output_path}")
            
            return MigrationResult(
                file_path=str(input_path),
                success=True,
                migration_time=migration_time,
                file_size_before=file_size_before,
                file_size_after=file_size_after,
                validation_passed=validation_passed,
                backup_created=backup_path is not None,
                backup_path=backup_path
            )
            
        except Exception as e:
            migration_time = time.time() - start_time
            error_message = f"Migration failed: {e}"
            self.logger.error(f"Failed to migrate {input_path}: {e}")
            
            return MigrationResult(
                file_path=str(input_path),
                success=False,
                error_message=error_message,
                migration_time=migration_time
            )
    
    def migrate_directory(self, input_dir: str, output_dir: Optional[str] = None, 
                         max_workers: int = 4) -> MigrationReport:
        """Migrate all files in a directory."""
        start_time = datetime.now()
        start_timestamp = start_time.isoformat()
        
        input_path = Path(input_dir)
        if not input_path.exists():
            raise ValueError(f"Input directory not found: {input_dir}")
        
        # Find all files to migrate
        file_patterns = ['*.json', '*.csv', '*.xml']
        files_to_migrate = []
        
        for pattern in file_patterns:
            files_to_migrate.extend(input_path.glob(pattern))
        
        if not files_to_migrate:
            self.logger.warning(f"No files found to migrate in {input_dir}")
            return MigrationReport(
                start_time=start_timestamp,
                end_time=datetime.now().isoformat(),
                total_files=0,
                successful_migrations=0,
                failed_migrations=0,
                total_migration_time=0.0,
                total_size_before=0,
                total_size_after=0,
                validation_success_rate=0.0,
                backup_created=False,
                results=[],
                errors=[],
                warnings=[]
            )
        
        self.logger.info(f"Found {len(files_to_migrate)} files to migrate")
        
        # Set up output directory
        if output_dir is None:
            output_dir = input_dir
        else:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Migrate files
        results = []
        errors = []
        warnings = []
        
        if max_workers > 1:
            # Parallel migration
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(self.migrate_file, str(file_path), 
                                  str(Path(output_dir) / file_path.name)): file_path
                    for file_path in files_to_migrate
                }
                
                for future in as_completed(future_to_file):
                    result = future.result()
                    results.append(result)
                    
                    if not result.success:
                        errors.append(f"{result.file_path}: {result.error_message}")
                    elif not result.validation_passed:
                        warnings.append(f"{result.file_path}: Validation warnings")
        else:
            # Sequential migration
            for file_path in files_to_migrate:
                result = self.migrate_file(str(file_path), 
                                         str(Path(output_dir) / file_path.name))
                results.append(result)
                
                if not result.success:
                    errors.append(f"{result.file_path}: {result.error_message}")
                elif not result.validation_passed:
                    warnings.append(f"{result.file_path}: Validation warnings")
        
        # Calculate statistics
        end_time = datetime.now()
        total_migration_time = (end_time - start_time).total_seconds()
        
        successful_migrations = sum(1 for r in results if r.success)
        failed_migrations = len(results) - successful_migrations
        
        total_size_before = sum(r.file_size_before for r in results)
        total_size_after = sum(r.file_size_after for r in results)
        
        validation_passed_count = sum(1 for r in results if r.validation_passed)
        validation_success_rate = validation_passed_count / len(results) if results else 0.0
        
        backup_created = any(r.backup_created for r in results)
        
        report = MigrationReport(
            start_time=start_timestamp,
            end_time=end_time.isoformat(),
            total_files=len(results),
            successful_migrations=successful_migrations,
            failed_migrations=failed_migrations,
            total_migration_time=total_migration_time,
            total_size_before=total_size_before,
            total_size_after=total_size_after,
            validation_success_rate=validation_success_rate,
            backup_created=backup_created,
            results=results,
            errors=errors,
            warnings=warnings
        )
        
        self.logger.info(f"Migration completed: {successful_migrations}/{len(results)} files migrated successfully")
        
        return report
    
    def generate_report(self, report: MigrationReport, output_path: str) -> None:
        """Generate migration report."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate JSON report
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
        
        # Generate HTML report
        html_path = output_path.with_suffix('.html')
        self._generate_html_report(report, html_path)
        
        # Generate text report
        txt_path = output_path.with_suffix('.txt')
        self._generate_text_report(report, txt_path)
        
        self.logger.info(f"Migration report generated: {output_path}")
    
    def _generate_html_report(self, report: MigrationReport, output_path: Path) -> None:
        """Generate HTML migration report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CHA Output Migration Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .error {{ background-color: #ffe8e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .warning {{ background-color: #fff8e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>CHA Output Migration Report</h1>
        <p>Generated on: {report.end_time}</p>
    </div>
    
    <div class="summary">
        <h2>Migration Summary</h2>
        <ul>
            <li>Total files: {report.total_files}</li>
            <li>Successful migrations: <span class="success">{report.successful_migrations}</span></li>
            <li>Failed migrations: <span class="failure">{report.failed_migrations}</span></li>
            <li>Total migration time: {report.total_migration_time:.2f} seconds</li>
            <li>Validation success rate: {report.validation_success_rate:.1%}</li>
            <li>Backup created: {'Yes' if report.backup_created else 'No'}</li>
        </ul>
    </div>
    
    <h2>File Results</h2>
    <table>
        <tr>
            <th>File</th>
            <th>Status</th>
            <th>Migration Time</th>
            <th>Size Before</th>
            <th>Size After</th>
            <th>Validation</th>
            <th>Backup</th>
        </tr>
"""
        
        for result in report.results:
            status_class = "success" if result.success else "failure"
            status_text = "Success" if result.success else "Failed"
            
            html_content += f"""
        <tr>
            <td>{result.file_path}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{result.migration_time:.2f}s</td>
            <td>{result.file_size_before:,} bytes</td>
            <td>{result.file_size_after:,} bytes</td>
            <td>{'Passed' if result.validation_passed else 'Failed'}</td>
            <td>{'Yes' if result.backup_created else 'No'}</td>
        </tr>
"""
        
        html_content += """
    </table>
"""
        
        if report.errors:
            html_content += f"""
    <div class="error">
        <h2>Errors</h2>
        <ul>
"""
            for error in report.errors:
                html_content += f"            <li>{error}</li>\n"
            
            html_content += """
        </ul>
    </div>
"""
        
        if report.warnings:
            html_content += f"""
    <div class="warning">
        <h2>Warnings</h2>
        <ul>
"""
            for warning in report.warnings:
                html_content += f"            <li>{warning}</li>\n"
            
            html_content += """
        </ul>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _generate_text_report(self, report: MigrationReport, output_path: Path) -> None:
        """Generate text migration report."""
        with open(output_path, 'w') as f:
            f.write("CHA Output Migration Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Start time: {report.start_time}\n")
            f.write(f"End time: {report.end_time}\n")
            f.write(f"Total migration time: {report.total_migration_time:.2f} seconds\n\n")
            
            f.write("Migration Summary:\n")
            f.write(f"  Total files: {report.total_files}\n")
            f.write(f"  Successful migrations: {report.successful_migrations}\n")
            f.write(f"  Failed migrations: {report.failed_migrations}\n")
            f.write(f"  Validation success rate: {report.validation_success_rate:.1%}\n")
            f.write(f"  Backup created: {'Yes' if report.backup_created else 'No'}\n\n")
            
            f.write("File Results:\n")
            f.write("-" * 80 + "\n")
            for result in report.results:
                status = "SUCCESS" if result.success else "FAILED"
                f.write(f"{result.file_path}: {status}\n")
                if result.error_message:
                    f.write(f"  Error: {result.error_message}\n")
                f.write(f"  Migration time: {result.migration_time:.2f}s\n")
                f.write(f"  Size: {result.file_size_before:,} -> {result.file_size_after:,} bytes\n")
                f.write(f"  Validation: {'Passed' if result.validation_passed else 'Failed'}\n")
                f.write(f"  Backup: {'Yes' if result.backup_created else 'No'}\n\n")
            
            if report.errors:
                f.write("Errors:\n")
                f.write("-" * 20 + "\n")
                for error in report.errors:
                    f.write(f"  - {error}\n")
                f.write("\n")
            
            if report.warnings:
                f.write("Warnings:\n")
                f.write("-" * 20 + "\n")
                for warning in report.warnings:
                    f.write(f"  - {warning}\n")
                f.write("\n")
    
    def rollback_migration(self, backup_dir: str, target_dir: str) -> bool:
        """Rollback migration using backups."""
        try:
            backup_path = Path(backup_dir)
            target_path = Path(target_dir)
            
            if not backup_path.exists():
                self.logger.error(f"Backup directory not found: {backup_dir}")
                return False
            
            # Find backup files
            backup_files = list(backup_path.glob("*"))
            
            if not backup_files:
                self.logger.error(f"No backup files found in {backup_dir}")
                return False
            
            # Restore files
            restored_count = 0
            for backup_file in backup_files:
                target_file = target_path / backup_file.name
                
                # Remove existing file if it exists
                if target_file.exists():
                    target_file.unlink()
                
                # Copy backup file
                shutil.copy2(backup_file, target_file)
                restored_count += 1
            
            self.logger.info(f"Rollback completed: {restored_count} files restored")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="CHA Output Migration Tool")
    parser.add_argument("input", help="Input file or directory path")
    parser.add_argument("-o", "--output", help="Output file or directory path")
    parser.add_argument("-c", "--config", default="configs/cha.yml", help="Configuration file path")
    parser.add_argument("-r", "--report", help="Migration report output path")
    parser.add_argument("-w", "--workers", type=int, default=4, help="Number of worker threads")
    parser.add_argument("--rollback", help="Rollback migration using backup directory")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    parser.add_argument("--no-validation", action="store_true", help="Skip validation")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no actual migration)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Initialize migrator
    migrator = CHAOutputMigrator(args.config)
    
    if args.verbose:
        migrator.logger.setLevel(logging.DEBUG)
    
    # Override safety settings if requested
    if args.no_backup:
        migrator.safety_config['backup_before_migration'] = False
    if args.no_validation:
        migrator.safety_config['validate_after_migration'] = False
    
    try:
        if args.rollback:
            # Rollback migration
            success = migrator.rollback_migration(args.rollback, args.input)
            if success:
                print("✅ Rollback completed successfully")
                return 0
            else:
                print("❌ Rollback failed")
                return 1
        
        # Check if input is file or directory
        input_path = Path(args.input)
        
        if input_path.is_file():
            # Migrate single file
            if args.dry_run:
                print(f"Dry run: Would migrate {args.input} to {args.output or args.input}")
                return 0
            
            result = migrator.migrate_file(args.input, args.output)
            
            if result.success:
                print(f"✅ Successfully migrated: {args.input}")
                if args.report:
                    report = MigrationReport(
                        start_time=datetime.now().isoformat(),
                        end_time=datetime.now().isoformat(),
                        total_files=1,
                        successful_migrations=1 if result.success else 0,
                        failed_migrations=0 if result.success else 1,
                        total_migration_time=result.migration_time,
                        total_size_before=result.file_size_before,
                        total_size_after=result.file_size_after,
                        validation_success_rate=1.0 if result.validation_passed else 0.0,
                        backup_created=result.backup_created,
                        results=[result],
                        errors=[result.error_message] if result.error_message else [],
                        warnings=[]
                    )
                    migrator.generate_report(report, args.report)
                return 0
            else:
                print(f"❌ Migration failed: {result.error_message}")
                return 1
        
        elif input_path.is_dir():
            # Migrate directory
            if args.dry_run:
                files = list(input_path.glob("*.json")) + list(input_path.glob("*.csv")) + list(input_path.glob("*.xml"))
                print(f"Dry run: Would migrate {len(files)} files from {args.input} to {args.output or args.input}")
                return 0
            
            report = migrator.migrate_directory(args.input, args.output, args.workers)
            
            print(f"📊 Migration completed:")
            print(f"  Total files: {report.total_files}")
            print(f"  Successful: {report.successful_migrations}")
            print(f"  Failed: {report.failed_migrations}")
            print(f"  Validation success rate: {report.validation_success_rate:.1%}")
            print(f"  Total time: {report.total_migration_time:.2f} seconds")
            
            if args.report:
                migrator.generate_report(report, args.report)
            
            return 0 if report.failed_migrations == 0 else 1
        
        else:
            print(f"❌ Input path not found: {args.input}")
            return 1
    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
