"""
STEP 2.7 - Database Analyzer.

Detects database technologies, migration files, and schema hints.

Signals:
  - PostgreSQL:  psycopg2, asyncpg, pg, Npgsql, ActiveRecord, SQLAlchemy
                 postgresql:// URLs, docker-compose with postgres
  - MySQL/MariaDB: mysql-connector, pymysql, mysqli, PDO mysql,
                   mysql2, mysql-js
  - SQLite: sqlite3, pysqlite, better-sqlite3, go-sqlite3,
            Room (Android), .sqlite / .db files
  - SQL Server: mssql, pyodbc, tedious, Microsoft.Data.SqlClient,
                *.mdf, SQL Server references
  - MongoDB: pymongo, mongoose, mongodb driver, *.json schema files
  - Redis: redis-py, ioredis, redis-cli references
  - ORM hints: Django ORM (models.py with models.Model),
               SQLAlchemy (Base, declarative_base, session),
               Hibernate (Entity classes), Prisma schema.prisma,
               TypeORM entities, MikroORM,
               Entity Framework (DbContext, DbSet<T>),
               ActiveRecord (app/models), Eloquent (Model),
               GORM, sqlx, pgx
  - Migration tools: Alembic (alembic/), Django migrations
                     (migrations/), Flyway, Liquibase,
                     Prisma migrate, EF Core migrations,
                     Knex migrations, Rails migrations (db/migrate),
                     golang-migrate
  - Schema files: schema.sql, init.sql, structure.sql, dump.sql,
                  *.sql in db/ or migrations/
  - Connection strings in env / config files
"""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import Field

from ..Core import DatabaseContext
from ..Core.detector import Detector

MIGRATION_DIR_HINTS = {"migrations", "db/migrations", "database/migrations", "src/migrations", "migrations/sql"}
MIGRATION_TOOL_FILES = {
    "alembic": ["alembic.ini", "alembic"],
    "django": ["manage.py"],
    "flyway": ["flyway.conf"],
    "liquibase": ["liquibase.properties", "changelog"],
    "prisma": ["prisma/schema.prisma"],
    "knex": ["knexfile.js", "knexfile.ts"],
    "rails": ["db/migrate"],
    "efcore": ["*.csproj"],  # EF Core migrations live alongside code
    "golang-migrate": ["migrate"],  # binary name; unsafe to rely on alone
    "typeorm": ["ormconfig.json", "ormconfig.ts", "data-source.ts"],
    "mikroorm": ["mikro-orm.config.ts", "mikro-orm.config.js"],
}

SQL_SCRIPT_HINTS = ["schema.sql", "init.sql", "structure.sql", "dump.sql", "001_schema.sql", "V1__initial.sql"]


class DatabaseDetector(Detector):
    """STEP 2.7 - Database Analyzer."""

    @property
    def block_name(self) -> str:
        return "database"

    def detect(self) -> dict:
        technologies: list[str] = []
        migration_files: list[str] = []
        schema_hints: list[dict[str, object]] = []
        detected = False

        technologies = _detect_technologies(self.root)
        migration_files = _detect_migrations(self.root)
        schema_hints = _detect_schema_hints(self.root)

        if technologies or migration_files or schema_hints:
            detected = True

        return DatabaseContext(
            technologies=sorted(set(technologies)),
            migration_files=sorted(set(migration_files)),
            schema_hints=schema_hints,
            detected=detected,
        ).model_dump()


