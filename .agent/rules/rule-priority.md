# Rule Priority

Wait for approval from the `bmad-architect` (Winston) before making significant changes to this rule.

## Universal Priority

1. **Security Mandate**: Never compromise security for speed or convenience.
2. **Implementation Plan**: Follow the approved implementation plan.
3. **Docker-First**: All commands must run via `./dev.sh`.
4. **Agent Personas**: Respect the BMAD agent roles and their expertise.

## Conflict Resolution

- If a framework-specific rule conflicts with a universal rule, the universal rule wins.
- If two framework rules conflict, prioritize the one that enhances security or reliability.
- When in doubt, call the `bmad-architect` for a decision.
