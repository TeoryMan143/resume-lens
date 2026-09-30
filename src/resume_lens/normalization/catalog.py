"""Canonical qualifications and the surface variants that map to each one.

Each entry becomes one finite-state transducer T_<CANONICAL>. Variants are
written as they appear in résumés; the lexical-cleaning transducer (T_clean)
lower-cases them and deletes separators (' ', '-', '.', '_', '/') before the
canonical-mapping transducers read them, so for instance 'Scikit-learn',
'scikit learn' and 'scikitlearn' all reach T_SCIKIT_LEARN as 'scikitlearn'.

Every variant listed here can be produced by a Stage 1 regular expression
(this is checked by the test suite).
"""

from __future__ import annotations

CANONICAL_VARIANTS: dict[str, tuple[str, ...]] = {
    # --- programming languages ------------------------------------------------
    "JAVASCRIPT": ("JS", "JavaScript", "Java Script", "ECMAScript", "ES6"),
    "TYPESCRIPT": ("TS", "TypeScript"),
    "PYTHON": ("Python", "Python3", "Python 3"),
    "JAVA": ("Java",),
    "C_PLUS_PLUS": ("C++", "CPP"),
    "C_SHARP": ("C#", "CSharp", "C Sharp"),
    "GO": ("Golang",),
    "KOTLIN": ("Kotlin",),
    "SWIFT": ("Swift",),
    "RUST": ("Rust",),
    "PHP": ("PHP",),
    "RUBY": ("Ruby",),
    "SCALA": ("Scala",),
    # --- frontend frameworks --------------------------------------------------
    "REACT": ("React", "React.js", "ReactJS"),
    "ANGULAR": ("Angular", "AngularJS", "Angular.js"),
    "VUE": ("Vue", "Vue.js", "VueJS"),
    "NEXT_JS": ("Next.js", "NextJS"),
    # --- backend frameworks ---------------------------------------------------
    "NODE_JS": ("Node", "Node.js", "NodeJS"),
    "EXPRESS": ("Express.js", "ExpressJS"),
    "DJANGO": ("Django",),
    "FLASK": ("Flask",),
    "FASTAPI": ("FastAPI", "Fast API"),
    "SPRING_BOOT": ("Spring Boot", "SpringBoot"),
    # --- data / ML libraries --------------------------------------------------
    "PANDAS": ("pandas",),
    "NUMPY": ("NumPy", "Num Py"),
    "SCIKIT_LEARN": ("Scikit-learn", "scikit learn", "scikitlearn", "sklearn"),
    "TENSORFLOW": ("TensorFlow", "Tensor Flow"),
    "PYTORCH": ("PyTorch", "Py Torch"),
    "KERAS": ("Keras",),
    "MATPLOTLIB": ("Matplotlib",),
    # --- databases --------------------------------------------------------------
    "SQL": ("SQL",),
    "NOSQL": ("NoSQL", "No SQL"),
    "POSTGRESQL": ("PostgreSQL", "Postgres"),
    "MYSQL": ("MySQL", "My SQL"),
    "MARIADB": ("MariaDB",),
    "SQLITE": ("SQLite",),
    "SQL_SERVER": ("SQL Server", "SQLServer"),
    "ORACLE": ("Oracle",),
    "MONGODB": ("MongoDB", "Mongo DB", "Mongo"),
    "REDIS": ("Redis",),
    "CASSANDRA": ("Cassandra",),
    "DYNAMODB": ("DynamoDB",),
    "FIREBASE": ("Firebase",),
    # --- tools ------------------------------------------------------------------
    "GIT": ("Git",),
    "GITHUB": ("GitHub",),
    "GITLAB": ("GitLab",),
    "DOCKER": ("Docker",),
    "KUBERNETES": ("Kubernetes", "K8s"),
    "AWS": ("AWS", "Amazon Web Services"),
    "AZURE": ("Azure",),
    "GCP": ("GCP",),
    "LINUX": ("Linux",),
    "JUPYTER": ("Jupyter", "Jupyter Notebook", "Jupyter Notebooks"),
    "JENKINS": ("Jenkins",),
    "POSTMAN": ("Postman",),
    "JIRA": ("Jira",),
    "MLFLOW": ("MLflow",),
    "AIRFLOW": ("Airflow",),
    "SPARK": ("Spark",),
    "HADOOP": ("Hadoop",),
    # --- other qualifications -------------------------------------------------
    "REST_API": ("REST API", "REST APIs", "RESTful API", "RESTful APIs", "REST-API"),
    "GRAPHQL": ("GraphQL",),
    "MICROSERVICES": ("Microservices",),
    "CI_CD": ("CI/CD",),
    "ML_MODEL_DEVELOPMENT": (
        "Machine Learning",
        "Machine-learning",
        "Machine Learning Model",
        "Machine Learning Models",
        "Predictive Model",
        "Predictive Models",
    ),
    "DEEP_LEARNING": ("Deep Learning", "Deep-learning"),
    "DATA_PIPELINES": (
        "Data Processing",
        "Data-processing",
        "Data Processing Pipeline",
        "Data-processing pipelines",
        "Data Pipeline",
        "Data Pipelines",
    ),
}
