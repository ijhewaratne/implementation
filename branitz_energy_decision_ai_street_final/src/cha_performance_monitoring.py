#!/usr/bin/env python3
"""
CHA Performance Monitoring System

This module provides comprehensive performance monitoring and optimization capabilities
for the CHA Intelligent Pipe Sizing System, including real-time monitoring, alerting,
and performance optimization recommendations.
"""

import os
import json
import yaml
import time
import psutil
import threading
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import queue
import statistics
from collections import defaultdict, deque
import numpy as np

class MetricType(Enum):
    """Types of performance metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertLevel(Enum):
    """Alert levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class PerformanceMetric:
    """Performance metric definition."""
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Alert:
    """Performance alert."""
    alert_id: str
    metric_name: str
    level: AlertLevel
    message: str
    threshold: float
    current_value: float
    timestamp: datetime
    resolved: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class PerformanceThreshold:
    """Performance threshold definition."""
    metric_name: str
    warning_threshold: float
    error_threshold: float
    critical_threshold: float
    comparison_operator: str = "greater_than"  # "greater_than", "less_than", "equals"
    window_size_minutes: int = 5
    evaluation_interval_seconds: int = 60

@dataclass
class PerformanceReport:
    """Performance report."""
    report_id: str
    start_time: datetime
    end_time: datetime
    metrics_summary: Dict[str, Any]
    alerts: List[Alert]
    recommendations: List[str]
    system_info: Dict[str, Any]
    timestamp: datetime

