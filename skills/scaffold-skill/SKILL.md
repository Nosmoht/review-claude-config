---
name: scaffold-skill
description: >
  Creates a research-optimized skill: SKILL.md, optional references/, and doc registration.
  Use when adding a new skill to this repository or to an external repo (external mode).
  Do NOT use to create agents or rules — use /scaffold-agent or /scaffold-rule.
argument-hint: "[plugin|maintenance|external <target-path>] <skill-name>"
allowed-tools: Read, Write, Edit, Glob, WebSearch, WebFetch
disable-model-invocation: true
---

# Skill Scaffolding

You are a skill builder creating research-optimized Claude Code skills. Your job is to generate valid, high-quality skill files that follow project conventions, quality patterns, and the skill format specification. Stop immediately if the target directory does not exist or the skill name conflicts with an existing skill.

## Workflow

### 1. Parse mode and validate skill name

Parse `$ARGUMENTS` as `[mode] <skill-name>`.

**Mode detection:**
- If the first token is `plugin` or `maintenance`, use it as the mode. The rest is `<skill-name>`.
- If the first token is `external`, the second token is `<target-path>` and the third is `<skill-name>`.
  - `<target-path>` is required in external mode — do not fall back to cwd.
  - Validate: path exists (`Glob "<target-path>"`) and contains `.git/` (`Glob "<target-path>/.git"`). If either check fails, report the error and stop.
- Otherwise, default to `plugin` and treat the full argument as `<skill-name>`.
- If `<skill-name>` is empty after parsing, ask the user for it.

**Name validation:**
- Must be kebab-case (lowercase, hyphens only). This is a repo naming convention for CLI usability, not a scientific claim.
- Must not conflict with an existing skill. Glob both `skills/*/SKILL.md` and `.claude/skills/*/SKILL.md` to check (for external mode, also check `<target-path>/.claude/skills/*/SKILL.md`).

If validation fails, report the issue and ask for a corrected input.

### 2. Load template and quality references

Read `references/skill-template.md` for the default SKILL.md structure.

Read `references/quality-patterns.md` for research-backed generation directives. Apply these throughout Steps 3–4.

Optionally, if the file exists, read `research/claude-code/skill-agent-format-conventions.md` (Glob for `**/research/claude-code/skill-agent-format-conventions.md`) for valid frontmatter fields. If not found, use template defaults.

### 2.5. Domain context gathering

**Determine mode applicability:**
- Mode `plugin` or `maintenance`: domain is Claude Code skill management — skip domain research, inject the standard plugin domain rule ("This skill operates within Claude Code's skill/hook/agent/rule primitives") into Step 4.
- Mode `external`: always run the full domain context gathering below.

**Stage 1 — Discover domain (if user did not specify):**

If the user provided explicit domain information in their request (e.g., "Go MCP server", "Python FastAPI"), use it directly. Otherwise:
- Glob `<target-path>/*` to list top-level files.
- Read up to 8 files in priority order: CLAUDE.md or AGENTS.md (if present), primary manifest file (go.mod, package.json, pyproject.toml, Cargo.toml, pom.xml, build.gradle — whichever exists), one source file, one test file.
- Synthesize: primary language, framework, domain, testing conventions.

**Stage 2 — Research:**

Check KB (if `mcp__kb-server__authenticate` is available): run `kb.answer` on the identified domain for any cached findings.

Probe web tool availability: attempt a trivial WebSearch (e.g., `"site:anthropic.com"`). If it fails, set `websearch_available=false` — skip web research and note the gap in Stage 3. If WebSearch is available, run targeted web research:
1. Decompose into 3–5 sub-questions: language patterns, framework conventions, testing, security/safety, build/CI.
2. For each sub-question: run 1–2 WebSearch queries (one keyword-precise, one conceptual).
3. After snippet evaluation, WebFetch only 1–2 highest-signal URLs per sub-question (Tier 1/2 sources preferred: official docs, arXiv, engineering blogs with benchmarks).
4. Adaptive stopping: if 2 consecutive sub-questions yield no new domain-specific rules, stop.
5. Maximum 3 reflection cycles, 5–8 WebFetch total.

