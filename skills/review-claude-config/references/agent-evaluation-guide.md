---
name: agent-evaluation-guide
description: Type-specific evaluation criteria for Claude Code agents (single-file .md in agents/ directory)
last_refreshed: 2026-04-19
---

# Agent Evaluation Checklist

> **Dim-Mapping authority**: the per-item `Dim` column below remains the
> human-readable specification; the **machine-readable agent-item dim pins**
> live in `scoring-rubric.md §Agent Items` (single source of truth, consumed
> by `merge_findings.py:get_item_dim()`). Any change to a `Dim` value here
> requires a synchronous edit to `scoring-rubric.md §Agent Items` and a
> regenerate of `merge-policy.yaml`.

Answer EVERY item: PASS | FAIL | NA. No skipping. FAILs map to Dim for scoring.

The 15-field 2026 frontmatter catalog (`name`, `description`, `model`, `color`,
`tools`, `disallowedTools`, `maxTurns`, `background`, `isolation`, `memory`,
`initialPrompt`, `mcpServers`, `skills`, `hooks`, `permissionMode`, `effort`)
is the authoritative source — see
`research/claude-code/skill-agent-format-conventions.md` §"Agent Frontmatter
2026 Catalog" for field semantics, the 6-mode `permissionMode` hierarchy, and
the `effort` Opus 4.7 compatibility table. If the parent guide overflows
1,800 tok, Opus-4.7 specifics are extracted to
`opus-4.7-migration-checks.md` (loaded JIT when `model: opus-4-7` detected).

| ID | Check | Dim |
|----|-------|-----|
| MS-1 | Model matches task complexity — no over/under-provisioning (haiku=routing, sonnet=analysis, opus=complex reasoning)? Opus 4.7 reserved for `effort: xhigh|max` workloads. | Meta |
| DA-1 | Description has specific trigger keywords — not generic? | Meta |
| DA-2a | Description contains ≥1 discriminating keyword not in unrelated requests? | CE |
| DA-2b | Description covers all documented example triggers? | CE |
| DA-4 | `<example>` blocks present when trigger conditions are non-obvious? | Compl |
| DA-5 | Body instructions do not redefine or contradict the description's trigger logic? | Meta |
| TC-1 | `<example>` blocks cover all primary use cases? | Compl |
| TC-2 | Negative examples present (when NOT to trigger)? | Compl |
| TC-3 | Agent includes verification criteria or success conditions for its primary output? | Compl |
| AH-2b | Missing-arg trigger paired with PASS-response (default value OR prompt-and-stop) within 200 chars? (binary check — see scoring-rubric.md) | Compl |
| TV-1 | Tool array matches tools actually referenced in the body? | Meta |
| TV-2 | No unused tools — tool set matches task archetype per `tool-grant-decision-tree.md` (least-privilege)? | Safety |
| SP-2b | Per-tool archetype binding (body OR Hard Rules OR referenced policy) for each `tools` entry? (binary check — see scoring-rubric.md) | Safety |
| TV-3 | High-risk tool combinations (Tier A/B) or `mcpServers`/`skills` surface expansions justified if present? (Plugin agents cannot use `mcpServers`.) | Safety |
| SP-4b | For Tier-A combinations: ≥1 constraint sentence per Tier-A tool (location-agnostic)? (binary check — see scoring-rubric.md) | Safety |
| TV-4 | `disallowedTools` (denylist) does not overlap with `tools` (allowlist) — denylist is subtractive from inherited tools, not from explicit allowlist? [If `disallowedTools` present] | Meta |
| TV-5 | Declared `skills` exist as resolvable skill names (cross-primitive integrity); not inherited from parent — explicit redeclaration required? [If `skills` present] | Meta |
| TV-6 | Declared `hooks` reference valid event names from the 26-event catalog (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `Stop`, etc.); event-to-CLI-version compatible with target runtime? [If `hooks` present] | Meta |
| SF-1 | All context self-contained — no external files assumed? | CE |
| SF-2 | Long body uses headings for structure (not dense prose)? | Clarity |
| AP-2 | No tools copied from another agent without pruning unused ones? | Safety |
| AP-3 | `disable-model-invocation: true` present if user-only invocation is appropriate? | Meta |
| AP-4 | Non-guardrail sections use MUST/CRITICAL ≤3 times total? | PE |
| RL-1 | Termination conditions defined (step limit, timeout, success criteria, or bounded retry/backoff; `maxTurns` frontmatter satisfies this)? | Safety |
| RL-1b | Numeric/enum termination predicate matches one of the RL-1b regex variants? [Agentic only] | Safety |
| RL-2 | Failure paths specified, not just happy path? | Compl |
| RL-3b | Every retry/regenerate/redisplay/adjust has a numeric cap within 400 chars? [Agentic only] | Safety |
| RL-4 | Escalation / HITL trigger defined for high-autonomy operations? | Safety |
| RL-4b | ≥1 literal HITL / `status: partial` / `escalate` token present on autonomy paths? [Agentic only] | Safety |
| RL-5 | State validation or checkpointing for multi-step workflows? | Compl |
| RL-6 | Verification step before declaring success? | Compl |
| RL-7 | Reasoning-action consistency enforced in workflow? | Clarity |
| RL-8 | Role/scope boundaries explicitly stated? | Safety |
| RL-9 | Safety/PII/credential scope constraints present? | Safety |
| RL-9b | ≥1 credential-scope rule matches redact/truncate/skip/token-like regex? [Agentic only] | Safety |
| RL-10 | Observability hooks or logging specified? | Compl |
| RT-4 | Subagent failure propagated — parent defines behavior when child fails/times out, not just retry? [Agentic only] | Compl |
| RT-5 | Numeric cap stated for ≥1 context-consuming operation (files read, search results, output size)? [Multi-step only] | CE |
| IJ-1 | External input (Web/MCP) + write tool without sanitization boundary? | Safety |
| IJ-1b | Validation regex/allowlist AND write-gate (AskUserQuestion/preview/confirm before Write/Edit) both present? | Safety |
| IJ-2 | initialPrompt forwards raw user input without scope constraint? | Safety |
| GV-1 | Delegation depth limit stated? [Delegating] | Safety |
| GV-2 | Scope boundary (CWD or tool restriction) stated? [Delegating] | Safety |

