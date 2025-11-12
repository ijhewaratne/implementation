"""
Configuration loader for visualization module.

Loads and manages visualization configuration from YAML files.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class VisualizationConfig:
    """
    Load and manage visualization configuration.
    
    Loads settings from config/visualization_config.yaml and provides
    easy access to configuration values with sensible defaults.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to visualization config file
        """
        if config_path is None:
            config_path = Path("config/visualization_config.yaml")
        else:
            config_path = Path(config_path)
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            print(f"⚠️  Visualization config not found at {self.config_path}, using defaults")
            return self._get_defaults()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Merge with defaults to ensure all keys exist
            defaults = self._get_defaults()
            merged = self._merge_configs(defaults, config)
            
            return merged
        
        except Exception as e:
            print(f"⚠️  Error loading visualization config: {e}, using defaults")
            return self._get_defaults()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'visualization': {
                'enabled': True,
                'auto_generate_on_simulation': False,
                'static_maps_enabled': True,
                'interactive_maps_enabled': True,
                'dashboards_enabled': True,
                'output': {
                    'base_dir': 'results_test/visualizations',
                    'static_dir': 'results_test/visualizations/static',
                    'interactive_dir': 'results_test/visualizations/interactive',
                    'dashboard_dir': 'results_test/visualizations/dashboards',
                },
                'static': {
                    'enabled': True,
                    'dpi': 300,
                    'format': 'png',
                    'figsize': [15, 12],
                    'include_street_map': True,
                },
                'interactive': {
                    'enabled': True,
                    'zoom_start': 16,
                    'tiles': 'OpenStreetMap',
                    'include_statistics_panel': True,
                    'include_performance_dashboard': True,
                    'include_legend': True,
                },
                'colors': {
                    'dh_supply': '#DC143C',
                    'dh_return': '#4682B4',
                    'normal': '#2ECC71',
                    'warning': '#F39C12',
                    'critical': '#E74C3C',
                },
                'temperature': {
                    'colormap': 'hot',
                    'min_temp_c': 40,
                    'max_temp_c': 90,
                },
                'voltage': {
                    'colormap': 'RdYlGn',
                    'acceptable_min': 0.95,
                    'acceptable_max': 1.05,
                },
            }
        }
    
    def _merge_configs(self, default: Dict, override: Dict) -> Dict:
        """Recursively merge configuration dictionaries."""
        merged = default.copy()
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation path.
        
        Args:
            path: Dot-separated path (e.g., 'visualization.static.dpi')
            default: Default value if path not found
        
        Returns:
            Configuration value or default
        
        Example:
            >>> config = VisualizationConfig()
            >>> dpi = config.get('visualization.static.dpi')
            >>> 300
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def is_enabled(self) -> bool:
        """Check if visualizations are enabled."""
        return self.get('visualization.enabled', True)
    
    def get_output_dir(self, viz_type: str = 'static') -> str:
        """
        Get output directory for visualization type.
        
        Args:
            viz_type: Type of visualization ('static', 'interactive', 'dashboard')
        
        Returns:
            Output directory path
        """
        return self.get(f'visualization.output.{viz_type}_dir', 
                       f'results_test/visualizations/{viz_type}')
    
    def get_color(self, color_name: str) -> str:
        """
        Get color value by name.
        
        Args:
            color_name: Color name (e.g., 'dh_supply', 'normal', 'warning')
        
        Returns:
            Hex color string
        """
        return self.get(f'visualization.colors.{color_name}', '#000000')
    
    def get_static_settings(self) -> Dict[str, Any]:
        """Get all static map settings."""
        return self.get('visualization.static', {})
    
    def get_interactive_settings(self) -> Dict[str, Any]:
        """Get all interactive map settings."""
        return self.get('visualization.interactive', {})
    
    def get_dashboard_settings(self) -> Dict[str, Any]:
        """Get all dashboard settings."""
        return self.get('visualization.dashboard', {})


# Singleton instance
_config_instance = None


def get_visualization_config() -> VisualizationConfig:
    """
    Get singleton visualization configuration instance.
    
    Returns:
        VisualizationConfig instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = VisualizationConfig()
    
    return _config_instance

