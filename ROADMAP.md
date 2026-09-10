# AI-Driven SDLC Roadmap

## Vision

Build an **AI Software Factory** that can automate the software development lifecycle from requirement analysis through development, testing, security, deployment, and operations.

The core principle:

> AI provides intelligence. Deterministic engineering tools provide execution and verification.

The system should remain **human-in-the-loop** for high-impact decisions such as destructive database changes, major architecture changes, breaking API changes, security exceptions, and production deployment.

---

# Roadmap Overview

```text
AI-DRIVEN SDLC ROADMAP
======================

FOUNDATION
├── STEP 1     Foundation                         ✅
├── STEP 1.5   Agent Contracts / Schemas          ✅
│
│
UNDERSTANDING
├── STEP 2     Context Engine                ✅
├── STEP 3     AI CLI                        ✅
│
│
SDLC INTELLIGENCE
├── STEP 4     Analyst Agent
├── STEP 5     Architect Agent
├── STEP 6     Planner Agent
│
│
PROJECT CREATION
├── STEP 7     Project Bootstrapper
│
│
DEVELOPMENT
├── STEP 8     Developer Agent
├── STEP 9     Test Agent
├── STEP 10    Security Agent
├── STEP 11    Code Review Agent
│
│
DELIVERY
├── STEP 12    CI/CD Agent
├── STEP 13    Release & Deployment Agent
│
│
OPERATIONS
├── STEP 14    SRE / Observability Agent
│
│
AUTOMATION
├── STEP 15    SDLC Orchestrator
├── STEP 16    Human Approval & Governance
│
│
END GAME
└── STEP 17    AI Software Factory
```

## 🎯 Milestone yang paling penting

Gue bakal membagi roadmap ini menjadi 4 fase besar:

Phase 1 — AI understands software

```text
STEP 1 → 3
Foundation → Contracts → Context → CLI
```

Phase 2 - AI engineers software

```text
STEP 4 → 8
Analyst → Architect → Planner → Bootstrapper → Developer
```

Phase 3 - AI validates & ships software

```text
STEP 9 → 14
Test → Security → Review → CI/CD → Deploy → SRE
```

Phase 4 — AI operates the entire SDLC

```text
STEP 15 → 17
Orchestrator → Governance → AI Software Factory
```

## STEP 1 — Foundation ✅

Goal: membuat aturan dasar AI Software Factory.

Yang sudah kita buat:

```text
.ai/
├── README.md
├── rules/
│   ├── 00-core.md
│   ├── 01-architecture.md
│   ├── 02-coding.md
│   ├── 03-testing.md
│   ├── 04-security.md
│   ├── 05-database.md
│   └── 06-git.md
├── context/
├── tasks/
├── decisions/
└── reports/
```

Output:
```text
Engineering Rules
Architecture Rules
Coding Rules
Testing Rules
Security Rules
Database Rules
Git Rules
```

## STEP 1.5 — Agent Contracts / Schemas ✅

Goal: memastikan setiap agent punya output yang predictable.

Kita sudah punya:

```text
.ai/schemas/

common.schema.json
analysis.schema.json
design.schema.json
task.schema.json
implementation.schema.json
test.schema.json
security.schema.json
review.schema.json
```

Pipeline:

```text
Agent
  ↓
JSON Contract
  ↓
Validator
  ↓
Gate
  ↓
Next Agent
```

Ini penting supaya kita nggak bergantung kepada free-form LLM output.

## STEP 2 — Context Engine ✅

Goal: AI harus memahami project sebelum melakukan perubahan.

Status: **IMPLEMENTED — Python package `SoftwareFactory.Context` with 8 detectors, CLI, and 41 passing tests.**

What was delivered:

```text
src/SoftwareFactory/Context/
├── Core/             ← models (8 Context types), ContextEngine, ContextWriter, scan_root()
├── Detectors/        ← filesystem, language, architecture, dependencies, api,
│                       database, test, git
└── CLI/              ← `ai context scan <path>` — writes .ai/context/*.json

tests/SoftwareFactory.Tests/
└── test_context_engine.py   ← 41 tests (models, detectors, integration, CLI)
```

Output (verified on POS_SaaS):

```text
.ai/context/
├── project.json
├── language.json
├── architecture.json
├── dependencies.json
├── database.json
├── api.json
├── tests.json
└── git.json
```