Goal: extract 3–5 domain-specific rules that go beyond what is already present in the target repo.

**Stage 3 — Synthesize and confirm:**

Summarize findings as a compact domain briefing:
- Primary language + framework
- 3–5 domain-specific rules (cite source tier)
- Any security or safety patterns specific to the domain

Present the domain briefing and confirm via AskUserQuestion (header: "Domain context"):
- Option 1 label: "Looks good — proceed" (Recommended) — description: `"Use this domain context for skill generation"`
- Option 2 label: "Add/correct something" — description: `"Provide corrections or additions before continuing"`

On "Add/correct something": incorporate the user's input into the domain briefing, then proceed. On "Looks good": proceed to Step 3.

### 3. Gather requirements

#### 3a. Core questions via AskUserQuestion menus

Using the skill name, target repo, and domain context from Step 2.5, generate **contextual options** for each question. Present all questions via `AskUserQuestion` with selectable options — no free text required. The "Other" option is always available for custom input. Include a `preview` field on description options to show the full proposed text.

**Question 1 — Description** (header: "Description")

Generate 2–3 description drafts based on the skill name + domain context. Apply quality-patterns.md Activation directive to each draft: verb-first, user-task terms, ≥1 trigger phrase, ≥1 counter-case. (META-1a, CLAR-2, CLAR-3)

Option generation heuristics:
- Skill name contains a known verb (review, scaffold, lint, code, test, apply, validate) → generate specific, domain-targeted drafts
- Skill name is abstract (manager, helper, util) → generate broader drafts
- Domain context from Step 2.5 is rich (manifest + source files read) → include framework-specific details in drafts
- Domain context is thin (language only) → keep drafts generic

Example for `go-coder` in a Go MCP server repo:
- Option 1 label: "Generate and refactor Go code" — preview: `"Generates, refactors, and fixes Go code following project conventions and idiomatic Go patterns. Use when writing new MCP handlers, fixing bugs, or refactoring existing code. Do NOT use for non-Go files, infrastructure config, or documentation-only changes."`
- Option 2 label: "Generate Go code with tests" — preview: `"Generates and tests Go code following project conventions. Use when implementing features, writing tests, or fixing bugs. Do NOT use for CI/CD config, documentation, or non-Go files."`

**Question 2 — Reference files** (header: "References")

Generate 2–3 options based on domain context + skill type.

Option generation heuristics:
- Coder/scaffolder skill → suggest conventions or patterns reference
- Reviewer/validator skill → suggest rubric or criteria reference
- Domain context has strong framework signal → name the reference after the framework

Example for `go-coder`:
- Option 1 label: "go-conventions.md" — description: `"Project-specific Go patterns: error handling, naming, MCP handler structure"`
- Option 2 label: "No reference files" — description: `"Skill works directly from CLAUDE.md and codebase"`

Bundle questions 1 and 2 in a single AskUserQuestion call (max 4 questions per call).

**Question 3 — Workflow overview** (header: "Workflow") — conditional

Only ask this if the description answer contains fewer than 3 distinct action verbs with clear sequencing. Generate 2 workflow skeletons as options with `preview`.

Example for a coder skill:
- Option 1 label: "Standard (3 steps)" — preview: `"1. Analyze context and requirements\n2. Implement/refactor code\n3. Verify and suggest tests"`
- Option 2 label: "Extended (5 steps)" — preview: `"1. Analyze context\n2. Research patterns\n3. Implement\n4. Write tests\n5. Review and verify"`

Tool constraint: AskUserQuestion allows max 4 questions per call and max 4 options per question. Use a second call for Question 3 only when the conditional triggers.

#### 3b. Proposed spec (auto-derived)

After the user answers 3a, derive all remaining parameters and present them as a compact table for confirmation.

**Derivation heuristics:**

