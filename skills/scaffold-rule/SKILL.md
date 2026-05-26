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

Per [`docs/skill-verification-architecture.md`](../../docs/skill-verification-architecture.md) (deep-research retrofit 2026-05-26), SCAFFOLD-class verification is deterministic — `make validate` exit-0 plus idempotency plus the rule-corpus content predicates (NO-FRONTMATTER, H1-FIRST, ENFORCEMENT-VERB) plus a sensitive-content sweep is the sufficient verification primitive for this output class. Adversarial-critic (Layer B) and binary-rubric (Layer C) layers were dropped because the scaffolder's contract is "did you produce a syntactically valid rule matching the corpus convention," not "is this a high-quality rule" — quality assessment belongs in `/review-rule`, not here. Only Layer A (mechanical invariants) remains; the section below is therefore single-layer.

After Step 5 writes the file and before Step 7 reports success, record the artifact path for the verification layer:

```bash
TMPDIR=$(mktemp -d -t scaffold-rule-XXXX)
PROMISED="$TMPDIR/promised.txt"   # exactly one absolute path: the new rule file
# Write the scaffolded rule path to $PROMISED (and any doc-registration paths edited in Step 6).
```

### Pipeline — Layer A (mechanical invariants, deterministic, fail-fast)

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

### Reconciliation outcomes

- **All STRICT pass (Layer A: A.1 existence, A.2 `make validate` + NO-FRONTMATTER + H1-FIRST + ENFORCEMENT-VERB predicates, A.3 sensitive-content sweep, A.4 path regex)** → SCAFFOLD reported successful; proceed to Step 7 commit-suggestion + next-step menu.
- **Any STRICT fail** → restore inline. For frontmatter-leak the fix is mechanical (strip the leading `---` block, regenerate). For path mismatch, move the file to `.claude/rules/<name>.md`. For missing enforcement verb, rewrite the directive sentence. Max **2 iterations**, then surface to the user with the exact failing predicate + the candidate diff. Do NOT silently overwrite or hide the failure. The 2-iteration cap mirrors `rules/agentic-workflow.md §"Loop-on-symptom — stop after three"` — by iteration 3 the frame is wrong, not the artifact.
- **Only SOFT warnings (e.g. A.5 registration-skip when no listing target exists)** → report in the Step 7 success notice but proceed. The Step 4 AskUserQuestion preview gate is the final human-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

The deterministic Layer A checks bound **structural correctness**, not **quality**. Semantic defects (wrong-directive-with-valid-form, cross-rule contradiction, consolidation-miss heuristic) and template-drift detection live in `/review-rule`, `/review-claude-config`, and the 90-day baseline-refresh cadence. See [`docs/skill-verification-architecture.md`](../../docs/skill-verification-architecture.md) for the full residual catalog and per-output-class form mapping rationale. Two representative residuals worth surfacing at the Step 7 notice:

1. **Semantic-wrong directive with valid form.** A rule whose H1 + Scope + Edge Cases are all present and whose directive sentence uses `never` correctly, but the directive itself states the wrong constraint. All Layer A checks pass; only the Step 4 human preview gate catches.
2. **Cross-rule contradiction.** The new rule's directive contradicts an existing rule. Detected by `/review-rule` or human review, out of scope for SCAFFOLD verification.

## Hard Rules

- **Never overwrite an existing rule.** If a file already exists at the target path, refuse and ask for a different name.
- **Rules have no frontmatter.** Do not add YAML frontmatter to the generated rule file. Rules are plain Markdown only.
- **Preview before writing.** Always show the full generated content before creating any file.
- **Documentation edits are additive.** Append concise entries under stable headings. Never modify or remove unrelated entries.
- **Kebab-case names only.** Reject names that are not valid kebab-case. This is a repo convention, not a universal claim.
- **Constraint load check.** If the user's project already has 5 or more rules covering similar themes, flag the consolidation risk before writing a new one.
