---
name: audit-context-budget
description: >
  Estimates token cost of a repo's Claude Code configuration (CLAUDE.md, rules,
  skills, MCP servers, agents) and recommends optimizations. Use when context
  feels cramped at session start, after adding MCP servers or skills, or before
  optimizing a Claude Code setup. Do NOT use to audit source code tokens — use
  /audit-repo for that.
argument-hint: "[folder]"
allowed-tools: Agent, Read, Write, Glob, Grep
disable-model-invocation: true
---

# Audit Context Budget

You are a configuration cost analyst that estimates and visualizes the token footprint of a repo's Claude Code setup. Your job is to measure what loads into context at session start, identify the largest cost drivers, and surface optimization options — without judging whether any particular configuration is wrong.

Stop conditions:
- If the target folder does not exist, report the error and stop.
- If no Claude Code configuration is detected, produce a baseline-only report and stop.
- If the scanner subagent fails to return structured results, report what failed and stop.

## Phase 1 — Setup

**Step 1: Load references.**

Read these files from this skill's `references/` directory:
- `references/context-budget-heuristics.md` — estimation formulas and optimization multipliers
- `references/context-report-schema.md` — report structure and YAML schema
- `references/healthy-baselines.md` — per-component thresholds

**Step 2: Resolve target.**

`$ARGUMENTS` is the target folder path. Use the current working directory when empty.

Validate the folder exists via Glob (`<folder>/**`). Stop with an error if the folder has no files.

**Step 3: Detect configuration presence.**

Glob for:
- `<folder>/CLAUDE.md`
- `<folder>/.claude/` (any contents)
- `<folder>/.mcp.json`
- `<folder>/settings.json` or `<folder>/.claude/settings.json`

If none found: produce a minimal report with only the unavoidable baseline (system prompt + tools + git + environment) and stop. Note that without Claude Code config, these baseline costs are the only session-start tokens.

Also check if the target is a plugin repo: Glob for `<folder>/skills/*/SKILL.md` at root level. If found, set `is_plugin_repo = true`.

## Phase 2 — Collection

Launch a **Context Budget Scanner Agent** to collect raw measurements. The agent returns structured facts only — no recommendations or interpretations.

Agent allowed-tools: `Glob, Grep, Read, Bash`

---

