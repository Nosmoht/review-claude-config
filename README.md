# Review Claude Config

Evidence-based quality review plugin for Claude Code skills, agents, and rules. Evaluates across 7 dimensions with A-F grading, produces actionable optimization recommendations.

## What It Does

1. **Discovers** all skills (`.claude/skills/*/SKILL.md`), agents (`.claude/agents/*.md`), and rules (`.claude/rules/*.md`) in the target folder, including monorepo support
2. **Researches** domain-specific best practices for each item via WebSearch — because [domain knowledge improves output quality by 30-206%](https://arxiv.org/html/2601.15153) (with [graceful degradation](research/domain-knowledge/domain-knowledge-impact-on-quality.md) when WebSearch is unavailable)
3. **Evaluates** each item across 7 dimensions using a [curated, evidence-based rubric](skills/review-claude-config/references/scoring-rubric.md):
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
cp -r .claude/skills/sync-research-index <target>/.claude/skills/
```

## Workflow

After each step, you'll see a numbered menu with your options — just type the number to continue.

### Quality Review (existing skills/agents/rules)

Start here to evaluate and improve existing Claude Code primitives.

1. `/review-claude-config [folder]` — batch review all items (or `/review-skill`, `/review-agent`, `/review-rule` for singles)
2. Apply findings → menu offers `/apply-review-findings`
3. Verify → menu offers re-review to confirm improvements
4. Track → `/review-analytics` shows grade evolution across cycles

### New Project Setup (repo audit)

Start here to determine what Claude Code primitives a repo needs.

1. `/audit-repo [folder]` — analyze repo, produce prioritized intervention matrix
2. Apply → menu offers `/apply-audit-findings` (creates CLAUDE.md sections, rules, hooks)
3. Scaffold → menu offers `/scaffold-skill` for each recommended skill
4. Review → menu offers `/review-claude-config` to evaluate new primitives

### Skill Discovery

Start here to explore what skills a project would benefit from.

1. `/suggest-skills [folder]` — open-ended skill opportunity analysis
2. Scaffold → menu offers `/scaffold-skill` for suggested skills
3. Review → menu offers `/review-claude-config` to evaluate new skills

## Command Reference

### Review (read-only on analyzed files)

```
/review-claude-config [folder]     # Batch audit all skills/agents/rules
/review-skill <path>               # Review a single skill
/review-agent <path>               # Review a single agent
/review-rule <path>                # Review a single rule
/suggest-skills [folder]           # Identify missing skills with prioritized suggestions
/audit-repo [folder]               # Map error classes to recommended primitives
```

### Fix (apply review recommendations, requires confirmation)

```
/apply-review-findings [report]              # Orchestrate fixes from any review report
/apply-skill-review-findings [report]        # Apply skill-specific findings
/apply-agent-review-findings [report]        # Apply agent-specific findings
/apply-rule-review-findings [report]         # Apply rule-specific findings
/apply-audit-findings [report]               # Create primitives from audit-repo recommendations
```

### Maintain (diagnostics)

```
/check-repo-health [all|freshness|tokens|integrity]  # Reference freshness, token budgets, integrity
/review-analytics [folder]                            # Grade trajectories and regression detection
/sync-research-index [folder]                         # Detect drift between research/ and CLAUDE.md
```

### Develop

```
/scaffold-skill <name>             # Generate skill directory with SKILL.md, references/, CLAUDE.md registration
/refresh-engineering-baseline      # Update baseline with current web research
```

## Architecture

- **`.claude-plugin/plugin.json`** — Plugin manifest (name, version, description)
- **`skills/`** — 13 globally-available skills installed via `claude --plugin-dir`. Organized by function: 4 review, 4 apply, 5 analysis/utility skills.
- [**`skills/review-claude-config/references/`**](skills/review-claude-config/references/) — Shared references for all review skills:
  - [**`scoring-rubric.md`**](skills/review-claude-config/references/scoring-rubric.md) — A-F grading criteria with discriminating examples per dimension
  - [**`engineering-baseline.md`**](skills/review-claude-config/references/engineering-baseline.md) — Curated prompt, context, and tool design techniques with evidence sources
  - [**`domain-cache/`**](skills/review-claude-config/references/domain-cache/) — 24 pre-researched domains committed to git, refreshed on 90-day cycles
- **`hooks/`** — Two hooks configured in `hooks.json`:
  - `skill_quality_gate.py` (PreToolUse on Edit/Write) — injects [`guidelines.md`](hooks/guidelines.md) quality checklist when editing skill, agent, or rule files
  - `session_check.py` (SessionStart) — warns if engineering baseline is stale (>90 days)
- **`.claude/skills/`** — 2 repo-internal maintenance skills (not globally needed): `refresh-engineering-baseline`, `sync-research-index`
- **`.claude/reviews/`** — Timestamped review reports (`YYYY-MM-DDTHHMMSS-{type}.md`) with YAML frontmatter for tracking quality evolution

### Key Design Decisions

Every design decision is evidence-based. See the full rationale in [docs/planning-process-learnings.md](docs/planning-process-learnings.md).

| Decision | Why | Evidence |
|----------|-----|----------|
| Separate review + refresh skills | Avoid race conditions, ensure consistent results | [Single Responsibility Principle](docs/planning-process-learnings.md#6-separate-concerns-static-baseline--refresh-skill) |
| Domain WebSearch per item | Structural review alone misses domain-critical gaps | [30-206% quality improvement](research/domain-knowledge/domain-knowledge-impact-on-quality.md) |
| Context Engineering as evaluation dimension | It's the broader discipline; prompt engineering is a subset | [Anthropic research](research/context-engineering/anthropic-effective-context-engineering.md) |
| No Bash in review allowed-tools | Enforces safety via tooling, not just rules | [Principle of least privilege](research/tool-design/anthropic-writing-tools-for-agents.md) |
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
| [Agent Knowledge Caching](research/agent-knowledge-caching/) | [Caching patterns](research/agent-knowledge-caching/llm-agent-caching-patterns.md) | File-based memory outperforms graph systems; simpler storage effective for <128K tokens |
| [Web Scraping](research/web-scraping/) | [Scraping tools](research/web-scraping/web-content-scraping-tools.md) | WebSearch snippets lack benchmarks and code examples; full scraping needed |
| [Skill Gap Detection](research/skill-gap-detection/) | [Detection approaches](research/skill-gap-detection/skill-gap-detection-approaches.md) | No proactive framework exists; skill gap detection is novel contribution |
| [Repo Static Analysis](research/repo-static-analysis/) | [Readiness frameworks](research/repo-static-analysis/repo-readiness-frameworks.md) | Three frameworks measure repo readiness maturity levels |
| [Token Efficiency](research/token-efficiency/) | [Context window optimization](research/token-efficiency/context-window-optimization.md) | Context rot degrades performance; positional accuracy and language choice matter |
| [Architecture Detection](research/architecture-detection/) | [Pattern recognition](research/architecture-detection/architecture-pattern-recognition.md) | Hybrid: directory heuristics for recall + dependency graphs for precision |
| [Primitive Derivation](research/primitive-derivation/) | [Error-to-primitive mapping](research/primitive-derivation/error-class-to-primitive-mapping.md) | Best models score 68% at 500 instructions; budget ~100-150 after system prompt |
| [Repo Audit](research/repo-audit/) | [Audit methodology](research/repo-audit/repo-audit-methodology.md) | Deductive analysis derives Claude Code primitives from repo structure and error patterns |

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
