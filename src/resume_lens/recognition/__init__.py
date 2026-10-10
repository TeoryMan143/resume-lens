"""Stage 3 — Qualification pattern recognition (finite automata)."""

from .automata import AutomatonDefinition, ProfileAutomaton, Trace, set_label
from .classifier import (
    ACCEPTED,
    REJECTED,
    ClassificationResult,
    ProfileClassifier,
    ProfileVerdict,
)
from .models import PatternStage, ProfilePattern
from .patterns import (
    DATA_ENGINEER_PATTERN,
    DEVOPS_PATTERN,
    FULL_STACK_PATTERN,
    MACHINE_LEARNING_PATTERN,
    NAMED_SETS,
    PATTERNS,
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
    "set_label",
]
