"""Stage 2 — Finite-state transducers implemented with pyformlang.

Two kinds of transducers are used, applied in cascade:

1. ``CleaningTransducer`` (T_clean) — a one-state transducer that lower-cases
   letters, copies digits, '+' and '#', and erases the separators
   ' ', '-', '.', '_' and '/'.  Example: "Scikit-learn" -> "scikitlearn".

2. ``QualificationTransducer`` (T_<CANONICAL>) — one per canonical qualification.
   It reads a cleaned variant character by character through a prefix tree
   (every character transition outputs ε) and, once a complete variant has been
   read, takes an ε-transition to the final state q_F emitting the canonical
   token.  Example: T_REACT maps "reactjs" -> REACT.

Both are 7-tuples M = (Q, Σ, Γ, δ, ω, q0, F).
"""

from __future__ import annotations

import string
from dataclasses import dataclass
from functools import reduce
from pathlib import Path
from typing import Iterable

from pyformlang.fst import FST

EPSILON = "epsilon"  # pyformlang's name for the empty input symbol

LOWER = tuple(string.ascii_lowercase)
UPPER = tuple(string.ascii_uppercase)
DIGITS = tuple(string.digits)
KEPT_SYMBOLS = ("+", "#")
SEPARATORS = (" ", "-", ".", "_", "/")


@dataclass(frozen=True)
class FormalDefinition:
    """Explicit 7-tuple M = (Q, Σ, Γ, δ, ω, q0, F) of a transducer."""

    states: frozenset
    input_alphabet: frozenset
    output_alphabet: frozenset
    delta: dict  # (state, input symbol or 'epsilon') -> next state
    omega: dict  # (state, input symbol or 'epsilon') -> tuple of output symbols
    initial_state: str
    final_states: frozenset


def _formal_definition(fst: FST, initial_state: str) -> FormalDefinition:
    delta, omega = {}, {}
    for (source, symbol), targets in fst.transitions.items():
        # Every transducer in this module is deterministic: one target per head.
        target, output = targets[0]
        delta[(source, symbol)] = target
        omega[(source, symbol)] = tuple(output)
    return FormalDefinition(
        states=frozenset(fst.states),
        input_alphabet=frozenset(fst.input_symbols),
        output_alphabet=frozenset(fst.output_symbols),
        delta=delta,
        omega=omega,
        initial_state=initial_state,
        final_states=frozenset(fst.final_states),
    )


class CleaningTransducer:
    """T_clean: case folding + separator removal (single state q0)."""

    STATE = "q0"

    def __init__(self) -> None:
        q0 = self.STATE
        fst = FST()
        fst.add_start_state(q0)
        fst.add_final_state(q0)
        for upper, lower in zip(UPPER, LOWER):
            fst.add_transition(q0, upper, q0, [lower])
        for symbol in LOWER + DIGITS + KEPT_SYMBOLS:
            fst.add_transition(q0, symbol, q0, [symbol])
        for separator in SEPARATORS:
            fst.add_transition(q0, separator, q0, [])  # output ε
        self.fst = fst

    def apply(self, text: str) -> str | None:
        """Cleaned string, or ``None`` if ``text`` has symbols outside Σ."""
        for output in self.fst.translate(text):
            return "".join(output)
        return None

    def formal_definition(self) -> FormalDefinition:
        return _formal_definition(self.fst, self.STATE)

    def write_dot(self, path: str | Path) -> None:
        self.fst.write_as_dot(str(path))


class QualificationTransducer:
    """T_<CANONICAL>: maps every cleaned variant to one canonical token."""

    INITIAL = "q0"
    FINAL = "qF"

    def __init__(self, canonical: str, variants: Iterable[str],
                 cleaner: CleaningTransducer | None = None) -> None:
        cleaner = cleaner or CleaningTransducer()
        self.canonical = canonical
        self.variants = tuple(variants)
        if not self.variants:
            raise ValueError(f"{canonical} needs at least one variant")
        cleaned = []
        for variant in self.variants:
            value = cleaner.apply(variant)
            if not value:
                raise ValueError(f"Variant {variant!r} of {canonical} is not over Σ_clean")
            cleaned.append(value)
        self.cleaned_variants = tuple(sorted(set(cleaned)))
        self.fst = self._build()

    def _build(self) -> FST:
        fst = FST()
        fst.add_start_state(self.INITIAL)
        fst.add_final_state(self.FINAL)
        next_id = 1
        children: dict[tuple[str, str], str] = {}
        word_ends: set[str] = set()
        for word in self.cleaned_variants:
            state = self.INITIAL
            for char in word:
                if (state, char) not in children:
                    new_state = f"q{next_id}"
                    next_id += 1
                    children[(state, char)] = new_state
                    fst.add_transition(state, char, new_state, [])  # ω = ε
                state = children[(state, char)]
            word_ends.add(state)
        for state in sorted(word_ends, key=lambda s: int(s[1:])):
            fst.add_transition(state, EPSILON, self.FINAL, [self.canonical])
        return fst

    def translate(self, cleaned: str) -> str | None:
        """Canonical token for a *cleaned* string, or ``None``."""
        for output in self.fst.translate(cleaned):
            return " ".join(output)
        return None

    def formal_definition(self) -> FormalDefinition:
        return _formal_definition(self.fst, self.INITIAL)

    def write_dot(self, path: str | Path) -> None:
        self.fst.write_as_dot(str(path))


def union_of(transducers: Iterable[QualificationTransducer]) -> FST:
    """T_norm = T_1 ∪ T_2 ∪ ... ∪ T_n (pyformlang ``FST.union``)."""
    return reduce(lambda a, b: a.union(b), (t.fst for t in transducers))
