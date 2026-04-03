---
name: token-heuristics
description: Repo token-efficiency heuristics and evidence-informed thresholds for audit-repo
---

## Token Density by Language

| Language | Tokens/Line | Notes |
|----------|------------|-------|
| Python | ~10 | Moderate density |
| JavaScript/TypeScript | ~7 | Lower due to syntax tokens |
| Rust/C++ | ~12-15 | Type annotations increase density |
| Go | ~8 | Compact syntax |
| SQL | ~11.5 | Query-heavy |

## File Size Thresholds

These thresholds are `Repo default` operating cutoffs informed by context-efficiency guidance. They are useful decision aids, not universal scientific constants.

| Lines | Classification | Intervention |
|-------|---------------|-------------|
| >500 | Token sink | CLAUDE.md hint: "relevant logic in lines X-Y" |
| >1000 | Critical | Scope restriction + refactoring note |
| >2000 | Severe (~3K+ tokens/read) | Active intervention required |

## Navigation Sprawl Score

Formula: `max_depth × max_files_per_dir × naming_collision_score`

This score is a repo heuristic for navigation risk, not a benchmark-backed universal metric.

| Score | Action |
|-------|--------|
| >100 | Architecture map with entry points needed (P0) |
| 30-100 | Selective hints for ambiguous paths |
| <30 | No navigation intervention needed |

Naming collision: count identical class/function names across packages. Score = count of names appearing in 2+ locations.

## Build Error Verbosity

| Toolchain | Verbosity | Typical Output |
|-----------|-----------|---------------|
| Webpack/Vite/Turbopack | Extreme | >500 lines per error |
| Rust compiler | Verbose | Informative but long spans |
| TypeScript tsc | Medium | Cascading type errors |
| Go compiler | Compact | One line per error |

## Context Burn Rate

These burn-rate bands are heuristic operating ranges synthesized from context-engineering guidance and local repo policy.

| Task Type | Estimated Tokens |
|-----------|-----------------|
| Simple edit (known location) | 5-20K |
| Exploration + edit | 40-80K |
| Multi-file refactor | 100-300K |

Effective context capacity: 60-70% of nominal window. Lost-in-the-middle: 30%+ accuracy drop for middle-positioned information.
Treat the exact percentages as evidence-informed guidance rather than fixed guarantees for every model/runtime combination.