```
You are scanning a repository to collect Claude Code configuration facts for a context budget audit.
Return facts only — no recommendations or interpretations.

SCAN LIMITS:
- Read at most 50 lines per file
- Scan at most 4 directory levels deep
- Cap file listings at 200 entries per glob
- BASH RESTRICTIONS: Only read-only commands allowed (wc, grep, git).
  Never use: rm, mv, cp, tee, >, >>, mkdir, touch, or any write command.

ERROR HANDLING:
- If a glob returns no results, report "NOT FOUND" for that item.
- If a file cannot be read (permission error, missing), report "ERROR: [path] — [reason]" and continue.
- If a bash command fails, report the command and error under the category.
- Always produce output for every category, even if empty.

TARGET FOLDER: [insert target folder]

## Category A: CLAUDE.md Files

1. Check for user-global file: `~/.claude/CLAUDE.md`. If accessible: char_count via `wc -c`, line_count via `wc -l`.
2. Read `<folder>/CLAUDE.md` (project root). char_count, line_count.
3. Walk parent directories from `<folder>` looking for additional CLAUDE.md files (up to 3 levels up).
4. For each CLAUDE.md found: count lines matching imperative-verb or list pattern (proxy for instruction count).
   Pattern: lines starting with `- `, `* `, a digit+`.`, or words: Add|Run|Use|Check|Do|Set|Never|Always|Avoid|Prefer|Keep|Load|Read|Create|Write|Ensure|Follow|Apply|Review|Report
5. Check `<folder>/.claude/settings.json` for `claudeMdExcludes` key. Report: present or absent.
6. Check `~/.claude/settings.json` for `claudeMdExcludes`. Report: present or absent.

## Category B: Rules

1. Glob `<folder>/.claude/rules/*.md`. For each file: `wc -c` for char_count.
   Read first 10 lines of each file to check for `paths:` in frontmatter.
   Classify as: unconditional (no `paths:`) or path-scoped (has `paths:`).

2. Glob `~/.claude/rules/*.md`. Same collection.
   Note: global rules without `paths:` re-inject on every tool call.

## Category C: MCP Servers

1. Read `<folder>/.mcp.json` (project-level). List server names.
2. Read `<folder>/.claude/settings.json`. Extract `mcpServers` keys.
3. Read `~/.claude/settings.json`. Extract `mcpServers` keys.
4. For each server: check if it has a `disabled: true` field.
5. Check for `ENABLE_TOOL_SEARCH` in any of: `.env`, `.envrc`, shell profiles accessible. Report found/not found.
6. For each server: count tools if a local schema file exists (e.g., in `.claude/` or repo root). Otherwise estimate 10 tools as default.

## Category D: Skills and Agents

1. Glob `<folder>/.claude/skills/*/SKILL.md`. For each: `wc -c`, read frontmatter (first 15 lines) to check `disable-model-invocation`.
2. Glob `<folder>/skills/*/SKILL.md` (plugin skills). For each: `wc -c`, read frontmatter. These load full content at session start.
3. Glob `<folder>/.claude/agents/*.md`. For each: `wc -c`, read frontmatter (first 15 lines).

## Category E: Git Context

1. Run `git -C <folder> rev-parse --is-inside-work-tree 2>/dev/null`. Report: git repo or not.
2. If git repo:
   - `git -C <folder> status --porcelain | wc -l` — dirty file count.
   - `git -C <folder> log --oneline | wc -l` — commit count.

## Category F: Other

1. Check `<folder>/.claude/MEMORY.md`. If exists: `wc -c`.
2. Read `<folder>/.claude/settings.json` or `~/.claude/settings.json`. Count entries in `permissions.deny` list.

---
COMPLETION: End your response with "SCAN COMPLETE" on its own line.
```

---

Wait for the scanner to return "SCAN COMPLETE" before proceeding.

## Phase 3 — Analysis

Using the scanner output and the loaded reference files, compute estimates and classifications inline.

**Step 1: Compute token ranges.**

For each measured component, apply chars/4 (low) and chars/3 (high) from `context-budget-heuristics.md`.

Fixed values:
- System prompt: 5,000 tokens
- Built-in tools: 6,000 (ENABLE_TOOL_SEARCH found/default) or 16,000 (not found in env)
- Environment: 280 tokens
- Git context: apply the formula from `context-budget-heuristics.md`

For MCP servers: apply per-tool heuristic from `context-budget-heuristics.md` based on tool counts and deferred/eager mode.

**Step 2: Compute instruction density.**

Sum instruction-proxy line counts from: all CLAUDE.md files + unconditional rule files. Add the fixed Claude Code base of 50. Compare against thresholds in `healthy-baselines.md`.

**Step 3: Classify each component.**

Apply thresholds from `healthy-baselines.md`. Assign OK / WARN / CRITICAL per component. Overall status = highest severity.

**Step 4: Generate optimization recommendations.**

For each WARN or CRITICAL component, generate a specific recommendation using multipliers from `context-budget-heuristics.md`:

- CLAUDE.md > 200 lines or > 3K tokens: "Convert prose rules to tables. Based on measured compression of 82%, this file (~X chars) could reduce to ~Y-Z tokens."
- Unconditional rules present: "These N rules re-inject on every tool call. Session cost at 20 tool calls: ~X tokens. Adding `paths:` frontmatter where applicable could reduce re-injection by ~24%."
- Plugin skills (under `skills/*/SKILL.md`) without `disable-model-invocation`: "Plugin skills load full SKILL.md content at session start. The stub + Read-on-invoke pattern reduces this by ~91%."
- Project skills without `disable-model-invocation`: "Consider adding `disable-model-invocation: true` to skills invoked only by user command. Reduces always-on cost to 0 tokens."
- MCP servers in eager mode: "ENABLE_TOOL_SEARCH not detected. With tool search disabled, MCP tool schemas load fully (~480 tokens/tool). Enabling defers all to ~0.85 tokens/tool."
- Disabled MCP servers: "Disabled servers still inject tool names. Remove them from config to recover ~10 tokens/tool."
- claudeMdExcludes absent in apparent monorepo: "CLAUDE.md files in parent directories may load unexpectedly. `claudeMdExcludes` in settings.json prevents this."

Frame each recommendation as cost visibility, not removal. Do not recommend removing any MCP server, skill, or rule.

**Step 5: Rank by savings.**

Sort recommendations: highest estimated savings first. Assign P0 (>5K tokens saved or instruction density CRITICAL), P1 (1-5K), P2 (<1K or informational).

## Phase 4 — Report

Build the report using the schema from `context-report-schema.md`.

**Body sections in order:**

### Context Budget Summary

Total estimated config context (excluding unavoidable baseline): X–Y tokens (Z–W% of 200K).
Overall status: healthy / warning / critical.
Instruction density: N estimated instructions. Status: healthy / warning / critical.

If `is_plugin_repo = true`: "This is a plugin repo. For internal reference file budgets, use `/check-repo-health tokens`."

### Limitations

Estimation method: character count divided by 3–4. Actual tokens depend on tokenizer, language mix, and content structure. Estimates may be off by ±30% for code-heavy content.

Base overhead: system prompt and built-in tool costs derive from community measurements, not official Anthropic documentation [Tier 3: community observation].

Unmeasured factors: actual API token consumption (no access), prompt cache hit rates (cached tokens cost 10× less — a "costly" config that caches well may be cheaper than a "lean" one that cache-misses), rule re-injection multiplier depends on conversation length, context compaction behavior.

Cache alignment warning: splitting a large CLAUDE.md or rule file can break the stable prefix required for prompt caching. Measure the cache hit rate before and after significant splits.

### Component Breakdown

Table: Component | Token Range (Low–High) | Est. % of 200K | Status | Key Observation

Include one row per measured component, plus the unavoidable baseline as an informational row.

### Optimization Recommendations

Grouped by P0 / P1 / P2. Each recommendation: specific file(s), what to change, estimated savings range, evidence tier.

### Action Plan

Checkbox list: one item per recommendation with specific file path and action.

---

**Present the full report in the conversation. Then confirm before writing the report file.**

Offer to write to: `<target>/.claude/reviews/<YYYY-MM-DDTHHMMSS>-audit-context-budget.md`

## Hard Rules

- Read-only on the target repository. Write only the report file to `<target>/.claude/reviews/`.
- Token estimates are always ranges (chars/4 to chars/3), always labeled "estimated".
- Every recommendation cites the evidence tier and specific file paths measured.
- Never recommend removing MCP servers, skills, or rules. Report cost only.
- Limitations section appears before recommendations in every report.
- Bash is restricted to the scanner subagent. Top-level workflow uses Read/Glob/Grep only.
- When the target is a plugin repo (`skills/*/SKILL.md` at root), note that `/check-repo-health tokens` handles internal reference budgets.
