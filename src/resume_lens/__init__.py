"""ResumeLens — Formal language-based résumé screening."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    from .dsl import CandidateProfileProcessor, ProfileValidationError
    from .normalization import PROFILES
    from .pipeline import ResumeLensPipeline
    from .recognition import ProfileClassifier

    parser = argparse.ArgumentParser(prog="resume-lens")
    parser.add_argument("--resume", required=True, help="Path to a .txt résumé")
    parser.add_argument(
        "--profile", default="FULL_STACK_DEVELOPER", type=str.upper, choices=list(PROFILES)
    )
    parser.add_argument("--out", help="Optional path to save the Stage 1 JSON")
    parser.add_argument("--cpl", help="Optional path to save the Stage 4 candidate profile")
    parser.add_argument("--html", help="Optional path to save the HTML visualization")
    args = parser.parse_args(argv)

    output = ResumeLensPipeline().run(Path(args.resume).read_text(encoding="utf-8"), args.profile)
    if args.out:
        output.extraction.save_json(args.out)

    print("Stage 1 - extracted:", ", ".join(output.extraction.qualifications))
    print("Stage 2 - normalized:", ", ".join(output.normalization.canonical))
    if output.normalization.unrecognized:
        print("Stage 2 - unrecognized:", ", ".join(output.normalization.unrecognized))
    print(f"Stage 2 - sorted for {output.profile}:", ", ".join(output.sorted_qualifications))

    classification = ProfileClassifier().classify(output.normalization.canonical)
    verdict = classification.verdicts[output.profile]
    detail = f" (missing {verdict.missing_stage})" if verdict.missing_stage else ""
    print(f"Stage 3 - {output.profile}: {verdict.status}{detail}")
    print("Stage 3 - accepted profiles:", ", ".join(classification.accepted_profiles) or "none")

    try:
        profile = CandidateProfileProcessor().process(
            output.extraction, output.normalization, classification
        )
    except ProfileValidationError as e:
        print(f"Stage 4 - invalid candidate profile: {e}", file=sys.stderr)
        return 1
    print("Stage 4 - candidate profile (valid):")
    print(profile.text, end="")
    if args.cpl:
        print("Stage 4 - saved to", profile.save(args.cpl))
    if args.html:
        print("Stage 4 - HTML visualization saved to", profile.save_html(args.html))
    return 0
