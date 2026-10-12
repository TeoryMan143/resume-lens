"""Stage 3 — Classification of the résumés in tests/resources.

Every résumé goes through Stage 1 (extraction), Stage 2 (normalization and
sorting) and the Stage 3 automata of the four profiles.
"""

from __future__ import annotations

import random

import pytest

from resume_lens.recognition import ACCEPTED, REJECTED

FS = "FULL_STACK_DEVELOPER"
ML = "MACHINE_LEARNING_ENGINEER"
DEVOPS = "DEVOPS_ENGINEER"
DATA = "DATA_ENGINEER"

# (résumé fixture, profile) -> (status, first missing stage)
EXPECTED = {
    ("wednesday_text", FS): (ACCEPTED, None),
    ("wednesday_text", ML): (REJECTED, "LANGUAGE"),
    ("wednesday_text", DEVOPS): (REJECTED, "OS_SCRIPTING"),
    ("wednesday_text", DATA): (REJECTED, "LANGUAGE"),
    ("mary_jane_text", FS): (REJECTED, "LANGUAGE"),
    ("mary_jane_text", ML): (ACCEPTED, None),
    ("mary_jane_text", DEVOPS): (REJECTED, "OS_SCRIPTING"),
    ("mary_jane_text", DATA): (REJECTED, "DATA_PROCESSING"),
    ("full_resume_text", FS): (REJECTED, "VERSION_CONTROL"),
    ("full_resume_text", ML): (REJECTED, "LANGUAGE"),
    ("full_resume_text", DEVOPS): (REJECTED, "OS_SCRIPTING"),
    ("full_resume_text", DATA): (REJECTED, "DATA_PROCESSING"),
}


@pytest.mark.parametrize("resume, profile", list(EXPECTED))
def test_tc_r_22_verdict_of_every_resume_for_every_profile(request, classify, resume, profile):
    result = classify(request.getfixturevalue(resume))
    verdict = result.verdicts[profile]
    assert (verdict.status, verdict.missing_stage) == EXPECTED[(resume, profile)]


def test_tc_r_23_wednesday_addams_is_a_full_stack_developer(classify, wednesday_text):
    result = classify(wednesday_text)
    assert result.accepted_profiles == [FS]
    assert result.verdicts[FS].sequence == (
        "JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT",
    )


def test_tc_r_24_mary_jane_watson_is_a_machine_learning_engineer(classify, mary_jane_text):
    result = classify(mary_jane_text)
    assert result.accepted_profiles == [ML]
    assert result.verdicts[ML].sequence == (
        "PYTHON", "PANDAS", "NUMPY", "DATA_PIPELINES", "SCIKIT_LEARN", "TENSORFLOW",
        "ML_MODEL_DEVELOPMENT", "SQL", "GIT",
    )


def test_tc_r_25_full_resume_is_accepted_by_no_profile(classify, full_resume_text):
    result = classify(full_resume_text)
    assert result.accepted_profiles == []
    assert all(v.status == REJECTED for v in result.verdicts.values())


def test_tc_r_26_tokens_outside_the_profile_are_ignored(classify, full_resume_text):
    # The résumé has C++, C#, Docker and ML libraries; the Full Stack automaton never reads them.
    sequence = classify(full_resume_text).verdicts[FS].sequence
    assert sequence == (
        "JAVASCRIPT", "TYPESCRIPT", "ANGULAR", "VUE", "SPRING_BOOT", "REST_API",
        "MICROSERVICES", "MYSQL", "NOSQL", "MONGODB",
    )


@pytest.mark.parametrize("resume", ["wednesday_text", "mary_jane_text", "full_resume_text"])
def test_tc_r_27_result_does_not_depend_on_the_order_of_the_resume(
    request, extractor, normalizer, classifier, resume
):
    text = request.getfixturevalue(resume)
    qualifications = extractor.extract(text).qualifications
    expected = classifier.classify(normalizer.normalize(qualifications).canonical).to_dict()
    rng = random.Random(2026)
    for _ in range(20):
        shuffled = qualifications[:]
        rng.shuffle(shuffled)
        assert classifier.classify(normalizer.normalize(shuffled).canonical).to_dict() == expected


def test_tc_r_28_verdict_status_helpers(classify, wednesday_text):
    result = classify(wednesday_text)
    assert result.status(" full_stack_developer ") == ACCEPTED
    assert result.status(ML) == REJECTED
    assert set(result.to_dict()) == {FS, ML, DEVOPS, DATA}


def test_tc_r_29_unknown_profile_is_an_error(classifier):
    with pytest.raises(ValueError, match="Unknown profile"):
        classifier.classify_profile(["GIT"], "ASTRONAUT")
