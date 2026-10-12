# Test Design — Stage 3 (Qualification Pattern Recognition, Finite Automata)

ResumeLens · Computación y Estructuras Discretas III · 2026-2

This document describes the automated tests for Stage 3 of the ResumeLens pipeline. Every test case has an ID
(`TC-R-xx`) that appears in the name of the matching pytest function.

| Area | Module under test | Test file |
|---|---|---|
| Profile patterns | `resume_lens.recognition.patterns` (`PatternStage`, `ProfilePattern`, `PATTERNS`, `get_pattern`) | `tests/test_patterns.py` |
| Automata | `resume_lens.recognition.automaton` (`ProfileAutomaton`) | `tests/test_automata.py` |
| Classification of the sample résumés | `resume_lens.recognition.classifier` (`ProfileClassifier`, `ClassificationResult`) | `tests/test_classifier_resumes.py` |
| Edited résumés | `ProfileClassifier` through Stages 1–3 | `tests/test_classifier_variants.py` |

**How to run**

```bash
pytest -k "tc_r_"        # 64 test executions (parametrized cases included)
```

---

## 1. Scenario configuration

Scenarios are pytest fixtures in `tests/conftest.py`. Stage 1 and 2 scenarios (`SC-E*`, `SC-N*`, `SC-I*`) are
described in [`test-design-stages-1-2.md`](test-design-stages-1-2.md).

| ID | Name (fixture) | Class | Scenario |
|---|---|---|---|
| SC-R1 | `classifier` | `ProfileClassifier` | `ProfileClassifier()` with the four patterns of `PATTERNS` and the four orders of `PROFILES`. |
| SC-R2 | `automata` | `dict[str, ProfileAutomaton]` | One `ProfileAutomaton` per profile, built from `PATTERNS`: FULL_STACK_DEVELOPER (q0–q5), MACHINE_LEARNING_ENGINEER (q0–q5), DEVOPS_ENGINEER (q0–q6), DATA_ENGINEER (q0–q5). |
| SC-R3 | `classify` | callable | Résumé text → Stage 1 + Stage 2 (SC-I1) → canonical tokens → `classifier.classify` (SC-R1) → `ClassificationResult`. |
| SC-R4 | `VARIANTS` (in `test_classifier_variants.py`) | list | 11 edits of the sample résumés: one skill removed or replaced (table in 2.4). |

Résumés used: `wednesday_text` (SC-E2), `mary_jane_text` (SC-E3), `full_resume_text` (SC-E4).

---

## 2. Test case design

### 2.1 Profile patterns — `PatternStage`, `ProfilePattern`

**Objective:** verify that the four patterns are well defined: one per profile, the same vocabulary and order
as Stage 2, and that invalid patterns (which would give a nondeterministic or empty automaton) are refused.

| ID | Class | Method | Scenario | Input values | Expected result |
|---|---|---|---|---|---|
| TC-R-01 | ProfilePattern | `PATTERNS` | — | The pattern registry | Same profile names, in the same order, as `PROFILES` |
| TC-R-02 | ProfilePattern | `tokens` | — | Each of the 4 patterns | The pattern alphabet Σ has exactly the tokens of the profile order |
| TC-R-03 | ProfilePattern | `tokens` | — | Each of the 4 patterns | Ranks of the tokens in the profile order are non-decreasing: stages follow the Stage 2 order |
| TC-R-04 | — | `get_pattern` | — | `" full_stack_developer "` | The FULL_STACK_DEVELOPER pattern (spaces and case ignored) |
| TC-R-05 | — | `get_pattern` | — | `"ASTRONAUT"` | `ValueError("Unknown profile …")` |
| TC-R-06 | PatternStage | constructor | — | `PatternStage("EMPTY", ())` | `ValueError` (a stage needs a required token) |
| TC-R-07 | PatternStage | constructor | — | `GIT` both required and optional | `ValueError` |
| TC-R-08 | ProfilePattern | constructor | — | Stages A = {GIT} and B = {GIT, DOCKER} | `ValueError(… disjoint)`: overlapping stages would make δ(q, GIT) have two targets |
| TC-R-09 | ProfilePattern | constructor | — | No stages | `ValueError` |

### 2.2 Automata — `ProfileAutomaton`

