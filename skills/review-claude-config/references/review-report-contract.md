---
name: review-report-contract
description: Canonical review/report contract for all producers and consumers
last_refreshed: 2026-04-03
---

# Review Report Contract

Normative source for the review/report contract (`review-*`, `apply-*-review-findings`, `review-analytics`, `check-repo-health`).

## Certificate Shape

Order: `Goal` → `Certificate` → `Strengths` → `[Diagnostics]` → `Recommendations`. Calibration/diagnostic sections may appear between `Certificate` and `Recommendations`.

## Recommendation Block

Heading: `#### N. [Title] (Impact: [High/Medium/Low][, Category: ...][, ID: {finding_id}])`

Required: `Evidence`, `Why it matters`, `Validation`. Optional: `Current`, `Recommended`, `finding_id`.

Dispatchable = both `Current` and `Recommended` present. Manual-only = valid finding without anchors.

## Finding Identity (optional)

`finding_id`: `{checklist_item}:{path}:{dimension}/v1`. Non-checklist: `ADHOC:{path}:{dim}:{slug}/v1`. Consumers match on `finding_id` when present; fall back to heading parse when absent.

## Finding Determinism

Findings fall into two classes:

- **Deterministic** — `checklist_item` is in the binary or narrative-parent enumeration (see `scripts/merge_findings.py` `BINARY_ITEM_IDS` / `NARRATIVE_PARENT_IDS`, and `skills/review-skill/references/merge-rules.md` §"Convergence Policy"). `finding_id` is byte-stable across runs on unchanged artifacts. Counted in convergence gates.
- **Advisory** — items emitted by perspective Haiku agents that fall outside the deterministic enumeration. May vary run-to-run. Surface in the cert but do not count toward convergence. Consumers parsing finding_ids for delta analytics SHOULD filter to the deterministic class for stable series.

Advisory findings surface only at Low severity (issue #72 demotes advisory H/M to Low at merge). H+M is deterministic by construction.

## Report Frontmatter

```yaml
---
generated_by: review-*  # review-skill, review-agent, review-rule, review-mcp-server, review-settings, review-claude-config
schema_version: 1
date: YYYY-MM-DD
repo: <slug>                # basename(target_dir)
origin: <git-remote-url>    # Optional
target: /absolute/path
baseline_version: YYYY-MM-DD
items_reviewed: N
summary:
  - name: item-name
    type: Skill|Agent|Rule|MCP|Settings
    path: relative/path/to/file
    overall: B
    score: 85.0
    clarity: B
    completeness: A
    prompt_engineering: B
    context_engineering: B
    goal_alignment: B
    safety: A
    metadata: B
---
```

## Identity and Tracking

`type + path` is the canonical artifact identity; `name` is display-only. A disappearing path + new path is a rename/move candidate, not a silent merge by name. Analytics series identity: `repo + generated_by + type + path`.

## Producer Compatibility

Single-item and batch reports share the same schemas. `schema_version` stays `1` unless breaking change.

## Dimensions

Full reports: `clarity`, `completeness`, `prompt_engineering`, `context_engineering`, `goal_alignment`, `safety`, `metadata`. Rules/MCP/Settings: non-applicable → `null`.

## Sidecar Emission

Producers MAY emit a structured `findings.json` sidecar alongside the Markdown report. When emitted, the sidecar is the authoritative machine-parsable input for `apply-*-review-findings`; the Markdown report becomes the human-readable surface.

- **Sibling naming:** `<report-prefix>.findings.json` next to `<report-prefix>.md`. Example: `2026-04-27T120000-review-skill.md` ↔ `2026-04-27T120000-review-skill.findings.json`.
- **Schema:** `skills/review-claude-config/references/schemas/findings-list.schema.json` (top-level wrapper) referencing `finding.schema.json` (per-finding shape). Required wrapper keys: `generated_by`, `findings`. Optional: `schema_version`, `session_id`, `artifact_path`, `artifact_type`.
- **Emit conditions:** `/review-skill` emits the sidecar in **multi-perspective standalone mode only** (i.e., not `--single-perspective`, not orchestrated mode). `/review-agent`, `/review-rule`, and `/review-claude-config` do not yet emit sidecars; consumers must tolerate absence.
- **Empty findings:** `findings: []` is a valid clean-review state. Consumers MUST surface this as "no findings" and stop, not fall back to Markdown parsing.
- **Atomicity:** producers write the sidecar via tmp-file + rename. Consumers that hit a parse error MUST treat it as missing-or-malformed and fall back to Markdown.
- **Applyability gate (consumer contract):** before classifying a finding as Dispatchable, consumers MUST verify `current` is a literal substring of the artifact file (Read the file, simple substring check). Findings whose `current` is empty or non-substring drop to Manual-only. This catches synthesized-binary findings (whose `current` is the composed evidence string, never present in the file verbatim) and whitespace-drifted perspective findings, preventing corrupted Edit replacements.

### Batch sidecars

Future emission of a sidecar for `/review-claude-config` (multi-item batch) follows the same wrapper but covers all items:

- One sidecar per batch report. `findings` is a single flat array; per-finding `path` keys back to `summary[*].path` for type lookup.
- `artifact_path` and `artifact_type` SHOULD be omitted (the wrapper covers heterogeneous artifacts).
- Consumers that need per-type grouping (orchestrators) MUST match `findings[*].path` against the report's frontmatter `summary[*].path` to derive each finding's `type`. Findings whose `path` does not match any `summary` entry MUST be marked Manual-only with reason "Path not in report scope".

This shape is reserved; no producer emits batch sidecars yet.
