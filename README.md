# ResumeLens — Formal Language-Based Résumé Screening

Integrative Task 1 — *Computación y Estructuras Discretas III* (2026-2)
Departamento de CSI

## Description

**ResumeLens** is an application that processes textual résumés and determines whether the qualifications identified in a candidate's résumé satisfy the patterns defined for a professional profile. The system does **not** rank candidates or make hiring decisions — it only evaluates whether the qualifications explicitly stated in a résumé formally satisfy a given qualification pattern.

The system supports four professional profiles:

1. **Full Stack Developer** (predefined)
2. **Machine Learning Engineer** (predefined)
3. **DevOps Engineer** (software engineering, defined by the team)
4. **Data Engineer** (AI/data, defined by the team)

All four profiles are processed through the same general pipeline, built on formal language theory concepts, in four stages:

| Stage | Formal model | Purpose |
|---|---|---|
| 1. Information Extraction | Regular expressions (`re`) | Extract candidate data (name, contact info, languages, frameworks, databases, tools, experience, degrees) from raw résumé text. |
| 2. Qualification Normalization | Finite-State Transducers (`pyformlang`) | Map different textual variants of the same qualification (e.g. `JS`, `Javascript` → `JAVASCRIPT`) to a single canonical token, then sort the tokens into the profile's canonical order. |
| 3. Qualification Pattern Recognition | Deterministic Finite Automata (`pyformlang`) | Run the sorted sequence through one DFA per profile and decide whether it is **ACCEPTED** or **REJECTED**. |
| 4. Candidate Profile Language | Context-Free Grammar (`textX`) | Write the results of Stages 1–3 in a domain-specific language (CPL), validate it against the grammar and semantic rules, and render it as an **HTML visualization**. |

```
résumé.txt ──► Stage 1 (regex) ──► raw strings: JS, React.js, NodeJS, Postgres, Git
           ──► Stage 2 (FSTs)  ──► canonical tokens: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT
           ──► Stage 3 (DFAs)  ──► FULL_STACK_DEVELOPER: ACCEPTED, the other three: REJECTED
           ──► Stage 4 (CFG)   ──► validated profile.cpl ──► profile.html
```

## Professional Profiles

Each profile is a sequence of **stages**. A stage is satisfied when the résumé contains **at least one** of its required qualifications; optional qualifications may also appear but are never needed. A résumé is **ACCEPTED** for a profile when every stage is satisfied. Qualifications that a profile does not mention are ignored for that profile (they neither help nor penalize).

**1. Full Stack Developer** — builds both client-side and server-side components.

| Stage | Required (at least one) | Optional |
|---|---|---|
| LANGUAGE | JavaScript, TypeScript | |
| FRONTEND_FRAMEWORK | React, Angular, Vue | Next.js |
| BACKEND_TECHNOLOGY | Node.js, Express, Django, Flask, FastAPI, Spring Boot | REST APIs, GraphQL, Microservices |
| DATABASE | any SQL or NoSQL database | |
| VERSION_CONTROL | Git, GitHub, GitLab | |

**2. Machine Learning Engineer** — combines software development, data processing and machine-learning models.

| Stage | Required (at least one) | Optional |
|---|---|---|
| LANGUAGE | Python | |
| DATA_PROCESSING | Pandas, NumPy | Data pipelines |
| ML_FRAMEWORK | Scikit-learn, TensorFlow, PyTorch | Keras, ML model development, Deep learning |
| DATABASE | any SQL database | any NoSQL database |
| VERSION_CONTROL | Git, GitHub, GitLab | |

**3. DevOps Engineer** — automates building, deploying and operating software infrastructure.

| Stage | Required (at least one) | Optional |
|---|---|---|
| OS_SCRIPTING | Linux, Bash | Python |
| VERSION_CONTROL | Git, GitHub, GitLab | |
| CI_CD | CI/CD, Jenkins, GitHub Actions | |
| CONTAINERS | Docker, Kubernetes | |
| INFRASTRUCTURE_AS_CODE | Infrastructure as Code, Terraform, Ansible | |
| CLOUD | AWS, Azure, GCP | Prometheus, Grafana |

