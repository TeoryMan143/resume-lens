# Stage 4 — Candidate Profile Language (Context-Free Grammar with textX)

Implementation: [`src/resume_lens/dsl/`](../src/resume_lens/dsl/)

| File | Role |
|---|---|
| [`candidate_profile.tx`](../src/resume_lens/dsl/candidate_profile.tx) | The grammar, in textX syntax |
| [`builder.py`](../src/resume_lens/dsl/builder.py) | `CandidateProfileBuilder`: Stage 1–3 results → CPL text |
| [`language.py`](../src/resume_lens/dsl/language.py) | `CandidateProfileLanguage`: parsing (textX) + semantic checks |
| [`processor.py`](../src/resume_lens/dsl/processor.py) | `CandidateProfileProcessor`: build + validate; `CandidateProfile` result |
| [`visualization.py`](../src/resume_lens/dsl/visualization.py) | `ProfileHtmlRenderer`: validated model → HTML page |

The **Candidate Profile Language (CPL)** is a domain-specific language that describes one candidate with the
information produced by the previous stages. Its job is different from the other stages: it does not extract,
normalize or classify. It defines **how the result must be structured**, and it rejects any document that does
not follow that structure.

**Contents**

1. Overview and example
2. Grammar in EBNF
3. Terminals and non-terminals
4. Structural characteristics
5. Properties of the grammar
6. Validation: lexical, syntactic and semantic
7. From Stages 1–3 to a CPL document
8. Visualization output
9. Limitations

---

## 1. Overview and example

```
candidate "Wednesday Addams" {
    contact {
        email "wednesday.addams@nevermore.edu"
        phone "+57 300 123 4567"
        link "https://github.com/wednesday-a"
    }
    education {
        degree "B.Sc. in Computer Science"
    }
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
        MACHINE_LEARNING_ENGINEER: REJECTED missing LANGUAGE;  // first unsatisfied stage
        DEVOPS_ENGINEER: REJECTED missing OS_SCRIPTING;
        DATA_ENGINEER: REJECTED missing LANGUAGE;
    }
}
```

Each section comes from one stage:

| Section | Information | Produced by |
|---|---|---|
| `candidate "<name>"` | Candidate name | Stage 1 (`NAME`) |
| `contact` | E-mails, phones, profile links | Stage 1 (`EMAIL`, `PHONE`, `LINK`) |
| `education` | Degrees | Stage 1 (`DEGREE`) |
| `experience` | Years + activity | Stage 1 (`EXPERIENCE`) |
| `skills` | Canonical tokens grouped by Stage 1 category, with the original spellings in parentheses; strings no transducer accepted | Stage 1 categories + Stage 2 tokens |
| `classification` | One verdict per profile: the word the automaton accepted, or the first missing stage | Stage 3 |

## 2. Grammar in EBNF

ISO/IEC 14977 notation: `=` defines a rule, `,` is concatenation, `|` alternation, `[ … ]` an optional
part (0 or 1), `{ … }` repetition (0 or more), `;` ends a rule, and quoted strings are terminal symbols.
The regular-expression terminals are defined in section 3.2.

```ebnf
candidate profile    = "candidate", person name, "{",
                           [ contact section ],
                           [ education section ],
                           [ experience section ],
                           skills section,
                           classification section,
                       "}" ;

(* ---- contact ---- *)
contact section      = "contact", "{", contact entry, { contact entry }, "}" ;
contact entry        = email entry | phone entry | link entry ;
email entry          = "email", email address ;
phone entry          = "phone", phone number ;
link entry           = "link", url ;

(* ---- education ---- *)
education section    = "education", "{", degree, { degree }, "}" ;
degree               = "degree", string ;

(* ---- experience ---- *)
experience section   = "experience", "{", experience entry, { experience entry }, "}" ;
experience entry     = integer, ( "years" | "year" ), [ string ] ;

(* ---- skills ---- *)
skills section       = "skills", "{", { skill group }, [ unrecognized group ], "}" ;
skill group          = skill category, ":", skill, { ",", skill }, ";" ;
skill category       = "programming_language" | "framework_library" | "database"
                     | "tool" | "other_qualification" ;
skill                = canonical token, [ "(", string, { ",", string }, ")" ] ;
unrecognized group   = "unrecognized", ":", string, { ",", string }, ";" ;

(* ---- classification ---- *)
classification section = "classification", "{", verdict, { verdict }, "}" ;
verdict              = accepted verdict | rejected verdict ;
accepted verdict     = profile name, ":", "ACCEPTED", "via",
                       canonical token, { ",", canonical token }, ";" ;
rejected verdict     = profile name, ":", "REJECTED", [ "missing", stage name ], ";" ;
```

