"""Stage 1 — Résumé information extraction with Python's ``re`` module."""

from __future__ import annotations

from pathlib import Path

from .models import Experience, ExtractedItem, ExtractionResult
from .patterns import PATTERNS, QUALIFICATION_CATEGORIES, Category, RegexPattern


class ResumeExtractor:
    """Applies the Stage 1 regular expressions to a résumé text."""

    def __init__(self, patterns: dict[Category, RegexPattern] | None = None) -> None:
        self.patterns = dict(PATTERNS if patterns is None else patterns)

    # -- single-category helpers --------------------------------------------
    def extract_name(self, text: str) -> str | None:
        match = self.patterns[Category.NAME].compiled.search(text)
        return match.group("name") if match else None

    def extract_emails(self, text: str) -> list[str]:
        return self._distinct(Category.EMAIL, text)

    def extract_phones(self, text: str) -> list[str]:
        return self._distinct(Category.PHONE, text)

    def extract_links(self, text: str) -> list[str]:
        return self._distinct(Category.LINK, text)

    def extract_degrees(self, text: str) -> list[str]:
        return [d.strip() for d in self._distinct(Category.DEGREE, text)]

    def extract_experience(self, text: str) -> list[Experience]:
        result = []
        for m in self.patterns[Category.EXPERIENCE].find_all(text):
            description = (m.group("field") or "").strip()
            result.append(Experience(int(m.group("years")), description))
        return result

    def extract_qualifications(self, text: str) -> list[ExtractedItem]:
        """All qualification occurrences (every category), sorted by position."""
        items: list[ExtractedItem] = []
        for category in QUALIFICATION_CATEGORIES:
            for m in self.patterns[category].find_all(text):
                items.append(ExtractedItem(m.group(0), category, m.start(), m.end()))
        return sorted(items, key=lambda i: (i.start, i.end))

    # -- full extraction -----------------------------------------------------
    def extract(self, text: str) -> ExtractionResult:
        if text is None:
            raise ValueError("The résumé text cannot be None")
        return ExtractionResult(
            name=self.extract_name(text),
            emails=self.extract_emails(text),
            phones=self.extract_phones(text),
            links=self.extract_links(text),
            experience=self.extract_experience(text),
            degrees=self.extract_degrees(text),
            items=self.extract_qualifications(text),
        )

    def extract_file(self, path: str | Path) -> ExtractionResult:
        return self.extract(Path(path).read_text(encoding="utf-8"))

    # -- internals -----------------------------------------------------------
    def _distinct(self, category: Category, text: str) -> list[str]:
        seen: dict[str, None] = {}
        for m in self.patterns[category].find_all(text):
            seen.setdefault(m.group(0), None)
        return list(seen)
