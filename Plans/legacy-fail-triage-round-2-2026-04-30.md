# Legacy FAIL Triage — Round 2 (2026-04-30)

Continuation of `Plans/legacy-fail-triage-2026-04-30.md` (Round 1: COMP-X,
COMP-W, RL-9b). This round triages the next 5 highest-FAIL items.

## Method

Identical to Round 1: per item sample 3 random FAIL paths, dump
`evaluate()` reasons, inspect cited lines, classify the verdict as:

- **A: Rubric over-strict** — false positive; pattern matches valid forms
- **B: Real defect** — skill genuinely lacks the required predicate
- **C: NA-condition missing** — trigger fires on construct that should be exempt

`random.seed(42)` for reproducibility.

## Findings

### CLAR-2 (13 fails) — VERDICT: A (over-strict)

Sampled `scaffold-skill`, `apply-audit-findings`, `apply-agent-review-findings`.

| Path | Match | Class |
|---|---|---|
| `scaffold-skill` (line 23) | "use it" in `If the first token is plugin or maintenance, use it as the mode` | **A** — antecedent is "first token" |
| `apply-audit-findings` (line 23) | "use it" in `If $ARGUMENTS contains a file path, use it` | **A** — antecedent is "file path" |
| `apply-agent-review-findings` (line 45) | "use it" in `If $ARGUMENTS contains a file path, use it` | **A** — antecedent is "file path" |

**Root cause:** `BARE_PRONOUN_VERB` regex (`scripts/rubric_patterns.py:56`)
is purely lexical — it does not detect locally-bound antecedents. The
`if X, use it` construct is an idiomatic conditional with `it` resolving
unambiguously to `X` in the same sentence.

**Recommendation:** narrow CLAR-2 trigger to exclude matches where:
1. The pronoun appears within the same sentence as a noun-phrase antecedent
   ending in `, ` (`if X, use it`, `Otherwise, use it`)
2. The match is in a quoted code/option-label string

Estimated 80% of CLAR-2 FAILs flip to PASS after refinement.

### CLAR-3 (15 fails) — VERDICT: A + C (over-strict + missing NA)

Sampled `scaffold-agent`, `develop-hooks`, `audit-trust-chain`.

| Path | Trigger / Context | Class |
|---|---|---|
| `scaffold-agent` (line 142) | "refuse and ask for a different name" | **A** — recovery IS the trigger ("refuse and ask") |
| `develop-hooks` (line 82) | "Timeout — command handlers default to 600 seconds" | **C** — `Timeout` is a config noun, not a control-flow trigger |
| `audit-trust-chain` (line 74) | "Grep fails → abort with error" | **A** — `abort with error` is itself the terminal recovery action |

**Root cause:** `CLAR_3_RECOVERY` regex enumerates a closed set of recovery
patterns but misses three idioms:
1. `refuse and ask for X` — interactive recovery (rejection + re-prompt)
2. `abort with error` — terminal action that both fires and resolves
3. Negation contexts — `not abort` / `do not refuse` get matched as
   triggers despite the negation
4. Documentation contexts — `Timeout` as a noun describing a config
   default, not a runtime branch

**Recommendation:**
1. Add to `CLAR_3_RECOVERY`: `refuse(\s+\w+)?\s+(and|then)\s+(ask|prompt|request)`
   and `abort\s+with\s+(error|message|<exit\s+code\s+\d+>)`
2. Add NA-condition: when `Timeout` appears in a heading or bullet-list
   item describing a configuration field (not in an `if X → Y` clause),
   treat as NA
3. Add negation guard: skip triggers preceded by `not\s+`, `never\s+`,
   `do\s+not\s+`

Estimated 60% of CLAR-3 FAILs flip to PASS, 20% to NA after refinement.

### SP-2b (21 fails) — VERDICT: A (over-strict) + B (some genuine)

Sampled `audit-repo`, `apply-skill-review-findings`, `apply-rule-review-findings`.

