# Test Design — Stage 4 (Candidate Profile Language, Context-Free Grammar with textX)

ResumeLens · Computación y Estructuras Discretas III · 2026-2

This document describes the automated tests for Stage 4 of the ResumeLens pipeline and for the end-to-end
command documented in the README. Every test case has an ID (`TC-G-xx`, `TC-C-xx`) that appears in the name
of the matching pytest function.

| Scope                       | Module under test                                                                   | Test file             |
| --------------------------- | ----------------------------------------------------------------------------------- | --------------------- |
| 4. Profile generation       | `resume_lens.dsl.builder` (`CandidateProfileBuilder`)                               | `tests/test_dsl.py`   |
| 4. Profile validation       | `resume_lens.dsl.language` (`CandidateProfileLanguage`, `candidate_profile.tx`)     | `tests/test_dsl.py`   |
| 4. Stage entry point        | `resume_lens.dsl.processor` (`CandidateProfileProcessor`, `CandidateProfile`)       | `tests/test_dsl.py`   |
| 4. HTML visualization       | `resume_lens.dsl.visualization` (`ProfileHtmlRenderer`, `profile_label`)            | `tests/test_visualization.py` |
| 1 → 4 end-to-end (CLI)      | `main.py`, `resume_lens.main`                                                       | `tests/test_cli.py`   |

**How to run**

```bash
pytest -k "tc_g_"           # Stage 4 only
pytest -k "tc_h_"           # HTML visualization
pytest -k "tc_c_"           # command line (Stages 1 -> 4)
```

---

## 1. Scenario configuration

Scenarios are pytest fixtures in `tests/conftest.py`; résumés and profiles are in `tests/resources/`.
Stage 1–3 scenarios (SC-E*, SC-N*, SC-R*, SC-I*) are described in `test-design-stages-1-2.md`.

| ID    | Name (fixture)       | Class                       | Scenario                                                                                                                                                                                                                                                                                                                                       |
| ----- | -------------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SC-G1 | `language`           | `CandidateProfileLanguage`  | textX metamodel built from `candidate_profile.tx` (`autokwd=True`) with the semantic object processors; canonical tokens = `CANONICAL_VARIANTS`, patterns = the four Stage 3 `PATTERNS`.                                                                                                                                                      |
| SC-G2 | `profile_processor`  | `CandidateProfileProcessor` | `CandidateProfileBuilder` + SC-G1.                                                                                                                                                                                                                                                                                                            |
| SC-G3 | `valid_cpl_text`     | `str`                       | Content of `valid_profile.cpl`: candidate `Peter Benjamin Parker`; contact (1 e-mail, 1 phone, 1 link); 2 degrees; 3 experience entries (`1 year`, `4 years` with description, `2 years` without); skills in 4 categories, one skill without aliases (`NUMPY`), 2 unrecognized strings; verdicts: FULL_STACK ACCEPTED, ML REJECTED missing `ML_FRAMEWORK`, DEVOPS REJECTED missing `OS_SCRIPTING`, DATA_ENGINEER REJECTED (no stage); `//` comments. |
| SC-G4 | `stage_outputs`      | callable                    | Résumé text → (`ExtractionResult`, `NormalizationResult`, `ClassificationResult`) = SC-I1 followed by SC-R1.                                                                                                                                                                                                                                   |
| SC-G5 | `all_rejected()`     | `ClassificationResult`      | Helper in `test_dsl.py`: the four profiles REJECTED at the first stage of their pattern, as an empty résumé produces.                                                                                                                                                                                                                          |
| SC-C1 | `SAMPLES`            | `dict`                      | Each sample résumé and the profile it was written for: `wednesday_addams.txt` → FULL_STACK_DEVELOPER, `mary_jane_watson.txt` → MACHINE_LEARNING_ENGINEER, `devops_resume.txt` → DEVOPS_ENGINEER, `data_engineer_resume.txt` → DATA_ENGINEER.                                                                                               |

---

## 2. Test case design

### 2.1 `CandidateProfileBuilder` — Stage 1–3 outputs → CPL text

**Objective:** verify that every piece of information produced by the previous stages is written in the
right section of the document, and that the generated document is always valid.

