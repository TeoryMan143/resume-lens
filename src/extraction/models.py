"""Data structures that keep the information extracted in Stage 1."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .patterns import QUALIFICATION_CATEGORIES, Category


@dataclass(frozen=True)
class ExtractedItem:
    """A string found in the résumé, its category and its position."""

    value: str
    category: Category
    start: int
    end: int


@dataclass(frozen=True)
class Experience:
    """A 'N years of experience ...' statement."""

    years: int
    description: str


@dataclass
class ExtractionResult:
    """Everything Stage 1 found in one résumé."""

    name: str | None = None
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    experience: list[Experience] = field(default_factory=list)
    degrees: list[str] = field(default_factory=list)
    items: list[ExtractedItem] = field(default_factory=list)

    # -- queries -------------------------------------------------------------
    def by_category(self, category: Category) -> list[str]:
        """Distinct values of a category, in order of appearance."""
        seen: dict[str, None] = {}
        for item in self.items:
            if item.category == category:
                seen.setdefault(item.value, None)
        return list(seen)

    @property
    def programming_languages(self) -> list[str]:
        return self.by_category(Category.PROGRAMMING_LANGUAGE)

    @property
    def frameworks(self) -> list[str]:
        return self.by_category(Category.FRAMEWORK_LIBRARY)

    @property
    def databases(self) -> list[str]:
        return self.by_category(Category.DATABASE)

    @property
    def tools(self) -> list[str]:
        return self.by_category(Category.TOOL)

    @property
    def other_qualifications(self) -> list[str]:
        return self.by_category(Category.OTHER_QUALIFICATION)

    @property
    def qualifications(self) -> list[str]:
        """Distinct qualification strings in order of appearance.

        This list is the input of Stage 2 (normalization).
        """
        seen: dict[str, None] = {}
        for item in sorted(self.items, key=lambda i: i.start):
            if item.category in QUALIFICATION_CATEGORIES:
                seen.setdefault(item.value, None)
        return list(seen)

    # -- persistence ---------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "emails": list(self.emails),
            "phones": list(self.phones),
            "links": list(self.links),
            "experience": [asdict(e) for e in self.experience],
            "degrees": list(self.degrees),
            "items": [
                {"value": i.value, "category": i.category.value, "start": i.start, "end": i.end}
                for i in self.items
            ],
            "qualifications": self.qualifications,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExtractionResult":
        return cls(
            name=data.get("name"),
            emails=list(data.get("emails", [])),
            phones=list(data.get("phones", [])),
            links=list(data.get("links", [])),
            experience=[Experience(**e) for e in data.get("experience", [])],
            degrees=list(data.get("degrees", [])),
            items=[
                ExtractedItem(i["value"], Category(i["category"]), i["start"], i["end"])
                for i in data.get("items", [])
            ],
        )

    def save_json(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    @classmethod
    def load_json(cls, path: str | Path) -> "ExtractionResult":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
