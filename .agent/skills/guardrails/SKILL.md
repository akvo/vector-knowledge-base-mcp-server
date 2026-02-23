---
name: guardrails
description: Pre-flight and post-implementation checklist for code quality and security.
---

# Guardrails

Self-review protocol to be followed before notifying the user.

## Pre-flight (Before Implementation)

- [ ] Does this follow the approved `implementation_plan.md`?
- [ ] Are all external service integrations (Minio, Chroma) planned?
- [ ] Is the Pydantic schema defined for input validation?

## Post-implementation (Self-Review)

### Security
- [ ] No hardcoded API keys or secrets.
- [ ] All inputs are validated via Pydantic or LangChain tools.
- [ ] Minio access uses signed URLs or restricted policies.

### AI Integration
- [ ] LangGraph state is correctly managed and typed.
- [ ] LLM outputs are handled gracefully (error handling/parsing).
- [ ] Prompt templates are organized and not hardcoded strings.

### Code Quality
- [ ] Code is formatted and linted.
- [ ] `./dc.sh tests` passes.
- [ ] New functionality is documented in the code or a walkthrough.