| Path | Unbound | Class |
|---|---|---|
| `audit-repo` | Agent, Write, WebFetch | **A** — Agent is dispatched only via `subagent_type=Plan` for review (binding by construction); Write goes only to report path (line 421); WebFetch is optional (line 429) |
| `apply-skill-review-findings` | Edit, Bash | **A** — Edit is gated by per-recommendation `AskUserQuestion` confirmation (line 194); Bash usage is restricted to `realpath` and `git log` (lines 62, 259) |
| `apply-rule-review-findings` | Edit, Bash | **A** — same per-rec confirmation gate (line 185) and narrow Bash use |

**Root cause:** `SP_2B_BINDING` regex (`rubric_binary_evaluator.py:176`)
enumerates a closed set of lexical binding patterns (`restricted to`,
`allowlisted`, `limited to`, `scoped to`, `policy-gate`, etc.) but misses
the dominant binding mechanisms in this repo's apply-* and audit skills:

1. **Per-call confirmation gates** — `AskUserQuestion` directly preceding
   the tool call is a binding constraint (the user authorizes each
   invocation). The regex captures `Read-only` but not this idiom.
2. **Narrative scope clauses** — `The only file this skill writes is the
   audit report at <path>` binds Write to a single path. Pattern misses
   the `only … is … at <path>` construction.
3. **Subagent_type binding** — Agent dispatch with a fixed `subagent_type`
   is a binding (the type allowlist is enforced by Claude Code).

**Recommendation:** extend `SP_2B_BINDING` with:
- `(only\s+(used\s+for|file\s+\w+\s+writes|invoked|dispatched))`
- `(per[-_\s](recommendation|finding|item)\s+(confirmation|approval))`
- `(subagent_type\s*[:=]\s*['"]?\w+['"]?)`
- `(after\s+(AskUserQuestion|confirm|approval))`
- `optional\s+\(\s*degrade\s+gracefully\s+\)`

Some genuine B cases likely remain (skills with Write/Edit and no
confirmation gate). Estimated 65% of SP-2b FAILs flip to PASS, 35%
remain genuine defects requiring per-tool binding clauses.

### IJ-1b (19 fails) — VERDICT: A + C (over-strict + missing NA)

Sampled `review-settings`, `apply-review-findings`, `review-claude-md`.

| Path | Missing | Class |
|---|---|---|
| `review-settings` | validation-predicate + write-gate | **C** — Write target is internal report path (`$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/...`), not user-controlled; should NA the trigger |
| `apply-review-findings` | validation-predicate | **A** — has `AskUserQuestion` write-gate (lines 100, 140, 215) and sidecar schema validation (line 49); validation regex doesn't recognize "conforms to schema" |
| `review-claude-md` | validation-predicate | **A** — line 19 "Validate the file exists" is real validation but regex requires `validate ... format/regex/pattern` — existence check is not recognized |

**Root cause:** `IJ_1B_VALIDATION` regex requires `validate|matches|
conforms ... $ARGUMENTS|repo-slug|path|url|input|argument` — too narrow.
Does not recognize:
1. **Existence checks** — `validate the file exists` is the dominant form
2. **Schema-conformance** — `sidecar conforms to <schema>.json` (when
   schema is referenced separately from `$ARGUMENTS`)
3. **Implicit type-narrowing via Glob** — `Glob "*.md"` constrains the
   set even without an explicit validate clause

Additionally, the trigger fires on review skills whose only Write target
is an internal report path (not user-derived). For these, IJ-1b should
NA on the basis that the Write payload is not derived from `$ARGUMENTS`
in any unsafe way.

