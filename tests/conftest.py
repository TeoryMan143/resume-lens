"""Scenario configuration (see docs/test-design-stages-1-2.md and
docs/test-design-stage-4.md, section 1).

Each fixture corresponds to one row of the scenario table.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from resume_lens.dsl import CandidateProfileLanguage, CandidateProfileProcessor
from resume_lens.extraction import ResumeExtractor
from resume_lens.normalization import (
    CleaningTransducer,
    QualificationNormalizer,
    QualificationSorter,
    QualificationTransducer,
)
from resume_lens.pipeline import ResumeLensPipeline
from resume_lens.recognition import (
    PATTERNS,
    ClassificationResult,
    ProfileAutomaton,
    ProfileClassifier,
)

RESOURCES = Path(__file__).parent / "resources"


# --------------------------------------------------------------------------- #
# Stage 1 scenarios
# --------------------------------------------------------------------------- #
@pytest.fixture
def extractor() -> ResumeExtractor:
    """SC-E1 — extractor with the default pattern set."""
    return ResumeExtractor()


@pytest.fixture
def wednesday_text() -> str:
    """SC-E2 — Full Stack résumé fragment from the project statement."""
    return (RESOURCES / "wednesday_addams.txt").read_text(encoding="utf-8")


@pytest.fixture
def mary_jane_text() -> str:
    """SC-E3 — Machine Learning résumé fragment from the project statement."""
    return (RESOURCES / "mary_jane_watson.txt").read_text(encoding="utf-8")


@pytest.fixture
def full_resume_text() -> str:
    """SC-E4 — résumé with contact data, links, education and many skills."""
    return (RESOURCES / "full_resume.txt").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Stage 2 scenarios
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def cleaner() -> CleaningTransducer:
    """SC-N1 — lexical cleaning transducer T_clean."""
    return CleaningTransducer()


@pytest.fixture(scope="session")
def react_transducer() -> QualificationTransducer:
    """SC-N2 — T_REACT built from {React, React.js, ReactJS}."""
    return QualificationTransducer("REACT", ["React", "React.js", "ReactJS"])


@pytest.fixture(scope="session")
def scikit_transducer() -> QualificationTransducer:
    """SC-N3 — T_SCIKIT_LEARN built from four spellings (two collapse after cleaning)."""
    return QualificationTransducer(
        "SCIKIT_LEARN", ["Scikit-learn", "scikit learn", "scikitlearn", "sklearn"]
    )


@pytest.fixture(scope="session")
def normalizer() -> QualificationNormalizer:
    """SC-N4 — normalizer with the complete catalogue (T_clean ; ∪ T_i)."""
    return QualificationNormalizer()


@pytest.fixture
def sorter() -> QualificationSorter:
    """SC-N5 — sorter with the FULL_STACK_DEVELOPER / MACHINE_LEARNING_ENGINEER orders."""
    return QualificationSorter()


@pytest.fixture(scope="session")
def pipeline() -> ResumeLensPipeline:
    """SC-I1 — Stage 1 + Stage 2 chained."""
    return ResumeLensPipeline()


# --------------------------------------------------------------------------- #
# Stage 3 scenarios
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="session")
def classifier() -> ProfileClassifier:
    """SC-R1 — classifier with the four profile automata."""
    return ProfileClassifier()


@pytest.fixture(scope="session")
def automata() -> dict[str, ProfileAutomaton]:
    """SC-R2 — one DFA per profile, built from the declarative patterns."""
    return {name: ProfileAutomaton(pattern) for name, pattern in PATTERNS.items()}


@pytest.fixture(scope="session")
def classify(pipeline, classifier) -> Callable[[str], ClassificationResult]:
    """SC-R3 — résumé text through Stage 1, Stage 2 and the Stage 3 classifier."""

    def _classify(text: str) -> ClassificationResult:
        tokens = pipeline.run(text, "FULL_STACK_DEVELOPER").normalization.canonical
        return classifier.classify(tokens)

    return _classify


# --------------------------------------------------------------------------- #
# Stage 4 scenarios
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def language() -> CandidateProfileLanguage:
    """SC-G1 — textX metamodel of the Candidate Profile Language + semantic checks."""
    return CandidateProfileLanguage()


@pytest.fixture(scope="session")
def profile_processor(language) -> CandidateProfileProcessor:
    """SC-G2 — builder + language: outputs of Stages 1-3 -> validated profile."""
    return CandidateProfileProcessor(language=language)


@pytest.fixture
def valid_cpl_text() -> str:
    """SC-G3 — hand-written profile that uses every construct of the language."""
    return (RESOURCES / "valid_profile.cpl").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def stage_outputs(pipeline, classifier):
    """SC-G4 — résumé text -> (ExtractionResult, NormalizationResult, ClassificationResult)."""

    def _run(text: str):
        out = pipeline.run(text, "FULL_STACK_DEVELOPER")
        return (
            out.extraction,
            out.normalization,
            classifier.classify(out.normalization.canonical),
        )

    return _run
