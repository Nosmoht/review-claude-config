---
name: scaffold-agent
description: >
  Creates a Claude Code agent with valid frontmatter and numbered workflow
  body. Use when adding a subagent to any project's .claude/agents/. Do NOT
  use for skills or rules — use /scaffold-skill or /scaffold-rule.
argument-hint: "<agent-name>"
allowed-tools: Read, Write, Edit, Glob
disable-model-invocation: true
---

# Agent Scaffolding

You are an agent builder creating correctly structured Claude Code agent files. Your job is to generate valid agent .md files that follow the project's format specification and register them in the relevant documentation. Naming guidance here is a repo convention for consistency, not a claim of universal naming science.

## Workflow

### 1. Validate agent name

Parse `$ARGUMENTS` as `<agent-name>`.

- If the argument is empty, ask the user for the agent name.

Validate:
- Name must be kebab-case (lowercase, hyphens only, no spaces or underscores). This is a repo naming convention for CLI and filesystem usability.
- Name must not exceed 64 characters.
- Name must not contain `anthropic` or `claude` as a substring.
- Name must not conflict with an existing agent. Glob `.claude/agents/*.md` and `**/.claude/agents/*.md` to check.

If validation fails, report the specific issue and ask for a corrected name. Stop and wait — do not continue until a valid name is provided.

### 2. Load template and conventions

Read `references/agent-template.md` for the canonical agent .md structure and model selection guidance.

If the file cannot be read (missing or unreadable), stop and report:
"agent-template.md not found — cannot scaffold without format conventions. Verify the file exists at skills/scaffold-agent/references/agent-template.md."

Optionally, if the file exists, read `research/claude-code/skill-agent-format-conventions.md` (Glob for `**/research/claude-code/skill-agent-format-conventions.md`) for additional valid frontmatter fields. If not found, use the template defaults.

### 3. Gather requirements

Ask the user for the following. Collect all answers before proceeding:

1. **Description** — What does the agent do? When should it trigger? (required, max 1024 chars; the description becomes the frontmatter `description` field and guides activation)
2. **Example blocks** — Provide 1-2 activation examples showing the context, user message, and assistant response? (recommended for precise trigger targeting; format is shown in the template)
3. **Model** — haiku / sonnet / opus. Default: sonnet. See the template for when-to-use guidance.
4. **Color** — Optional visual indicator (e.g., `blue`, `green`, `purple`). Skip if not needed.
5. **Tools / allowed-tools** — Which tools does the agent need? Apply least-privilege: list only the tools the agent's workflow actually requires.
6. **Workflow complexity** — How many steps? Brief description of each step. (used to generate numbered workflow stubs in the body)

If any required field is missing after asking, prompt again. Do not generate the agent .md with empty required fields.

### 4. Generate and validate agent .md

Build the content from `references/agent-template.md`:

- **Frontmatter:** `name`, `description` (with any `<example>` blocks embedded), `model`, and optionally `color` and `tools`/`allowed-tools`.
- **Body heading:** `# <Agent Name>` (title-cased version of the name).
- **Role statement:** One sentence: "You are a [functional role] that [purpose]."
- **Workflow section:** Numbered steps based on the user's workflow description. Each step gets a heading and a 1-2 sentence placeholder — enough to show structure.
- **Hard Rules section:** Standard constraints appropriate to the agent's write-capability and scope.

Example generated output:

    ---
    name: pr-reviewer
    description: >
      Review pull request diffs for correctness, style, and test coverage.
      Use when a user asks to review a PR or check code quality before merging.
    model: sonnet
    tools:
      - Read
      - Glob
    ---

    # PR Reviewer

    You are a code review agent that inspects pull request diffs and reports findings
    grouped by severity.

    ## Workflow

    ### 1. Fetch PR diff
    [step placeholder]

    ## Hard Rules

    - Never approve or merge PRs; analysis only.

