# ResumeLens — Formal Language-Based Résumé Screening

Integrative Task 1 — *Computación y Estructuras Discretas III* (2026-2)
Departamento de CSI

## Description

**ResumeLens** is an application that processes textual résumés and determines whether the qualifications identified in a candidate's résumé satisfy the patterns defined for a professional profile. The system does **not** rank candidates or make hiring decisions — it only evaluates whether the qualifications explicitly stated in a résumé formally satisfy a given qualification pattern.

The system supports four professional profiles:

1. **Full Stack Developer** (predefined)
2. **Machine Learning Engineer** (predefined)
3. *TODO*
4. *TODO*

All four profiles are processed through the same general pipeline, built on formal language theory concepts, in four stages:

| Stage | Formal model | Purpose |
|---|---|---|
| 1. Information Extraction | Regular expressions (`re`) | Extract candidate data (contact info, languages, frameworks, databases, tools, experience, etc.) from raw résumé text. |
| 2. Qualification Normalization | Finite-State Transducers (`pyformlang`) | Map different textual variants of the same qualification (e.g. `JS`, `Javascript` → `JAVASCRIPT`) to a single canonical form, then sort them into the profile's canonical order. |
| 3. Qualification Pattern Recognition | Finite Automata — DFA/NFA/ε-NFA (`pyformlang`) | Determine whether the normalized, sorted sequence of qualifications is **ACCEPTED** or **REJECTED** for each of the four profiles. |
| 4. Candidate Profile Language | Context-Free Grammar (`textX`) | Define a DSL that structurally represents the candidate's information (personal data, experience, skills, classification result) and validate it against the grammar. |

The pipeline finishes by generating an HTML or Markdown **visualization** of a successfully validated candidate profile.

## Project Structure

```
├── docs/                     # Design documents (formalizations, module design, test cases) — Markdown
├── src/                      # Source code for the four pipeline stages
│   └──resume_lens
│      ├── extraction/        # Stage 1 — regular expressions
│      ├── normalization/     # Stage 2 — finite-state transducers
│      ├── recognition/       # Stage 3 — finite automata
│      └── dsl/               # Stage 4 — textX grammar and profile validation
├── tests/                    # Test cases and scenarios
├── requirements.txt
└── README.md
```


## Requirements

- Python 3.14+
- Dependencies listed in [`requirements.txt`](./requirements.txt)

## How to Run

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd resume-lens
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Linux: source venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py --resume path/to/resume.txt --profile FULL_STACK_DEVELOPER
   ```
5. Open the generated HTML/Markdown visualization output to view the validated candidate profile.

## Documentation

Design documents (module design, formal definitions of the FSTs/automata/grammar, and test case design) are located in the `docs/` directory, written in Markdown.

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
- **Deadline:** October 11, 2026