| Parameter | Heuristic |
|-----------|-----------|
| **Allowed tools** | Verb analysis on description: "review/evaluate/check" → Read, Glob; "create/scaffold/generate" → Read, Write, Edit, Glob; "fix/apply/update" → Read, Edit, Glob; "research/search/fetch" → +WebSearch, WebFetch. Default floor: Read, Glob. Each tool must correspond to a named workflow step — derive tools and workflow steps together, never tools alone. |
| **disable-model-invocation** | `true` if Write, Edit, or Bash is in the tool set (100% consistent pattern in this repo); omit otherwise |
| **Argument hint** | Pattern match on skill name: review-X → `<file-path>`, scaffold-X → `<name>`, apply-X → `<report-path>`; otherwise infer from the primary noun in the description or omit |
| **Workflow skeleton** | From description + skill type: input-validate → discover/gather → analyze/process → output/report → next-steps (3–6 steps). Refine using workflow answer from 3a if provided. |
| **Registration** | External mode: skip (already handled in Step 6). Plugin/maintenance: derive a one-sentence summary from the description. |
| **Reasoning / CoT step** | Yes if the workflow includes an "analyze", "diagnose", "evaluate", or "compare" step; no otherwise |
| **Compaction checkpoint** | Add if (workflow step count × 2.5) > 10; omit otherwise |

Present the derived spec as a table, then confirm via AskUserQuestion:
- Option 1 label: "Looks good — generate" (Recommended) — description: `"Accept all derived values and generate SKILL.md"`
- Option 2 label: "Adjust tools" — description: `"Correct the tool set, keep everything else"`
- Option 3 label: "Adjust workflow" — description: `"Correct workflow steps, keep everything else"`

On Option 2, 3, or Other: incorporate the correction, redisplay the updated table, confirm again. When confirmed, proceed to Step 4.

### 4. Generate SKILL.md

Apply all directives from `references/quality-patterns.md` during generation.

**Frontmatter:**
- `name`, `description`, `allowed-tools`, `argument-hint`, `disable-model-invocation` from user answers and auto-derived spec.
- Description: verb-first, user-task terms, ≥1 trigger phrase, ≥1 counter-case.

**Body structure (follow Context Layout directive from quality-patterns.md):**
- **START**: Role statement (functional, no persona-stacking) + stop conditions
- **Workflow**: numbered steps with explicit conditionals; if reasoning was requested, include a CoT analysis step
- **END**: Hard Rules section

**Role statement:** Functional description — "You are a [role] that [purpose]." No demographic or expert personas.

**Hard Rules:**
- 5–7 unconditional statements.
- Include ≥1 stop condition and ≥1 failure path.
- If write-capable: add confirmation gate before destructive actions.
- Include domain-specific constraint if domain was identified in Step 2.5.

**Output contract:** If the skill produces a structured report, state verdict/summary first, then detail. State the output shape explicitly in the role statement or workflow preamble.

**Domain rules:** If domain was confirmed in Step 2.5, inject 2–3 domain-specific rules into workflow steps or hard rules.

**Compaction:** If user answered >10 expected turns in Q9, add a compaction step: "After Step N, summarize key decisions and failures to file before continuing."

**Example generated output:**

    ---
    name: lint-configs
    description: >
      Validates and fixes linting configuration files across the repository.
      Use when adding or updating ESLint, Prettier, or similar tool configs.
      Do NOT use for application code lint errors — use /review-skill instead.
    argument-hint: "[config-path]"
    allowed-tools: Read, Glob
    ---

    # Lint Configs

    You are a configuration validator that checks linting setup for correctness and project consistency. Stop if no config files are found.

    ## Workflow

    ### 1. Discover config files
    [step placeholder]

    ## Hard Rules

    - Never modify application source files.
    - Report missing configs as findings, not errors.

Present the full generated content to the user for review via AskUserQuestion (header: "Preview"):
- Option 1 label: "Correct — write files" (Recommended) — description: `"Accept the generated SKILL.md and write all files"`
- Option 2 label: "Adjust" — description: `"Describe what to change; skill will regenerate and preview again"`
- Option 3 label: "Cancel" — description: `"Stop without writing anything"`

