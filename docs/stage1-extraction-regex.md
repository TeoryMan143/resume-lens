# Stage 1 — Résumé Information Extraction with Regular Expressions

Implementation: [`src/resume_lens/extraction/patterns.py`](../src/resume_lens/extraction/patterns.py) (the expressions),
[`extractor.py`](../src/resume_lens/extraction/extractor.py) (`ResumeExtractor`) and
[`models.py`](../src/resume_lens/extraction/models.py) (`ExtractionResult`), using Python's `re` module.

Stage 1 only **detects** strings that may describe the candidate. It does not decide whether two strings
mean the same thing (Stage 2) or whether a profile is satisfied (Stage 3). Strings are kept exactly as they
appear in the résumé (`JS`, `React.js`, `Postgres`).

**Contents**

1. Regular expressions and notation
2. Token boundaries
3. Personal and contact information (name, e-mail, phone, link)
4. Experience and education
5. Qualifications (languages, frameworks, databases, tools, other)
6. How the extracted information is stored
7. Worked example
8. Limitations

---

## 1. Regular expressions and notation

A regular expression over an alphabet Σ denotes a language L ⊆ Σ*. The constructions used here are the
classical ones (union `|`, concatenation, Kleene star `*`), plus derived operators that do not add expressive
power:

| Python syntax | Meaning | Equivalent classical form |
|---|---|---|
| `[A-Z]` | one symbol of a class | A ∪ B ∪ … ∪ Z |
| `r?` | optional | r ∪ ε |
| `r+` | one or more | r r* |
| `r{m,n}` | between m and n copies | r^m ∪ r^(m+1) ∪ … ∪ r^n |
| `(?:r)` | grouping without capture | (r) |
| `(?P<name>r)` | named capture group (used to read a part of the match) | (r) |

Two Python features go beyond the classical definition and are used only to **restrict where** a match may
start or end, never to change the matched string:

- **Lookarounds** `(?<!…)`, `(?!…)`: a zero-width test of the surrounding characters (section 2).
- **Anchors** `^`, `$` with `re.MULTILINE`: the match must fill a whole line.
- **Word boundary** `\b`: a position between a word character and a non-word character.

Σ is the set of Unicode characters of the résumé. `re.IGNORECASE` makes letters match in either case
(`JS`, `js`, `Js`), which is equivalent to replacing each letter `a` by `[aA]`.

## 2. Token boundaries

Qualification names are short and appear inside longer text, so the core expression alone would produce
false positives: `js` inside `React.js`, `Java` inside `JavaScript`, `github` inside a URL. Every
qualification expression is therefore wrapped as `_LEFT (alternatives) _RIGHT`:

```python
_LEFT  = r"(?<![\w.#+/@-])"   # not preceded by a word character, '.', '#', '+', '/', '@' or '-'
_RIGHT = r"(?![\w+#]|\.\w)"   # not followed by a word character, '+', '#', or '.' + letter (a domain)
```

| Text | Without boundaries | With boundaries |
|---|---|---|
| `React.js` | `React.js` **and** `js` (language) | `React.js` only |
| `JavaScript` | `JavaScript` **and** `Java` | `JavaScript` only |
| `https://github.com/x` | `github` (tool) | nothing (handled by the link expression) |
| `C++`, `C#` | `C` inside them | `C++`, `C#` |

Alternatives are ordered longest first where one is a prefix of another (`GitHub Actions` before `GitHub`
before `Git`, `PostgreSQL` before `Postgres`), because Python tries alternatives left to right.

---

## 3. Personal and contact information

### 3.1 Name — `NAME` (`re.MULTILINE`)

```regex
^[ \t]*(?P<name>
      [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:[ \t]+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}
    | (?!(?:TECHNICAL|PROFESSIONAL|WORK|KEY|CORE|SKILLS?|EXPERIENCE|EDUCATION|CONTACT|PERSONAL
          |CURRICULUM|RESUME|PROJECTS?|CERTIFICATIONS?|SUMMARY|PROFILE|OBJECTIVE|ACADEMIC)\b)
      [A-ZÁÉÍÓÚÑ]{2,}(?:[ \t]+[A-ZÁÉÍÓÚÑ]{2,}){1,3}
)[ \t]*$
```

(Shown on several lines for reading; the implementation is one line.)

