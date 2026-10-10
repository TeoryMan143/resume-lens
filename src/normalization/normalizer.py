"""Stage 2 — Normalization of extracted qualifications (T_clean ; T_norm)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from .catalog import CANONICAL_VARIANTS
from .transducers import CleaningTransducer, QualificationTransducer, union_of


@dataclass
class NormalizationResult:
    """Output of the normalizer for a list of extracted strings."""

    mapping: dict[str, str] = field(default_factory=dict)  # raw -> canonical
    canonical: list[str] = field(default_factory=list)  # distinct, first-seen order
    unrecognized: list[str] = field(default_factory=list)


class QualificationNormalizer:
    """Transforms surface qualifications into canonical tokens.

    ``normalize_term(x) = T_norm(T_clean(x))`` where
    ``T_norm = ∪ T_<CANONICAL>`` over the whole catalogue.
    """

    def __init__(self, catalog: Mapping[str, Iterable[str]] | None = None) -> None:
        catalog = CANONICAL_VARIANTS if catalog is None else catalog
        self.cleaner = CleaningTransducer()
        self.transducers: dict[str, QualificationTransducer] = {
            canonical: QualificationTransducer(canonical, variants, self.cleaner)
            for canonical, variants in catalog.items()
        }
        if not self.transducers:
            raise ValueError("The catalogue must contain at least one qualification")
        self._check_disjoint()
        self.fst = union_of(self.transducers.values())

    def _check_disjoint(self) -> None:
        owner: dict[str, str] = {}
        for canonical, transducer in self.transducers.items():
            for word in transducer.cleaned_variants:
                if word in owner and owner[word] != canonical:
                    raise ValueError(
                        f"Ambiguous variant {word!r}: maps to {owner[word]} and {canonical}"
                    )
                owner[word] = canonical

    @property
    def canonical_tokens(self) -> list[str]:
        return list(self.transducers)

    def normalize_term(self, raw: str) -> str | None:
        """Canonical token of one extracted string, or ``None`` if unknown."""
        cleaned = self.cleaner.apply(raw.strip())
        if not cleaned:
            return None
        for output in self.fst.translate(cleaned):
            return " ".join(output)
        return None

    def normalize(self, qualifications: Iterable[str]) -> NormalizationResult:
        result = NormalizationResult()
        for raw in qualifications:
            token = self.normalize_term(raw)
            if token is None:
                if raw not in result.unrecognized:
                    result.unrecognized.append(raw)
                continue
            result.mapping[raw] = token
            if token not in result.canonical:
                result.canonical.append(token)
        return result