| ID      | Method  | Scenario      | Input values                                                                 | Expected result                                                                                                       |
| ------- | ------- | ------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| TC-G-01 | `build` | SC-G4, SC-E2  | Wednesday résumé                                                             | Exactly the reference document (`WEDNESDAY_CPL`): experience, 4 skill groups, FULL_STACK ACCEPTED, 3 REJECTED with stage. |
| TC-G-02 | `build` | SC-G4, SC-E4  | `full_resume.txt`                                                            | e-mail, both phones, both links, degrees and experience present; `REST_API ("REST APIs", "RESTful APIs")`.            |
| TC-G-03 | `build` | SC-G4, SC-E2  | Wednesday résumé (no contact, no degrees)                                    | No `contact` and no `education` section.                                                                              |
| TC-G-04 | `build` | SC-G4, SC-E4  | `full_resume.txt`                                                            | Skill groups appear in the Stage 1 category order: programming_language, framework_library, database, tool, other_qualification. |
| TC-G-05 | `build` | SC-G1, SC-G5  | Empty `ExtractionResult` and `NormalizationResult`                           | Name `Unknown Candidate`; empty but present `skills { }`; document parses.                                            |
| TC-G-06 | `build` | SC-G1, SC-G5  | Experience `building "spider" tools`; unrecognized `Web Slinging`            | Double quotes become single quotes; `unrecognized: "Web Slinging";`; document parses.                                 |
| TC-G-07 | `build` | —             | Verdict REJECTED with `missing_stage=None`                                   | `DATA_ENGINEER: REJECTED;`                                                                                            |

### 2.2 `CandidateProfileLanguage` — valid documents

| ID      | Method                   | Scenario      | Input values                                     | Expected result                                                                                                     |
| ------- | ------------------------ | ------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| TC-G-08 | `parse`                  | SC-G1, SC-G3  | `valid_profile.cpl`                              | Model: unquoted name/contact values, degrees, `(years, field)` with `""` when omitted, skills with aliases, unrecognized list. |
| TC-G-09 | `parse`                  | SC-G1, SC-G3  | `valid_profile.cpl`                              | 4 verdicts with status; accepted sequence; `missing` = `ML_FRAMEWORK`, `OS_SCRIPTING`, `None`.                        |
| TC-G-10 | `parse`                  | SC-G1, SC-G3  | Same document without comments in one line       | Same model: whitespace, line breaks and comments are not significant.                                               |
| TC-G-11 | `parse`                  | SC-G1         | `candidate "Ann Lee" { skills { } classification { DATA_ENGINEER: REJECTED; } }` | Valid; optional sections are `None`, no skill groups.                                     |
| TC-G-12 | `process`                | SC-G2, SC-G4  | Every `tests/resources/*.txt` (5 résumés)        | Valid profile; model name = Stage 1 name; declared skills = Stage 2 canonical set; ACCEPTED profiles = Stage 3 accepted profiles. |
| TC-G-13 | `save`, `parse_file`     | SC-G2, SC-E5  | Wednesday résumé, `tmp/out/wednesday.cpl`        | Parent folder created; file content = `WEDNESDAY_CPL`; file parses.                                                 |
| TC-G-14 | `GRAMMAR_PATH`           | —             | —                                                | The grammar file exists and defines `CandidateProfile`.                                                             |

### 2.3 Lexical errors — a terminal does not match its regular expression

Each case applies one change to SC-G3 and expects `ProfileValidationError` (TC-G-15, parametrized).

| Case                  | Change                                              | Violated terminal  |
| --------------------- | --------------------------------------------------- | ------------------ |
| email_without_at      | `peter.parker.dailybugle.com`                       | `EmailAddress`     |
| email_without_tld     | `peter.parker@dailybugle`                           | `EmailAddress`     |
| phone_with_letters    | `+1 (212) CALL-NOW`                                 | `PhoneNumber`      |
| url_without_domain    | `github/peter-parker`                               | `Url`              |
| name_with_digits      | `Peter Parker 2`                                    | `PersonName`       |
| lowercase_token       | `javascript (`                                      | `CanonicalToken`   |
| lowercase_status      | `accepted via`                                      | keyword `ACCEPTED` |
| years_not_integer     | `four years`                                        | `INT`              |
| unterminated_string   | `degree "B.Sc. in Computer Science` (no closing `"`) | `STRING`           |

### 2.4 Syntactic errors — the token sequence cannot be derived from the grammar

Each case applies one change to SC-G3 and expects `ProfileValidationError`.

