---
last_refreshed: 2026-05-02
---

# Meta-Review Threat Model

This document catalogues threats that arise *against the reviewer* when
ingesting, processing, and acting on reviewed content. The
`skills/review-claude-config/references/injection-surface-catalog.md`
addresses subject-side patterns (IJ-1 / IJ-2) — threats *inside* the
artifact being reviewed. This document addresses the complementary
meta-review surface: the reviewer itself is the attack target. All four
threat classes below represent variants of OWASP LLM01:2025 (Prompt
Injection) adapted to the review-workflow context.

## Reviewed-Artifact Injection

When the review skill reads a skill, agent, rule, or hook file, the
content of that file enters the model's context as quasi-trusted input.
An adversarially authored artifact can embed imperative text — `<system>`
tags, "Always do X", "Ignore prior instructions", inline role assignments
("You are now a…") — that exploits the instruction-hierarchy ambiguity
present in V2 indirect injection (see
`research/injection-taxonomy/injection-taxonomy.md` line 36–44). Because
the reviewer has no separate parse layer that strips instruction-like
content before it reaches the model, a sufficiently crafted artifact can
alter grading behaviour, suppress findings for a sibling artifact, or
cause the review report to omit a dimension entirely. AgentDojo
(arXiv:2406.13352) demonstrated that injection via tool-returned content
achieves high task-hijack rates even on instruction-following-hardened
models. The current plugin defence relies exclusively on Claude's
built-in instruction hierarchy (V1 inheritance); no additional
reviewer-context sandboxing exists at the plugin layer.

**Sources:** OWASP LLM01:2025; AgentDojo arXiv:2406.13352.

## Apply-Flow Mutation

Apply-skills (`/apply-review-findings`, `/apply-skill-review-findings`,
etc.) mutate target files directly based on findings extracted from a
review report. If the review report contains poisoned or fabricated
findings — introduced either by a prior reviewed-artifact injection
event or by direct report tampering — those findings drive real file
mutations with no subsequent validation gate. The Progent containment
framework (arXiv:2504.11703) identifies this as the "lethal trifecta"
configuration: untrusted input (the review report) feeds a privileged
action (file write via Edit/Write tools) without a deterministic
blast-radius boundary. Today's only mitigations are the confirmation
gates documented at `CLAUDE.md` line 219 and the operator-readable
change preview in apply-flow prompts; no automated policy that limits
apply scope to files named in the original issue, or that caps the
number of lines changed per apply run, is currently codified.

**Sources:** OWASP LLM01:2025; Progent arXiv:2504.11703.

## Report Poisoning

A review report (stored as Markdown with optional sidecar JSON under
`${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`) is itself consumed by
downstream flows: apply-skills read it, `/review-analytics` aggregates
it, and future review sessions may load prior reports for context.
Fabricated grade values, false-negative findings, or injected
high-severity findings in a report body propagate silently through all
these consumers. The audit (§10.2, line 463–465) flagged
Scheinpräzision — false precision in grade values — as a credibility
erosion path; an adversary exploiting this surface need not compromise
the review model itself but only needs to write a plausible-looking
Markdown file in the expected output location. The sidecar JSON is
schema-validated by `validate_schema.py`, providing partial structural
integrity; however the Markdown body is free-form with no signature or
cryptographic authenticity check, leaving the human-readable portion
of every report open to silent modification.

**Sources:** OWASP LLM06:2025; AgentDojo arXiv:2406.13352.

## Stale-Evidence Poisoning

The plugin's scoring decisions rely on several layers of persistent
evidence: the `engineering-baseline.md` values, the seven
`references/domain-cache/` entries, and per-file `last_refreshed`
timestamps throughout `skills/review-claude-config/references/`. When
these entries drift — references citing superseded standards, baseline
values reflecting outdated benchmarks, or domain-cache entries
summarising retracted research — they silently corrupt the grading
calibration for every review performed in that window. This is the P2
stale-accumulation pattern from
`research/memory-poisoning/memory-poisoning-patterns.md` (line 39–45):
the agent acts on an outdated picture of reality, producing systematically
miscalibrated findings without any visible error signal. MCPTox
(arXiv:2508.14925) documented how data-source freshness erosion across
MCP servers produces analogous cross-session drift at the tool-output
layer; the same mechanism applies to this repo's in-repo evidence layer.
The current 90-day refresh cadence and `session_check.py` freshness
warnings are soft controls that report staleness but do not fail the
review pipeline.

**Sources:** OWASP LLM01:2025; MCPTox arXiv:2508.14925.

## Mitigation Mapping

| Threat | Existing control | Control location | Coverage gap |
| --- | --- | --- | --- |
| Reviewed-Artifact Injection | IJ-1 / IJ-2 rubric checks | `skills/review-claude-config/references/injection-surface-catalog.md` (line 11–32) | Subject-side only; reviewer-context defences rely on Claude instruction-hierarchy (V1 inheritance); no plugin-layer sandboxing exists |
| Apply-Flow Mutation | Confirmation gates on apply-* skills | `CLAUDE.md` line 219 (`Apply skills and scaffold-skill modify files and require confirmation gates`) | No deterministic blast-radius gating; auto-apply scope policy not codified (audit §12.3 R1 deferred) |
| Report Poisoning | Read-only review/audit skills + reports under `${HOME}/.claude/plugins/data/claude-config/reports/` | `CLAUDE.md` line 218 + `skills/review-claude-config/references/review-report-contract.md` | Sidecar JSON schema-validated; Markdown body free-form with no signature or authenticity check |
| Stale-Evidence Poisoning | `last_refreshed` freshness checks | `skills/check-repo-health/SKILL.md` (line 40–49) + 90-day refresh cadence | Soft warning only for non-baseline files (`session_check.py` per `CLAUDE.md` line 212); no hard fail gate on stale evidence |
