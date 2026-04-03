# suggest-skills

Analyze a repository's structure, workflows, and documentation to identify missing Claude Code skills. Produces a prioritized report with rationale and skeleton SKILL.md for each suggestion. Uses two-layer analysis: deterministic table-based signal matching plus heuristic open reasoning with validation gates and explicit uncertainty labels.

## Overview

| Property | Value |
|----------|-------|
| **Name** | suggest-skills |
| **Location** | `skills/suggest-skills/SKILL.md` |
| **Type** | Discovery |
| **Allowed Tools** | Agent, Read, Write, Glob, Grep, WebSearch, WebFetch |
| **disable-model-invocation** | true |
| **Argument Hint** | `[folder]` |
| **Mode** | Standalone only |

## Purpose

The skill answers the question: "What Claude Code skills should this repository have but doesn't?" It takes a target folder, scans its structure, classifies the repository type, and runs two complementary analysis layers -- one deterministic (table matching) and one heuristic (open reasoning with web validation). The result is a prioritized list of skill suggestions, each backed by concrete evidence, labeled with `evidence_class` and `confidence`, and accompanied by a skeleton SKILL.md.

The skill is strictly read-only on the target repository. It writes only to `.claude/reviews/` when persisting a report.

## Process Steps

### Phase 1 -- Setup and Discovery

**Step 0: Tool availability checks.** The skill attempts a trivial WebSearch query ("Claude Code documentation") to test whether WebSearch is available. If the call fails, `websearch_available` is set to false. It then attempts a trivial WebFetch against `https://docs.anthropic.com`. If that fails, `webfetch_available` is set to false. When WebSearch is unavailable, Layer 2 suggestions are generated from model knowledge only and marked `[no web verification]`.

**Steps 1-2: Launched in parallel.**

**Step 1: Load references.** The skill reads its own reference file:

- `references/signal-catalog.md` -- signal patterns organized into Application and Skills Repository signal tables, plus the 4 extraction criteria used in Layer 2.

It also looks for the shared domain cache from the `review-claude-config` sibling skill:

- `references/domain-cache/INDEX.md` -- cached domain research entries available for reuse. If the file is not found, the skill continues without it (no error).

**Step 2: Repository Scan Agent.** An Agent subagent (allowed tools: Glob, Grep, Read) scans the target repository and collects structured facts across 6 categories. The agent returns facts only -- no interpretations or skill suggestions.

| Category | What It Collects |
|----------|------------------|
| **A: Documentation** | CLAUDE.md processes, `.claude/rules/` entries, README workflows, onboarding instructions |
| **B: Existing Skill/Agent Coverage** | Inventory of all skills and agents already present (paths, names, purposes) |
| **C: Tech Stack** | Languages, frameworks, infrastructure tools, package manifests |
| **D: CI/CD & Automation** | Pipelines, build targets, Makefiles, scripts, GitHub Actions |
| **E: Git Conventions** | Static files: `.gitignore`, `CODEOWNERS`, PR/issue templates, commit hooks |
| **F: Quality & Config** | Linting configs, test frameworks, formatting tools, type checking |

Scan limits: at most 50 lines per file, at most 3 directory levels deep. For very large repositories (>1000 files at top level), the agent focuses on root-level config files and the first level of subdirectories.

**Step 3: Classify repo type.** Based on scan results, the skill classifies the repository into one of three types:

| Type | Criteria | Signal Table Used |
|------|----------|-------------------|
| **Application** | Has application code, services, APIs, or user-facing features | Application signal table |
| **Skills-Config** | Primarily contains Claude Code skills, agents, rules, and configuration | Skills Repository signal table |
| **Mixed** | Contains both application code and significant Claude Code configuration | Both signal tables |

The classification determines which signal table(s) are applied in Phase 2.

### Phase 2 -- Signal Analysis

**Step 0: Build coverage map.** Before running either analysis layer, the skill maps existing skills (from Category B) to workflows and domains they cover. When a potential suggestion overlaps more than 60% with an existing skill, it is classified as an "enhancement" to the existing skill rather than a "new" suggestion. This prevents recommending skills that already exist under a different name.