`X, { X }` (one or more) corresponds to `+=` in textX, `{ X }` to `*=`, and `X, { ",", X }` to
`+=X[',']`. Whitespace and `// …` comments may appear between any two symbols and are ignored.

## 3. Terminals and non-terminals

### 3.1 Non-terminals (19)

| Non-terminal | textX rule | Derives |
|---|---|---|
| candidate profile | `CandidateProfile` | the whole document (start symbol) |
| contact section | `ContactSection` | `contact { … }` |
| contact entry | `ContactEntry` | one e-mail, phone or link |
| email entry, phone entry, link entry | `EmailEntry`, `PhoneEntry`, `LinkEntry` | keyword + value |
| education section | `EducationSection` | `education { … }` |
| degree | `Degree` | `degree "…"` |
| experience section | `ExperienceSection` | `experience { … }` |
| experience entry | `ExperienceEntry` | `3 years "…"` |
| skills section | `SkillsSection` | `skills { … }` |
| skill group | `SkillGroup` | `category: skill, …;` |
| skill category | `SkillCategory` | one of the five category keywords |
| skill | `Skill` | `TOKEN ("alias", …)` |
| unrecognized group | `UnrecognizedGroup` | `unrecognized: "…", …;` |
| classification section | `ClassificationSection` | `classification { … }` |
| verdict | `Verdict` | an accepted or a rejected verdict |
| accepted verdict, rejected verdict | `AcceptedVerdict`, `RejectedVerdict` | one profile result |

### 3.2 Terminals

**Keywords** (matched as whole words; textX option `autokwd=True`, so `database` does not match the start of
`databases`):

`candidate`, `contact`, `email`, `phone`, `link`, `education`, `degree`, `experience`, `year`, `years`,
`skills`, `programming_language`, `framework_library`, `database`, `tool`, `other_qualification`,
`unrecognized`, `classification`, `ACCEPTED`, `REJECTED`, `via`, `missing`

**Punctuation:** `{`  `}`  `:`  `;`  `,`  `(`  `)`

**Token classes** (each is a regular language, given by a regular expression):

| Terminal | textX rule | Regular expression | Examples |
|---|---|---|---|
| person name | `PersonName` | `"[^\W\d_][^"\d\n]*"` | `"Wednesday Addams"`, `"José Pérez"` |
| email address | `EmailAddress` | `"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"` | `"ana@uni.edu.co"` |
| phone number | `PhoneNumber` | `"\+?[0-9() .\-]{7,24}"` | `"+57 300 123 4567"` |
| url | `Url` | `"(https?://)?(www\.)?[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(/[A-Za-z0-9._~\-/]*)?"` | `"github.com/ana"` |
| canonical token | `CanonicalToken` | `[A-Z][A-Z0-9_]*` | `NODE_JS` |
| profile name | `ProfileName` | `[A-Z][A-Z0-9_]*` | `DATA_ENGINEER` |
| stage name | `StageName` | `[A-Z][A-Z0-9_]*` | `VERSION_CONTROL` |
| string | `STRING` (textX built-in) | a double- or single-quoted string | `"developing web applications"` |
| integer | `INT` (textX built-in) | `[-+]?[0-9]+` | `3` |
| comment | `Comment` | `//.*$` | `// note` (ignored) |

The quotes of `PersonName`, `EmailAddress`, `PhoneNumber` and `Url` are part of the terminal and are removed
after parsing by object processors (`_unquote` in `language.py`).

## 4. Structural characteristics

