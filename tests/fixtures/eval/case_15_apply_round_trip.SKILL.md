---
name: case-15-apply-round-trip-fixture
description: Reviews configuration files and updates settings in the target directory.
allowed-tools: Read, Write, Glob
---

# Case 15 Apply Round-Trip Fixture

A synthetic skill for the D5 apply round-trip eval case. It intentionally
carries two deterministic-subset defects with known mechanical fixes:

1. **SP-2b (Safety / High)** — `Write` is present in `allowed-tools` without
   a `disable-model-invocation: true` gate or an explicit binding clause in the
   body. Fix: add `disable-model-invocation: true` to frontmatter.

2. **META-2 (Metadata / Medium)** — The `description` field lacks a
   `do not use` / `not for` / `skip when` exclusion phrase. Fix: append
   "Do not use for read-only audits." to the description.

All other rubric dimensions are intentionally clean so that no stray
Medium/High findings inflate the "no new Medium/High" re-review check.

## Workflow

### Step 1 — Locate configuration files

Use Glob to find all `*.yaml` configuration files under the target directory.
Skip any file whose path contains `.ssh` or `.env`.

### Step 2 — Read and validate each file

For each file found in Step 1, use Read to load its contents and verify the
required keys are present. Stop with an error message if a file cannot be read.

### Step 3 — Apply updates

For each configuration file that requires a change, use Write to apply the
update in the target directory.

### Step 4 — Summarise

Produce a Markdown summary listing every file updated and its new setting value.
Output a final status line indicating the number of files processed.

## Completion

Output the final Markdown summary after all configuration files have been
processed (updated or confirmed unchanged).

## Error Handling

If Write fails or the target directory is absent, escalate to the user:
stop with a structured error message listing the affected paths before
proceeding to Step 4. The workflow produces a partial result with
`status: partial` when some files succeed and others fail.
