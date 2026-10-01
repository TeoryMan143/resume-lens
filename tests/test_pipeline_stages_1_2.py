"""Integration — Stage 1 output feeds Stage 2.

Test IDs (TC-I-xx) match docs/test-design-stages-1-2.md, section 2.5.
"""

from __future__ import annotations

import json

import pytest

from resume_lens import main
from resume_lens.normalization import CANONICAL_VARIANTS

from pathlib import Path

RESOURCES = Path(__file__).parent / "resources"


def test_tc_i_01_wednesday_full_stack(pipeline, wednesday_text):
    out = pipeline.run(wednesday_text, "FULL_STACK_DEVELOPER")
    assert out.sorted_qualifications == ["JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"]
    assert out.normalization.unrecognized == []


def test_tc_i_02_mary_jane_ml(pipeline, mary_jane_text):
    out = pipeline.run(mary_jane_text, "MACHINE_LEARNING_ENGINEER")
    assert out.sorted_qualifications == [
        "PYTHON", "PANDAS", "NUMPY", "DATA_PIPELINES", "SCIKIT_LEARN",
        "TENSORFLOW", "ML_MODEL_DEVELOPMENT", "SQL", "GIT",
    ]


def test_tc_i_03_resume_order_does_not_matter(pipeline):
    a = pipeline.run("Skills: Git, NodeJS, JS, Postgres, React.js.", "FULL_STACK_DEVELOPER")
    b = pipeline.run("Skills: React.js, JS, Postgres, Git, NodeJS.", "FULL_STACK_DEVELOPER")
    assert a.sorted_qualifications == b.sorted_qualifications


VARIANTS = [(c, v) for c, vs in CANONICAL_VARIANTS.items() for v in vs]


@pytest.mark.parametrize("canonical, variant", VARIANTS, ids=[v for _, v in VARIANTS])
def test_tc_i_04_every_catalog_variant_flows_through(pipeline, canonical, variant):
    """Stage 1 extracts exactly the variant and Stage 2 maps it to its canonical."""
    out = pipeline.run(f"Technical Skills:\n{variant}.\n", "FULL_STACK_DEVELOPER")
    assert out.extraction.qualifications == [variant]
    assert out.normalization.canonical == [canonical]


def test_tc_i_05_everything_extracted_is_normalized(pipeline, full_resume_text):
    out = pipeline.run(full_resume_text, "FULL_STACK_DEVELOPER")
    assert out.normalization.unrecognized == []
    assert set(out.normalization.mapping) == set(out.extraction.qualifications)


def test_tc_i_06_cli(capsys, tmp_path):
    json_path = tmp_path / "stage1.json"
    main(["--resume", str(RESOURCES / "wednesday_addams.txt"),
        "--profile", "FULL_STACK_DEVELOPER", "--out", str(json_path)])
    printed = capsys.readouterr().out
    assert "JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT" in printed
    assert json.loads(json_path.read_text(encoding="utf-8"))["qualifications"] == [
        "JS", "React.js", "NodeJS", "Postgres", "Git",
    ]
