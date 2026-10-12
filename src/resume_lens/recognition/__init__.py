"""Stage 3 — Qualification pattern recognition (finite automata)."""

from .automaton import AutomatonDefinition, ProfileAutomaton, Trace
from .classifier import (
    ACCEPTED,
    REJECTED,
    ClassificationResult,
    ProfileClassifier,
    ProfileVerdict,
)
from .patterns import (
    DATA_ENGINEER_PATTERN,
    DEVOPS_PATTERN,
    FULL_STACK_PATTERN,
    MACHINE_LEARNING_PATTERN,
    NAMED_SETS,
    PATTERNS,
    PatternStage,
    ProfilePattern,
    get_pattern,
)

__all__ = [
    "ACCEPTED",
    "AutomatonDefinition",
    "ClassificationResult",
    "DATA_ENGINEER_PATTERN",
    "DEVOPS_PATTERN",
    "FULL_STACK_PATTERN",
    "MACHINE_LEARNING_PATTERN",
    "NAMED_SETS",
    "PATTERNS",
    "PatternStage",
    "ProfileAutomaton",
    "ProfileClassifier",
    "ProfilePattern",
    "ProfileVerdict",
    "REJECTED",
    "Trace",
    "get_pattern",
]
