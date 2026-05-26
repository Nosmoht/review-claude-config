---
name: scaffold-rule
description: >
  Creates a plain-Markdown rule at .claude/rules/<name>.md with directive,
  scope, and edge cases. Use when adding an always-active constraint to a
  project. Do NOT use for skills or agents — use /scaffold-skill or
  /scaffold-agent.
argument-hint: "<rule-name>"
allowed-tools: Read, Write, Edit, Glob
disable-model-invocation: true
---

# Rule Scaffolding

You are a rule scaffolding tool that creates correctly structured Claude Code rule files. Your job is to generate focused directive files that follow the plain-Markdown rule format — no frontmatter, no workflows, no tool access declarations.

## Workflow

### 1. Validate rule name

Parse `$ARGUMENTS` as `<rule-name>`.

- If the argument is empty, ask the user for a rule name.
- Name must be kebab-case (lowercase letters, hyphens only, no spaces or underscores). This is a repo naming convention for consistency and filesystem predictability.
- Check for conflicts: Glob `.claude/rules/*.md` and `**/.claude/rules/*.md`. If a file with the same name already exists, report the conflict and ask for a different name.

Stop if the name is invalid or conflicts with an existing rule.

### 2. Load template and conventions

Read `references/rule-template.md` for the canonical rule structure.

If the file cannot be read (missing or unreadable), stop and report:
"rule-template.md not found — cannot scaffold without format conventions. Verify the file exists at skills/scaffold-rule/references/rule-template.md."

Optionally read `research/claude-code/skill-agent-format-conventions.md` (Glob for `**/research/claude-code/skill-agent-format-conventions.md`) — specifically the Rules section — for additional format guidance. If not found, proceed with the template defaults.

### 3. Gather requirements

Ask the user for the following before generating anything:

1. **Purpose** — What constraint does this rule enforce? What specific behavior does it prevent or require?
2. **Scope** — Which files, tools, commands, or actions does it apply to? Is the scope broad (all conversations) or narrow (specific file types, specific tools)?
3. **Enforcement verbs** — Suggest: `always`, `never`, `before X do Y`. Confirm which phrasing fits.
4. **Edge cases** — Are there situations where this rule does not apply? Known exceptions or conditions that narrow the scope?
5. **Consolidation check** — List existing rules found during the conflict check. If 5 or more rules cover similar themes (e.g., multiple "no destructive ops" rules), suggest consolidating into one rather than adding another. Ask whether consolidation makes sense before proceeding.

### 4. Generate rule file

Build the rule content as plain Markdown with no frontmatter:

```
# <Rule Name>

<Directive statement: one or two sentences using strong enforcement verbs — always, never, before X do Y.>

## Scope

<Paragraph describing which files, tools, actions, or situations this rule applies to. Be specific enough to avoid ambiguity.>

## Edge Cases

- <Exception or boundary condition>
- <Another exception, or "None" if truly universal>
```

Before presenting, run these validation checks against the generated content:
- The rule file must NOT start with `---` (YAML frontmatter is not allowed in rule files)
- The first non-blank line must be a Markdown heading (`# ...`)
- The directive section must contain at least one enforcement verb: `always`, `never`, `before`, `do not`, `must`

If any check fails, report the specific violation and correct it before presenting.

Present the full generated content to the user. Confirm via AskUserQuestion (header: "Rule preview"):
- Option 1 label: "Correct — write file" (Recommended) — description: `"Write the rule to .claude/rules/<rule-name>.md"`
- Option 2 label: "Adjust" — description: `"Describe what to change; will regenerate and show again"`
- Option 3 label: "Cancel" — description: `"Stop without writing anything"`

On "Adjust": ask what to change, regenerate, and show the preview again before writing. On "Cancel": stop without writing anything.

### 5. Write file

Determine the target path: `.claude/rules/<rule-name>.md`.

- If `.claude/rules/` does not exist, create it by writing the file (Write creates intermediate paths).
- Write the rule file.
- Report success with the full path, or report the failure clearly if the write did not complete.

### 6. Register in repository docs

Make targeted, additive edits only. Do not rewrite unrelated sections.

- Update `CLAUDE.md` under `## Commands` if a new rule category is introduced and a listing belongs there.
- Update `docs/skills/README.md` under `## Quick Reference` and `## By Function` when the new rule belongs in a component inventory tracked there.

