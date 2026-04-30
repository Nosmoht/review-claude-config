---
name: review-settings
description: >
  Evaluates Claude Code settings.json (deny-rules, env-vars, statusline)
  across 4 dimensions (Completeness, Goal Alignment, Safety, Metadata).
  Use when asked to 'review settings', 'review settings.json', or
  'check settings'. Do NOT use for .mcp.json, skills, agents, rules, or hooks.
argument-hint: <path-to-settings.json>
allowed-tools: Read, Write, Glob, Grep, WebSearch
---

# Review Settings

Evaluate a Claude Code `settings.json` for quality across 4 evidence-based dimensions. Project-level scope by default (`.claude/settings.json`). Standalone mode accepts any explicit path (including user-level `~/.claude/settings.json`).

## Argument Handling

- `$ARGUMENTS` is a path to a `settings.json` file.
- If given a directory, look for `.claude/settings.json` in that directory.
- If `.claude/settings.local.json` also exists, read both and note local overrides.
- If no settings file found, report the error and stop.
- **Parse the JSON first.** Invalid JSON silently disables ALL permission rules — this is a Critical finding.

## Mode Detection

Check whether the prompt contains an orchestration metadata block:

```
---orchestration---
mode: orchestrated
websearch_available: true|false
webfetch_available: true|false
domain_cache: |
  <cached domain content or "none">
---
```

- If present → **orchestrated mode** (return structured certificate only).
- If absent → **standalone mode** (full workflow below).

## Phase 1 — Setup (standalone mode only)

1. **Load references.** Read:
   - Scoring rubric: Glob `**/review-claude-config/references/scoring-rubric.md`
   - Source quality criteria: Glob `**/review-claude-config/references/source-quality-criteria.md`
   - Repo identification: Glob `**/review-claude-config/references/repo-identification.md` to resolve `suite-root` and `repo-slug`
   - Settings evaluation guide: `references/settings-evaluation-guide.md`

2. **Probe tool availability.** Test WebSearch with a trivial query. Record `websearch_available`.

## Phase 2 — Evaluation

### Step A: Context Inference + Domain Research

1. Read the settings file. Parse JSON. If parse fails → Critical finding, stop.
2. Identify project context: read `CLAUDE.md` or `README.md` if available.
3. Domain research:
   - Check domain cache: Read `${CLAUDE_PLUGIN_ROOT}/skills/review-claude-config/references/domain-cache/INDEX.md`.
   - If `CACHED`: use cache. If `STALE`: refresh via WebSearch.
   - If no match: perform 1-2 targeted WebSearch queries for Claude Code settings security best practices.
   - If unavailable: use model knowledge only, marked `[no external verification]`.
4. Synthesize: what security posture should this project's settings have?

### Step B: Checklist Evaluation

1. Load `references/settings-evaluation-guide.md`.
2. Evaluate every checklist item: PASS | FAIL | NA.
3. If `.claude/settings.local.json` exists, check for scope conflicts with main settings.
4. Score each dimension using the rubric. Cite evidence before grading.
   - Grade derivation: A=0 FAILs; B=≤25% (no High); C=any High or >25%; D=>50% High; F=>50% total.
5. Calculate overall grade: Completeness 25%, Goal Alignment 25%, Safety 30%, Metadata 20%.

### Step C: Output

Produce the certificate (same format as review-mcp-server).

## Phase 3 — Report (standalone mode only)

1. Create the `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/` directory if it does not exist. Write to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-settings.md` with `repo: <slug>` and optionally `origin: <git-remote-url>` in the frontmatter (after `date`).
2. Suggest commit message.

## Hard Rules

- **Read-only on analyzed files.** Never modify settings.json. Write only to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/`.
- **Apply the rubric strictly.**
- **Every High or Medium recommendation must include evidence and a concrete rewrite.**
- **Parse failure = Critical.** Invalid JSON disables ALL permission rules.