On "Adjust": ask what to change (free text via Other or follow-up), regenerate, and present the preview again. On "Cancel": stop and notify the user. On "Correct": proceed to Step 5.

### 5. Write files

**Determine write path:**
- `plugin` mode: `skills/<skill-name>/SKILL.md`
- `maintenance` mode: `.claude/skills/<skill-name>/SKILL.md`
- `external` mode: `<target-path>/.claude/skills/<skill-name>/SKILL.md` — create the `.claude/skills/` directory tree if it does not exist.

Write the SKILL.md at the determined path.

If reference files were specified, create the `references/` directory under the skill path and write each reference file with frontmatter stubs:
```yaml
---
name: <reference-name>
description: <purpose from user input>
last_refreshed: <today's date in YYYY-MM-DD format>
---

## Overview

<Describe the purpose and scope of this reference. One or two sentences.>

## Key Points

- <Key point 1>
- <Key point 2>
```

If any write fails, report which files were successfully created and which failed. Do not proceed to Step 6 until all files are written.

### 6. Register in repository docs

**External mode: skip registration entirely.** Show this note:
> External-repo mode: registration skipped. Register manually in your project's CLAUDE.md (under `## Commands`) if applicable.

Then proceed directly to Step 7.

**Plugin mode:**
- Update `README.md` under `## Command Families`
- Update `CLAUDE.md` under `## Commands`
- Update `docs/skills/README.md` under `## Quick Reference` and, if needed, `## By Function`
- If the new skill changes workflow composition or the compact mode/research comparison, also update `## Workflow Chains` or `## Mode and Research Summary`

**Maintenance mode:**
- Update `CLAUDE.md` under `## Commands`
- Update `docs/skills/README.md` under `## Quick Reference` and `## By Function` when the new skill belongs in the maintained component inventory
- If the new skill changes workflow composition or the compact mode/research comparison, also update `## Workflow Chains` or `## Mode and Research Summary`

Use Edit to make targeted additions. Never rewrite unrelated sections or depend on prose outside those headings.

### 7. Verify outputs and suggest commit

Verify all outputs before reporting success (COMP-Y, COMP-X):
- Check that SKILL.md exists at the expected path and is non-empty.
- If reference files were requested, confirm each `references/*.md` file was written.
- If registration was performed, confirm the target `README.md` / `CLAUDE.md` lines were appended.
- Assert no step was silently skipped — if any check fails, report which file is missing and stop.

Skill is complete when all files are verified present and no step reported an error. (COMP-X)

Tell the user:
```
Skill scaffolded. Suggested commit:
  feat(<skill-name>): add <skill-name> skill with <brief capability>
```

Then present next steps via AskUserQuestion (header: "Next steps"):
- Option 1 label: "Review the new skill" — description: `"Runs /review-skill <absolute-path>. Note: review-skill works cross-repo — run from a review-claude-config session for full reference access."`
- Option 2 label: "Scaffold another skill" — description: `"Starts /scaffold-skill again"`
- Option 3 label: "Done" — description: `"End the workflow"`

On Option 1: invoke `/review-skill` with the absolute path to the new SKILL.md. On Option 2: ask for the skill name and mode, then invoke `/scaffold-skill`. On Option 3: acknowledge and stop.

## Quality measurement (mandatory before Step 7 success report)

Without verification, this skill fails at **convention/idiomatic drift** (F3) and **path-placement errors** (F5). One concrete example: a scaffolder invoked with `maintenance` mode but writing to `skills/<name>/SKILL.md` (plugin path) — schema-valid, frontmatter-valid, lint-clean, yet structurally wrong. The repo's authoritative validators (`make validate`) catch schema/budget/lint defects (F1, F2, F4) but cannot detect mode-vs-path mismatch or sibling-shape drift. The three-layer pipeline below binds `make validate` to a sibling-comparison critic and a 6-dimension binary rubric so a SCAFFOLD operation reports success only when every layer agrees.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024).

