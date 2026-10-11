"""ResumeLens — Formal language-based résumé screening."""

from __future__ import annotations

import argparse
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    from .pipeline import ResumeLensPipeline

    parser = argparse.ArgumentParser(prog="resume-lens")
    parser.add_argument("--resume", required=True, help="Path to a .txt résumé")
    parser.add_argument("--profile", default="FULL_STACK_DEVELOPER")
    parser.add_argument("--out", help="Optional path to save the Stage 1 JSON")
    args = parser.parse_args(argv)

    output = ResumeLensPipeline().run(Path(args.resume).read_text(encoding="utf-8"), args.profile)
    if args.out:
        output.extraction.save_json(args.out)

    print("Stage 1 - extracted:", ", ".join(output.extraction.qualifications))
    print("Stage 2 - normalized:", ", ".join(output.normalization.canonical))
    if output.normalization.unrecognized:
        print("Stage 2 - unrecognized:", ", ".join(output.normalization.unrecognized))
    print(f"Stage 2 - sorted for {output.profile}:", ", ".join(output.sorted_qualifications))
