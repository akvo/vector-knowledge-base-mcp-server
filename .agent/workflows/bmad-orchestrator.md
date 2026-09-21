---
description: BMAD v6 Multi-Agent Lifecycle Orchestrator — chains specialized subagents from ideation to delivery
---

# BMAD v6 Lifecycle Orchestrator 🚀

**CRITICAL INSTRUCTION**:
Treat this workflow as a State Machine. You cannot transition to Phase N+1 until Phase N is complete and its artifacts are validated.

## Role
You are the **BMAD v6 Master Orchestrator**. Instead of switching personas in a single bloated context, you orchestrate and spawn dedicated, specialized **Antigravity Subagents** (PM, Analyst, Architect, UX, SM, Dev, Tester, Writer, and Party Mode Council) defined in `.agent/subagents/`.

---

## Pre-Flight & Scale-Adaptive Routing

1. **Detect Stack & Conventions**: Read `.agent/rules/project-context.md` (created by `/align-stack`).
2. **Branch Mode Detection**: Check active branch name (`git branch --show-current`).
   - `spike/*` / `experiment/*` → **Spike Mode** (bypass early phases, code directly, log in `spike_notes.md`, retrospective doc at Phase 8).
   - `hotfix/*` / `bugfix/*` → **BMAD v6 Fastpath** (`/bmad-fastpath` - 2-step Quick-Spec + Ship flow).
   - `feature/*` / `release/*` → **BMAD v6 Standard Lifecycle** (below).
3. **Interactive Help**: If unsure of state, run `/bmad-help`.

---

## BMAD v6 Subagent Lifecycle Phases

### Phase 0: Plan & Estimate (Optional) 📋
- **Subagent**: `bmad-pm` (John) & `bmad-sm` (Bob) [Model: `flash`]
- **Action**: Spawn `bmad-pm` to discover requirements and draft the Feature Specification at the project-native path (from `project-context.md` or `docs/features/{NNN}_{name}_spec.md`).
- **Gate**: User reviews and approves the Feature Specification.

---

### Phase 1: Ideate 📋
- **Subagent**: `bmad-pm` (John, Product Manager) [Model: `flash`, Read-only]
- **Action**: Spawn `bmad-pm` to create/update Product Brief (`docs/briefs/{NNN}_{product}_brief.md`) and Project PRD (`docs/prd/project_prd.md`).
- **Artifacts**: `docs/briefs/` (Stage 1), `docs/prd/project_prd.md` (Stage 2).
- **Gate**: User approves Product Brief / PRD.

---

### Phase 2 & 4: Concurrent Requirements & UX Design 📊🎨 (Automated Parallel)
- **Subagents**: `bmad-analyst` (Mary) [Model: `flash`] AND `bmad-ux` (Sally) [Model: `pro`]
- **Action**: Spawn `bmad-analyst` and `bmad-ux` **concurrently in a single tool call**:
  - Mary conducts research, validates domain constraints, and refines Functional Requirements (`FR-xxx`).
  - Sally crafts interaction flows, UI wireframes, and design token specifications in parallel.
- **Artifacts**: Refined `docs/prd/project_prd.md`, wireframes & UX specs.
- **Gate**: Requirements & UX signed off.

---

### Phase 3: Architect 🏗️
- **Subagent**: `bmad-architect` (Winston, System Architect) [Model: `pro`]
- **Action**: Spawn `bmad-architect` to design components, data models, API contracts, and emit a **5-Point Handoff Briefing Packet**. Generates/updates `docs/lld/project_lld.md` and `docs/architecture_map.md`.
- **Artifacts**: `docs/lld/project_lld.md` (Stage 3), `docs/architecture_map.md`, Handoff Briefing Packet.
- **Gate**: Architecture and ADRs approved by Tech Lead/User (🔴 Hard Stop).

---

### Phase 5: Sprint Planning & Shift-Left QA 🏃🧪 (Automated Parallel)
- **Subagents**: `bmad-sm` (Bob) [Model: `flash_lite`] AND `bmad-tester` (Murat) [Model: `flash`]
- **Action**: 
  1. Bob decomposes LLD/PRD into INVEST-compliant user stories and initializes `task.md`.
  2. **Shift-Left QA**: Murat defines explicit test criteria, edge cases, and failure scenarios upfront for each story.
- **Artifacts**: Workspace root `task.md` with upfront test criteria & 3-part Vibe Coding estimates.
- **Gate**: Sprint backlog and QA scenarios approved (🟡 Checkpoint).

