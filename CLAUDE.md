# Review Claude Config

Maintainer operating guide for this repository (Clarity, Completeness, Prompt Engineering, Context Engineering, Goal Alignment, Safety, Metadata). Use this file for active repo conventions, command inventory, and maintenance workflow. User-facing orientation lives in [README.md](README.md). Skill and hook navigation lives in [docs/skills/README.md](docs/skills/README.md).

## Architecture

- **Plugin surface**: `skills/`, `agents/`, and `hooks/`, installed via `claude --plugin-dir`. `agents/` contains top-level perspective agents (`review-perspective-{clarity,correctness,integration}`) dispatched by `/review-skill` in multi-perspective mode (P1.1 pilot).
- **Shared references**: `skills/review-claude-config/references/`, including the rubric, baseline, evidence contract, source-quality criteria, and review-report contract
- **Domain cache**: `skills/review-claude-config/references/domain-cache/`, contains 7 universal methodology entries (context-engineering, research-sourcing, etc.) maintained on the repo's 90-day rhythm. Domain-specific knowledge is researched at runtime via WebSearch, not pre-cached
- **Repo-internal skills**: `.claude/skills/` for maintenance utilities not needed globally
- **Review reports**: `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/` for timestamped reports organized by target repo, consumed by analytics and apply flows. Slug = `basename(target_dir)`, see `references/repo-identification.md`
- **Self-contained knowledge**: The plugin carries all knowledge needed for quality in its own files. External services (KB server, web research) are optional enhancements — skills degrade gracefully without them. The distillation path is: `research/ → engineering-baseline.md + skill-agent-format-conventions.md → skill decisions`. Research findings must be distilled into these operational surfaces to affect plugin behavior in any repo.
- **Runtime audit layer**: `hooks/` provides observation (PostToolUse, SubagentStart/Stop, SessionEnd) and opt-in policy enforcement (PreToolUse policy gate). Audit traces written to `$CLAUDE_PLUGIN_DATA/audit/`. Skills consume these traces for analysis.

### Plugin vs External Infrastructure Boundaries

The plugin model has hard limits. These boundaries determine what can be built as skills/hooks vs what requires external systems.

| Capability | Plugin provides | Requires external infrastructure |
|---|---|---|
| Per-tool-call audit log | PostToolUse async hook → JSONL | — |
| Pre-action policy gate | PreToolUse hook (deny/ask/allow) | — |
| Delegation chain tracking | SubagentStart/Stop hooks | — |
| Session summary metrics | SessionEnd hook | — |
| Post-hoc trace analysis | `/review-session-trace`, `/classify-trace-errors`, `/audit-trust-chain`, `/audit-policy-compliance` | — |
| Memory hygiene auditing | `/audit-memory-hygiene` | — |
| Persistent governance state | — | MCP server (policy store, cross-session ledger) |
| Kill switch / session termination | — | External process manager or sidecar |
| Token cost tracking | — | API proxy between Claude Code and Anthropic API |
| Multi-run statistical evaluation | — | CI pipeline invoking Claude Code programmatically |
| Continuous runtime monitoring | — | Watchdog daemon |

## Commands

This is the authoritative maintainer command inventory for the repo.

### Review

- `/review-claude-config [folder] [--validation]` - batch audit of skills, agents, and rules
- `/review-skill <path>` - single skill review
- `/review-agent <path>` - single agent review
- `/review-rule <path>` - single rule review
- `/review-hook <path>` - single hook review (hooks.json + Python scripts)
- `/review-mcp-server <path>` - single MCP server config review (.mcp.json)
- `/review-plugin <plugin-root>` - single Claude Code plugin review (.claude-plugin/plugin.json + components)
- `/review-settings <path>` - single settings.json quality review
- `/review-claude-md <path>` - single CLAUDE.md quality review
- `/audit-mcp-auth [account]` - audit macOS keychain for #45551 MCP OAuth credential-store race
- `/review-session-trace <path>` - analyze Claude Code JSONL transcript for runtime behavior
- `/classify-trace-errors <path>` - classify trace errors against MAST failure taxonomy
- `/audit-policy-compliance <path>` - audit tool call authorization against action classification policy
- `/audit-trust-chain <path>` - audit delegation chains for trust violations (orphan agents, CWD escapes, scope)
- `/audit-memory-hygiene [memory-dir]` - scan memory files for poisoning, staleness, credential leaks
- `/suggest-skills [folder]` - heuristic skill discovery
- `/audit-repo [folder]` - repo-structure audit for Claude Code primitives

### Fix