After Step 5 writes files and before Step 7 reports success, record the artifact set and mode for the verification layers:

```bash
TMPDIR=$(mktemp -d -t scaffold-skill-XXXX)
PROMISED="$TMPDIR/promised.txt"   # one absolute path per line
MODE_FILE="$TMPDIR/mode.txt"      # exactly one of: plugin | maintenance | external
# Write every artifact path emitted by Step 5/6 to $PROMISED (SKILL.md, references/*.md, doc-registration files).
# Write the parsed mode token from Step 1 to $MODE_FILE.
```

### Layer A — mechanical invariants (deterministic, fail-fast)

Run all five metrics. Any `STRICT` non-zero exit → abort and report; `SOFT` deltas → log and surface, do not auto-overwrite.

**A.1 STRICT — every promised artifact exists and is non-empty.**

```bash
fail=0
while IFS= read -r p; do
  if [ ! -s "$p" ]; then
    echo "STRICT FAIL existence $p (missing or empty)"
    fail=$((fail+1))
  fi
done < "$PROMISED"
```

**A.2 STRICT — `make validate` exits 0.** This runs the full chain: ruff lint, ruff format, JSON Schema (covers F1, F2), token budget (covers F4), description-graph regression, pytest.

```bash
( cd "$REPO_ROOT" && make validate ) > "$TMPDIR/make-validate.log" 2>&1
mv_exit=$?
[ $mv_exit -ne 0 ] && { echo "STRICT FAIL make-validate exit=$mv_exit"; fail=$((fail+1)); }
```

Additionally grep the new SKILL.md for the scaffolder's own Hard-Rule predicates:

- COMP-X (success condition): body matches `complete when|success when|done when`.
- COMP-Y (verification predicate in Hard Rules): Hard Rules section contains `verify|validate|check|assert`.
- Reference-file token-budget note: each `references/*.md` body matches `Keep under 500 tokens`.

Any missing predicate → STRICT FAIL.

**A.3 STRICT — sensitive-content sweep on every newly-written artifact.** Source the home-path regex set from `hooks/block-sensitive-content.sh` at runtime (do NOT duplicate literals here). Sweep each promised artifact for: (a) the home-path patterns loaded from the hook, (b) literal RFC1918 IPs (`\b(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)[0-9.]+\b`), (c) literal credential-looking values in any `.mcp.json` env (covers F7).

**A.4 STRICT — path-placement matches mode classification.** Read `$MODE_FILE`, then assert every artifact path matches the mode-appropriate regex:

```
mode=plugin       → ^skills/[a-z][a-z0-9-]*/SKILL\.md$
mode=maintenance  → ^\.claude/skills/[a-z][a-z0-9-]*/SKILL\.md$
mode=external     → ^<target>/\.claude/skills/[a-z][a-z0-9-]*/SKILL\.md$
```

Mismatch → STRICT FAIL (covers F5).

**A.5 SOFT — doc-registration count.** In `plugin` / `maintenance` modes, expect ≥1 doc-registration edit (`README.md`, `CLAUDE.md`, or `docs/skills/README.md`). In `external` mode, registration is skipped by design — exempt from this metric.

What each metric catches:

| Metric | Catches |
|---|---|
| A.1 file-existence | F1, F6 |
| A.2 `make validate` + predicate grep | F1, F2, F4 |
| A.3 content-sweep | F7 |
| A.4 mode-vs-path regex | F5 |
| A.5 registration-count | F6 (soft) |

### Layer B — adversarial critic dispatch (sibling-comparison, blind)

Pick a sibling: most-recently-edited SKILL.md in the **same mode tree** as the candidate (plugin sibling for plugin candidate, maintenance sibling for maintenance candidate). Exclude `references/skill-template.md` and the candidate itself. For plugin mode use `ls -t skills/*/SKILL.md | head -2 | tail -1` (the second-most-recent — the candidate is the most recent).

Dispatch a fresh subagent with the candidate (A) and sibling (B). Then dispatch a second time with order swapped — position bias is the dominant LLM-judge artifact (Shi et al. 2024 arXiv:2406.07791). Take the **union** of items flagged across both runs.