- **One root, fixed section order.** A document describes one candidate. The sections appear in the
  order contact → education → experience → skills → classification. Moving a section is a syntax error.
- **Optional and mandatory sections.** `contact`, `education` and `experience` are optional, because a
  résumé may not contain them. `skills` and `classification` are mandatory, because they are the result of
  the pipeline. `skills` may be empty (no qualification found), but `classification` needs at least one
  verdict.
- **Repetition.** Every section holds a list:
  - several contact entries, degrees, experience entries;
  - zero or more skill groups, each with one or more comma-separated skills;
  - one or more aliases per skill;
  - one or more verdicts.

  Lists inside a line use `,` and end with `;`. Lists of entries are separated only by whitespace.
- **Nesting (hierarchy).** document → section → entry/group → item (skill, alias, token). Braces delimit
  sections; parentheses delimit the aliases of one skill.
- **Alternatives.** A contact entry is an e-mail, a phone or a link, chosen by its keyword. A verdict is
  ACCEPTED (it must list the accepted word after `via`) or REJECTED (it may name the missing stage). The
  grammar enforces this pairing: `ACCEPTED;` and `REJECTED via GIT;` are both syntax errors.
- **Closed vocabularies.** Skill categories are a fixed set of keywords, the same as the Stage 1
  categories. Canonical tokens, profiles and stages are free upper-case identifiers in the grammar; their
  allowed values are checked semantically (section 6.3), so adding a profile does not require changing
  the grammar.
- **Insignificant layout.** Line breaks, indentation and `//` comments do not change the meaning; a
  whole profile may be written on one line.

## 5. Properties of the grammar

- **Context-free.** Every rule has a single non-terminal on the left-hand side, so the grammar is a
  context-free grammar G = (V, T, P, S), with V the 19 non-terminals of 3.1, T the terminals of 3.2, P the
  rules of section 2 and S = candidate profile.
- **The language is in fact regular.** Nesting depth is bounded (at most `{ … ( … ) … }` inside the
  root), and no rule is recursive. A finite-state machine could therefore recognize L(G). A CFG is used
  anyway because it states the hierarchical structure directly: sections, entries and items become rules
  and textX builds an object model (`model.skills.groups[0].skills[0].token`) from the derivation tree.
  Recursive structures such as nested projects would need the full power of a CFG; this grammar does
  not.
- **No useless symbols.** Every non-terminal is reachable from the start symbol and derives at least one
  terminal string.
- **No left recursion**, which textX requires. textX builds a PEG parser (Arpeggio), whose ordered
  choice `A | B` tries A first. In this grammar the alternatives of every choice start with a different
  keyword (`email`/`phone`/`link`, the five categories, `years`/`year`), or they differ at the third
  symbol (`ACCEPTED`/`REJECTED`) and the parser backtracks. So ordered choice accepts the same language
  as the unordered CFG, and each valid document has exactly one derivation tree: the grammar is
  **unambiguous**.
- **ε-productions** appear only through the optional parts `[ … ]` and `{ … }`. Rewriting them with new
  non-terminals (for example `opt contact = contact section | ε`) and then removing ε, unit and long rules
  gives the Chomsky normal form of the same grammar; the EBNF form is kept because it is the one textX
  uses.

## 6. Validation: lexical, syntactic and semantic

`CandidateProfileLanguage.parse(text)` returns the model of a valid document or raises
`ProfileValidationError` with the line and column of the first error.

### 6.1 Lexical errors (a terminal does not match its regular expression)

Messages are the parser's own, followed by `(line L, col C)`.

| Input fragment | Error |
|---|---|
| `email "peter.parker.dailybugle.com"` | Expected EmailAddress |
| `phone "+1 (212) CALL-NOW"` | Expected PhoneNumber |
| `candidate "Peter Parker 2"` | Expected PersonName |
| `javascript ("JS")` | Expected CanonicalToken |
| `four years` | Expected INT or '}' |

### 6.2 Syntactic errors (the token sequence cannot be derived)

