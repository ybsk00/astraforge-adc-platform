"""
Rule Engine Module

ADC 후보 물질 평가를 위한 룰 엔진
"""

from .models import (
    ActionType,
    Severity,
    RuleCondition,
    RuleAction,
    Rule,
    RuleResult,
    EvaluationResult,
    CandidateFeatures,
    RuleSet,
)
from .evaluator import (
    SafeExpressionEvaluator,
    EvaluatorError,
    get_evaluator,
)
from .rule_engine import (
    RuleEngine,
    get_rule_engine,
)
from .loader import (
    RuleLoader,
    RuleLoadError,
    RuleSchemaError,
    get_loader,
)

__all__ = [
    # Enums
    "ActionType",
    "Severity",
    # Models
    "RuleCondition",
    "RuleAction",
    "Rule",
    "RuleResult",
    "EvaluationResult",
    "CandidateFeatures",
    "RuleSet",
    # Evaluator
    "SafeExpressionEvaluator",
    "EvaluatorError",
    "get_evaluator",
    # Rule Engine
    "RuleEngine",
    "get_rule_engine",
    # Loader
    "RuleLoader",
    "RuleLoadError",
    "RuleSchemaError",
    "get_loader",
]