**4. Data Engineer** — designs and maintains the pipelines that collect, transform and store data.

| Stage | Required (at least one) | Optional |
|---|---|---|
| LANGUAGE | Python, Scala, Java | |
| DATA_PROCESSING | Spark, Hadoop, Databricks, Kafka | |
| ORCHESTRATION_ETL | Airflow, ETL, Data pipelines, dbt | |
| DATABASE | any SQL database | any NoSQL database, Snowflake, BigQuery, AWS, Azure, GCP |
| VERSION_CONTROL | Git, GitHub, GitLab | |

The patterns are defined in [`recognition/patterns.py`](src/resume_lens/recognition/patterns.py) and the canonical sorting orders in [`normalization/profiles.py`](src/resume_lens/normalization/profiles.py).

## Project Structure

```
├── main.py                       # Entry point: python main.py --resume ... --profile ...
├── docs/                         # Design documents (Markdown)
│   ├── module-design.md              # Modules, functions, inputs and outputs
│   ├── stage1-extraction-regex.md    # Regular expressions (Stage 1)
│   ├── stage2-normalization-fst.md   # Finite-state transducers (Stage 2)
│   ├── fst/                          # Transducer diagrams (PlantUML + SVG)
│   ├── automata/                     # Automaton diagrams (PlantUML + SVG)
│   ├── diagrams/                     # Architecture and CLI flow (PlantUML + SVG)
│   ├── stage3-recognition-automata.md    # Finite automata (Stage 3)
│   ├── stage4-candidate-profile-language.md  # Grammar and DSL (Stage 4)
│   ├── test-design-*.md              # Test scenarios and cases (stages 1-2, 3, 4)
│   └── poster.png                    # Project poster
├── src/
│   └── resume_lens/
│       ├── __init__.py           # Command-line interface (main)
│       ├── pipeline.py           # Stage 1 + Stage 2 chained
│       ├── extraction/           # Stage 1 — regular expressions
│       ├── normalization/        # Stage 2 — finite-state transducers, profile orders, sorter
│       ├── recognition/          # Stage 3 — profile patterns and their DFAs
│       └── dsl/                  # Stage 4 — textX grammar, validation and HTML visualization
│           ├── candidate_profile.tx  # CPL grammar (EBNF, textX syntax)
│           ├── builder.py            # Stage 1–3 results -> CPL text
│           ├── language.py           # Parsing + semantic validation
│           ├── processor.py          # Stage 4 entry point
│           └── visualization.py      # Validated model -> HTML page
├── tests/                        # pytest test cases
│   └── resources/                # Sample résumés (.txt) and a sample profile (.cpl)
├── pyproject.toml                # Project metadata and dependencies (uv)
├── uv.lock                       # Locked dependency versions (uv)
├── requirements.txt              # Same dependencies for pip (generated with uv export)
└── README.md
```

## Requirements

