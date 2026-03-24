# Equipping Agents for the Real World with Agent Skills

**Source:** [Claude Blog](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)
**Fetched:** 2026-03-24

## What Makes a Good Skill

A skill requires a `SKILL.md` file with YAML frontmatter containing `name` and `description` metadata. The description is critical — Claude uses it to decide whether to activate the skill. "Claude will use these when deciding whether to trigger the skill in response to its current task," making clear, accurate naming essential for proper skill discovery.

Example: The PDF skill bundles a core `SKILL.md` with related files (`reference.md`, `forms.md`) that Claude accesses only when needed.

## Best Practices

### Evaluation-First Approach
"Identify specific gaps in your agents' capabilities by running them on representative tasks and observing where they struggle or require additional context."

### Progressive Layering
Start with lean core documentation, then split into separate files when content becomes unwieldy. "If certain contexts are mutually exclusive or rarely used together, keeping the paths separate will reduce the token usage."

### Iterative Refinement
"Ask Claude to capture its successful approaches and common mistakes into reusable context and code within a skill." This collaborative development reveals what agents actually need versus anticipated requirements.

### Perspective-Taking
Monitor real usage patterns rather than assuming optimal structure upfront.

## Progressive Disclosure (Context Engineering)

Skills implement a hierarchical information architecture mirroring "a well-organized manual that starts with a table of contents, then specific chapters, and finally a detailed appendix."

This design ensures "agents don't need to read the entirety of a skill into their context window when working on a particular task," making "the amount of context that can be bundled into a skill effectively unbounded."

### How It Works
1. Pre-load skill metadata (names/descriptions) into system prompt
2. Load full `SKILL.md` when Claude deems the skill relevant
3. Access supplementary files on-demand via code execution

## Quality Criteria

### Security
"Install skills only from trusted sources" and thoroughly audit code dependencies and external network connections before deployment.

### Structural Patterns
- Use code for deterministic operations (form extraction, sorting) rather than token generation
- Bundle executable scripts alongside documentation
- Keep instructions and code clear about when Claude should execute versus read-as-reference

### Documentation Quality
The `name` and `description` serve as discovery mechanisms — they must accurately convey skill scope without loading full context unnecessarily.