- `/apply-review-findings [report]` - orchestrate fixes from a review report
- `/apply-skill-review-findings [report]`
- `/apply-agent-review-findings [report]`
- `/apply-rule-review-findings [report]`
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
- `/scaffold-mcp-server <server-name>` - scaffold a `.mcp.json` server entry (declaration only, not server code)
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
- **Iterate reviews until convergence.** Converged = two consecutive runs on unchanged files produce: (1) **on the deterministic subset** (finding_ids whose `checklist_item` is in the 28 binary items or 14 narrative-parent items enumerated in [merge-rules.md §"Perspective Finding Handling"](skills/review-skill/references/merge-rules.md)) — identical set of `finding_id`s at Impact High/Medium; (2) grade variance ≤1 letter in any dimension; (3) no null dimensions where prior run had values. Advisory findings (items outside the deterministic subset) are demoted to Low severity at merge time, surface in the cert for reviewer triage, and do NOT block convergence. Medium and High findings in the deterministic subset block completion.
- **Prefer evidence over rhetoric.** Findings should cite concrete paths, text, or examples.
- **Research before design in novel areas.** Save results in `research/` with sources.
- **Use `$HOME/...` (never absolute user-home paths) in written doc/report content.** The user's `block-sensitive-content.sh` PreToolUse hook rejects Writes whose content embeds a hardcoded home-dir prefix. Applies to review report frontmatter `target:` fields, plan files, and any body text. Relative paths (`.claude/skills/...`) in bodies are preferred. Scan generated content for absolute home-dir prefixes before Write.
- **Recover large lost tool-call payloads from the session transcript, don't regenerate.** If context compaction drops a prepared Write/Edit payload (e.g., a multi-thousand-line review report), the full content is preserved in the session jsonl under `$HOME/.claude/projects/<project>/<sessionId>.jsonl`. Parse jsonl for the matching `tool_use` entry and extract `input.content` — regeneration can require re-dispatching all analysis agents.
- **Keep project knowledge in the repo.** No reliance on external memory.
- **Mid-session rubric/baseline freeze.** `skills/review-claude-config/references/scoring-rubric.md` and `engineering-baseline.md` are committed BETWEEN sessions, never edited mid-session. Mid-session changes invalidate the shared prefix used by perspective sub-agents and break KV-cache friendliness (84% → <20% cache-hit drop). If a critical rubric bug is found mid-session, abort and fix `scoring-rubric.md` via direct edit in a fresh session; baseline bugs use `/refresh-engineering-baseline`.
- **Verify changes with the repo's own review skills, not ad-hoc Plan agents.** `make validate` checks structure; review skills check quality. Use this mapping:

| Changed... | Run... |
|---|---|
| Evaluation guide or rubric | `/review-skill` or `/review-agent` on a representative artifact |
| Hook code or hook eval guide | `/review-hook hooks/hooks.json` |
| CLAUDE.md | `/review-claude-md CLAUDE.md` |
| Rule eval guide or template | `/review-rule` on a representative rule |
| Eval cases | `/run-eval-cases <case-numbers>` |
| Cross-primitive references | `/validate-primitive-dependencies` |
| Any batch of changes | `/review-claude-config .` |

## Development Conventions

- Language: English
- Reference file budgets: see `scripts/validate_token_budgets.py` BUDGETS map (authoritative); default `<=500` tokens, named files have justified higher budgets
- Treat exact thresholds and workflow conventions as `Repo default` unless stronger evidence exists
- Domain cache contains only universal methodology entries (7 total); domain-specific knowledge is researched at runtime. Universal entries follow the repo's 90-day refresh cadence
- `last_refreshed` belongs in YAML frontmatter only — body markers (`**Fetched:**`, `Last reviewed:`) are distinct fields with different meanings and must not be converted; absence of `last_refreshed` causes silent skip by `check-repo-health` (not FAIL)
- Reference files carry `name` + `description` + `last_refreshed`; research files carry `last_refreshed` only — these shapes are intentionally different
- `last_refreshed` is hard-enforced only for `engineering-baseline.md`; `session_check.py` also provides opportunistic freshness warnings for all other `*.md` files in `skills/review-claude-config/references/`, reporting only the single oldest stale file (>90 days)
- WebFetch is optional; skills must degrade gracefully to WebSearch-only when needed
- Baseline updates happen only through `/refresh-engineering-baseline`
- Baseline refresh covers only `Prompt Engineering`, `Context Engineering`, and `Tool Design`
- Artifact identity is `type + path`; analytics series identity is `repo + generated_by + type + path`; `name` is display-only
- Commit format: `type(scope): description`
- Make targets:

