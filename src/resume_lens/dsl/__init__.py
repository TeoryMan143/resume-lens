"""Stage 4 — Candidate Profile Language (context-free grammar with textX)."""

from .builder import CandidateProfileBuilder
from .language import GRAMMAR_PATH, CandidateProfileLanguage, ProfileValidationError
from .processor import CPL_EXTENSION, CandidateProfile, CandidateProfileProcessor
from .visualization import ProfileHtmlRenderer, profile_label

__all__ = [
    "ProfileHtmlRenderer",
    "profile_label",
    "CPL_EXTENSION",
    "CandidateProfile",
    "CandidateProfileBuilder",
    "CandidateProfileLanguage",
    "CandidateProfileProcessor",
    "GRAMMAR_PATH",
    "ProfileValidationError",
]