**Language.** A whole line made of 2 to 4 words separated by blanks, where either

- every word is **capitalized**: one upper-case letter followed by one or more lower-case letters
  (`Wednesday Addams`, `Mary Jane Watson`), or
- every word is **all caps** with at least two letters (`ALEX MORGAN`), and the first word is not a usual
  section-header word, so `TECHNICAL SKILLS` or `WORK EXPERIENCE` are not names.

Spanish accented letters and `Ñ` are allowed. Only the **first** matching line is taken
(`ResumeExtractor.extract_name`), and an all-caps name is returned in title case (`Alex Morgan`).

| Matches | Does not match |
|---|---|
| `Wednesday Addams`, `Mary Jane Watson`, `ALEX MORGAN` | `technical skills: python, git` (lower case, punctuation) |
| `José Pérez` | `TECHNICAL SKILLS`, `CURRICULUM VITAE` (header words) |
| | `Chad "The Code Ninja" Johnson` (quotes are not letters) |
| | `Ada` (one word), `Full Stack Developer Senior Engineer Lead` (more than 4 words) |

### 3.2 E-mail — `EMAIL`

```regex
(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w-])
```

**Language.** `local-part @ domain . TLD`, where local-part ∈ [A-Za-z0-9._%+-]⁺, the domain is one or more
labels [A-Za-z0-9-]⁺ separated by dots, and the top-level domain has at least two letters.

| Matches | Does not match |
|---|---|
| `wednesday.addams@nevermore.edu` | `user@domain` (no TLD) |
| `cooldev420@hotmail.com` | `user@domain.c` (one-letter TLD) |
| | `@nevermore.edu` (empty local part), `user at mail.com` |

### 3.3 Phone — `PHONE`

```regex
(?<![\w+])(?:\+\d{1,3}[ .-]?)?(?:\(\d{2,4}\)[ .-]?|\d{2,4}[ .-]?)?\d{3}[ .-]?\d{4}(?![\w])
```

**Language.** An optional international prefix `+` followed by 1–3 digits, an optional area code of 2–4 digits
(with or without parentheses), and a local number of 3 + 4 digits. Consecutive groups may be separated by one
space, dot or hyphen.

| Matches | Does not match |
|---|---|
| `+57 300 123 4567` | `Universidad Icesi (2019 - 2023)`, `2019-2023` (years) |
| `(602) 555-0199` | `Code A00411070` (glued to a letter) |
| `3001234567` | `12345` (too short) |

### 3.4 Profile link — `LINK` (`re.IGNORECASE`)

```regex
(?:https?://)?(?:www\.)?(?:linkedin\.com/in|github\.com)/[A-Za-z0-9_-]+/?
```

**Language.** A LinkedIn profile URL (`linkedin.com/in/<user>`) or a GitHub account URL
(`github.com/<user>`), with optional `http://`/`https://` and `www.`, and an optional final `/`.

| Matches | Does not match |
|---|---|
| `https://github.com/wednesday-a` | `alexmorgan.dev` (personal site: not a profile link) |
| `linkedin.com/in/wednesday` | `gitlab.com/user` |

`extract_links` keeps each account once: two links are the same when they differ only in scheme, `www.`,
letter case or a trailing `/` (`github.com/amorgan-dev` = `https://www.GitHub.com/amorgan-dev/`).

---

## 4. Experience and education

### 4.1 Professional experience — `EXPERIENCE` (`re.IGNORECASE`)

```regex
(?P<years>\d{1,2})\+?[ \t]*(?:years?|yrs?\.?|años?)[ \t]+(?:of[ \t]+|de[ \t]+)?
(?:professional[ \t]+|profesional[ \t]+)?(?:experience|experiencia)
(?:[ \t]+(?P<field>(?:in|with|developing|building|as|en|como|desarrollando)[ \t]+[^.\n]+))?
```

**Language.** A number of years (1–2 digits, optional `+`), the unit `year(s)` / `yr(s)` / `año(s)`,
optionally `of`/`de` and `professional`/`profesional`, the word `experience`/`experiencia`, and optionally the
activity: a connecting word (`in`, `with`, `developing`, `building`, `as`, `en`, `como`, `desarrollando`)
followed by any text up to the end of the sentence (`.`) or line. Group `years` gives the number and
group `field` the activity.

