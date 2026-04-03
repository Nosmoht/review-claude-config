# Session Check Hook

> Warns at session start if the engineering baseline reference file is stale (older than 90 days).

**Hook Event:** SessionStart
**Matcher:** (all sessions)
**Script:** `hooks/session_check.py`
**Timeout:** 10s
**Configuration:** `hooks/hooks.json`

## Overview

The session check hook fires once at the beginning of every Claude Code session when the plugin is installed. It reads the `last_refreshed` date from the engineering baseline file's YAML frontmatter and computes the age in days. If the baseline is older than 90 days, it injects a warning message suggesting the user run `/refresh-engineering-baseline` to update it.

This ensures that review skills always operate against reasonably current best practices. Without this hook, a stale baseline could silently degrade review quality — the hook makes staleness visible to the user at session start rather than waiting until a review produces outdated recommendations.

## Process Steps

### Step 1: Environment Check

**Purpose:** Verify the hook is running within a plugin context.

**Process:**
- Read `CLAUDE_PLUGIN_ROOT` environment variable
- If not set, return `{}` immediately

### Step 2: Locate and Read Baseline

**Purpose:** Find the `last_refreshed` date in the baseline file.

**Process:**
- Construct path: `{CLAUDE_PLUGIN_ROOT}/skills/review-claude-config/references/engineering-baseline.md`
- Read the file line by line (efficient — no need to parse full YAML)
- Search for a line starting with `last_refreshed:`
- Extract the date string after the colon

### Step 3: Compute Age

**Purpose:** Determine if the baseline is stale.

**Process:**
- Parse the date string as ISO format (`YYYY-MM-DD`) using `datetime.date.fromisoformat()`
- Compute difference from today's date in days

### Step 4: Conditional Warning

**Purpose:** Alert the user if the baseline needs refreshing.

**Process:**
- If age > 90 days: return JSON with `hookSpecificOutput`:
  ```json
  {
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": "Engineering baseline last refreshed YYYY-MM-DD (N days ago). Run /refresh-engineering-baseline to update."
    }
  }
  ```
- If age <= 90 days: return `{}` (no warning, session starts normally)

## Injected Content

When the baseline is stale, the user sees a warning message at session start:

> Engineering baseline last refreshed 2025-12-15 (101 days ago). Run /refresh-engineering-baseline to update.

This message appears as additional context in the session, making it visible but non-blocking.

## Graceful Degradation

The hook is designed to never block session startup:

- **No `CLAUDE_PLUGIN_ROOT`:** Returns `{}` silently
- **Baseline file missing:** The outer `try/except` catches `FileNotFoundError` and returns `{}`
- **No `last_refreshed` line:** Loop completes without finding the line, falls through to return `{}`
- **Unparseable date:** Exception caught, returns `{}`
- **Always exits 0:** The `finally` block ensures clean exit regardless of outcome

## Related Components

- **Reads:** `skills/review-claude-config/references/engineering-baseline.md` (specifically the `last_refreshed` frontmatter field)
- **Triggers for:** All sessions when plugin is installed
- **Related skill:** `/refresh-engineering-baseline` — the skill this hook suggests running when baseline is stale
- **Related skill:** `/check-repo-health freshness` — performs the same freshness check as a diagnostic, plus checks all other reference files
- **Configuration:** Registered in `hooks/hooks.json` under `SessionStart` with no matcher (fires for all sessions)
