---
description: TDD implementation workflow
---

# Phase 2: Implement (Vector KB MCP Stack)

Write production code following strict **TDD** principles and project-specific design patterns.

## Prerequisites

- **Phase 1 (Research)** completed with a confirmed Specification.
- **Feature Spec** (path per @documentation-hierarchy.md or `project-context.md`) approved and available — sole implementation source.
- **Collaboration**: Invoke **Amelia (Developer)** for core logic and endpoints.

## Steps

**Set Mode:** Use `task_boundary` to set mode to **EXECUTION**.

### 1. Workspace Setup

Before coding, ensure the environment is ready:

- Review backend constraints, models, schemas, and services.
- Identify the correct test runner and command wrapper (`./dev.sh exec main ./test.sh [mode]`).

### 2. TDD Cycle: RED (Failing Test)

Create the test files first:

- Locate the project's test directory (`main/tests/unit/`, `main/tests/functional/`, `main/tests/integration/`).
- Write a test that fails because the feature does not exist yet.

### 3. TDD Cycle: GREEN (Minimal Code)

Write **only** the code necessary to make the tests pass:

- Follow the project's coding standards (FastAPI, FastMCP, SQLAlchemy 2.0, Pydantic v2).
- Verify that the tests now pass.

### 4. TDD Cycle: REFACTOR (Blue)

Improve the code while keeping the tests green:

- **Quality**: Ensure type hinting, logging, and proper documentation.
- **Story Alignment**: Verify work against the specific Acceptance Criteria (UAC/TAC).

### 5. Repeat

Continue the Red-Green-Refactor cycle for each story requirement until the task is complete.

## Development Commands

```bash
# Run API Tests
./dev.sh exec main ./test.sh api

# Run MCP Tests
./dev.sh exec main ./test.sh mcp

# Run All Tests
./dev.sh exec main ./test.sh all
```

## Completion Criteria

- [ ] Unit tests passing (TDD cycle strictly followed)
- [ ] **Standards**: DRY, KISS, YAGNI, SOC, SOLID, Security — see @coding-standards.md
- [ ] **Security**: User inputs sanitized and validated; two-tier API key auth enforced
- [ ] Implementation aligns with UAC/TAC in the Feature Spec
- [ ] Document Sync: Update `task.md` (mark tasks `[x]`, note actual time)

## Next Phase

Ready for integration? Use the `/3-integrate` workflow or invoke **Amelia (Developer)** and **Murat (Tester)**.
