# Legacy FAIL Triage — Round 3 (2026-04-30)

Continuation of `Plans/legacy-fail-triage-2026-04-30.md` (Round 1) and
`Plans/legacy-fail-triage-round-2-2026-04-30.md` (Round 2). This round
triages the next 5 highest-FAIL untriaged items after Bundle 1 + 2
landed (commit `0aad9d9`, suite at 171 FAILs).

## Method

Identical to Round 1/2: per item sample 3 random FAIL paths
(`random.seed(42)`), dump `evaluate()` reasons, inspect cited lines,
classify A/B/C.

## Findings

### SP-4b (14 fails) — VERDICT: A (over-strict)

Sampled `run-eval-cases`, `audit-context-budget`, `apply-audit-findings`.

| Path | Unconstrained Tier-A tools | Class |
|---|---|---|
| `run-eval-cases` | Write, Agent, Bash | **A** — Bash scoped to per-case `case.execution.dispatch`; Agent dispatched with explicit `subagent_type`; Write only emits per-case evaluation report |
| `audit-context-budget` | Write, Agent | **A** — Write only to `$CLAUDE_PLUGIN_DATA/reports/...`; Agent dispatched for sub-investigations with fixed `subagent_type` |
| `apply-audit-findings` | Write, Bash | **A** — Write creates new files only after per-recommendation `AskUserQuestion`; Bash narrowed to `realpath`/`git log` |

