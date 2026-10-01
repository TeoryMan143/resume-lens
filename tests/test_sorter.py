"""Stage 2 — Sorting the normalized output in the profile's canonical order.

Test IDs (TC-N-xx) match docs/test-design-stages-1-2.md, section 2.4.
"""

from __future__ import annotations

from itertools import permutations

import pytest

from resume_lens.normalization import (
    FULL_STACK_DEVELOPER,
    MACHINE_LEARNING_ENGINEER,
    PROFILES,
    get_profile,
)


def test_tc_n_23_statement_full_stack_order(sorter):
    tokens = ["GIT", "NODE_JS", "JAVASCRIPT", "POSTGRESQL", "REACT"]
    assert sorter.sort(tokens, FULL_STACK_DEVELOPER) == [
        "JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT",
    ]


def test_tc_n_24_order_independence(sorter):
    tokens = ["GIT", "NODE_JS", "JAVASCRIPT", "POSTGRESQL", "REACT"]
    outputs = {tuple(sorter.sort(p, FULL_STACK_DEVELOPER)) for p in permutations(tokens)}
    assert outputs == {("JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT")}


def test_tc_n_25_ml_order(sorter):
    tokens = ["GIT", "POSTGRESQL", "TENSORFLOW", "PANDAS", "PYTHON"]
    assert sorter.sort(tokens, MACHINE_LEARNING_ENGINEER) == [
        "PYTHON", "PANDAS", "TENSORFLOW", "POSTGRESQL", "GIT",
    ]


def test_tc_n_26_tokens_outside_profile_go_last(sorter):
    tokens = ["PYTHON", "GIT", "DOCKER", "REACT"]
    assert sorter.sort(tokens, FULL_STACK_DEVELOPER) == ["REACT", "GIT", "DOCKER", "PYTHON"]


def test_tc_n_27_duplicates_and_empty(sorter):
    assert sorter.sort(["GIT", "GIT", "REACT"], FULL_STACK_DEVELOPER) == ["REACT", "GIT"]
    assert sorter.sort([], FULL_STACK_DEVELOPER) == []


def test_tc_n_28_profile_by_name(sorter):
    assert sorter.sort(["GIT", "PYTHON"], " machine_learning_engineer ") == ["PYTHON", "GIT"]
    assert get_profile("full_stack_developer") is FULL_STACK_DEVELOPER
    with pytest.raises(ValueError):
        sorter.sort(["GIT"], "DATA_SCIENTIST")


@pytest.mark.parametrize("profile", list(PROFILES.values()), ids=list(PROFILES))
def test_tc_n_29_profile_tokens_are_unique(profile):
    assert len(profile.tokens) == len(set(profile.tokens))
