---
name: debugging-protocol
description: Systematic global protocol for debugging issues across any stack. Use when tests fail, builds crash, or unexpected behavior occurs.
---

# Global Debugging Protocol

Follow these steps rigorously when encountering any bug or issue. Do NOT guess the fix.

## 1. Isolate the Issue
- Check service status (e.g., `docker ps`, `pm2 status`, or stack-specific commands).
- Inspect logs for the failing component.
- Identify the exact error message and stack trace.

## 2. Formulate a Hypothesis
- Based on the logs, state what you think is failing and why.
- Check if this is a known issue (e.g., database connection failure, missing environment variables).

## 3. Surgical Search
- Use precise tools like `grep_search` and `view_file` to locate the exact lines of code involved.
- NEVER try to read entire large files or guess the implementation. Look for the function mentioned in the stack trace.

## 4. TDD Bug Fixing (Red → Green)
- **Red**: Write a failing test that reproduces the bug. If a test already exists and fails, you are in the Red state.
- **Green**: Implement the fix.
- Run the test suite to verify the fix works and no regressions were introduced.

## 5. Mandatory User Validation
- Present your hypothesis and proposed fix to the user.
- You MUST receive explicit user validation before executing the fix.

## 6. Document the Fix
- Briefly explain why the bug occurred and how it was fixed in the PR/commit message.