| Target | Command | Purpose |
|--------|---------|---------|
| `validate` | `make validate` | Run all checks (lint + format + schema + budget + test) |
| `lint` | `make lint` | `ruff check hooks/ scripts/` |
| `format` | `make format` | `ruff format --check hooks/ scripts/` |
| `schema-validate` | `make schema-validate` | `python3 scripts/validate_schema.py` |
| `token-budget` | `make token-budget` | `python3 scripts/validate_token_budgets.py` |
| `test` | `make test` | `pytest tests/ -v --tb=short` |
| `test-cov` | `make test-cov` | `pytest tests/ -v --tb=short --cov=hooks --cov=scripts` |
- Audit-fix chain: commit review report first, then commit fixes
- Review, suggest, and audit skills are read-only on analyzed files except for reports (`$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/`) and domain cache
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
- [Claude Code Skill and Agent Format Conventions](research/claude-code/skill-agent-format-conventions.md) — official frontmatter fields, body structure, activation patterns, safety constraints. Load when scaffolding, reviewing format violations, or checking frontmatter completeness. Includes 15-field agent-frontmatter 2026 catalog + Opus 4.7 migration rules (SAMP-1/SAMP-2).
- [Claude Code Plugin System](research/claude-code/plugin-system.md) — `.claude-plugin/plugin.json` manifest schema, marketplace distribution, skill/agent namespacing, `claude plugin validate` CLI, top-5 failure modes. Load when reviewing plugin manifests, scaffolding new plugins, or writing `/review-plugin`.
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
- [Hook-Based Runtime Observation Patterns](research/hook-observation/hook-based-runtime-observation-patterns.md) — 26 hook events categorized by observation value; 5 observation patterns (audit logger, policy gate, session bookend, delegation tracker, stateful via ENV_FILE); transcript_path as underutilized asset; architectural boundaries (no token/cost/confidence visibility). Load when designing runtime audit hooks or building trace infrastructure.
- [Prompt Injection Taxonomy for Claude Code](research/injection-taxonomy/injection-taxonomy.md) — 4 injection vectors (direct, indirect via tools, via memory, via config); detection feasibility per vector; IJ-* checklist item evidence. Load when reviewing Safety for injection surface or designing injection detection.
- [Memory Poisoning Patterns](research/memory-poisoning/memory-poisoning-patterns.md) — 3 poisoning vectors (instruction injection, stale accumulation, contradiction insertion); detection heuristics; mitigation patterns. Load when running `/audit-memory-hygiene` or evaluating memory-related security.
- [Claude Code Auto-Memory System](research/claude-code/auto-memory-system.md) — per-project MEMORY.md storage, 200-line / 25 KB system-prompt injection rule, agent memory scoping (`user`/`project`/`local`), 3 poisoning-vector detectors. Load when extending `/audit-memory-hygiene` or reviewing agents with `memory:` frontmatter.
- [Claude Code Known Issues](research/claude-code/known-issues.md) — rolling catalog of open bugs (permissions, MCP OAuth, hooks, plugin manifest git-index leak) with detector recipes per issue. Load when building or extending `/audit-policy-compliance`, `/audit-mcp-auth`, or any bug-specific detector.
- [Injection Surface Catalog](skills/review-claude-config/references/injection-surface-catalog.md) — IJ-1 data flow path and IJ-2 raw input forwarding detection criteria. Load during Safety evaluation for IJ-* checklist items.

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
- [Audit-Harness Research Summary](research/audit-harness/audit-harness-research-summary.md) — 15 core audit themes, 15 autonomy themes, 12 target audit domains, 9 required system components for an autonomous agent harness auditor. Seed document for the runtime audit roadmap. Load when planning new phases or revisiting architectural scope.

