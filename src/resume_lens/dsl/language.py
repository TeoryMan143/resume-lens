"""Stage 4 — textX implementation of the Candidate Profile Language (CPL).

Validation happens in two layers:

1. Lexical/syntactic: textX parses the document with the context-free grammar
   in ``candidate_profile.tx``; any violation raises ``TextXSyntaxError``.
2. Semantic: object processors check the rules a CFG cannot express (known
   canonical tokens, unique entries, verdicts consistent with the Stage 3
   patterns); violations raise ``TextXSemanticError``.

Both are reported to callers as ``ProfileValidationError``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Mapping

from textx import TextXError, TextXSemanticError, get_location, metamodel_from_file

from ..normalization import CANONICAL_VARIANTS
from ..recognition import PATTERNS, ProfilePattern

GRAMMAR_PATH = Path(__file__).with_name("candidate_profile.tx")

MAX_YEARS = 60
MIN_PHONE_DIGITS, MAX_PHONE_DIGITS = 7, 15


class ProfileValidationError(ValueError):
    """A CPL document violates the lexical, syntactic or semantic rules."""

    def __init__(self, message: str, line: int | None = None, col: int | None = None) -> None:
        self.line, self.col = line, col
        where = f" (line {line}, col {col})" if line is not None else ""
        super().__init__(f"{message}{where}")


def _unquote(value: str) -> str:
    return value[1:-1]


def _error(message: str, obj) -> TextXSemanticError:
    return TextXSemanticError(message, **get_location(obj))


class CandidateProfileLanguage:
    """Parses and validates CPL documents."""

    def __init__(
        self,
        canonical_tokens: Iterable[str] | None = None,
        patterns: Mapping[str, ProfilePattern] | None = None,
    ) -> None:
        self.canonical_tokens = set(CANONICAL_VARIANTS if canonical_tokens is None else canonical_tokens)
        self.patterns = dict(PATTERNS if patterns is None else patterns)
        self.metamodel = metamodel_from_file(str(GRAMMAR_PATH), autokwd=True)
        self.metamodel.register_obj_processors(
            {
                "PersonName": _unquote,
                "EmailAddress": _unquote,
                "PhoneNumber": _unquote,
                "Url": _unquote,
                "PhoneEntry": self._check_phone,
                "ExperienceEntry": self._check_experience,
                "CandidateProfile": self._check_profile,
            }
        )

    # -- public API ----------------------------------------------------------
    def parse(self, text: str):
        """Return the model of a valid CPL document or raise ``ProfileValidationError``."""
        try:
            return self.metamodel.model_from_str(text)
        except TextXError as e:
            raise ProfileValidationError(e.message, e.line, e.col) from e

    def parse_file(self, path: str | Path):
        return self.parse(Path(path).read_text(encoding="utf-8"))

    def is_valid(self, text: str) -> bool:
        try:
            self.parse(text)
        except ProfileValidationError:
            return False
        return True

    # -- semantic checks -----------------------------------------------------
    @staticmethod
    def _check_phone(entry) -> None:
        digits = len(re.sub(r"\D", "", entry.value))
        if not MIN_PHONE_DIGITS <= digits <= MAX_PHONE_DIGITS:
            raise _error(
                f"Phone {entry.value!r} must have {MIN_PHONE_DIGITS}-{MAX_PHONE_DIGITS} digits",
                entry,
            )

    @staticmethod
    def _check_experience(entry) -> None:
        if not 0 < entry.years <= MAX_YEARS:
            raise _error(f"Years of experience must be in 1..{MAX_YEARS}, got {entry.years}", entry)

    def _check_profile(self, profile) -> None:
        skills = self._check_skills(profile.skills)
        self._check_classification(profile.classification, skills)

    def _check_skills(self, section) -> set[str]:
        declared: set[str] = set()
        for group in section.groups:
            for skill in group.skills:
                if skill.token not in self.canonical_tokens:
                    raise _error(f"Unknown canonical qualification {skill.token!r}", skill)
                if skill.token in declared:
                    raise _error(f"Qualification {skill.token!r} is declared twice", skill)
                declared.add(skill.token)
        return declared

    def _check_classification(self, section, skills: set[str]) -> None:
        seen: set[str] = set()
        for verdict in section.verdicts:
            pattern = self.patterns.get(verdict.profile)
            if pattern is None:
                raise _error(
                    f"Unknown profile {verdict.profile!r}. "
                    f"Available: {', '.join(self.patterns)}",
                    verdict,
                )
            if verdict.profile in seen:
                raise _error(f"Profile {verdict.profile!r} is classified twice", verdict)
            seen.add(verdict.profile)

            if verdict.status == "ACCEPTED":
                self._check_accepted(verdict, pattern, skills)
            else:
                self._check_rejected(verdict, pattern, skills)

    @staticmethod
    def _check_accepted(verdict, pattern: ProfilePattern, skills: set[str]) -> None:
        alphabet = set(pattern.tokens)
        for token in verdict.sequence:
            if token not in skills:
                raise _error(f"{verdict.profile}: {token!r} is not a declared skill", verdict)
            if token not in alphabet:
                raise _error(
                    f"{verdict.profile}: {token!r} is not in the profile alphabet", verdict
                )
        if not pattern.is_satisfied_by(verdict.sequence):
            raise _error(
                f"{verdict.profile}: the sequence does not satisfy the profile pattern", verdict
            )

    @staticmethod
    def _check_rejected(verdict, pattern: ProfilePattern, skills: set[str]) -> None:
        if pattern.is_satisfied_by(skills):
            raise _error(
                f"{verdict.profile}: declared REJECTED but the skills satisfy the pattern",
                verdict,
            )
        stages = [stage.name for stage in pattern.stages]
        if verdict.missing and verdict.missing not in stages:
            raise _error(
                f"{verdict.profile}: unknown stage {verdict.missing!r}. "
                f"Available: {', '.join(stages)}",
                verdict,
            )
