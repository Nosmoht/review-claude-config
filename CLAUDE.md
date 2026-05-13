# Review Claude Config

Maintainer operating guide for this repository (Clarity, Completeness, Prompt Engineering, Context Engineering, Goal Alignment, Safety, Metadata). Use this file for active repo conventions, command inventory, and maintenance workflow. User-facing orientation lives in [README.md](README.md). Skill and hook navigation lives in [docs/skills/README.md](docs/skills/README.md).

## Architecture

- **Plugin surface**: `skills/`, `agents/`, and `hooks/`, distributed via personal marketplace (`Nosmoht/review-claude-config` → `ntbc-plugins/claude-config`); `claude --plugin-dir` is the dev override that takes precedence. `agents/` contains top-level perspective agents (`review-perspective-{clarity,correctness,integration}`) dispatched by `/review-skill` in multi-perspective mode (P1.1 pilot).
- **Shared references**: `skills/review-claude-config/references/`, including the rubric, baseline, evidence contract, source-quality criteria, review-report contract, plus 6 cross-skill files migrated 2026-05-03 (`merge-rules.md`, `commit-conventions.md`, `signal-catalog.md`, `report-schema.md`, `mcp-evaluation-guide.md`, `agent-evaluation-guide.md`). Hub-inclusion follows the Rule-of-Three: a reference file moves to the hub only when ≥3 cross-skill consumers depend on it. Files with 0–2 consumers stay skill-local (Locality of Behaviour over premature DRY).
- **Domain cache**: `skills/review-claude-config/references/domain-cache/`, contains 7 universal methodology entries (context-engineering, research-sourcing, etc.) maintained on the repo's 90-day rhythm. Domain-specific knowledge is researched at runtime via WebSearch, not pre-cached
- **Repo-internal skills**: `.claude/skills/` for maintenance utilities not needed globally
- **Repo-internal agents**: `.claude/agents/` for maintenance subagents that orchestrate this repo's workflow but are NOT shipped to plugin consumers (e.g., `builder-implementer`, `builder-evaluator` driven by `/implement-issue`). Mirrors the `.claude/skills/` repo-internal convention. Plugin-distributed agents stay at top-level `agents/`. Discovered only at session start; new agents require a fresh session to register
- **Advisory-only skills (orphan-by-design)**: `review-domain-currency` is a standalone advisory skill — it is NOT registered with the `/review-claude-config` orchestrator, NOT in the merge-policy registry, NOT a perspective agent. Because this domain-currency skill is not in the orchestrator path, findings cannot be demoted by `scripts/merge_findings.py`; the skill enforces a Low-severity hard-cap programmatically before report write per `skills/review-claude-config/references/merge-rules.md` issue #72 (advisory-only precedent). Reports go under `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/domain-currency-{ts}.md`. The advisory-only pattern is appropriate when a quality dimension is LLM-judged + drift-bounded and would otherwise force edits to the rubric/baseline/merge-rules trio.
- **Review reports**: `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` for timestamped reports organized by target repo, consumed by analytics and apply flows. Slug = `basename(target_dir)`, see `references/repo-identification.md`
- **Self-contained knowledge**: The plugin carries all knowledge needed for quality in its own files. External services (KB server, web research) are optional enhancements — skills degrade gracefully without them. The distillation path is: `research/ → engineering-baseline.md + skill-agent-format-conventions.md → skill decisions`. Research findings must be distilled into these operational surfaces to affect plugin behavior in any repo.
- **Runtime audit layer**: `hooks/` provides observation (PostToolUse, SubagentStart/Stop, SessionEnd) and opt-in policy enforcement (PreToolUse policy gate). Audit traces written to `${HOME}/.claude/plugins/data/claude-config/audit/`. Skills consume these traces for analysis. Per-hook classification + redaction/retention policy: [docs/hook-governance.md](docs/hook-governance.md).
- **Bash helpers**: `bin/` for deterministic Bash helpers ≤30 LOC (e.g., `bin/sync-marketplace-ref.sh`). `scripts/` for Python scripts and ≥100-LOC Bash scripts with pipeline state (e.g., `scripts/issue-state.sh` — legacy position retained). All `bin/*.sh` must pass `shellcheck` (hard-required in `make lint`); install via `brew install shellcheck` (macOS) or `apt install shellcheck` (Linux).
- **Plans/ is gitignored working-output**: the Claude Code Plan tool, `/implement-issue`, and similar planners write to `Plans/`. **GitHub Issues are the single source of truth for status, acceptance criteria, and progress** — never commit `Plans/*.md`. Knowledge-bearing artifacts (audits, spikes, ADRs, roadmaps) live in `docs/{audits,refactors,...}/`. Plan-tool output that contains durable knowledge must be promoted to `docs/` (or extracted into an Issue body) before the session ends. Pre-2026-05-04 commits show 12 Plan files were historically tracked; that pattern was sunset on 2026-05-04 (commits `599c571` + this one).
- **Meta-review threat model**: reviewer-side threats (reading
  malicious skill content, applying poisoned findings, ingesting
  stale evidence) are catalogued in
  [docs/meta-review-threat-model.md](docs/meta-review-threat-model.md).
  Subject-side patterns remain in
  `skills/review-claude-config/references/injection-surface-catalog.md`.

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
- `/refresh-evidence-coverage [dimension|all]` - quartärly (90-day) re-audit of `docs/dimension-evidence-coverage.md`
- `/run-eval-cases [case-number|all]`
- `/validate-primitive-dependencies [folder]`
- `/maintain-evidence-layer [--scope all|labels|freshness|contradictions|tiers]`

