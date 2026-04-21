---
last_refreshed: 2026-04-19
---

# Claude Code Known Issues (rolling catalog)

Rolling catalog of known bugs, regressions, and CVEs in Claude Code that are relevant to this review plugin. Quarterly sections are appended in place; closed/resolved entries are removed. Used to seed `/audit-policy-compliance`, `/audit-mcp-auth`, `/audit-plugins`, and related detectors.

## TL;DR (2026-04-19)

- Two 9-month-old **CRITICAL** bugs still open: #39523 (bypass-permissions fundamentally broken) and #45551 (MCP OAuth credential-store corruption can log out whole Team workspace).
- Permission cache reload bug #41259 still OPEN (rev2's hope that it was fixed was wrong).
- Hook exit-code phantom-block bug #21988 is **closed** (fixed 2026-01-30).
- Plugin manifest git-index leak #50655 is a niche but destructive bug affecting pre-commit `claude -p` invocations.

## 2026-Q1 / Q2 — Active Critical and High Issues

### Permissions and Settings

| Issue | State | Severity | Detector target |
|-------|-------|----------|-----------------|
| [#39523](https://github.com/anthropics/claude-code/issues/39523) [META] Bypass permissions fundamentally broken across all bypass mechanisms for protected dirs (9-month trail) | OPEN | Critical | `/audit-policy-compliance` |
| [#41259](https://github.com/anthropics/claude-code/issues/41259) Permissions in `settings.local.json` not respected after Edit tool writes (Windows-prevalent) | OPEN | High | `/audit-policy-compliance` |
| [#47180](https://github.com/anthropics/claude-code/issues/47180) Cowork scheduled tasks ignore "Always Allow" | OPEN | High | `/audit-cowork` or extended `/audit-policy-compliance` |
| [#46681](https://github.com/anthropics/claude-code/issues/46681) Local-directory permissions copied to global settings | OPEN | Medium | `/audit-settings` |
| [#46978](https://github.com/anthropics/claude-code/issues/46978) Permission matcher does not auto-approve glob patterns | OPEN | Medium | `/audit-policy-compliance` |

### MCP

| Issue | State | Severity | Detector target |
|-------|-------|----------|-----------------|
| [#45551](https://github.com/anthropics/claude-code/issues/45551) MCP OAuth corrupts credential store; Team-plan concurrent sessions can wipe `claudeAiOauth` keychain entry, logging out the whole workspace | OPEN | Critical | new `/audit-mcp-auth` |
| [#44026](https://github.com/anthropics/claude-code/issues/44026) MCP toggle clears `disabledMcpServers`, process exhaustion | OPEN | High | `/review-mcp-server` or `/audit-mcp` |
| [#43789](https://github.com/anthropics/claude-code/issues/43789) MCP OAuth tokens expire, require manual `/mcp reconnect` | OPEN | Medium | `/audit-mcp-auth` |

### Plugin System

| Issue | State | Severity | Detector target |
|-------|-------|----------|-----------------|
| [#50655](https://github.com/anthropics/claude-code/issues/50655) Plugin-manifest index leak in pre-commit hooks causes phantom SHAs in `.git/index` | OPEN | Medium | `/review-plugin` |
| [#50232](https://github.com/anthropics/claude-code/issues/50232) Claude Code broke git authentication (unauthorized `gh auth setup-git`) | OPEN | High | `/audit-git-integration` |

### Hooks

| Issue | State | Severity | Detector target |
|-------|-------|----------|-----------------|
| [#34713](https://github.com/anthropics/claude-code/issues/34713) False "Hook Error" labels for exit-0 hooks (200–400 fake errors/session) | OPEN | Medium | `/review-hook` |
| [#23545](https://github.com/anthropics/claude-code/issues/23545) Docs incomplete for `TeammateIdle` + `TaskCompleted` JSON decision control | OPEN | Low | Docs |
| [#18392](https://github.com/anthropics/claude-code/issues/18392) Hooks in agent frontmatter not executed (only global/project hooks run) | OPEN | High | `/review-agent`, `/review-hook` |
| [#21988](https://github.com/anthropics/claude-code/issues/21988) PreToolUse hooks exit code ignored | **CLOSED 2026-01-30** | — | Already accounted for in `hook-evaluation-guide.md` PY-3/SR-4 (corrected 2026-04-14) |

### Stability & Performance

| Issue | State | Severity | Detector target |
|-------|-------|----------|-----------------|
| [#50187](https://github.com/anthropics/claude-code/issues/50187) Cowork process exits code 139 (SIGSEGV) on launch | OPEN | Critical | `/audit-stability` (future) |
| [#45931](https://github.com/anthropics/claude-code/issues/45931) TUI freeze at 250+ messages (ioctl TIOCSWINSZ loop) | OPEN | Medium | Session hygiene |
| [#49949](https://github.com/anthropics/claude-code/issues/49949), [#49163](https://github.com/anthropics/claude-code/issues/49163) Excessive token consumption on simple tasks (>10× budget) | OPEN | Medium | Cost hygiene |

### Security

| Issue | State | Severity | Note |
|-------|-------|----------|------|
| MCP protocol design flaw (disclosed 2026-04-16) — ~200K vulnerable servers; Anthropic declined architectural fix | OPEN (won't-fix) | Critical | Documented in `research/mcp-server-quality/mcp-server-configuration-quality.md` protocol-updates section |
| [#30731](https://github.com/anthropics/claude-code/issues/30731) Claude reads process env, hardcodes credentials in output | OPEN | Critical | `/audit-security` / settings scrubbing |
| [#34819](https://github.com/anthropics/claude-code/issues/34819) Full credential file contents displayed | OPEN | High | `/audit-security` |

## Detector Recipes (abridged)

### #39523 — Bypass-permissions contradiction

Detect `defaultMode: "bypassPermissions"` in any settings layer combined with write attempts to protected dirs (`.claude/`, `.git/`, `.vscode/`, `.idea/`, `.husky/`). Warn that protected dirs override bypass regardless of settings, VSCode `initialPermissionMode`, CLI flag, or PreToolUse hook `allow`.

### #41259 — Permissions cache-reload drift

Monitor Edit/Write targets for `settings.local.json` or `settings.json`. Compare in-memory permission cache timestamp against disk mtime; warn if disk is newer but cache not reloaded. Recommend session restart.

### #45551 — MCP OAuth credential-store race

macOS + Team plan + concurrent sessions (count >5): warn. Check single keychain entry `Claude Code-credentials` for size >2010 bytes (truncation risk). Cross-check `claudeAiOauth` entry existence before and after MCP OAuth operations.

### #47180 — Cowork scheduled-task permission-persistence

List scheduled tasks, extract per-task allow list, compare against global settings. Warn when divergent or when "Always allow" setting does not persist across task runs.

### #50655 — Plugin-manifest git-index leak

When reviewing a plugin that suggests `claude -p` invocation in pre-commit hooks: flag. Additionally inspect `.git/index` for phantom SHAs referencing `.claude-plugin/marketplace.json`.

## Input Normalization for All Detectors

Every detector normalizes inputs before regex match:
- Unicode NFC normalization.
- Case-folding (lowercase).
- Whitespace trim + collapse.
- Comment-stripping (JSON with `//` or `/* */` is not JSON — catch both).
- Key-case variants (`bypassPermissions`, `bypasspermissions`, `BYPASS_PERMISSIONS`).

Every detector ships with at least 5 adversarial test cases covering whitespace, case, Unicode, comment obfuscation, and split-value attacks.

## Refresh Cadence

Quarterly scan of `anthropics/claude-code` open issues with the `bug`, `permissions`, `hooks`, `mcp`, `plugin` labels. Closed issues removed from this file; new criticals appended under the relevant category section. `last_refreshed` bumped on each pass.

## Sources

Tier 1:
- `gh issue view <n> --repo anthropics/claude-code` for each issue — accessed 2026-04-19
- [The Register — Anthropic MCP Design Flaw](https://www.theregister.com/2026/04/16/anthropic_mcp_design_flaw) — 2026-04-16
- [claude-code releases](https://github.com/anthropics/claude-code/releases) — for fix-version verification
