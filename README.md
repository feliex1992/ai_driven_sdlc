# AI-Driven SDLC

A framework for building an **AI Software Factory** — a system that automates
the software development lifecycle from requirement analysis through deployment
and operations, with AI as the engineering workforce and deterministic tools
as the execution/verification layer.

The core principle:

> AI provides intelligence. Deterministic engineering tools provide execution
> and verification.

High-impact decisions (destructive DB changes, major architecture changes,
breaking API changes, security exceptions, production deployment) require
human approval.

---

## Vision

The end goal is a factory where a user states a requirement and the system
drives it through:

```text
Requirement → Analysis → Architecture → Planning →
Project Creation → Development → Testing → Security →
Code Review → CI/CD → Release → Deployment → SRE
```

Each stage is an agent producing a structured, schema-validated artifact
that the next stage consumes — not free-form LLM chat.

---

## Where we are

The project is organized as a sequence of steps. See `ROADMAP.md` for the
full 17-step plan.

### Completed

**STEP 1 — Foundation** ✅

Engineering rules for AI agents:

```text
.ai/rules/
├── 00-core.md        Core behavior (understand before changing, minimal change, traceability)
├── 01-architecture.md Respect existing architecture, separation of concerns
├── 02-coding.md      Correctness, readability, existing conventions
├── 03-testing.md     Required scenarios, test levels, failure analysis
├── 04-security.md    Input validation, auth, data protection, parameterized queries
├── 05-database.md    Migrations, backward compatibility, destructive changes
└── 06-git.md         Branching, commits, PR contents, commit safety
```

**STEP 1.5 — Agent Contracts / Schemas** ✅

JSON Schema contracts that every agent output must satisfy. This keeps the
pipeline deterministic — agent → JSON contract → validator → gate → next agent.

```text
.ai/schemas/
├── common.schema.json        Shared finding/artifact structure
├── analysis.schema.json      Analyst output
├── design.schema.json        Architect output
├── task.schema.json          Planner output
├── implementation.schema.json Developer output
├── test.schema.json          Test Agent output
├── security.schema.json      Security Agent output
└── review.schema.json        Code Review Agent output
```

**STEP 2 — Context Engine** ✅

A Python package that reads a repository and produces structured
`.ai/context/*.json` files so downstream agents start from evidence, not
guesses. 8 detectors, CLI, 41 passing tests.

```text
src/SoftwareFactory/Context/
├── Core/             Models (8 Context types), ContextEngine, ContextWriter, scan_root()
├── Detectors/        filesystem, language, architecture, dependencies,
│                     api, database, test, git
└── CLI/              `ai context scan <path>` → writes .ai/context/*.json

tests/SoftwareFactory.Tests/test_context_engine.py   ← 41 tests
```

**STEP 3 — AI CLI** ✅

The CLI is the control plane for the AI Software Factory. It combines the Context Engine with a full workflow management system and 8 single-stage commands — one per SDLC stage.

```text
src/SoftwareFactory/SDLC/
├── workflow.py              Workflow model, WorkflowStore, STAGES, STAGE_LABELS
└── Agents/
    ├── __init__.py          exports AgentRunner, AgentKind, invoke_agent
    └── runner.py            AgentRunner, AgentKind enum (8 agents), invoke_agent() stub

src/SoftwareFactory/Context/CLI/
├── __init__.py              delegates to run.main()
├── __main__.py              python -m entry point
└── run.py                   full CLI
```

Perintah:

```text
ai context scan <path>       Scan repo → .ai/context/*.json
ai status                     Show active workflow state
ai init <feature> <req>      Start new workflow
ai run <feature> <req>       Run full pipeline
ai run <feature> <req> --stages s1 s2 s3   Run selected stages
ai analyze                    Run analysis stage
ai design                     Run architecture stage
ai plan                       Run planning stage
ai implement                  Run development stage
ai test                       Run testing stage
ai security                   Run security stage
ai review                     Run code review stage
ai deploy                     Run deployment stage
```

Workflow stages:

```text
analyze  → Analyst Agent    requirement → analysis.json
design   → Architect Agent  analysis + context → design.json
plan     → Planner Agent    design → task.json
implement → Developer Agent  task → code
test     → Test Agent       implementation → test results
security → Security Agent   code + findings → security.json
review   → Review Agent     diff + context → review.json
deploy   → Deployer Agent   ready → deployed
```

Example session:

```bash
# Start a workflow
.venv/bin/python -m SoftwareFactory.Context.CLI init "membership freeze" \
  "Buat fitur freeze membership untuk member tidak aktif"

# Check progress
.venv/bin/python -m SoftwareFactory.Context.CLI status

# Run a single stage
.venv/bin/python -m SoftwareFactory.Context.CLI analyze

# Run selected stages
.venv/bin/python -m SoftwareFactory.Context.CLI run "membership freeze" \
  --stages analysis architecture planning

# Resume from where it stopped
.venv/bin/python -m SoftwareFactory.Context.CLI run "membership freeze"
```

Workflow state is stored in `.ai/workflow/*.json`. The agent runner is a stub today — it produces structured output matching the STEP 1.5 contracts. LLM-backed agents will replace the stubs in STEP 4+.

---

## The CLI — usage guide

From the `ai_driven_sdlc` directory:

```bash
.venv/bin/python -m SoftwareFactory.Context.CLI <command> [args]
```

Or install as a script:

```bash
.venv/bin/pip install -e .
ai <command> [args]
```

### Commands

#### Context scanning

```bash
ai context scan /path/to/repo
```

