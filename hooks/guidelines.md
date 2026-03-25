## Skill/Agent/Rule Quality Checklist

You are editing a Claude Code skill, agent, or rule. Apply these quality guidelines:

**Frontmatter:** `name` and `description` are required. Description must specify precise trigger conditions. `allowed-tools` should be minimal (least privilege). For agents: include `<example>` blocks showing trigger patterns.

**Clarity:** Every step must be unambiguous — if two models could produce different workflows, rewrite. Use numbered steps with explicit sequencing. Replace vague conditionals ("if needed", "as appropriate") with concrete criteria.

**Completeness:** Define output format with a literal template (placeholders, not descriptions). Handle error cases explicitly. Include input validation. For agents: add diverse `<example>` blocks covering common trigger patterns.

**Prompt Engineering:** Use structured output templates with placeholders. Add role priming for domain tasks. Include 2-3 diverse examples where output format is non-obvious. State negative constraints (what NOT to do). Add verification criteria so the agent can self-check its output.

**Context Engineering:** Keep SKILL.md under 500 lines. Offload stable knowledge to `references/` files. Use JIT retrieval (load data on demand, not upfront). For multi-agent dispatch: keep shared prefixes byte-identical for KV-cache efficiency. Every token must justify its cost.

**Safety:** Restrict `allowed-tools` to what is actually needed. Add confirmation gates before writes/deletes. Define stop conditions. Use `disable-model-invocation: true` for skills with side effects. If tools include Write/Bash/Edit, safety weight increases.

**Goal Alignment:** Include domain-specific checks and best practices. A domain expert should not find obvious missing steps. Verify the body actually supports achieving the stated goal.

**Rules only:** Evaluated on 3 dimensions — Clarity (30%), Completeness (30%), Goal Alignment (40%). Must be unambiguous directives with defined scope boundaries. No frontmatter, no tools, no prompt engineering required.
