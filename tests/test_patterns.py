"""Stage 3 — Declarative qualification patterns and their validation."""

from __future__ import annotations

import pytest

from resume_lens.normalization import PROFILES
from resume_lens.recognition import PATTERNS, PatternStage, ProfilePattern, get_pattern


def test_tc_r_01_one_pattern_per_profile():
    assert list(PATTERNS) == list(PROFILES)


@pytest.mark.parametrize("name", list(PATTERNS))
def test_tc_r_02_pattern_tokens_are_the_tokens_of_the_profile_order(name):
    assert sorted(PATTERNS[name].tokens) == sorted(PROFILES[name].tokens)


@pytest.mark.parametrize("name", list(PATTERNS))
def test_tc_r_03_stages_follow_the_canonical_order_of_the_profile(name):
    order = PROFILES[name]
    ranks = [order.rank(token) for token in PATTERNS[name].tokens]
    assert ranks == sorted(ranks)


def test_tc_r_04_get_pattern_is_case_insensitive():
    assert get_pattern(" full_stack_developer ") is PATTERNS["FULL_STACK_DEVELOPER"]


def test_tc_r_05_get_pattern_rejects_unknown_profile():
    with pytest.raises(ValueError, match="Unknown profile"):
        get_pattern("ASTRONAUT")


def test_tc_r_06_stage_needs_a_required_token():
    with pytest.raises(ValueError, match="required token"):
        PatternStage("EMPTY", ())


def test_tc_r_07_token_cannot_be_required_and_optional():
    with pytest.raises(ValueError, match="required and optional"):
        PatternStage("BAD", ("GIT",), ("GIT",))


def test_tc_r_08_stages_must_have_disjoint_tokens():
    a = PatternStage("A", ("GIT",))
    b = PatternStage("B", ("GIT", "DOCKER"))
    with pytest.raises(ValueError, match="disjoint"):
        ProfilePattern("X", (a, b))  # overlapping stages: the DFA would be nondeterministic


def test_tc_r_09_pattern_needs_at_least_one_stage():
    with pytest.raises(ValueError, match="at least one stage"):
        ProfilePattern("X", ())
