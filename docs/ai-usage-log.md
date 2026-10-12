# Generative AI Usage Log

ResumeLens · Computación y Estructuras Discretas III · 2026-2

The assignment allows AI use at level **3 — Colaboración con IAG**: students may use generative AI to complete
tasks and improve deliverables, but must keep a record of their interactions, including **their own content
given to the AI and the prompts used**, and must be able to modify and explain the results.

Each entry below records:
- the prompt, quoted exactly as written;
- the material the team provided;
- the decisions the team made;
- what the AI produced;
- how the team reviewed and changed it.

| # | Date | Tool | Task |
|---|---|---|---|
| 1 | 2026-10-12 | Claude (Claude Code, VS Code extension) | Audit of the required documentation and of the implementation against the assignment PDF |
| 2 | 2026-10-12 | Claude | Sample résumés for testing: a very good and a very bad Full Stack Developer résumé |

---

## 1. Documentation and implementation audit

### Prompt

> I need you take a look and list all the documentation needed for the project that is specified in the pdf,
> and also check if we are missing something from the implementation part.

### Team content provided

- The assignment statement `Integrative-Task1-2026-2_CyED3.pdf` (attached to the prompt).
- The project repository as it was at that moment: Stages 1–4, the tests, and the existing documents in `docs/`.

### Team decisions

Before any change, the AI asked two questions. The team answered:

| Question | Team answer |
|---|---|
| The PDF asks for "the model, UI, and tests". Should a graphical UI be added? | **No.** The command line plus the HTML report counts as the UI. |
| Which documents should the AI write? | Formal documents for Stages 1, 3 and 4; the module design document; the Stage 3 test design. The poster, presentation and literature review stay with the team. |

### Plan proposed by the AI (excerpt)

The AI produced a checklist of what the PDF requires, the status of each item, and a list of work. Shortened
version:

**Documentation required by the PDF**

| # | Requirement | Status found |
|---|---|---|
| D1 | Stage 1: each regular expression and the language it recognizes | Only in code, no document |
| D2 | Stage 2: 7-tuple and diagram of every transducer | Done; one broken diagram link and an outdated note about a deleted generator |
| D4 | Stage 3: 5-tuple, type (DFA/NFA/ε-NFA) with justification, diagram and pattern of every automaton | Missing |
| D5 | Stage 4: EBNF grammar, terminals and non-terminals, structural characteristics | Missing |
| D6 | Design 2a: modules, functions, inputs and outputs | Missing |
| D7 | Design 2c: test cases and scenarios | Stages 1, 2 and 4 done; Stage 3 missing |
| T1–T4 | Poster, presentation, literature review, AI usage log | Team deliverables |
| T5 | ≥ 10 meaningful commits, ≥ 2 h apart | Some commits less than 2 h apart; recent work not committed |

**Implementation problems found**

| # | Problem |
|---|---|
| I2 | `from resume_lens.recognition import *` failed: `__all__` listed two names that do not exist (`set_label`, `to_dot`) |
| I3 | An all-caps name (`ALEX MORGAN` in `good.txt`) was not detected, so the job title "Full Stack Developer" was taken as the name |
| I4 | The same GitHub account was extracted twice (`github.com/amorgan-dev` and `github.com/amorgan-dev/`) |

**Work plan**

1. Fix I2–I4, with new tests `TC-E-27` to `TC-E-29`.
2. Repair the Stage 2 document (broken diagram, outdated note).
3. Write `stage1-extraction-regex.md`, `stage3-recognition-automata.md`,
   `stage4-candidate-profile-language.md`, `module-design.md` and `test-design-stage-3.md`, taking every
   definition from the code.
4. Link the new documents from the README.

**Verification planned**

- Run all tests.
- Check every Markdown link.
- Run the sample résumés through the command line.
- Check the Stage 3 tables automatically against `ProfileAutomaton.formal_definition()`.

### Result

- The three implementation problems were fixed and covered by new tests (608 tests passing).
- The five documents listed in the plan were written, and the Stage 2 document was repaired.
- The Stage 3 5-tuples were generated from the code and checked against it.

### Team review and modifications

After reading the result, the team asked for three corrections:

> Try to nomalize the usage of diagrams only plantuml or maermaid and also the transition diagrams of the
> automatons are not that clear about the text that take them to the loop or the next state as shown in the
> image. and fix the numbering of the tests

1. **One diagram format.** All diagrams were converted to PlantUML with rendered SVG, the same format as the
   existing transducer diagrams (`docs/automata/`, `docs/diagrams/`).
2. **Clearer automaton diagrams.** Labels were redesigned:
   - each forward edge shows `R_i (stage)` and its required tokens;
   - each loop shows only `R_i ∪ {optional tokens}`.
3. **Test numbering.** `TC-R-22`…`31` were renumbered to `TC-R-17`…`26` (there was a gap), and `TC-G-16b`
   became `TC-G-17`, shifting the following IDs.

---

## 2. Sample résumés: a very good and a very bad Full Stack Developer

### Prompt

> give me a txt example of a very good full stack developer resume and a very bad one

### Team content provided

None besides the prompt. The purpose was to have two realistic inputs, beyond the short examples of the
assignment, to test the whole pipeline.

### Result

Two plain-text résumés, saved in `tests/resources/`:

| File | Content | Purpose in the project |
|---|---|---|
| `good.txt` | "Alex Morgan": summary, technical skills grouped by area (TypeScript, React, Next.js, Node.js, PostgreSQL, Redis, Docker, AWS, ...), two jobs with measurable results, a project, education and a certification | A complete, realistic résumé that should be ACCEPTED for Full Stack Developer |
| `bad.txt` | "Chad 'The Code Ninja' Johnson": vague skills ("Computer", "Databases", "Backend"), incorrect claims ("Java and JavaScript are basically the same"), no measurable experience, unfinished projects, irrelevant personal data | A poorly written résumé, to check how the pipeline behaves when information is vague or badly formatted |

### Team review and use

The team ran both files through the pipeline:

```bash
python main.py --resume tests/resources/good.txt --profile FULL_STACK_DEVELOPER
python main.py --resume tests/resources/bad.txt --profile FULL_STACK_DEVELOPER
```

- `good.txt` is ACCEPTED for FULL_STACK_DEVELOPER.
- `bad.txt` is not accepted for any profile. For Full Stack it is REJECTED, missing BACKEND_TECHNOLOGY:
  it names frontend frameworks but no concrete backend technology.
  - Its name line contains quotes, so no name is detected and the profile uses `Unknown Candidate`.
  - This case is checked by `TC-G-12` (every sample résumé gives a valid profile).
- `good.txt` exposed two Stage 1 bugs: the all-caps name and the duplicated link (I3 and I4 in entry 1).
  Both were fixed, and `good.txt` is now used by test `TC-E-27`.
