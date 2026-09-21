---
description: Verify phase - run full validation suite
---

# Phase 4: Verify (Vector KB MCP Stack)

## Purpose

Run all test suites and coverage reports to ensure the implementation meets technical, quality, and security standards.

## Prerequisites

- **Phase 3 (Integrate)** completed with all integration tests passing.
- All unit and functional tests passing.

## If This Phase Fails

1. **Do not proceed** to Phase 5 (Ship).
2. Address the failure in the relevant component (`main/app/`).
3. Re-run the verification suite until 100% success is achieved.

## Steps

**Set Mode:** Use `task_boundary` to set mode to **VERIFICATION**.

### 1. Code Quality & Syntax Validation

- Verify Python type hinting and Pydantic schemas.
- Ensure no hardcoded secrets or unhandled exceptions.

### 2. Full Test Suite & Coverage

Run the complete test suite across all modes:

- **API Suite**: `./dev.sh exec main ./test.sh api` (generates `coverage.xml`)
- **MCP Suite**: `./dev.sh exec main ./test.sh mcp`
- **E2E Suite**: `./dev.sh exec main ./test.sh e2e`
- **Full Suite**: `./dev.sh exec main ./test.sh all`

### 3. Build & Container Check

Ensure Docker containers build and start cleanly:

```bash
./dev.sh build
./dev.sh up -d
./dev.sh ps
```

### 4. Coverage Audit

Verify that domain logic and API routes meet the project's coverage mandates (target: ≥80%).

## Development Commands

```bash
# Run All Tests with Coverage Report
./dev.sh exec main ./test.sh all

# Run API Tests only
./dev.sh exec main ./test.sh api

# Run MCP Tests only
./dev.sh exec main ./test.sh mcp

# Run E2E Tests only
./dev.sh exec main ./test.sh e2e
```

## Completion Criteria

- [ ] All tests pass in API, MCP, and E2E modes (100% pass rate).
- [ ] Test coverage meets or exceeds ≥80% requirement.
- [ ] Service builds succeed without warnings or errors.
- [ ] Two-tier authentication verified on endpoints.

## Next Phase

Proceed to **Phase 5: Ship** (`/5-commit`).
