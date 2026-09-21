## Rule Priority (Global)

When two rules pull in opposite directions, use this priority to decide:

0. **Professional Team SOP** — The foundation of our collaboration (TDD, DRY, LLD).
1. **Security** — Never compromise security for convenience.
1.1 **Docs-First & Research** — Always reference official docs and best practices before acting.
1.2 **Project Specifications & Contracts** — Always respect and follow all specifications, schemas, api contracts, and product briefs/designs defined under the `docs/` folder (such as `docs/product_brief.md`, `docs/api_contract.md`, PRDs under `docs/prd/`, and LLDs under `docs/lld/`) as the primary sources of truth if available.
2. **Consistency** — Follow existing patterns in each stack directory while applying DRY.
3. **Premium Quality** — Prioritize high-performance logic and premium aesthetics (Antigravity standard).
4. **Stack Conventions** — Respect the target framework's idioms.
5. **Simplicity** — When equally valid, prefer the simpler, more maintainable approach.