**Objective:** verify the formal properties of each automaton (type, 5-tuple, minimality) and its runs on
accepted and rejected words.

| ID | Class | Method | Scenario | Input values | Expected result |
|---|---|---|---|---|---|
| TC-R-10 | ProfileAutomaton | `automaton_type`, `dfa.is_deterministic()` | SC-R2 | Each of the 4 automata | `"DFA"`; deterministic; no `epsilon` symbol in δ |
| TC-R-11 | ProfileAutomaton | `formal_definition` | SC-R2 | Each of the 4 automata | q0 ∈ Q; F ⊆ Q with \|F\| = 1; every transition goes between states of Q on a symbol of Σ; Σ = tokens of the profile |
| TC-R-12 | ProfileAutomaton | `dfa.minimize()` | SC-R2 | Each of the 4 automata | The minimized DFA has the same number of states: every automaton is already minimal |
| TC-R-13 | ProfileAutomaton | `accepts`, `trace` | SC-R2, SC-I1, SC-E2 | Wednesday sorted sequence `JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT` | Accepted; states q0 → q1 → q2 → q3 → q4 → q5; no symbol without transition |
| TC-R-14 | ProfileAutomaton | `accepts` | SC-R2, SC-I1, SC-E3 | Mary Jane sequence sorted for ML | Accepted by the ML automaton, rejected by the Full Stack automaton |
| TC-R-15 | ProfileAutomaton | `trace`, `missing_stage` | SC-R2 | `JAVASCRIPT, NODE_JS, POSTGRESQL, GIT` (no frontend framework) | Rejected; stuck on `NODE_JS` in q1; missing stage `FRONTEND_FRAMEWORK` |
| TC-R-16 | ProfileAutomaton | `accepts` | SC-R2, SC-I1, SC-E2 | Wednesday sequence reversed | Rejected: the automaton relies on the Stage 2 sorting |

### 2.3 Classification of the sample résumés — `ProfileClassifier`

**Objective:** verify the verdict of every sample résumé for every profile, the projection onto each profile
alphabet, and that the result does not depend on the order of the résumé.

TC-R-17 (parametrized, 12 cases): expected (status, first missing stage) for each résumé and profile:

| Résumé | FULL_STACK_DEVELOPER | MACHINE_LEARNING_ENGINEER | DEVOPS_ENGINEER | DATA_ENGINEER |
|---|---|---|---|---|
| Wednesday Addams (SC-E2) | ACCEPTED | REJECTED, LANGUAGE | REJECTED, OS_SCRIPTING | REJECTED, LANGUAGE |
| Mary Jane Watson (SC-E3) | REJECTED, LANGUAGE | ACCEPTED | REJECTED, OS_SCRIPTING | REJECTED, DATA_PROCESSING |
| Full résumé (SC-E4) | REJECTED, VERSION_CONTROL | REJECTED, LANGUAGE | REJECTED, OS_SCRIPTING | REJECTED, DATA_PROCESSING |