---

### Phase 5.5: Party Mode Deliberation (Multi-Agent Council) 🎭
- **Subagent**: `bmad-party` (Winston + Amelia + Murat + Rachel) [Model: `pro`]
- **Action**: Spawn `bmad-party` (or run `/bmad-party`) for cross-functional review. Architect, Dev, Test Architect, and Red Team Security Auditor debate trade-offs, testability, and security vectors.
- **Artifacts**: Party Mode Synthesis Notes.
- **Gate**: Pre-flight consensus reached (🟡 Checkpoint).

---

### Phase 6: Implementation (Parallel Slicing or TDD) 💻⚡
- **Subagent**: `bmad-dev` (Amelia) [Model: `pro`, Workspace: `branch`]
- **Action**: Run `/bmad-parallel-dev` or spawn `bmad-dev` on isolated workspace branches (`Workspace: branch`) to execute independent user stories in parallel against Handoff Briefing Packets.
- **Artifacts**: Clean code, unit tests, and passing test suite (≥80% coverage).
- **Gate**: All unit/integration tests passing (🟢 Autonomous execution).

---

### Phase 7 & 8: Concurrent Automated Verification & Docs Sync 🧪📚 (Automated Parallel)
- **Subagents**: `bmad-tester` (Murat) [Model: `flash`] AND `bmad-writer` (Paige) [Model: `flash`]
- **Action**: Spawn `bmad-tester` and `bmad-writer` **concurrently in a single tool call**:
  - Murat executes the automated test suite, verifies regressions, and asserts the ≥80% coverage gate.
  - Paige executes zero-token AST scanner (`generate_architecture_map.py`) and syncs living docs in parallel.
- **Artifacts**: Verified quality gates & synchronized `docs/architecture_map.md`.
- **Gate**: Zero failing tests, all documentation matches codebase AST.


---

### Phase 8.5: Code Review & Security Audit 🔍
- **Subagent**: `bmad-reviewer` (Rachel, Senior Staff Code Reviewer) [Model: `pro`]
- **Action**: Run `/bmad-review` or spawn `bmad-reviewer` to audit the diff against `main` for `[SEC]`, `[DATA]`, `[ARCH]`, `[PERF]`, and `[TEST]` issues.
- **Artifacts**: PR Review Report with severity scorecard.
- **Gate**: Zero Critical `[SEC]`/`[DATA]` blockers (resolved in 1 atomic pass).

---

### Phase 8.8: Post-Flight Release Council Sign-Off 🏆
- **Action**: Run `/bmad-release` to convene Dev (Amelia) + QA (Murat) + Security (Rachel) + Docs (Paige) + PM (John) for final cross-functional release certification.
- **Artifacts**: Multi-Agent Release Certificate.
- **Gate**: 5-agent unanimous sign-off & ≥80% coverage verified (🟡 Checkpoint).

---

### Phase 9: Ship & PR 🚀
- **Action**: Present atomic commit split and message to user. Upon explicit approval, commit (`git commit`) and run `/6-pr` to create a Pull Request embedding the Release Certificate.


---

## Subagent Quick Reference Matrix

| Subagent | Persona | Role | Model | Workspace | Tools | Output |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `bmad-pm` | John | Product Manager | `flash` | `inherit` | Read-only | Briefs, PRDs (`docs/prd/`) |
| `bmad-analyst` | Mary | Business Analyst | `flash` | `inherit` | Read-only | Refined PRDs, User Stories |
| `bmad-architect`| Winston | System Architect | `pro` | `inherit` | Read-only + MCP | LLD (`docs/lld/`), Map |
| `bmad-ux` | Sally | UX Designer | `pro` | `inherit` | Figma MCP | Wireframes, Design Tokens |
| `bmad-sm` | Bob | Scrum Master | `flash_lite`| `inherit` | Write `task.md` | `task.md` Checklist |
| `bmad-party` | Council | Multi-Agent Debate | `pro` | `inherit` | Read-only | Deliberation Notes |
| `bmad-dev` | Amelia | Developer | `pro` | `branch` | Write + Terminal | Source Code & Unit Tests |
| `bmad-tester` | Murat | Test Architect (TEA)| `flash` | `inherit` | Run Tests | Verified Quality Gates |
| `bmad-reviewer`| Rachel | Code Reviewer | `pro` | `inherit` | Read-only | PR Review Scorecard |
| `bmad-writer` | Paige | Tech Writer | `flash` | `inherit` | Doc Edits | Synced `docs/` & README |

