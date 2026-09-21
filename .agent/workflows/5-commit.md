---
description: Ship phase - Commit changes using Conventional Commits
---

# Phase 5: Ship (Commit)

## Purpose

Finalize the feature by committing verified code using the **Akvo Commit Standard** and ensuring alignment with documentation.

## Prerequisites

- **Phase 4 (Verify)** completed with all tests and linters passing.
- **Sprint Collaboration**: Invoke **Bob (Scrum Master)** to verify all tasks are marked as complete (`[x]`) in `task.md`.
- **Writer Collaboration**: Invoke **Paige (Documentation Writer)** to ensure implementation is synced with the corresponding PRD/docs under `agent_docs/` or `docs/`.

## Steps

### 1. Mandatory Git Confirmation

Before committing, you MUST verify:

1. **Doc Alignment**: Verify `agent_docs/` and `docs/` are updated to match current code.
2. **Task Status**: Update `task.md` with actual times and mark all tasks complete.
3. **User Confirmation**: Present the alignment and sprint status to the user.
4. **Atomic Commit Strategy**: Propose a plan to split changes into multiple atomic commits if necessary.
5. **Commit Preparation**: Prepare commit messages following Akvo standard: `[#issue_number] <type>(<scope>): <description>`.
6. **Final Approval**: Ask: "Should I proceed with the proposed commit(s) and push?"

### 2. Execution

Only after receiving explicit approval, execute the commands (NEVER run blanket `git add .`):

```bash
git add <explicit_file_1> <explicit_file_2>
git commit -m "[#issue_number] <type>(<scope>): <description>"
git push origin {branch_name}
```

## Completion Criteria

- [ ] User provided explicit confirmation for alignment and commit plan.
- [ ] `task.md` is 100% updated — all tasks marked `[x]`.
- [ ] Explicit files staged (no blanket staging).
- [ ] Commits follow `[#issue_number] <type>(<scope>): <description>` format.

## Next Phase

Task complete! Ready for PR? Use the `/6-pr` workflow to create a Pull Request.