Scans the repository and writes 8 `.ai/context/*.json` files, then prints a
human-readable summary. See the [Context Engine section](#the-context-engine-step-2-how-to-use-it)
for details on the output files.

#### Workflow management

```bash
# Start a new workflow
ai init "feature-name" "Requirement description"

# Check status of active workflow
ai status

# Run the full pipeline
ai run "feature-name" "Requirement description"

# Run only selected stages
ai run "feature-name" "Requirement description" --stages analysis architecture planning
```

#### Single-stage execution

```bash
ai analyze      # Analyst: requirement → analysis
ai design       # Architect: analysis + context → design
ai plan         # Planner: design → tasks
ai implement    # Developer: tasks → code
ai test         # Tester: code → test results
ai security     # Security: code → security findings
ai review       # Reviewer: diff + context → review
ai deploy       # Deployer: ready → deployed
```

Each single-stage command reads the current workflow state, runs the stage via
the agent runner (stub today), saves the result, and updates the workflow.

### Workflow state file

Stored at `.ai/workflow/<workflow_id>.json`. Contains:

```json
{
  "workflow_id": "WF-2026-001",
  "project_root": "...",
  "feature": "membership freeze",
  "requirement": "...",
  "status": "in_progress",
  "current_stage": "development",
  "stages": {
    "analysis": { "status": "completed", "note": "...", "output_path": "..." },
    "architecture": { "status": "completed", ... },
    "planning": { "status": "completed", ... },
    "development": { "status": "pending", ... },
    "testing": { "status": "pending", ... },
    "security": { "status": "pending", ... },
    "review": { "status": "pending", ... },
    "deployment": { "status": "pending", ... }
  }
}
```

### Status codes

| Symbol | Meaning |
|--------|---------|
| ✓ | Completed |
| → | Current / in progress |
| ○ | Pending |
| ✗ / ⚠ | Blocked |

### What's stub vs real

Today every `ai <stage>` command routes through `AgentRunner.invoke_agent()`,
which is a **stub** — it returns a structured dict matching the STEP 1.5
contract but doesn't call an LLM. When STEP 4 (Analyst Agent) lands, the stub
gets replaced with a real LLM-backed implementation per stage.

---

## The Context Engine (STEP 2) — how to use it

```
SDLC INTELLIGENCE
├── STEP 4     Analyst Agent
├── STEP 5     Architect Agent
├── STEP 6     Planner Agent

PROJECT CREATION
├── STEP 7     Project Bootstrapper

DEVELOPMENT
├── STEP 8     Developer Agent
├── STEP 9     Test Agent
├── STEP 10    Security Agent
├── STEP 11    Code Review Agent

DELIVERY
├── STEP 12    CI/CD Agent
├── STEP 13    Release & Deployment Agent

OPERATIONS
├── STEP 14    SRE / Observability Agent

AUTOMATION
├── STEP 15    SDLC Orchestrator
├── STEP 16    Human Approval & Governance

END GAME
└── STEP 17    AI Software Factory
```

---

## The Context Engine (STEP 2) — how to use it

### Run it

From the `ai_driven_sdlc` directory:

```bash
.venv/bin/python -m SoftwareFactory.Context.CLI context scan /path/to/repo
```

This writes 8 files into `<repo>/.ai/context/`:

| File | What it contains |
|---|---|
| `project.json` | Project name, root path, scan timestamp |
| `language.json` | Languages detected, file counts, LOC, dominant language |
| `architecture.json` | Detected architectural styles, components, layers, confidence |
| `dependencies.json` | Per-ecosystem dependency list (node, python, go, rust, jvm, php, ruby, dotnet, elixir) |
| `database.json` | Database technologies, migration files, schema hints |
| `api.json` | API styles, routing files, extracted endpoints |
| `tests.json` | Test frameworks, test file count, test directories, coverage signals |
| `git.json` | Is git repo, branch, commit count, authors, remote presence |

### Example output (POS_SaaS)

```bash
$ .venv/bin/python -m SoftwareFactory.Context.CLI context scan ~/Documents/Projects/digital-frontier/POS_SaaS

Context Engine — scan complete
==================================================
Project : POS_SaaS
Root    : /Users/.../POS_SaaS
Scanned : 2026-09-07T18:02:19.637963+00:00

Languages
  - TypeScript      files=38     loc=2115
  - Other           files=6      loc=5408
  - JSON            files=5      loc=3875
  ...

Dominant language : TypeScript
Source files      : 49
Lines of code     : 7017

Architecture
  Styles : React + Vite
  Confidence : 0.40
  Components : 2

Dependencies
  node: 18 package(s)
  Total dependencies: 18
  Lockfile present   : True

Database
  Technologies : (none detected)
  Migrations   : 0
  Schema hints : 0

API
  Styles : Custom / unclassified
  Routing files : 1
  Endpoints     : 0

Tests
  Frameworks : (none detected)
  Test files  : 0
  Test dirs   : -
  Coverage    : no

Git
  Repository   : no
  Branch       : -
  Commits      : 0
  Authors      : 0
  Has remote   : False

==================================================
Wrote context to: /Users/.../POS_SaaS/.ai/context
```

### Design principles

- **Deterministic first.** Detectors use filesystem walks, extension maps,
  manifest parsing, and regex patterns — not LLM calls.
- **One detector, one concern.** Each detector is a small module implementing
  the `Detector` interface (`block_name` + `detect() -> dict`).
- **Failure isolation.** A single detector failure does not kill the scan —
  the engine records the error and continues.
- **No mutation.** The engine reads the target repo only. It never modifies
  files.
- **Skip junk.** node_modules, .git, dist, build, venv, .next, .vite, and
  similar directories are excluded from all scans.

---

## Project structure

```text
ai_driven_sdlc/
├── .ai/
│   ├── README.md              ← what each .ai/ subdirectory is for
│   ├── rules/                 ← STEP 1: agent behavior rules (7 files)
│   ├── schemas/               ← STEP 1.5: agent output contracts (8 JSON schemas)
│   ├── context/               ← STEP 2: produced by the Context Engine
│   ├── tasks/                 ← future: task definitions
│   ├── decisions/             ← future: Architecture Decision Records
│   └── reports/               ← future: analysis/test/security/review reports
│
├── src/SoftwareFactory/
│   └── Context/               ← STEP 2: the Context Engine package
│       ├── Core/              Models + engine + writer
│       ├── Detectors/         8 detector modules
│       └── CLI/               `ai` CLI entry point
│
├── tests/
│   └── SoftwareFactory.Tests/
│       └── test_context_engine.py   ← STEP 2 test suite
│
├── pyproject.toml             ← package metadata + pydantic dependency
├── ROADMAP.md                 ← the 17-step plan
├── note.md                    ← step-by-step progression notes
└── .venv/                     ← isolated Python environment
```

---

## Setup

### Prerequisite

Python 3.11+ and `pip`.

### First time

```bash
cd ai_driven_sdlc
python3 -m venv .venv
.venv/bin/pip install -e .
```

This installs `pydantic` (the only runtime dependency) and the package in
editable mode so the CLI and tests work from the repo root.

### Run the tests

```bash
.venv/bin/pytest tests/SoftwareFactory.Tests/ -v
```

Expected: 41 passed.

### Run a scan

```bash
.venv/bin/python -m SoftwareFactory.Context.CLI context scan /path/to/some/repo
```

Replace `/path/to/some/repo` with any project directory. The engine writes
`.ai/context/*.json` inside it.

---

## Key design decisions

### Why separate `.ai/` from `src/`?

`.ai/` is the **data layer** — rules, schemas, context, tasks, decisions,
reports. It is language-agnostic and meant to be consumed by agents running
in any stack.

`src/` is the **implementation layer** — the Python package that implements
the Context Engine. It can be swapped out later for a different language if
needed.

### Why JSON schemas for agent contracts?

Free-form LLM output is unpredictable. A schema turns each agent's output
into a validated, machine-readable contract. The pipeline becomes:

```text
Agent → JSON Contract → Validator → Gate → Next Agent
```

### Why deterministic detectors before LLM?

The Context Engine's job is to gather facts. Files exist or they don't.
Package manifests have specific keys. ASTs have structure. These are
deterministic signals. LLM calls are expensive and nondeterministic — they
belong in the analysis/interpretation layers, not in the fact-gathering
layer.

---

## Context Engine — known gaps

These are carried forward from the STEP 2 implementation. None block the
pipeline today, but each is a real limitation.

- **lockfile_present** semantics are too loose — it currently returns True if
  any ecosystem manifest exists, rather than only when a real lockfile is present.
- **API endpoint extraction** is narrow. Misses Hono, Elysia, tRPC routers,
  gRPC service definitions, GraphQL resolver maps.
- **Database detector** does not parse ORM models — SQLAlchemy models, Prisma
  schema, EF Core DbContext, Hibernate entities, Django models.
- **Test detector** does not parse config files — jest.config, pytest.ini,
  vitest include globs.
- **No scan caching.** Every scan re-walks the entire tree.
- **Context schemas are not cross-linked** to the `.ai/schemas/` agent
  contracts. The context files are validated by pydantic, but there is no
  explicit link between `architecture.json` and the schema an Architect agent
  would consume.

---

## What's next

The natural next step is to wire the Context Engine into the agent pipeline.

Today: Context Engine produces `.ai/context/*.json` as a standalone tool.

Next: an agent input assembler that merges `context/` + `requirement` +
`rules/` into a single prompt package for the Analyst Agent (STEP 4). The
Analyst should not re-derive the tech stack from scratch when the Context
Engine already knows it.

After that: Architect Agent (STEP 5) reads analysis + context + architecture
rules, produces `design.json`. Planner Agent (STEP 6) reads design, produces
`task.json`. Then the development loop begins.

---

## Rules for working on this project

Read `.ai/rules/00-core.md` before making changes. The short version:

- Understand before changing.
- Make the smallest change that satisfies the task.
- Follow existing patterns.
- No assumptions without evidence.
- Every significant change is traceable: requirement → design → task →
  implementation → test → review.
- Preserve existing behavior unless the task requires a change.
- Base decisions on evidence, not opinion.
- Request human approval before destructive or high-impact changes.

AI agents working on this project MUST follow the rules in `.ai/rules/`.
