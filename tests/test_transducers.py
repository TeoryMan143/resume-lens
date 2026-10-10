"""Stage 2 — Individual finite-state transducers (7-tuple and behaviour).

Test IDs (TC-N-xx) match docs/test-design-stages-1-2.md, section 2.2.
"""

from __future__ import annotations

import pytest

from resume_lens.normalization import CANONICAL_VARIANTS, QualificationTransducer
from resume_lens.normalization.transducers import EPSILON


# -------------------------------------------------------------- T_clean ----
@pytest.mark.parametrize(
    "raw, cleaned",
    [
        ("Scikit-learn", "scikitlearn"),
        ("React.js", "reactjs"),
        ("Tensor Flow", "tensorflow"),
        ("C++", "c++"),
        ("C#", "c#"),
        ("CI/CD", "cicd"),
        ("node_js", "nodejs"),
        ("Python3", "python3"),
    ],
)
def test_tc_n_01_cleaning_output(cleaner, raw, cleaned):
    assert cleaner.apply(raw) == cleaned


@pytest.mark.parametrize("raw", ["Café", "Ruby & Rails", "C++\n", "Node,js"])
def test_tc_n_02_cleaning_rejects_symbols_outside_sigma(cleaner, raw):
    assert cleaner.apply(raw) is None


def test_tc_n_03_cleaning_empty_word(cleaner):
    assert cleaner.apply("") == ""
    assert cleaner.apply(" .-_/") == ""


def test_tc_n_04_cleaning_formal_definition(cleaner):
    m = cleaner.formal_definition()
    assert m.states == {"q0"}
    assert m.initial_state == "q0"
    assert m.final_states == {"q0"}
    assert len(m.input_alphabet) == 26 + 26 + 10 + 2 + 5  # A-Z a-z 0-9 + # separators
    assert len(m.output_alphabet) == 26 + 10 + 2  # a-z 0-9 + #
    assert m.delta[("q0", "A")] == "q0"
    assert m.omega[("q0", "A")] == ("a",)
    assert m.omega[("q0", "a")] == ("a",)
    assert m.omega[("q0", " ")] == ()  # ε output
    assert all(target == "q0" for target in m.delta.values())


# ---------------------------------------------------------- T_<CANONICAL> ----
@pytest.mark.parametrize("word", ["react", "reactjs"])
def test_tc_n_05_react_accepts_variants(react_transducer, word):
    assert react_transducer.translate(word) == "REACT"


@pytest.mark.parametrize("word", ["reac", "reactjss", "angular", "", "React"])
def test_tc_n_06_react_rejects_other_words(react_transducer, word):
    # 'React' is rejected because T_REACT reads *cleaned* input (lower case).
    assert react_transducer.translate(word) is None


def test_tc_n_07_react_formal_definition(react_transducer):
    m = react_transducer.formal_definition()
    assert m.states == {"q0", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "qF"}
    assert m.input_alphabet == set("reactjs")
    assert m.output_alphabet == {"REACT"}
    assert m.initial_state == "q0"
    assert m.final_states == {"qF"}
    assert m.delta[("q0", "r")] == "q1"
    assert m.delta[("q5", EPSILON)] == "qF" and m.omega[("q5", EPSILON)] == ("REACT",)
    assert m.delta[("q7", EPSILON)] == "qF" and m.omega[("q7", EPSILON)] == ("REACT",)
    char_outputs = [out for (q, a), out in m.omega.items() if a != EPSILON]
    assert char_outputs and all(out == () for out in char_outputs)


def test_tc_n_08_scikit_variants_collapse(scikit_transducer):
    assert scikit_transducer.cleaned_variants == ("scikitlearn", "sklearn")
    assert scikit_transducer.translate("scikitlearn") == "SCIKIT_LEARN"
    assert scikit_transducer.translate("sklearn") == "SCIKIT_LEARN"
    assert scikit_transducer.translate("scikit") is None


@pytest.mark.parametrize("variants", [[], ["Café"], ["---"]])
def test_tc_n_09_invalid_transducer_definition(variants):
    with pytest.raises(ValueError):
        QualificationTransducer("X", variants)


@pytest.mark.parametrize("canonical", sorted(CANONICAL_VARIANTS))
def test_tc_n_10_catalog_transducers_are_deterministic(canonical):
    t = QualificationTransducer(canonical, CANONICAL_VARIANTS[canonical])
    assert all(len(targets) == 1 for targets in t.fst.transitions.values())
    assert t.fst.start_states == {"q0"} and t.fst.final_states == {"qF"}
