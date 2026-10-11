"""Canonical order of qualifications for each professional profile.

The order is used to sort the normalized qualifications before they are sent
to the Stage 3 automata, so the result does not depend on the order in which
the candidate wrote them.

Profiles 1 and 2 are predefined by the assignment; profiles 3 (software
engineering) and 4 (AI/data) were defined by the team.
"""

from __future__ import annotations

from dataclasses import dataclass

_DATABASES = (
    "SQL", "POSTGRESQL", "MYSQL", "MARIADB", "SQLITE", "SQL_SERVER", "ORACLE",
    "NOSQL", "MONGODB", "REDIS", "CASSANDRA", "DYNAMODB", "FIREBASE",
)
_VERSION_CONTROL = ("GIT", "GITHUB", "GITLAB")
_CLOUD = ("AWS", "AZURE", "GCP")


@dataclass(frozen=True)
class ProfileOrder:
    """Ordered groups (category -> tokens) that define a profile's order."""

    name: str
    groups: tuple[tuple[str, tuple[str, ...]], ...]

    def rank(self, token: str) -> tuple[int, int] | None:
        """(group index, index inside the group) or ``None`` if not in profile."""
        for g, (_, tokens) in enumerate(self.groups):
            if token in tokens:
                return g, tokens.index(token)
        return None

    @property
    def tokens(self) -> list[str]:
        return [t for _, tokens in self.groups for t in tokens]


FULL_STACK_DEVELOPER = ProfileOrder(
    "FULL_STACK_DEVELOPER",
    (
        ("FRONTEND", ("JAVASCRIPT", "TYPESCRIPT", "REACT", "ANGULAR", "VUE", "NEXT_JS")),
        ("BACKEND", ("NODE_JS", "EXPRESS", "DJANGO", "FLASK", "FASTAPI", "SPRING_BOOT",
                     "REST_API", "GRAPHQL", "MICROSERVICES")),
        ("DATABASE", _DATABASES),
        ("VERSION_CONTROL", _VERSION_CONTROL),
    ),
)

MACHINE_LEARNING_ENGINEER = ProfileOrder(
    "MACHINE_LEARNING_ENGINEER",
    (
        ("PROGRAMMING_LANGUAGE", ("PYTHON",)),
        ("DATA_PROCESSING", ("PANDAS", "NUMPY", "DATA_PIPELINES")),
        ("ML_LIBRARY", ("SCIKIT_LEARN",)),
        ("DL_FRAMEWORK", ("TENSORFLOW", "PYTORCH", "KERAS")),
        ("ML_DEVELOPMENT", ("ML_MODEL_DEVELOPMENT", "DEEP_LEARNING")),
        ("DATABASE", _DATABASES),
        ("VERSION_CONTROL", _VERSION_CONTROL),
    ),
)

# Profile 3 (software engineering, defined by the team)
DEVOPS_ENGINEER = ProfileOrder(
    "DEVOPS_ENGINEER",
    (
        ("OS_SCRIPTING", ("LINUX", "BASH", "PYTHON")),
        ("VERSION_CONTROL", _VERSION_CONTROL),
        ("CI_CD", ("CI_CD", "JENKINS", "GITHUB_ACTIONS")),
        ("CONTAINERS", ("DOCKER", "KUBERNETES")),
        ("INFRASTRUCTURE_AS_CODE", ("INFRASTRUCTURE_AS_CODE", "TERRAFORM", "ANSIBLE")),
        ("CLOUD", _CLOUD),
        ("MONITORING", ("PROMETHEUS", "GRAFANA")),
    ),
)

# Profile 4 (AI/data, defined by the team)
DATA_ENGINEER = ProfileOrder(
    "DATA_ENGINEER",
    (
        ("PROGRAMMING_LANGUAGE", ("PYTHON", "SCALA", "JAVA")),
        ("DATA_PROCESSING", ("SPARK", "HADOOP", "DATABRICKS", "KAFKA")),
        ("ORCHESTRATION_ETL", ("AIRFLOW", "ETL", "DATA_PIPELINES", "DBT")),
        ("DATABASE", _DATABASES),
        ("DATA_WAREHOUSE", ("SNOWFLAKE", "BIGQUERY")),
        ("CLOUD", _CLOUD),
        ("VERSION_CONTROL", _VERSION_CONTROL),
    ),
)

PROFILES: dict[str, ProfileOrder] = {
    p.name: p
    for p in (FULL_STACK_DEVELOPER, MACHINE_LEARNING_ENGINEER, DEVOPS_ENGINEER, DATA_ENGINEER)
}


def get_profile(name: str) -> ProfileOrder:
    try:
        return PROFILES[name.strip().upper()]
    except KeyError:
        raise ValueError(
            f"Unknown profile {name!r}. Available: {', '.join(PROFILES)}"
        ) from None