**Severity guidance:** Broken tool grants or cross-primitive dependencies (missing referenced tools, dangling agent/skill references) are **High** severity findings.

## Agent Frontmatter (AF)

Each AF item is NA unless its trigger field is present.

| ID | Check | Dim | Trigger |
|----|-------|-----|---------|
| AF-1 | `background`/`isolation` match autonomy level — background agents need `isolation: worktree` or explicit scope constraints? | Safety | `background` or `isolation` |
| AF-2 | `memory` scope (`user`/`project`/`local`) proportional to task? | CE | `memory` |
| AF-3 | `initialPrompt` structured (goal, constraints, references) — not raw user forwarding? | PE | `initialPrompt` |
| AF-4 | `maxTurns` set when agent does multi-step work (>3 expected tool calls) — runaway prevention? Verify integer >0 and ≤200 (sanity ceiling). | Safety | `maxTurns` or multi-step body |
| AF-5 | `permissionMode` value ∈ {`default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`}. `bypassPermissions` justified inline (downgrade rationale + scope). Parent-overrides-child rule respected — child cannot escalate beyond parent. | Safety | `permissionMode` |
| AF-6 | `effort` value ∈ {`low`, `medium`, `high`, `xhigh`, `max`}. `xhigh`/`max` requires `model: opus` or `claude-opus-4-7` (xhigh+max are Opus-4.7-only). | Meta | `effort` |
| AF-7 | `model` override matches workload — no `inherit` for agents with safety-critical or long-horizon work; full model ID (`claude-opus-4-7`) preferred over `opus` alias when version pinning matters. | Meta | `model` |

## Opus 4.7 Sampling-Param Migration (SAMP)

Opus 4.7 (released 2026-04-16) removed `temperature`, `top_p`, `top_k` sampling
parameters. Agents carrying these references either fail review (PE-body) or
400-error at runtime (Metadata frontmatter override block).

| ID | Check | Dim | Verification |
|----|-------|-----|--------------|
| SAMP-1 | Body contains no hardcoded `temperature`/`top_p`/`top_k` references (case-insensitive). | PE | Regex `/\b(temperature\|top_p\|top_k)\s*[:=]/i` returns no match in body. **FAIL → PE capped at Grade C.** |
| SAMP-2 | Frontmatter override block is free of removed sampling params. | Meta | Same regex on YAML frontmatter. **FAIL → hard F on Metadata** (runtime 400-error on Opus 4.7). |

**Finding identity:** Every FAIL must produce a recommendation with `ID: {item}:{path}:{dim}/v1` in the heading.