If neither section exists or the new rule does not add to an existing listing, skip this step and note the omission.

### 7. Suggest commit and next steps

Tell the user:

```
Rule scaffolded. Suggested commit:
  feat(<rule-name>): add <rule-name> rule
```

Then present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Review the new rule" (Recommended) — description: `"Run /review-rule .claude/rules/<rule-name>.md to validate quality"`
- Option 2 label: "Scaffold another rule" — description: `"Provide a rule name to scaffold another"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Review the new rule": invoke `/review-rule` with the new rule's path. On "Scaffold another rule": ask for the rule name, then invoke `/scaffold-rule`. On "Done": acknowledge and stop.

## Quality measurement (mandatory before Step 7 success report)

Without verification, this skill fails at **convention/idiomatic drift** (F3) — specifically, emitting a rule file that begins with `---` YAML frontmatter. Rules have NO JSON Schema, so `make schema-validate` cannot enforce the no-frontmatter convention; a file like `---\nname: foo\n---\n# X` passes JSON validation and lint yet structurally violates the rule corpus convention (rules are plain Markdown, the Hard Rule in this skill, and the conventions in every sibling under `.claude/rules/`). The three-layer pipeline below binds `make validate` to a sibling-comparison critic and a 6-dimension binary rubric so a SCAFFOLD operation reports success only when every layer agrees.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024).

After Step 5 writes the file and before Step 7 reports success, record the artifact path for the verification layers:

```bash
TMPDIR=$(mktemp -d -t scaffold-rule-XXXX)
PROMISED="$TMPDIR/promised.txt"   # exactly one absolute path: the new rule file
# Write the scaffolded rule path to $PROMISED (and any doc-registration paths edited in Step 6).
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

**A.2 STRICT — `make validate` exits 0 AND rule-specific content predicates pass.** `make validate` runs the full chain (ruff lint, ruff format, JSON Schema, token budget, description-graph regression, pytest); rules have no JSON Schema, but a token-budget overflow or description-graph regression on a doc-registration edit can still surface here.

```bash
( cd "$REPO_ROOT" && make validate ) > "$TMPDIR/make-validate.log" 2>&1
mv_exit=$?
[ $mv_exit -ne 0 ] && { echo "STRICT FAIL make-validate exit=$mv_exit"; fail=$((fail+1)); }
```

Additionally apply rule-corpus content predicates against the new rule file. **These are load-bearing for scaffold-rule because rules have no schema** — without them, F3 frontmatter-leak passes silently:

- **NO-FRONTMATTER (load-bearing)**: the first non-blank line of the file MUST NOT be `---`. `head -1 <rule-path>` MUST NOT equal `---`. STRICT FAIL on any leading YAML frontmatter.
- **H1-FIRST**: the first non-blank line MUST match `^# `. Absence is STRICT FAIL.
- **ENFORCEMENT-VERB**: the body MUST contain at least one of `always`, `never`, `before`, `do not`, `must` (case-insensitive). Absence is STRICT FAIL — a rule without an enforcement verb has no directive force.

**A.3 STRICT — sensitive-content sweep on every newly-written artifact.** Source the home-path regex set from `hooks/block-sensitive-content.sh` at runtime (do NOT duplicate literals here). Sweep each promised path for: (a) the home-path patterns loaded from the hook, (b) literal RFC1918 IPs (`\b(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)[0-9.]+\b`). Rules carry no `.mcp.json` `env` block, so the literal-credential check is not applicable to this skill's outputs.

**A.4 STRICT — path-placement matches the rule class.** The scaffolded path MUST match `^\.claude/rules/[a-z][a-z0-9-]*\.md$`. Mismatch → STRICT FAIL (covers F5).

**A.5 SOFT — doc-registration count.** Per the scaffolder's Step 6, expect ≥0 doc-registration edits (`CLAUDE.md`, `docs/skills/README.md`) — registration is best-effort per the Hard Rules ("if neither section exists or the new rule does not add to an existing listing, skip this step and note the omission"). Zero edits is acceptable; surface as a warning only when the rule introduces a new category that would normally be listed.

What each metric catches:

| Metric | Catches |
|---|---|
| A.1 file-existence | F1, F6 |
| A.2 `make validate` + NO-FRONTMATTER + H1-FIRST + ENFORCEMENT-VERB | F1, F2 (inverted), F3 (frontmatter-leak), F4 |
| A.3 content-sweep | F7 |
| A.4 path regex | F5 |
| A.5 registration-count | F6 (soft) |

### Layer B — adversarial critic dispatch (sibling-comparison, blind)

Pick a sibling: most-recently-edited `.claude/rules/*.md` in the same repo, excluding the candidate itself. If the candidate is the first rule scaffolded into this repo and no in-repo sibling exists, fall back to a recently-edited rule from the user-global rules tree (`$HOME/workspace/claude-config/rules/`).

Dispatch a fresh subagent with the candidate (A) and sibling (B). Then dispatch a second time with order swapped — position bias is the dominant LLM-judge artifact (Shi et al. 2024 arXiv:2406.07791). Take the **union** of items flagged across both runs.

```
Agent({
  description: "Adversarial scaffold-rule critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer of two Claude Code rule files (plain " +
    "Markdown, no frontmatter). Neither label tells you which is the " +
    "freshly-scaffolded candidate. Compare A and B for structural and " +
    "conventional fit. List every: (1) top-level structural element " +
    "(H1 heading, top-level subheading) present in EXACTLY ONE file; " +
    "(2) presence of leading `---` YAML frontmatter on either file " +
    "(this is a hard violation for rule files); (3) convention " +
    "divergence — enforcement-verb usage (MUST/NEVER vs always/never/" +
    "do not), directive-statement positioning, Scope / Edge Cases " +
    "section presence; (4) required-element omission — H1 heading, " +
    "directive sentence with enforcement verb, Scope paragraph, Edge " +
    "Cases list. For each item: quote the literal token/heading, name " +
    "which file (A or B), and classify as MISSING / EXTRA / RENAMED / " +
    "NOVEL_SHAPE. Do not rate quality. Do not praise clarity. Report " +
    "under 500 words. " +
    "A:\n<paste candidate rule contents>\n\nB:\n<paste sibling rule contents>"
})
```

Vocabulary the critic produces:

- `MISSING` — element in sibling but not candidate (maps to F2/F6 — for rules, this means missing Scope or Edge Cases).
- `EXTRA` — element in candidate but not sibling (maps to F3 — may be legitimate).
- `RENAMED` — semantic match under different identifier (maps to F3).
- `NOVEL_SHAPE` — structurally unprecedented for the rule class (maps to F3 — strongest idiomaticity signal). **Any frontmatter on the candidate is auto-classified as NOVEL_SHAPE** even if the critic does not explicitly flag it, because the rule class definition prohibits frontmatter.

Skill-specific binary checks the critic must report:

- Presence of leading `---` on either file → NOVEL_SHAPE on whichever file has it.
- Absence of an H1 heading on either file → MISSING on whichever lacks it.
- Directive sentence lacks an enforcement verb (`always`, `never`, `before`, `do not`, `must`) → MISSING on whichever lacks it.

### Layer C — 6-dimension binary rubric (CheckEval-style)

Bind Layer A failures and Layer B findings to a yes/no rubric. CheckEval (arXiv:2403.18771) reports +0.45 inter-evaluator agreement for binary vs. Likert. Any `NO` blocks the success report.

```
D1 VALIDATION_PASS    `make validate` exits 0 with the scaffolded rule
                      on disk AND the NO-FRONTMATTER / H1-FIRST /
                      ENFORCEMENT-VERB predicate greps all pass.
                      STRICT-tied to Layer A.2. Catches F1, F4.
D2 FRONTMATTER_VALID  INVERTED for rules — yes iff the file has NO
                      leading `---` YAML frontmatter (per scaffold-rule
                      Hard Rule "Rules have no frontmatter"). Catches
                      F3 (frontmatter-leak — the load-bearing failure
                      class for this skill).
D3 PATH_CORRECT       Candidate path matches
                      `^\.claude/rules/[a-z][a-z0-9-]*\.md$` (Layer A.4).
                      Catches F5.
D4 IDIOMATIC_FIT      Zero NOVEL_SHAPE findings from Layer B union;
                      ≤2 RENAMED findings (RENAMED is judgment-call,
                      hard cap 2); first non-blank line is `# ` heading;
                      body contains an enforcement verb. Catches F3.
                      Load-bearing for SCAFFOLD.
