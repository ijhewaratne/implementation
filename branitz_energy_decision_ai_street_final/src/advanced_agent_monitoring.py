#!/usr/bin/env python3
"""
ADK Agent Performance Monitoring
Advanced ADK agent performance monitoring system with efficiency tracking, delegation analytics, response time analysis, learning progress tracking, and performance optimization.
"""

import os
import sys
import json
import time
import logging
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import hashlib
import numpy as np
from pathlib import Path
import queue
import psutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentMonitoringSession:
    """Agent monitoring session."""
    session_id: str
    session_name: str
    start_time: str
    status: str = "active"
    agents_monitored: List[str] = None
    metrics_collected: Dict[str, Any] = None

@dataclass
class AgentEfficiencyMetrics:
    """Agent efficiency metrics."""
    agent_name: str
    operation: str
    timestamp: str
    execution_time: float
    success_rate: float
    resource_usage: Dict[str, float]
    throughput: float
    accuracy: float
    efficiency_score: float
    optimization_suggestions: List[Dict]

@dataclass
class DelegationMetrics:
    """Delegation metrics."""
    delegator_agent: str
    delegatee_agent: str
    timestamp: str
    delegation_reason: str
    success: bool
    execution_time: float
    result_quality: float
    delegation_pattern: str

@dataclass
class LearningProgressMetrics:
    """Learning progress metrics."""
    agent_name: str
    timestamp: str
    learning_metric: str
    previous_value: float
    current_value: float
    improvement_rate: float
    progress_score: float
    improvement_areas: List[str]

