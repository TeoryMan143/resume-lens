"""Stage 2 — Normalizer (T_clean followed by the union of all T_<CANONICAL>).

Test IDs (TC-N-xx) match docs/test-design-stages-1-2.md, section 2.3.
"""

from __future__ import annotations

import pytest

from resume_lens.normalization import CANONICAL_VARIANTS, QualificationNormalizer


@pytest.mark.parametrize(
    "raw, canonical",
    [
        ("JS", "JAVASCRIPT"), ("Javascript", "JAVASCRIPT"),
        ("React.js", "REACT"), ("ReactJS", "REACT"),
        ("NodeJS", "NODE_JS"), ("Node.js", "NODE_JS"),
        ("Postgres", "POSTGRESQL"), ("PostgreSQL", "POSTGRESQL"),
        ("pandas", "PANDAS"),
        ("sklearn", "SCIKIT_LEARN"), ("scikit learn", "SCIKIT_LEARN"), ("Scikit-learn", "SCIKIT_LEARN"),
        ("Tensor Flow", "TENSORFLOW"), ("TensorFlow", "TENSORFLOW"),
        ("Py Torch", "PYTORCH"), ("PyTorch", "PYTORCH"),
    ],
)
def test_tc_n_11_statement_transformations(normalizer, raw, canonical):
    assert normalizer.normalize_term(raw) == canonical


@pytest.mark.parametrize(
    "raw, canonical",
    [
        ("Java Script", "JAVASCRIPT"), ("TS", "TYPESCRIPT"), ("C++", "C_PLUS_PLUS"),
        ("CSharp", "C_SHARP"), ("Golang", "GO"), ("K8s", "KUBERNETES"), ("Mongo", "MONGODB"),
        ("RESTful APIs", "REST_API"), ("predictive models", "ML_MODEL_DEVELOPMENT"),
        ("data-processing pipelines", "DATA_PIPELINES"), ("Amazon Web Services", "AWS"),
        ("CI/CD", "CI_CD"), ("Spring Boot", "SPRING_BOOT"), ("Python 3", "PYTHON"),
    ],
)
def test_tc_n_12_team_transformations(normalizer, raw, canonical):
    assert normalizer.normalize_term(raw) == canonical


@pytest.mark.parametrize(
    "raw, canonical",
    [("  REACTJS  ", "REACT"), ("node.JS", "NODE_JS"), ("NUMPY", "NUMPY"), ("tensor-flow", "TENSORFLOW")],
)
def test_tc_n_13_case_and_separator_robustness(normalizer, raw, canonical):
    assert normalizer.normalize_term(raw) == canonical


@pytest.mark.parametrize("raw", ["Cobol", "Excel", "Ruby on Rails", "", "   ", "Java EE", "Café"])
def test_tc_n_14_unknown_terms(normalizer, raw):
    assert normalizer.normalize_term(raw) is None


@pytest.mark.parametrize(
    "raw, canonical",
    [("Java", "JAVA"), ("JavaScript", "JAVASCRIPT"), ("Git", "GIT"), ("GitHub", "GITHUB"),
     ("SQL", "SQL"), ("MySQL", "MYSQL"), ("NoSQL", "NOSQL"), ("Node", "NODE_JS")],
)
def test_tc_n_15_prefixes_are_not_confused(normalizer, raw, canonical):
    assert normalizer.normalize_term(raw) == canonical


def test_tc_n_16_normalize_statement_list(normalizer):
    result = normalizer.normalize(["JS", "React.js", "NodeJS", "Postgres", "Git"])
    assert result.canonical == ["JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"]
    assert result.mapping == {
        "JS": "JAVASCRIPT", "React.js": "REACT", "NodeJS": "NODE_JS",
        "Postgres": "POSTGRESQL", "Git": "GIT",
    }
    assert result.unrecognized == []


def test_tc_n_17_equivalent_terms_collapse(normalizer):
    result = normalizer.normalize(["JS", "JavaScript", "Javascript", "React"])
    assert result.canonical == ["JAVASCRIPT", "REACT"]
    assert len(result.mapping) == 4


def test_tc_n_18_unrecognized_terms_reported_once(normalizer):
    result = normalizer.normalize(["Python", "Cobol", "Cobol"])
    assert result.canonical == ["PYTHON"]
    assert result.unrecognized == ["Cobol"]


def test_tc_n_19_empty_input(normalizer):
    result = normalizer.normalize([])
    assert result.canonical == [] and result.mapping == {} and result.unrecognized == []


@pytest.mark.parametrize(
    "catalog",
    [{"JAVA_A": ["Java"], "JAVA_B": ["JAVA"]}, {"X": ["Node.js"], "Y": ["nodejs"]}, {}],
)
def test_tc_n_20_invalid_catalogs(catalog):
    with pytest.raises(ValueError):
        QualificationNormalizer(catalog)


@pytest.mark.parametrize("canonical", sorted(CANONICAL_VARIANTS))
def test_tc_n_21_every_variant_maps_to_its_canonical(normalizer, canonical):
    for variant in CANONICAL_VARIANTS[canonical]:
        assert normalizer.normalize_term(variant) == canonical


def test_tc_n_22_union_structure(normalizer):
    n = len(CANONICAL_VARIANTS)
    assert len(normalizer.fst.start_states) == n
    assert len(normalizer.fst.final_states) == n
    assert normalizer.fst.output_symbols == set(CANONICAL_VARIANTS)
    assert normalizer.canonical_tokens == list(CANONICAL_VARIANTS)
