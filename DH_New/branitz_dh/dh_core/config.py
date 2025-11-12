"""
Configuration management for Branitz DH project.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dataclasses import dataclass


class Config:
    """Configuration manager for the DH project."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        self.project_root = Path(__file__).parent.parent
        self.config_path = config_path or self.project_root / "config.yaml"
        
        # Default configuration
        self._config = {
            "data": {
                "inputs_dir": "data/inputs",
                "outputs_dir": "data/outputs", 
                "cache_dir": "data/cache",
                "catalogs_dir": "data/catalogs"
            },
            "processing": {
                "max_workers": 4,
                "chunk_size": 1000,
                "enable_caching": True
            },
            "visualization": {
                "default_style": "seaborn",
                "figure_size": [12, 8],
                "save_format": "png"
            },
            "costs": {
                "track_costs": True,
                "currency": "USD",
                "cost_per_token": 0.0001
            }
        }
        
        # Load configuration from file if it exists
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    self._config.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'data.inputs_dir')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'data.inputs_dir')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self):
        """Save current configuration to YAML file."""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file {self.config_path}: {e}")
    
    @property
    def data_dirs(self) -> Dict[str, Path]:
        """Get data directory paths."""
        return {
            "inputs": self.project_root / self.get("data.inputs_dir"),
            "outputs": self.project_root / self.get("data.outputs_dir"),
            "cache": self.project_root / self.get("data.cache_dir"),
            "catalogs": self.project_root / self.get("data.catalogs_dir")
        }
    
    def ensure_dirs(self):
        """Ensure all data directories exist."""
        for dir_path in self.data_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)


@dataclass
class DHDesign:
    """District heating design parameters."""
    supply_c: float = 75.0
    return_c: float = 45.0
    u_w_per_m2k: float = 0.35
    sections: int = 8


class Paths:
    """Path management for the DH project."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self._inputs = self.project_root / "data" / "inputs"
        self._outputs = self.project_root / "data" / "outputs"
        self._cache = self.project_root / "data" / "cache"
        self._catalogs = self.project_root / "data" / "catalogs"
    
    @property
    def inputs(self) -> Path:
        """Input data directory."""
        return self._inputs
    
    @property
    def outputs(self) -> Path:
        """Output data directory."""
        return self._outputs
    
    @property
    def cache(self) -> Path:
        """Cache directory."""
        return self._cache
    
    @property
    def catalogs(self) -> Path:
        """Catalogs directory."""
        return self._catalogs
