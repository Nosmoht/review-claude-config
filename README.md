# Review Claude Config

A Claude Code skill to analyze and optimize all Claude Code skills and agents in a given folder using evidence-based prompt and context engineering evaluation.

## What It Does

1. **Discovers** all skills (`.claude/skills/*/SKILL.md`) and agents (`.claude/agents/*.md`) in the target folder, including monorepo support
2. **Researches** domain-specific best practices for each item via WebSearch — because [domain knowledge improves output quality by 30-206%](https://arxiv.org/html/2601.15153) (with [graceful degradation](research/domain-knowledge/domain-knowledge-impact-on-quality.md) when WebSearch is unavailable)
3. **Evaluates** each item across 7 dimensions using a [curated, evidence-based rubric](.claude/skills/review-claude-config/references/scoring-rubric.md):
   - Clarity (15%) — Can a model follow this unambiguously?
   - Completeness (15%) — Are all cases handled?
   - Prompt Engineering (15%) — Does it use [proven techniques](research/prompt-engineering/prompt-engineering-techniques.md)?
   - Context Engineering (15%) — Is [context managed efficiently](research/context-engineering/anthropic-effective-context-engineering.md)?
   - Goal Alignment (20%) — Will it actually achieve its stated goal?
   - Safety (10-15%) — Are dangerous cases prevented?
   - Metadata (5-10%) — Is frontmatter correct and complete?
4. **Produces** per-item quality certificates with grades (A-F), strengths, and concrete optimization recommendations with rewrites

## Installation

Install as a Claude Code plugin (makes all review skills globally available):

```bash
claude --plugin-dir /path/to/review-claude-config
```

**Only local `--plugin-dir` is supported.** Marketplace installation would break domain cache writes since `${CLAUDE_PLUGIN_ROOT}` would point to a read-only directory.

For repo-internal maintenance skills only (not globally needed):
```bash
cp -r .claude/skills/refresh-engineering-baseline <target>/.claude/skills/
cp -r .claude/skills/research-index <target>/.claude/skills/
```

## Usage

```
/review-claude-config              # Audit all skills/agents/rules in current directory
/review-claude-config /path/to    # Audit a specific folder
/review-skill <path>              # Review a single skill
/suggest-skills                   # Identify missing skills
/audit-repo                       # Map error classes to recommended primitives
/apply-review-findings            # Apply High/Medium findings from latest review
/refresh-engineering-baseline     # Update the baseline with latest research
```

## Architecture

- [**`review-claude-config/SKILL.md`**](.claude/skills/review-claude-config/SKILL.md) — Orchestrator skill. Dispatches parallel analysis subagents per item. Uses a static [engineering baseline](.claude/skills/review-claude-config/references/engineering-baseline.md) for consistent results. Read-only on analyzed files; writes reports to `.claude/reviews/`.
- [**`refresh-engineering-baseline/SKILL.md`**](.claude/skills/refresh-engineering-baseline/SKILL.md) — Separate skill to update the baseline reference via WebSearch. User-invoked only. Includes freshness gate (90-day), source quality criteria with cross-validation, and user confirmation before writing.
- **`.claude/reviews/`** — Timestamped review reports (`YYYY-MM-DDTHHMMSS-review-claude-config.md`) with YAML frontmatter for machine-readable tracking of skill quality evolution.
- [**`references/scoring-rubric.md`**](.claude/skills/review-claude-config/references/scoring-rubric.md) — A-F grading criteria with discriminating examples per dimension
- [**`references/engineering-baseline.md`**](.claude/skills/review-claude-config/references/engineering-baseline.md) — Curated prompt, context, and tool design techniques with evidence sources

### Key Design Decisions

Every design decision is evidence-based. See the full rationale in [docs/planning-process-learnings.md](docs/planning-process-learnings.md).

| Decision | Why | Evidence |
|----------|-----|----------|
| Separate review + refresh skills | Avoid race conditions, ensure consistent results | [Single Responsibility Principle](docs/planning-process-learnings.md#6-separate-concerns-static-baseline--refresh-skill) |
| Domain WebSearch per item | Structural review alone misses domain-critical gaps | [30-206% quality improvement](research/domain-knowledge/domain-knowledge-impact-on-quality.md) |
| Context Engineering as evaluation dimension | It's the broader discipline; prompt engineering is a subset | [Anthropic research](research/context-engineering/anthropic-effective-context-engineering.md) |
| No Bash in allowed-tools | Enforces safety via tooling, not just rules | [Principle of least privilege](research/tool-design/anthropic-writing-tools-for-agents.md) |
| Timestamped report files | Each review run produces a unique file, supporting iterate-until-convergence workflow | Multiple runs per day are expected |
| Deterministic scoring formula | A=95, B=85, C=75, D=65, F=50 weighted sum ensures consistent Overall grades | Eliminates subjective variation across runs |
| Token budgets (baseline <2K, rubric <1K) | Focused context outperforms unfocused context | [Context rot research](research/context-engineering/context-engineering-overview.md) |
| Cache-friendly subagent dispatch | 10x cost difference cached vs uncached | [Manus/Meta production lessons](research/context-engineering/manus-context-engineering-lessons.md) |

## Research

All research is saved in [`research/`](research/) organized by topic:

| Topic | Files | Key Finding |
|-------|-------|-------------|
| [Context Engineering](research/context-engineering/) | [Anthropic article](research/context-engineering/anthropic-effective-context-engineering.md), [Manus lessons](research/context-engineering/manus-context-engineering-lessons.md), [Overview](research/context-engineering/context-engineering-overview.md) | Context is a finite resource; 300 focused tokens > 113K unfocused |
| [Prompt Engineering](research/prompt-engineering/) | [Techniques summary](research/prompt-engineering/prompt-engineering-techniques.md) | Structured output, role priming, CoT, few-shot, constraints |
| [Tool Design](research/tool-design/) | [Anthropic article](research/tool-design/anthropic-writing-tools-for-agents.md) | "Small refinements to tool descriptions yield dramatic improvements" |
| [Agent Skills](research/agent-skills/) | [Anthropic article](research/agent-skills/anthropic-equipping-agents-with-skills.md) | Progressive disclosure makes skill context "effectively unbounded" |
| [Domain Knowledge](research/domain-knowledge/) | [Academic evidence](research/domain-knowledge/domain-knowledge-impact-on-quality.md) | 30-206% quality improvement with domain-specific knowledge |
| [Claude Code Formats](research/claude-code/) | [Format conventions](research/claude-code/skill-agent-format-conventions.md) | Skill/agent file structure, frontmatter fields, naming |
| [Documentation](research/documentation/) | [Best practices](research/documentation/engineering-documentation-best-practices.md) | Hyperlink everything, document rationale, organize for discoverability |

## For Colleagues

If you want to learn from how this project was built — the iterative planning process, evidence-based decision making, subagent review loops, and the mistakes we almost made — read [**Planning Process Learnings**](docs/planning-process-learnings.md).

## Primary Sources

- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic: Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
- [Anthropic: Equipping agents with agent skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)
- [Manus/Meta: Context Engineering for AI Agents](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
- [arXiv 2601.15153: Domain Knowledge Impact](https://arxiv.org/html/2601.15153)
- [arXiv 2507.13334: Survey of Context Engineering](https://arxiv.org/abs/2507.13334)
- [Chroma Research: Context Rot](https://research.trychroma.com/context-rot)
