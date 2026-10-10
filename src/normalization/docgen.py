"""Generates the Stage 2 formal documentation from the implemented transducers.

The 7-tuples, transition tables and diagrams are produced from the same
pyformlang objects the program uses, so the documentation cannot drift away
from the code.  Usage::

    python -m resume_lens.normalization.docgen            # writes into ./docs
    python -m resume_lens.normalization.docgen path/to/docs

It writes ``stage2-normalization-fst.md`` plus ``fst/T_<NAME>.dot`` for every
transducer, and ``fst/T_<NAME>.svg`` when Graphviz (``dot``) is installed.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .catalog import CANONICAL_VARIANTS
from .normalizer import QualificationNormalizer
from .profiles import PROFILES
from .sorter import QualificationSorter
from .transducers import (
    DIGITS,
    EPSILON,
    KEPT_SYMBOLS,
    LOWER,
    SEPARATORS,
    UPPER,
    CleaningTransducer,
    FormalDefinition,
    QualificationTransducer,
)

DOC_NAME = "stage2-normalization-fst.md"
FIG_DIR = "fst"
EPS = "ε"

# Example used for each profile in the sorting section (raw Stage 1 strings).
PROFILE_EXAMPLES = {
    "FULL_STACK_DEVELOPER": ["Git", "NodeJS", "JS", "Postgres", "React.js"],
    "MACHINE_LEARNING_ENGINEER": ["Git", "PostgreSQL", "TensorFlow", "Pandas", "Python"],
    "DEVOPS_ENGINEER": ["Kubernetes", "Terraform", "GitHub Actions", "Linux", "Docker", "AWS", "Git"],
    "DATA_ENGINEER": ["Airflow", "Apache Spark", "Python", "SQL", "Snowflake", "Kafka", "Git"],
}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _state_key(state: str) -> tuple[int, int]:
    if state == QualificationTransducer.FINAL:
        return (1, 0)
    return (0, int(state[1:]))


def _sym(symbol: str) -> str:
    return EPS if symbol == EPSILON else symbol


def _out(output: tuple) -> str:
    return EPS if not output else " ".join(output)


def _set(items) -> str:
    return "{" + ", ".join(items) + "}"


def _code_set(items) -> str:
    return "{" + ", ".join(f"`{i}`" for i in items) + "}"


def transducer_name(canonical: str) -> str:
    return f"T_{canonical}"


def ordered_transitions(fd: FormalDefinition) -> list[tuple[str, str, str, tuple]]:
    rows = [(q, a, fd.delta[(q, a)], fd.omega[(q, a)]) for (q, a) in fd.delta]
    return sorted(rows, key=lambda r: (_state_key(r[0]), r[1] == EPSILON, r[1]))


# --------------------------------------------------------------------------- #
# Graphviz
# --------------------------------------------------------------------------- #
def qualification_dot(t: QualificationTransducer) -> str:
    fd = t.formal_definition()
    lines = [
        f'digraph "{transducer_name(t.canonical)}" {{',
        "  rankdir=LR;",
        '  graph [fontname="Helvetica", labelloc=t, fontsize=14, '
        f'label="{transducer_name(t.canonical)}: {{{", ".join(t.cleaned_variants)}}} → {t.canonical}"];',
        '  node [shape=circle, fontname="Helvetica", fontsize=11];',
        '  edge [fontname="Helvetica", fontsize=10];',
        '  start [shape=point, width=0];',
        f"  {QualificationTransducer.FINAL} [shape=doublecircle];",
        f"  start -> {fd.initial_state};",
    ]
    for q, a, p, out in ordered_transitions(fd):
        lines.append(f'  {q} -> {p} [label="{_sym(a)} / {_out(out)}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"


def cleaning_dot() -> str:
    return "\n".join([
        'digraph "T_clean" {',
        "  rankdir=LR;",
        '  graph [fontname="Helvetica", labelloc=t, fontsize=14, '
        'label="T_clean: case folding and separator removal"];',
        '  node [shape=doublecircle, fontname="Helvetica", fontsize=11];',
        '  edge [fontname="Helvetica", fontsize=10];',
        '  start [shape=point, width=0];',
        "  start -> q0;",
        '  q0:n -> q0:n [label="x / lower(x)   for x ∈ {A,…,Z}"];',
        '  q0:e -> q0:e [label="x / x   for x ∈ {a,…,z} ∪ {0,…,9} ∪ {+, #}"];',
        '  q0:s -> q0:s [label="x / ε   for x ∈ {␣, -, ., _, /}"];',
        "}",
    ]) + "\n"


def write_figure(dot_source: str, stem: str, fig_dir: Path) -> bool:
    """Writes ``stem.dot``; renders ``stem.svg`` if Graphviz is available."""
    fig_dir.mkdir(parents=True, exist_ok=True)
    dot_file = fig_dir / f"{stem}.dot"
    dot_file.write_text(dot_source, encoding="utf-8")
    executable = shutil.which("dot")
    if executable is None:
        return False
    subprocess.run([executable, "-Tsvg", str(dot_file), "-o", str(fig_dir / f"{stem}.svg")],
                   check=True)
    return True


# --------------------------------------------------------------------------- #
# Markdown sections
# --------------------------------------------------------------------------- #
def _intro(n: int, n_variants: int) -> list[str]:
    return [
        "# Stage 2 — Qualification Normalization with Finite-State Transducers",
        "",
        "> This file is generated from the code by "
        "`python -m resume_lens.normalization.docgen`. "
        "Do not edit it by hand: change `catalog.py` / `profiles.py` and regenerate.",
        "",
        "## 1. Model",
        "",
        "Every transducer is a 7-tuple **M = (Q, Σ, Γ, δ, ω, q0, F)** where",
        "",
        "| Component | Meaning |",
        "|---|---|",
        "| Q | finite set of states |",
        "| Σ | input alphabet (characters) |",
        "| Γ | output alphabet |",
        "| δ ⊆ Q × (Σ ∪ {ε}) × Q | transition relation |",
        "| ω : δ → Γ* | output relation: the string written when a transition is taken |",
        "| q0 ∈ Q | initial state |",
        "| F ⊆ Q | set of accepting states |",
        "",
        "A word w is translated into y when there is a path from q0 to a state of F that reads w "
        "and writes y. δ is **partial**: any pair (q, a) not listed in a table has no "
        "transition, so a word that needs it is rejected (the transducer produces no output).",
        "",
        "Normalization is a **cascade of two transducers**:",
        "",
        "```",
        "raw string ──T_clean──▶ cleaned string ──T_norm──▶ canonical token",
        '"Scikit-learn"          "scikitlearn"              SCIKIT_LEARN',
        "```",
        "",
        "1. **T_clean** (section 2) removes the differences that are only typographic: "
        "upper/lower case and the separators space, `-`, `.`, `_`, `/`.",
        f"2. **T_norm = T_1 ∪ T_2 ∪ … ∪ T_{n}** (section 3) is the union of one transducer per "
        f"canonical qualification ({n} transducers, {n_variants} surface variants, section 5). "
        "Each T_i is a prefix tree over the cleaned variants of its qualification: every "
        "character transition writes ε and, once a complete variant has been read, an "
        "ε-transition to the only accepting state **qF** writes the canonical token. "
        "Using a separate accepting state means a variant that is a prefix of another "
        "(`react` / `reactjs`) still writes the token exactly once.",
        "",
        "Implementation: `src/resume_lens/normalization/transducers.py` "
        "(`CleaningTransducer`, `QualificationTransducer`, `union_of`) built with "
        "`pyformlang.fst.FST` (`add_transition`, `add_start_state`, `add_final_state`, "
        "`union`, `translate`).",
        "",
    ]


def _cleaning_section(fd: FormalDefinition, has_svg: bool) -> list[str]:
    sigma = list(UPPER) + list(LOWER) + list(DIGITS) + list(KEPT_SYMBOLS) + list(SEPARATORS)
    assert set(sigma) == set(fd.input_alphabet)
    lines = [
        "## 2. T_clean — lexical cleaning transducer",
        "",
        "M_clean = (Q, Σ, Γ, δ, ω, q0, F)",
        "",
        f"- **Q** = {{q0}}",
        "- **Σ** = {A, …, Z} ∪ {a, …, z} ∪ {0, …, 9} ∪ {`+`, `#`} ∪ {␣, `-`, `.`, `_`, `/`} "
        f"(|Σ| = {len(fd.input_alphabet)}; ␣ is the blank space)",
        "- **Γ** = {a, …, z} ∪ {0, …, 9} ∪ {`+`, `#`} "
        f"(|Γ| = {len(fd.output_alphabet)})",
        "- **q0** = q0",
        "- **F** = {q0} (q0 is accepting, so the empty word is accepted and translated to ε)",
        "- **δ** = {(q0, x, q0) | x ∈ Σ}",
        "- **ω**:",
        "",
        "| Input x | δ(q0, x) | ω(q0, x) |",
        "|---|---|---|",
        "| x ∈ {A, …, Z} | q0 | lower(x) — e.g. ω(q0, `R`) = `r` |",
        "| x ∈ {a, …, z} ∪ {0, …, 9} ∪ {`+`, `#`} | q0 | x (copied) |",
        "| x ∈ {␣, `-`, `.`, `_`, `/`} | q0 | ε (erased) |",
        "",
        "Any character outside Σ (for example `é`, `&`, `,`) has no transition, so the whole "
        "string is rejected and reported as *unrecognized*.",
        "",
    ]
    if has_svg:
        lines += ["![T_clean](fst/T_clean.svg)", ""]
    else:
        lines += ["Diagram source: [`fst/T_clean.dot`](fst/T_clean.dot)", ""]
    lines += [
        "| Input | Output |",
        "|---|---|",
        "| `Scikit-learn` | `scikitlearn` |",
        "| `React.js` | `reactjs` |",
        "| `Tensor Flow` | `tensorflow` |",
        "| `CI/CD` | `cicd` |",
        "| `C++` | `c++` |",
        "",
    ]
    return lines


def _union_section(normalizer: QualificationNormalizer) -> list[str]:
    fst = normalizer.fst
    return [
        "## 3. T_norm — union of the qualification transducers",
        "",
        "T_norm = T_1 ∪ … ∪ T_n is built with `FST.union` (pyformlang renames the states "
        "of each T_i so they are disjoint):",
        "",
        "- **Q** = Q_1 ⊎ … ⊎ Q_n (disjoint union)",
        "- **Σ** = Σ_1 ∪ … ∪ Σ_n,  **Γ** = Γ_1 ∪ … ∪ Γ_n (the set of canonical tokens)",
        "- **δ** = δ_1 ∪ … ∪ δ_n,  **ω** = ω_1 ∪ … ∪ ω_n",
        "- **Initial states** = {q0_1, …, q0_n}. This is equivalent to a single new initial "
        "state q_s with the transitions (q_s, ε, q0_i) and ω = ε for every i.",
        "- **F** = {qF_1, …, qF_n}",
        "",
        "| Measure | Value |",
        "|---|---|",
        f"| Transducers in the union | {len(normalizer.transducers)} |",
        f"| \\|Q\\| | {len(fst.states)} |",
        f"| \\|Σ\\| | {len(fst.input_symbols)} |",
        f"| \\|Γ\\| | {len(fst.output_symbols)} |",
        f"| Transitions | {fst.get_number_transitions()} |",
        f"| Initial states | {len(fst.start_states)} |",
        f"| Accepting states | {len(fst.final_states)} |",
        "",
        "The catalogue is checked when the normalizer is built: no cleaned variant may belong to "
        "two qualifications, so every accepted word has exactly one output (the translation is "
        "a function).",
        "",
    ]


def _sorting_section(normalizer: QualificationNormalizer) -> list[str]:
    sorter = QualificationSorter()
    lines = [
        "## 4. Sorting the output by profile",
        "",
        "Before Stage 3, the canonical tokens are de-duplicated and sorted by the order of the "
        "selected profile (`profiles.py`, `QualificationSorter`). Tokens that are not part of the "
        "profile are kept at the end in alphabetical order. The result therefore does not depend "
        "on the order in which the candidate wrote the skills.",
        "",
    ]
    for i, (name, profile) in enumerate(PROFILES.items(), start=1):
        origin = "predefined" if i <= 2 else "defined by the team"
        lines += [f"### 4.{i} {name} ({origin})", "", "| # | Group | Tokens (in order) |",
                  "|---|---|---|"]
        for g, (group, tokens) in enumerate(profile.groups, start=1):
            lines.append(f"| {g} | {group} | {', '.join(tokens)} |")
        example = PROFILE_EXAMPLES.get(name)
        if example:
            normalized = normalizer.normalize(example).canonical
            ordered = sorter.sort(normalized, profile)
            lines += [
                "",
                f"- Résumé: `{', '.join(example)}`",
                f"- Normalized: `{', '.join(normalized)}`",
                f"- Sorted: **`{', '.join(ordered)}`**",
            ]
        lines.append("")
    return lines


def _index_section(transducers: dict[str, QualificationTransducer]) -> list[str]:
    lines = [
        "## 5. Catalogue of qualification transducers",
        "",
        "| Transducer | Surface variants (input of T_clean) | Cleaned words (input of T_i) | \\|Q\\| | Transitions |",
        "|---|---|---|---|---|",
    ]
    for canonical, t in transducers.items():
        name = transducer_name(canonical)
        anchor = name.lower()
        lines.append(
            f"| [{name}](#{anchor}) | {', '.join(f'`{v}`' for v in t.variants)} | "
            f"{', '.join(f'`{w}`' for w in t.cleaned_variants)} | {len(t.fst.states)} | "
            f"{t.fst.get_number_transitions()} |"
        )
    lines.append("")
    return lines


def _transducer_section(t: QualificationTransducer, has_svg: bool) -> list[str]:
    fd = t.formal_definition()
    name = transducer_name(t.canonical)
    states = sorted(fd.states, key=_state_key)
    word = max(t.cleaned_variants, key=len)
    rejected = word[:-1] if word[:-1] and t.translate(word[:-1]) is None else word + "x"
    lines = [
        f"### {name}",
        "",
        f"Transforms {', '.join(f'`{v}`' for v in t.variants)} → **{t.canonical}**",
        "",
        f"M_{t.canonical} = (Q, Σ, Γ, δ, ω, q0, F)",
        "",
        f"- **Q** = {_set(states)} (|Q| = {len(states)})",
        f"- **Σ** = {_code_set(sorted(fd.input_alphabet))}",
        f"- **Γ** = {{{t.canonical}}}",
        f"- **q0** = {fd.initial_state}",
        f"- **F** = {_set(sorted(fd.final_states))}",
        "- **δ** and **ω**:",
        "",
        "| # | q | a ∈ Σ ∪ {ε} | δ(q, a) | ω(q, a) |",
        "|---|---|---|---|---|",
    ]
    for i, (q, a, p, out) in enumerate(ordered_transitions(fd), start=1):
        symbol = EPS if a == EPSILON else f"`{a}`"
        lines.append(f"| {i} | {q} | {symbol} | {p} | {_out(out)} |")
    lines += ["", "δ is undefined for every other pair (q, a)."]
    lines += [""]
    if has_svg:
        lines += [f"![{name}]({FIG_DIR}/{name}.svg)", ""]
    else:
        lines += [f"Diagram source: [`{FIG_DIR}/{name}.dot`]({FIG_DIR}/{name}.dot)", ""]
    lines += [
        f"Example: `{word}` ⟼ {t.translate(word)}; a word outside the language, such as "
        f"`{rejected}`, is rejected.",
        "",
    ]
    return lines


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #
def generate(docs_dir: str | Path = "docs") -> Path:
    docs_dir = Path(docs_dir)
    fig_dir = docs_dir / FIG_DIR
    normalizer = QualificationNormalizer(CANONICAL_VARIANTS)
    cleaner = normalizer.cleaner

    has_svg = write_figure(cleaning_dot(), "T_clean", fig_dir)
    for canonical, t in normalizer.transducers.items():
        has_svg = write_figure(qualification_dot(t), transducer_name(canonical), fig_dir) and has_svg

    n_variants = sum(len(t.variants) for t in normalizer.transducers.values())
    lines = _intro(len(normalizer.transducers), n_variants)
    lines += _cleaning_section(cleaner.formal_definition(), has_svg)
    lines += _union_section(normalizer)
    lines += _sorting_section(normalizer)
    lines += _index_section(normalizer.transducers)
    for t in normalizer.transducers.values():
        lines += _transducer_section(t, has_svg)

    out = docs_dir / DOC_NAME
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    path = generate(argv[0] if argv else "docs")
    print(f"Written {path}")
    if shutil.which("dot") is None:
        print("Graphviz 'dot' not found: only .dot sources were written (no .svg).")


if __name__ == "__main__":
    main()
