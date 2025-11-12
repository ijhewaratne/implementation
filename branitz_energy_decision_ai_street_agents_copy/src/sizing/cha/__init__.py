"""
CHA-inspired pipe sizing toolkit.

This package provides a trimmed-down version of the City Heat Analytics
pipe-sizing utilities so the agent system can reuse the same
flow-calculation, sizing, and standards-compliance logic.
"""

from .cha_flow_calculation import (
    CHAFlowCalculationEngine,
    FlowCalculationResult,
    NetworkFlowResult,
)
from .cha_network_hierarchy import (
    CHANetworkHierarchyManager,
    NetworkPipeDescription,
)
from .cha_pipe_sizing import (
    CHAPipeSizingEngine,
    PipeSizingResult,
)
from .cha_standards_compliance import (
    CHAStandardsComplianceEngine,
    ComplianceResult,
    StandardsViolation,
)
from .cha_intelligent_sizing import CHAIntelligentSizing

__all__ = [
    "CHAFlowCalculationEngine",
    "FlowCalculationResult",
    "NetworkFlowResult",
    "CHANetworkHierarchyManager",
    "NetworkPipeDescription",
    "CHAPipeSizingEngine",
    "PipeSizingResult",
    "CHAStandardsComplianceEngine",
    "ComplianceResult",
    "StandardsViolation",
    "CHAIntelligentSizing",
]