| ID       | Case                        | Change                                                        | Violated rule                                  |
| -------- | --------------------------- | ------------------------------------------------------------- | ---------------------------------------------- |
| TC-G-16  | missing_semicolon           | `tool: GIT ("Git")`                                           | `SkillGroup` ends with `';'`                   |
| TC-G-16  | missing_closing_brace       | experience section without `}`                                | `ExperienceSection`                            |
| TC-G-16  | trailing_comma              | `PYTHON ("Python"),;`                                         | `skills+=Skill[',']`                           |
| TC-G-16  | misspelled_keyword          | `skils {`                                                     | `SkillsSection`                                |
| TC-G-16  | unknown_category            | `databases:`                                                  | `SkillCategory`                                |
| TC-G-16  | unknown_contact_kind        | `url "https…"`                                                | `ContactEntry`                                 |
| TC-G-16  | accepted_without_sequence   | `FULL_STACK_DEVELOPER: ACCEPTED;`                             | `AcceptedVerdict` needs `'via' sequence+=`     |
| TC-G-16  | rejected_with_sequence      | `DEVOPS_ENGINEER: REJECTED via GIT;`                          | `RejectedVerdict`                              |
| TC-G-16  | empty_alias_list            | `NUMPY ();`                                                   | `aliases+=STRING[',']` (one or more)           |
| TC-G-16  | empty_education             | `education { }`                                               | `degrees+=Degree` (one or more)                |
| TC-G-17  | text_after_document         | `extra`, `}`, a second `candidate` appended                   | one `CandidateProfile` per document            |
| TC-G-18  | section_order               | `contact` moved after `experience`                            | fixed section order of `CandidateProfile`      |
| TC-G-19  | mandatory_sections          | document without `skills` / without `classification`          | `skills=`, `classification=` are not optional  |
| TC-G-20  | empty_classification        | `classification { }`                                          | `verdicts+=Verdict` (one or more)              |

### 2.5 Semantic errors — well-formed but inconsistent with Stages 2 and 3

Each case applies one change to SC-G3 and expects `ProfileValidationError` whose message contains the given text (TC-G-21, parametrized).

| Case                              | Change                                                   | Expected message                         |
| --------------------------------- | -------------------------------------------------------- | ---------------------------------------- |
| unknown_canonical_token           | `COBOL ("Python")`                                       | `Unknown canonical qualification`        |
| duplicate_skill                   | `GIT` declared again as `PYTHON`                         | `declared twice`                         |
| unknown_profile                   | `QA_ENGINEER: REJECTED;`                                 | `Unknown profile`                        |
| duplicate_profile                 | `DEVOPS_ENGINEER` classified twice                       | `classified twice`                       |
| accepted_token_not_declared       | accepted sequence uses `MYSQL`                           | `not a declared skill`                   |
| accepted_token_outside_alphabet   | accepted sequence adds `PANDAS` (not in Full Stack Σ)    | `not in the profile alphabet`            |
| forged_acceptance                 | Full Stack ACCEPTED without a backend token              | `does not satisfy the profile pattern`   |
| forged_rejection                  | Full Stack REJECTED although the skills satisfy it       | `skills satisfy the pattern`             |
| unknown_missing_stage             | `missing KUBERNETES_SKILLS`                              | `unknown stage`                          |
| zero_years / too_many_years       | `0 years`, `61 years`                                    | `Years of experience`                    |
| phone_too_short / phone_too_long  | `12 34 56` (6 digits), 17 digits                         | `digits`                                 |

### 2.6 Error reporting

| ID      | Method                        | Input values                                     | Expected result                                                         |
| ------- | ----------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------- |
| TC-G-22 | `parse`                       | SC-G3 with `COBOL`                               | `line == 18`, `col == 64`, message ends with `(line 18, col 64)`.       |
| TC-G-23 | `is_valid`                    | SC-G3; `""`; SC-G3 with `COBOL`                  | `True`, `False`, `False`.                                               |
| TC-G-24 | `process_resume`              | Builder patched to return `candidate {`          | `ProfileValidationError` (an invalid generated document is never returned). |

### 2.7 End-to-end — `python main.py --resume … --profile …`

| ID      | Scenario       | Input values                                                               | Expected result                                                                                   |
| ------- | -------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| TC-C-01 | SC-E2          | `python main.py --resume wednesday_addams.txt --profile FULL_STACK_DEVELOPER` in a subprocess | Exit code 0; Stage 3 ACCEPTED; valid Stage 4 profile printed.                    |
| TC-C-02 | SC-E2          | Same arguments, in process                                                 | First five lines: Stage 1 strings, Stage 2 canonical and sorted, Stage 3 verdict and accepted list. |
| TC-C-03 | SC-C1          | Each sample résumé with its profile                                        | `Stage 3 - <profile>: ACCEPTED`; it is the only accepted profile.                                 |
| TC-C-04 | SC-E2          | Wednesday + `MACHINE_LEARNING_ENGINEER`                                    | Exit code 0; `REJECTED (missing LANGUAGE)`; accepted list still `FULL_STACK_DEVELOPER`.           |
| TC-C-05 | SC-E4          | `full_resume.txt`                                                          | `accepted profiles: none`; the profile is still generated and valid.                              |
| TC-C-06 | SC-E2          | `--profile full_stack_developer`                                           | Treated as `FULL_STACK_DEVELOPER`.                                                                |
| TC-C-07 | SC-E2          | No `--profile`                                                             | Default `FULL_STACK_DEVELOPER`.                                                                   |
| TC-C-08 | SC-E2          | `--profile QA_ENGINEER`                                                    | `SystemExit(2)`, `invalid choice` on stderr.                                                      |
| TC-C-09 | SC-E2, SC-E5   | `--cpl tmp/profiles/wednesday.cpl`                                         | File saved (folder created); its content is the printed profile and parses.                      |
| TC-C-10 | SC-E3, SC-E5   | `--out tmp/stage1.json`                                                    | Stage 1 JSON still written.                                                                       |
| TC-C-11 | SC-E5          | Résumé without a name line                                                 | `candidate "Unknown Candidate"`; FULL_STACK ACCEPTED.                                             |
| TC-C-12 | SC-E2, SC-E5   | Builder patched to return `candidate {`, `--cpl tmp/never.cpl`             | Exit code 1; error on stderr; no profile printed; no file written.                                |
| TC-C-13 | SC-E2, SC-E5   | `--html tmp/html/wednesday.html`                                           | File saved (folder created); contains the candidate name and the Full Stack accepted badge.      |

