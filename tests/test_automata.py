"""Stage 3 — Finite automata built with pyformlang."""

from __future__ import annotations

import pytest

from resume_lens.normalization import PROFILES

FS = "FULL_STACK_DEVELOPER"
PROFILE_NAMES = list(PROFILES)


@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_tc_r_10_every_automaton_is_a_dfa(automata, profile):
    a = automata[profile]
    assert a.automaton_type == "DFA"
    assert a.dfa.is_deterministic()
    delta = a.formal_definition().delta
    assert all(symbol != "epsilon" for _, symbol in delta)  # no ε-transitions


@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_tc_r_11_five_tuple_is_consistent(automata, profile):
    d = automata[profile].formal_definition()
    assert d.initial_state in d.states
    assert d.final_states <= set(d.states)
    assert len(d.final_states) == 1
    for (source, symbol), target in d.delta.items():
        assert source in d.states and target in d.states
        assert symbol in d.alphabet
    assert d.alphabet == set(PROFILES[profile].tokens)


@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_tc_r_12_automaton_is_minimal(automata, profile):
    dfa = automata[profile].dfa
    assert len(dfa.minimize().states) == len(dfa.states)


def test_tc_r_13_wednesday_sequence_is_accepted(automata, pipeline, wednesday_text):
    sequence = pipeline.run(wednesday_text, FS).sorted_qualifications
    assert sequence == ["JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"]
    assert automata[FS].accepts(sequence)
    trace = automata[FS].trace(sequence)
    assert trace.accepted
    assert trace.states == ("q0", "q1", "q2", "q3", "q4", "q5")
    assert trace.stuck_on is None


def test_tc_r_14_mary_jane_sequence_is_accepted_only_by_the_ml_automaton(
    automata, pipeline, mary_jane_text
):
    ml = "MACHINE_LEARNING_ENGINEER"
    sequence = pipeline.run(mary_jane_text, ml).sorted_qualifications
    assert automata[ml].accepts(sequence)
    assert not automata[FS].accepts(sequence)


def test_tc_r_15_trace_stops_where_the_wednesday_sequence_breaks(automata):
    # Without React the sequence jumps from the language to the backend.
    trace = automata[FS].trace(["JAVASCRIPT", "NODE_JS", "POSTGRESQL", "GIT"])
    assert not trace.accepted
    assert trace.stuck_on == "NODE_JS"
    assert trace.last_state == "q1"
    assert automata[FS].missing_stage(["JAVASCRIPT", "NODE_JS", "POSTGRESQL", "GIT"]) == (
        "FRONTEND_FRAMEWORK"
    )


def test_tc_r_16_unsorted_sequence_is_rejected(automata, pipeline, wednesday_text):
    # The automaton relies on the Stage 2 sorting: the same tokens in another order are not in L(M).
    sequence = pipeline.run(wednesday_text, FS).sorted_qualifications
    assert not automata[FS].accepts(list(reversed(sequence)))