def _detect_technologies(root: Path) -> list[str]:
    tech: list[str] = []

    # Connection strings and URLs
    for env_name in (".env", ".env.local", ".env.development", ".env.production", "docker-compose.yml", "docker-compose.yaml"):
        env = root / env_name
        if not env.exists():
            continue
        try:
            text = env.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if re.search(r"postgresql|postgres|psql", text, re.IGNORECASE):
            tech.append("PostgreSQL")
        if re.search(r"mysql|mariadb", text, re.IGNORECASE):
            if "MySQL" not in tech:
                tech.append("MySQL")
        if re.search(r"sqlite", text, re.IGNORECASE):
            tech.append("SQLite")
        if re.search(r"mssql|sqlserver|odbc", text, re.IGNORECASE):
            tech.append("SQL Server")
        if re.search(r"mongodb", text, re.IGNORECASE):
            tech.append("MongoDB")
        if re.search(r"redis", text, re.IGNORECASE):
            tech.append("Redis")
        if re.search(r"oracle|jdbc:oracle", text, re.IGNORECASE):
            tech.append("Oracle")

    # Python deps
    req = root / "requirements.txt"
    if req.exists():
        try:
            text = req.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if "psycopg2" in text or "psycopg" in text:
            tech.append("PostgreSQL")
        if "asyncpg" in text:
            tech.append("PostgreSQL")
        if "pymysql" in text or "mysql-connector" in text:
            tech.append("MySQL")
        if "sqlite3" in text:
            tech.append("SQLite")
        if "pyodbc" in text:
            tech.append("SQL Server")
        if "pymongo" in text or "mongoengine" in text:
            tech.append("MongoDB")
        if "redis" in text:
            tech.append("Redis")
        if "sqlalchemy" in text:
            tech.append("SQLAlchemy (ORM)")
        if "alembic" in text:
            tech.append("Alembic (migrations)")
        if "djangorestframework" in text or "django" in text:
            tech.append("Django ORM")

    # Node deps
    pkg = root / "package.json"
    if pkg.exists():
        try:
            import json as _json
            data = _json.loads(pkg.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        except (OSError, ValueError):
            deps = {}
        if any(k.startswith("pg") or k.startswith("postgres") or k.startswith("psql") for k in deps):
            tech.append("PostgreSQL")
        if any(k.startswith("mysql") or k.startswith("mariadb") for k in deps):
            tech.append("MySQL")
        if any(k.startswith("mongodb") or k.startswith("mongoose") for k in deps):
            tech.append("MongoDB")
        if any(k.startswith("redis") or k == "ioredis" for k in deps):
            tech.append("Redis")
        if any(k.startswith("prisma") for k in deps):
            tech.append("Prisma (ORM)")
            tech.append("PostgreSQL")  # prisma default
        if any(k.startswith("typeorm") for k in deps):
            tech.append("TypeORM (ORM)")
        if any(k.startswith("sequelize") for k in deps):
            tech.append("Sequelize (ORM)")
        if any(k.startswith("better-sqlite3") or k.startswith("sql.js") for k in deps):
            tech.append("SQLite")

    # Go
    if root.joinpath("go.mod").exists():
        try:
            text = root.joinpath("go.mod").read_text(encoding="utf-8")
        except OSError:
            text = ""
        if "gorm" in text:
            tech.append("GORM (ORM)")
        if "sqlx" in text:
            tech.append("sqlx")
        if "pgx" in text or "pg" in text:
            tech.append("PostgreSQL")
        if "mgo" in text or "mongo-go-driver" in text:
            tech.append("MongoDB")
        if "redigo" in text or "go-redis" in text:
            tech.append("Redis")

    # Ruby
    gemfile = root / "Gemfile"
    if gemfile.exists():
        try:
            text = gemfile.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if "pg" in text or "postgresql" in text:
            tech.append("PostgreSQL")
        if "mysql2" in text or "mysql" in text:
            tech.append("MySQL")
        if "sqlite3" in text:
            tech.append("SQLite")
        if "mongo" in text:
            tech.append("MongoDB")
        if "redis" in text:
            tech.append("Redis")

    # .NET
    for csproj in root.glob("*.csproj"):
        try:
            text = csproj.read_text(encoding="utf-8")
        except OSError:
            continue
        if "Npgsql" in text or "postgresql" in text.lower():
            tech.append("PostgreSQL")
        if "Microsoft.Data.SqlClient" in text or "System.Data.SqlClient" in text:
            tech.append("SQL Server")
        if "Pomelo.EntityFrameworkCore.MySql" in text or "MySqlConnector" in text:
            tech.append("MySQL")
        if "Microsoft.EntityFrameworkCore.Sqlite" in text:
            tech.append("SQLite")
        if "MongoDB.Driver" in text:
            tech.append("MongoDB")

    # Java
    pom = root / "pom.xml"
    if pom.exists():
        try:
            text = pom.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if "postgresql" in text.lower() or "org.postgresql" in text:
            tech.append("PostgreSQL")
        if "mysql" in text.lower() or "com.mysql" in text:
            tech.append("MySQL")
        if "mongodb" in text.lower() or "org.mongodb" in text:
            tech.append("MongoDB")
        if "hibernate" in text.lower():
            tech.append("Hibernate (ORM)")

    # ORM files
    if root.joinpath("prisma/schema.prisma").exists():
        tech.append("Prisma (ORM)")
    if root.joinpath("schema.prisma").exists():
        tech.append("Prisma (ORM)")
    if list(root.glob("**/entities/*.ts")) or list(root.glob("**/models/*.ts")):
        if any("typeorm" in t.lower() for t in tech) or any("mikro" in t.lower() for t in tech):
            pass  # already captured
        else:
            tech.append("TypeScript ORM entities (TypeORM / MikroORM likely)")

    # Django
    if root.joinpath("manage.py").exists():
        tech.append("Django ORM")
    if list(root.glob("**/models.py")):
        if "Django ORM" not in tech and "django" not in " ".join(tech).lower():
            pass  # heuristics: models.py alone isn't enough without a framework signal

    # SQLAlchemy
    if list(root.glob("**/models.py")):
        try:
            for mp in root.glob("**/models.py"):
                if "sqlalchemy" in mp.read_text(encoding="utf-8", errors="ignore").lower():
                    tech.append("SQLAlchemy (ORM)")
                    break
        except OSError:
            pass

    # Entity Framework
    if list(root.glob("**/*DbContext.cs")) or list(root.glob("**/DbContext.cs")):
        tech.append("Entity Framework (ORM)")

    # Hibernate
    if list(root.glob("**/*Entity.java")) or list(root.glob("**/src/main/java/**/*Entity.java")):
        tech.append("Hibernate (ORM)")

    return tech


def _detect_migrations(root: Path) -> list[str]:
    files: list[str] = []

    # Directory-based migration systems
    for hint in MIGRATION_DIR_HINTS:
        for p in root.glob(hint + "/**/*"):
            if p.is_file():
                files.append(p.relative_to(root).as_posix())

    # Tool-specific signals
    if root.joinpath("alembic.ini").exists():
        for p in root.glob("alembic/versions/**/*.py"):
            if p.is_file():
                files.append(p.relative_to(root).as_posix())

    if root.joinpath("manage.py").exists():
        for p in root.glob("**/migrations/**/*.py"):
            if p.is_file() and p.name != "__init__.py":
                files.append(p.relative_to(root).as_posix())

    if root.joinpath("prisma/schema.prisma").exists():
        files.append("prisma/schema.prisma")

    # Rails
    if root.joinpath("Gemfile").exists():
        try:
            if "rails" in root.joinpath("Gemfile").read_text(encoding="utf-8", errors="ignore"):
                for p in root.glob("db/migrate/*.rb"):
                    if p.is_file():
                        files.append(p.relative_to(root).as_posix())
        except OSError:
            pass

    # SQL scripts
    for hint in SQL_SCRIPT_HINTS:
        for p in root.rglob(hint):
            if p.is_file():
                files.append(p.relative_to(root).as_posix())

    for p in root.rglob("*.sql"):
        if p.is_file():
            files.append(p.relative_to(root).as_posix())

    return files


def _detect_schema_hints(root: Path) -> list[dict[str, object]]:
    hints: list[dict[str, object]] = []

    # Look for well-known schema files
    for p in root.rglob("*.sql"):
        if p.is_file():
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            tables = re.findall(r"CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?([\w.]+)", text, re.IGNORECASE)
            if tables:
                hints.append({
                    "file": p.relative_to(root).as_posix(),
                    "type": "sql",
                    "tables": [t[1] for t in tables],
                })

    # Prisma schema
    for p in root.rglob("schema.prisma"):
        if p.is_file():
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            models = re.findall(r"model\s+(\w+)", text)
            hints.append({
                "file": p.relative_to(root).as_posix(),
                "type": "prisma",
                "models": models,
            })

    return hints
