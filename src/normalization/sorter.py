"""Sorting of normalized qualifications in a profile's canonical order."""

from __future__ import annotations

from typing import Iterable

from .profiles import ProfileOrder, get_profile


class QualificationSorter:
    """Removes duplicates and sorts tokens by the order of a profile.

    Tokens that belong to the profile come first, in profile order; tokens that
    do not belong to it are kept at the end in alphabetical order, so the
    output never depends on the order in the résumé.
    """

    def sort(self, tokens: Iterable[str], profile: ProfileOrder | str) -> list[str]:
        if isinstance(profile, str):
            profile = get_profile(profile)
        distinct = list(dict.fromkeys(tokens))
        ranked = [t for t in distinct if profile.rank(t) is not None]
        unranked = [t for t in distinct if profile.rank(t) is None]
        return sorted(ranked, key=profile.rank) + sorted(unranked)
