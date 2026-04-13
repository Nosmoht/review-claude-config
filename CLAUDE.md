# Review Claude Config

Maintainer operating guide for this repository (Clarity, Completeness, Prompt Engineering, Context Engineering, Goal Alignment, Safety, Metadata). Use this file for active repo conventions, command inventory, and maintenance workflow. User-facing orientation lives in [README.md](README.md). Skill and hook navigation lives in [docs/skills/README.md](docs/skills/README.md).

## Architecture

- **Plugin surface**: `skills/` and `hooks/`, installed via `claude --plugin-dir`
- **Shared references**: `skills/review-claude-config/references/`, including the rubric, baseline, evidence contract, source-quality criteria, and review-report contract
- **Domain cache**: `skills/review-claude-config/references/domain-cache/`, committed to git and maintained on the repo's 90-day rhythm; this is a repo default, not a scientific claim
- **Repo-internal skills**: `.claude/skills/` for maintenance utilities not needed globally
- **Review reports**: `.claude/reviews/` for timestamped reports consumed by analytics and apply flows
- **Self-contained knowledge**: The plugin carries all knowledge needed for quality in its own files. External services (KB server, web research) are optional enhancements — skills degrade gracefully without them. The distillation path is: `research/ → engineering-baseline.md + skill-agent-format-conventions.md → skill decisions`. Research findings must be distilled into these operational surfaces to affect plugin behavior in any repo.

## Commands

This is the authoritative maintainer command inventory for the repo.

### Review

- `/review-claude-config [folder] [--validation]` - batch audit of skills, agents, and rules
- `/review-skill <path>` - single skill review
- `/review-agent <path>` - single agent review
- `/review-rule <path>` - single rule review
- `/review-hook <path>` - single hook review (hooks.json + Python scripts)
- `/review-claude-md <path>` - single CLAUDE.md quality review
- `/suggest-skills [folder]` - heuristic skill discovery
- `/audit-repo [folder]` - repo-structure audit for Claude Code primitives

### Fix

- `/apply-review-findings [report]` - orchestrate fixes from a review report
- `/apply-skill-review-findings [report]`
- `/apply-agent-review-findings [report]`
- `/apply-rule-review-findings [report]`
- `/apply-claude-md-review-findings [report]`
- `/apply-audit-findings [report]` - create primitives recommended by `audit-repo`

### Maintain

- `/audit-context-budget [folder]` - estimate session-start token cost of a repo's Claude Code config
- `/check-repo-health [all|freshness|tokens|integrity] [--validation]`
- `/review-analytics [folder] [--validation]`
- `/sync-research-index [folder]`
- `/refresh-engineering-baseline`
- `/run-eval-cases [case-number|all]`
- `/validate-primitive-dependencies [folder]`
- `/maintain-evidence-layer [--scope all|labels|freshness|contradictions|tiers]`

### Develop

- `/scaffold-skill [plugin|maintenance|external <target-path>] <name>`
- `/scaffold-agent <agent-name>`
- `/scaffold-rule <rule-name>`
- `/develop-hooks [hook-type] <hook-name>`

## Issue Tracking

This repo is managed on GitHub at **Nosmoht/review-claude-config**.

### Label Taxonomy

