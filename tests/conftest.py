"""Scenario configuration (see docs/test-design-stages-1-2.md, section 1).

Each fixture corresponds to one row of the scenario table.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_lens.extraction import ResumeExtractor
from resume_lens.normalization import (
    CleaningTransducer,
    QualificationNormalizer,
    QualificationSorter,
    QualificationTransducer,
)
from resume_lens.pipeline import ResumeLensPipeline

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
