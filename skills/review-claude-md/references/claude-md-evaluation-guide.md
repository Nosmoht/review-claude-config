---
name: claude-md-evaluation-guide
description: Type-specific evaluation criteria for CLAUDE.md files across 4 dimensions
last_refreshed: 2026-04-07
---

# CLAUDE.md Evaluation Checklist

Answer EVERY item: PASS | FAIL | NA. No skipping. FAILs map to Dim for scoring.

## Clarity

| ID | Check | Dim |
|----|-------|-----|
| CL-1 | Instructions use imperative or must/always/never language rather than "should", "try", or "prefer"? | Clarity |
| CL-2 | Each instruction is self-contained — no implicit knowledge required to act on it? | Clarity |
| CL-3 | Section headings match their content (no misleading titles)? | Clarity |
| CL-4 | Conditional instructions specify explicit criteria ("when X, do Y" not "if needed, do Y")? | Clarity |
| CL-5 | No aspirational statements that describe intent without prescribing behavior? | Clarity |

## Completeness

| ID | Check | Dim |
|----|-------|-----|
| CO-1 | Project purpose or scope is stated (what this project is and what it does)? | Compl |
| CO-2 | Architecture or key file locations described so Claude can navigate without guessing? | Compl |
| CO-3 | Command inventory present (list of available slash commands or make targets)? | Compl |
| CO-4 | Development conventions documented (language, style, testing approach)? | Compl |
| CO-5 | Cross-project or external dependencies noted (other repos, APIs, env vars)? | Compl |
| CO-6 | Working guidelines or collaboration rules present (what to do and not do)? | Compl |

## Context Engineering

| ID | Check | Dim |
|----|-------|-----|
| CE-1 | No content duplicated between sections (each piece of information appears once)? | CE |
| CE-2 | No information derivable by reading the code (e.g., language version, file count) stated redundantly? | CE |
| CE-3 | No boilerplate preamble ("This file provides guidance…") before actionable content? | CE |
| CE-4 | Lists and tables used in preference to prose paragraphs for reference content? | CE |
| CE-5 | Instructions scoped to what Claude actually needs — no historical context unless it changes behavior? | CE |
| CE-6 | Reference files or external docs linked rather than their content inlined where appropriate? | CE |

## Goal Alignment (Command Inventory + Freshness)

| ID | Check | Dim |
|----|-------|-----|
| GA-1 | Every listed command resolves to an existing file (verified by Glob)? | Goal |
| GA-2 | No listed command points to a file that has been renamed or deleted? | Goal |
| GA-3 | File paths referenced in the body (e.g., architecture paths, key files) exist on disk? | Goal |
| GA-4 | Section content reflects the current state of the project (no obviously stale entries)? | Goal |
| GA-5 | Instructions would produce correct Claude behavior for this specific project (not generic advice)? | Goal |
| GA-6 | The CLAUDE.md would allow a fresh Claude session to orient correctly without additional prompting? | Goal |
