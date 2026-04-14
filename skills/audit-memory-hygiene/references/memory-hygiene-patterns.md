---
name: memory-hygiene-patterns
description: Detection patterns for memory file poisoning, staleness, credential leaks, and growth bounds
last_refreshed: 2026-04-14
---

# Memory Hygiene Patterns

## Check Types

| ID | Check | Severity | Heuristic |
|---|---|---|---|
| MH-1 | Stale entry | Medium | Frontmatter date >90 days old or absent |
| MH-2 | Injection artifact | High | Body has ≥2 imperative starts (Always/Never/You must/Do not) OR system syntax (`<system>`, `[INST]`) |
| MH-3 | Credential leak | High | Body matches: `sk-`, `AKIA`, `ghp_`, `gho_`, `xoxb-`, `password=`, `token=`, `secret=`, base64 >40 chars |
| MH-4 | Contradiction | Medium | Two files assert conflicting values for same subject (X is A vs X is B) |
| MH-5 | Growth bound | Low | Total memory >10K tokens (est: words * 1.3) or >50 files |
| MH-6 | Missing provenance | Medium | File has no YAML frontmatter or missing `type`/`name`/`description` fields |

## Credential Patterns (Grep-ready)

```
sk-[a-zA-Z0-9]{20,}
AKIA[A-Z0-9]{16}
ghp_[a-zA-Z0-9]{36}
gho_[a-zA-Z0-9]{36}
xoxb-[0-9]{10,}
password\s*[=:]\s*\S+
token\s*[=:]\s*\S+
secret\s*[=:]\s*\S+
```

## Injection Artifact Patterns

```
^(Always|Never|You must|Do not|Ignore)\b
<system>|</system>|\[INST\]|\[/INST\]|<\|im_start\|>
^(You are a|Act as|Pretend to be)\b
```
