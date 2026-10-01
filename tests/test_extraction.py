"""Stage 1 — Résumé information extraction (regular expressions).

Test IDs (TC-E-xx) match docs/test-design-stages-1-2.md, section 2.1.
"""

from __future__ import annotations

import pytest

from resume_lens.extraction import (
    PATTERNS,
    Category,
    Experience,
    ExtractionResult,
    ResumeExtractor,
)

from pathlib import Path

RESOURCES = Path(__file__).parent / "resources"


# ------------------------------------------------------------------ name ----
def test_tc_e_01_name_first_line(extractor, wednesday_text):
    assert extractor.extract_name(wednesday_text) == "Wednesday Addams"


def test_tc_e_02_name_three_words(extractor, mary_jane_text):
    assert extractor.extract_name(mary_jane_text) == "Mary Jane Watson"


def test_tc_e_03_name_absent(extractor):
    assert extractor.extract_name("technical skills: python, git\n3 years of experience") is None


# --------------------------------------------------------------- contact ----
def test_tc_e_04_email_valid(extractor, full_resume_text):
    assert extractor.extract_emails(full_resume_text) == ["wednesday.addams@nevermore.edu"]


@pytest.mark.parametrize("text", ["user@domain", "user@domain.c", "@nevermore.edu", "user at mail.com"])
def test_tc_e_05_email_invalid(extractor, text):
    assert extractor.extract_emails(text) == []


def test_tc_e_06_phone_formats(extractor, full_resume_text):
    assert extractor.extract_phones(full_resume_text) == ["+57 300 123 4567", "(602) 555-0199"]
    assert extractor.extract_phones("Cel: 3001234567") == ["3001234567"]


@pytest.mark.parametrize("text", ["Universidad Icesi (2019 - 2023)", "2019-2023", "Code A00411070", "12345"])
def test_tc_e_07_phone_false_positives(extractor, text):
    assert extractor.extract_phones(text) == []


def test_tc_e_08_links(extractor, full_resume_text):
    assert extractor.extract_links(full_resume_text) == [
        "https://github.com/wednesday-a",
        "linkedin.com/in/wednesday",
    ]


# ------------------------------------------------------------ experience ----
def test_tc_e_09_experience_statement(extractor, wednesday_text):
    assert extractor.extract_experience(wednesday_text) == [
        Experience(3, "developing web applications")
    ]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("5+ yrs of experience with REST APIs", Experience(5, "with REST APIs")),
        ("4 años de experiencia en desarrollo backend", Experience(4, "en desarrollo backend")),
        ("10 years of professional experience", Experience(10, "")),
    ],
)
def test_tc_e_10_experience_variants(extractor, text, expected):
    assert extractor.extract_experience(text) == [expected]


def test_tc_e_11_degrees(extractor, full_resume_text):
    assert extractor.extract_degrees(full_resume_text) == [
        "B.Sc. in Computer Science",
        "Master of Science in Artificial Intelligence",
        "Ingeniería de Sistemas",
    ]


# -------------------------------------------------------- qualifications ----
def test_tc_e_12_programming_languages(extractor):
    result = extractor.extract("Skills: JavaScript, TypeScript, Java, C++, C#, Python 3.")
    assert result.programming_languages == ["JavaScript", "TypeScript", "Java", "C++", "C#", "Python 3"]


def test_tc_e_13_languages_not_inside_other_tokens(extractor):
    result = extractor.extract("React.js, NodeJS, JavaScript")
    assert result.programming_languages == ["JavaScript"]  # no 'js', no 'Java'
    assert result.frameworks == ["React.js", "NodeJS"]


def test_tc_e_14_frameworks_and_libraries(extractor):
    text = ("React.js, ReactJS, Vue.js, Angular, Spring Boot, scikit learn, sklearn, "
            "Scikit-learn, Tensor Flow, Py Torch, NumPy, pandas")
    assert extractor.extract(text).frameworks == [
        "React.js", "ReactJS", "Vue.js", "Angular", "Spring Boot", "scikit learn", "sklearn",
        "Scikit-learn", "Tensor Flow", "Py Torch", "NumPy", "pandas",
    ]


def test_tc_e_15_databases_sql_standalone(extractor):
    result = extractor.extract("PostgreSQL, Postgres, MySQL, NoSQL, MongoDB, SQL")
    assert result.databases == ["PostgreSQL", "Postgres", "MySQL", "NoSQL", "MongoDB", "SQL"]


def test_tc_e_16_tools_not_inside_urls(extractor):
    result = extractor.extract("Git, GitHub, Docker, Kubernetes, AWS. See https://github.com/x")
    assert result.tools == ["Git", "GitHub", "Docker", "Kubernetes", "AWS"]


def test_tc_e_17_other_qualifications(extractor):
    text = ("Built RESTful APIs and machine learning models, predictive models, "
            "data-processing pipelines and CI/CD.")
    assert extractor.extract(text).other_qualifications == [
        "RESTful APIs", "machine learning models", "predictive models",
        "data-processing pipelines", "CI/CD",
    ]


def test_tc_e_18_statement_example_full_stack(extractor, wednesday_text):
    assert extractor.extract(wednesday_text).qualifications == [
        "JS", "React.js", "NodeJS", "Postgres", "Git",
    ]


def test_tc_e_19_statement_example_ml(extractor, mary_jane_text):
    assert extractor.extract(mary_jane_text).qualifications == [
        "predictive models", "data-processing pipelines", "Python", "Pandas",
        "NumPy", "Scikit-learn", "TensorFlow", "SQL", "Git",
    ]


def test_tc_e_20_case_insensitive(extractor):
    result = extractor.extract("PYTHON, javascript, POSTGRES")
    assert result.programming_languages == ["PYTHON", "javascript"]
    assert result.databases == ["POSTGRES"]


def test_tc_e_21_duplicates_removed(extractor):
    assert extractor.extract("Git, Python, Git, Python").qualifications == ["Git", "Python"]


# ------------------------------------------------------------ edge cases ----
def test_tc_e_22_empty_text(extractor):
    result = extractor.extract("")
    assert result.name is None
    assert result.qualifications == []
    assert result.emails == result.phones == result.links == result.degrees == []
    assert result.experience == []


def test_tc_e_23_none_text(extractor):
    with pytest.raises(ValueError):
        extractor.extract(None)


# ----------------------------------------------------------- persistence ----
def test_tc_e_24_json_round_trip(extractor, full_resume_text, tmp_path):
    result = extractor.extract(full_resume_text)
    path = result.save_json(tmp_path / "out" / "stage1.json")
    assert path.exists()
    loaded = ExtractionResult.load_json(path)
    assert loaded.to_dict() == result.to_dict()
    assert loaded.qualifications == result.qualifications


def test_tc_e_25_extract_file(extractor, wednesday_text):
    from_file = extractor.extract_file(RESOURCES / "wednesday_addams.txt")
    assert from_file.to_dict() == extractor.extract(wednesday_text).to_dict()


def test_tc_e_26_every_pattern_is_documented():
    assert set(PATTERNS) == set(Category)
    for pattern in PATTERNS.values():
        assert pattern.description.strip()
        assert pattern.compiled.pattern == pattern.expression