### Review Convergence & Evaluation Quality
- [LLM Evaluator Consistency](research/llm-evaluator-consistency/llm-evaluator-consistency.md) — behavioral rubrics ICC3 +46%; RULERS binary decomposition QWK 0.7276; majority voting k=3 strongest variance reduction. Load when addressing review convergence or evaluator reliability.
- [Rubric Design for LLM Evaluators](research/rubric-design/rubric-design-for-llm-evaluators.md) — Prometheus r=0.897 with behavioral anchoring; binary 76% acc vs 5-way 57%; LLM-hostile/friendly pattern catalog. Load when modifying scoring-rubric.md or evaluation guides.
- [Rubric Calibration Evidence](research/rubric-design/rubric-calibration-evidence.md) — binary-verifiable checklist items for issues #4/#5/#6/#10 (META-1a/1b/2/3a/3b, CE-X, COMP-X/Y/Z) with BOUNDARY PASS/FAIL examples + 10 Tier-1 citations. Load when implementing P0.5 rubric calibration or auditing rubric item quality.
- [Task-Type Rubric Variants](research/rubric-design/task-type-rubric-variants.md) — override tables per task type (orchestrator / code-review / research-synthesis / scaffold / tutoring) + heuristic-first resolution algorithm. Load when reviewing task-specialized skills or resolving dimension-weight ambiguity.
- [Checklist Item Calibration](research/checklist-calibration/checklist-calibration.md) — RubricEval 55.97% on hard binary; IFEval programmatic-first; BARS kappa >0.80 with boundary examples; Gawande 5-9 item cap. Load when calibrating evaluation guide checklist items.
- [Finding Identity and Lifecycle](research/finding-identity/finding-identity-and-lifecycle.md) — SARIF v2.1.0 fingerprints; SonarQube cascading match; baseline diff pattern; dual-layer fingerprint + multi-source merge rules (Layer 0–4) for multi-perspective review. Load when implementing finding tracking, delta comparison, or the P1.1 merge pipeline.
- [Fix Completeness](research/fix-completeness/fix-completeness.md) — DRV K=2 raises yield 0-54%→50-77%; LLMs cannot self-correct without external feedback; per-finding tracking raises resolution 52%→70%. Load when improving apply-review-findings.
- [Structured Output Recovery Patterns](research/fix-completeness/structured-output-recovery-patterns.md) — 3-tier cascade (strict parse → LLM-assisted minimal-schema → regex text fallback) reducing total failure <2%. Aperant PR #1797 reference. Load when implementing `report-parser-contract.md` or reviewing robustness of `apply-*-review-findings`.
- [Verification Methods per Dimension](research/verification-methods/verification-methods-per-dimension.md) — CheckEval +0.45 agreement with binary verification; 3-tier architecture (deterministic→LLM-binary→functional). Load when designing fix verification.
- [Selective Multi-Rating](research/selective-multi-rating/selective-multi-rating.md) — Trust or Escalate: 78.5% cost reduction; selective k=3 at 1.6x cost targets borderline items. Load when considering multi-rater evaluation.

### Primitive Coverage
- [MCP Server Configuration Quality](research/mcp-server-quality/mcp-server-configuration-quality.md) — MCP spec schema, security risk taxonomy (43% command injection rate), server risk tiers, token cost thresholds. Load when reviewing MCP server configs or designing MCP evaluation.
- [Settings.json Quality Criteria](research/settings-quality/settings-json-quality-criteria.md) — 60+ fields, scope precedence, critical security fields (permissions.deny, enableAllProjectMcpServers, invalid JSON). Load when reviewing settings.json or designing settings evaluation.

### Supporting Research
- [LLM Agent Caching and Knowledge Persistence Patterns](research/agent-knowledge-caching/llm-agent-caching-patterns.md) — file-based memory beats graph-based (74% vs 68.5%); CAG beats RAG for bounded corpora. Load when designing knowledge persistence or reviewing caching strategies.
- [Aperant Orchestration Patterns](research/agent-knowledge-caching/aperant-orchestration-patterns.md) — Anthropic prompt-cache mechanics (4,096/1,024 token minimums, 90% savings), shared-prefix construction, atomic file writes (Aperant PR #1785). Load when designing multi-perspective orchestration (P1.1), review-report persistence (P2.7), or debugging KV-cache hit rate.
- [Cache-Status Labels and Runtime JIT Research](research/agent-knowledge-caching/cache-labels-and-jit-research.md) — 4-state label schema (CACHED/STALE/FAILED/RUNTIME_RESEARCH), 2h sliding-window stuck-detection, Tier-1/2/3 ephemeral research injection, Aperant RDR 6-priority recovery. Load when designing domain-cache freshness (P2.4) or runtime fallback (P2.6).
- [Claude Code /ultrareview Service](research/claude-code/ultrareview-service.md) — cloud multi-agent PR review service (GA 2026-04-16). $15–25/review. No programmatic API trigger — only `@claude review` PR comments. Load when considering `/ultrareview` integration or recommending it from local review skills.
- [Claude Code Monitor Tool](research/claude-code/monitor-tool.md) — streaming stdout tool for background processes. Known bugs #50258 (notification flooding) and #45976 (tmux detachment). Not on Bedrock/Vertex/Foundry. Load when choosing between Monitor, `Bash(run_in_background)`, and `/loop` for long-running skills.
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
