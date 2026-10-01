"""Stage 2 — Qualification normalization (finite-state transducers)."""

from .catalog import CANONICAL_VARIANTS
from .normalizer import NormalizationResult, QualificationNormalizer
from .profiles import (
    FULL_STACK_DEVELOPER,
    MACHINE_LEARNING_ENGINEER,
    PROFILES,
    ProfileOrder,
    get_profile,
)
from .sorter import QualificationSorter
from .transducers import CleaningTransducer, FormalDefinition, QualificationTransducer

__all__ = [
    "CANONICAL_VARIANTS",
    "CleaningTransducer",
    "FULL_STACK_DEVELOPER",
    "FormalDefinition",
    "MACHINE_LEARNING_ENGINEER",
    "NormalizationResult",
    "PROFILES",
    "ProfileOrder",
    "QualificationNormalizer",
    "QualificationSorter",
    "QualificationTransducer",
    "get_profile",
]