Roadmap sub-steps (2.1–2.12) — all implemented, with notes on what remains:

```text
2.1  Context Engine Core      ✅  ContextEngine + ContextWriter + scan_root()
2.2  Filesystem Scanner       ✅  FilesystemDetector → project.json
2.3  Language & Framework     ✅  LanguageDetector → language.json (extension map,
                                       LOC counting, dominant language)
2.4  Architecture Detector    ✅  ArchitectureDetector → architecture.json
                                       (pattern matching + framework signals)
2.5  Dependency Analyzer      ✅  DependencyDetector → dependencies.json
                                       (node, python, go, rust, jvm, php, ruby, dotnet, elixir)
2.6  API Analyzer             ✅  ApiDetector → api.json (styles + routing files +
                                       endpoint extraction; node_modules excluded)
2.7  Database Analyzer        ✅  DatabaseDetector → database.json
                                       (technologies, migrations, schema hints)
2.8  Test Analyzer            ✅  TestDetector → tests.json
                                       (frameworks, test dirs, coverage signals)
2.9  Git Analyzer             ✅  GitDetector → git.json (branch, commits, authors)
2.10 Context Aggregator       ✅  FullContext aggregates every detector block
2.11 Context JSON             ✅  8 files written as validated JSON
2.12 Context Validation       ⚠️  pydantic validation yes; cross-link to .ai/schemas/
                                       not yet done (see open gaps in commit log)
```

Known gaps (carried forward to next session):

- lockfile_present semantics too loose
- API endpoint extraction narrow (Hono, Elysia, tRPC routers, gRPC services, GraphQL resolvers not yet covered)
- Database detector: no ORM model parsing (SQLAlchemy, Prisma, EF Core, Hibernate, Django models)
- Test detector: no config-file parsing (jest config, pytest.ini, vitest include globs)
- No scan caching (re-walks tree every run)
- Context schemas not cross-linked to .ai/schemas/ agent contracts

```text
STEP 3 — AI CLI

Goal: kita punya interface utama untuk berinteraksi dengan AI Software Factory.

CLI is partially built — `ai context scan` works. The full envisioned CLI
(`ai analyze`, `ai design`, `ai plan`, `ai implement`, `ai test`,
`ai security`, `ai review`, `ai deploy`, `ai run <feature>`) is still ahead.

Context Engine akan membaca:

```text
Repository
    ↓
File System
    ↓
Language Detection
    ↓
Framework Detection
    ↓
Architecture Detection
    ↓
Dependencies
    ↓
Database
    ↓
API
    ↓
Tests
    ↓
Git History
```

Output misalnya:

```text
.ai/context/

project.json
architecture.json
dependencies.json
database.json
api.json
tests.json
git.json
```

Contoh:

```text
.NET 9
ASP.NET Core
Clean Architecture
PostgreSQL
Entity Framework
React
REST API
xUnit
Docker
GitLab CI
```

Catatan: awalnya jangan pakai Vector DB.

Mulai dari:

```text
filesystem
+
grep/search
+
parser
+
AST
+
git
```

Vector/RAG bisa datang belakangan.

## STEP 3 — AI CLI ✅

**Status: IMPLEMENTED.** Complete CLI control plane with workflow management, context scanning, and 8 single-stage commands — one per SDLC stage.

### Yang sudah ada

```text
src/SoftwareFactory/SDLC/
├── workflow.py              Workflow model, WorkflowStore, STAGES, STAGE_LABELS
└── Agents/
    ├── __init__.py          exports AgentRunner, AgentKind, invoke_agent
    └── runner.py            AgentRunner, AgentKind enum (8 agents), invoke_agent() stub

