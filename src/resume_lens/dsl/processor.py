"""Stage 4 — Generation and validation of the candidate profile."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..extraction import ExtractionResult, ResumeExtractor
from ..normalization import NormalizationResult, QualificationNormalizer
from ..recognition import ClassificationResult, ProfileClassifier
from .builder import CandidateProfileBuilder
from .language import CandidateProfileLanguage
from .visualization import ProfileHtmlRenderer

CPL_EXTENSION = ".cpl"


@dataclass
class CandidateProfile:
    """A validated CPL document: its source text and its textX model."""

    text: str
    model: Any

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.text, encoding="utf-8")
        return path

    def to_html(self) -> str:
        return ProfileHtmlRenderer().render(self.model, self.text)

    def save_html(self, path: str | Path) -> Path:
        return ProfileHtmlRenderer().save(self.model, path, self.text)


class CandidateProfileProcessor:
    """Builds the CPL document of a résumé and validates it with textX."""

    def __init__(
        self,
        builder: CandidateProfileBuilder | None = None,
        language: CandidateProfileLanguage | None = None,
    ) -> None:
        self.builder = builder or CandidateProfileBuilder()
        self.language = language or CandidateProfileLanguage()

    def process(
        self,
        extraction: ExtractionResult,
        normalization: NormalizationResult,
        classification: ClassificationResult,
    ) -> CandidateProfile:
        """Stage 4 proper: outputs of Stages 1-3 -> validated profile.

        Raises ``ProfileValidationError`` if the generated document is invalid.
        """
        text = self.builder.build(extraction, normalization, classification)
        return CandidateProfile(text, self.language.parse(text))

    def process_resume(self, text: str) -> CandidateProfile:
        """Runs Stages 1, 2 and 3 on a raw résumé and then Stage 4."""
        extraction = ResumeExtractor().extract(text)
        normalization = QualificationNormalizer().normalize(extraction.qualifications)
        classification = ProfileClassifier().classify(normalization.canonical)
        return self.process(extraction, normalization, classification)
