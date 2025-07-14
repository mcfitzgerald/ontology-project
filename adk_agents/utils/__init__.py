"""
Utility modules for ADK agents.
"""
from .owlready2_adapter import (
    adapt_sparql_for_owlready2,
    format_owlready2_results,
    Owlready2Adapter
)
from .financial_calc import (
    FinancialCalculator,
    calculate_oee_opportunity,
    estimate_micro_stop_impact
)

# Cost monitoring utilities
try:
    from .vertex_ai_monitor import (
        TokenCounter,
        SafeVertexAIClient,
        ModelPricing,
        UsageStats,
        VERTEX_AI_PRICING
    )
    VERTEX_AI_MONITOR_AVAILABLE = True
except ImportError:
    VERTEX_AI_MONITOR_AVAILABLE = False
    TokenCounter = None
    SafeVertexAIClient = None
    ModelPricing = None
    UsageStats = None
    VERTEX_AI_PRICING = None

__all__ = [
    'adapt_sparql_for_owlready2',
    'format_owlready2_results',
    'Owlready2Adapter',
    'FinancialCalculator',
    'calculate_oee_opportunity',
    'estimate_micro_stop_impact',
    'TokenCounter',
    'SafeVertexAIClient',
    'ModelPricing',
    'UsageStats',
    'VERTEX_AI_PRICING',
    'VERTEX_AI_MONITOR_AVAILABLE'
]