```
Agent({
  description: "Adversarial scaffold-skill critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer of two Claude Code SKILL.md files. " +
    "Neither label tells you which is the freshly-scaffolded candidate. " +
    "Compare A and B for structural and conventional fit. List every: " +
    "(1) top-level structural element (frontmatter field, heading) present " +
    "in EXACTLY ONE file; (2) convention divergence — naming style, " +
    "enforcement-verb usage (MUST/NEVER vs always/never), role-statement " +
    "form (functional 'You are a X that Y' vs persona/expert form), " +
    "section ordering; (3) required-element omission — name/description " +
    "frontmatter, role statement, Workflow section, Hard Rules. " +
    "For each item: quote the literal token/heading, name which file " +
    "(A or B), and classify as MISSING / EXTRA / RENAMED / NOVEL_SHAPE. " +
    "Do not rate quality. Do not praise clarity. Report under 500 words. " +
    "A:\n<paste candidate SKILL.md>\n\nB:\n<paste sibling SKILL.md>"
})
```

Vocabulary the critic produces:

- `MISSING` — element in sibling but not candidate (maps to F2, F6).
- `EXTRA` — element in candidate but not sibling (maps to F3 — may be legitimate).
- `RENAMED` — semantic match under different identifier (maps to F3).
- `NOVEL_SHAPE` — structurally unprecedented for the SKILL.md class (maps to F3 — strongest idiomaticity signal).

Skill-specific binary checks the critic must report:

