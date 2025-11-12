"""
Cost tracking and calculation utilities for the DH project.
"""

import time
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta
import logging

from .config import Config
from .data_adapters import DataAdapter


class CostEntry:
    """Represents a single cost entry."""
    
    def __init__(self, operation: str, cost: float, currency: str = "USD",
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize cost entry.
        
        Args:
            operation: Description of the operation
            cost: Cost amount
            currency: Currency code
            metadata: Additional metadata
        """
        self.timestamp = datetime.now()
        self.operation = operation
        self.cost = cost
        self.currency = currency
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "cost": self.cost,
            "currency": self.currency,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostEntry':
        """Create CostEntry from dictionary."""
        entry = cls(
            operation=data["operation"],
            cost=data["cost"],
            currency=data.get("currency", "USD"),
            metadata=data.get("metadata", {})
        )
        entry.timestamp = datetime.fromisoformat(data["timestamp"])
        return entry


class CostCalculator:
    """Cost calculator and tracker for computational operations."""
    
    def __init__(self, config: Config):
        """Initialize cost calculator.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.data_adapter = DataAdapter(config)
        self.logger = logging.getLogger(__name__)
        
        # Cost tracking settings
        self.track_costs = config.get("costs.track_costs", True)
        self.currency = config.get("costs.currency", "USD")
        self.cost_per_token = config.get("costs.cost_per_token", 0.0001)
        
        # In-memory cost tracking
        self.cost_history: List[CostEntry] = []
        self.current_session_costs: Dict[str, float] = {}
    
    def calculate_api_cost(self, tokens_used: int, model: str = "gpt-3.5-turbo") -> float:
        """Calculate cost for API token usage.
        
        Args:
            tokens_used: Number of tokens used
            model: Model name (for different pricing)
            
        Returns:
            Calculated cost
        """
        # Simple pricing model - in reality you'd have different rates per model
        pricing = {
            "gpt-3.5-turbo": 0.0001,
            "gpt-4": 0.0003,
            "gpt-4-turbo": 0.0002,
            "claude-3": 0.00015
        }
        
        rate = pricing.get(model, self.cost_per_token)
        return tokens_used * rate
    
    def calculate_compute_cost(self, duration_seconds: float, 
                             cpu_hours_rate: float = 0.01) -> float:
        """Calculate cost for computational resources.
        
        Args:
            duration_seconds: Duration of computation in seconds
            cpu_hours_rate: Cost per CPU hour
            
        Returns:
            Calculated cost
        """
        cpu_hours = duration_seconds / 3600
        return cpu_hours * cpu_hours_rate
    
    def calculate_storage_cost(self, size_bytes: int, 
                             storage_rate_per_gb_month: float = 0.023) -> float:
        """Calculate storage cost.
        
        Args:
            size_bytes: Size in bytes
            storage_rate_per_gb_month: Cost per GB per month
            
        Returns:
            Calculated cost
        """
        size_gb = size_bytes / (1024 ** 3)
        return size_gb * storage_rate_per_gb_month
    
    def add_cost(self, operation: str, cost: float, 
                metadata: Optional[Dict[str, Any]] = None):
        """Add a cost entry.
        
        Args:
            operation: Description of the operation
            cost: Cost amount
            metadata: Additional metadata
        """
        if not self.track_costs:
            return
        
        entry = CostEntry(operation, cost, self.currency, metadata)
        self.cost_history.append(entry)
        
        # Update session costs
        if operation not in self.current_session_costs:
            self.current_session_costs[operation] = 0
        self.current_session_costs[operation] += cost
        
        self.logger.info(f"Added cost: {operation} - ${cost:.4f} {self.currency}")
    
    def track_api_call(self, tokens_used: int, model: str = "gpt-3.5-turbo",
                      operation: Optional[str] = None):
        """Track API call costs.
        
        Args:
            tokens_used: Number of tokens used
            model: Model name
            operation: Operation description
        """
        cost = self.calculate_api_cost(tokens_used, model)
        op_name = operation or f"API call ({model})"
        metadata = {
            "tokens_used": tokens_used,
            "model": model,
            "cost_per_token": self.calculate_api_cost(1, model)
        }
        self.add_cost(op_name, cost, metadata)
    
    def track_computation(self, duration_seconds: float, operation: str,
                         cpu_hours_rate: Optional[float] = None):
        """Track computation costs.
        
        Args:
            duration_seconds: Duration in seconds
            operation: Operation description
            cpu_hours_rate: Optional custom rate
        """
        rate = cpu_hours_rate if cpu_hours_rate is not None else 0.01
        cost = self.calculate_compute_cost(duration_seconds, rate)
        metadata = {
            "duration_seconds": duration_seconds,
            "cpu_hours": duration_seconds / 3600,
            "rate_per_cpu_hour": cpu_hours_rate or 0.01
        }
        self.add_cost(operation, cost, metadata)
    
    def track_storage(self, size_bytes: int, operation: str,
                     storage_rate: Optional[float] = None):
        """Track storage costs.
        
        Args:
            size_bytes: Size in bytes
            operation: Operation description
            storage_rate: Optional custom rate
        """
        rate = storage_rate if storage_rate is not None else 0.023
        cost = self.calculate_storage_cost(size_bytes, rate)
        metadata = {
            "size_bytes": size_bytes,
            "size_gb": size_bytes / (1024 ** 3),
            "rate_per_gb_month": storage_rate or 0.023
        }
        self.add_cost(operation, cost, metadata)
    
    def get_total_cost(self, operation_filter: Optional[str] = None) -> float:
        """Get total cost for all operations or filtered operations.
        
        Args:
            operation_filter: Optional operation name filter
            
        Returns:
            Total cost
        """
        if operation_filter:
            costs = [entry.cost for entry in self.cost_history 
                    if operation_filter in entry.operation]
        else:
            costs = [entry.cost for entry in self.cost_history]
        
        return sum(costs)
    
    def get_session_costs(self) -> Dict[str, float]:
        """Get costs for current session.
        
        Returns:
            Dictionary of operation costs
        """
        return self.current_session_costs.copy()
    
    def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get cost summary for specified period.
        
        Args:
            days: Number of days to include
            
        Returns:
            Cost summary dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_costs = [entry for entry in self.cost_history 
                       if entry.timestamp >= cutoff_date]
        
        total_cost = sum(entry.cost for entry in recent_costs)
        
        # Group by operation
        operation_costs = {}
        for entry in recent_costs:
            if entry.operation not in operation_costs:
                operation_costs[entry.operation] = 0
            operation_costs[entry.operation] += entry.cost
        
        return {
            "period_days": days,
            "total_cost": total_cost,
            "currency": self.currency,
            "entry_count": len(recent_costs),
            "operation_breakdown": operation_costs,
            "average_daily_cost": total_cost / days if days > 0 else 0
        }
    
    def save_cost_report(self, filename: Optional[str] = None) -> Path:
        """Save cost history to file.
        
        Args:
            filename: Optional filename
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cost_report_{timestamp}"
        
        report_data = {
            "summary": self.get_cost_summary(),
            "cost_history": [entry.to_dict() for entry in self.cost_history],
            "session_costs": self.current_session_costs,
            "generated_at": datetime.now().isoformat()
        }
        
        return self.data_adapter.save_json(report_data, f"{filename}.json")
    
    def load_cost_history(self, filename: str):
        """Load cost history from file.
        
        Args:
            filename: Cost report filename (without extension)
        """
        try:
            report_data = self.data_adapter.load_json(f"{filename}.json")
            self.cost_history = [
                CostEntry.from_dict(entry) for entry in report_data.get("cost_history", [])
            ]
            self.logger.info(f"Loaded cost history from {filename}")
        except FileNotFoundError:
            self.logger.warning(f"Cost report {filename} not found")
    
    def reset_session(self):
        """Reset current session costs."""
        self.current_session_costs.clear()
        self.logger.info("Reset session costs")
    
    def clear_history(self):
        """Clear all cost history."""
        self.cost_history.clear()
        self.reset_session()
        self.logger.info("Cleared all cost history")
