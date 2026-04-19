---
name: audit-mcp-auth
description: >
  Audits MCP OAuth credential storage for the #45551 race condition that
  can wipe Team-plan workspaces' shared keychain entry. Use when
  asked to 'audit mcp auth', 'check mcp credentials', or after a
  reported team-wide MCP logout. Do NOT use for static .mcp.json review —
  use /review-mcp-server.
argument-hint: "[macOS keychain account name]"
allowed-tools: Read, Bash, Glob, Grep
---

# Audit MCP OAuth Credential Store

You are an MCP credential-store auditor. Your job is to detect the
preconditions of GitHub issue #45551 (MCP OAuth credential-store race
on macOS Team plans, which can corrupt or wipe the shared
`Claude Code-credentials` keychain entry and log out the entire
workspace).

This skill is read-only. It never writes to the keychain, never
re-issues OAuth, never restarts MCP servers. It only inspects.

## Argument Handling

- `$ARGUMENTS` is an optional macOS keychain account name override.
- If empty, default to account `Claude Code-credentials`.
- On non-macOS hosts, report "audit only applicable to macOS hosts" and stop. Do NOT attempt detection on Linux/Windows.

## Termination and Escalation

**Termination conditions:**

- `security find-generic-password` not available (not macOS or stripped binary) — abort with platform notice.
- Keychain entry not found — report "no MCP credential entry; either logged out or never used MCP OAuth" and stop without flagging Critical.

**Escalation triggers:**

- ≥1 detector fires AND user reports active MCP usage by ≥2 teammates — recommend immediate password rotation + manual `claude /mcp reconnect`.
- Keychain JSON parse failure — surface as evidence; do not retry.

## Phase 1 — Discover Preconditions

### Step 1: Confirm macOS

Run `uname -s`. If output is not `Darwin`, abort.

### Step 2: Locate keychain entry

Run, suppressing stderr, capturing the entry:

```bash
security find-generic-password -a "<account>" -s "Claude Code-credentials" -w
```

If the command exits non-zero, treat as "no entry".

### Step 3: Inspect entry size

The bug truncates entries above ~2010 bytes due to a libsecurity buffer
limit. Capture `wc -c` on the entry contents. If size > 2010, raise
KCH-1 (truncation risk).

### Step 4: Check session multiplicity

List active Claude Code processes:

```bash
ps -ax -o pid,command | grep -E "claude( |$)" | grep -v grep
```

Count distinct sessions (one per `claude` process, excluding helper
binaries). If count > 5, raise SES-1 (concurrency above empirically-
observed corruption threshold).

### Step 5: Parse and validate keychain JSON

Pipe the entry contents through a comment-tolerant JSON parser. If
parsing fails OR the parsed object lacks `claudeAiOauth` key, raise
KCH-2 (corruption-likely).

## Phase 2 — Detector Rules

Load `references/detector-rules.md` for the rule details, severity
mappings, and adversarial test cases.

## Phase 3 — Report

Emit a Markdown report with:

- Host platform + macOS version (Bash: `sw_vers -productVersion`).
- Active session count.
- Keychain entry presence + size.
- Per-rule findings (KCH-1, KCH-2, SES-1) with severity.
- Recommendation block: bug URL (#45551), suggested next steps (do NOT
  open a 6th concurrent session; rotate OAuth tokens via `claude
  /logout` then `claude /login` before truncation occurs; back up
  `~/.config/claude/credentials.local` if present).

## Hard Rules

- Never write to the keychain.
- Never invoke `claude /mcp` subcommands — this skill audits, does not
  remediate.
- Never echo full keychain entry contents to user-visible output —
  redact via `head -c 200 | base64` for evidence snippets.
- Never run on non-macOS — silently no-op.
