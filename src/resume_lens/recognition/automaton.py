"""Stage 3 — Finite automata (pyformlang) that recognise a profile pattern.

Construction (generic, one builder for every profile)
-----------------------------------------------------
For a pattern with stages S1 … Sn the automaton has the states q0 … qn::

    q0 --required(S1)--> q1 --required(S2)--> q2 … --required(Sn)--> qn
         (qi loops on required(Si) ∪ optional(Si))

* ``qi`` means "stages S1 … Si are satisfied".
* The initial state is ``q0``; the only accepting state is ``qn``.
* The result is a **DFA**: the stage token sets are pairwise disjoint (checked
  by ``ProfilePattern``), so each (state, symbol) pair has at most one target,
  and there are no ε-transitions.  Missing transitions go to an implicit
  rejecting (dead) state, which is how ``pyformlang`` models partial DFAs.

The automaton reads the sequence produced by Stage 2: distinct canonical
tokens sorted in the profile's canonical order.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pyformlang.finite_automaton import DeterministicFiniteAutomaton, State, Symbol

from .patterns import ProfilePattern


@dataclass(frozen=True)
class AutomatonDefinition:
    """Explicit 5-tuple M = (Q, Σ, δ, q0, F)."""

    states: tuple[str, ...]
    alphabet: frozenset[str]
    delta: dict  # (state, symbol) -> state   (partial function)
    initial_state: str
    final_states: frozenset[str]


@dataclass(frozen=True)
class Trace:
    """Step-by-step run of an automaton over a sequence."""

    accepted: bool
    states: tuple[str, ...]  # visited states, starting with q0
    consumed: int  # symbols read before accepting/stopping
    stuck_on: str | None  # symbol without transition, if any
    last_state: str


class ProfileAutomaton:
    """DFA of one profile pattern, built with pyformlang."""

    def __init__(self, pattern: ProfilePattern) -> None:
        self.pattern = pattern
        self.state_names = tuple(f"q{i}" for i in range(len(pattern.stages) + 1))
        self.dfa = self._build()

    @property
    def name(self) -> str:
        return self.pattern.name

    # -- construction --------------------------------------------------------
    def transitions(self) -> list[tuple[str, str, str]]:
        """(source, symbol, target) triples of δ, in stage order."""
        triples: list[tuple[str, str, str]] = []
        for i, stage in enumerate(self.pattern.stages):
            source, target = self.state_names[i], self.state_names[i + 1]
            for token in stage.required:
                triples.append((source, token, target))  # satisfy the stage
            for token in stage.tokens:
                triples.append((target, token, target))  # stay in the stage
        return triples

    def _build(self) -> DeterministicFiniteAutomaton:
        dfa = DeterministicFiniteAutomaton()
        states = {name: State(name) for name in self.state_names}
        dfa.add_start_state(states[self.state_names[0]])
        dfa.add_final_state(states[self.state_names[-1]])
        for source, token, target in self.transitions():
            dfa.add_transition(states[source], Symbol(token), states[target])
        return dfa

    # -- formal definition ---------------------------------------------------
    def formal_definition(self) -> AutomatonDefinition:
        return AutomatonDefinition(
            states=self.state_names,
            alphabet=frozenset(self.pattern.tokens),
            delta={(s, t): q for s, t, q in self.transitions()},
            initial_state=self.state_names[0],
            final_states=frozenset({self.state_names[-1]}),
        )

    @property
    def automaton_type(self) -> str:
        """'DFA' when the pyformlang automaton is deterministic (it always is)."""
        return "DFA" if self.dfa.is_deterministic() else "NFA"

    # -- recognition ---------------------------------------------------------
    def accepts(self, sequence: Iterable[str]) -> bool:
        """True iff the sequence of canonical tokens is in the language."""
        return bool(self.dfa.accepts([Symbol(token) for token in sequence]))

    def trace(self, sequence: Iterable[str]) -> Trace:
        """Run the automaton step by step (used to explain a rejection)."""
        delta = self.formal_definition().delta
        state = self.state_names[0]
        visited = [state]
        consumed = 0
        for token in sequence:
            nxt = delta.get((state, token))
            if nxt is None:
                return Trace(False, tuple(visited), consumed, token, state)
            state = nxt
            visited.append(state)
            consumed += 1
        return Trace(state == self.state_names[-1], tuple(visited), consumed, None, state)

    def missing_stage(self, sequence: Iterable[str]) -> str | None:
        """Name of the first unsatisfied stage for a rejected sequence."""
        trace = self.trace(sequence)
        if trace.accepted:
            return None
        return self.pattern.stages[self.state_names.index(trace.last_state)].name
