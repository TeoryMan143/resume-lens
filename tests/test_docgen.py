"""Stage 2 — Generated formal documentation (7-tuples and diagrams).

Test IDs (TC-D-xx) match docs/test-design-stages-1-2.md, section 2.6.
"""

from __future__ import annotations

import shutil

import pytest

from resume_lens.normalization import CANONICAL_VARIANTS, QualificationTransducer
from resume_lens.normalization.docgen import DOC_NAME, generate, qualification_dot


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    docs = tmp_path_factory.mktemp("docs")
    return docs, generate(docs)


def test_tc_d_01_files_are_written(generated):
    docs, path = generated
    assert path == docs / DOC_NAME and path.exists()
    dots = {p.stem for p in (docs / "fst").glob("*.dot")}
    assert dots == {"T_clean"} | {f"T_{c}" for c in CANONICAL_VARIANTS}


def test_tc_d_02_one_section_per_transducer(generated):
    _, path = generated
    text = path.read_text(encoding="utf-8")
    for canonical in CANONICAL_VARIANTS:
        assert f"### T_{canonical}\n" in text
        assert f"M_{canonical} = (Q, Σ, Γ, δ, ω, q0, F)" in text
    assert "## 2. T_clean" in text and "## 3. T_norm" in text


def test_tc_d_03_sorting_section_lists_four_profiles(generated):
    _, path = generated
    text = path.read_text(encoding="utf-8")
    for name in ("FULL_STACK_DEVELOPER", "MACHINE_LEARNING_ENGINEER", "DEVOPS_ENGINEER", "DATA_ENGINEER"):
        assert name in text
    assert "**`JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT`**" in text


def test_tc_d_04_react_table_and_diagram():
    t = QualificationTransducer("REACT", ["React", "React.js", "ReactJS"])
    dot = qualification_dot(t)
    assert "qF [shape=doublecircle]" in dot
    assert 'q5 -> qF [label="ε / REACT"]' in dot
    assert 'q0 -> q1 [label="r / ε"]' in dot
    assert dot.count("->") == 1 + t.fst.get_number_transitions()  # + start arrow


@pytest.mark.skipif(shutil.which("dot") is None, reason="Graphviz is not installed")
def test_tc_d_05_svg_rendered_when_graphviz_available(generated):
    docs, path = generated
    assert (docs / "fst" / "T_REACT.svg").exists()
    assert "![T_REACT](fst/T_REACT.svg)" in path.read_text(encoding="utf-8")