D5 COMPLETENESS       The single rule file in $PROMISED exists,
                      non-empty. Doc-registration is best-effort per
                      the scaffolder's Hard Rules; D5 does NOT block
                      on missing registration edits. Catches F6.
D6 NO_LEAKAGE         Zero matches for the hook-sourced home-path
                      patterns, zero RFC1918 IPs in the rule body
                      (Layer A.3). Catches F7.
```

Map Layer A failures → D1 (make validate, predicates), D2 (NO-FRONTMATTER), D3 (path), D5 (existence), D6 (content sweep). Map Layer B `MISSING` → D2/D5. Map `EXTRA`/`RENAMED`/`NOVEL_SHAPE` → D4.

### Reconciliation outcomes

- **All STRICT pass + zero `MISSING`/`NOVEL_SHAPE` from critic + all D1–D6 = yes** → SCAFFOLD reported successful; proceed to Step 7 commit-suggestion + next-step menu.
- **Any STRICT fail OR any `MISSING`/`NOVEL_SHAPE` OR any D1–D6 = no** → restore inline. For frontmatter-leak the fix is mechanical (strip the leading `---` block, regenerate). For path mismatch, move the file to `.claude/rules/<name>.md`. For missing enforcement verb, rewrite the directive sentence. Max **2 iterations**, then surface to the user with the exact failing dimension + the candidate-vs-sibling diff. Do NOT silently overwrite or hide the failure. The 2-iteration cap mirrors `rules/agentic-workflow.md §"Loop-on-symptom — stop after three"` — by iteration 3 the frame is wrong, not the artifact.
- **Only SOFT warnings (e.g. A.5 registration-skip when no listing target exists, ≤2 `RENAMED` from Layer B)** → report in the Step 7 success notice but proceed. The Step 4 AskUserQuestion preview gate is the final human-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Semantic-wrong directive with valid form.** A rule whose H1 + Scope + Edge Cases are all present and whose directive sentence uses `never` correctly, but the directive itself states the wrong constraint (user asked for "never overwrite logs"; scaffolder emitted "never overwrite configs"). D1, D2, D3, D4 all pass. Only the Step 4 human preview gate catches.
2. **Cross-rule contradiction.** The new rule's directive contradicts an existing rule in `.claude/rules/` or `$HOME/workspace/claude-config/rules/`. Layer B compares structure to one sibling, not semantic consistency across the corpus. Detected only by `/review-rule` or human review at the AskUserQuestion preview gate.
3. **Consolidation miss.** The Hard Rule "Constraint load check" asks the scaffolder to flag when ≥5 rules cover similar themes, but the threshold is heuristic — a new rule adjacent to 4 existing ones still passes the check and may compound rule sprawl. Detected only by `/review-claude-config` running the rule-corpus audit.
4. **Description-graph regression on doc-registration edits.** A new line appended to `docs/skills/README.md` that contradicts an existing entry's description nudges the description-graph clarity score below the calibrated threshold for `make validate-descriptions`. A.5 counts edits, not semantic-fit.
5. **Future-template drift.** This skill reads `references/rule-template.md` — if the template falls out of sync with the rule-corpus conventions or `engineering-baseline.md`, the scaffolder faithfully emits drifted content. Detected only by the 90-day baseline-refresh cadence.

The Step 7 success notice MUST list which residual classes apply to passages the critic flagged as MISSING/EXTRA without resolution, so the operator has one last human-glance opportunity before the suggested commit lands.

## Hard Rules

- **Never overwrite an existing rule.** If a file already exists at the target path, refuse and ask for a different name.
- **Rules have no frontmatter.** Do not add YAML frontmatter to the generated rule file. Rules are plain Markdown only.
- **Preview before writing.** Always show the full generated content before creating any file.
- **Documentation edits are additive.** Append concise entries under stable headings. Never modify or remove unrelated entries.
- **Kebab-case names only.** Reject names that are not valid kebab-case. This is a repo convention, not a universal claim.
- **Constraint load check.** If the user's project already has 5 or more rules covering similar themes, flag the consolidation risk before writing a new one.
