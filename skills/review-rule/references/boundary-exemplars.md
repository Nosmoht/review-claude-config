---
name: boundary-exemplars
description: PASS/FAIL boundary examples for rule evaluation checklist items — reduces verdict variance
last_refreshed: 2026-04-14
---

# Boundary Exemplars

## CL-1 — Rule contains no term that admits two plausible opposite actions?

**PASS:** "Never commit files matching `*.env` or `credentials.json`."
**FAIL:** "Keep sensitive files secure." ("secure" admits both encrypt-in-repo and exclude-from-repo)

## CL-2 — Terms precisely defined (no "appropriate", "good", "reasonable")?

**PASS:** "Commit messages must use the format `type(scope): description` with scope matching a top-level directory name."
**FAIL:** "Write good commit messages with an appropriate scope."

## GA-5 — All constraints needed for stated goal are present?

**PASS:** Goal: "Block commits without ticket ID." Rule: "Commit message first line must match `^[A-Z]+-[0-9]+: .+`." — format, position, and pattern all specified.
**FAIL:** Goal: "Block commits without ticket ID." Rule: "Commit messages should reference a ticket." — no format, no enforcement point, no error guidance.
