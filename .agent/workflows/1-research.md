---
description: Research phase — bridges approved Feature Spec to implementation by mapping exact code insertion points and building task.md.
---

# Phase 1: Research

> [!IMPORTANT]
> **No code changes in this phase.** Read and map only. Implementation begins at `/2-implement`.
>
> **Pre-Flight**: Read `.agent/rules/project-context.md` if it exists — use project-native doc paths instead of BMAD defaults.

---

## Steps

### 0. Spec Verification
Confirm the Feature Spec exists and is approved (path from `project-context.md` or BMAD default). Also check for PRD and LLD if they exist. Ask the user: *"Are these the correct spec documents for this task?"*. If spec is ambiguous, invoke **John (PM)** to clarify.

### 1. Analyze Request & Workspace Context
- **Scope**: Define what is being asked
- **Context**: Check `docs/` to align with current project phase
- For complex domain logic, invoke **Mary (Analyst)**

### 2. Repository Reconnaissance
- **Architecture**: Identify relevant modules; invoke **Winston (Architect)** for structural guidance
- **Patterns**: Locate similar implementations for consistency
- **Dependencies**: Review `package.json`, `requirements.txt`, `composer.json` for versions

### 3. Build Mental Model
- **Business Logic**: Derived from requirements and specs
- **Technical Constraints**: Stack limitations
- **Integration Points**: Exact touch points between new and old code

### 4. Define Scope & Build `task.md`
Translate the Feature Spec's tasks into atomic checklist items in `task.md` at workspace root. Map each task to specific files.

### 5. Technical Research
For each identified technology or pattern, run targeted queries for the project's exact versions. Check for "Migration Guides" or "Breaking Changes" on older dependencies.

### 6. Document Findings
Log key research findings and verified API signatures in the Feature Spec under a "Technical Audit" section, or inline in `task.md`.

### 7. Architectural Decisions
If structural changes are needed, invoke **Winston** to document them in `docs/lld/project_lld.md` or `docs/lld/components/`.

---

## Completion Criteria
- [ ] Feature Spec confirmed with user
- [ ] Workspace patterns and versions identified
- [ ] `task.md` created with file-specific atomic tasks
- [ ] Findings documented in Feature Spec or `task.md`
- [ ] Architectural decisions logged in LLD if needed

**Next**: `/2-implement` or invoke **Amelia (Developer)**.
