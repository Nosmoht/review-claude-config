# Error Class to Primitive Mapping for AI Coding Assistants

Sources:
- [How Many Instructions Can LLMs Follow at Once? (IFScale)](https://arxiv.org/abs/2507.11538) — Distyl AI benchmark: 20 frontier models, 10-500 instructions, three decay patterns
- [Debugging AI-Generated Code: 8 Failure Patterns & Fixes](https://www.augmentcode.com/guides/debugging-ai-generated-code-8-failure-patterns-and-fixes) — Augment Code's systematic taxonomy of AI code failures
- [Equipping Agents for the Real World with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — Anthropic's progressive disclosure architecture for skills
- [Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — Anthropic's official context engineering guidance
- [Automate Workflows with Hooks](https://code.claude.com/docs/en/hooks-guide) — Claude Code hooks documentation (deterministic lifecycle automation)
- [How to Write a Great agents.md: Lessons from Over 2,500 Repositories](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) — GitHub analysis of effective agent instruction files
- [Your AGENTS.md is a Liability](https://paddo.dev/blog/your-agents-md-is-a-liability/) — Analysis of instruction dilution, attention sinks, and modularization

Fetched: 2026-03-26

## Instruction Budget Research

The IFScale benchmark (Jaroslawicz et al., 2025; arXiv 2507.11538) tested 20 frontier models on 10-500 simultaneous keyword-inclusion instructions for a business report task. Key findings:

- **Best model scored 68% at 500 instructions** — one in three instructions silently dropped.
- **Three decay patterns**: (1) Threshold decay — reasoning models (o3, Gemini 2.5 Pro) hold near-perfect compliance through 100-250 instructions then collapse sharply. (2) Linear decay — steady decline from the start (GPT-4.1, Claude Sonnet 4). (3) Exponential decay — rapid failure (GPT-4o, LLaMA-4-Scout).
- **Primacy bias peaks at 150-200 instructions**: models satisfy earlier instructions at higher rates than later ones; bias is strongest at moderate density, then converges toward uniform failure at 300+ instructions as models shift from selective to universal instruction abandonment.
- **Practical ceiling**: reasoning models reliably follow 100-250 simple instructions before degradation onset. Non-reasoning models degrade from the start.

Implication for CLAUDE.md design: monolithic instruction files exceeding ~200 rules enter the degradation zone. Each added instruction dilutes attention to all others (softmax is zero-sum). The "Your AGENTS.md is a Liability" analysis cites Xiao et al. (ICLR 2024) on attention sinks — initial tokens receive disproportionate attention regardless of semantic content — and Liu et al. (TACL 2024) on lost-in-the-middle effects (20+ point accuracy drop for mid-context information).

## Error Taxonomy

Seven error classes observed in AI coding assistants, with Augment Code's 8 failure patterns as supporting evidence:

| Error Class | Description | Augment Code Pattern(s) |
|---|---|---|
| **Toolchain** | Wrong build commands, missing flags, incorrect tool invocations | Missing Context Dependencies (#8) |
| **Navigation** | Edits wrong file, misses related files, ignores project structure | Data Model Mismatches (#7) |
| **Convention** | Style violations, wrong commit format, naming mismatches | Outdated Library Usage (#6) |
| **Architecture** | Violates layering, creates circular deps, misuses abstractions | Performance Anti-Patterns (#3) |
| **Repetition** | Re-introduces fixed bugs, ignores prior context, loops on same approach | Error Handling That Assumes Happy Paths (#4) |
| **Domain** | Misunderstands business logic, applies wrong domain patterns | Missing Edge Cases (#5), Data Model Mismatches (#7) |
| **Security** | Hardcoded secrets, injection vulnerabilities, auth bypasses | Security Vulnerabilities (#2), Hallucinated APIs (#1) |

Augment Code's 8 patterns mapped: (1) Hallucinated APIs That Don't Exist, (2) Security Vulnerabilities That Look Functional, (3) Performance Anti-Patterns Nobody Notices, (4) Error Handling That Assumes Happy Paths, (5) Missing Edge Cases, (6) Outdated Library Usage, (7) Data Model Mismatches, (8) Missing Context Dependencies. Veracode's 2025 research found 45% of AI-generated code contains security vulnerabilities, with Java at 70%+ failure rates.

## Primitive Selection Framework

Claude Code provides four primitives at increasing autonomy levels. From Anthropic's official documentation:

| Primitive | Persistence | Trigger | Autonomy | Best For |
|---|---|---|---|---|
| **CLAUDE.md** | Always loaded at session start | Universal — every session | None (passive context) | Conventions, architecture decisions, coding standards |
| **Hooks** | Registered in settings.json | Deterministic lifecycle events (PreToolUse, PostToolUse, SessionStart, etc.) | Mechanical — runs shell commands, no LLM judgment | Format-on-save, file protection, environment reload, notifications |
| **Skills** | Loaded on demand via slash command or auto-detection | User invocation or relevance match | Guided — LLM follows structured instructions | Domain workflows, multi-step procedures, specialized analysis |
| **Agents/Subagents** | Spawned in isolated context | Delegated by parent or skill | Full — own toolchain, model selection, termination criteria | Complex verification, parallel tasks, multi-file operations |

Selection rule: **use the least autonomous primitive that solves the error class.**

- Toolchain/Convention errors → CLAUDE.md rules (always visible, no activation needed)
- Format/lint enforcement → Hooks (deterministic, cannot be forgotten)
- Navigation/Architecture/Domain errors → Skills (load domain knowledge on demand)
- Repetition/Security requiring verification → Agents (can inspect code, run tests, iterate)

## Progressive Disclosure

Anthropic's "Equipping Agents" post describes a 3-tier loading architecture that keeps context lean:

1. **Metadata at startup**: Skill name + description loaded from frontmatter into the skill index. Provides just enough for Claude to know when each skill applies without consuming context tokens. This is the "table of contents."
2. **SKILL.md on activation**: Full instructions loaded when the skill is invoked (by user or auto-detection). This is the "chapter" — procedure steps, output format, constraints.
3. **References on demand**: Additional files in the skill's `references/` directory loaded only when the skill explicitly reads them. This is the "appendix" — rubrics, templates, domain research.

This mirrors human cognition: we maintain indexes (file systems, bookmarks) rather than memorizing entire corpora, retrieving detail only when needed. The architecture directly addresses IFScale's finding: by deferring instructions to activation time, the always-loaded instruction count stays within the reliable 100-250 range.

## Prior Art Gap

Existing tools address parts of this problem but none map repo characteristics to error classes to primitives:

- **ContextPilot** (contextpilot.dev): Closest prior art. Analyzes codebases to generate .cursorrules, CLAUDE.md, and copilot-instructions.md. Detects frameworks, languages, and patterns. Provides context quality scoring. However, it generates generic context files — it does not classify which errors a repo is prone to or select primitives accordingly.
- **GitHub agents.md analysis** (2,500+ repos): Identified that effective files provide specific personas, exact commands with flags, clear boundaries, and code examples over prose. But this is guidance for writing better monolithic files, not for decomposing across primitives.
- **"Your AGENTS.md is a Liability"**: Correctly diagnoses the dilution problem and recommends modularization, front-loading critical rules, and pruning. But stops at "keep it shorter" — does not provide a framework for deciding what goes where.

**Gap**: No existing tool maps a repository's structure, toolchain, and domain → likely error classes → optimal primitive assignment. The error-class-to-primitive mapping in this document provides that missing framework.