| Prefix | Purpose | Examples |
|--------|---------|---------|
| *(none)* | GitHub defaults | `bug`, `enhancement`, `documentation`, `invalid`, `duplicate`, `wontfix`, `question`, `good first issue`, `help wanted` |
| `priority:` | Urgency (P0=critical → P3=low) | `priority: P0` (#b60205), `priority: P1` (#d93f0b), `priority: P2` (#fbca04), `priority: P3` (#0e8a16) |
| `status:` | Lifecycle state | `status: in-progress` (#1d76db), `status: in-review` (#5319e7), `status: blocked` (#d93f0b) |
| `category:` | Domain area | `category: infrastructure`, `category: research`, `category: workflow`, `category: automation`, `category: utility-skills`, `category: primitive-coverage`, `category: eval-cases` |

### Issue Lifecycle

```
OPEN (new issue)
  → assign: priority: P*, category: *
  ↓
IN PROGRESS  — label: status: in-progress
  → implement → make validate → commit
  ↓                          ↓
IN REVIEW    — label: status: in-review     BLOCKED — label: status: blocked
  → feedback addressed                       → unblock, return to IN PROGRESS
  ↓
CLOSED — remove status label, close via mcp__github__issue_write (state_reason: completed)
```

### Workflow Rules

- **Before starting work**: check open issues to avoid duplicates — `gh issue list --repo Nosmoht/review-claude-config`
- **When a bug/improvement is found**: create issue immediately (`gh issue create` or `mcp__github__issue_write`)
- **When starting work on an issue**: set `status: in-progress` via `mcp__github__issue_write` (method: update, labels: ["status: in-progress", ...existing labels])
- **When blocked**: replace `status: in-progress` with `status: blocked`; document the blocker in an issue comment
- **When ready for review** (PR or peer check): replace with `status: in-review`
- **When closing**: only close when implemented, tested (`make validate`), committed, and docs updated — remove status label, close with state_reason: completed

## Working Guidelines

- **Every claim needs a source.** All research files, documentation, and recommendations must link to verifiable sources.
- **Verify claims before acting on them.** Check git history, inspect actual data. Do not redesign a working system based on theoretical concerns.
- **Use the canonical evidence layer for repo-wide claims.** Classify repository-level statements with [evidence-contract.md](skills/review-claude-config/references/evidence-contract.md) and follow [evidence-maintenance.md](docs/evidence-maintenance.md) for maintenance process.
- **Iterate reviews until convergence.** Address findings, then re-review. Medium and High findings block completion.
- **Prefer evidence over rhetoric.** Findings should cite concrete paths, text, or examples.
- **Research before design in novel areas.** Save results in `research/` with sources.
- **Keep project knowledge in the repo.** No reliance on external memory.

## Development Conventions

- Language: English
- Reference file budgets: see `scripts/validate_token_budgets.py` BUDGETS map (authoritative); default `<=500` tokens, named files have justified higher budgets
- Treat exact thresholds and workflow conventions as `Repo default` unless stronger evidence exists
- Domain cache refresh discipline follows the repo's 90-day cadence
- `last_refreshed` belongs in YAML frontmatter only — body markers (`**Fetched:**`, `Last reviewed:`) are distinct fields with different meanings and must not be converted; absence of `last_refreshed` causes silent skip by `check-repo-health` (not FAIL)
- Reference files carry `name` + `description` + `last_refreshed`; research files carry `last_refreshed` only — these shapes are intentionally different
- `last_refreshed` is hard-enforced only for `engineering-baseline.md`; `session_check.py` also provides opportunistic freshness warnings for all other `*.md` files in `skills/review-claude-config/references/`, reporting only the single oldest stale file (>90 days)
- WebFetch is optional; skills must degrade gracefully to WebSearch-only when needed
- Baseline updates happen only through `/refresh-engineering-baseline`
- Baseline refresh covers only `Prompt Engineering`, `Context Engineering`, and `Tool Design`
- Artifact identity is `type + path`; analytics series identity is `generated_by + type + path`; `name` is display-only
- Commit format: `type(scope): description`
- Audit-fix chain: commit review report first, then commit fixes
- Review, suggest, and audit skills are read-only on analyzed files except for reports and domain cache
- Apply skills and `scaffold-skill` modify files and require confirmation gates

## Research References

Load these files JIT when the task matches the trigger. Descriptions are routing signals — read them before deciding to load the full file.

### Operational References (always relevant for review work)
- [Evidence Contract](skills/review-claude-config/references/evidence-contract.md) — claim classes (Empirical/Engineering guidance/Repo default) and source precedence. Load when classifying evidence labels or writing claim citations.
- [Engineering Baseline](skills/review-claude-config/references/engineering-baseline.md) — distilled PE/CE/tool-design evidence (<2K tokens), updated only via `/refresh-engineering-baseline`. Load when reviewing Prompt Engineering, Context Engineering, or Tool Design dimensions.
- [Review Report Contract](skills/review-claude-config/references/review-report-contract.md) — canonical output schema: grade format, severity levels, Current/Recommended/Validation blocks. Load when writing or parsing review reports.
- [Source Quality Criteria](skills/review-claude-config/references/source-quality-criteria.md) — Tier 1/2/3 classification; cross-validation requires 2+ sources with ≥1 Tier 1/2. Load when evaluating research sources or running web research.
- [Evidence Maintenance Guide](docs/evidence-maintenance.md) — label upgrade/downgrade process, contradiction resolution, freshness enforcement. Load when running `/maintain-evidence-layer` or auditing stale labels.

### Format & Scaffolding
- [Claude Code Skill and Agent Format Conventions](research/claude-code/skill-agent-format-conventions.md) — official frontmatter fields, body structure, activation patterns, safety constraints. Load when scaffolding, reviewing format violations, or checking frontmatter completeness.
- [Command Naming Conventions: Evidence-Based Findings](research/command-naming/command-naming-conventions.md) — verb-noun CLI convention; slash command brevity evidence; plugin naming patterns. Load when scaffolding new commands or reviewing command naming.
- [Scientific Research Dossier](docs/scientific-research-dossier.md) — repo-level evidence synthesis with theme matrix; tracks which research themes are covered. Load when planning new research or checking overall evidence state.

### Prompt & Context Engineering
- [Prompt Engineering Techniques: Evidence-Based Summary](research/prompt-engineering/prompt-engineering-techniques.md) — evidence-backed PE techniques: few-shot (largest gains), CoT, role priming, output constraints. Load when reviewing Prompt Engineering dimension or writing new skills.
- [Context Engineering: Overview and Industry Adoption](research/context-engineering/context-engineering-overview.md) — context rot starts at 60% window fill; ACE pattern; JIT retrieval tradeoffs. Load when reviewing Context Engineering dimension or designing context loading strategies.
- [Effective Context Engineering for AI Agents](research/context-engineering/anthropic-effective-context-engineering.md) — official Anthropic guidance: progressive disclosure, JIT retrieval, subagent isolation, write to files not context. Load when reviewing CE for agentic skills.
- [Context Engineering for AI Agents: Lessons from Building Manus](research/context-engineering/manus-context-engineering-lessons.md) — KV-cache optimization for skill chains, error message preservation, file-based state handoff. Load when reviewing multi-step agentic workflows or KV-cache strategies.
- [Instruction Following at Scale: Evidence-Based Thresholds](research/instruction-following/instruction-following-at-scale.md) — ISR <30% at avg 11.9 constraints (AgentIF); Claude Sonnet = linear decay from first density increase; >10 constraints risks Grade C. Load when reviewing Context Engineering B/C boundary or writing constraint-heavy skills/rules.
- [Context Window Optimization for AI Coding Assistants](research/token-efficiency/context-window-optimization.md) — context rot threshold at ~60% fill; token density strategies; irrelevant context degrades accuracy measurably. Load when reviewing token efficiency or Context Engineering dimension.
- [Selective Context Injection for LLM Agents: Evidence-Based Patterns](research/selective-context-injection/selective-context-injection-patterns.md) — CAG beats RAG for corpora <36K tokens; description quality is routing bottleneck; 15x manual compression via noun/metric preservation. Load when designing knowledge injection strategies or improving research index routing.

### Tool Design & Safety
- [Writing Effective Tools for AI Agents](research/tool-design/anthropic-writing-tools-for-agents.md) — Anthropic tool design: minimal surface area, clear names, typed parameters, no side effects in read tools. Load when reviewing Tool Design or Safety dimensions.
- [Least-Privilege Tool Grants for LLM Agents](research/tool-least-privilege/tool-least-privilege-agents.md) — OWASP LLM06; Progent reduces attack success 41–70% → 2–7% with least-privilege; 5-tier high-risk tool combination checklist. Load when reviewing Safety dimension tool grants or evaluating `allowedTools`/`disallowedTools`.
- [Tool Grant Decision Tree](skills/review-claude-config/references/tool-grant-decision-tree.md) — archetype-to-tool mapping and high-risk combination flags (Tier A/B/C). Load during Safety dimension evaluation when item has Write/Bash/Edit/MCP tools.
- [Autonomous Agent Reliability: Frameworks and Failure Taxonomies](research/autonomous-agent-reliability/autonomous-agent-reliability.md) — MAST 14 failure modes (kappa=0.88, 1600+ traces); R1–R10 rubric checks; R1/R4/R9 are High-severity B/C discriminators. Load when reviewing Safety for agentic skills or evaluating R1–R10 compliance.
- [Multi-Primitive Dependency Integrity in Claude Code](research/multi-primitive-dependencies/multi-primitive-dependency-integrity.md) — 8 cross-primitive dependency types with silent failure modes; exit-code phantom block bug (anthropics/claude-code#21988). Load when reviewing hook/skill/agent dependencies or running `/validate-primitive-dependencies`.

### Agent Skills & Quality
- [Equipping Agents for the Real World with Agent Skills](research/agent-skills/anthropic-equipping-agents-with-skills.md) — three-layer progressive disclosure, skill description as routing signal, JIT file loading. Load when reviewing Metadata dimension or skill activation/description quality.
- [Agent Definition Quality Benchmarks](research/agent-definition-quality/agent-definition-quality-benchmarks.md) — proxy evaluation dimensions for design-time agent quality; description precision and activation accuracy signals. Load when reviewing Metadata dimension or agent description quality.
- [Domain Knowledge Impact on LLM Agent Quality](research/domain-knowledge/domain-knowledge-impact-on-quality.md) — domain-specific knowledge improves agent quality 30–206% (Tier 1). Load when reviewing Goal Alignment or justifying domain cache investment.
- [Change Discipline Workflow Research](research/change-discipline/change-discipline-workflow-research.md) — multi-perspective review reduces blindspots (arXiv:2502.17086); LLM self-review catches <44% of own errors. Load when designing review workflows or justifying multi-perspective subagent approach.

### Repo Analysis & Audit
- [Skill Gap Detection for LLM Agent Skills](research/skill-gap-detection/skill-gap-detection-approaches.md) — heuristics: task frequency, error patterns, workaround prevalence, user intent signals. Load when running `/suggest-skills` or `/audit-repo` gap analysis.
- [Repo Readiness Frameworks for AI Coding Assistants](research/repo-static-analysis/repo-readiness-frameworks.md) — static analysis frameworks for primitive detection by repo type. Load when running `/audit-repo` on unknown repos.
- [Architecture Pattern Recognition from Repository Structure](research/architecture-detection/architecture-pattern-recognition.md) — hybrid detection of repo architecture from file structure; Kustomize, Helm, FastAPI, monorepo patterns. Load when running `/audit-repo` on unknown repos.
- [Error Class to Primitive Mapping for AI Coding Assistants](research/primitive-derivation/error-class-to-primitive-mapping.md) — IFScale error taxonomy → primitive type mapping. Load when deriving primitives from error patterns or designing audit detection logic.
- [Systematische Claude Code Optimierung für unbekannte Repositories](research/repo-audit/repo-audit-methodology.md) — 6-phase primitive derivation methodology; phase ordering and output contracts. Load when running `/audit-repo` or extending audit workflow.

### Supporting Research
- [LLM Agent Caching and Knowledge Persistence Patterns](research/agent-knowledge-caching/llm-agent-caching-patterns.md) — file-based memory beats graph-based (74% vs 68.5%); CAG beats RAG for bounded corpora. Load when designing knowledge persistence or reviewing caching strategies.
- [Web Content Scraping Tools for LLM Agents](research/web-scraping/web-content-scraping-tools.md) — Jina Reader returns clean Markdown, handles 512K tokens; faster than raw WebFetch for technical docs. Load when writing web research skills or choosing fetch strategy.
- [Engineering Documentation Best Practices](research/documentation/engineering-documentation-best-practices.md) — rationale-first docs, hyperlinks over repetition; omitting rationale halves documentation value. Load when reviewing skill reference file quality or writing new reference docs.
- [Web Research Quality Evaluation](research/source-quality/web-research-quality-evaluation.md) — CRAAP/E-E-A-T credibility assessment; Tier 1/2/3 classification guide with age cutoffs. Load when evaluating research sources (alongside Source Quality Criteria).

## Change Discipline

Change Discipline Rule ([docs/change-discipline-rule.md](docs/change-discipline-rule.md)) — mandatory plan→review→implement→review→commit; **subagent must receive plan+CLAUDE.md+research+target files+checklist** before any plan approval. Zero Medium findings before commit. Applies to all changes: skills, agents, rules, code, docs.

**No plan without multi-perspective review.** Before calling ExitPlanMode, launch 2–3 Plan agents with different review perspectives (risk/regression, convention compliance, dependency correctness). Only truly trivial single-file changes (typo, rename) skip this step. LLM self-review catches <44% of its own errors — subagent review is mandatory.

## Research Backlog

[Research Backlog](docs/research-backlog.md) — 6 deep research topics for review suite quality gaps (autonomous reliability, dependency integrity, instruction following at scale, tool least-privilege, low-evidence baseline refresh, agent definition quality benchmarks).

## Manual Regression Cases

Use [Review Eval Cases](docs/review-eval-cases.md) after changing the rubric, baseline, review prompts, analytics conventions, or scaffold workflow.