| ID | Class | Method | Scenario | Input values | Expected result |
|---|---|---|---|---|---|
| TC-R-17 | ProfileClassifier | `classify` | SC-R3 | The 3 résumés × 4 profiles | The table above |
| TC-R-18 | ClassificationResult | `accepted_profiles`, `sequence` | SC-R3, SC-E2 | Wednesday résumé | Only FULL_STACK_DEVELOPER; word `JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT` |
| TC-R-19 | ClassificationResult | `accepted_profiles`, `sequence` | SC-R3, SC-E3 | Mary Jane résumé | Only MACHINE_LEARNING_ENGINEER; word `PYTHON, PANDAS, NUMPY, DATA_PIPELINES, SCIKIT_LEARN, TENSORFLOW, ML_MODEL_DEVELOPMENT, SQL, GIT` |
| TC-R-20 | ClassificationResult | `accepted_profiles` | SC-R3, SC-E4 | Full résumé | No accepted profile; all four REJECTED |
| TC-R-21 | ProfileClassifier | `sequence_for` (via `classify`) | SC-R3, SC-E4 | Full résumé (has C++, C#, Docker, ML libraries) | Full Stack word `JAVASCRIPT, TYPESCRIPT, ANGULAR, VUE, SPRING_BOOT, REST_API, MICROSERVICES, MYSQL, NOSQL, MONGODB`: tokens outside Σ are erased |
| TC-R-22 | ProfileClassifier | `classify` | SC-R1, SC-E1, SC-N4 | Each of the 3 résumés, its Stage 1 list shuffled 20 times (seed 2026) | Always the same `to_dict()` as the original order |
| TC-R-23 | ClassificationResult | `status`, `to_dict` | SC-R3, SC-E2 | Wednesday; `" full_stack_developer "` | `ACCEPTED`; ML `REJECTED`; `to_dict()` has the 4 profiles |
| TC-R-24 | ProfileClassifier | `classify_profile` | SC-R1 | `["GIT"]`, profile `"ASTRONAUT"` | `ValueError("Unknown profile …")` |

### 2.4 Edited résumés (SC-R4)

**Objective:** verify, through the whole pipeline (Stages 1 → 3), that removing a required skill rejects the
résumé at exactly the stage it satisfied, and that replacing it by another required skill of the same stage
keeps the résumé accepted.

TC-R-25 (parametrized, 11 cases):

| Case | Résumé | Edit | Profile | Expected result |
|---|---|---|---|---|
| wednesday-without-git | Wednesday | remove `, Git` | FULL_STACK_DEVELOPER | REJECTED, VERSION_CONTROL |
| wednesday-without-react | Wednesday | remove `React.js, ` | FULL_STACK_DEVELOPER | REJECTED, FRONTEND_FRAMEWORK |
| wednesday-without-node | Wednesday | remove `NodeJS, ` | FULL_STACK_DEVELOPER | REJECTED, BACKEND_TECHNOLOGY |
| wednesday-angular-instead-of-react | Wednesday | `React.js` → `Angular` | FULL_STACK_DEVELOPER | ACCEPTED |
| wednesday-mongodb-instead-of-postgres | Wednesday | `Postgres` → `MongoDB` | FULL_STACK_DEVELOPER | ACCEPTED (any database) |
| mary-without-python | Mary Jane | remove `Python, ` | MACHINE_LEARNING_ENGINEER | REJECTED, LANGUAGE |
| mary-without-pandas-numpy | Mary Jane | remove `Pandas, NumPy, ` | MACHINE_LEARNING_ENGINEER | REJECTED, DATA_PROCESSING |
| mary-without-ml-libraries | Mary Jane | remove `Scikit-learn, TensorFlow, ` | MACHINE_LEARNING_ENGINEER | REJECTED, ML_FRAMEWORK |
| mary-nosql-instead-of-sql | Mary Jane | `SQL` → `MongoDB` | MACHINE_LEARNING_ENGINEER | REJECTED, DATABASE (NoSQL is only optional) |
| mary-without-git | Mary Jane | remove `, Git` | MACHINE_LEARNING_ENGINEER | REJECTED, VERSION_CONTROL |
| full-resume-with-git | Full résumé | `Docker` → `Docker, Git` | FULL_STACK_DEVELOPER | ACCEPTED |

| ID | Class | Method | Scenario | Input values | Expected result |
|---|---|---|---|---|---|
| TC-R-25 | ProfileClassifier | `classify` | SC-R3, SC-R4 | The 11 edits above | The status and missing stage of the table |
| TC-R-26 | ClassificationResult | `accepted_profiles` | SC-R3, SC-E2, SC-E3 | Wednesday + Mary Jane texts concatenated | `[FULL_STACK_DEVELOPER, MACHINE_LEARNING_ENGINEER]`: one résumé can satisfy two profiles |

---

## 3. Coverage summary

| Area | Test cases | Kind of cases |
|---|---|---|
| Pattern definitions | TC-R-01 … TC-R-09 | registry, alignment with the Stage 2 vocabulary and order, invalid patterns |
| Automata | TC-R-10 … TC-R-16 | DFA type, 5-tuple consistency, minimality, accepted runs, rejected runs with trace, dependence on sorting |
| Classification | TC-R-17 … TC-R-24 | every résumé × every profile, projection, order invariance, helpers, unknown profile |
| Edited résumés | TC-R-25 … TC-R-26 | removal of each required stage, replacement within a stage, optional vs required (NoSQL), two accepted profiles |

The DevOps and Data Engineer automata are also checked end to end with their own résumés in
`TC-I-07`, `TC-I-08` (Stage 1–2 order) and `TC-C-03` (command line, ACCEPTED).
