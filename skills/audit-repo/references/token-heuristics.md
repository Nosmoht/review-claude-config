---
name: token-heuristics
description: Thresholds and scoring formulas for token efficiency analysis
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

| Lines | Classification | Intervention |
|-------|---------------|-------------|
| >500 | Token sink | CLAUDE.md hint: "relevant logic in lines X-Y" |
| >1000 | Critical | Scope restriction + refactoring note |
| >2000 | Severe (~3K+ tokens/read) | Active intervention required |

## Navigation Sprawl Score

Formula: `max_depth × max_files_per_dir × naming_collision_score`

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

| Task Type | Estimated Tokens |
|-----------|-----------------|
| Simple edit (known location) | 5-20K |
| Exploration + edit | 40-80K |
| Multi-file refactor | 100-300K |

Effective context capacity: 60-70% of nominal window. Lost-in-the-middle: 30%+ accuracy drop for middle-positioned information.