Before presenting, run these validation checks against the generated content:
- Name length ≤ 64 characters (count characters in the `name` field)
- Description length ≤ 1024 characters (count characters in the full `description` value, excluding YAML key and quotes)
- No XML tags (`<`, `>`) appear in the description field (XML tags are not allowed in description)
- Only documented frontmatter keys are present: `name`, `description`, `model`, `color`, `tools`, `allowed-tools`

If any check fails, report the specific violation and correct it before presenting.

Present the full generated content to the user for review. Confirm via AskUserQuestion (header: "Agent preview"):
- Option 1 label: "Correct — write file" (Recommended) — description: `"Write the agent to .claude/agents/<agent-name>.md"`
- Option 2 label: "Adjust" — description: `"Describe what to change; will regenerate and show again"`
- Option 3 label: "Cancel" — description: `"Stop without writing anything"`

On "Adjust": ask what to change, regenerate, and preview again. On "Cancel": stop without writing anything.

### 5. Write file

Write the agent file:

1. Check whether `.claude/agents/` exists. If not, create it by writing the file — the Write tool will create intermediate directories.
2. Write `.claude/agents/<agent-name>.md` with the approved content.

If the write fails, report the error clearly. Do not proceed to Step 6 until the file is written successfully.

### 6. Register in repository docs

Use only the stable surviving headings. Do not invent new top-level sections.

- Update `README.md` under `## Command Families` if the agent is user-invocable.
- Update `CLAUDE.md` under `## Commands`.
- Update `docs/skills/README.md` under `## Quick Reference` and `## By Function` when applicable.

Use Edit to make targeted additions. Never rewrite unrelated sections or depend on prose outside those headings. If a heading does not exist in the target file, skip that registration step and note it in your report.

### 7. Verify outputs and suggest commit

Verify all outputs before reporting success (COMP-Y, COMP-X):
- Check that the agent file exists at `.claude/agents/<agent-name>.md` and is non-empty (0 missing files).
- If registration was performed, confirm the target `README.md` / `CLAUDE.md` lines were appended.
- Assert no step was silently skipped — if the file is missing, report the error and stop.

Agent scaffolding is complete when the file exists and all registrations are confirmed. (COMP-X)

Tell the user:
```
Agent scaffolded. Suggested commit:
  feat(<agent-name>): add <agent-name> agent
```

Then present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Review the new agent" (Recommended) — description: `"Run /review-agent <agent-path> to validate quality"`
- Option 2 label: "Scaffold another agent" — description: `"Provide an agent name to scaffold another"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Review the new agent": invoke `/review-agent` with the new agent's path. On "Scaffold another agent": ask for the agent name, then invoke `/scaffold-agent`. On "Done": acknowledge and stop.

## Quality measurement (mandatory before Step 7 success report)

Without verification, this skill fails at **frontmatter incompleteness or invalid keys** (F2) and **convention/idiomatic drift** (F3). One concrete example: a scaffolded agent that renders `agent_name:` (snake_case) instead of `name:`, or declares an undocumented top-level frontmatter key — schema-valid prose, lint-clean body, yet structurally invalid for the dispatch layer that reads only the YAML head. The repo's authoritative validators (`make validate`) catch schema/budget/lint defects (F1, F2 partial, F4) but cannot detect XML tags inside `description:`, mode-vs-path mismatch, or sibling-shape drift. The three-layer pipeline below binds `make validate` to a sibling-comparison critic and a 6-dimension binary rubric so a SCAFFOLD operation reports success only when every layer agrees.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024).

After Step 5 writes the file and before Step 7 reports success, record the artifact set for the verification layers:

```bash
TMPDIR=$(mktemp -d -t scaffold-agent-XXXX)
PROMISED="$TMPDIR/promised.txt"   # one absolute path per line
# Write every artifact path emitted by Step 5/6 to $PROMISED:
#   <repo-root>/.claude/agents/<agent-name>.md  (always)
#   <repo-root>/README.md                       (if Step 6 registration touched it)
#   <repo-root>/CLAUDE.md                       (if Step 6 registration touched it)
#   <repo-root>/docs/skills/README.md           (if Step 6 registration touched it)
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