| Text | years | field |
|---|---|---|
| `3 years of experience developing web applications.` | 3 | `developing web applications` |
| `5+ yrs of experience with REST APIs` | 5 | `with REST APIs` |
| `4 años de experiencia en desarrollo backend` | 4 | `en desarrollo backend` |
| `10 years of professional experience` | 10 | (empty) |

### 4.2 Academic qualifications — `DEGREE`

```regex
\b(?:(?:Bachelor|Master)(?:'s)?\b(?:[ \t]+[Dd]egree)?|Doctorate\b|MBA\b|Ph\.?[ ]?D\b\.?|B\.?[ ]?Sc\b\.?
    |M\.?[ ]?Sc\b\.?|Ingenier(?:o|a|ía|ia)\b|Maestr(?:ía|ia)\b|Licenciatura\b)
(?:[ \t]+(?:of|in|en|de)[ \t]+(?:Science[ \t]+in[ \t]+)?
    [A-ZÁÉÍÓÚ][\wáéíóúñ]*(?:[ \t]+(?:[A-ZÁÉÍÓÚ][\wáéíóúñ]*|and|&|de|y))*)?
```

**Language.** A degree keyword (Bachelor, Master, Doctorate, MBA, Ph.D., B.Sc., M.Sc., Ingeniería, Maestría,
Licenciatura, with optional dots and `'s Degree`), optionally followed by `of`/`in`/`en`/`de` and a field of
study made of capitalized words, which may be joined by `and`, `&`, `de` or `y`.

| Matches |
|---|
| `B.Sc. in Computer Science` |
| `Master of Science in Artificial Intelligence` |
| `Ingeniería de Sistemas` |

---

## 5. Qualifications

These five categories form the input of Stage 2 (`QUALIFICATION_CATEGORIES`). All of them use
`re.IGNORECASE` and the boundaries of section 2. Each expression is the union of the surface forms of one
group of qualifications.

### 5.1 Programming languages — `PROGRAMMING_LANGUAGE`

```regex
_LEFT (?:Java[ ]?Script|ECMAScript|ES6|JS|TypeScript|TS|Python[ ]?3?|Java(?![ ]?Script)
      |C\+\+|CPP|C#|C[ ]?Sharp|Kotlin|Swift|Golang|Rust|PHP|Ruby|Scala) _RIGHT
```

**Language.** Names and abbreviations of programming languages. `Java(?![ ]?Script)` stops `Java` from
matching the start of `JavaScript`/`Java Script`.

| Matches | Not reported |
|---|---|
| `JavaScript`, `JS`, `TypeScript`, `Java`, `C++`, `C#`, `Python 3` | `js` in `React.js`, `Java` in `JavaScript` |

### 5.2 Frameworks and libraries — `FRAMEWORK_LIBRARY`

```regex
_LEFT (?:React(?:\.?js)?|Angular(?:\.?js)?|Vue(?:\.?js)?|Node(?:\.?js)?|Express(?:\.?js)|Next\.?js|Django|Flask
      |Fast[ ]?API|Spring[ ]?Boot|Pandas|Num[ ]?Py|Scikit[ -]?learn|sklearn|Tensor[ ]?Flow|Py[ ]?Torch
      |Keras|Matplotlib) _RIGHT
```

**Language.** Web and data/ML frameworks with their usual spellings: an optional `.js`/`js` suffix, and an
optional space or hyphen inside compound names.

| Matches |
|---|
| `React.js`, `ReactJS`, `Vue.js`, `Angular`, `NodeJS`, `Spring Boot` |
| `scikit learn`, `sklearn`, `Scikit-learn`, `Tensor Flow`, `Py Torch`, `NumPy`, `pandas` |

### 5.3 Databases — `DATABASE`

```regex
_LEFT (?:PostgreSQL|Postgres|MySQL|My[ ]SQL|MariaDB|SQLite|Mongo[ ]?DB|Mongo|Redis|Oracle|SQL[ ]?Server
      |No[ ]?SQL|SQL|Cassandra|DynamoDB|Firebase|Snowflake|Big[ ]?Query) _RIGHT
```

**Language.** Database engines, data warehouses and the families SQL/NoSQL. Because of the left boundary,
`SQL` is only reported as a separate word and never inside `PostgreSQL`, `MySQL` or `NoSQL`.

