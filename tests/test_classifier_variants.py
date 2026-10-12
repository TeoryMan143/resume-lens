"""Stage 3 — Variants of the résumés in tests/resources.

Each case edits the text of a résumé (removing or replacing one skill) and
checks how the verdict changes after Stage 1, Stage 2 and Stage 3.
"""

from __future__ import annotations

import pytest

from resume_lens.recognition import ACCEPTED, REJECTED

FS = "FULL_STACK_DEVELOPER"
ML = "MACHINE_LEARNING_ENGINEER"

# (id, résumé fixture, text to replace, replacement, profile, expected missing stage)
VARIANTS = [
    ("wednesday-without-git", "wednesday_text", ", Git", "", FS, "VERSION_CONTROL"),
    ("wednesday-without-react", "wednesday_text", "React.js, ", "", FS, "FRONTEND_FRAMEWORK"),
    ("wednesday-without-node", "wednesday_text", "NodeJS, ", "", FS, "BACKEND_TECHNOLOGY"),
    ("wednesday-angular-instead-of-react", "wednesday_text", "React.js", "Angular", FS, None),
    ("wednesday-mongodb-instead-of-postgres", "wednesday_text", "Postgres", "MongoDB", FS, None),
    ("mary-without-python", "mary_jane_text", "Python, ", "", ML, "LANGUAGE"),
    ("mary-without-pandas-numpy", "mary_jane_text", "Pandas, NumPy, ", "", ML, "DATA_PROCESSING"),
    ("mary-without-ml-libraries", "mary_jane_text", "Scikit-learn, TensorFlow, ", "", ML, "ML_FRAMEWORK"),
    ("mary-nosql-instead-of-sql", "mary_jane_text", "SQL", "MongoDB", ML, "DATABASE"),
    ("mary-without-git", "mary_jane_text", ", Git", "", ML, "VERSION_CONTROL"),
    ("full-resume-with-git", "full_resume_text", "Docker", "Docker, Git", FS, None),
]


@pytest.mark.parametrize(
    "resume, old, new, profile, missing",
    [pytest.param(*case[1:], id=case[0]) for case in VARIANTS],
)
def test_tc_r_25_removing_or_replacing_a_skill_changes_the_verdict(
    request, classify, resume, old, new, profile, missing
):
    text = request.getfixturevalue(resume)
    assert old in text  # the edit really changes the résumé
    verdict = classify(text.replace(old, new)).verdicts[profile]
    assert verdict.missing_stage == missing
    assert verdict.status == (ACCEPTED if missing is None else REJECTED)


def test_tc_r_26_a_resume_can_satisfy_two_profiles(classify, wednesday_text, mary_jane_text):
    # Wednesday's web skills and Mary Jane's machine-learning skills in one résumé.
    result = classify(wednesday_text + "\n" + mary_jane_text)
    assert result.accepted_profiles == [FS, ML]