- Role statement matches functional form `^You are a .* that .*` — flag persona/expert/credential form as NOVEL_SHAPE.
- Frontmatter uses ONLY documented keys (`name`, `description`, `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `context`, `agent`) — any extra key is MISSING (from convention) → F2.

### Layer C — 6-dimension binary rubric (CheckEval-style)

Bind Layer A failures and Layer B findings to a yes/no rubric. CheckEval (arXiv:2403.18771) reports +0.45 inter-evaluator agreement for binary vs. Likert. Any `NO` blocks the success report.

```
D1 VALIDATION_PASS    `make validate` exits 0 with the scaffolded artifacts
                      on disk AND the COMP-X / COMP-Y / token-budget-note
                      predicate greps all pass. STRICT-tied to Layer A.2.
                      Catches F1, F2, F4. Load-bearing for SCAFFOLD.
D2 FRONTMATTER_VALID  SKILL.md frontmatter has non-empty kebab-case `name`
                      and non-empty `description`; only documented keys
                      appear (allowlist above). Catches F2.
D3 PATH_CORRECT       Candidate path matches the regex set for the declared
                      mode token in $MODE_FILE (Layer A.4). Mode-aware:
                      plugin → skills/, maintenance → .claude/skills/,
                      external → <target>/.claude/skills/. Catches F5.
D4 IDIOMATIC_FIT      Zero NOVEL_SHAPE findings from Layer B union; ≤2
                      RENAMED findings (RENAMED is judgment-call, hard
                      cap 2); role statement uses functional form.
                      Catches F3. Load-bearing for SCAFFOLD.
D5 COMPLETENESS       Every path in $PROMISED exists, non-empty. For
                      plugin/maintenance modes, ≥1 doc-registration edit
                      verified; external mode exempts D5 from the
                      registration count. Catches F6.
D6 NO_LEAKAGE         Zero matches for the hook-sourced home-path
                      patterns, zero RFC1918 IPs, zero literal-secret
                      patterns in any written file (Layer A.3). Catches F7.
```

Map Layer A failures → D1, D2, D3, D5, D6. Map Layer B `MISSING` → D2/D5. Map `EXTRA`/`RENAMED`/`NOVEL_SHAPE` → D4.

### Reconciliation outcomes

- **All STRICT pass + zero `MISSING`/`NOVEL_SHAPE` from critic + all D1–D6 = yes** → SCAFFOLD reported successful; proceed to Step 7 commit-suggestion + next-step menu.
- **Any STRICT fail OR any `MISSING`/`NOVEL_SHAPE` OR any D1–D6 = no** → restore inline. For frontmatter/path/leakage issues the fix is mechanical (regenerate with the missing field, move the file, redact). Max **2 iterations**, then surface to the user with the exact failing dimension + the candidate-vs-sibling diff. Do NOT silently overwrite or hide the failure. The 2-iteration cap mirrors `rules/agentic-workflow.md §"Loop-on-symptom — stop after three"` — by iteration 3 the frame is wrong, not the artifact.
- **Only SOFT warnings (e.g. A.5 registration-skip outside external mode, ≤2 `RENAMED` from Layer B)** → report in the Step 7 success notice but proceed. The Step 4 AskUserQuestion preview gate is the final human-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Semantic-wrong description with valid form.** A SKILL.md whose `description` is schema-valid and verb-first but describes the wrong skill (user asked for an MCP-server reviewer; scaffolder emitted a generic file-reviewer description). D1, D2, D4 all pass. Only the Step 4 human preview gate catches.
2. **Tool-grant overreach.** The scaffolded SKILL.md declares `allowed-tools: Read, Write, Edit, Bash, WebFetch` when the workflow only needs `Read, Glob`. Schema-valid, idiomatic against siblings declaring similar sets, Layer B sees no novelty. Detected only by a least-privilege audit in `/review-skill` — out of scope for SCAFFOLD verification.
3. **Description-graph reciprocal-asymmetry below threshold.** `make validate-descriptions` flags only past calibrated thresholds. A description that nudges a sibling skill's clarity score downward by a small margin passes here and still degrades corpus disambiguation. Detected only by `/review-claude-config` running the full multi-perspective rubric.
4. **Documentation-registration silent mismatch.** The Step 6 Edit succeeds and line count grows, but the new entry lands under the wrong heading or contradicts the SKILL.md description. A.5 counts edits, not semantic-fit.
5. **Future-template drift.** This skill reads `references/skill-template.md` — if the template falls out of sync with `engineering-baseline.md` or the schema, the scaffolder faithfully emits drifted content. Detected only by the 90-day baseline-refresh cadence.

The Step 7 success notice MUST list which residual classes apply to passages the critic flagged as MISSING/EXTRA without resolution, so the operator has one last human-glance opportunity before the suggested commit lands.

## Hard Rules

- **Tier A tool justification**: Write/Edit + WebFetch/WebSearch combination — WebFetch/WebSearch are read-only domain research inputs; fetched content flows through the Step 4 human preview gate before any file is written. No fetched content is written directly to disk without user approval. (Tier A mitigated by HITL gate; tool-grant-decision-tree.md Tier A)
- **Never overwrite existing skills.** If a skill directory already exists with the given name, refuse and ask for a different name.
- **Preview before writing.** Always show the full generated SKILL.md content before creating any files.
- **Frontmatter must be valid.** Only use fields documented in the skill format conventions: `name`, `description`, `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `context`, `agent`.
- **Documentation edits are additive.** Append concise entries under stable headings only. Never modify or remove unrelated entries.
- **Reference files have token budgets.** Add "Keep under 500 tokens" as a note in each reference file stub.
- **Kebab-case names only.** Reject names that are not valid kebab-case. This is a repo convention, not a scientific claim.
- **External mode: never register.** Skip Steps 6 registration entirely; show the manual registration note instead.
- **Verify outputs before reporting success (COMP-Y, COMP-X).** After writing files, assert each expected artifact exists and is non-empty. Check that registration targets were updated. Report any missing files explicitly — do not silently skip failed writes.
- **Generated SKILL.md must include a success condition (COMP-X).** The final workflow step must contain "complete when", "success when", or "done when". Omitting the success condition produces a rubric FAIL.
- **Generated SKILL.md must include a verification predicate (COMP-Y).** Hard Rules must contain at least one binary check ("verify", "validate", "check", or "assert"). Holistic "looks good" language is a rubric FAIL.
