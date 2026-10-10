"""Qualification pattern of each professional profile.

A pattern is a sequence of stages.  A stage is satisfied when the résumé has
*at least one* of its ``required`` tokens; its ``optional`` tokens may appear
once the stage is satisfied, but are never necessary.

The tokens are the canonical tokens produced by Stage 2 and the stages follow
the canonical order of the profile (``normalization.profiles``), so the sorted
sequence that Stage 2 produces always visits the stages from first to last.
Each pattern is recognised by a DFA built by ``recognition.automata``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

_SQL_DATABASES = ("SQL", "POSTGRESQL", "MYSQL", "MARIADB", "SQLITE", "SQL_SERVER", "ORACLE")
_NOSQL_DATABASES = ("NOSQL", "MONGODB", "REDIS", "CASSANDRA", "DYNAMODB", "FIREBASE")
_ANY_DATABASE = _SQL_DATABASES + _NOSQL_DATABASES
_VERSION_CONTROL = ("GIT", "GITHUB", "GITLAB")
_CLOUD = ("AWS", "AZURE", "GCP")

# Display names of token sets; they keep the transition diagrams readable.
NAMED_SETS: dict[str, tuple[str, ...]] = {
    "ANY_DB": _ANY_DATABASE,
    "SQL_DB": _SQL_DATABASES,
    "NOSQL_DB": _NOSQL_DATABASES,
    "GIT_TOOLS": _VERSION_CONTROL,
    "CLOUD": _CLOUD,
}


@dataclass(frozen=True)
class PatternStage:
    """One requirement of a pattern: 'at least one of ``required``'."""

    name: str
    required: tuple[str, ...]
    optional: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.required:
            raise ValueError(f"Stage {self.name!r} needs at least one required token")
        if set(self.required) & set(self.optional):
            raise ValueError(f"Stage {self.name!r}: a token cannot be required and optional")

    @property
    def tokens(self) -> tuple[str, ...]:
        return self.required + self.optional


@dataclass(frozen=True)
class ProfilePattern:
    """Ordered stages that a résumé must satisfy to be accepted for a profile."""

    name: str
    stages: tuple[PatternStage, ...]

    def __post_init__(self) -> None:
        if not self.stages:
            raise ValueError("A pattern needs at least one stage")
        seen: dict[str, str] = {}
        for stage in self.stages:
            for token in stage.tokens:
                if token in seen:
                    raise ValueError(
                        f"Token {token!r} appears in stages {seen[token]!r} and "
                        f"{stage.name!r}; stage token sets must be disjoint"
                    )
                seen[token] = stage.name

    @property
    def tokens(self) -> list[str]:
        """Σ of the profile automaton: every token mentioned by the pattern."""
        return [t for stage in self.stages for t in stage.tokens]

    def is_satisfied_by(self, tokens: Iterable[str]) -> bool:
        """Reference semantics: every stage has at least one required token.

        Independent of any automaton; used by the tests as an oracle.
        """
        present = set(tokens)
        return all(present & set(stage.required) for stage in self.stages)


#
FULL_STACK_PATTERN = ProfilePattern(
    "FULL_STACK_DEVELOPER",
    (
        PatternStage("LANGUAGE", ("JAVASCRIPT", "TYPESCRIPT")),
        PatternStage("FRONTEND_FRAMEWORK", ("REACT", "ANGULAR", "VUE"), ("NEXT_JS",)),
        PatternStage(
            "BACKEND_TECHNOLOGY",
            ("NODE_JS", "EXPRESS", "DJANGO", "FLASK", "FASTAPI", "SPRING_BOOT"),
            ("REST_API", "GRAPHQL", "MICROSERVICES"),
        ),
        PatternStage("DATABASE", _ANY_DATABASE),
        PatternStage("VERSION_CONTROL", _VERSION_CONTROL),
    ),
)


MACHINE_LEARNING_PATTERN = ProfilePattern(
    "MACHINE_LEARNING_ENGINEER",
    (
        PatternStage("LANGUAGE", ("PYTHON",)),
        PatternStage("DATA_PROCESSING", ("PANDAS", "NUMPY"), ("DATA_PIPELINES",)),
        PatternStage(
            "ML_FRAMEWORK",
            ("SCIKIT_LEARN", "TENSORFLOW", "PYTORCH"),
            ("KERAS", "ML_MODEL_DEVELOPMENT", "DEEP_LEARNING"),
        ),
        PatternStage("DATABASE", _SQL_DATABASES, _NOSQL_DATABASES),
        PatternStage("VERSION_CONTROL", _VERSION_CONTROL),
    ),
)

# Profile 3: DevOps Engineer (software engineering, defined by the team).
DEVOPS_PATTERN = ProfilePattern(
    "DEVOPS_ENGINEER",
    (
        PatternStage("OS_SCRIPTING", ("LINUX", "BASH"), ("PYTHON",)),
        PatternStage("VERSION_CONTROL", _VERSION_CONTROL),
        PatternStage("CI_CD", ("CI_CD", "JENKINS", "GITHUB_ACTIONS")),
        PatternStage("CONTAINERS", ("DOCKER", "KUBERNETES")),
        PatternStage(
            "INFRASTRUCTURE_AS_CODE", ("INFRASTRUCTURE_AS_CODE", "TERRAFORM", "ANSIBLE")
        ),
        PatternStage("CLOUD", _CLOUD, ("PROMETHEUS", "GRAFANA")),
    ),
)


DATA_ENGINEER_PATTERN = ProfilePattern(
    "DATA_ENGINEER",
    (
        PatternStage("LANGUAGE", ("PYTHON", "SCALA", "JAVA")),
        PatternStage("DATA_PROCESSING", ("SPARK", "HADOOP", "DATABRICKS", "KAFKA")),
        PatternStage("ORCHESTRATION_ETL", ("AIRFLOW", "ETL", "DATA_PIPELINES", "DBT")),
        PatternStage(
            "DATABASE",
            _SQL_DATABASES,
            _NOSQL_DATABASES + ("SNOWFLAKE", "BIGQUERY") + _CLOUD,
        ),
        PatternStage("VERSION_CONTROL", _VERSION_CONTROL),
    ),
)

PATTERNS: dict[str, ProfilePattern] = {
    p.name: p
    for p in (
        FULL_STACK_PATTERN,
        MACHINE_LEARNING_PATTERN,
        DEVOPS_PATTERN,
        DATA_ENGINEER_PATTERN,
    )
}


def get_pattern(name: str) -> ProfilePattern:
    try:
        return PATTERNS[name.strip().upper()]
    except KeyError:
        raise ValueError(
            f"Unknown profile {name!r}. Available: {', '.join(PATTERNS)}"
        ) from None
