"""
Dashboard module for creating comprehensive visualization dashboards.

This module provides classes for creating:
- Summary dashboards (12-panel comprehensive analysis)
- Comparison dashboards (DH vs HP)
- HTML dashboards (comprehensive web pages)
- Performance dashboards (KPI metrics)
"""

from .summary_dashboard import SummaryDashboard
from .comparison_dashboard import ComparisonDashboard
from .html_dashboard import HTMLDashboardGenerator

__all__ = [
    'SummaryDashboard',
    'ComparisonDashboard',
    'HTMLDashboardGenerator',
]

