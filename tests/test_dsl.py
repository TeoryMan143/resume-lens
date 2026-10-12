"""Stage 4 — Candidate Profile Language (context-free grammar with textX).

Test IDs (TC-G-xx) match docs/test-design-stage-4.md, section 2.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from resume_lens.dsl import (
    CPL_EXTENSION,
    GRAMMAR_PATH,
    CandidateProfileBuilder,
    ProfileValidationError,
)
from resume_lens.dsl.builder import UNKNOWN_NAME
from resume_lens.extraction import Category, Experience, ExtractedItem, ExtractionResult
from resume_lens.normalization import NormalizationResult
from resume_lens.recognition import PATTERNS, ClassificationResult, ProfileVerdict

RESOURCES = Path(__file__).parent / "resources"
RESUMES = sorted(RESOURCES.glob("*.txt"))

WEDNESDAY_CPL = """\
candidate "Wednesday Addams" {
    experience {
        3 years "developing web applications"
    }
    skills {
        programming_language: JAVASCRIPT ("JS");
        framework_library: REACT ("React.js"), NODE_JS ("NodeJS");
        database: POSTGRESQL ("Postgres");
        tool: GIT ("Git");
    }
    classification {
        FULL_STACK_DEVELOPER: ACCEPTED via JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT;
        MACHINE_LEARNING_ENGINEER: REJECTED missing LANGUAGE;
        DEVOPS_ENGINEER: REJECTED missing OS_SCRIPTING;
        DATA_ENGINEER: REJECTED missing LANGUAGE;
    }
}
"""


def mutate(text: str, old: str, new: str) -> str:
    """Replace the first ``old`` by ``new``; fails if ``old`` is not in the text."""
    assert old in text, f"{old!r} not found in the base document"
    return text.replace(old, new, 1)


def all_rejected() -> ClassificationResult:
    """Every profile rejected at its first stage (what an empty résumé produces)."""
    return ClassificationResult(
        {n: ProfileVerdict(n, False, (), p.stages[0].name) for n, p in PATTERNS.items()}
    )


# --------------------------------------------------------------------------- #
# 2.1 CandidateProfileBuilder — Stage 1-3 outputs -> CPL text
# --------------------------------------------------------------------------- #
def test_tc_g_01_wednesday_document(stage_outputs, wednesday_text):
    text = CandidateProfileBuilder().build(*stage_outputs(wednesday_text))
    assert text == WEDNESDAY_CPL


def test_tc_g_02_full_resume_sections(stage_outputs, full_resume_text):
    text = CandidateProfileBuilder().build(*stage_outputs(full_resume_text))
    assert 'email "wednesday.addams@nevermore.edu"' in text
    assert 'phone "+57 300 123 4567"' in text
    assert 'phone "(602) 555-0199"' in text
    assert 'link "linkedin.com/in/wednesday"' in text
    assert 'degree "B.Sc. in Computer Science"' in text
    assert '5 years "with REST APIs and microservices"' in text
    # two surface forms collapse into one canonical skill with both aliases
    assert 'REST_API ("REST APIs", "RESTful APIs")' in text
    assert "FULL_STACK_DEVELOPER: REJECTED missing VERSION_CONTROL;" in text


def test_tc_g_03_empty_optional_sections_are_omitted(stage_outputs, wednesday_text):
    text = CandidateProfileBuilder().build(*stage_outputs(wednesday_text))
    assert "contact" not in text
    assert "education" not in text


def test_tc_g_04_skills_grouped_by_stage1_category(stage_outputs, full_resume_text):
    text = CandidateProfileBuilder().build(*stage_outputs(full_resume_text))
    lines = [line.strip() for line in text.splitlines()]
    categories = [line.split(":")[0] for line in lines if line.endswith(";") and ":" in line
                  and line.split(":")[0].islower()]
    assert categories == [
        "programming_language", "framework_library", "database", "tool", "other_qualification",
    ]


def test_tc_g_05_missing_name_uses_placeholder(language):
    builder = CandidateProfileBuilder()
    text = builder.build(ExtractionResult(), NormalizationResult(), all_rejected())
    assert text.startswith('candidate "Unknown Candidate" {')
    assert "    skills {\n    }" in text  # skills is mandatory even when empty
    assert language.parse(text).name == "Unknown Candidate"


def test_tc_g_06_unrecognized_and_quotes(language):
    extraction = ExtractionResult(
        name="Peter Parker",
        experience=[Experience(1, 'building "spider" tools')],
        items=[ExtractedItem("Git", Category.TOOL, 0, 3)],
    )
    normalization = NormalizationResult({"Git": "GIT"}, ["GIT"], ["Web Slinging"])
    text = CandidateProfileBuilder().build(extraction, normalization, all_rejected())
    assert "1 year \"building 'spider' tools\"" in text
    assert 'unrecognized: "Web Slinging";' in text
    language.parse(text)


def test_tc_g_07_rejected_without_missing_stage():
    classification = ClassificationResult(
        {"DATA_ENGINEER": ProfileVerdict("DATA_ENGINEER", False, (), None)}
    )
    text = CandidateProfileBuilder().build(ExtractionResult(name="Ann Lee"),
                                           NormalizationResult(), classification)
    assert "DATA_ENGINEER: REJECTED;" in text


# --------------------------------------------------------------------------- #
# 2.2 CandidateProfileLanguage — valid documents
# --------------------------------------------------------------------------- #
def test_tc_g_08_valid_document_model(language, valid_cpl_text):
    model = language.parse(valid_cpl_text)
    assert model.name == "Peter Benjamin Parker"
    assert [e.value for e in model.contact.entries] == [
        "peter.parker@dailybugle.com", "+1 (212) 555-0147", "https://github.com/peter-parker",
    ]
    assert [d.title for d in model.education.degrees] == [
        "B.Sc. in Computer Science", "Master of Science in Artificial Intelligence",
    ]
    assert [(e.years, e.field) for e in model.experience.entries] == [
        (1, "as an intern"), (4, "developing web applications"), (2, ""),
    ]
    first = model.skills.groups[0]
    assert first.category == "programming_language"
    assert [(s.token, s.aliases) for s in first.skills] == [
        ("JAVASCRIPT", ["JS", "JavaScript"]), ("PYTHON", ["Python"]),
    ]
    assert model.skills.groups[1].skills[-1].aliases == []  # NUMPY has no aliases
    assert model.skills.unrecognized.values == ["web slinging", "photography"]


def test_tc_g_09_valid_document_verdicts(language, valid_cpl_text):
    verdicts = language.parse(valid_cpl_text).classification.verdicts
    assert [(v.profile, v.status) for v in verdicts] == [
        ("FULL_STACK_DEVELOPER", "ACCEPTED"),
        ("MACHINE_LEARNING_ENGINEER", "REJECTED"),
        ("DEVOPS_ENGINEER", "REJECTED"),
        ("DATA_ENGINEER", "REJECTED"),
    ]
    assert verdicts[0].sequence == ["JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"]
    assert [v.missing for v in verdicts[1:]] == ["ML_FRAMEWORK", "OS_SCRIPTING", None]


def test_tc_g_10_layout_and_comments_are_insignificant(language, valid_cpl_text):
    no_comments = re.sub(r"(^|\s)//.*$", "", valid_cpl_text, flags=re.MULTILINE)
    one_line = " ".join(no_comments.split())
    assert "//" not in one_line.replace("https://", "")
    a, b = language.parse(valid_cpl_text), language.parse(one_line)
    assert a.name == b.name
    assert [v.profile for v in a.classification.verdicts] == [
        v.profile for v in b.classification.verdicts
    ]


def test_tc_g_11_minimal_document(language):
    text = 'candidate "Ann Lee" { skills { } classification { DATA_ENGINEER: REJECTED; } }'
    model = language.parse(text)
    assert model.contact is None and model.education is None and model.experience is None
    assert model.skills.groups == []


@pytest.mark.parametrize("resume", RESUMES, ids=[r.stem for r in RESUMES])
def test_tc_g_12_every_sample_resume_is_valid(profile_processor, stage_outputs, resume):
    extraction, normalization, classification = stage_outputs(resume.read_text(encoding="utf-8"))
    profile = profile_processor.process(extraction, normalization, classification)
    model = profile.model
    assert model.name == (extraction.name or UNKNOWN_NAME)
    declared = {s.token for g in model.skills.groups for s in g.skills}
    assert declared == set(normalization.canonical)
    accepted = [v.profile for v in model.classification.verdicts if v.status == "ACCEPTED"]
    assert accepted == classification.accepted_profiles


def test_tc_g_13_save_and_parse_file(language, profile_processor, wednesday_text, tmp_path):
    profile = profile_processor.process_resume(wednesday_text)
    path = profile.save(tmp_path / "out" / f"wednesday{CPL_EXTENSION}")
    assert path.read_text(encoding="utf-8") == WEDNESDAY_CPL
    assert language.parse_file(path).name == "Wednesday Addams"


def test_tc_g_14_grammar_file():
    assert GRAMMAR_PATH.is_file()
    assert "CandidateProfile:" in GRAMMAR_PATH.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# 2.3 Lexical errors — a terminal does not match its regular expression
# --------------------------------------------------------------------------- #
LEXICAL = {
    "email_without_at": ('"peter.parker@dailybugle.com"', '"peter.parker.dailybugle.com"'),
    "email_without_tld": ('"peter.parker@dailybugle.com"', '"peter.parker@dailybugle"'),
    "phone_with_letters": ('"+1 (212) 555-0147"', '"+1 (212) CALL-NOW"'),
    "url_without_domain": ('"https://github.com/peter-parker"', '"github/peter-parker"'),
    "name_with_digits": ('"Peter Benjamin Parker"', '"Peter Parker 2"'),
    "lowercase_token": ("JAVASCRIPT (", "javascript ("),
    "lowercase_status": ("ACCEPTED via", "accepted via"),
    "years_not_integer": ("4 years", "four years"),
    "unterminated_string": ('degree "B.Sc. in Computer Science"', 'degree "B.Sc. in Computer Science'),
}


@pytest.mark.parametrize("old, new", LEXICAL.values(), ids=LEXICAL.keys())
def test_tc_g_15_lexical_errors_are_rejected(language, valid_cpl_text, old, new):
    with pytest.raises(ProfileValidationError):
        language.parse(mutate(valid_cpl_text, old, new))


# --------------------------------------------------------------------------- #
# 2.4 Syntactic errors — the token sequence is not derivable from the grammar
# --------------------------------------------------------------------------- #
SYNTACTIC = {
    "missing_semicolon": ('tool: GIT ("Git");', 'tool: GIT ("Git")'),
    "missing_closing_brace": ("    }\n    skills", "    skills"),
    "trailing_comma": ('PYTHON ("Python");', 'PYTHON ("Python"),;'),
    "misspelled_keyword": ("    skills {", "    skils {"),
    "unknown_category": ("database:", "databases:"),
    "unknown_contact_kind": ('link "https', 'url "https'),
    "accepted_without_sequence": ("ACCEPTED via JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT;",
                                  "ACCEPTED;"),
    "rejected_with_sequence": ("DEVOPS_ENGINEER: REJECTED missing OS_SCRIPTING;",
                               "DEVOPS_ENGINEER: REJECTED via GIT;"),
    "empty_alias_list": ('NUMPY;', 'NUMPY ();'),
    "empty_education": ('degree "B.Sc. in Computer Science"\n        degree '
                        '"Master of Science in Artificial Intelligence"', ""),
}


@pytest.mark.parametrize("old, new", SYNTACTIC.values(), ids=SYNTACTIC.keys())
def test_tc_g_16_syntactic_errors_are_rejected(language, valid_cpl_text, old, new):
    with pytest.raises(ProfileValidationError):
        language.parse(mutate(valid_cpl_text, old, new))


@pytest.mark.parametrize("suffix", ["extra", "}", 'candidate "Ann Lee" { }'])
def test_tc_g_17_text_after_document(language, valid_cpl_text, suffix):
    with pytest.raises(ProfileValidationError):
        language.parse(valid_cpl_text + suffix)


def test_tc_g_18_section_order_is_fixed(language, valid_cpl_text):
    start, end = valid_cpl_text.index("    contact {"), valid_cpl_text.index("    education {")
    contact = valid_cpl_text[start:end]
    swapped = valid_cpl_text.replace(contact, "", 1).replace(
        "    skills {", contact + "    skills {", 1
    )
    with pytest.raises(ProfileValidationError):
        language.parse(swapped)


@pytest.mark.parametrize("section", ["skills", "classification"])
def test_tc_g_19_mandatory_sections(language, section):
    parts = {
        "skills": "skills { }",
        "classification": "classification { DATA_ENGINEER: REJECTED; }",
    }
    del parts[section]
    text = 'candidate "Ann Lee" { ' + " ".join(parts.values()) + " }"
    with pytest.raises(ProfileValidationError):
        language.parse(text)


def test_tc_g_20_empty_classification(language):
    with pytest.raises(ProfileValidationError):
        language.parse('candidate "Ann Lee" { skills { } classification { } }')


# --------------------------------------------------------------------------- #
# 2.5 Semantic errors — well-formed but inconsistent with Stages 2 and 3
# --------------------------------------------------------------------------- #
SEMANTIC = {
    "unknown_canonical_token": (("PYTHON (", "COBOL ("), "Unknown canonical qualification"),
    "duplicate_skill": (('tool: GIT ("Git");', 'tool: GIT ("Git"), PYTHON;'), "declared twice"),
    "unknown_profile": (("DATA_ENGINEER: REJECTED;", "QA_ENGINEER: REJECTED;"),
                        "Unknown profile"),
    "duplicate_profile": (("DATA_ENGINEER: REJECTED;", "DEVOPS_ENGINEER: REJECTED;"),
                          "classified twice"),
    "accepted_token_not_declared": (("POSTGRESQL, GIT;", "MYSQL, GIT;"),
                                    "not a declared skill"),
    "accepted_token_outside_alphabet": (("POSTGRESQL, GIT;", "POSTGRESQL, GIT, PANDAS;"),
                                        "not in the profile alphabet"),
    "forged_acceptance": (("JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT;",
                           "JAVASCRIPT, REACT, POSTGRESQL, GIT;"),
                          "does not satisfy the profile pattern"),
    "forged_rejection": (("FULL_STACK_DEVELOPER: ACCEPTED via JAVASCRIPT, REACT, NODE_JS, "
                          "POSTGRESQL, GIT;", "FULL_STACK_DEVELOPER: REJECTED;"),
                         "skills satisfy the pattern"),
    "unknown_missing_stage": (("missing OS_SCRIPTING", "missing KUBERNETES_SKILLS"),
                              "unknown stage"),
    "zero_years": (("2 years\n", "0 years\n"), "Years of experience"),
    "too_many_years": (("4 years", "61 years"), "Years of experience"),
    "phone_too_short": (('"+1 (212) 555-0147"', '"12 34 56"'), "digits"),
    "phone_too_long": (('"+1 (212) 555-0147"', '"+1 (212) 555-0147 0000 00"'), "digits"),
}


@pytest.mark.parametrize("change, message", SEMANTIC.values(), ids=SEMANTIC.keys())
def test_tc_g_21_semantic_errors_are_rejected(language, valid_cpl_text, change, message):
    with pytest.raises(ProfileValidationError, match=message):
        language.parse(mutate(valid_cpl_text, *change))


# --------------------------------------------------------------------------- #
# 2.6 Error reporting
# --------------------------------------------------------------------------- #
def test_tc_g_22_error_has_location(language, valid_cpl_text):
    with pytest.raises(ProfileValidationError) as info:
        language.parse(mutate(valid_cpl_text, "PYTHON (", "COBOL ("))
    assert (info.value.line, info.value.col) == (18, 64)
    assert "(line 18, col 64)" in str(info.value)


def test_tc_g_23_is_valid(language, valid_cpl_text):
    assert language.is_valid(valid_cpl_text)
    assert not language.is_valid("")
    assert not language.is_valid(mutate(valid_cpl_text, "PYTHON (", "COBOL ("))


def test_tc_g_24_processor_rejects_invalid_generated_text(profile_processor, wednesday_text,
                                                          monkeypatch):
    monkeypatch.setattr(CandidateProfileBuilder, "build", lambda self, *a: "candidate {")
    with pytest.raises(ProfileValidationError):
        profile_processor.process_resume(wednesday_text)