src/SoftwareFactory/Context/CLI/
├── __init__.py              delegates to run.main()
├── __main__.py              python -m entry point
└── run.py                   full CLI parser + dispatch
```

### Perintah yang tersedia

```text
ai context scan <path>       Scan repo → .ai/context/*.json + summary
ai status                     Show active workflow state
ai init <feature> <req>      Start new workflow
ai run <feature> <req>       Run full pipeline (all 8 stages)
ai run <feature> <req> --stages s1 s2 s3   Run selected stages only
ai analyze                    Run analysis stage (Analyst Agent)
ai design                     Run architecture stage (Architect Agent)
ai plan                       Run planning stage (Planner Agent)
ai implement                  Run development stage (Developer Agent)
ai test                       Run testing stage (Test Agent)
ai security                   Run security stage (Security Agent)
ai review                     Run code review stage (Reviewer Agent)
ai deploy                     Run deployment stage (Deployer Agent)
```

### 8 Workflow stages

```text
analyze    → Analyst Agent    requirement → analysis.json
design     → Architect Agent  analysis + context → design.json
plan       → Planner Agent    design → task.json
implement  → Developer Agent  task → code + implementation.json
test       → Test Agent       implementation → test results + test.json
security   → Security Agent   code + findings → security.json
review     → Review Agent     diff + context → review.json
deploy     → Deployer Agent   ready → deployed
```

### Contoh penggunaan

```bash
# Mulai workflow baru
ai init "membership freeze" "Fitur freeze untuk member tidak aktif"

# Lihat status
ai status

# Output:
# Workflow: WF-2026-001
# Feature  : membership freeze
# Status   : in_progress
#
# ✓ Analysis       requirement received, no ambiguity
# ✓ Architecture   clean architecture proposed
# ✓ Planning       7 tasks generated
# → Development    pending
# ○ Testing        pending
# ○ Security       pending
# ○ Review         pending
# ○ Deployment     pending

# Jalankan stage tunggal
ai analyze

# Jalankan beberapa stage sekaligus
ai run "membership freeze" --stages analysis architecture planning

# Resume dari stage yang diblokir
ai run "membership freeze"
```

### Workflow state

Disimpan di `.ai/workflow/<workflow_id>.json`. Struktur:

```text
Workflow
  ├── workflow_id      (misal: WF-2026-001)
  ├── project_root
  ├── feature
  ├── requirement
  ├── status           (pending / in_progress / blocked / completed)
  ├── current_stage
  └── stages[]         (8 buah, tiap status: pending / in_progress /
                        completed / blocked)
```

### Agent Runner

```text
AgentRunner
  └── invoke_agent(kind, stage, workflow) → dict
        ├── status: "completed" | "blocked"
        ├── summary: str
        ├── output_path: str
        └── findings: list
```

invoke_agent saat ini adalah stub — stage dilewatkan dan menghasilkan output terstruktur sesuai contract STEP 1.5. Agent nyata (LLM-backed) akan mengganti stub ini mulai STEP 4.

### Hubungan dengan Context Engine

```text
Context Engine → .ai/context/*.json (8 file: project, language,
                                       architecture, dependencies,
                                       database, api, tests, git)
       ↓
CLI baca context saat stage dijalankan
       ↓
Agent dapat context + workflow state + requirement
```

### Pengujian

- 41 pytest tests (STEP 2: models, detectors, integration, CLI)
- CLI integration: status (no wf), init, status (in_progress), single-stage (analyze, design), status (completed stages), context scan self, full run with --stages — semua pass

### Pekerjaan tersisa (dipindah ke STEP 4+)

- invoke_agent stub → ganti dengan agent nyata (STEP 4 Analyst Agent)
- Agent output path convention
- Approval UI (CLI-only sekarang)


## STEP 4 — Analyst Agent

Goal: requirement → structured analysis.

Input:

```text
User Requirement
```

```text
analysis.json
```

Contoh:

```text
Requirement
    ↓
Analyst
    ↓
Business Requirements
Business Rules
Actors
Constraints
Assumptions
Acceptance Criteria
Dependencies
    ↓
analysis.json
```

Agent harus bisa menemukan ambiguity.

Contoh:

> “Buat fitur freeze membership.”

Agent jangan langsung coding.

Dia harus bertanya:

```text
❓ Apakah freeze mengurangi masa membership?
❓ Berapa maksimal hari?
❓ Apakah ada biaya?
❓ Siapa yang boleh melakukan freeze?
```

## STEP 5 — Architect Agent

Goal: analysis → technical design.

Input:

```text
analysis.json
+
context
+
architecture rules
```

Output:

```text
design.json
```

Architect menentukan:

```text
Architecture
Components
Database Changes
API Changes
Integration
Dependencies
Technical Decisions
Trade-offs
```

Contoh:

```text
REQ-001
   ↓
Architect
   ↓
MembershipService
FreezeMembershipCommand
MembershipFreeze table
POST /memberships/{id}/freeze
```

Kalau ada architecture change besar:

```text
ADR-001
```

dibuat otomatis.

## STEP 6 — Planner Agent

Goal: technical design → executable tasks.

Input:

```text
design.json
```

Output:

```text
task.json
```

Misalnya:

```text
TASK-001
Create migration

TASK-002
Create MembershipFreeze entity

TASK-003
Create repository

TASK-004
Create FreezeMembership service

TASK-005
Create API endpoint

TASK-006
Create unit tests

TASK-007
Create integration tests
```

Dengan dependency:

```text
TASK-001
   ↓
TASK-002
   ↓
TASK-003
   ↓
TASK-004
   ↓
TASK-005
   ↓
TASK-006
TASK-007
```

Planner juga menentukan affected files.

## STEP 7 — Project Bootstrapper

Goal: ini bagian yang mulai membuat project dari nol.

Ini penting banget untuk target lo.

Command:

```text
ai create
```

Contoh:

```text
ai create gym-management
```

AI akan menentukan / menerima:

```text
Project Name
Language
Framework
Database
Architecture
Frontend
Testing
CI/CD
```

Misalnya:

```text
Backend
.NET 9

Architecture
Clean Architecture

Database
PostgreSQL

Frontend
React + Vite

Testing
xUnit

Infrastructure
Docker

CI/CD
GitLab
```

Kemudian:

```text
Project Bootstrapper
        ↓
Generate Repository
        ↓
Generate Solution
        ↓
Generate Projects
        ↓
Generate Docker
        ↓
Generate Database
        ↓
Generate Tests
        ↓
Generate CI/CD
        ↓
Initialize Git
```

Output:

```text
gym-management/
├── src/
├── tests/
├── docs/
├── docker/
├── .gitlab-ci.yml
├── .ai/
├── README.md
└── ...
```

Ini adalah milestone besar pertama:

> AI bisa membuat sebuah software project dari nol.

## STEP 8 — Developer Agent

Goal: task → code.

Input:

```text
task.json
+
context
+
design
+
rules
```

Flow:

```text
TASK-001
   ↓
Developer
   ↓
Inspect Code
   ↓
Plan Change
   ↓
Modify Files
   ↓
Compile
   ↓
Run Tests
   ↓
implementation.json
```

Developer tidak boleh asal generate code.

Dia harus:

```text
Understand
→ Locate
→ Plan
→ Change
→ Validate
```

Dan idealnya satu task satu execution.

## STEP 9 — Test Agent

Goal: memastikan implementation benar.

Test Agent membaca:

```text
Requirement
Design
Implementation
Existing Tests
```

Kemudian

```text
Generate Tests
      ↓
Run Tests
      ↓
Analyze Failures
      ↓
Fix / Return to Developer
```

Flow:

```text
Developer
   ↓
Test
   ↓
PASS ─────→ Security
   │
   ↓
FAIL
   ↓
Developer
```

Coverage juga dikumpulkan.

Output:

```text
test.json
```

## STEP 10 — Security Agent

Goal: security validation.

Jangan hanya LLM.

Gunakan deterministic tools:

```text
SAST
Dependency Scanner
Secret Scanner
Container Scanner
SQL Analysis
Configuration Scanner
```

Kemudian AI melakukan interpretation.

Flow:

```text
Code
 ↓
Security Tools
 ↓
Findings
 ↓
AI Security Agent
 ↓
security.json
```

Gate:

```text
Critical > 0
    ↓
BLOCK

High > 0
    ↓
BLOCK

Medium
    ↓
Human Review

Low
    ↓
PASS
```

## STEP 11 — Code Review Agent

Goal: AI melakukan review sebelum merge.

Review:

```text
Architecture
Correctness
Maintainability
Performance
Security
Testing
Code Quality
```

Input:

```text
Git Diff
+
Requirement
+
Design
+
Tests
+
Security Report
```

Output:

```text
review.json
```

Contoh:

```text
✓ Architecture
✓ Correctness
⚠ Maintainability
✓ Performance
✓ Security
```

## STEP 12 — CI/CD Agent

Goal: AI memahami dan mengelola pipeline.

Misalnya generate:

```text
.gitlab-ci.yml
```

Pipeline:

```text
Build
 ↓
Unit Test
 ↓
Integration Test
 ↓
SAST
 ↓
Dependency Scan
 ↓
Build Docker
 ↓
Security Scan
 ↓
Package
```

AI juga bisa menganalisis pipeline failure.

Misalnya:

```text
Pipeline Failed

Cause:
.NET SDK mismatch

Suggested Fix:
Update global.json
```

## STEP 13 — Release & Deployment Agent

Goal: deployment otomatis dengan approval gate.

Flow:

```text
Code
 ↓
CI
 ↓
Test
 ↓
Security
 ↓
Review
 ↓
Release
 ↓
Deployment
```

Environment:

```text
Development
    ↓
Staging
    ↓
Production
```

Production harus punya:

```text
HUMAN APPROVAL
```

AI boleh:

```text
prepare deployment
validate deployment
execute deployment
```

Tapi production deployment idealnya:

```text
AI
 ↓
READY
 ↓
Human Approval
 ↓
Deploy
```

## STEP 14 — SRE / Observability Agent

Setelah software sudah hidup, AI jangan berhenti.

Dia harus bisa membaca:

```text
Logs
Metrics
Traces
Errors
Infrastructure
Database
```

Contoh:

```text
API latency meningkat 300%
        ↓
SRE Agent
        ↓
Analyze
        ↓
Database query identified
        ↓
Suggest index
```

Atau:

```text
Error rate > threshold
        ↓
AI detects incident
        ↓
Root Cause Analysis
        ↓
Incident Report
```

## STEP 15 — SDLC Orchestrator

Ini otaknya workflow, bukan LLM-nya.

Sebelumnya kita punya:

```text
Agent → Contract → Validator → Gate → Next Agent
```

Sekarang menjadi:

```text
                ORCHESTRATOR
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
    Analyst      Architect     Planner
        ↓            ↓            ↓
   Developer      Tester      Security
        └────────────┼────────────┘
                     ↓
                   Review
                     ↓
                    CI
                     ↓
                  Release
                     ↓
                 Deployment
                     ↓
                    SRE
```

Orchestrator menyimpan:

```text
Workflow State
Agent State
Task State
Approval State
Retry State
Failure State
```

Contoh:

```text
{
  "workflow_id": "WF-2026-001",
  "current_stage": "testing",
  "status": "blocked"
}
```

Kemudian:

```text
ai resume WF-2026-001
```

## STEP 16 — Human Approval & Governance

Ini layer yang memastikan AI tidak menjadi autonomous uncontrolled system.

Approval gate untuk:

```text
Architecture changes
Destructive DB changes
Breaking API
Security exceptions
Production deployment
Infrastructure changes
Removing functionality
Major dependency changes
```

Flow:

```text
AI
 ↓
Proposal
 ↓
Evidence
 ↓
Risk
 ↓
Human
 ↓
Approve / Reject
```

Semua dicatat:

```text
.ai/decisions/
```

Jadi ada audit trail.

## STEP 17 — AI Software Factory 🏭

Nah, ini end goal kita.

User cukup memberikan:

```text
"Build a gym membership management system."
```

Kemudian:

```text
                    USER
                      ↓
                 REQUIREMENT
                      ↓
                  ANALYST
                      ↓
                 ARCHITECT
                      ↓
                  PLANNER
                      ↓
             PROJECT BOOTSTRAPPER
                      ↓
                 DEVELOPER
                      ↓
                   TESTER
                      ↓
                 SECURITY
                      ↓
                  REVIEWER
                      ↓
                    CI/CD
                      ↓
                   RELEASE
                      ↓
                 DEPLOYMENT
                      ↓
                     SRE
```

Dan hasil akhirnya:

```text
┌──────────────────────────────────┐
│       AI SOFTWARE FACTORY        │
├──────────────────────────────────┤
│                                  │
│ Requirement                      │
│      ↓                           │
│ Analysis                         │
│      ↓                           │
│ Architecture                     │
│      ↓                           │
│ Planning                         │
│      ↓                           │
│ Project Creation                 │
│      ↓                           │
│ Development                      │
│      ↓                           │
│ Testing                          │
│      ↓                           │
│ Security                         │
│      ↓                           │
│ Code Review                      │
│      ↓                           │
│ CI/CD                            │
│      ↓                           │
│ Deployment                       │
│      ↓                           │
│ Monitoring                       │
│      ↓                           │
│ Continuous Improvement           │
│                                  │
└──────────────────────────────────┘
```

## Conclusion

Kalau roadmap ini kita pegang, target akhirnya jelas: bukan bikin “AI yang bisa coding”, tapi bikin sebuah software factory yang menjadikan AI sebagai engineering workforce dan deterministic tools sebagai execution/verification layer.