Additionally grep the new agent .md for the scaffolder's own validation predicates:

- Name length: the `name:` value MUST be ≤64 characters AND match `^[a-z][a-z0-9-]*$` (kebab-case, leading letter).
- Forbidden substring: `name:` MUST NOT contain `anthropic` or `claude`.
- Description length: the full `description:` value (excluding YAML key and quotes) MUST be ≤1024 characters.
- XML-tag ban: the `description:` value MUST NOT contain literal `<` or `>` characters that open a tag (XML tags are not allowed in `description:` per the scaffolder's own validation rule; `<example>` blocks belong inside the description as quoted YAML, never as raw XML at the YAML-key level).
- Frontmatter key allowlist: the top-level frontmatter MUST contain ONLY keys from `{name, description, model, color, tools, allowed-tools}`. Any other top-level key is a STRICT FAIL.

Any predicate violation → STRICT FAIL.

**A.3 STRICT — sensitive-content sweep on every newly-written artifact.** Source the home-path regex set from `hooks/block-sensitive-content.sh` at runtime (do NOT duplicate literals here). Sweep each promised artifact for: (a) the home-path patterns loaded from the hook, (b) literal RFC1918 IPs (`\b(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)[0-9.]+\b`), (c) literal credential-looking values (covers F7).

**A.4 STRICT — path-placement matches the agent class.** Assert the candidate file path matches:

```
^\.claude/agents/[a-z][a-z0-9-]*\.md$
```

Mismatch → STRICT FAIL (covers F5). The path is class-fixed (no mode parameter), so this is a single regex rather than mode-aware.

**A.5 SOFT — doc-registration count.** Expect ≥1 doc-registration edit across `README.md`, `CLAUDE.md`, and `docs/skills/README.md`. Step 6 explicitly allows skipping a registration when the target heading does not exist — surface as a warning, not a fail.

What each metric catches:

| Metric | Catches |
|---|---|
| A.1 file-existence | F1, F6 |
| A.2 `make validate` + predicate grep | F1, F2, F4 |
| A.3 content-sweep | F7 |
| A.4 path regex | F5 |
| A.5 registration-count | F6 (soft) |

### Layer B — adversarial critic dispatch (sibling-comparison, blind)

Pick a sibling: most-recently-edited `.claude/agents/*.md` (excluding the candidate and `references/agent-template.md`). Use `ls -t .claude/agents/*.md | grep -v "/<agent-name>.md$" | head -1`. If no sibling exists in the current repo, fall back to a recently-edited agent from `$HOME/workspace/claude-config/agents/`.

Dispatch a fresh subagent with the candidate (A) and sibling (B). Then dispatch a second time with order swapped — position bias is the dominant LLM-judge artifact (Shi et al. 2024 arXiv:2406.07791). Take the **union** of items flagged across both runs.

```
Agent({
  description: "Adversarial scaffold-agent critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer of two Claude Code agent .md files. " +
    "Neither label tells you which is the freshly-scaffolded candidate. " +
    "Compare A and B for structural and conventional fit. List every: " +
    "(1) top-level structural element (frontmatter field, heading) present " +
    "in EXACTLY ONE file; (2) convention divergence — naming style, " +
    "enforcement-verb usage (MUST/NEVER vs always/never), role-statement " +
    "form (functional 'You are a X that Y' vs persona/expert form), " +
    "presence of <example> blocks inside the description field, section " +
    "ordering, Hard Rules count (5-7 expected per quality-patterns.md); " +
    "(3) required-element omission — name/description frontmatter, role " +
    "statement, Workflow section, Hard Rules. " +
    "For each item: quote the literal token/heading, name which file " +
    "(A or B), and classify as MISSING / EXTRA / RENAMED / NOVEL_SHAPE. " +
    "Do not rate quality. Do not praise clarity. Report under 500 words. " +
    "A:\n<paste candidate agent .md>\n\nB:\n<paste sibling agent .md>"
})
```

Vocabulary the critic produces:

- `MISSING` — element in sibling but not candidate (maps to F2, F6).
- `EXTRA` — element in candidate but not sibling (maps to F3 — may be legitimate).
- `RENAMED` — semantic match under different identifier (maps to F3).
- `NOVEL_SHAPE` — structurally unprecedented for the agent .md class (maps to F3 — strongest idiomaticity signal).

Skill-specific binary checks the critic must report:

- Role statement matches functional form `^You are a .* that .*` — flag persona/expert/credential form as NOVEL_SHAPE.
- Frontmatter uses ONLY documented keys (`name`, `description`, `model`, `color`, `tools`, `allowed-tools`) — any extra top-level key is MISSING (from convention) → F2.
- Hard Rules section contains 5-7 bullet entries (per `quality-patterns.md` Constraints) — count outside this band is flagged as EXTRA/MISSING.

### Layer C — 6-dimension binary rubric (CheckEval-style)

Bind Layer A failures and Layer B findings to a yes/no rubric. CheckEval (arXiv:2403.18771) reports +0.45 inter-evaluator agreement for binary vs. Likert. Any `NO` blocks the success report.

```
D1 VALIDATION_PASS    `make validate` exits 0 with the scaffolded agent on
                      disk AND the name-length / kebab-case / forbidden-
                      substring / description-length / XML-tag / frontmatter
                      allowlist predicate greps all pass. STRICT-tied to
                      Layer A.2. Catches F1, F2, F4. Load-bearing for
                      SCAFFOLD.
D2 FRONTMATTER_VALID  Agent .md frontmatter has non-empty kebab-case `name`
                      (≤64 chars, no anthropic/claude substring) and non-
                      empty `description` (≤1024 chars, no literal XML
                      tags); ONLY documented top-level keys appear
                      (allowlist: name, description, model, color, tools,
                      allowed-tools). STRICT-fail if any undocumented key
                      is present. Catches F2.
D3 PATH_CORRECT       Candidate path matches `^\.claude/agents/[a-z][a-z0-9-]*\.md$`
                      (Layer A.4). Path-mode-aware: agents live only at
                      this class-fixed location, never at top-level
                      `agents/` for repo-internal scaffolds. Catches F5.
D4 IDIOMATIC_FIT      Zero NOVEL_SHAPE findings from Layer B union; ≤2
                      RENAMED findings (RENAMED is judgment-call, hard
                      cap 2); role statement uses functional form; Hard
                      Rules count is 5-7. Catches F3. Load-bearing for
                      SCAFFOLD.
D5 COMPLETENESS       Every path in $PROMISED exists, non-empty. ≥1 doc-
                      registration edit verified across README.md /
                      CLAUDE.md / docs/skills/README.md when the target
                      headings exist; SOFT-exempt when all target
                      headings are absent. Catches F6.
D6 NO_LEAKAGE         Zero matches for the hook-sourced home-path
                      patterns, zero RFC1918 IPs, zero literal-secret
                      patterns in any written file (Layer A.3). Catches F7.
```

Map Layer A failures → D1, D2, D3, D5, D6. Map Layer B `MISSING` → D2/D5. Map `EXTRA`/`RENAMED`/`NOVEL_SHAPE` → D4.

### Reconciliation outcomes

- **All STRICT pass + zero `MISSING`/`NOVEL_SHAPE` from critic + all D1–D6 = yes** → SCAFFOLD reported successful; proceed to Step 7 commit-suggestion + next-step menu.
- **Any STRICT fail OR any `MISSING`/`NOVEL_SHAPE` OR any D1–D6 = no** → restore inline. For frontmatter/path/leakage issues the fix is mechanical (regenerate with the missing field, strip the XML tag, move the file, redact). Max **2 iterations**, then surface to the user with the exact failing dimension + the candidate-vs-sibling diff. Do NOT silently overwrite or hide the failure. The 2-iteration cap mirrors `rules/agentic-workflow.md §"Loop-on-symptom — stop after three"` — by iteration 3 the frame is wrong, not the artifact.
- **Only SOFT warnings (e.g. A.5 registration-skip when target headings are absent, ≤2 `RENAMED` from Layer B)** → report in the Step 7 success notice but proceed. The Step 4 AskUserQuestion preview gate is the final human-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Semantic-wrong description with valid form.** An agent whose `description:` is schema-valid, verb-first, and within length budget but describes the wrong agent (user asked for a PR reviewer; scaffolder emitted a description for a generic file reviewer). D1, D2, D4 all pass. Only the Step 4 human preview gate catches.
2. **Tool-grant overreach.** The scaffolded agent declares `tools: [Read, Write, Edit, Bash, WebFetch]` when the workflow only needs `Read, Glob`. Schema-valid, idiomatic against siblings declaring similar sets, Layer B sees no novelty. Detected only by a least-privilege audit in `/review-agent` — out of scope for SCAFFOLD verification.
3. **Description-routing ambiguity below threshold.** `make validate-descriptions` flags only past calibrated thresholds. A description that nudges a sibling agent's dispatch clarity downward by a small margin passes here and still degrades routing disambiguation (per `rules/agent-antipatterns.md §A3 — Description-field is the only routing surface`). Detected only by `/review-claude-config` running the full multi-perspective rubric.
4. **Documentation-registration silent mismatch.** The Step 6 Edit succeeds and line count grows, but the new entry lands under the wrong heading or contradicts the agent .md description. A.5 counts edits, not semantic-fit.
5. **Future-template drift.** This skill reads `references/agent-template.md` — if the template falls out of sync with `engineering-baseline.md` or the schema, the scaffolder faithfully emits drifted content. Detected only by the 90-day baseline-refresh cadence.

The Step 7 success notice MUST list which residual classes apply to passages the critic flagged as MISSING/EXTRA without resolution, so the operator has one last human-glance opportunity before the suggested commit lands.

## Hard Rules

- **Never overwrite existing agents.** If `.claude/agents/<agent-name>.md` already exists, refuse and ask for a different name.
- **Preview before writing.** Show the full generated .md content before creating any file.
- **Frontmatter must be valid.** Only use documented fields: `name`, `description`, `model`, `color`, `tools`, `allowed-tools`. Do not invent new frontmatter keys.
- **Name constraints are enforced before generation.** kebab-case, max 64 chars, no "anthropic"/"claude" substring.
- **Example blocks belong inside the description field, not in the body.**
- **Documentation edits are additive.** Append concise entries under stable headings. Never modify or remove unrelated entries.
- **Least-privilege tools.** Only include tools the agent's workflow actually uses. Keep the list minimal.
- **Stop conditions apply.** Stop immediately if: name is invalid and user does not supply a corrected one, user chooses cancel, or file write fails.
- **Verify outputs before reporting success (COMP-Y, COMP-X).** After writing the agent file, assert it exists and is non-empty. Report any missing file explicitly — do not silently skip a failed write.
- **Generated agent must include a success condition (COMP-X) with numeric predicate (COMP-V).** The final workflow step must contain "complete when", "done when", or "success when" plus a verifiable component (digit count, "frontmatter", exit code, or tool binding). Omitting either is a rubric FAIL.
- **Generated agent must include HITL escalation (RL-4b) and termination ceiling (RL-1b).** The body must contain AskUserQuestion, `status: partial`, or an escalate heading; plus a numeric/enum termination predicate (`retry up to N` / `max N iterations` / `status: terminal`).
- **Generated agent must include a verification predicate (COMP-Y).** Hard Rules must contain ≥1 binary check ("verify", "validate", "check", or "assert"). Holistic "looks good" language is a rubric FAIL.
