"""Stage 4 — HTML visualization of a validated candidate profile.

Test IDs (TC-H-xx) match docs/test-design-stage-4.md, section 2.8.
"""

from __future__ import annotations

from html.parser import HTMLParser

import pytest

from resume_lens.dsl import ProfileHtmlRenderer, profile_label

MINIMAL = 'candidate "Ann Lee" { skills { } classification { DATA_ENGINEER: REJECTED; } }'
VOID_TAGS = {"meta", "br", "hr", "img", "input", "link"}


class TagBalance(HTMLParser):
    """Collects unbalanced tags; an empty ``errors`` list means well-formed."""

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            self.errors.append(tag)


@pytest.fixture
def render(language):
    """Parse a CPL document and render its model."""

    def _render(text: str, with_source: bool = False) -> str:
        return ProfileHtmlRenderer().render(language.parse(text), text if with_source else None)

    return _render


@pytest.fixture
def valid_html(render, valid_cpl_text) -> str:
    return render(valid_cpl_text)


def test_tc_h_01_document_and_header(valid_html):
    assert valid_html.startswith("<!DOCTYPE html>")
    assert "<title>Peter Benjamin Parker · ResumeLens</title>" in valid_html
    assert "<h1>Peter Benjamin Parker</h1>" in valid_html
    assert 'href="mailto:peter.parker@dailybugle.com"' in valid_html
    assert 'href="tel:+12125550147">+1 (212) 555-0147</a>' in valid_html
    assert 'href="https://github.com/peter-parker"' in valid_html


def test_tc_h_02_link_without_scheme(render):
    text = MINIMAL.replace("{ skills", '{ contact { link "linkedin.com/in/ann" } skills')
    assert 'href="https://linkedin.com/in/ann">linkedin.com/in/ann</a>' in render(text)


def test_tc_h_03_summary(valid_html, render):
    assert "Satisfies the qualification pattern of" in valid_html
    assert '<span class="badge accepted">Full Stack Developer</span></section>' in valid_html
    assert "Satisfies no qualification pattern" in render(MINIMAL)


def test_tc_h_04_classification(valid_html):
    section = valid_html.split("<h2>Profile classification</h2>")[1].split("</section>")[0]
    assert section.count('class="verdict-head"') == 4
    assert section.count('class="badge accepted"') == 1
    assert section.count('class="badge rejected"') == 3
    for token in ["JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"]:
        assert f'<li class="chip">{token}</li>' in section
    assert '<span class="chip">ML_FRAMEWORK</span>' in section
    assert "Pattern not satisfied." in section  # DATA_ENGINEER: REJECTED; (no stage)


def test_tc_h_05_skills(valid_html):
    section = valid_html.split("<h2>Skills</h2>")[1].split("</section>")[0]
    headings = [h.split("</h3>")[0] for h in section.split("<h3>")[1:]]
    assert headings == [
        "Programming languages", "Frameworks &amp; libraries", "Databases",
        "Tools &amp; technologies", "Not recognized",
    ]
    assert "JAVASCRIPT <small>JS, JavaScript</small>" in section
    assert '<li class="chip" title="">NUMPY</li>' in section  # no aliases
    assert "web slinging, photography" in section


def test_tc_h_06_experience_and_education(valid_html):
    assert "<li><strong>1 year</strong> — as an intern</li>" in valid_html
    assert "<li><strong>2 years</strong></li>" in valid_html
    assert "<li>B.Sc. in Computer Science</li>" in valid_html


def test_tc_h_07_optional_sections_are_omitted(render):
    html = render(MINIMAL)
    for absent in ['class="contact"', "<h2>Experience</h2>", "<h2>Education</h2>", "<details>"]:
        assert absent not in html
    assert "No qualifications were identified." in html


def test_tc_h_08_text_is_escaped(render):
    text = MINIMAL.replace(
        "{ skills { }",
        '{ education { degree "<script>alert(1)</script> & co" } '
        'skills { unrecognized: "a<b"; }',
    )
    html = render(text)
    assert "<script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; co" in html
    assert "a&lt;b" in html


def test_tc_h_09_cpl_source_is_embedded(render, valid_cpl_text):
    html = render(valid_cpl_text, with_source=True)
    assert "<summary>Candidate profile (CPL source)</summary>" in html
    assert "candidate &quot;Peter Benjamin Parker&quot; {" in html


@pytest.mark.parametrize("text", ["valid", "minimal"])
def test_tc_h_10_well_formed(render, valid_cpl_text, text):
    checker = TagBalance()
    checker.feed(render(valid_cpl_text if text == "valid" else MINIMAL, with_source=True))
    assert checker.errors == [] and checker.stack == []


def test_tc_h_11_save(profile_processor, wednesday_text, tmp_path):
    profile = profile_processor.process_resume(wednesday_text)
    path = profile.save_html(tmp_path / "out" / "wednesday.html")
    html = path.read_text(encoding="utf-8")
    assert html == profile.to_html()
    assert "<h1>Wednesday Addams</h1>" in html


@pytest.mark.parametrize("name, label", [
    ("FULL_STACK_DEVELOPER", "Full Stack Developer"),
    ("MACHINE_LEARNING_ENGINEER", "Machine Learning Engineer"),
    ("DEVOPS_ENGINEER", "DevOps Engineer"),
    ("DATA_ENGINEER", "Data Engineer"),
])
def test_tc_h_12_profile_label(name, label):
    assert profile_label(name) == label