- Python **3.14+**
- Dependencies: `pyformlang`, `textx` and, for the tests, `pytest` (exact versions in [`uv.lock`](./uv.lock) / [`requirements.txt`](./requirements.txt))
- Optional: [uv](https://docs.astral.sh/uv/) as the package manager

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd resume-lens
```

### Option A — with uv (recommended)

```bash
uv sync
```

This creates `.venv/` and installs the project, its dependencies and the development tools (pytest) at the locked versions. Run any command inside the environment with `uv run`, so there is no need to activate it.

### Option B — with pip

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py --resume path/to/resume.txt --profile FULL_STACK_DEVELOPER
```

With uv, the same command is `uv run main.py ...`, or use the installed script `uv run resume-lens ...`.

### Command-line options

| Option | Required | Description |
|---|---|---|
| `--resume PATH` | yes | Résumé to analyze: a plain-text (`.txt`) file in UTF-8. |
| `--profile NAME` | no | Profile whose Stage 2 order and Stage 3 verdict are shown. One of `FULL_STACK_DEVELOPER` (default), `MACHINE_LEARNING_ENGINEER`, `DEVOPS_ENGINEER`, `DATA_ENGINEER`; case-insensitive. The four profiles are always classified and all appear in the candidate profile. |
| `--out PATH` | no | Save the Stage 1 extraction as JSON. |
| `--cpl PATH` | no | Save the validated Stage 4 candidate profile (`.cpl`). |
| `--html PATH` | no | Save the HTML visualization of the candidate profile; open it in any browser. |
| `-h`, `--help` | no | Show the help message. |

Folders in the output paths are created if they do not exist. The program exits with code `0` on success (whether the profile is accepted or rejected), `1` if the generated candidate profile is invalid, and `2` for invalid arguments (e.g. an unknown profile).

### Example

```bash
python main.py --resume tests/resources/wednesday_addams.txt --profile FULL_STACK_DEVELOPER --html out/wednesday.html
```

```
Stage 1 - extracted: JS, React.js, NodeJS, Postgres, Git
Stage 2 - normalized: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT
Stage 2 - sorted for FULL_STACK_DEVELOPER: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT
Stage 3 - FULL_STACK_DEVELOPER: ACCEPTED
Stage 3 - accepted profiles: FULL_STACK_DEVELOPER
Stage 4 - candidate profile (valid):
candidate "Wednesday Addams" {
    experience {
        3 years "developing web applications"
    }
    skills {
        programming_language: JAVASCRIPT ("JS");
        framework_library: REACT ("React.js"), NODE_JS ("NodeJS");
        database: POSTGRESQL ("Postgres");
        tool: GIT ("Git");
    }
    classification {
        FULL_STACK_DEVELOPER: ACCEPTED via JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT;
        MACHINE_LEARNING_ENGINEER: REJECTED missing LANGUAGE;
        DEVOPS_ENGINEER: REJECTED missing OS_SCRIPTING;
        DATA_ENGINEER: REJECTED missing LANGUAGE;
    }
}
Stage 4 - HTML visualization saved to out/wednesday.html
```

When a profile is rejected, Stage 3 also prints the first unsatisfied stage, e.g. `MACHINE_LEARNING_ENGINEER: REJECTED (missing LANGUAGE)`.

### Sample résumés

`tests/resources/` contains résumés you can try right away:

| File | Written for |
|---|---|
| `wednesday_addams.txt` | Full Stack Developer (example from the assignment) |
| `mary_jane_watson.txt` | Machine Learning Engineer (example from the assignment) |
| `devops_resume.txt` | DevOps Engineer |
| `data_engineer_resume.txt` | Data Engineer |
| `full_resume.txt` | No profile; includes contact data, links and education |
| `good.txt` | A complete, realistic Full Stack résumé |
| `bad.txt` | A poorly written résumé |

## Candidate Profile Language (CPL)

Stage 4 writes every analyzed résumé in a small domain-specific language defined by the context-free grammar in [`candidate_profile.tx`](src/resume_lens/dsl/candidate_profile.tx). A document has a fixed section order:

```
candidate "<name>" {
    contact { email "..."  phone "..."  link "..." }        // optional
    education { degree "..." }                               // optional
    experience { 3 years "developing web applications" }    // optional
    skills { <category>: TOKEN ("surface form", ...), ...; } // required
    classification { PROFILE: ACCEPTED via TOKEN, ...; | PROFILE: REJECTED missing STAGE; } // required
}
```

A profile is checked in three layers, and the first error is reported with its line and column:

1. **Lexical:** e-mails, phones, URLs, names and canonical tokens must match their regular expressions.
2. **Syntactic:** the document must be derivable from the grammar (sections, separators, repetitions).
3. **Semantic:** tokens must exist in the Stage 2 catalog; skills and profiles cannot be repeated; and each ACCEPTED/REJECTED verdict must agree with the Stage 3 pattern of that profile.

Only valid profiles are turned into HTML.

## Running the Tests

```bash
uv run pytest            # with uv
pytest                   # with pip, inside the activated virtual environment
```

Run one part of the suite by its test ID prefix:

```bash
pytest -k "tc_e_"        # Stage 1 — extraction
pytest -k "tc_n_"        # Stage 2 — normalization
pytest -k "tc_r_"        # Stage 3 — recognition
pytest -k "tc_g_"        # Stage 4 — candidate profile language
pytest -k "tc_h_"        # Stage 4 — HTML visualization
pytest -k "tc_c_"        # command line, Stages 1 -> 4
```

Each test ID corresponds to a row in the test-design documents in `docs/`.

## Documentation

The project poster is at [`docs/poster.png`](docs/poster.png).

Design documents are in the `docs/` directory, written in Markdown:

| Document | Content |
|---|---|
| [`module-design.md`](docs/module-design.md) | Architecture, modules, functions with their inputs and outputs, data passed between stages |
| [`stage1-extraction-regex.md`](docs/stage1-extraction-regex.md) | Every Stage 1 regular expression and the language it recognizes |
| [`stage2-normalization-fst.md`](docs/stage2-normalization-fst.md) | Formal 7-tuple and diagram of every finite-state transducer; sorting by profile |
| [`stage3-recognition-automata.md`](docs/stage3-recognition-automata.md) | 5-tuple, type (DFA) and transition diagram of the four profile automata |
| [`stage4-candidate-profile-language.md`](docs/stage4-candidate-profile-language.md) | CPL grammar in EBNF, terminals and non-terminals, structure, validation, HTML output |
| [`test-design-stages-1-2.md`](docs/test-design-stages-1-2.md) | Test scenarios and cases for Stages 1 and 2 |
| [`test-design-stage-3.md`](docs/test-design-stage-3.md) | Test scenarios and cases for Stage 3 |
| [`test-design-stage-4.md`](docs/test-design-stage-4.md) | Test scenarios and cases for Stage 4, the HTML visualization and the command line |
| [`ai-usage-log.md`](docs/ai-usage-log.md) | Generative AI usage log: prompts, content given to the AI, results and team review |
| [`poster.png`](docs/poster.png) | Project poster |

All diagrams are written in **PlantUML** (`.puml`) and committed together with their rendered `.svg`, so they display on GitHub and in any Markdown preview. After editing a `.puml` file, render it again with `plantuml -tsvg -charset UTF-8 docs/<folder>/<file>.puml`.

## Known Limitations

- Only plain-text résumés are supported (no PDF or DOCX).
- Only qualifications listed in the Stage 2 catalog ([`normalization/catalog.py`](src/resume_lens/normalization/catalog.py)) can be recognized. Others are reported as unrecognized and do not count toward any profile.
- The candidate name is taken from the first line made of 2–4 capitalized words (`Alex Morgan`) or 2–4 all-caps words (`ALEX MORGAN`, shown as `Alex Morgan`). Names with lower-case particles (`Ana de la Cruz`) or quotes are not detected; if no line matches, the profile uses `Unknown Candidate`.
- Keywords for experience and degrees are recognized in English and Spanish.

## IDE Used

VS Code

## Team Members

| Name | Student Code | GitHub User |
|---|---|---|
| Jonathan David Cortés Castaño | A00411095 | TeoryMan143 |
| Juan Camilo Borrero Flórez | A00430714 | NPt214 |
| Andrés Martínez Martínez | A00411070 | itshappysad |

## Course Information

- **Course:** Computación y Estructuras Discretas III — 2026-2
- **Course Code:** 09834
- **Group:** 3
- **Deadline:** October 12, 2026
