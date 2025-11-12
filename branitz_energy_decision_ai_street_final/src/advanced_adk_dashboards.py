"""
ADK-Specific Dashboards - Advanced dashboard system
Part of Phase 6: Advanced ADK Features
"""

import logging
import time
import json
import os
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from dataclasses import dataclass, asdict

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@dataclass
class SystemMetric:
    """Represents a system metric."""
    name: str
    value: float
    unit: str
    timestamp: str
    status: str  # 'healthy', 'warning', 'critical'
    trend: str  # 'up', 'down', 'stable'

@dataclass
class PerformanceTrend:
    """Represents a performance trend."""
    metric_name: str
    time_period: str
    values: List[float]
    timestamps: List[str]
    trend_direction: str
    change_percentage: float

class RealTimeSystemMonitor:
    """Real-time system monitoring."""
    
    def __init__(self, db_path: str = 'data/system_metrics.db'):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
        self.current_metrics: Dict[str, SystemMetric] = {}
        logger.info("Initialized RealTimeSystemMonitor")
    
    def _create_tables(self):
        """Create database tables."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY,
                metric_name TEXT,
                value REAL,
                unit TEXT,
                timestamp TEXT,
                status TEXT,
                trend TEXT
            )
        ''')
        self.conn.commit()
    
    def update_metric(self, name: str, value: float, unit: str, status: str = "healthy", trend: str = "stable"):
        """Update a system metric."""
        timestamp = datetime.now().isoformat()
        metric = SystemMetric(name, value, unit, timestamp, status, trend)
        self.current_metrics[name] = metric
        
        # Store in database
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO system_metrics (metric_name, value, unit, timestamp, status, trend)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, value, unit, timestamp, status, trend))
        self.conn.commit()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        healthy_count = sum(1 for m in self.current_metrics.values() if m.status == "healthy")
        warning_count = sum(1 for m in self.current_metrics.values() if m.status == "warning")
        critical_count = sum(1 for m in self.current_metrics.values() if m.status == "critical")
        total_count = len(self.current_metrics)
        
        health_score = (healthy_count / total_count * 100) if total_count > 0 else 100
        
        return {
            'health_score': health_score,
            'status': 'healthy' if health_score > 80 else 'warning' if health_score > 60 else 'critical',
            'metrics_summary': {
                'healthy': healthy_count,
                'warning': warning_count,
                'critical': critical_count,
                'total': total_count
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def get_agent_performance(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        agents = ['EnergyPlannerAgent', 'CentralHeatingAgent', 'DecentralizedHeatingAgent', 
                 'ComparisonAgent', 'AnalysisAgent', 'DataExplorerAgent', 'EnergyGPT']
        
        performance_data = {}
        for agent in agents:
            # Mock performance data
            response_time = np.random.uniform(1.0, 5.0)
            success_rate = np.random.uniform(85.0, 98.0)
            throughput = np.random.uniform(10.0, 50.0)
            
            performance_data[agent] = {
                'response_time_ms': response_time,
                'success_rate_percent': success_rate,
                'throughput_per_minute': throughput,
                'status': 'healthy' if success_rate > 90 else 'warning',
                'last_updated': datetime.now().isoformat()
            }
        
        return {
            'agents': performance_data,
            'average_response_time': np.mean([p['response_time_ms'] for p in performance_data.values()]),
            'average_success_rate': np.mean([p['success_rate_percent'] for p in performance_data.values()]),
            'total_agents': len(agents)
        }
    
    def get_tool_usage(self) -> Dict[str, Any]:
        """Get tool usage metrics."""
        tools = ['data_exploration', 'district_heating_analysis', 'heat_pump_feasibility',
                'scenario_comparison', 'report_generation', 'optimization_engine']
        
        usage_data = {}
        for tool in tools:
            usage_count = np.random.randint(10, 100)
            avg_duration = np.random.uniform(2.0, 15.0)
            error_rate = np.random.uniform(1.0, 10.0)
            
            usage_data[tool] = {
                'usage_count': usage_count,
                'avg_duration_seconds': avg_duration,
                'error_rate_percent': error_rate,
                'last_used': datetime.now().isoformat()
            }
        
        return {
            'tools': usage_data,
            'total_tool_usage': sum(u['usage_count'] for u in usage_data.values()),
            'most_used_tool': max(usage_data.keys(), key=lambda k: usage_data[k]['usage_count']),
            'average_error_rate': np.mean([u['error_rate_percent'] for u in usage_data.values()])
        }
    
    def get_user_activity(self) -> Dict[str, Any]:
        """Get user activity metrics."""
        active_users = np.random.randint(5, 25)
        total_sessions = np.random.randint(50, 200)
        avg_session_duration = np.random.uniform(300.0, 1800.0)  # 5-30 minutes
        
        return {
            'active_users': active_users,
            'total_sessions_today': total_sessions,
            'avg_session_duration_seconds': avg_session_duration,
            'peak_usage_hour': np.random.randint(9, 17),  # 9 AM - 5 PM
            'user_engagement_score': np.random.uniform(70.0, 95.0),
            'last_updated': datetime.now().isoformat()
        }
    
    def get_resource_utilization(self) -> Dict[str, Any]:
        """Get resource utilization metrics."""
        cpu_usage = np.random.uniform(20.0, 80.0)
        memory_usage = np.random.uniform(30.0, 85.0)
        disk_usage = np.random.uniform(40.0, 90.0)
        network_io = np.random.uniform(100.0, 1000.0)  # MB/s
        
        return {
            'cpu_usage_percent': cpu_usage,
            'memory_usage_percent': memory_usage,
            'disk_usage_percent': disk_usage,
            'network_io_mbps': network_io,
            'status': 'healthy' if cpu_usage < 70 and memory_usage < 80 else 'warning',
            'last_updated': datetime.now().isoformat()
        }
    
    def get_error_rates(self) -> Dict[str, Any]:
        """Get error rates by component."""
        components = ['agents', 'tools', 'database', 'api', 'network']
        error_data = {}
        
        for component in components:
            error_rate = np.random.uniform(0.1, 5.0)
            error_count = np.random.randint(1, 20)
            
            error_data[component] = {
                'error_rate_percent': error_rate,
                'error_count': error_count,
                'status': 'healthy' if error_rate < 2.0 else 'warning' if error_rate < 5.0 else 'critical',
                'last_error': datetime.now().isoformat()
            }
        
        return {
            'components': error_data,
            'overall_error_rate': np.mean([e['error_rate_percent'] for e in error_data.values()]),
            'total_errors': sum(e['error_count'] for e in error_data.values()),
            'last_updated': datetime.now().isoformat()
        }
    
    def get_response_times(self) -> Dict[str, Any]:
        """Get response time metrics."""
        operations = ['delegation', 'analysis', 'report_generation', 'data_processing']
        response_data = {}
        
        for operation in operations:
            avg_time = np.random.uniform(1.0, 10.0)
            p95_time = avg_time * np.random.uniform(1.5, 3.0)
            p99_time = avg_time * np.random.uniform(2.0, 5.0)
            
            response_data[operation] = {
                'avg_response_time_seconds': avg_time,
                'p95_response_time_seconds': p95_time,
                'p99_response_time_seconds': p99_time,
                'status': 'healthy' if avg_time < 5.0 else 'warning' if avg_time < 10.0 else 'critical'
            }
        
        return {
            'operations': response_data,
            'overall_avg_response_time': np.mean([r['avg_response_time_seconds'] for r in response_data.values()]),
            'last_updated': datetime.now().isoformat()
        }

class PerformanceTrendsAnalyzer:
    """Analyzes performance trends over time."""
    
    def __init__(self):
        self.trend_data: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        logger.info("Initialized PerformanceTrendsAnalyzer")
    
    def add_data_point(self, metric_name: str, timestamp: str, value: float):
        """Add a data point to trend analysis."""
        self.trend_data[metric_name].append((timestamp, value))
        # Keep only last 1000 points per metric
        if len(self.trend_data[metric_name]) > 1000:
            self.trend_data[metric_name] = self.trend_data[metric_name][-1000:]
    
    def get_trends(self, time_period: str = "24h") -> Dict[str, Any]:
        """Get performance trends for specified time period."""
        trends = {}
        
        for metric_name, data_points in self.trend_data.items():
            if not data_points:
                continue
                
            # Get recent data points
            recent_points = data_points[-100:] if len(data_points) > 100 else data_points
            values = [point[1] for point in recent_points]
            timestamps = [point[0] for point in recent_points]
            
            # Calculate trend direction
            if len(values) >= 2:
                trend_direction = "up" if values[-1] > values[0] else "down" if values[-1] < values[0] else "stable"
                change_percentage = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
            else:
                trend_direction = "stable"
                change_percentage = 0.0
            
            trends[metric_name] = {
                'values': values,
                'timestamps': timestamps,
                'trend_direction': trend_direction,
                'change_percentage': change_percentage,
                'current_value': values[-1] if values else 0,
                'min_value': min(values) if values else 0,
                'max_value': max(values) if values else 0,
                'avg_value': np.mean(values) if values else 0
            }
        
        return {
            'time_period': time_period,
            'trends': trends,
            'total_metrics': len(trends),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def analyze_trends(self, time_period: str = "24h") -> Dict[str, Any]:
        """Analyze trend patterns and anomalies."""
        trends = self.get_trends(time_period)
        
        analysis = {
            'improving_metrics': [],
            'degrading_metrics': [],
            'stable_metrics': [],
            'volatile_metrics': [],
            'trend_summary': {}
        }
        
        for metric_name, trend_data in trends['trends'].items():
            change_pct = trend_data['change_percentage']
            values = trend_data['values']
            
            # Categorize trends
            if change_pct > 5:
                analysis['improving_metrics'].append({
                    'metric': metric_name,
                    'improvement_percent': change_pct,
                    'current_value': trend_data['current_value']
                })
            elif change_pct < -5:
                analysis['degrading_metrics'].append({
                    'metric': metric_name,
                    'degradation_percent': abs(change_pct),
                    'current_value': trend_data['current_value']
                })
            else:
                analysis['stable_metrics'].append({
                    'metric': metric_name,
                    'current_value': trend_data['current_value']
                })
            
            # Check for volatility
            if len(values) > 1:
                volatility = np.std(values) / np.mean(values) if np.mean(values) != 0 else 0
                if volatility > 0.2:  # 20% volatility threshold
                    analysis['volatile_metrics'].append({
                        'metric': metric_name,
                        'volatility_percent': volatility * 100,
                        'current_value': trend_data['current_value']
                    })
        
        return analysis
    
    def detect_anomalies(self, time_period: str = "24h") -> Dict[str, Any]:
        """Detect performance anomalies."""
        anomalies = []
        
        for metric_name, data_points in self.trend_data.items():
            if len(data_points) < 10:
                continue
                
            values = [point[1] for point in data_points[-50:]]  # Last 50 points
            if len(values) < 10:
                continue
            
            # Simple anomaly detection using z-score
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if std_val > 0:
                for i, value in enumerate(values):
                    z_score = abs((value - mean_val) / std_val)
                    if z_score > 2.5:  # Anomaly threshold
                        anomalies.append({
                            'metric_name': metric_name,
                            'timestamp': data_points[-len(values) + i][0],
                            'value': value,
                            'z_score': z_score,
                            'severity': 'high' if z_score > 3.0 else 'medium'
                        })
        
        return {
            'anomalies': anomalies,
            'total_anomalies': len(anomalies),
            'high_severity_count': len([a for a in anomalies if a['severity'] == 'high']),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def forecast_performance(self, time_period: str = "24h") -> Dict[str, Any]:
        """Forecast future performance trends."""
        forecasts = {}
        
        for metric_name, data_points in self.trend_data.items():
            if len(data_points) < 20:
                continue
                
            values = [point[1] for point in data_points[-30:]]  # Last 30 points
            
            # Simple linear trend forecast
            x = np.arange(len(values))
            coeffs = np.polyfit(x, values, 1)
            
            # Forecast next 7 points
            future_x = np.arange(len(values), len(values) + 7)
            forecast_values = np.polyval(coeffs, future_x)
            
            forecasts[metric_name] = {
                'current_value': values[-1],
                'forecast_values': forecast_values.tolist(),
                'trend_slope': coeffs[0],
                'confidence': 'high' if abs(coeffs[0]) < 0.1 else 'medium' if abs(coeffs[0]) < 0.5 else 'low'
            }
        
        return {
            'forecasts': forecasts,
            'forecast_period': '7 data points',
            'total_forecasts': len(forecasts),
            'analysis_timestamp': datetime.now().isoformat()
        }

class UsagePatternsAnalyzer:
    """Analyzes usage patterns and user behavior."""
    
    def __init__(self):
        self.usage_data: List[Dict] = []
        logger.info("Initialized UsagePatternsAnalyzer")
    
    def add_usage_event(self, event_data: Dict):
        """Add a usage event for pattern analysis."""
        self.usage_data.append({
            'timestamp': datetime.now().isoformat(),
            'user_id': event_data.get('user_id', 'unknown'),
            'feature': event_data.get('feature', 'unknown'),
            'duration': event_data.get('duration', 0),
            'success': event_data.get('success', True)
        })
    
    def get_patterns(self) -> Dict[str, Any]:
        """Get usage patterns."""
        if not self.usage_data:
            return {'patterns': [], 'total_events': 0}
        
        # Feature usage patterns
        feature_counts = Counter(event['feature'] for event in self.usage_data)
        hourly_patterns = Counter()
        daily_patterns = Counter()
        
        for event in self.usage_data:
            timestamp = datetime.fromisoformat(event['timestamp'])
            hourly_patterns[timestamp.hour] += 1
            daily_patterns[timestamp.weekday()] += 1
        
        return {
            'feature_usage': dict(feature_counts.most_common(10)),
            'hourly_patterns': dict(hourly_patterns),
            'daily_patterns': dict(daily_patterns),
            'total_events': len(self.usage_data),
            'unique_users': len(set(event['user_id'] for event in self.usage_data)),
            'unique_features': len(set(event['feature'] for event in self.usage_data)),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def get_user_segments(self) -> Dict[str, Any]:
        """Get user segmentation analysis."""
        if not self.usage_data:
            return {'segments': [], 'total_users': 0}
        
        user_stats = defaultdict(lambda: {'usage_count': 0, 'features_used': set(), 'total_duration': 0})
        
        for event in self.usage_data:
            user_id = event['user_id']
            user_stats[user_id]['usage_count'] += 1
            user_stats[user_id]['features_used'].add(event['feature'])
            user_stats[user_id]['total_duration'] += event['duration']
        
        # Segment users
        segments = {
            'power_users': [],
            'regular_users': [],
            'casual_users': []
        }
        
        usage_counts = [stats['usage_count'] for stats in user_stats.values()]
        if usage_counts:
            p75 = np.percentile(usage_counts, 75)
            p25 = np.percentile(usage_counts, 25)
            
            for user_id, stats in user_stats.items():
                if stats['usage_count'] >= p75:
                    segments['power_users'].append(user_id)
                elif stats['usage_count'] >= p25:
                    segments['regular_users'].append(user_id)
                else:
                    segments['casual_users'].append(user_id)
        
        return {
            'segments': {
                name: {'count': len(users), 'users': users[:5]}  # Show first 5 users
                for name, users in segments.items()
            },
            'total_users': len(user_stats),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def get_feature_popularity(self) -> Dict[str, Any]:
        """Get feature popularity analysis."""
        if not self.usage_data:
            return {'features': [], 'total_usage': 0}
        
        feature_stats = defaultdict(lambda: {'usage_count': 0, 'users': set(), 'avg_duration': 0, 'total_duration': 0})
        
        for event in self.usage_data:
            feature = event['feature']
            feature_stats[feature]['usage_count'] += 1
            feature_stats[feature]['users'].add(event['user_id'])
            feature_stats[feature]['total_duration'] += event['duration']
        
        # Calculate averages
        for feature, stats in feature_stats.items():
            stats['avg_duration'] = stats['total_duration'] / stats['usage_count']
            stats['unique_users'] = len(stats['users'])
            del stats['users']  # Remove set for JSON serialization
        
        # Sort by usage count
        sorted_features = sorted(feature_stats.items(), key=lambda x: x[1]['usage_count'], reverse=True)
        
        return {
            'features': [
                {'feature': feature, **stats}
                for feature, stats in sorted_features[:10]
            ],
            'total_usage': sum(stats['usage_count'] for stats in feature_stats.values()),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def get_usage_correlations(self) -> Dict[str, Any]:
        """Get usage correlations between features."""
        if len(self.usage_data) < 10:
            return {'correlations': [], 'total_correlations': 0}
        
        # Group events by user session
        user_sessions = defaultdict(list)
        for event in self.usage_data:
            user_sessions[event['user_id']].append(event['feature'])
        
        # Find feature co-occurrences
        feature_pairs = defaultdict(int)
        total_sessions = 0
        
        for user_id, features in user_sessions.items():
            if len(features) > 1:
                total_sessions += 1
                for i in range(len(features)):
                    for j in range(i + 1, len(features)):
                        pair = tuple(sorted([features[i], features[j]]))
                        feature_pairs[pair] += 1
        
        # Calculate correlations (simplified)
        correlations = []
        for (feature1, feature2), count in feature_pairs.items():
            if count > 2:  # Minimum co-occurrence threshold
                correlation_strength = count / total_sessions if total_sessions > 0 else 0
                correlations.append({
                    'feature1': feature1,
                    'feature2': feature2,
                    'co_occurrence_count': count,
                    'correlation_strength': correlation_strength
                })
        
        # Sort by correlation strength
        correlations.sort(key=lambda x: x['correlation_strength'], reverse=True)
        
        return {
            'correlations': correlations[:10],  # Top 10 correlations
            'total_correlations': len(correlations),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def get_behavioral_insights(self) -> Dict[str, Any]:
        """Get behavioral insights."""
        patterns = self.get_patterns()
        segments = self.get_user_segments()
        
        insights = []
        
        if patterns['total_events'] > 0:
            # Peak usage insights
            if patterns['hourly_patterns']:
                peak_hour = max(patterns['hourly_patterns'].items(), key=lambda x: x[1])[0]
                insights.append(f"Peak usage occurs at {peak_hour}:00 ({patterns['hourly_patterns'][peak_hour]} events)")
            
            # Feature insights
            if patterns['feature_usage']:
                top_feature = max(patterns['feature_usage'].items(), key=lambda x: x[1])
                insights.append(f"Most popular feature: {top_feature[0]} ({top_feature[1]} uses)")
            
            # User segment insights
            if segments['segments']['power_users']['count'] > 0:
                insights.append(f"Power users represent {segments['segments']['power_users']['count']} users with high engagement")
        
        return {
            'insights': insights,
            'total_insights': len(insights),
            'analysis_timestamp': datetime.now().isoformat()
        }

class PredictiveInsightsGenerator:
    """Generates predictive insights and recommendations."""
    
    def __init__(self):
        self.performance_history: List[Dict] = []
        self.usage_history: List[Dict] = []
        logger.info("Initialized PredictiveInsightsGenerator")
    
    def get_performance_predictions(self) -> Dict[str, Any]:
        """Get performance predictions."""
        predictions = []
        
        # Mock performance predictions
        predictions.append({
            'metric': 'response_time',
            'current_value': 2.5,
            'predicted_value': 2.8,
            'confidence': 'high',
            'time_horizon': '24h',
            'trend': 'increasing'
        })
        
        predictions.append({
            'metric': 'throughput',
            'current_value': 45.2,
            'predicted_value': 48.7,
            'confidence': 'medium',
            'time_horizon': '7d',
            'trend': 'increasing'
        })
        
        return {
            'predictions': predictions,
            'total_predictions': len(predictions),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def get_usage_predictions(self) -> Dict[str, Any]:
        """Get usage predictions."""
        predictions = []
        
        # Mock usage predictions
        predictions.append({
            'metric': 'daily_active_users',
            'current_value': 23,
            'predicted_value': 28,
            'confidence': 'high',
            'time_horizon': '30d',
            'trend': 'increasing'
        })
        
        predictions.append({
            'metric': 'feature_usage',
            'feature': 'district_heating_analysis',
            'current_value': 45,
            'predicted_value': 52,
            'confidence': 'medium',
            'time_horizon': '14d',
            'trend': 'increasing'
        })
        
        return {
            'predictions': predictions,
            'total_predictions': len(predictions),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get optimization recommendations."""
        recommendations = []
        
        # Mock optimization recommendations
        recommendations.append({
            'category': 'performance',
            'priority': 'high',
            'description': 'Optimize database queries for faster response times',
            'expected_improvement': '30% reduction in query time',
            'implementation_effort': 'medium',
            'time_to_implement': '2-3 weeks'
        })
        
        recommendations.append({
            'category': 'scalability',
            'priority': 'medium',
            'description': 'Implement caching for frequently accessed data',
            'expected_improvement': '50% reduction in data access time',
            'implementation_effort': 'low',
            'time_to_implement': '1 week'
        })
        
        return {
            'recommendations': recommendations,
            'total_recommendations': len(recommendations),
            'high_priority_count': len([r for r in recommendations if r['priority'] == 'high']),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def get_risk_assessments(self) -> Dict[str, Any]:
        """Get risk assessments."""
        risks = []
        
        # Mock risk assessments
        risks.append({
            'risk_type': 'performance_degradation',
            'probability': 'medium',
            'impact': 'high',
            'description': 'Response times may exceed SLA during peak hours',
            'mitigation': 'Implement auto-scaling and load balancing',
            'timeframe': 'next 30 days'
        })
        
        risks.append({
            'risk_type': 'resource_exhaustion',
            'probability': 'low',
            'impact': 'critical',
            'description': 'Memory usage trending upward, may hit limits',
            'mitigation': 'Optimize memory usage and add monitoring',
            'timeframe': 'next 60 days'
        })
        
        return {
            'risks': risks,
            'total_risks': len(risks),
            'high_probability_risks': len([r for r in risks if r['probability'] == 'high']),
            'critical_impact_risks': len([r for r in risks if r['impact'] == 'critical']),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def get_opportunity_identification(self) -> Dict[str, Any]:
        """Get opportunity identification."""
        opportunities = []
        
        # Mock opportunities
        opportunities.append({
            'category': 'feature_enhancement',
            'description': 'Add real-time collaboration features',
            'potential_impact': 'high',
            'user_demand': 'medium',
            'implementation_complexity': 'medium',
            'estimated_roi': '150%'
        })
        
        opportunities.append({
            'category': 'performance_optimization',
            'description': 'Implement predictive caching',
            'potential_impact': 'medium',
            'user_demand': 'high',
            'implementation_complexity': 'low',
            'estimated_roi': '200%'
        })
        
        return {
            'opportunities': opportunities,
            'total_opportunities': len(opportunities),
            'high_impact_count': len([o for o in opportunities if o['potential_impact'] == 'high']),
            'analysis_timestamp': datetime.now().isoformat()
        }

class DashboardRenderer:
    """Renders dashboards as HTML."""
    
    def __init__(self):
        logger.info("Initialized DashboardRenderer")
    
    def render_html(self, dashboard_data: Dict[str, Any]) -> str:
        """Render dashboard data as HTML."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADK System Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .status-healthy {{ color: #28a745; }}
        .status-warning {{ color: #ffc107; }}
        .status-critical {{ color: #dc3545; }}
        .insights-section {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .insight-item {{ padding: 10px; border-left: 4px solid #667eea; margin: 10px 0; background: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>ADK System Dashboard</h1>
            <p>Real-time monitoring and analytics</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value status-healthy">{health_score:.1f}%</div>
                <div class="metric-label">System Health</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{active_users}</div>
                <div class="metric-label">Active Users</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_response_time:.1f}s</div>
                <div class="metric-label">Avg Response Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_errors}</div>
                <div class="metric-label">Total Errors</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>System Performance Trends</h3>
            <canvas id="performanceChart" width="400" height="200"></canvas>
        </div>
        
        <div class="insights-section">
            <h3>Key Insights</h3>
            <div class="insight-item">
                <strong>System Status:</strong> {system_status}
            </div>
            <div class="insight-item">
                <strong>Most Used Tool:</strong> {most_used_tool}
            </div>
            <div class="insight-item">
                <strong>Peak Usage Hour:</strong> {peak_usage_hour}:00
            </div>
            <div class="insight-item">
                <strong>Last Updated:</strong> {last_updated}
            </div>
        </div>
    </div>
    
    <script>
        // Mock chart data
        const ctx = document.getElementById('performanceChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: ['1h ago', '2h ago', '3h ago', '4h ago', '5h ago', 'Now'],
                datasets: [{{
                    label: 'Response Time (s)',
                    data: [2.1, 2.3, 2.0, 2.5, 2.2, 2.4],
                    borderColor: 'rgb(102, 126, 234)',
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """
        
        # Extract data for template
        live_metrics = dashboard_data.get('live_metrics', {})
        system_health = live_metrics.get('system_health', {})
        user_activity = live_metrics.get('user_activity', {})
        agent_performance = live_metrics.get('agent_performance', {})
        error_rates = live_metrics.get('error_rates', {})
        tool_usage = live_metrics.get('tool_usage', {})
        
        html_content = html_template.format(
            health_score=system_health.get('health_score', 95.0),
            active_users=user_activity.get('active_users', 15),
            avg_response_time=agent_performance.get('average_response_time', 2.5),
            total_errors=error_rates.get('total_errors', 3),
            system_status=system_health.get('status', 'healthy'),
            most_used_tool=tool_usage.get('most_used_tool', 'data_exploration'),
            peak_usage_hour=user_activity.get('peak_usage_hour', 14),
            last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        return html_content

class ADKDashboard:
    """Advanced ADK-specific dashboard."""
    
    def __init__(self):
        self.real_time_monitor = RealTimeSystemMonitor()
        self.performance_trends = PerformanceTrendsAnalyzer()
        self.usage_patterns = UsagePatternsAnalyzer()
        self.predictive_insights = PredictiveInsightsGenerator()
        self.dashboard_renderer = DashboardRenderer()
        logger.info("Initialized ADKDashboard")
    
    def show_live_metrics(self) -> Dict:
        """Show live system metrics."""
        logger.info("Getting live system metrics")
        
        return {
            'system_health': self.real_time_monitor.get_system_health(),
            'agent_performance': self.real_time_monitor.get_agent_performance(),
            'tool_usage': self.real_time_monitor.get_tool_usage(),
            'user_activity': self.real_time_monitor.get_user_activity(),
            'resource_utilization': self.real_time_monitor.get_resource_utilization(),
            'error_rates': self.real_time_monitor.get_error_rates(),
            'response_times': self.real_time_monitor.get_response_times(),
            'timestamp': datetime.now().isoformat()
        }
    
    def show_performance_trends(self, time_period: str = "24h") -> Dict:
        """Show performance trends over time."""
        logger.info(f"Getting performance trends for {time_period}")
        
        return {
            'time_period': time_period,
            'performance_trends': self.performance_trends.get_trends(time_period),
            'trend_analysis': self.performance_trends.analyze_trends(time_period),
            'anomaly_detection': self.performance_trends.detect_anomalies(time_period),
            'forecasting': self.performance_trends.forecast_performance(time_period),
            'timestamp': datetime.now().isoformat()
        }
    
    def show_usage_patterns(self) -> Dict:
        """Show usage patterns and insights."""
        logger.info("Getting usage patterns")
        
        return {
            'usage_patterns': self.usage_patterns.get_patterns(),
            'user_segments': self.usage_patterns.get_user_segments(),
            'feature_popularity': self.usage_patterns.get_feature_popularity(),
            'usage_correlations': self.usage_patterns.get_usage_correlations(),
            'behavioral_insights': self.usage_patterns.get_behavioral_insights(),
            'timestamp': datetime.now().isoformat()
        }
    
    def show_predictive_insights(self) -> Dict:
        """Show predictive insights and recommendations."""
        logger.info("Getting predictive insights")
        
        return {
            'performance_predictions': self.predictive_insights.get_performance_predictions(),
            'usage_predictions': self.predictive_insights.get_usage_predictions(),
            'optimization_recommendations': self.predictive_insights.get_optimization_recommendations(),
            'risk_assessments': self.predictive_insights.get_risk_assessments(),
            'opportunity_identification': self.predictive_insights.get_opportunity_identification(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_dashboard_data(self, dashboard_type: str = "comprehensive") -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        logger.info(f"Getting {dashboard_type} dashboard data")
        
        dashboard_data = {
            'dashboard_type': dashboard_type,
            'live_metrics': self.show_live_metrics(),
            'performance_trends': self.show_performance_trends(),
            'usage_patterns': self.show_usage_patterns(),
            'predictive_insights': self.show_predictive_insights(),
            'generated_at': datetime.now().isoformat()
        }
        
        return dashboard_data
    
    def render_dashboard(self, dashboard_type: str = "comprehensive") -> str:
        """Render dashboard as HTML."""
        logger.info(f"Rendering {dashboard_type} dashboard as HTML")
        
        dashboard_data = self.get_dashboard_data(dashboard_type)
        html_content = self.dashboard_renderer.render_html(dashboard_data)
        
        return html_content
    
    def save_dashboard_html(self, output_path: str, dashboard_type: str = "comprehensive"):
        """Save dashboard as HTML file."""
        logger.info(f"Saving {dashboard_type} dashboard to {output_path}")
        
        html_content = self.render_dashboard(dashboard_type)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Dashboard saved to {output_path}")
    
    def close(self):
        """Close database connections."""
        self.real_time_monitor.conn.close()
        logger.info("ADKDashboard closed")
