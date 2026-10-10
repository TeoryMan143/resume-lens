"""Stage 3 — Qualification patterns of the four professional profiles.

Every pattern follows the canonical order of its profile in
``normalization.profiles``: one stage per group of that order (a few groups are
merged into the optional complements of a neighbouring stage).  A single
generic builder (``recognition.automata``) turns any pattern into a DFA, which
is what lets the four profiles share one implementation.
"""

from __future__ import annotations

from typing import Iterable

from .models import PatternStage, ProfilePattern

# --- Named token sets (also used to keep diagrams readable) -------------------
SQL_DATABASES = frozenset(
    {"SQL", "POSTGRESQL", "MYSQL", "MARIADB", "SQLITE", "SQL_SERVER", "ORACLE"}
)
NOSQL_DATABASES = frozenset(
    {"NOSQL", "MONGODB", "REDIS", "CASSANDRA", "DYNAMODB", "FIREBASE"}
)
ANY_DATABASE = SQL_DATABASES | NOSQL_DATABASES
GIT_TOOLS = frozenset({"GIT", "GITHUB", "GITLAB"})
CLOUD_PROVIDERS = frozenset({"AWS", "AZURE", "GCP"})

#: Display names for token sets, ordered so the largest set is tried first.
NAMED_SETS: dict[str, frozenset[str]] = {
    "ANY_DB": ANY_DATABASE,
    "SQL_DB": SQL_DATABASES,
    "NOSQL_DB": NOSQL_DATABASES,
    "GIT_TOOLS": GIT_TOOLS,
    "CLOUD": CLOUD_PROVIDERS,
}


def _stage(name: str, required: Iterable[str], optional: Iterable[str] = ()) -> PatternStage:
    return PatternStage(name, frozenset(required), frozenset(optional))


# --- Profile 1: Full Stack Developer (predefined) -----------------------------
FULL_STACK_PATTERN = ProfilePattern(
    "FULL_STACK_DEVELOPER",
    "JavaScript or TypeScript, a frontend framework (React, Angular or Vue), a "
    "backend technology (Node.js, Express, Django, Flask, FastAPI or Spring "
    "Boot), a SQL or NoSQL database and Git.  REST APIs, GraphQL, "
    "microservices and Next.js are accepted as complements.",
    (
        _stage("LANGUAGE", {"JAVASCRIPT", "TYPESCRIPT"}),
        _stage("FRONTEND_FRAMEWORK", {"REACT", "ANGULAR", "VUE"}, {"NEXT_JS"}),
        _stage(
            "BACKEND_TECHNOLOGY",
            {"NODE_JS", "EXPRESS", "DJANGO", "FLASK", "FASTAPI", "SPRING_BOOT"},
            {"REST_API", "GRAPHQL", "MICROSERVICES"},
        ),
        _stage("DATABASE", ANY_DATABASE),
        _stage("VERSION_CONTROL", GIT_TOOLS),
    ),
)

# --- Profile 2: Machine Learning Engineer (predefined) ------------------------
MACHINE_LEARNING_PATTERN = ProfilePattern(
    "MACHINE_LEARNING_ENGINEER",
    "Python, a data-processing library (Pandas or NumPy), a machine-learning "
    "framework (Scikit-learn, TensorFlow or PyTorch), a SQL database and Git.  "
    "Data pipelines, Keras, model development and deep learning are accepted "
    "as complements; NoSQL databases are accepted next to the SQL one.",
    (
        _stage("LANGUAGE", {"PYTHON"}),
        _stage("DATA_PROCESSING", {"PANDAS", "NUMPY"}, {"DATA_PIPELINES"}),
        _stage(
            "ML_FRAMEWORK",
            {"SCIKIT_LEARN", "TENSORFLOW", "PYTORCH"},
            {"KERAS", "ML_MODEL_DEVELOPMENT", "DEEP_LEARNING"},
        ),
        _stage("DATABASE", SQL_DATABASES, NOSQL_DATABASES),
        _stage("VERSION_CONTROL", GIT_TOOLS),
    ),
)

# --- Profile 3: DevOps Engineer (team-defined, software engineering) ----------
DEVOPS_PATTERN = ProfilePattern(
    "DEVOPS_ENGINEER",
    "Linux or Bash, a Git-based version-control tool, a CI/CD practice or tool "
    "(CI/CD, Jenkins, GitHub Actions), a container technology (Docker or "
    "Kubernetes), infrastructure as code (IaC, Terraform or Ansible) and a "
    "cloud provider (AWS, Azure or GCP).  Python scripting and monitoring tools "
    "(Prometheus, Grafana) are accepted as complements.",
    (
        _stage("OS_SCRIPTING", {"LINUX", "BASH"}, {"PYTHON"}),
        _stage("VERSION_CONTROL", GIT_TOOLS),
        _stage("CI_CD", {"CI_CD", "JENKINS", "GITHUB_ACTIONS"}),
        _stage("CONTAINERS", {"DOCKER", "KUBERNETES"}),
        _stage("INFRASTRUCTURE_AS_CODE", {"INFRASTRUCTURE_AS_CODE", "TERRAFORM", "ANSIBLE"}),
        _stage("CLOUD", CLOUD_PROVIDERS, {"PROMETHEUS", "GRAFANA"}),
    ),
)

# --- Profile 4: Data Engineer (team-defined, AI / data) -----------------------
DATA_ENGINEER_PATTERN = ProfilePattern(
    "DATA_ENGINEER",
    "A programming language (Python, Scala or Java), a data-processing "
    "technology (Spark, Hadoop, Databricks or Kafka), an orchestration / ETL "
    "practice or tool (Airflow, ETL, data pipelines or dbt), a SQL database and "
    "Git.  NoSQL databases, data warehouses (Snowflake, BigQuery) and cloud "
    "providers are accepted as complements.",
    (
        _stage("LANGUAGE", {"PYTHON", "SCALA", "JAVA"}),
        _stage("DATA_PROCESSING", {"SPARK", "HADOOP", "DATABRICKS", "KAFKA"}),
        _stage("ORCHESTRATION_ETL", {"AIRFLOW", "ETL", "DATA_PIPELINES", "DBT"}),
        _stage(
            "DATABASE",
            SQL_DATABASES,
            NOSQL_DATABASES | {"SNOWFLAKE", "BIGQUERY"} | CLOUD_PROVIDERS,
        ),
        _stage("VERSION_CONTROL", GIT_TOOLS),
    ),
)

PATTERNS: dict[str, ProfilePattern] = {
    p.profile: p
    for p in (
        FULL_STACK_PATTERN,
        MACHINE_LEARNING_PATTERN,
        DEVOPS_PATTERN,
        DATA_ENGINEER_PATTERN,
    )
}
