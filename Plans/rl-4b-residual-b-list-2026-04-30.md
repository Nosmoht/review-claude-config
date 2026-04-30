# RL-4b Residual Genuine-FAIL Subset (post #111)
Generated from `python3 scripts/audit_suite.py --show-fail-paths`.
For follow-up under #90.

| Path | Tool/Command | Triage note |
|------|-------------|-------------|
| `skills/audit-mcp-auth/SKILL.md` | (no Write to internal report path) | Class B — autonomous one-time keychain-bug detector; body does not reference $CLAUDE_PLUGIN_DATA output path, so NA-rescue cannot fire; needs HITL clause or explicit report-path mention |
| `skills/refresh-evidence-coverage/SKILL.md` | Edit | Class B — autonomous evidence-coverage updater; Edit in allowed-tools makes it a mutating skill that genuinely requires HITL gating |
