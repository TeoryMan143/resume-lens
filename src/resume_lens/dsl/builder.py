"""Stage 4 — Builds a CPL document from the outputs of Stages 1, 2 and 3."""

from __future__ import annotations

from ..extraction import QUALIFICATION_CATEGORIES, Category, ExtractionResult
from ..normalization import NormalizationResult
from ..recognition import ClassificationResult

UNKNOWN_NAME = "Unknown Candidate"
INDENT = "    "


def _quote(value: str) -> str:
    """A CPL STRING literal; double quotes inside the value become single quotes."""
    return '"' + " ".join(value.replace('"', "'").split()) + '"'


class CandidateProfileBuilder:
    """Serializes the structured information of one résumé as CPL text.

    * Stage 1 (``ExtractionResult``): name, contact data, degrees, experience
      and the category and surface form of every qualification.
    * Stage 2 (``NormalizationResult``): ``mapping`` raw -> canonical token and
      the ``unrecognized`` strings.
    * Stage 3 (``ClassificationResult``): the verdict of every profile.
    """

    def build(
        self,
        extraction: ExtractionResult,
        normalization: NormalizationResult,
        classification: ClassificationResult,
    ) -> str:
        lines = [f"candidate {_quote(extraction.name or UNKNOWN_NAME)} {{"]
        lines += self._contact(extraction)
        lines += self._education(extraction)
        lines += self._experience(extraction)
        lines += self._skills(extraction, normalization)
        lines += self._classification(classification)
        lines.append("}")
        return "\n".join(lines) + "\n"

    # -- sections ------------------------------------------------------------
    def _contact(self, extraction: ExtractionResult) -> list[str]:
        entries = (
            [f"email {_quote(e)}" for e in extraction.emails]
            + [f"phone {_quote(p)}" for p in extraction.phones]
            + [f"link {_quote(l)}" for l in extraction.links]
        )
        return self._section("contact", entries)

    def _education(self, extraction: ExtractionResult) -> list[str]:
        return self._section("education", [f"degree {_quote(d)}" for d in extraction.degrees])

    def _experience(self, extraction: ExtractionResult) -> list[str]:
        entries = []
        for exp in extraction.experience:
            entry = f"{exp.years} {'year' if exp.years == 1 else 'years'}"
            if exp.description:
                entry += f" {_quote(exp.description)}"
            entries.append(entry)
        return self._section("experience", entries)

    def _skills(
        self, extraction: ExtractionResult, normalization: NormalizationResult
    ) -> list[str]:
        # canonical token -> (Stage 1 category, surface forms), first-seen order
        skills: dict[str, tuple[Category, list[str]]] = {}
        for item in sorted(extraction.items, key=lambda i: i.start):
            if item.category not in QUALIFICATION_CATEGORIES:
                continue
            token = normalization.mapping.get(item.value)
            if token is None:
                continue
            _, aliases = skills.setdefault(token, (item.category, []))
            if item.value not in aliases:
                aliases.append(item.value)

        entries = []
        for category in QUALIFICATION_CATEGORIES:
            group = [
                f"{token} ({', '.join(_quote(a) for a in aliases)})"
                for token, (cat, aliases) in skills.items()
                if cat == category
            ]
            if group:
                entries.append(f"{category.value}: {', '.join(group)};")
        if normalization.unrecognized:
            values = ", ".join(_quote(u) for u in normalization.unrecognized)
            entries.append(f"unrecognized: {values};")
        return self._section("skills", entries, required=True)

    def _classification(self, classification: ClassificationResult) -> list[str]:
        entries = []
        for name, verdict in classification.verdicts.items():
            if verdict.accepted:
                entries.append(f"{name}: ACCEPTED via {', '.join(verdict.sequence)};")
            elif verdict.missing_stage:
                entries.append(f"{name}: REJECTED missing {verdict.missing_stage};")
            else:
                entries.append(f"{name}: REJECTED;")
        return self._section("classification", entries, required=True)

    @staticmethod
    def _section(keyword: str, entries: list[str], required: bool = False) -> list[str]:
        if not entries and not required:
            return []
        body = [f"{INDENT * 2}{e}" for e in entries]
        return [f"{INDENT}{keyword} {{", *body, f"{INDENT}}}"]
