# Agent Onboarding

Welcome, Agent! Follow these steps to correctly explore and implement changes in this repository.

## 1. Understand the Method
- **Read `bmad-team.md`**: This project follows the BMAD (Business-Model-Architecture-Development) Method.
- **Identify Your Role**: Determine which persona (John, Mary, Winston, etc.) you are currently embodying.
- **Respect the Lifecycle**: Follow the sequence: Ideate → Analyze → Architect → Design → Plan → Implement → Test → Document.

## 2. Environment & Tools
- **Use `./dev.sh`**: NEVER run commands like `pip`, `pytest`, or `python` directly. Always use `./dev.sh exec main ...` or `./dev.sh exec script ...`.
- **Check `.env`**: Configuration defaults are in `.env.example`.
- **Knowledge Base**: This is a RAG-enabled project. Check `ai-workflow.md` for LangChain and ChromaDB standards.

## 3. Documentation First
- **`agent_docs/`**: All BMAD artifacts (PRDs, ADRs, Stories) live here. Read them before starting any task.
- **Living Documents**: Always update `README.md`, `architecture.md`, and `user-guide.md` to reflect the latest state.
- **Chronological Records**: Create new versioned files for Stories and ADRs.

## 4. Rule Priority
- [ ] Security first (`security-mandate.md`).
- [ ] Use Docker patterns (`docker-commands.md`).
- [ ] Follow linting and TDD (`fastapi-backend.md`).

**When in doubt, consult the `bmad-architect` (Winston).**