---

### 2.8 `ProfileHtmlRenderer` — HTML visualization

**Objective:** verify that the page is built only from the validated model, shows every section of the
profile, escapes all text, and is well-formed. `MINIMAL` = `candidate "Ann Lee" { skills { } classification { DATA_ENGINEER: REJECTED; } }`.

| ID      | Method                  | Scenario      | Input values                                                   | Expected result                                                                                                  |
| ------- | ----------------------- | ------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| TC-H-01 | `render`                | SC-G1, SC-G3  | `valid_profile.cpl`                                            | Doctype; `<title>`; `<h1>` name; `mailto:` e-mail; `tel:+12125550147`; link `href`.                              |
| TC-H-02 | `render`                | SC-G1         | `MINIMAL` + `link "linkedin.com/in/ann"`                        | `href="https://linkedin.com/in/ann"` (scheme added, text unchanged).                                             |
| TC-H-03 | `render`                | SC-G1, SC-G3  | `valid_profile.cpl`; `MINIMAL`                                 | Summary badge `Full Stack Developer`; `Satisfies no qualification pattern` when nothing is accepted.             |
| TC-H-04 | `render`                | SC-G1, SC-G3  | `valid_profile.cpl`                                            | 4 verdict rows (1 accepted, 3 rejected); accepted sequence as chips; missing stage `ML_FRAMEWORK`; `Pattern not satisfied.` |
| TC-H-05 | `render`                | SC-G1, SC-G3  | `valid_profile.cpl`                                            | Category headings in order, then `Not recognized`; aliases next to the token; `NUMPY` without aliases.          |
| TC-H-06 | `render`                | SC-G1, SC-G3  | `valid_profile.cpl`                                            | `1 year — as an intern`, `2 years` (no description); degrees listed.                                            |
| TC-H-07 | `render`                | SC-G1         | `MINIMAL`                                                      | No contact, experience, education or source section; `No qualifications were identified.`                       |
| TC-H-08 | `render`                | SC-G1         | degree `<script>alert(1)</script> & co`, unrecognized `a<b`     | No raw `<script>`; text appears HTML-escaped.                                                                    |
| TC-H-09 | `render`                | SC-G1, SC-G3  | `valid_profile.cpl` with source                                | `<details>` with the escaped CPL source.                                                                         |
| TC-H-10 | `render`                | SC-G1         | `valid_profile.cpl`; `MINIMAL`                                 | Every opened tag is closed in order (checked with `html.parser`).                                                |
| TC-H-11 | `save_html`, `to_html`  | SC-G2, SC-E5  | Wednesday résumé, `tmp/out/wednesday.html`                     | Folder created; file content = `to_html()`; contains `<h1>Wednesday Addams</h1>`.                                |
| TC-H-12 | `profile_label`         | —             | The four profile names                                         | `Full Stack Developer`, `Machine Learning Engineer`, `DevOps Engineer`, `Data Engineer`.                         |

---

## 3. Coverage summary

| Area                          | Tests                         |
| ----------------------------- | ----------------------------- |
| Generation (builder)          | TC-G-01 … TC-G-07             |
| Valid documents / round trip  | TC-G-08 … TC-G-14             |
| Lexical rejection             | TC-G-15 (9 cases)             |
| Syntactic rejection           | TC-G-16 … TC-G-20 (17 cases)  |
| Semantic rejection            | TC-G-21 (13 cases)            |
| Error reporting               | TC-G-22 … TC-G-24             |
| HTML visualization            | TC-H-01 … TC-H-12 (16 cases)  |
| Command line (Stages 1 → 4)   | TC-C-01 … TC-C-13 (16 cases)  |