**Step 1: Layer 1 -- Table-Based Signal Matching.** An Agent subagent (allowed tools: Agent, Read only) performs deterministic matching of scan results against the applicable signal table(s) from the signal catalog. For each signal pattern that matches:

1. Record the signal name and the concrete evidence from the scan.
2. Check the match against the existing skill inventory (Category B).
3. If no existing skill covers it, generate a suggestion.

The agent returns a structured table:

| Column | Content |
|--------|---------|
| Signal | The signal pattern name from the catalog |
| Match | Whether the signal was found in the repository |
| Evidence | Concrete file paths or configuration entries |
| Existing Coverage | Which existing skill (if any) already covers this |
| Suggestion | The recommended skill name and brief description |

Layer 1 performs no web research. It is purely deterministic, matching repository signals against known patterns from the repo-maintained signal catalog.

**Step 2: Layer 2 -- Open Reasoning.** An Agent subagent (allowed tools: Agent, WebSearch, WebFetch, Read) reasons heuristically about gaps that the signal table cannot catch. It looks for four types of gaps:

- **Workflow gaps** -- multi-step processes described in documentation but not automated by any skill
- **Domain gaps** -- domain-specific best practices that the repository's tech stack would benefit from
- **Lifecycle gaps** -- missing stages in the development lifecycle (testing, deployment, monitoring, etc.)
- **Cross-cutting gaps** -- patterns that span multiple categories (e.g., security, performance, accessibility)

For each identified opportunity:

1. Conduct 1-2 WebSearch queries to validate that the domain has established practices worth encoding.
2. If WebFetch is available, fetch 1-2 relevant URLs for deeper content.
3. Apply the 4 extraction criteria:

| Criterion | Description |
|-----------|-------------|
| **Recurrence** | Does this task repeat across projects or development cycles? |
| **Verification** | Can the output be checked for correctness? |
| **Non-obviousness** | Does it require domain knowledge that is not immediately available? |
| **Generalizability** | Would this skill be useful beyond just this repository? |

A suggestion must pass at least 3 of 4 criteria to proceed. This is a repo-level decision rule, not a universal science of skill-gap detection.

4. Generate a skeleton SKILL.md for each suggestion that passes the criteria gate.

### Phase 3 -- Consolidation and Prioritization

**Step 1: Deduplicate.** Merge overlapping suggestions from Layer 1 and Layer 2. When two suggestions target the same workflow or domain, combine them into a single entry with the stronger evidence.

**Step 2: Score.** Each surviving suggestion is scored on three axes:

| Axis | Scale | What It Measures |
|------|-------|------------------|
| **Signal** | 1-3 | Strength of evidence from repository signals |
| **Impact** | 1-3 | Expected value of the skill to the development workflow |
| **Feasibility** | 1-3 | How straightforward the skill is to implement |

Priority is the sum of all three scores:

| Priority | Score Range |
|----------|-------------|
| High | 7-9 |
| Medium | 4-6 |
| Low | 1-3 |

**Step 3: Filter.** Apply final filters:

- Cap at 10 suggestions maximum.
- Drop suggestions scoring below 4, unless fewer than 3 suggestions would remain (keep at least 3 if available).
- Apply false positive gates -- reject suggestions that are:
  - Single-command operations (too simple for a skill)
  - Based on no concrete evidence combined with weak signal strength
  - Fail the Generalizability criterion (too repository-specific)

### Phase 4 -- Presentation and Persistence

**Step 1: Full report.** The skill presents the complete report to the user containing:

- **Repo Overview** -- repository type classification, tech stack summary, existing skill count
- **Suggestions** -- each suggestion includes:
  - Signal Sources (which categories and signals contributed)
  - Evidence Class and Confidence
  - Extraction Criteria results (which of the 4 criteria passed)
  - Rationale (why this skill would be valuable)
  - Skeleton SKILL.md (explicitly marked as a starting point)
  - Reference Files (if applicable, what reference files the skill would need)
