"""Stage 3 — Classification of a résumé among the four profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from ..normalization import PROFILES, ProfileOrder, QualificationSorter
from .patterns import PATTERNS, ProfilePattern

ACCEPTED = "ACCEPTED"
REJECTED = "REJECTED"
from .automaton import ProfileAutomaton

@dataclass(frozen=True)
class ProfileVerdict:
    """Result of running one profile automaton over a résumé."""

    profile: str
    accepted: bool
    sequence: tuple[str, ...]  # sorted sequence projected onto Σ of the profile
    missing_stage: str | None = None  # first unsatisfied stage when rejected

    @property
    def status(self) -> str:
        return ACCEPTED if self.accepted else REJECTED


@dataclass
class ClassificationResult:
    """Verdicts for every profile."""

    verdicts: dict[str, ProfileVerdict] = field(default_factory=dict)

    @property
    def accepted_profiles(self) -> list[str]:
        return [name for name, verdict in self.verdicts.items() if verdict.accepted]

    def status(self, profile: str) -> str:
        return self.verdicts[profile.strip().upper()].status

    def to_dict(self) -> dict:
        return {
            name: {
                "status": v.status,
                "sequence": list(v.sequence),
                "missing_stage": v.missing_stage,
            }
            for name, v in self.verdicts.items()
        }


class ProfileClassifier:
    """Runs the normalized qualifications through the automaton of each profile.

    For every profile the classifier

    1. sorts the canonical tokens in the profile's canonical order (Stage 2),
    2. projects the sequence onto the profile alphabet Σ, erasing tokens that
       the profile does not mention (they are neither required nor penalised),
    3. runs the profile's DFA.
    """

    def __init__(
        self,
        patterns: Mapping[str, ProfilePattern] | None = None,
        orders: Mapping[str, ProfileOrder] | None = None,
    ) -> None:
        patterns = PATTERNS if patterns is None else patterns
        self.orders = dict(PROFILES if orders is None else orders)
        self.sorter = QualificationSorter()
        self.automata: dict[str, ProfileAutomaton] = {}
        for name, pattern in patterns.items():
            self.automata[name] = ProfileAutomaton(pattern)

    @property
    def profiles(self) -> list[str]:
        return list(self.automata)

    def sequence_for(self, tokens: Iterable[str], profile: str) -> tuple[str, ...]:
        """Sorted + projected sequence that the automaton of ``profile`` reads."""
        profile = profile.strip().upper()
        automaton = self._automaton(profile)
        alphabet = set(automaton.pattern.tokens)
        ordered = self.sorter.sort(tokens, self.orders[profile])
        return tuple(t for t in ordered if t in alphabet)

    def classify_profile(self, tokens: Iterable[str], profile: str) -> ProfileVerdict:
        profile = profile.strip().upper()
        automaton = self._automaton(profile)
        sequence = self.sequence_for(tokens, profile)
        accepted = automaton.accepts(sequence)
        missing = None if accepted else automaton.missing_stage(sequence)
        return ProfileVerdict(profile, accepted, sequence, missing)

    def classify(self, tokens: Iterable[str]) -> ClassificationResult:
        tokens = list(tokens)
        return ClassificationResult(
            {name: self.classify_profile(tokens, name) for name in self.automata}
        )

    def _automaton(self, profile: str) -> ProfileAutomaton:
        try:
            return self.automata[profile]
        except KeyError:
            raise ValueError(
                f"Unknown profile {profile!r}. Available: {', '.join(self.automata)}"
            ) from None