class CHAPerformanceMonitor:
    """Performance monitoring system for CHA."""
    
    def __init__(self, config_path: str = "configs/performance_monitoring.yml"):
        """Initialize the performance monitoring system.
        
        Args:
            config_path: Path to performance monitoring configuration file
        """
        self.config_path = config_path
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.thresholds: Dict[str, PerformanceThreshold] = {}
        self.alerts: List[Alert] = []
        self.monitoring_active = False
        self.monitoring_thread = None
        self.metric_queue = queue.Queue()
        self.alert_callbacks: List[Callable] = []
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self._load_config()
        
        # Setup logging
        self._setup_logging()
        
        # Start monitoring
        self.start_monitoring()
    
    def _setup_logging(self):
        """Setup logging for performance monitoring."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_config(self):
        """Load performance monitoring configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Load thresholds
                for threshold_config in config.get('thresholds', []):
                    threshold = PerformanceThreshold(
                        metric_name=threshold_config['metric_name'],
                        warning_threshold=threshold_config['warning_threshold'],
                        error_threshold=threshold_config['error_threshold'],
                        critical_threshold=threshold_config['critical_threshold'],
                        comparison_operator=threshold_config.get('comparison_operator', 'greater_than'),
                        window_size_minutes=threshold_config.get('window_size_minutes', 5),
                        evaluation_interval_seconds=threshold_config.get('evaluation_interval_seconds', 60)
                    )
                    self.thresholds[threshold.metric_name] = threshold
                
                self.logger.info(f"Loaded {len(self.thresholds)} performance thresholds from {self.config_path}")
            else:
                self.logger.warning(f"Performance monitoring configuration file not found: {self.config_path}")
                self._create_default_thresholds()
                
        except Exception as e:
            self.logger.error(f"Failed to load performance monitoring configuration: {e}")
            self._create_default_thresholds()
    
    def _create_default_thresholds(self):
        """Create default performance thresholds."""
        default_thresholds = [
            {
                'metric_name': 'pipe_sizing_time_ms',
                'warning_threshold': 1000.0,
                'error_threshold': 5000.0,
                'critical_threshold': 10000.0,
                'comparison_operator': 'greater_than'
            },
            {
                'metric_name': 'network_creation_time_ms',
                'warning_threshold': 2000.0,
                'error_threshold': 10000.0,
                'critical_threshold': 30000.0,
                'comparison_operator': 'greater_than'
            },
            {
                'metric_name': 'simulation_time_ms',
                'warning_threshold': 5000.0,
                'error_threshold': 30000.0,
                'critical_threshold': 60000.0,
                'comparison_operator': 'greater_than'
            },
            {
                'metric_name': 'memory_usage_mb',
                'warning_threshold': 1000.0,
                'error_threshold': 2000.0,
                'critical_threshold': 4000.0,
                'comparison_operator': 'greater_than'
            },
            {
                'metric_name': 'cpu_usage_percent',
                'warning_threshold': 80.0,
                'error_threshold': 90.0,
                'critical_threshold': 95.0,
                'comparison_operator': 'greater_than'
            },
            {
                'metric_name': 'error_rate_percent',
                'warning_threshold': 1.0,
                'error_threshold': 5.0,
                'critical_threshold': 10.0,
                'comparison_operator': 'greater_than'
            }
        ]
        
        for threshold_config in default_thresholds:
            threshold = PerformanceThreshold(**threshold_config)
            self.thresholds[threshold.metric_name] = threshold
        
        self.logger.info(f"Created {len(self.thresholds)} default performance thresholds")
    
    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE,
                     tags: Optional[Dict[str, str]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Record a performance metric.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            tags: Metric tags
            metadata: Metric metadata
        """
        metric = PerformanceMetric(
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {},
            metadata=metadata or {}
        )
        
        # Add to metrics storage
        self.metrics[name].append(metric)
        
        # Add to queue for processing
        self.metric_queue.put(metric)
        
        self.logger.debug(f"Recorded metric {name}={value}")
    
    def record_timer(self, name: str, duration_seconds: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer metric.
        
        Args:
            name: Timer name
            duration_seconds: Duration in seconds
            tags: Metric tags
        """
        self.record_metric(name, duration_seconds * 1000, MetricType.TIMER, tags)  # Convert to milliseconds
    
    def record_counter(self, name: str, increment: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Record a counter metric.
        
        Args:
            name: Counter name
            increment: Increment value
            tags: Metric tags
        """
        self.record_metric(name, increment, MetricType.COUNTER, tags)
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a gauge metric.
        
        Args:
            name: Gauge name
            value: Gauge value
            tags: Metric tags
        """
        self.record_metric(name, value, MetricType.GAUGE, tags)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram metric.
        
        Args:
            name: Histogram name
            value: Histogram value
            tags: Metric tags
        """
        self.record_metric(name, value, MetricType.HISTOGRAM, tags)
    
    def start_monitoring(self):
        """Start performance monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("Started performance monitoring")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("Stopped performance monitoring")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Process metrics from queue
                self._process_metric_queue()
                
                # Evaluate thresholds
                self._evaluate_thresholds()
                
                # Record system metrics
                self._record_system_metrics()
                
                # Sleep for a short interval
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def _process_metric_queue(self):
        """Process metrics from the queue."""
        while not self.metric_queue.empty():
            try:
                metric = self.metric_queue.get_nowait()
                # Metrics are already stored in self.metrics
                # Additional processing can be added here
            except queue.Empty:
                break
            except Exception as e:
                self.logger.error(f"Error processing metric: {e}")
    
    def _evaluate_thresholds(self):
        """Evaluate performance thresholds."""
        current_time = datetime.now()
        
        for metric_name, threshold in self.thresholds.items():
            if metric_name not in self.metrics:
                continue
            
            # Get recent metrics within the window
            window_start = current_time - timedelta(minutes=threshold.window_size_minutes)
            recent_metrics = [
                m for m in self.metrics[metric_name]
                if m.timestamp >= window_start
            ]
            
            if not recent_metrics:
                continue
            
            # Calculate metric value (mean for most metrics)
            if threshold.metric_name.endswith('_rate') or threshold.metric_name.endswith('_percent'):
                # For rates and percentages, use the latest value
                metric_value = recent_metrics[-1].value
            else:
                # For other metrics, use the mean
                metric_value = statistics.mean([m.value for m in recent_metrics])
            
            # Check thresholds
            alert_level = self._check_threshold(metric_value, threshold)
            if alert_level:
                self._create_alert(metric_name, alert_level, metric_value, threshold)
    
    def _check_threshold(self, value: float, threshold: PerformanceThreshold) -> Optional[AlertLevel]:
        """Check if a value exceeds a threshold.
        
        Args:
            value: Metric value
            threshold: Performance threshold
            
        Returns:
            Alert level if threshold is exceeded, None otherwise
        """
        if threshold.comparison_operator == "greater_than":
            if value >= threshold.critical_threshold:
                return AlertLevel.CRITICAL
            elif value >= threshold.error_threshold:
                return AlertLevel.ERROR
            elif value >= threshold.warning_threshold:
                return AlertLevel.WARNING
        
        elif threshold.comparison_operator == "less_than":
            if value <= threshold.critical_threshold:
                return AlertLevel.CRITICAL
            elif value <= threshold.error_threshold:
                return AlertLevel.ERROR
            elif value <= threshold.warning_threshold:
                return AlertLevel.WARNING
        
        elif threshold.comparison_operator == "equals":
            if value == threshold.critical_threshold:
                return AlertLevel.CRITICAL
            elif value == threshold.error_threshold:
                return AlertLevel.ERROR
            elif value == threshold.warning_threshold:
                return AlertLevel.WARNING
        
        return None
    
    def _create_alert(self, metric_name: str, level: AlertLevel, value: float, threshold: PerformanceThreshold):
        """Create a performance alert.
        
        Args:
            metric_name: Metric name
            level: Alert level
            value: Current metric value
            threshold: Performance threshold
        """
        alert_id = f"{metric_name}_{level.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Check if similar alert already exists
        existing_alerts = [
            a for a in self.alerts
            if a.metric_name == metric_name and a.level == level and not a.resolved
        ]
        
        if existing_alerts:
            return  # Don't create duplicate alerts
        
        alert = Alert(
            alert_id=alert_id,
            metric_name=metric_name,
            level=level,
            message=f"{metric_name} threshold exceeded: {value} {threshold.comparison_operator} {getattr(threshold, f'{level.value}_threshold')}",
            threshold=getattr(threshold, f'{level.value}_threshold'),
            current_value=value,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
        
        self.logger.warning(f"Performance alert: {alert.message}")
    
    def _record_system_metrics(self):
        """Record system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_gauge('cpu_usage_percent', cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_gauge('memory_usage_mb', memory.used / 1024 / 1024)
            self.record_gauge('memory_usage_percent', memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_gauge('disk_usage_percent', disk.percent)
            
            # Process-specific metrics
            process = psutil.Process()
            self.record_gauge('process_memory_mb', process.memory_info().rss / 1024 / 1024)
            self.record_gauge('process_cpu_percent', process.cpu_percent())
            
        except Exception as e:
            self.logger.error(f"Error recording system metrics: {e}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add an alert callback function.
        
        Args:
            callback: Callback function to call when alerts are created
        """
        self.alert_callbacks.append(callback)
    
    def get_metric_summary(self, metric_name: str, window_minutes: int = 60) -> Dict[str, Any]:
        """Get a summary of a metric over a time window.
        
        Args:
            metric_name: Name of the metric
            window_minutes: Time window in minutes
            
        Returns:
            Metric summary
        """
        if metric_name not in self.metrics:
            return {'error': f'Metric {metric_name} not found'}
        
        current_time = datetime.now()
        window_start = current_time - timedelta(minutes=window_minutes)
        
        recent_metrics = [
            m for m in self.metrics[metric_name]
            if m.timestamp >= window_start
        ]
        
        if not recent_metrics:
            return {'error': f'No data for metric {metric_name} in the last {window_minutes} minutes'}
        
        values = [m.value for m in recent_metrics]
        
        return {
            'metric_name': metric_name,
            'window_minutes': window_minutes,
            'sample_count': len(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std': statistics.stdev(values) if len(values) > 1 else 0.0,
            'min': min(values),
            'max': max(values),
            'percentile_95': np.percentile(values, 95) if len(values) > 1 else values[0],
            'percentile_99': np.percentile(values, 99) if len(values) > 1 else values[0]
        }
    
    def get_active_alerts(self) -> List[Alert]:
        """Get active (unresolved) alerts.
        
        Returns:
            List of active alerts
        """
        return [alert for alert in self.alerts if not alert.resolved]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert.
        
        Args:
            alert_id: Alert identifier
            
        Returns:
            True if alert was resolved, False otherwise
        """
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                self.logger.info(f"Resolved alert: {alert_id}")
                return True
        
        return False
    
    def generate_performance_report(self, start_time: Optional[datetime] = None, 
                                  end_time: Optional[datetime] = None) -> PerformanceReport:
        """Generate a performance report.
        
        Args:
            start_time: Report start time
            end_time: Report end time
            
        Returns:
            Performance report
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=1)
        if end_time is None:
            end_time = datetime.now()
        
        # Collect metrics summary
        metrics_summary = {}
        for metric_name in self.metrics.keys():
            summary = self.get_metric_summary(metric_name, 60)
            if 'error' not in summary:
                metrics_summary[metric_name] = summary
        
        # Get active alerts
        active_alerts = self.get_active_alerts()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics_summary, active_alerts)
        
        # Get system info
        system_info = self._get_system_info()
        
        report = PerformanceReport(
            report_id=f"perf_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_time=start_time,
            end_time=end_time,
            metrics_summary=metrics_summary,
            alerts=active_alerts,
            recommendations=recommendations,
            system_info=system_info,
            timestamp=datetime.now()
        )
        
        return report
    
    def _generate_recommendations(self, metrics_summary: Dict[str, Any], 
                                active_alerts: List[Alert]) -> List[str]:
        """Generate performance optimization recommendations.
        
        Args:
            metrics_summary: Metrics summary
            active_alerts: Active alerts
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Analyze metrics and generate recommendations
        for metric_name, summary in metrics_summary.items():
            if 'error' in summary:
                continue
            
            mean_value = summary['mean']
            percentile_95 = summary['percentile_95']
            
            # Pipe sizing performance recommendations
            if metric_name == 'pipe_sizing_time_ms':
                if mean_value > 1000:
                    recommendations.append("Consider optimizing pipe sizing algorithm - average time is high")
                if percentile_95 > 5000:
                    recommendations.append("Pipe sizing has high tail latency - investigate performance bottlenecks")
            
            # Network creation performance recommendations
            elif metric_name == 'network_creation_time_ms':
                if mean_value > 2000:
                    recommendations.append("Network creation is slow - consider parallel processing")
                if percentile_95 > 10000:
                    recommendations.append("Network creation has high variability - optimize data structures")
            
            # Simulation performance recommendations
            elif metric_name == 'simulation_time_ms':
                if mean_value > 5000:
                    recommendations.append("Simulation is slow - consider using faster numerical methods")
                if percentile_95 > 30000:
                    recommendations.append("Simulation has high tail latency - optimize convergence criteria")
            
            # Memory usage recommendations
            elif metric_name == 'memory_usage_mb':
                if mean_value > 1000:
                    recommendations.append("High memory usage - consider memory optimization techniques")
                if percentile_95 > 2000:
                    recommendations.append("Memory usage has high variability - investigate memory leaks")
            
            # CPU usage recommendations
            elif metric_name == 'cpu_usage_percent':
                if mean_value > 80:
                    recommendations.append("High CPU usage - consider load balancing or scaling")
                if percentile_95 > 95:
                    recommendations.append("CPU usage spikes detected - optimize CPU-intensive operations")
        
        # Alert-based recommendations
        for alert in active_alerts:
            if alert.level == AlertLevel.CRITICAL:
                recommendations.append(f"CRITICAL: {alert.message} - immediate attention required")
            elif alert.level == AlertLevel.ERROR:
                recommendations.append(f"ERROR: {alert.message} - investigate and resolve")
            elif alert.level == AlertLevel.WARNING:
                recommendations.append(f"WARNING: {alert.message} - monitor closely")
        
        return recommendations
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information.
        
        Returns:
            System information dictionary
        """
        try:
            return {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                'disk_total_gb': psutil.disk_usage('/').total / 1024 / 1024 / 1024,
                'python_version': os.sys.version,
                'platform': os.sys.platform,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}
    
    def save_report(self, report: PerformanceReport, output_path: Optional[str] = None) -> str:
        """Save a performance report to file.
        
        Args:
            report: Performance report
            output_path: Path to save the report
            
        Returns:
            Path to the saved report
        """
        if output_path is None:
            output_path = f"reports/performance_report_{report.report_id}.json"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        
        self.logger.info(f"Saved performance report: {output_path}")
        return output_path
    
    def save_config(self, output_path: Optional[str] = None):
        """Save performance monitoring configuration.
        
        Args:
            output_path: Path to save configuration file
        """
        if output_path is None:
            output_path = self.config_path
        
        config = {
            'thresholds': [
                {
                    'metric_name': threshold.metric_name,
                    'warning_threshold': threshold.warning_threshold,
                    'error_threshold': threshold.error_threshold,
                    'critical_threshold': threshold.critical_threshold,
                    'comparison_operator': threshold.comparison_operator,
                    'window_size_minutes': threshold.window_size_minutes,
                    'evaluation_interval_seconds': threshold.evaluation_interval_seconds
                }
                for threshold in self.thresholds.values()
            ]
        }
        
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Saved performance monitoring configuration: {output_path}")

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CHA Performance Monitoring System')
    parser.add_argument('--config', default='configs/performance_monitoring.yml', help='Performance monitoring configuration file')
    parser.add_argument('--action', choices=['start', 'stop', 'report', 'alerts', 'metrics'], required=True, help='Action to perform')
    parser.add_argument('--metric-name', help='Metric name for specific operations')
    parser.add_argument('--window-minutes', type=int, default=60, help='Time window in minutes')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Initialize performance monitoring
    monitor = CHAPerformanceMonitor(args.config)
    
    if args.action == 'start':
        monitor.start_monitoring()
        print("✅ Started performance monitoring")
    
    elif args.action == 'stop':
        monitor.stop_monitoring()
        print("✅ Stopped performance monitoring")
    
    elif args.action == 'report':
        report = monitor.generate_performance_report()
        output_path = monitor.save_report(report, args.output)
        print(f"✅ Generated performance report: {output_path}")
    
    elif args.action == 'alerts':
        alerts = monitor.get_active_alerts()
        print(f"📊 Active Alerts ({len(alerts)}):")
        for alert in alerts:
            print(f"  {alert.level.value.upper()}: {alert.message}")
    
    elif args.action == 'metrics':
        if args.metric_name:
            summary = monitor.get_metric_summary(args.metric_name, args.window_minutes)
            if 'error' in summary:
                print(f"❌ {summary['error']}")
            else:
                print(f"📊 Metric Summary: {args.metric_name}")
                print(f"   Mean: {summary['mean']:.2f}")
                print(f"   Median: {summary['median']:.2f}")
                print(f"   Std: {summary['std']:.2f}")
                print(f"   Min: {summary['min']:.2f}")
                print(f"   Max: {summary['max']:.2f}")
                print(f"   95th percentile: {summary['percentile_95']:.2f}")
                print(f"   99th percentile: {summary['percentile_99']:.2f}")
        else:
            print("Error: --metric-name is required for metrics action")
            return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