### Develop

- `/scaffold-skill [plugin|maintenance|external <target-path>] <name>`
- `/scaffold-mcp-server <server-name>` - scaffold a `.mcp.json` server entry (declaration only, not server code)
- `/scaffold-agent <agent-name>`
- `/scaffold-rule <rule-name>`
- `/develop-hooks [hook-type] <hook-name>`

### Issue Pipeline (user-global skill, not plugin-distributed)

- `/implement-issue <N>` - user-global skill at `~/.claude/skills/implement-issue/`; orchestrates the agent track defined in §Issue Lifecycle (Phases 1–8). Phase 4 dispatches `.claude/agents/builder-implementer.md` in an isolated context; Phase 7.5 dispatches `.claude/agents/builder-evaluator.md` (read-only). State transitions go through `scripts/issue-state.sh`. Available only when invoked from a session with the user's global skill installed

## Issue Tracking

This repo is managed on GitHub at **Nosmoht/review-claude-config**.

### Label Taxonomy

| Prefix | Purpose | Examples |
|--------|---------|---------|
| *(none)* | GitHub defaults | `bug`, `enhancement`, `documentation`, `invalid`, `duplicate`, `wontfix`, `question`, `good first issue`, `help wanted` |
| `priority:` | Urgency (P0=critical → P3=low) | `priority: P0` (#b60205), `priority: P1` (#d93f0b), `priority: P2` (#fbca04), `priority: P3` (#0e8a16) |
| `status:` | Lifecycle state | `status: ready` (#c5def5), `status: in-progress` (#1d76db), `status: needs-review` (#fbca04), `status: in-review` (#5319e7), `status: blocked` (#d93f0b) |
| `category:` | Domain area | `category: infrastructure`, `category: research`, `category: workflow`, `category: automation`, `category: utility-skills`, `category: primitive-coverage`, `category: eval-cases` |

### Issue Lifecycle

Two parallel tracks share the same labels — pick the track based on how the issue is being worked.

**Manual track** (default; maintainer drives the work directly):

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

**Agent track** (`/implement-issue` skill; gated by R1–R5 readiness predicates):

```
OPEN (triaged + acceptance criteria machine-checkable)
  → label: status: ready          (authorizes /implement-issue to claim)
  ↓ scripts/issue-state.sh claim
status: in-progress                (Builder runs)
  ↓ scripts/issue-state.sh handoff
status: needs-review               (Evaluator runs)
  ↓ scripts/issue-state.sh close --pr <ref>
CLOSED                             (only on Evaluator PASS)
  · any failure path: scripts/issue-state.sh block <reason>  → status: blocked
```

The agent track uses `status: needs-review` (machine-set by `scripts/issue-state.sh handoff` for the agent Evaluator gate); the manual track uses `status: in-review` (human peer review). The two are deliberately distinct so manual and agent flows don't collide on the same label.

### Workflow Rules

- **Before starting work**: check open issues to avoid duplicates — `gh issue list --repo Nosmoht/review-claude-config`
- **When a bug/improvement is found**: create issue immediately (`gh issue create` or `mcp__github__issue_write`)
- **When starting manual work on an issue**: set `status: in-progress` via `mcp__github__issue_write` (method: update, labels: ["status: in-progress", ...existing labels])
- **When staging an issue for `/implement-issue`**: triage acceptance criteria to satisfy all five readiness predicates, then add `status: ready`. The skill refuses to claim issues without this label. Manual issues do NOT need `status: ready`. Readiness predicates:
  - **R1 — Testable acceptance criteria**: every criterion is a finite, mechanically checkable assertion (Given-When-Then, exit code, regex, HTTP shape).
  - **R2 — Defined deliverable**: the issue names artifacts that change (file paths, behaviors, outputs) and the shape they should take.
  - **R3 — Single interpretation path**: two competent implementers reading the issue produce the same plan.
  - **R4 — Bounded scope**: the issue states what is in scope and (where relevant) out of scope.
  - **R5 — Necessary** ([ISO/IEC/IEEE 29148:2018 §"Necessary"](https://www.iso.org/obp/ui/#iso:std:iso-iec-ieee:29148:ed-2:v1:en)): every AC mitigates a defect class not already covered. Predicates 1–4 verify form; R5 verifies necessity. Run necessity-check after the form-check (cheap form-check first; necessity-check on parseable ACs). Stakeholder-asserted necessity is not evidence — apply all four sub-heuristics:
    - **Risk-mitigation predicate** — "What concrete defect/regression class would slip through if this AC were deleted? Name it. If 'none' or 'just re-asserts current behavior' → AC fails."
    - **Existing-coverage subtraction** — "Does an existing test/AC already fail when this AC fails? If yes, AC is redundant (Beck *Writable*: cost > value when coverage duplicated)."
    - **Test-the-test inversion** — "Construct an input that violates the spirit but passes this AC, and an input that satisfies the spirit but fails it. Second input existing → AC overfits."
    - **Structure-insensitive (Beck)** — "Snapshot/byte-identical ACs fail Structure-insensitive. Reframe to behavioral assertion."
- **Track-collision rule**: an issue carries either `status: ready` (agent track) OR `status: in-progress` (manual track) — never both. To take a `status: ready` issue manually, first remove `status: ready`, then set `status: in-progress`. The agent track's `scripts/issue-state.sh claim` enforces this by requiring `status: ready` AND no assignee; a manually-claimed issue with `status: ready` left on by accident is rejected, surfacing the collision rather than silently overwriting state. **Self-assigned issues**: a maintainer who self-assigns during triage must unassign before `/implement-issue` (e.g. `gh issue edit <N> --remove-assignee @me`) — otherwise `claim` rejects the no-assignee precondition.
- **When blocked**: replace the active status label with `status: blocked`; document the blocker in an issue comment (the agent track does this via `scripts/issue-state.sh block <N> "<reason>"`)
- **When ready for review** (PR or peer check, manual track): replace with `status: in-review`
- **When closing**: only close when implemented, tested (`make validate`), committed, and docs updated — remove status label, close with state_reason: completed (agent track does this via `scripts/issue-state.sh close <N> --pr <ref>`)

## Working Guidelines

- **Every claim needs a source.** All research files, documentation, and recommendations must link to verifiable sources.
- **Verify claims before acting on them.** Check git history, inspect actual data. Do not redesign a working system based on theoretical concerns.
- **Use the canonical evidence layer for repo-wide claims.** Classify repository-level statements with [evidence-contract.md](skills/review-claude-config/references/evidence-contract.md) and follow [evidence-maintenance.md](docs/evidence-maintenance.md) for maintenance process.
- **Iterate reviews until convergence.** Converged = two consecutive runs on unchanged files produce: (1) **on the deterministic subset** (finding_ids whose `checklist_item` is in the 30 binary items or 15 narrative-parent items enumerated in [merge-rules.md §"Perspective Finding Handling"](skills/review-claude-config/references/merge-rules.md)) — identical set of `finding_id`s at Impact High/Medium; (2) grade variance ≤1 letter in any dimension; (3) no null dimensions where prior run had values. Advisory findings (items outside the deterministic subset) are demoted to Low severity at merge time, surface in the cert for reviewer triage, and do NOT block convergence. Medium and High findings in the deterministic subset block completion.
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

## Hard Constraints

Diff-checkable never-violate rules. The `builder-evaluator` subagent enforces this list as its constraint sweep; humans verify the same rules at PR-merge time.

1. **No hardcoded home-directory prefixes in committed content.** Use `$HOME` or `~`. The user's `block-sensitive-content.sh` PreToolUse hook also blocks Writes that contain such prefixes. Applies to scripts, config (`.mcp.json`, `settings.json`), report frontmatter, plan files, and CLAUDE.md.
2. **No external tracker IDs** in commit messages, PR/issue bodies, code comments, or any committed file (no `NOS-`, `JIRA-`, `LIN-`, etc.). Linear is no longer in use; references are dead pointers.
3. **`make validate` passes** before any commit lands on `main`. Never bypass with `--no-verify`.
4. **Conventional-commit format** for every new commit: `^[a-z]+\([a-z0-9_/-]+\):\s+.+`. Body wraps at 72 chars. Self-contained — no tracker references in the body.
5. **No `--no-verify` / `--no-gpg-sign` markers** in any commit message body or trailer. Commit signing and pre-commit hooks must run.
6. **No mid-session edits to `skills/review-claude-config/references/scoring-rubric.md` or `skills/review-claude-config/references/engineering-baseline.md`.** These are committed BETWEEN sessions only (KV-cache invariant — see §Working Guidelines). Baseline edits go through `/refresh-engineering-baseline`. This rule is enforced by the Builder (knows session state); Evaluator surfaces it as WARNING when these files appear in a diff because session boundaries are not diff-checkable.
7. **No internal IPs / hostnames in public artifacts.** Use placeholders (`<API-VIP>`, `<NODE-IP>`) per `~/.claude/CLAUDE.md §Sensitive Paths Convention`. Public artifacts include GitHub Issues, PR descriptions, and any committed doc. **Sweep status**: HUMAN-ONLY at PR-merge time. The Evaluator does not include this in its automated sweep because a tight RFC1918 regex (`\b(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)[0-9.]+\b`) has unacceptable false-positive rate against version strings, IDs, and timestamps. Reviewer must check manually.

## Development Conventions

- Language: English
- Role statements for agents/skills: use functional form (`You are a <noun-phrase> that <verb-phrase>`); avoid demographic, expert, or narrative persona forms. See [`research/claude-code/skill-agent-format-conventions.md`](research/claude-code/skill-agent-format-conventions.md) §Role Statements for the rule and evidence anchors (arXiv:2603.18507 Sclar PRISM — MMLU −5.3pp from long expert persona length-controlled; arXiv:2311.10054v3 Zheng EMNLP 2024 — 162 personas across 9 OSS models).
- Reference file budgets: see `scripts/validate_token_budgets.py` BUDGETS map (authoritative); default `<=500` tokens, named files have justified higher budgets
- Treat exact thresholds and workflow conventions as `Repo default` unless stronger evidence exists
- Domain cache contains only universal methodology entries (7 total); domain-specific knowledge is researched at runtime. Universal entries follow the repo's 90-day refresh cadence
- `last_refreshed` belongs in YAML frontmatter only — body markers (`**Fetched:**`, `Last reviewed:`) are distinct fields with different meanings and must not be converted; absence of `last_refreshed` causes silent skip by `check-repo-health` (not FAIL)
- Reference files carry `name` + `description` + `last_refreshed`; research files carry `last_refreshed` only — these shapes are intentionally different
- `last_refreshed` is hard-enforced only for `engineering-baseline.md`; `session_check.py` also provides opportunistic freshness warnings for all other `*.md` files in `skills/review-claude-config/references/`, reporting only the single oldest stale file (>90 days)
- WebFetch is optional; skills must degrade gracefully to WebSearch-only when needed
- Baseline updates happen only through `/refresh-engineering-baseline`
- Evidence-coverage matrix re-audited every 90 days via `/refresh-evidence-coverage`; per-dimension `last_audited:` field in `docs/dimension-evidence-coverage.md` is the authoritative timestamp
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
| `validate-descriptions` | `make validate-descriptions` | Run description-graph validator |
- Local-dev venv: `.venv/` at repo root; the Makefile auto-detects `.venv/bin/python` when present and falls back to `python3` (CI path). Recreate via `python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"` if missing or corrupt.
- Domain-cache entries are read-only at runtime; maintainer refresh is hand-edit + commit in source repo (90-day cadence). Runtime researcher findings surface as `### Domain Cache Drift` in the review report — copy into the relevant `references/domain-cache/{key}.md` to refresh.
- Audit-fix chain: commit review report first, then commit fixes
- Review, suggest, and audit skills are read-only on analyzed files except for reports (`${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`)
- Apply skills and `scaffold-skill` modify files and require confirmation gates
- When changing primitive descriptions, run `make validate-descriptions` to verify no description-graph regressions (name collisions, reciprocal-asymmetry breaks, token-grade violations)
- Skills that emit reports use `bash bin/repo-slug.sh "$(pwd)"` to compute `<repo-slug>` deterministically; see `skills/review-claude-config/references/repo-identification.md §Canonical Implementation`

## Research References

The full JIT-loadable research index lives in [docs/research-references.md](docs/research-references.md). Load that file when your task touches one of the topic clusters below; do **not** preload it speculatively.

| Cluster | Load when… |
|---|---|
| Operational (evidence contract, baseline, report contract, source quality, evidence maintenance) | Writing/parsing review reports, classifying evidence labels, running web research |
| Format & Scaffolding | Scaffolding skills/agents/plugins, reviewing frontmatter, naming new commands |
| Prompt & Context Engineering | Reviewing PE/CE dimensions, designing context loading, tuning constraint density |
| Tool Design & Safety | Reviewing Safety dimension, evaluating tool grants, designing hooks/audit, injection or memory analysis |
| Goal Alignment & Failure Modes | Reviewing GA dimension, designing GA-* rubric items, evaluating success criteria |
| Agent Skills & Quality | Reviewing Metadata dimension, auditing description disambiguation, designing review workflows |
| Repo Analysis & Audit | Running `/audit-repo`, `/suggest-skills`, deriving primitives, planning audit phases |
| Review Convergence & Evaluation Quality | Modifying rubric/baseline, calibrating checklists, implementing finding tracking, designing fix verification |
| Primitive Coverage | Reviewing `.mcp.json` or `settings.json` configs |
| Supporting Research | Designing knowledge persistence, choosing fetch tools, evaluating sources, picking long-running runtimes |

## Change Discipline

Change Discipline Rule ([docs/change-discipline-rule.md](docs/change-discipline-rule.md)) — mandatory plan→review→implement→review→commit; **subagent must receive plan+CLAUDE.md+research+target files+checklist** before any plan approval. Zero Medium findings before commit. Applies to all changes: skills, agents, rules, code, docs.

**No plan without multi-perspective review.** Before calling ExitPlanMode, launch 2–3 Plan agents with different review perspectives (risk/regression, convention compliance, dependency correctness). Only truly trivial single-file changes (typo, rename) skip this step. LLM self-review catches <44% of its own errors — subagent review is mandatory.

## Research Backlog

[Research Backlog](docs/research-backlog.md) — 6 deep research topics for review suite quality gaps (autonomous reliability, dependency integrity, instruction following at scale, tool least-privilege, low-evidence baseline refresh, agent definition quality benchmarks).

## Manual Regression Cases

Use [Review Eval Cases](docs/review-eval-cases.md) after changing the rubric, baseline, review prompts, analytics conventions, or scaffold workflow.
