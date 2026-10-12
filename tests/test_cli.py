"""End-to-end — the command documented in README.md, Stages 1 -> 4.

    python main.py --resume path/to/resume.txt --profile FULL_STACK_DEVELOPER

Test IDs (TC-C-xx) match docs/test-design-stage-4.md, section 2.7.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from resume_lens import main
from resume_lens.dsl import CandidateProfileBuilder, CandidateProfileLanguage

ROOT = Path(__file__).parent.parent
RESOURCES = Path(__file__).parent / "resources"

# Each sample résumé and the profile it is written for.
SAMPLES = {
    "wednesday_addams.txt": "FULL_STACK_DEVELOPER",
    "mary_jane_watson.txt": "MACHINE_LEARNING_ENGINEER",
    "devops_resume.txt": "DEVOPS_ENGINEER",
    "data_engineer_resume.txt": "DATA_ENGINEER",
}


def run_main(capsys, resume: str | Path, *args: str) -> tuple[int, str, str]:
    code = main(["--resume", str(RESOURCES / resume), *args])
    out = capsys.readouterr()
    return code, out.out, out.err


def test_tc_c_01_readme_command(tmp_path):
    """Exactly the README invocation, in a separate Python process."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        [sys.executable, "main.py", "--resume", str(RESOURCES / "wednesday_addams.txt"),
         "--profile", "FULL_STACK_DEVELOPER"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=env,
    )
    assert result.returncode == 0, result.stderr
    assert "Stage 3 - FULL_STACK_DEVELOPER: ACCEPTED" in result.stdout
    assert "Stage 4 - candidate profile (valid):" in result.stdout
    assert 'candidate "Wednesday Addams" {' in result.stdout


def test_tc_c_02_output_shows_every_stage(capsys):
    code, out, _ = run_main(capsys, "wednesday_addams.txt", "--profile", "FULL_STACK_DEVELOPER")
    assert code == 0
    assert out.splitlines()[:5] == [
        "Stage 1 - extracted: JS, React.js, NodeJS, Postgres, Git",
        "Stage 2 - normalized: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT",
        "Stage 2 - sorted for FULL_STACK_DEVELOPER: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT",
        "Stage 3 - FULL_STACK_DEVELOPER: ACCEPTED",
        "Stage 3 - accepted profiles: FULL_STACK_DEVELOPER",
    ]


@pytest.mark.parametrize("resume, profile", SAMPLES.items(), ids=SAMPLES.values())
def test_tc_c_03_each_profile_accepts_its_resume(capsys, resume, profile):
    code, out, _ = run_main(capsys, resume, "--profile", profile)
    assert code == 0
    assert f"Stage 3 - {profile}: ACCEPTED" in out
    assert f"Stage 3 - accepted profiles: {profile}\n" in out


def test_tc_c_04_rejected_profile_shows_missing_stage(capsys):
    code, out, _ = run_main(capsys, "wednesday_addams.txt",
                            "--profile", "MACHINE_LEARNING_ENGINEER")
    assert code == 0  # a rejection is a valid result, not an error
    assert "Stage 3 - MACHINE_LEARNING_ENGINEER: REJECTED (missing LANGUAGE)" in out
    assert "Stage 3 - accepted profiles: FULL_STACK_DEVELOPER" in out


def test_tc_c_05_no_profile_accepted(capsys):
    code, out, _ = run_main(capsys, "full_resume.txt")
    assert code == 0
    assert "Stage 3 - accepted profiles: none" in out
    assert "Stage 4 - candidate profile (valid):" in out


def test_tc_c_06_profile_is_case_insensitive(capsys):
    code, out, _ = run_main(capsys, "wednesday_addams.txt", "--profile", "full_stack_developer")
    assert code == 0
    assert "Stage 3 - FULL_STACK_DEVELOPER: ACCEPTED" in out


def test_tc_c_07_default_profile_is_full_stack(capsys):
    _, out, _ = run_main(capsys, "wednesday_addams.txt")
    assert "Stage 3 - FULL_STACK_DEVELOPER: ACCEPTED" in out


def test_tc_c_08_unknown_profile_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as info:
        main(["--resume", str(RESOURCES / "wednesday_addams.txt"), "--profile", "QA_ENGINEER"])
    assert info.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_tc_c_09_cpl_file_is_saved_and_reparsable(capsys, tmp_path):
    path = tmp_path / "profiles" / "wednesday.cpl"
    code, out, _ = run_main(capsys, "wednesday_addams.txt", "--cpl", str(path))
    assert code == 0
    assert f"Stage 4 - saved to {path}" in out
    saved = path.read_text(encoding="utf-8")
    assert saved in out  # the printed profile is the saved one
    assert CandidateProfileLanguage().parse(saved).name == "Wednesday Addams"


def test_tc_c_10_stage1_json_still_written(capsys, tmp_path):
    path = tmp_path / "stage1.json"
    code, _, _ = run_main(capsys, "mary_jane_watson.txt", "--out", str(path))
    assert code == 0 and path.is_file()


def test_tc_c_11_resume_without_name(capsys, tmp_path):
    resume = tmp_path / "anonymous.txt"
    resume.write_text("Technical Skills:\nJS, React.js, NodeJS, Postgres, Git.\n", encoding="utf-8")
    code, out, _ = run_main(capsys, resume)
    assert code == 0
    assert 'candidate "Unknown Candidate" {' in out
    assert "Stage 3 - FULL_STACK_DEVELOPER: ACCEPTED" in out


def test_tc_c_12_invalid_profile_exits_with_error(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(CandidateProfileBuilder, "build", lambda self, *a: "candidate {")
    path = tmp_path / "never.cpl"
    code, out, err = run_main(capsys, "wednesday_addams.txt", "--cpl", str(path))
    assert code == 1
    assert "Stage 4 - invalid candidate profile:" in err
    assert "Stage 4 - candidate profile (valid)" not in out
    assert not path.exists()


def test_tc_c_13_html_visualization(capsys, tmp_path):
    path = tmp_path / "html" / "wednesday.html"
    code, out, _ = run_main(capsys, "wednesday_addams.txt", "--html", str(path))
    assert code == 0
    assert f"Stage 4 - HTML visualization saved to {path}" in out
    html = path.read_text(encoding="utf-8")
    assert "<h1>Wednesday Addams</h1>" in html
    assert '<span class="badge accepted">Full Stack Developer</span>' in html