| Input fragment | Error |
|---|---|
| `tool: GIT ("Git")` (no `;`) | Expected ',' or ';' |
| `skils { … }` | Expected 'skills' |
| `databases: …` | Expected 'programming_language' or 'framework_library' or 'database' or 'tool' or 'other_qualification' or 'unrecognized' or '}' |
| `FULL_STACK_DEVELOPER: ACCEPTED;` | Expected 'via' |
| `education { }` | Expected 'degree' |
| sections in a different order, a missing `skills` or `classification` section, text after the final `}` | Expected … (the symbol the grammar allows at that position) |

### 6.3 Semantic errors (well-formed but inconsistent with Stages 2 and 3)

A context-free grammar cannot express these rules, so they are checked by textX object processors after
parsing (`language.py`). They raise `TextXSemanticError` with the position of the offending element.

| Rule | Example of violation |
|---|---|
| Every skill token is a Stage 2 canonical token | `COBOL ("Python")` |
| A skill is declared only once | `GIT` in two groups |
| Every profile exists and is classified only once | `QA_ENGINEER: REJECTED;`, `DEVOPS_ENGINEER` twice |
| An ACCEPTED word uses only declared skills of the profile alphabet Σ | `… via …, MYSQL` when MySQL is not a skill |
| An ACCEPTED word satisfies the profile pattern | Full Stack ACCEPTED without a backend token |
| A REJECTED profile is really not satisfied by the declared skills | Full Stack REJECTED although the skills satisfy it |
| A missing stage is a stage of that profile | `DEVOPS_ENGINEER: REJECTED missing KUBERNETES_SKILLS;` |
| 1 ≤ years ≤ 60; a phone has 7–15 digits | `0 years`, `"12 34 56"` |

The last two consistency rules mean that a profile edited by hand cannot claim a result that Stage 3
would not produce.

## 7. From Stages 1–3 to a CPL document

`CandidateProfileBuilder.build(extraction, normalization, classification)`:

| Input object | Fields used | Written as |
|---|---|---|
| `ExtractionResult` (Stage 1) | `name` (or `Unknown Candidate` if none) | `candidate "…"` |
| | `emails`, `phones`, `links` | `contact { … }` (omitted if empty) |
| | `degrees` | `education { … }` (omitted if empty) |
| | `experience` | `experience { N years "…" }` (omitted if empty) |
| | `items` (value, category, position) | the category of each skill and its original spellings |
| `NormalizationResult` (Stage 2) | `mapping` raw → canonical | `TOKEN ("raw 1", "raw 2")`, grouped by category |
| | `unrecognized` | `unrecognized: "…";` |
| `ClassificationResult` (Stage 3) | `verdicts[profile]` | `P: ACCEPTED via …;` or `P: REJECTED missing S;` |

`CandidateProfileProcessor.process(...)` builds the text and immediately parses it. Only a validated
`CandidateProfile(text, model)` is returned. It can be saved (`save`, CLI `--cpl`) and turned into HTML
(`to_html`, `save_html`, CLI `--html`).

## 8. Visualization output

`ProfileHtmlRenderer.render(model, source)` reads **only the validated textX model** and produces one
self-contained HTML file (inline CSS, no scripts, light and dark mode). The page contains:

1. Header: name and clickable contact links.
2. Summary: the profiles whose pattern is satisfied.
3. Profile classification: every verdict, with the accepted word or the first missing stage.
4. Skills grouped by category, with the original spellings, and the unrecognized strings.
5. Experience and education.
6. The CPL source in a collapsible block, for traceability.
7. A footer stating that the page is not a ranking or a hiring decision.

All text from the document is HTML-escaped.

```bash
python main.py --resume tests/resources/good.txt --cpl out/alex.cpl --html out/alex.html
```

## 9. Limitations

- A CPL document describes the result of the pipeline, not the full résumé: projects, dates of jobs and
  certifications are not part of the language because Stage 1 does not extract them.
- Profiles, stages and canonical tokens are checked against the Python definitions (`PATTERNS`,
  `CANONICAL_VARIANTS`), not against a list written in the grammar. The grammar alone accepts any
  upper-case identifier there.
- Only the first error of a document is reported.
