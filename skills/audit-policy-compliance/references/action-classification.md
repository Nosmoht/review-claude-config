---
name: action-classification
description: Five-level action taxonomy mapping tools to authorization levels for policy enforcement
last_refreshed: 2026-04-14
---

# Action Classification Model

## Authorization Levels

| Level | Label | Default |
|---|---|---|
| L1 | Read | Allow |
| L2 | Analyze | Allow |
| L3 | Recommend | Allow |
| L4 | Act | Ask |
| L5 | Irreversible | Deny |

## Tool Mapping

| Tool | Level | Notes |
|---|---|---|
| Read, Glob | L1 | No side effects |
| Grep, WebSearch, WebFetch | L2 | Computation/query |
| AskUserQuestion | L3 | User decides |
| Edit, Write, MultiEdit, Agent | L4 | State change |
| Bash | L4* | *L5 if matches destructive pattern |
| MCP tools | L1 / L4 | L1 for `list_`/`get_`/`retrieve_`/`search_` prefixes and `_read` suffix; L4 for `create_`/`update_`/`delete_`/`archive_`/`unarchive_`/`add_`/`remove_`/`transfer_`/`assign_`/`merge_`/`push_`/`fork_`/`request_` prefixes and `_write` suffix; L4 default for unknown suffixes |

## Bash → L5 Escalation Patterns

`rm -rf`, `git push --force`, `git reset --hard`, `docker rm`, `kubectl delete`, `DROP TABLE`, `DELETE FROM`, `deploy`, `publish`, `release`

## Policy Rule Format

Stored in `$CLAUDE_PLUGIN_DATA/policy.json`:
```json
{
  "rules": [{"level": "L4", "action": "ask"}],
  "overrides": [{"tool": "Write", "path_pattern": "reports/*", "action": "allow"}]
}
```

No policy.json = pass-through (zero enforcement). Default when file exists: L1-L3 allow, L4 ask, L5 deny.