- **Signal Summary table** -- consolidated view of all signals checked and their status
- **Integration Notes** -- how the suggested skills relate to each other and to existing skills

**Step 2: Persist.** Write the report to `.claude/reviews/YYYY-MM-DDTHHMMSS-suggest-skills.md` with YAML frontmatter.

**Step 3: Commit and menu.** Suggest a commit message (`docs(reviews): add YYYY-MM-DDTHHMMSS suggest-skills report`) and present the "What's next?" menu:

1. Scaffold a suggested skill -- `/scaffold-skill`
2. Run a full config review -- `/review-claude-config`
3. Done

## Research Behavior

- **Layer 1:** No web research. Signal matching is deterministic and uses only the signal catalog and scan results.
- **Layer 2:** 1-2 WebSearch queries per suggestion to validate that the identified domain has established practices worth encoding as a skill. If WebFetch is available, it fetches 1-2 full articles for deeper content. If neither web tool is available, suggestions are generated from model knowledge and marked `[no web verification]`. Layer 2 remains heuristic even when web-validated.

## Reference Files

| File | Location | Purpose |
|------|----------|---------|
| `references/signal-catalog.md` | Own skill directory | Application + Skills Repository signal tables, extraction criteria |
| `references/domain-cache/INDEX.md` | `review-claude-config/references/` (shared) | Cached domain research for reuse across skills |

## Interactions

| Direction | Target | Notes |
|-----------|--------|-------|
| Called by | User directly | Standalone invocation only |
| Calls | Nothing | Suggests `/scaffold-skill` via menu |
| Shares references with | `/audit-repo` | Signal catalog (`signal-catalog.md`) |
| Shares references with | `/review-claude-config` | Domain cache |

## Hard Rules

1. **Read-only on the target repository.** Never modify any file in the analyzed repository. Write only to `.claude/reviews/`.
2. **Every suggestion needs evidence.** Each suggestion must cite a concrete signal (file path, configuration entry, documentation excerpt) and be web-validated or explicitly marked `[no web verification]`.
3. **No duplicates.** Cross-check every suggestion against the existing skill inventory (Category B). Overlapping coverage (>60%) becomes an enhancement note, not a new suggestion.
4. **Extraction criteria gate.** Layer 2 suggestions must pass at least 3 of 4 extraction criteria (Recurrence, Verification, Non-obviousness, Generalizability).
5. **Expose uncertainty honestly.** Every suggestion must carry `evidence_class` and `confidence`, and inference-heavy suggestions must stay labeled as heuristic or repo policy where appropriate.
6. **Skeletons are starting points.** Every skeleton SKILL.md in the report is explicitly marked as a draft that requires customization.
7. **Present all before follow-up.** The full report is shown to the user before any "What's next?" actions are offered.

## Output Format

The skill produces a report in this structure:

```
## Repo Overview
- **Type:** [Application | Skills-Config | Mixed]
- **Tech Stack:** [summary]
- **Existing Skills:** [count] ([list])

## Suggestions

### 1. [Skill Name] (Priority: [High/Medium/Low], Score: [N])

**Evidence Class:** [Proven result | Engineering guidance | Repo default | Low-evidence area]
**Confidence:** [High/Medium/Low]
**Signal Sources:** [category codes and signal names]
**Extraction Criteria:** Recurrence [pass/fail], Verification [pass/fail], Non-obviousness [pass/fail], Generalizability [pass/fail]
**Rationale:** [Why this skill would be valuable]
**Reference Files:** [What reference files the skill would need, if any]

<details><summary>Skeleton SKILL.md (starting point)</summary>

[YAML frontmatter + basic structure]

</details>

### 2. [Skill Name] ...

## Signal Summary

| Signal | Table | Match | Evidence | Suggestion |
|--------|-------|-------|----------|------------|
| ... | ... | ... | ... | ... |

## Integration Notes
[How suggested skills relate to each other and to existing skills]
```
