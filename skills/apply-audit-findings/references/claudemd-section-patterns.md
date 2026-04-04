---
name: claudemd-section-patterns
description: Rules for matching audit interventions to CLAUDE.md sections and determining placement
last_refreshed: 2026-03-26
---

## Section Matching

Map the intervention's error class to a target section header in CLAUDE.md:

| Error Class | Target Section | Fallback Headers |
|-------------|---------------|------------------|
| Toolchain | `## Commands` | `## Development`, `## Build`, `## Scripts` |
| Navigation | `## Architecture` | `## Structure`, `## Layout` |
| Architecture | `## Architecture` | `## Design`, `## Structure` |
| Convention | `## Working Guidelines` | `## Conventions`, `## Code Style`, `## Development Conventions` |
| Domain | `## Key Domain Concepts` | `## Domain`, `## Glossary`, `## Concepts` |
| Security | `## Working Guidelines` | `## Security`, `## Conventions` |
| Repetition | `## Commands` | `## Workflows`, `## Development` |

If a matching header exists, append the new content below that section (before the next `##` heading).

## New Section Placement

If no matching header exists, create a new `##` section. Insert it:
1. After existing content sections
2. Before trailing reference sections (`## Research References`, `## Sources`, `## Links`)
3. If no trailing sections, append at the end

## Deduplication

Before appending, grep the existing CLAUDE.md for 3+ consecutive key terms from the new content. If found:
- Show the existing text to the user
- Warn: "Similar content may already exist at line N"
- Ask whether to append anyway, skip, or replace