class EfficiencyTracker:
    """Agent efficiency tracking and analysis."""
    
    def __init__(self):
        self.efficiency_data: Dict[str, List[Dict]] = defaultdict(list)
        self.efficiency_scores: Dict[str, float] = defaultdict(float)
        self.performance_trends: Dict[str, List[float]] = defaultdict(list)
        self.optimization_history: Dict[str, List[Dict]] = defaultdict(list)
        logger.info("Initialized EfficiencyTracker")
    
    def start_tracking(self, session: AgentMonitoringSession):
        """Start efficiency tracking for a session."""
        self.efficiency_data[session.session_id] = []
        logger.info(f"Started efficiency tracking for session: {session.session_id}")
    
    def record_efficiency(self, efficiency_data: Dict[str, Any]):
        """Record agent efficiency metrics."""
        agent_name = efficiency_data['agent_name']
        operation = efficiency_data['operation']
        
        # Store efficiency data
        self.efficiency_data[agent_name].append(efficiency_data)
        
        # Keep only recent data (last 1000 entries)
        if len(self.efficiency_data[agent_name]) > 1000:
            self.efficiency_data[agent_name] = self.efficiency_data[agent_name][-1000:]
        
        # Update efficiency score
        self.efficiency_scores[agent_name] = efficiency_data.get('efficiency_score', 0)
        
        # Update performance trends
        self.performance_trends[agent_name].append(efficiency_data.get('efficiency_score', 0))
        
        # Keep only recent trends (last 100 entries)
        if len(self.performance_trends[agent_name]) > 100:
            self.performance_trends[agent_name] = self.performance_trends[agent_name][-100:]
        
        # Record optimization suggestions
        optimization_suggestions = efficiency_data.get('optimization_suggestions', [])
        if optimization_suggestions:
            self.optimization_history[agent_name].append({
                'timestamp': efficiency_data['timestamp'],
                'suggestions': optimization_suggestions
            })
        
        logger.debug(f"Recorded efficiency data for agent: {agent_name}")
    
    def calculate_efficiency_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate comprehensive efficiency score."""
        try:
            # Base metrics
            execution_time = metrics.get('execution_time', 0)
            success_rate = metrics.get('success_rate', 0)
            resource_usage = metrics.get('resource_usage', {})
            throughput = metrics.get('throughput', 0)
            accuracy = metrics.get('accuracy', 0)
            
            # Normalize metrics (0-1 scale)
            time_score = max(0, 1 - (execution_time / 10.0)) if execution_time > 0 else 0  # 10s max
            success_score = success_rate
            resource_score = max(0, 1 - (resource_usage.get('memory_mb', 0) / 1000.0))  # 1GB max
            throughput_score = min(1, throughput / 100.0)  # 100 ops/s max
            accuracy_score = accuracy
            
            # Weighted efficiency score
            weights = {
                'time': 0.25,
                'success': 0.30,
                'resource': 0.15,
                'throughput': 0.15,
                'accuracy': 0.15
            }
            
            efficiency_score = (
                time_score * weights['time'] +
                success_score * weights['success'] +
                resource_score * weights['resource'] +
                throughput_score * weights['throughput'] +
                accuracy_score * weights['accuracy']
            )
            
            return min(max(efficiency_score * 100, 0), 100)
            
        except Exception as e:
            logger.error(f"Error calculating efficiency score: {e}")
            return 0.0
    
    def get_efficiency_summary(self, agent_name: str) -> Dict[str, Any]:
        """Get efficiency summary for an agent."""
        if agent_name not in self.efficiency_data:
            return {'status': 'no_data'}
        
        data = self.efficiency_data[agent_name]
        if not data:
            return {'status': 'no_data'}
        
        # Calculate summary statistics
        efficiency_scores = [entry.get('efficiency_score', 0) for entry in data]
        execution_times = [entry.get('metrics', {}).get('execution_time', 0) for entry in data]
        success_rates = [entry.get('metrics', {}).get('success_rate', 0) for entry in data]
        
        # Calculate trends
        trend = self._calculate_efficiency_trend(agent_name)
        
        # Get recent optimization suggestions
        recent_suggestions = self._get_recent_optimization_suggestions(agent_name)
        
        return {
            'agent_name': agent_name,
            'total_operations': len(data),
            'average_efficiency_score': np.mean(efficiency_scores) if efficiency_scores else 0,
            'current_efficiency_score': efficiency_scores[-1] if efficiency_scores else 0,
            'average_execution_time': np.mean(execution_times) if execution_times else 0,
            'average_success_rate': np.mean(success_rates) if success_rates else 0,
            'efficiency_trend': trend,
            'recent_optimization_suggestions': recent_suggestions,
            'performance_grade': self._calculate_performance_grade(np.mean(efficiency_scores) if efficiency_scores else 0)
        }
    
    def _calculate_efficiency_trend(self, agent_name: str) -> str:
        """Calculate efficiency trend for an agent."""
        if agent_name not in self.performance_trends or len(self.performance_trends[agent_name]) < 10:
            return 'insufficient_data'
        
        recent_scores = self.performance_trends[agent_name][-10:]
        older_scores = self.performance_trends[agent_name][-20:-10] if len(self.performance_trends[agent_name]) >= 20 else self.performance_trends[agent_name][:-10]
        
        if not older_scores:
            return 'insufficient_data'
        
        recent_avg = np.mean(recent_scores)
        older_avg = np.mean(older_scores)
        
        if recent_avg > older_avg * 1.05:
            return 'improving'
        elif recent_avg < older_avg * 0.95:
            return 'degrading'
        else:
            return 'stable'
    
    def _get_recent_optimization_suggestions(self, agent_name: str) -> List[Dict]:
        """Get recent optimization suggestions for an agent."""
        if agent_name not in self.optimization_history:
            return []
        
        # Get suggestions from last 10 entries
        recent_entries = self.optimization_history[agent_name][-10:]
        all_suggestions = []
        
        for entry in recent_entries:
            all_suggestions.extend(entry.get('suggestions', []))
        
        # Count suggestion frequency
        suggestion_counts = defaultdict(int)
        for suggestion in all_suggestions:
            suggestion_type = suggestion.get('type', 'unknown')
            suggestion_counts[suggestion_type] += 1
        
        # Return top suggestions
        top_suggestions = sorted(suggestion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return [{'type': suggestion_type, 'frequency': count} for suggestion_type, count in top_suggestions]
    
    def _calculate_performance_grade(self, efficiency_score: float) -> str:
        """Calculate performance grade based on efficiency score."""
        if efficiency_score >= 90:
            return 'A'
        elif efficiency_score >= 80:
            return 'B'
        elif efficiency_score >= 70:
            return 'C'
        elif efficiency_score >= 60:
            return 'D'
        else:
            return 'F'
    
    def get_efficiency_analytics(self) -> Dict[str, Any]:
        """Get comprehensive efficiency analytics."""
        return {
            'total_agents_tracked': len(self.efficiency_data),
            'total_operations_recorded': sum(len(data) for data in self.efficiency_data.values()),
            'average_efficiency_score': np.mean(list(self.efficiency_scores.values())) if self.efficiency_scores else 0,
            'top_performing_agents': self._get_top_performing_agents(),
            'agents_needing_attention': self._get_agents_needing_attention(),
            'overall_trend': self._calculate_overall_trend()
        }
    
    def _get_top_performing_agents(self) -> List[Dict]:
        """Get top performing agents."""
        agent_scores = [(agent, score) for agent, score in self.efficiency_scores.items()]
        top_agents = sorted(agent_scores, key=lambda x: x[1], reverse=True)[:5]
        
        return [{'agent_name': agent, 'efficiency_score': score} for agent, score in top_agents]
    
    def _get_agents_needing_attention(self) -> List[Dict]:
        """Get agents that need attention."""
        agents_needing_attention = []
        
        for agent_name in self.efficiency_data:
            summary = self.get_efficiency_summary(agent_name)
            if summary.get('status') != 'no_data':
                efficiency_score = summary.get('current_efficiency_score', 0)
                trend = summary.get('efficiency_trend', 'stable')
                
                if efficiency_score < 70 or trend == 'degrading':
                    agents_needing_attention.append({
                        'agent_name': agent_name,
                        'efficiency_score': efficiency_score,
                        'trend': trend,
                        'grade': summary.get('performance_grade', 'F')
                    })
        
        return sorted(agents_needing_attention, key=lambda x: x['efficiency_score'])[:5]
    
    def _calculate_overall_trend(self) -> str:
        """Calculate overall efficiency trend."""
        if not self.performance_trends:
            return 'insufficient_data'
        
        all_trends = []
        for agent_name in self.performance_trends:
            trend = self._calculate_efficiency_trend(agent_name)
            if trend != 'insufficient_data':
                all_trends.append(trend)
        
        if not all_trends:
            return 'insufficient_data'
        
        # Count trend types
        improving_count = all_trends.count('improving')
        degrading_count = all_trends.count('degrading')
        stable_count = all_trends.count('stable')
        
        # Determine overall trend
        if improving_count > degrading_count and improving_count > stable_count:
            return 'improving'
        elif degrading_count > improving_count and degrading_count > stable_count:
            return 'degrading'
        else:
            return 'stable'

class DelegationAnalytics:
    """Delegation analytics and pattern analysis."""
    
    def __init__(self):
        self.delegation_data: Dict[str, List[Dict]] = defaultdict(list)
        self.delegation_patterns: Dict[str, Dict] = defaultdict(dict)
        self.success_rates: Dict[str, float] = defaultdict(float)
        self.delegation_network: Dict[str, List[str]] = defaultdict(list)
        logger.info("Initialized DelegationAnalytics")
    
    def start_analysis(self, session: AgentMonitoringSession):
        """Start delegation analysis for a session."""
        self.delegation_data[session.session_id] = []
        logger.info(f"Started delegation analysis for session: {session.session_id}")
    
    def record_delegation(self, delegation_data: Dict[str, Any]):
        """Record delegation metrics."""
        delegator = delegation_data.get('delegator_agent', 'unknown')
        delegatee = delegation_data.get('delegatee_agent', 'unknown')
        
        # Store delegation data
        delegation_key = f"{delegator}->{delegatee}"
        self.delegation_data[delegation_key].append(delegation_data)
        
        # Keep only recent data (last 500 entries)
        if len(self.delegation_data[delegation_key]) > 500:
            self.delegation_data[delegation_key] = self.delegation_data[delegation_key][-500:]
        
        # Update delegation network
        if delegatee not in self.delegation_network[delegator]:
            self.delegation_network[delegator].append(delegatee)
        
        # Update success rates
        self._update_success_rates(delegation_key)
        
        # Update delegation patterns
        self._update_delegation_patterns(delegation_key)
        
        logger.debug(f"Recorded delegation: {delegator} -> {delegatee}")
    
    def _update_success_rates(self, delegation_key: str):
        """Update success rates for delegation."""
        if delegation_key not in self.delegation_data:
            return
        
        data = self.delegation_data[delegation_key]
        if not data:
            return
        
        successful_delegations = sum(1 for entry in data if entry.get('success', False))
        total_delegations = len(data)
        
        self.success_rates[delegation_key] = successful_delegations / total_delegations if total_delegations > 0 else 0
    
    def _update_delegation_patterns(self, delegation_key: str):
        """Update delegation patterns."""
        if delegation_key not in self.delegation_data:
            return
        
        data = self.delegation_data[delegation_key]
        if not data:
            return
        
        # Analyze delegation patterns
        patterns = {
            'total_delegations': len(data),
            'successful_delegations': sum(1 for entry in data if entry.get('success', False)),
            'average_execution_time': np.mean([entry.get('execution_time', 0) for entry in data]),
            'average_result_quality': np.mean([entry.get('result_quality', 0) for entry in data]),
            'common_reasons': self._get_common_delegation_reasons(data),
            'delegation_frequency': len(data),
            'last_delegation': data[-1].get('timestamp') if data else None
        }
        
        self.delegation_patterns[delegation_key] = patterns
    
    def _get_common_delegation_reasons(self, data: List[Dict]) -> List[Dict]:
        """Get common delegation reasons."""
        reason_counts = defaultdict(int)
        
        for entry in data:
            reason = entry.get('delegation_reason', 'unknown')
            reason_counts[reason] += 1
        
        # Return top 5 reasons
        top_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [{'reason': reason, 'count': count} for reason, count in top_reasons]
    
    def get_patterns(self) -> Dict[str, Any]:
        """Get delegation patterns."""
        return {
            'delegation_network': dict(self.delegation_network),
            'delegation_patterns': dict(self.delegation_patterns),
            'total_delegation_paths': len(self.delegation_data),
            'most_active_delegator': self._get_most_active_delegator(),
            'most_requested_delegatee': self._get_most_requested_delegatee()
        }
    
    def _get_most_active_delegator(self) -> Optional[str]:
        """Get most active delegator agent."""
        delegator_counts = defaultdict(int)
        
        for delegation_key in self.delegation_data:
            if '->' in delegation_key:
                parts = delegation_key.split('->')
                if len(parts) >= 1:
                    delegator = parts[0]
                    delegator_counts[delegator] += len(self.delegation_data[delegation_key])
        
        if not delegator_counts:
            return None
        
        return max(delegator_counts, key=delegator_counts.get)
    
    def _get_most_requested_delegatee(self) -> Optional[str]:
        """Get most requested delegatee agent."""
        delegatee_counts = defaultdict(int)
        
        for delegation_key in self.delegation_data:
            if '->' in delegation_key:
                parts = delegation_key.split('->')
                if len(parts) >= 2:
                    delegatee = parts[1]
                    delegatee_counts[delegatee] += len(self.delegation_data[delegation_key])
        
        if not delegatee_counts:
            return None
        
        return max(delegatee_counts, key=delegatee_counts.get)
    
    def get_success_rates(self) -> Dict[str, float]:
        """Get delegation success rates."""
        return dict(self.success_rates)
    
    def get_optimization_opportunities(self) -> List[Dict]:
        """Get delegation optimization opportunities."""
        opportunities = []
        
        for delegation_key, success_rate in self.success_rates.items():
            if success_rate < 0.8:  # Low success rate
                delegator, delegatee = delegation_key.split('->')
                pattern = self.delegation_patterns.get(delegation_key, {})
                
                opportunities.append({
                    'delegation_path': delegation_key,
                    'delegator': delegator,
                    'delegatee': delegatee,
                    'success_rate': success_rate,
                    'issue_type': 'low_success_rate',
                    'recommendation': f"Investigate delegation from {delegator} to {delegatee}",
                    'severity': 'high' if success_rate < 0.5 else 'medium'
                })
        
        # Check for inefficient delegation patterns
        for delegation_key, pattern in self.delegation_patterns.items():
            avg_execution_time = pattern.get('average_execution_time', 0)
            if avg_execution_time > 10.0:  # High execution time
                delegator, delegatee = delegation_key.split('->')
                
                opportunities.append({
                    'delegation_path': delegation_key,
                    'delegator': delegator,
                    'delegatee': delegatee,
                    'average_execution_time': avg_execution_time,
                    'issue_type': 'high_execution_time',
                    'recommendation': f"Optimize delegation from {delegator} to {delegatee}",
                    'severity': 'medium'
                })
        
        return sorted(opportunities, key=lambda x: x.get('success_rate', 1), reverse=False)
    
    def get_recommendations(self) -> List[Dict]:
        """Get delegation recommendations."""
        recommendations = []
        
        # Get optimization opportunities
        opportunities = self.get_optimization_opportunities()
        
        for opportunity in opportunities:
            if opportunity['issue_type'] == 'low_success_rate':
                recommendations.append({
                    'type': 'delegation_optimization',
                    'priority': opportunity['severity'],
                    'recommendation': f"Improve delegation success rate from {opportunity['delegator']} to {opportunity['delegatee']}",
                    'current_success_rate': opportunity['success_rate'],
                    'target_success_rate': 0.9,
                    'suggested_actions': [
                        "Review delegation criteria",
                        "Improve error handling",
                        "Add validation checks"
                    ]
                })
            elif opportunity['issue_type'] == 'high_execution_time':
                recommendations.append({
                    'type': 'performance_optimization',
                    'priority': opportunity['severity'],
                    'recommendation': f"Optimize delegation performance from {opportunity['delegator']} to {opportunity['delegatee']}",
                    'current_execution_time': opportunity['average_execution_time'],
                    'target_execution_time': 5.0,
                    'suggested_actions': [
                        "Cache frequent results",
                        "Optimize data transfer",
                        "Parallel processing"
                    ]
                })
        
        return recommendations

class ResponseTimeAnalyzer:
    """Response time analysis for ADK agents."""
    
    def __init__(self):
        self.response_times: Dict[str, List[float]] = defaultdict(list)
        self.response_patterns: Dict[str, Dict] = defaultdict(dict)
        self.performance_bottlenecks: Dict[str, List[Dict]] = defaultdict(list)
        self.response_time_trends: Dict[str, List[float]] = defaultdict(list)
        logger.info("Initialized ResponseTimeAnalyzer")
    
    def start_analysis(self, session: AgentMonitoringSession):
        """Start response time analysis for a session."""
        self.response_times[session.session_id] = []
        logger.info(f"Started response time analysis for session: {session.session_id}")
    
    def record_response_time(self, agent_name: str, operation: str, response_time: float, context: Dict[str, Any] = None):
        """Record response time for an agent operation."""
        response_key = f"{agent_name}:{operation}"
        
        # Store response time
        self.response_times[response_key].append(response_time)
        
        # Keep only recent data (last 1000 entries)
        if len(self.response_times[response_key]) > 1000:
            self.response_times[response_key] = self.response_times[response_key][-1000:]
        
        # Update response patterns
        self._update_response_patterns(response_key, response_time, context)
        
        # Check for performance bottlenecks
        self._check_performance_bottlenecks(response_key, response_time, context)
        
        # Update response time trends
        self._update_response_trends(response_key)
        
        logger.debug(f"Recorded response time for {response_key}: {response_time:.3f}s")
    
    def _update_response_patterns(self, response_key: str, response_time: float, context: Dict[str, Any]):
        """Update response patterns."""
        if response_key not in self.response_times:
            return
        
        times = self.response_times[response_key]
        if not times:
            return
        
        # Calculate pattern statistics
        patterns = {
            'average_response_time': np.mean(times),
            'median_response_time': np.median(times),
            'min_response_time': np.min(times),
            'max_response_time': np.max(times),
            'std_response_time': np.std(times),
            'p95_response_time': np.percentile(times, 95),
            'p99_response_time': np.percentile(times, 99),
            'total_operations': len(times),
            'last_updated': datetime.now().isoformat()
        }
        
        # Add context-specific patterns
        if context:
            patterns['context_factors'] = self._analyze_context_factors(context)
        
        self.response_patterns[response_key] = patterns
    
    def _analyze_context_factors(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze context factors affecting response time."""
        factors = {}
        
        # Analyze parameter complexity
        parameters = context.get('parameters', {})
        if parameters:
            factors['parameter_count'] = len(parameters)
            factors['parameter_complexity'] = self._calculate_parameter_complexity(parameters)
        
        # Analyze data size
        data_size = context.get('data_size', 0)
        if data_size > 0:
            factors['data_size_mb'] = data_size / (1024 * 1024)
        
        # Analyze concurrent operations
        concurrent_ops = context.get('concurrent_operations', 1)
        factors['concurrent_operations'] = concurrent_ops
        
        return factors
    
    def _calculate_parameter_complexity(self, parameters: Dict) -> float:
        """Calculate parameter complexity score."""
        if not parameters:
            return 0.0
        
        complexity = 0.0
        
        # Count parameters
        complexity += len(parameters) * 0.1
        
        # Count nested structures
        for value in parameters.values():
            if isinstance(value, (dict, list)):
                complexity += 0.5
                if isinstance(value, dict):
                    complexity += len(value) * 0.1
                elif isinstance(value, list):
                    complexity += len(value) * 0.05
        
        return min(complexity, 10.0)
    
    def _check_performance_bottlenecks(self, response_key: str, response_time: float, context: Dict[str, Any]):
        """Check for performance bottlenecks."""
        # Define bottleneck thresholds
        thresholds = {
            'warning': 5.0,  # 5 seconds
            'critical': 10.0  # 10 seconds
        }
        
        if response_time > thresholds['critical']:
            severity = 'critical'
        elif response_time > thresholds['warning']:
            severity = 'warning'
        else:
            return  # No bottleneck
        
        # Create bottleneck record
        bottleneck = {
            'timestamp': datetime.now().isoformat(),
            'response_key': response_key,
            'response_time': response_time,
            'severity': severity,
            'context': context,
            'threshold_exceeded': thresholds[severity]
        }
        
        self.performance_bottlenecks[response_key].append(bottleneck)
        
        # Keep only recent bottlenecks (last 100)
        if len(self.performance_bottlenecks[response_key]) > 100:
            self.performance_bottlenecks[response_key] = self.performance_bottlenecks[response_key][-100:]
        
        logger.warning(f"Performance bottleneck detected: {response_key} - {response_time:.3f}s ({severity})")
    
    def _update_response_trends(self, response_key: str):
        """Update response time trends."""
        if response_key not in self.response_times:
            return
        
        times = self.response_times[response_key]
        if len(times) < 10:
            return
        
        # Calculate trend over last 20 data points
        recent_times = times[-20:] if len(times) >= 20 else times
        older_times = times[-40:-20] if len(times) >= 40 else times[:-20] if len(times) >= 20 else []
        
        if not older_times:
            return
        
        recent_avg = np.mean(recent_times)
        older_avg = np.mean(older_times)
        
        # Determine trend
        if recent_avg > older_avg * 1.1:
            trend = 'degrading'
        elif recent_avg < older_avg * 0.9:
            trend = 'improving'
        else:
            trend = 'stable'
        
        self.response_time_trends[response_key] = {
            'trend': trend,
            'recent_average': recent_avg,
            'older_average': older_avg,
            'change_percentage': ((recent_avg - older_avg) / older_avg) * 100,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_response_time_summary(self, agent_name: str, operation: str = None) -> Dict[str, Any]:
        """Get response time summary for an agent."""
        if operation:
            response_key = f"{agent_name}:{operation}"
            keys_to_check = [response_key]
        else:
            # Get all operations for the agent
            keys_to_check = [key for key in self.response_times.keys() if key.startswith(f"{agent_name}:")]
        
        if not keys_to_check:
            return {'status': 'no_data'}
        
        all_times = []
        all_patterns = {}
        
        for key in keys_to_check:
            if key in self.response_times:
                all_times.extend(self.response_times[key])
                all_patterns[key] = self.response_patterns.get(key, {})
        
        if not all_times:
            return {'status': 'no_data'}
        
        # Calculate overall summary
        summary = {
            'agent_name': agent_name,
            'operation': operation,
            'total_operations': len(all_times),
            'average_response_time': np.mean(all_times),
            'median_response_time': np.median(all_times),
            'min_response_time': np.min(all_times),
            'max_response_time': np.max(all_times),
            'p95_response_time': np.percentile(all_times, 95),
            'p99_response_time': np.percentile(all_times, 99),
            'response_time_trends': dict(self.response_time_trends),
            'performance_bottlenecks': self._get_bottleneck_summary(keys_to_check),
            'performance_grade': self._calculate_response_time_grade(np.mean(all_times))
        }
        
        if len(keys_to_check) > 1:
            summary['operation_patterns'] = all_patterns
        
        return summary
    
    def _get_bottleneck_summary(self, keys_to_check: List[str]) -> Dict[str, Any]:
        """Get bottleneck summary for specified keys."""
        total_bottlenecks = 0
        critical_bottlenecks = 0
        warning_bottlenecks = 0
        
        for key in keys_to_check:
            if key in self.performance_bottlenecks:
                bottlenecks = self.performance_bottlenecks[key]
                total_bottlenecks += len(bottlenecks)
                critical_bottlenecks += len([b for b in bottlenecks if b['severity'] == 'critical'])
                warning_bottlenecks += len([b for b in bottlenecks if b['severity'] == 'warning'])
        
        return {
            'total_bottlenecks': total_bottlenecks,
            'critical_bottlenecks': critical_bottlenecks,
            'warning_bottlenecks': warning_bottlenecks,
            'bottleneck_rate': total_bottlenecks / sum(len(self.response_times[key]) for key in keys_to_check if key in self.response_times) if any(key in self.response_times for key in keys_to_check) else 0
        }
    
    def _calculate_response_time_grade(self, average_response_time: float) -> str:
        """Calculate response time grade."""
        if average_response_time <= 1.0:
            return 'A'
        elif average_response_time <= 2.0:
            return 'B'
        elif average_response_time <= 5.0:
            return 'C'
        elif average_response_time <= 10.0:
            return 'D'
        else:
            return 'F'
    
    def get_response_time_analytics(self) -> Dict[str, Any]:
        """Get comprehensive response time analytics."""
        return {
            'total_operations_tracked': sum(len(times) for times in self.response_times.values()),
            'unique_agent_operations': len(self.response_times),
            'average_response_time_overall': np.mean([np.mean(times) for times in self.response_times.values()]) if self.response_times else 0,
            'agents_with_bottlenecks': len(self.performance_bottlenecks),
            'total_bottlenecks': sum(len(bottlenecks) for bottlenecks in self.performance_bottlenecks.values()),
            'performance_trends': dict(self.response_time_trends),
            'top_slow_operations': self._get_top_slow_operations(),
            'performance_insights': self._get_performance_insights()
        }
    
    def _get_top_slow_operations(self) -> List[Dict]:
        """Get top slow operations."""
        operation_averages = []
        
        for response_key, times in self.response_times.items():
            if times:
                avg_time = np.mean(times)
                operation_averages.append({
                    'operation': response_key,
                    'average_response_time': avg_time,
                    'total_operations': len(times)
                })
        
        # Sort by average response time (descending)
        top_slow = sorted(operation_averages, key=lambda x: x['average_response_time'], reverse=True)[:10]
        
        return top_slow
    
    def _get_performance_insights(self) -> List[Dict]:
        """Get performance insights."""
        insights = []
        
        # Analyze trends
        for response_key, trend_data in self.response_time_trends.items():
            trend = trend_data.get('trend', 'stable')
            change_percentage = trend_data.get('change_percentage', 0)
            
            if trend == 'degrading' and abs(change_percentage) > 10:
                insights.append({
                    'type': 'performance_degradation',
                    'operation': response_key,
                    'trend': trend,
                    'change_percentage': change_percentage,
                    'severity': 'high' if abs(change_percentage) > 50 else 'medium',
                    'recommendation': f"Investigate performance degradation in {response_key}"
                })
            elif trend == 'improving' and abs(change_percentage) > 10:
                insights.append({
                    'type': 'performance_improvement',
                    'operation': response_key,
                    'trend': trend,
                    'change_percentage': change_percentage,
                    'severity': 'info',
                    'recommendation': f"Performance improvement detected in {response_key}"
                })
        
        # Analyze bottlenecks
        for response_key, bottlenecks in self.performance_bottlenecks.items():
            if len(bottlenecks) > 5:  # Frequent bottlenecks
                recent_bottlenecks = [b for b in bottlenecks if datetime.fromisoformat(b['timestamp']) > datetime.now() - timedelta(hours=24)]
                
                if len(recent_bottlenecks) > 3:
                    insights.append({
                        'type': 'frequent_bottlenecks',
                        'operation': response_key,
                        'bottleneck_count': len(recent_bottlenecks),
                        'severity': 'high',
                        'recommendation': f"Address frequent bottlenecks in {response_key}"
                    })
        
        return insights

class LearningProgressTracker:
    """Learning progress tracking for ADK agents."""
    
    def __init__(self):
        self.learning_data: Dict[str, List[Dict]] = defaultdict(list)
        self.progress_scores: Dict[str, float] = defaultdict(float)
        self.learning_trends: Dict[str, List[float]] = defaultdict(list)
        self.improvement_areas: Dict[str, List[str]] = defaultdict(list)
        logger.info("Initialized LearningProgressTracker")
    
    def start_tracking(self, session: AgentMonitoringSession):
        """Start learning progress tracking for a session."""
        self.learning_data[session.session_id] = []
        logger.info(f"Started learning progress tracking for session: {session.session_id}")
    
    def record_progress(self, progress_data: Dict[str, Any]):
        """Record learning progress for an agent."""
        agent_name = progress_data['agent_name']
        
        # Store learning progress data
        self.learning_data[agent_name].append(progress_data)
        
        # Keep only recent data (last 500 entries)
        if len(self.learning_data[agent_name]) > 500:
            self.learning_data[agent_name] = self.learning_data[agent_name][-500:]
        
        # Update progress score
        self.progress_scores[agent_name] = progress_data.get('progress_score', 0)
        
        # Update learning trends
        self.learning_trends[agent_name].append(progress_data.get('progress_score', 0))
        
        # Keep only recent trends (last 50 entries)
        if len(self.learning_trends[agent_name]) > 50:
            self.learning_trends[agent_name] = self.learning_trends[agent_name][-50:]
        
        # Update improvement areas
        improvement_areas = progress_data.get('improvement_areas', [])
        if improvement_areas:
            self.improvement_areas[agent_name].extend(improvement_areas)
            # Keep only recent improvement areas (last 100)
            if len(self.improvement_areas[agent_name]) > 100:
                self.improvement_areas[agent_name] = self.improvement_areas[agent_name][-100:]
        
        logger.debug(f"Recorded learning progress for agent: {agent_name}")
    
    def calculate_learning_progress(self, learning_data: Dict[str, Any]) -> float:
        """Calculate learning progress score."""
        try:
            # Extract learning metrics
            current_value = learning_data.get('current_value', 0)
            previous_value = learning_data.get('previous_value', 0)
            learning_metric = learning_data.get('learning_metric', 'unknown')
            
            # Calculate improvement rate
            if previous_value > 0:
                improvement_rate = ((current_value - previous_value) / previous_value) * 100
            else:
                improvement_rate = 100 if current_value > 0 else 0
            
            # Calculate progress score based on metric type
            if learning_metric in ['accuracy', 'success_rate', 'efficiency']:
                # Higher is better
                progress_score = min(100, max(0, current_value * 100))
            elif learning_metric in ['error_rate', 'response_time', 'resource_usage']:
                # Lower is better
                progress_score = min(100, max(0, 100 - (current_value * 100)))
            else:
                # Generic improvement-based scoring
                progress_score = min(100, max(0, 50 + improvement_rate))
            
            return progress_score
            
        except Exception as e:
            logger.error(f"Error calculating learning progress: {e}")
            return 0.0
    
    def identify_improvement_areas(self, learning_data: Dict[str, Any]) -> List[str]:
        """Identify areas for improvement."""
        improvement_areas = []
        
        learning_metric = learning_data.get('learning_metric', 'unknown')
        current_value = learning_data.get('current_value', 0)
        previous_value = learning_data.get('previous_value', 0)
        
        # Analyze improvement opportunities
        if learning_metric == 'accuracy' and current_value < 0.8:
            improvement_areas.append('accuracy_improvement')
        
        if learning_metric == 'response_time' and current_value > 5.0:
            improvement_areas.append('response_time_optimization')
        
        if learning_metric == 'resource_usage' and current_value > 0.8:
            improvement_areas.append('resource_efficiency')
        
        if learning_metric == 'success_rate' and current_value < 0.9:
            improvement_areas.append('success_rate_improvement')
        
        # Check for negative trends
        if previous_value > 0 and current_value < previous_value * 0.9:
            improvement_areas.append('performance_degradation')
        
        return improvement_areas
    
    def get_learning_summary(self, agent_name: str) -> Dict[str, Any]:
        """Get learning summary for an agent."""
        if agent_name not in self.learning_data:
            return {'status': 'no_data'}
        
        data = self.learning_data[agent_name]
        if not data:
            return {'status': 'no_data'}
        
        # Calculate summary statistics
        progress_scores = [entry.get('progress_score', 0) for entry in data]
        learning_metrics = [entry.get('learning_data', {}).get('learning_metric', 'unknown') for entry in data]
        
        # Calculate learning trend
        trend = self._calculate_learning_trend(agent_name)
        
        # Get improvement areas
        improvement_areas = self._get_top_improvement_areas(agent_name)
        
        return {
            'agent_name': agent_name,
            'total_learning_entries': len(data),
            'average_progress_score': np.mean(progress_scores) if progress_scores else 0,
            'current_progress_score': progress_scores[-1] if progress_scores else 0,
            'learning_trend': trend,
            'top_learning_metrics': self._get_top_learning_metrics(learning_metrics),
            'improvement_areas': improvement_areas,
            'learning_grade': self._calculate_learning_grade(np.mean(progress_scores) if progress_scores else 0),
            'last_learning_update': data[-1].get('timestamp') if data else None
        }
    
    def _calculate_learning_trend(self, agent_name: str) -> str:
        """Calculate learning trend for an agent."""
        if agent_name not in self.learning_trends or len(self.learning_trends[agent_name]) < 5:
            return 'insufficient_data'
        
        recent_scores = self.learning_trends[agent_name][-5:]
        older_scores = self.learning_trends[agent_name][-10:-5] if len(self.learning_trends[agent_name]) >= 10 else self.learning_trends[agent_name][:-5]
        
        if not older_scores:
            return 'insufficient_data'
        
        recent_avg = np.mean(recent_scores)
        older_avg = np.mean(older_scores)
        
        if recent_avg > older_avg * 1.05:
            return 'improving'
        elif recent_avg < older_avg * 0.95:
            return 'degrading'
        else:
            return 'stable'
    
    def _get_top_learning_metrics(self, learning_metrics: List[str]) -> List[Dict]:
        """Get top learning metrics."""
        metric_counts = defaultdict(int)
        
        for metric in learning_metrics:
            metric_counts[metric] += 1
        
        # Return top 5 metrics
        top_metrics = sorted(metric_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [{'metric': metric, 'count': count} for metric, count in top_metrics]
    
    def _get_top_improvement_areas(self, agent_name: str) -> List[Dict]:
        """Get top improvement areas for an agent."""
        if agent_name not in self.improvement_areas:
            return []
        
        area_counts = defaultdict(int)
        
        for area in self.improvement_areas[agent_name]:
            area_counts[area] += 1
        
        # Return top 5 improvement areas
        top_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [{'area': area, 'frequency': count} for area, count in top_areas]
    
    def _calculate_learning_grade(self, average_progress_score: float) -> str:
        """Calculate learning grade based on progress score."""
        if average_progress_score >= 90:
            return 'A'
        elif average_progress_score >= 80:
            return 'B'
        elif average_progress_score >= 70:
            return 'C'
        elif average_progress_score >= 60:
            return 'D'
        else:
            return 'F'
    
    def get_learning_analytics(self) -> Dict[str, Any]:
        """Get comprehensive learning analytics."""
        return {
            'total_agents_learning': len(self.learning_data),
            'total_learning_entries': sum(len(data) for data in self.learning_data.values()),
            'average_progress_score': np.mean(list(self.progress_scores.values())) if self.progress_scores else 0,
            'top_learning_agents': self._get_top_learning_agents(),
            'agents_needing_improvement': self._get_agents_needing_improvement(),
            'learning_trends_summary': self._get_learning_trends_summary()
        }
    
    def _get_top_learning_agents(self) -> List[Dict]:
        """Get top learning agents."""
        agent_scores = [(agent, score) for agent, score in self.progress_scores.items()]
        top_agents = sorted(agent_scores, key=lambda x: x[1], reverse=True)[:5]
        
        return [{'agent_name': agent, 'progress_score': score} for agent, score in top_agents]
    
    def _get_agents_needing_improvement(self) -> List[Dict]:
        """Get agents that need improvement."""
        agents_needing_improvement = []
        
        for agent_name in self.learning_data:
            summary = self.get_learning_summary(agent_name)
            if summary.get('status') != 'no_data':
                progress_score = summary.get('current_progress_score', 0)
                trend = summary.get('learning_trend', 'stable')
                
                if progress_score < 70 or trend == 'degrading':
                    agents_needing_improvement.append({
                        'agent_name': agent_name,
                        'progress_score': progress_score,
                        'trend': trend,
                        'grade': summary.get('learning_grade', 'F'),
                        'improvement_areas': summary.get('improvement_areas', [])
                    })
        
        return sorted(agents_needing_improvement, key=lambda x: x['progress_score'])[:5]
    
    def _get_learning_trends_summary(self) -> Dict[str, int]:
        """Get learning trends summary."""
        trend_counts = defaultdict(int)
        
        for agent_name in self.learning_trends:
            trend = self._calculate_learning_trend(agent_name)
            if trend != 'insufficient_data':
                trend_counts[trend] += 1
        
        return dict(trend_counts)

class PerformanceOptimizer:
    """Performance optimization for ADK agents."""
    
    def __init__(self):
        self.optimization_suggestions: Dict[str, List[Dict]] = defaultdict(list)
        self.optimization_history: Dict[str, List[Dict]] = defaultdict(list)
        self.performance_baselines: Dict[str, Dict] = defaultdict(dict)
        logger.info("Initialized PerformanceOptimizer")
    
    def get_suggestions(self, metrics: Dict[str, Any]) -> List[Dict]:
        """Get performance optimization suggestions."""
        suggestions = []
        
        # Analyze execution time
        execution_time = metrics.get('execution_time', 0)
        if execution_time > 5.0:
            suggestions.append({
                'type': 'execution_time_optimization',
                'priority': 'high' if execution_time > 10.0 else 'medium',
                'description': f'Optimize execution time (current: {execution_time:.2f}s)',
                'suggestions': [
                    'Implement caching for frequent operations',
                    'Use parallel processing where possible',
                    'Optimize algorithm complexity',
                    'Reduce data transfer overhead'
                ]
            })
        
        # Analyze success rate
        success_rate = metrics.get('success_rate', 1.0)
        if success_rate < 0.8:
            suggestions.append({
                'type': 'reliability_improvement',
                'priority': 'high' if success_rate < 0.5 else 'medium',
                'description': f'Improve success rate (current: {success_rate:.1%})',
                'suggestions': [
                    'Add input validation',
                    'Improve error handling',
                    'Implement retry mechanisms',
                    'Add comprehensive logging'
                ]
            })
        
        # Analyze resource usage
        resource_usage = metrics.get('resource_usage', {})
        memory_usage = resource_usage.get('memory_mb', 0)
        if memory_usage > 500:
            suggestions.append({
                'type': 'memory_optimization',
                'priority': 'medium',
                'description': f'Optimize memory usage (current: {memory_usage:.1f}MB)',
                'suggestions': [
                    'Implement memory pooling',
                    'Use lazy loading for large datasets',
                    'Optimize data structures',
                    'Implement garbage collection tuning'
                ]
            })
        
        # Analyze throughput
        throughput = metrics.get('throughput', 0)
        if throughput < 10:
            suggestions.append({
                'type': 'throughput_improvement',
                'priority': 'medium',
                'description': f'Improve throughput (current: {throughput:.1f} ops/s)',
                'suggestions': [
                    'Implement batch processing',
                    'Use asynchronous operations',
                    'Optimize I/O operations',
                    'Implement connection pooling'
                ]
            })
        
        # Store suggestions
        if suggestions:
            suggestion_key = f"{metrics.get('agent_name', 'unknown')}:{metrics.get('operation', 'unknown')}"
            self.optimization_suggestions[suggestion_key].extend(suggestions)
            
            # Keep only recent suggestions (last 50)
            if len(self.optimization_suggestions[suggestion_key]) > 50:
                self.optimization_suggestions[suggestion_key] = self.optimization_suggestions[suggestion_key][-50:]
        
        return suggestions
    
    def record_optimization(self, agent_name: str, optimization_data: Dict[str, Any]):
        """Record optimization attempt."""
        optimization_record = {
            'timestamp': datetime.now().isoformat(),
            'agent_name': agent_name,
            'optimization_data': optimization_data,
            'success': optimization_data.get('success', False),
            'improvement_percentage': optimization_data.get('improvement_percentage', 0)
        }
        
        self.optimization_history[agent_name].append(optimization_record)
        
        # Keep only recent history (last 100 entries)
        if len(self.optimization_history[agent_name]) > 100:
            self.optimization_history[agent_name] = self.optimization_history[agent_name][-100:]
        
        logger.info(f"Recorded optimization for agent: {agent_name}")
    
    def get_optimization_summary(self, agent_name: str) -> Dict[str, Any]:
        """Get optimization summary for an agent."""
        if agent_name not in self.optimization_history:
            return {'status': 'no_data'}
        
        history = self.optimization_history[agent_name]
        if not history:
            return {'status': 'no_data'}
        
        # Calculate optimization statistics
        successful_optimizations = [opt for opt in history if opt.get('success', False)]
        total_optimizations = len(history)
        success_rate = len(successful_optimizations) / total_optimizations if total_optimizations > 0 else 0
        
        # Calculate average improvement
        improvements = [opt.get('improvement_percentage', 0) for opt in successful_optimizations]
        average_improvement = np.mean(improvements) if improvements else 0
        
        return {
            'agent_name': agent_name,
            'total_optimizations': total_optimizations,
            'successful_optimizations': len(successful_optimizations),
            'optimization_success_rate': success_rate,
            'average_improvement': average_improvement,
            'last_optimization': history[-1].get('timestamp') if history else None,
            'optimization_trend': self._calculate_optimization_trend(agent_name)
        }
    
    def _calculate_optimization_trend(self, agent_name: str) -> str:
        """Calculate optimization trend for an agent."""
        if agent_name not in self.optimization_history:
            return 'no_data'
        
        history = self.optimization_history[agent_name]
        if len(history) < 5:
            return 'insufficient_data'
        
        # Analyze recent vs older optimization success rates
        recent_history = history[-5:]
        older_history = history[-10:-5] if len(history) >= 10 else history[:-5]
        
        if not older_history:
            return 'insufficient_data'
        
        recent_success_rate = len([opt for opt in recent_history if opt.get('success', False)]) / len(recent_history)
        older_success_rate = len([opt for opt in older_history if opt.get('success', False)]) / len(older_history)
        
        if recent_success_rate > older_success_rate * 1.1:
            return 'improving'
        elif recent_success_rate < older_success_rate * 0.9:
            return 'degrading'
        else:
            return 'stable'
    
    def get_optimization_analytics(self) -> Dict[str, Any]:
        """Get comprehensive optimization analytics."""
        return {
            'total_agents_optimized': len(self.optimization_history),
            'total_optimizations': sum(len(history) for history in self.optimization_history.values()),
            'successful_optimizations': sum(len([opt for opt in history if opt.get('success', False)]) for history in self.optimization_history.values()),
            'average_improvement': np.mean([
                np.mean([opt.get('improvement_percentage', 0) for opt in history if opt.get('success', False)])
                for history in self.optimization_history.values()
            ]) if any(self.optimization_history.values()) else 0,
            'top_optimized_agents': self._get_top_optimized_agents(),
            'optimization_opportunities': self._get_optimization_opportunities()
        }
    
    def _get_top_optimized_agents(self) -> List[Dict]:
        """Get top optimized agents."""
        agent_improvements = []
        
        for agent_name, history in self.optimization_history.items():
            successful_optimizations = [opt for opt in history if opt.get('success', False)]
            if successful_optimizations:
                average_improvement = np.mean([opt.get('improvement_percentage', 0) for opt in successful_optimizations])
                agent_improvements.append({
                    'agent_name': agent_name,
                    'average_improvement': average_improvement,
                    'total_optimizations': len(history),
                    'successful_optimizations': len(successful_optimizations)
                })
        
        # Sort by average improvement
        top_agents = sorted(agent_improvements, key=lambda x: x['average_improvement'], reverse=True)[:5]
        
        return top_agents
    
    def _get_optimization_opportunities(self) -> List[Dict]:
        """Get optimization opportunities."""
        opportunities = []
        
        # Analyze suggestions to identify common optimization opportunities
        suggestion_counts = defaultdict(int)
        
        for suggestions in self.optimization_suggestions.values():
            for suggestion in suggestions:
                suggestion_type = suggestion.get('type', 'unknown')
                suggestion_counts[suggestion_type] += 1
        
        # Get top optimization opportunities
        top_opportunities = sorted(suggestion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for opportunity_type, count in top_opportunities:
            opportunities.append({
                'optimization_type': opportunity_type,
                'frequency': count,
                'priority': 'high' if count > 10 else 'medium',
                'recommendation': f"Focus on {opportunity_type.replace('_', ' ')} optimization"
            })
        
        return opportunities

class ADKAgentPerformanceMonitor:
    """Advanced ADK agent performance monitoring."""
    
    def __init__(self):
        self.efficiency_tracker = EfficiencyTracker()
        self.delegation_analytics = DelegationAnalytics()
        self.response_time_analyzer = ResponseTimeAnalyzer()
        self.learning_progress_tracker = LearningProgressTracker()
        self.performance_optimizer = PerformanceOptimizer()
        logger.info("Initialized ADKAgentPerformanceMonitor")
    
    def start_comprehensive_monitoring(self) -> AgentMonitoringSession:
        """Start comprehensive agent monitoring."""
        session = AgentMonitoringSession(
            session_id=f"comprehensive_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            session_name="comprehensive_agent_monitoring",
            start_time=datetime.now().isoformat(),
            agents_monitored=[],
            metrics_collected={}
        )
        
        # Start efficiency tracking
        self.efficiency_tracker.start_tracking(session)
        
        # Start delegation analytics
        self.delegation_analytics.start_analysis(session)
        
        # Start response time analysis
        self.response_time_analyzer.start_analysis(session)
        
        # Start learning progress tracking
        self.learning_progress_tracker.start_tracking(session)
        
        logger.info(f"Started comprehensive agent monitoring: {session.session_id}")
        return session
    
    def track_agent_efficiency(self, agent_name: str, operation: str, metrics: Dict):
        """Track agent efficiency metrics."""
        efficiency_data = {
            'agent_name': agent_name,
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'efficiency_score': self.efficiency_tracker.calculate_efficiency_score(metrics),
            'optimization_suggestions': self.performance_optimizer.get_suggestions(metrics)
        }
        
        self.efficiency_tracker.record_efficiency(efficiency_data)
        logger.debug(f"Tracked agent efficiency: {agent_name}:{operation}")
    
    def track_delegation(self, delegator_agent: str, delegatee_agent: str, delegation_data: Dict):
        """Track delegation metrics."""
        delegation_metrics = {
            'delegator_agent': delegator_agent,
            'delegatee_agent': delegatee_agent,
            'timestamp': datetime.now().isoformat(),
            'delegation_reason': delegation_data.get('reason', 'unknown'),
            'success': delegation_data.get('success', False),
            'execution_time': delegation_data.get('execution_time', 0),
            'result_quality': delegation_data.get('result_quality', 0),
            'delegation_pattern': delegation_data.get('pattern', 'unknown')
        }
        
        self.delegation_analytics.record_delegation(delegation_metrics)
        logger.debug(f"Tracked delegation: {delegator_agent} -> {delegatee_agent}")
    
    def track_response_time(self, agent_name: str, operation: str, response_time: float, context: Dict[str, Any] = None):
        """Track response time for agent operations."""
        self.response_time_analyzer.record_response_time(agent_name, operation, response_time, context)
        logger.debug(f"Tracked response time: {agent_name}:{operation} - {response_time:.3f}s")
    
    def track_learning_progress(self, agent_name: str, learning_data: Dict):
        """Track agent learning progress."""
        progress_data = {
            'agent_name': agent_name,
            'timestamp': datetime.now().isoformat(),
            'learning_data': learning_data,
            'progress_score': self.learning_progress_tracker.calculate_learning_progress(learning_data),
            'improvement_areas': self.learning_progress_tracker.identify_improvement_areas(learning_data)
        }
        
        self.learning_progress_tracker.record_progress(progress_data)
        logger.debug(f"Tracked learning progress: {agent_name}")
    
    def analyze_delegation_patterns(self) -> Dict:
        """Analyze delegation patterns and success rates."""
        return {
            'delegation_patterns': self.delegation_analytics.get_patterns(),
            'success_rates': self.delegation_analytics.get_success_rates(),
            'optimization_opportunities': self.delegation_analytics.get_optimization_opportunities(),
            'recommendations': self.delegation_analytics.get_recommendations()
        }
    
    def get_agent_performance_summary(self, agent_name: str) -> Dict[str, Any]:
        """Get comprehensive performance summary for an agent."""
        return {
            'agent_name': agent_name,
            'efficiency_summary': self.efficiency_tracker.get_efficiency_summary(agent_name),
            'response_time_summary': self.response_time_analyzer.get_response_time_summary(agent_name),
            'learning_summary': self.learning_progress_tracker.get_learning_summary(agent_name),
            'optimization_summary': self.performance_optimizer.get_optimization_summary(agent_name),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_comprehensive_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics for all agents."""
        return {
            'efficiency_analytics': self.efficiency_tracker.get_efficiency_analytics(),
            'delegation_analytics': self.analyze_delegation_patterns(),
            'response_time_analytics': self.response_time_analyzer.get_response_time_analytics(),
            'learning_analytics': self.learning_progress_tracker.get_learning_analytics(),
            'optimization_analytics': self.performance_optimizer.get_optimization_analytics(),
            'timestamp': datetime.now().isoformat()
        }

# Export classes for use in other modules
__all__ = [
    'ADKAgentPerformanceMonitor',
    'EfficiencyTracker',
    'DelegationAnalytics',
    'ResponseTimeAnalyzer',
    'LearningProgressTracker',
    'PerformanceOptimizer',
    'AgentMonitoringSession',
    'AgentEfficiencyMetrics',
    'DelegationMetrics',
    'LearningProgressMetrics'
]
