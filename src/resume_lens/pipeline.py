"""Stages 1 and 2 chained: extraction -> normalization -> profile sorting."""

from __future__ import annotations

from dataclasses import dataclass

from .extraction import ExtractionResult, ResumeExtractor
from .normalization import NormalizationResult, QualificationNormalizer, QualificationSorter


@dataclass
class StageTwoOutput:
    extraction: ExtractionResult
    normalization: NormalizationResult
    profile: str
    sorted_qualifications: list[str]


class ResumeLensPipeline:
    def __init__(self) -> None:
        self.extractor = ResumeExtractor()
        self.normalizer = QualificationNormalizer()
        self.sorter = QualificationSorter()

    def run(self, text: str, profile: str) -> StageTwoOutput:
        extraction = self.extractor.extract(text)
        normalization = self.normalizer.normalize(extraction.qualifications)
        ordered = self.sorter.sort(normalization.canonical, profile)
        return StageTwoOutput(extraction, normalization, profile.upper(), ordered)