**Root cause:** identical to SP-2b (Round 2 #106). `SP_4B_CONSTRAINT`
(`scripts/rubric_binary_evaluator.py:188`) enumerates `restricted|
limited|scoped|allowlist(ed)|confined|must not` followed by `path|
directory|folder|command|script|subagent_type|url|domain|allowlist`.
Misses the dominant binding mechanisms in this repo:

1. Per-call `AskUserQuestion` confirmation gates
2. `subagent_type` binding (already in regex, but only when paired with
   `restricted|limited|scoped`-style verbs — not as standalone clause)
3. Narrative scope clauses (`The only file this skill writes is at <path>`)
4. Per-case dispatch allowlists in YAML config (`case.execution.dispatch`)
5. Bash command allowlists (`ALLOWED commands: find, ls, wc, ...`)

**Recommendation:** Apply the same pattern extension developed for SP-2b
(#106) symmetrically to SP-4b. Refactor `SP_2B_BINDING` and
`SP_4B_CONSTRAINT` into a shared base regex with per-item suffix
constraints, since the binding-vocabulary is identical.

Estimated 65% of SP-4b FAILs flip to PASS after refinement (≈9 of 14).
Residual ~5 are genuine B-defects requiring per-tool binding clauses
(deferred to #90 backlog, paired with SP-2b residuals).

### CE-X (11 fails) — VERDICT: A + C (over-strict + missing NA)

Sampled `review-claude-md`, `review-agent`, `scaffold-mcp-server`.

| Path | Trigger | Class |
|---|---|---|
| `review-claude-md` (line 167) | "Quote or summarize the exact text that caused the issue" | **A** — `summarize` is an instruction to the OUTPUT (reviewer summarizing evidence), not skill-side conversation summarization |
| `review-agent` (line 142) | same `Quote or summarize ...` idiom | **A** — output instruction, not summarization of context |
| `scaffold-mcp-server` (line 110) | "The entry rendered (compact JSON)" | **C** — `compact` is a JSON-formatting noun, not context-compaction |

**Root cause:** `CE_X_TRIGGER` regex
(`rubric_binary_evaluator.py:139`) matches `summariz(e|ation)` and
`compact(ion)?` regardless of context. The CE-X concern is model
context-window summarization that loses information; output-side
summarization (writing a brief evidence quote) and JSON-formatting
language (compact JSON) are unrelated.

**Recommendation:** narrow `CE_X_TRIGGER` to require either:
1. Co-occurrence with `conversation history|context window|prior turns|
   compaction event` AND a summarization verb, OR
2. Bare `summariz*` only when NOT preceded by `quote\s+or` /
   `briefly|concise|short` (output-instruction context)

Add NA-condition: when `compact` is followed by `JSON|format|entry|
output|response|representation`, treat as formatting-noun and skip.

Estimated 75% of CE-X FAILs flip to PASS or NA (≈8 of 11).

### RL-4b (8 fails) — VERDICT: A (over-strict)

Sampled `audit-trust-chain`, `review-mcp-server`, `audit-mcp-auth`.

| Path | Reason | Class |
|---|---|---|
| `audit-trust-chain` | no HITL/partial/escalate path | **A** — read-only audit producing report; no mutating action requires HITL |
| `review-mcp-server` | same | **A** — read-only review producing report |
| `audit-mcp-auth` | same | **A** — one-time keychain bug detector; no mutation, no need for HITL |

**Root cause:** `check_RL_4b` requires `AskUserQuestion`, `status:
partial`, or an `escalate-heading` for every body classified as
agentic. But `is_agentic` is a coarse classifier (any `for each` /
`Agent` tool / etc. triggers it). Read-only audit/review skills are
agentic-by-classification but produce only reports — they have no
mutating action that needs HITL gating.

The MAST-F12 motivation (autonomous unsafe action) does not apply
when the body cannot mutate user state.

**Recommendation:** Add NA-condition to `check_RL_4b`: when the body
contains no Tier-A mutating tool path (`Write` only to
`$CLAUDE_PLUGIN_DATA/...`, no `Edit`/`Bash`-with-mutating-commands/
`Agent`-with-mutating-`subagent_type`), NA the trigger. Read-only
audit/review skills do not need HITL.

Implementation note: this NA-logic overlaps with the IJ-1b
internal-report-path detection from #107. Worth refactoring into a
shared `_writes_only_to_internal_reports` helper.

Estimated 70% of RL-4b FAILs flip to NA (≈6 of 8).

### COMP-Z (7 fails) — VERDICT: B + C (mixed: 2 genuine + 5 missing NA)

Sampled `scaffold-skill`, `validate-primitive-dependencies`, `scaffold-rule`.

| Path | Reason | Class |
|---|---|---|
| `scaffold-skill` | no evidence/citation/quote/verified against | **C** — scaffolds are creators, not reviewers; COMP-Z does not apply |
| `validate-primitive-dependencies` | same | **C** — validation/check skill, not graded review |
| `scaffold-rule` | same | **C** — scaffold |

Looking at the remaining 4 FAILs (`audit-policy-compliance`,
`check-repo-health`, `review-analytics`, `scaffold-mcp-server`):
`audit-policy-compliance` and `review-analytics` are in the
COMP-X review allowlist (true review-class skills) — for these,
missing evidence-citation IS a genuine B-defect. `check-repo-health`
and `scaffold-mcp-server` are non-review-class → C.

**Root cause:** `check_COMP_Z` applies to all skills uniformly. Scaffolds
and one-time validators have no findings to cite — the rubric item
applies only to skills that emit graded findings.

**Recommendation:** Add NA-condition to `check_COMP_Z`: NA when skill
name is NOT in `COMP_X_REVIEW_ALLOWLIST` (mirror the allowlist
introduced in #102). Makes COMP-Z and COMP-X scope-symmetric.

Estimated 5 of 7 FAILs flip to NA after refinement; 2 remain as
genuine B-defects in allowlisted skills (deferred to #90).

### RL-3b (7 fails) — VERDICT: A (over-strict)

Sampled `audit-mcp-auth`, `scaffold-agent`, `run-eval-cases`.

| Path | Trigger | Class |
|---|---|---|
| `audit-mcp-auth` (line 40) | "do not retry" | **A** — negated trigger |
| `scaffold-agent` (line 101) | option label `"Adjust"` | **A** — `Adjust` is option-label noun, not retry semantics |
| `run-eval-cases` (line 54/159) | "Do not retry" | **A** — negated trigger (×2) |

**Root cause:** `RL_3B_RETRY` regex (`rubric_binary_evaluator.py:235`)
matches `(retry|regenerate|redisplay|ask\s+again|adjust)` without
context-awareness:
1. Negated triggers (`do not retry`, `never retry`) — same issue as
   CLAR-3 (#105) and COMP-W (#103)
2. `Adjust` is too generic — frequently appears as option label
   (`"Adjust"`, `"Adjust X to Y"`) without retry semantics
3. Quoted-string contexts (option labels in backticks)

**Recommendation:**
1. Apply the `\b(not|never|don'?t|do\s+not)\s+\w*\s*$` negation guard
   used by `check_CLAR_3` and `check_COMP_W` to `check_RL_3b`
2. Drop `adjust` from `RL_3B_RETRY` (too generic; the rubric concern
   is about RETRY loops, not adjustment) OR require `adjust` to be
   followed by a retry-semantic noun (`retry|attempt|iteration|cycle`)
3. Skip matches inside backtick-quoted spans (mirror CLAR-2 #104 fix)

Estimated 80% of RL-3b FAILs flip to NA (≈6 of 7).

## Action Items

| Issue | Type | Effort | Description |
|---|---|---|---|
| New issue (P2) | Rubric refinement | 1 session | SP-4b — apply SP-2b (#106) binding-pattern extension symmetrically |
| New issue (P2) | Rubric refinement | 1 session | CE-X — narrow trigger to true context-summarization; NA `compact JSON`; skip output-instruction `quote or summarize` |
| New issue (P2) | Rubric refinement | 1 session | RL-4b — NA when skill writes only to internal report paths (no mutation surface); shares helper with #107 |
| New issue (P2) | Rubric refinement | 1 session | COMP-Z — NA when skill name not in `COMP_X_REVIEW_ALLOWLIST` (allowlist symmetry with #102) |
| New issue (P2) | Rubric refinement | 1 session | RL-3b — negation guard + drop `adjust` from trigger + backtick-skip |
| #90 (existing) | Skill defects | 1-2 sessions | SP-4b residual ~5 + COMP-Z residual ~2 + RL-9b residual + SP-2b residual ~7 = ~15 skill-edits |

## Total FAIL Reduction Projection

| Item | Current FAILs | Post-refinement (est.) | Method |
|---|---|---|---|
| SP-4b | 14 | 5 (-65%) | Pattern extension (mirror SP-2b/#106) |
| CE-X | 11 | 3 (-75%) | Trigger narrowing + compact-as-noun NA |
| RL-4b | 8 | 2 (-75%) | Internal-report-path NA |
| COMP-Z | 7 | 2 (-71%) | Allowlist symmetry |
| RL-3b | 7 | 1 (-86%) | Negation guard + adjust drop |
| **Subtotal** | **47** | **13** | **-72%** |

## Combined Round 1 + 2 + 3 Outlook

| Source | Current FAILs | Projected post-refinement |
|---|---|---|
| Round 1 — already shipped (#102, #103, #104, #105, #108) | 89 | 21 |
| Round 2 — partial shipped (#106, #107 deferred) | 93 | 23 (assuming #106/#107 ship) |
| Round 3 — this report | 47 | 13 |
| **Subtotal (13 items triaged across 3 rounds)** | **229** | **57** |
| Untriaged remainder (META-3b, CLAR-1, CLAR-4, RD-5b, COMP-Y, PE-2, AH-2b) | 23 | (small — likely <10 FAILs each, mostly minor or skill-defect) |
| **Total** | **252** | **~67-77** |

After all triaged refinements ship: ~70 FAILs across the suite, mostly
genuine B-defects deferred to #90 skill-content backlog.

## Next Step

Commit this triage report. Open the 5 rubric-refinement issues. The
~15 skill-edit defects across all 3 rounds form the consolidated #90
backlog: a separate Skill-Content-Sweep across ~3-5 sessions in a later
phase.

Per CLAUDE.md L156 cache-freeze, none of the Round 3 refinements edit
`scoring-rubric.md` or `engineering-baseline.md`. All refinements are
Python-evaluator pattern/NA-logic edits, identical mechanism to
Bundle 1 (commit 9b6af91) and Bundle 2 (commit 0aad9d9).
