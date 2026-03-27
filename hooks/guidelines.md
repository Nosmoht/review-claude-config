## Skill/Agent/Rule Quality Checklist

You are editing a Claude Code skill, agent, or rule. Apply these quality guidelines:

**Frontmatter:** Skills need `name` and `description`. Descriptions should say what the item does and when it should trigger. Keep tool lists minimal. Rules must not add YAML frontmatter. Agents should include `<example>` blocks when activation is non-obvious.

**Evidence-first writing:** Prefer explicit evidence over broad claims. If you add a recommendation, make sure the target file gives a concrete reason for it and that the recommendation can be re-checked later.

**Clarity and completeness:** Use numbered steps, explicit sequencing, concrete conditionals, defined output format, and visible error handling. Replace vague phrases like "if needed" or "as appropriate" with measurable criteria.

**Prompt and context engineering:** Keep main files concise, move stable material to `references/`, and use just-in-time loading. Add verification criteria, not just instructions. Avoid time-sensitive wording such as "today", "latest", or "current year" unless the task explicitly requires it.

**Safety:** Restrict `allowed-tools` to what is actually needed. Add confirmation gates before writes or deletions. Use `disable-model-invocation: true` for side-effectful skills.

**Rules only:** Rules are directives, not prompts. They should be precise, scoped, and enforceable with strong verbs like `must`, `never`, or `always`.
