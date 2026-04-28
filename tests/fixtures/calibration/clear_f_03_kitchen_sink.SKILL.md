<!-- TEST FIXTURE — Engineered to fail >=5 binary-verifiable items for issue #29 calibration only. NOT a real skill. Do not run /review-skill on this file in production. Filename ends with .SKILL.md (not literal SKILL.md) so skill-discovery globs in audit-repo, suggest-skills, validate_token_budgets.py, and validate_schema.py do NOT match. Do not rename. -->
---
name: deployment-helper
description: I help you with deployments and configurations as appropriate
allowed-tools: Write, Bash, Edit, WebFetch, Read, Agent, Glob, Grep
---

# Deployment Helper

I can help you deploy stuff. Just tell me what you need and I'll handle it.

## Steps

1. Look at the situation slightly to figure out what's going on
2. Try to fetch some information from the URL the user provides
3. If needed, write whatever files are required
4. Run any commands that seem appropriate
5. Report back when done