**Recommendation:**
1. Extend `IJ_1B_VALIDATION` to recognize:
   - `validate\s+(the\s+)?(file|path|input)\s+exists`
   - `(sidecar|payload|file)\s+conforms\s+to\s+\S+\.(schema|json)`
   - `Glob\s+[`'"][^`'"]+[`'"]` followed by per-match selection
2. Add NA-condition: if the only Write target in the body is
   `$CLAUDE_PLUGIN_DATA/reports/...` or `$CLAUDE_PLUGIN_DATA/audit/...`
   and the Write payload does not interpolate `$ARGUMENTS` raw, NA the
   trigger

Estimated 50% of IJ-1b FAILs flip to PASS, 30% to NA after refinement.

### RL-1b (25 fails) — VERDICT: A (over-strict)

Sampled `apply-audit-findings`, `apply-agent-review-findings`,
`apply-review-findings`.

| Path | Reason | Class |
|---|---|---|
| `apply-audit-findings` | "no numeric or enum termination predicate" | **A** — iterates `For each intervention` (line 89) over finite intervention matrix from a parsed report |
| `apply-agent-review-findings` | same | **A** — `For each mapped recommendation` (line 96), `For each recommendation (High first, then Medium)` (line 164), `For each modified file` (line 237) — all bounded by parsed-report sizes |
| `apply-review-findings` | same | **A** — `For each mapped recommendation` (line 80), `For each type group` (line 161) — bounded by report sections |

**Root cause:** `RL_1B_NUMERIC` / `RL_1B_MAX_KEY` / `RL_1B_STATUS`
require explicit numeric caps or enum status fields, but bounded
list-iteration over a finite parsed-report set provides termination by
construction. This is the same pattern Round 1 found in COMP-W.

**Recommendation:** mirror the Round-1 COMP-W refinement: add NA-condition
that triggers when iteration source is bounded. Specifically NA RL-1b
when:
1. Body contains `For each <X>` and `<X>` was previously sourced from
   a deterministic finite reader (`Glob`, parsed JSON sidecar, parsed
   Markdown table, frontmatter list)
2. Body has no explicit `while`, `until`, `loop until`, `keep <verb>`,
   `repeatedly`, or unbounded recursion

Estimated 75% of RL-1b FAILs flip to NA after refinement.

## Action Items

| Issue | Type | Effort | Description |
|---|---|---|---|
| New issue (P2) | Rubric refinement | 1 session | CLAR-2 antecedent-aware narrowing — exclude `if X, ... use it` constructs |
| New issue (P2) | Rubric refinement | 1 session | CLAR-3 — extend recovery patterns (`refuse and ask`, `abort with error`), add negation guard, NA Timeout-as-config-noun |
| New issue (P2) | Rubric refinement | 1 session | SP-2b — extend binding patterns (`AskUserQuestion`-gated, `subagent_type`-bound, `only ... at <path>`) |
| New issue (P2) | Rubric refinement | 1 session | IJ-1b — recognize existence checks, schema-conformance, Glob-bounded inputs; NA when Write target is internal report path |
| New issue (P2) | Rubric refinement | 1 session | RL-1b — NA when iteration source is bounded (mirror Round-1 COMP-W refinement) |
| #90 (existing) | Skill defects | 1 session | SP-2b residual ~7 genuine defects requiring per-tool binding clauses |

## Total FAIL Reduction Projection

| Item | Current FAILs | Post-refinement (est.) | Method |
|---|---|---|---|
| CLAR-2 | 13 | 3 (-77%) | Antecedent-aware narrowing |
| CLAR-3 | 15 | 3 (-80%) | Pattern + NA extension |
| SP-2b | 21 | 7 (-67%) | Binding-pattern extension; ~7 genuine remain |
| IJ-1b | 19 | 4 (-79%) | Validation-pattern + report-path NA |
| RL-1b | 25 | 6 (-76%) | Bounded-iteration NA |
| **Subtotal** | **93** | **23** | **-75%** |

## Combined Round 1 + Round 2 Outlook

| Source | Current FAILs | Projected post-refinement |
|---|---|---|
| Round 1 (COMP-X, COMP-W, RL-9b) | 89 | 24 |
| Round 2 (CLAR-2, CLAR-3, SP-2b, IJ-1b, RL-1b) | 93 | 23 |
| **Subtotal (8 items)** | **182** | **47** |
| Untriaged remainder | 70 | (pending Round 3) |
| **Total** | **252** | **117 + Round 3** |

## Next Step

Commit this triage report. Open the 5 rubric-refinement issues (one per
item). Skill-edit batch (SP-2b residual + RL-9b residual from Round 1) is
the existing #90 backlog. Remaining 70 FAILs across CLAR-1/CLAR-4/META-3b/
CE-X/COMP-Y/COMP-Z/PE-2/SP-4b/RL-3b/RL-4b/AH-2b/RD-5b need their own
sample-triage in a future Round 3 session.

Per CLAUDE.md L156, rubric refinements are between-session edits to
`scoring-rubric.md` (cache-prefix freeze). The 5 new issues track the
refinement work; no rubric edits in this session.
