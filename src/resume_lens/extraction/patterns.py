"""Stage 1 — Regular expressions used to extract information from résumés.

Every pattern is documented with the language (set of strings) it recognizes.
Stage 1 only *detects* candidate strings: it does not decide whether two
strings are equivalent (Stage 2) nor whether a profile is satisfied (Stage 3).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class Category(str, Enum):
    """Kinds of information that Stage 1 can extract."""

    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    LINK = "link"
    EXPERIENCE = "experience"
    DEGREE = "degree"
    PROGRAMMING_LANGUAGE = "programming_language"
    FRAMEWORK_LIBRARY = "framework_library"
    DATABASE = "database"
    TOOL = "tool"
    OTHER_QUALIFICATION = "other_qualification"


# Categories whose matches are qualifications (input of Stage 2).
QUALIFICATION_CATEGORIES: tuple[Category, ...] = (
    Category.PROGRAMMING_LANGUAGE,
    Category.FRAMEWORK_LIBRARY,
    Category.DATABASE,
    Category.TOOL,
    Category.OTHER_QUALIFICATION,
)


@dataclass(frozen=True)
class RegexPattern:
    """A named regular expression together with its explanation."""

    category: Category
    expression: str
    description: str
    flags: int = 0
    compiled: re.Pattern = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "compiled", re.compile(self.expression, self.flags))

    def find_all(self, text: str) -> list[re.Match]:
        return list(self.compiled.finditer(text))


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------
# A technology token must not be glued to other word characters, nor preceded
# by '.', '/', '@' or '-' (so "js" inside "React.js" is not the language JS and
# "github" inside "https://github.com/..." is not the tool GitHub). On the right
# it must not be followed by a word character or by '.' + letter (a domain).
_LEFT = r"(?<![\w.#+/@-])"
_RIGHT = r"(?![\w+#]|\.\w)"


def _tech(alternatives: str) -> str:
    return rf"{_LEFT}(?:{alternatives}){_RIGHT}"


# ---------------------------------------------------------------------------
# Contact / personal information
# ---------------------------------------------------------------------------
NAME = RegexPattern(
    Category.NAME,
    r"^[ \t]*(?P<name>[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:[ \t]+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})[ \t]*$",
    "A line made only of 2 to 4 capitalised words (e.g. 'Mary Jane Watson'). "
    "Only the first matching line of the résumé is taken as the candidate name.",
    re.MULTILINE,
)

EMAIL = RegexPattern(
    Category.EMAIL,
    r"(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w-])",
    "local-part '@' domain '.' TLD, where local-part ∈ [A-Za-z0-9._%+-]+ and "
    "the TLD has at least two letters (e.g. 'wednesday@nevermore.edu').",
)

PHONE = RegexPattern(
    Category.PHONE,
    r"(?<![\w+])(?:\+\d{1,3}[ .-]?)?(?:\(\d{2,4}\)[ .-]?|\d{2,4}[ .-]?)?\d{3}[ .-]?\d{4}(?![\w])",
    "Optional international prefix (+CC), optional area code (with or without "
    "parentheses) and a 7-digit local number split as 3+4 digits; groups may be "
    "separated by one space, dot or hyphen (e.g. '+57 300 123 4567', '(602) 555-0199').",
)

LINK = RegexPattern(
    Category.LINK,
    r"(?:https?://)?(?:www\.)?(?:linkedin\.com/in|github\.com)/[A-Za-z0-9_-]+/?",
    "LinkedIn profile or GitHub account URL, with optional scheme and 'www.' "
    "(e.g. 'https://github.com/wednesday', 'linkedin.com/in/mary-jane').",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Experience and education
# ---------------------------------------------------------------------------
EXPERIENCE = RegexPattern(
    Category.EXPERIENCE,
    r"(?P<years>\d{1,2})\+?[ \t]*(?:years?|yrs?\.?|años?)[ \t]+(?:of[ \t]+|de[ \t]+)?"
    r"(?:professional[ \t]+|profesional[ \t]+)?(?:experience|experiencia)"
    r"(?:[ \t]+(?P<field>(?:in|with|developing|building|as|en|como|desarrollando)[ \t]+[^.\n]+))?",
    "A number of years (1–2 digits, optional '+') followed by 'year(s)/yr(s)/año(s) "
    "of experience' and, optionally, the activity it refers to up to the end of the "
    "sentence (e.g. '3 years of experience developing web applications').",
    re.IGNORECASE,
)

_FIELD = (
    r"(?:[ \t]+(?:of|in|en|de)[ \t]+(?:Science[ \t]+in[ \t]+)?"
    r"[A-ZÁÉÍÓÚ][\wáéíóúñ]*(?:[ \t]+(?:[A-ZÁÉÍÓÚ][\wáéíóúñ]*|and|&|de|y))*)"
)
DEGREE = RegexPattern(
    Category.DEGREE,
    r"\b(?:(?:Bachelor|Master)(?:'s)?\b(?:[ \t]+[Dd]egree)?|Doctorate\b|MBA\b"
    r"|Ph\.?[ ]?D\b\.?|B\.?[ ]?Sc\b\.?|M\.?[ ]?Sc\b\.?"
    r"|Ingenier(?:o|a|ía|ia)\b|Maestr(?:ía|ia)\b|Licenciatura\b)" + _FIELD + "?",
    "A degree keyword (Bachelor, Master, Doctorate, MBA, Ph.D., B.Sc., M.Sc., "
    "Ingeniería, Maestría, Licenciatura) optionally followed by 'of/in/en/de' and a "
    "capitalised field of study (e.g. 'B.Sc. in Computer Science').",
)

# ---------------------------------------------------------------------------
# Qualifications (surface forms, NOT normalised)
# ---------------------------------------------------------------------------
PROGRAMMING_LANGUAGE = RegexPattern(
    Category.PROGRAMMING_LANGUAGE,
    _tech(
        r"Java[ ]?Script|ECMAScript|ES6|JS|TypeScript|TS|Python[ ]?3?|Java(?![ ]?Script)"
        r"|C\+\+|CPP|C#|C[ ]?Sharp|Kotlin|Swift|Golang|Rust|PHP|Ruby|Scala"
    ),
    "Names and common abbreviations of programming languages, case-insensitive "
    "(JavaScript, Java Script, JS, TypeScript, TS, Python, Java, C++, C#, Kotlin, ...). "
    "Tokens glued to letters or preceded by '.' are excluded, so 'js' in 'React.js' "
    "and 'Java' in 'JavaScript' are not reported.",
    re.IGNORECASE,
)

FRAMEWORK_LIBRARY = RegexPattern(
    Category.FRAMEWORK_LIBRARY,
    _tech(
        r"React(?:\.?js)?|Angular(?:\.?js)?|Vue(?:\.?js)?|Node(?:\.?js)?|Express(?:\.?js)"
        r"|Next\.?js|Django|Flask|Fast[ ]?API|Spring[ ]?Boot"
        r"|Pandas|Num[ ]?Py|Scikit[ -]?learn|sklearn|Tensor[ ]?Flow|Py[ ]?Torch|Keras|Matplotlib"
    ),
    "Frameworks and libraries with their usual spellings: optional '.js'/'js' suffix "
    "for JS frameworks, optional space/hyphen inside compound names "
    "(Tensor Flow, Py Torch, scikit learn, Scikit-learn), and the alias 'sklearn'.",
    re.IGNORECASE,
)

DATABASE = RegexPattern(
    Category.DATABASE,
    _tech(
        r"PostgreSQL|Postgres|MySQL|My[ ]SQL|MariaDB|SQLite|Mongo[ ]?DB|Mongo|Redis"
        r"|Oracle|SQL[ ]?Server|No[ ]?SQL|SQL|Cassandra|DynamoDB|Firebase"
    ),
    "Database engines and database families (SQL, NoSQL). 'SQL' is only reported "
    "as a standalone word, never inside 'PostgreSQL', 'MySQL' or 'NoSQL'.",
    re.IGNORECASE,
)

TOOL = RegexPattern(
    Category.TOOL,
    _tech(
        r"Git(?:Hub|Lab)?|Docker|Kubernetes|K8s|AWS|Amazon[ ]Web[ ]Services|Azure|GCP"
        r"|Linux|Jupyter(?:[ ]Notebooks?)?|Jenkins|Postman|Jira|MLflow|Airflow|Spark|Hadoop"
    ),
    "Development tools, version control systems and cloud platforms "
    "(Git, GitHub, GitLab, Docker, Kubernetes, AWS, Jupyter, ...).",
    re.IGNORECASE,
)

OTHER_QUALIFICATION = RegexPattern(
    Category.OTHER_QUALIFICATION,
    r"(?<![\w])(?:REST(?:ful)?[ -]?APIs?|GraphQL|Machine[ -]Learning(?:[ ]Models?)?"
    r"|Deep[ -]Learning|Predictive[ ]Models?|Data[ -]Processing(?:[ ]Pipelines?)?"
    r"|Data[ ]Pipelines?|Microservices|CI/CD)(?![\w])",
    "Multi-word skills and concepts relevant to the profiles: REST/RESTful API(s), "
    "GraphQL, machine learning (models), deep learning, predictive models, "
    "data-processing pipelines, microservices and CI/CD.",
    re.IGNORECASE,
)

PATTERNS: dict[Category, RegexPattern] = {
    p.category: p
    for p in (
        NAME,
        EMAIL,
        PHONE,
        LINK,
        EXPERIENCE,
        DEGREE,
        PROGRAMMING_LANGUAGE,
        FRAMEWORK_LIBRARY,
        DATABASE,
        TOOL,
        OTHER_QUALIFICATION,
    )
}