| Matches |
|---|
| `PostgreSQL`, `Postgres`, `MySQL`, `NoSQL`, `MongoDB`, `SQL`, `Snowflake`, `BigQuery` |

### 5.4 Tools and technologies — `TOOL`

```regex
_LEFT (?:GitHub[ ]Actions|Git(?:Hub|Lab)?|Docker|Kubernetes|K8s|AWS|Amazon[ ]Web[ ]Services|Azure|GCP
      |Google[ ]Cloud(?:[ ]Platform)?|Linux|Bash|Shell[ ]Scripting|Terraform|Ansible|Prometheus|Grafana
      |Jenkins|Jupyter(?:[ ]Notebooks?)?|Postman|Jira|MLflow|(?:Apache[ ])?(?:Airflow|Spark|Hadoop|Kafka)
      |PySpark|Databricks|dbt) _RIGHT
```

**Language.** Version control, containers, cloud platforms, DevOps and data-engineering tools.
`GitHub Actions` comes before `GitHub`, so the longer name is kept as one string.

| Matches | Not reported |
|---|---|
| `Git`, `GitHub`, `Docker`, `Kubernetes`, `AWS`, `Apache Spark`, `dbt` | `github` inside `https://github.com/x` |

### 5.5 Other qualifications — `OTHER_QUALIFICATION`

```regex
(?<![\w])(?:REST(?:ful)?[ -]?APIs?|GraphQL|Machine[ -]Learning(?:[ ]Models?)?|Deep[ -]Learning
      |Predictive[ ]Models?|Data[ -]Processing(?:[ ]Pipelines?)?|Data[ ]Pipelines?|Microservices|CI/CD
      |ETL|ELT|Infrastructure[ ]as[ ]Code|IaC)(?![\w])
```

**Language.** Multi-word skills and concepts that the profiles use: REST/RESTful API(s), GraphQL,
machine-learning models, deep learning, predictive models, data-processing pipelines, microservices,
CI/CD, ETL/ELT and Infrastructure as Code.

| Matches |
|---|
| `RESTful APIs`, `machine learning models`, `predictive models`, `data-processing pipelines`, `CI/CD` |

---

## 6. How the extracted information is stored

`ResumeExtractor.extract(text)` applies every expression and returns an `ExtractionResult`:

| Field | Type | Source expression |
|---|---|---|
| `name` | `str \| None` | `NAME` (first match) |
| `emails`, `phones`, `links` | `list[str]` | `EMAIL`, `PHONE`, `LINK` (distinct, in order of appearance) |
| `experience` | `list[Experience(years, description)]` | `EXPERIENCE` groups `years`, `field` |
| `degrees` | `list[str]` | `DEGREE` |
| `items` | `list[ExtractedItem(value, category, start, end)]` | the five qualification expressions, sorted by position |

Derived views: `programming_languages`, `frameworks`, `databases`, `tools`, `other_qualifications`
(by category), and **`qualifications`**, the distinct qualification strings in order of appearance. That
list is the input of Stage 2.

The result can be saved and reloaded as JSON (`save_json`, `load_json`, or `--out` in the command line).

## 7. Worked example

Input (example from the assignment):

```
Wednesday Addams
3 years of experience developing web applications.
Technical Skills:
JS, React.js, NodeJS, Postgres, Git.
```

| Expression | Matches |
|---|---|
| `NAME` | `Wednesday Addams` |
| `EXPERIENCE` | years = 3, field = `developing web applications` |
| `PROGRAMMING_LANGUAGE` | `JS` (the `js` of `React.js` and `NodeJS` is excluded by the boundaries) |
| `FRAMEWORK_LIBRARY` | `React.js`, `NodeJS` |
| `DATABASE` | `Postgres` |
| `TOOL` | `Git` |

`qualifications` = `[JS, React.js, NodeJS, Postgres, Git]` → input of Stage 2.

## 8. Limitations

- Qualifications are recognized only if they are in the expressions above. A new technology needs a
  new alternative here and a transducer in Stage 2.
- Words are not interpreted in context: "no experience with Docker" still reports `Docker`.
- The name rule depends on layout (a line with only 2–4 capitalized or all-caps words). Names with
  particles in lower case (`Ana de la Cruz`) or with quotes are not detected.
- Experience is only found in the "N years of experience …" form; date ranges of jobs are not added up.
