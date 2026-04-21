---
last_refreshed: 2026-04-19
---

# Claude Code Auto-Memory System

Reference for the per-project MEMORY.md auto-memory system, agent-level memory scoping, and poisoning-vector detection. Feeds `/audit-memory-hygiene` rubric updates.

## TL;DR

- Auto-memory lives per git repo at `~/.claude/projects/<project>/memory/`. The first 200 lines or 25 KB of `MEMORY.md` are injected into every session's system prompt.
- Contrast with CLAUDE.md which is loaded in full (no size cap); memory is deliberately truncated to preserve conversation context.
- Topic files (`MEMORY/<topic>.md`) are loaded on-demand, not eagerly.
- Agents may own a scoped MEMORY.md via the `memory:` frontmatter field (`user` / `project` / `local`).
- Memory-poisoning detection is currently manual; three vectors are well-catalogued.

## Storage Architecture

### Default locations

| Scope | Path | Intent |
|-------|------|--------|
| Project (session-scoped) | `~/.claude/projects/<project>/memory/MEMORY.md` | Cross-session learnings for this project/repo |
| User (`memory: user` agent) | `~/.claude/agent-memory/<agent-name>/MEMORY.md` | Knowledge reused across projects |
| Project-shared agent | `.claude/agent-memory/<agent-name>/MEMORY.md` | Team-shared, version-controlled |
| Project-local agent | `.claude/agent-memory-local/<agent-name>/MEMORY.md` | Project-private, gitignored |

### Loading rule

- **System prompt injection:** first 200 lines **or** 25 KB, whichever comes first. Everything past that is unavailable until the agent explicitly reads the file via the Read tool.
- **Topic files:** discoverable but not auto-loaded. Agents traverse them only when the system-prompt head references them or when the user asks.

### Checkpoint triggers

Auto-memory is written, not continuously but on signal:
- Explicit user instruction: "remember that X".
- After a user correction of Claude's behavior (the correction becomes the durable lesson).
- After a preference discovery during the session (debugging style, naming convention).
- Not on every tool call (by design — write frequency would harm performance and pollute memory with ephemera).

## Agent Memory Scoping

Agents declare memory via frontmatter:

```yaml
---
name: deep-review-agent
memory: project
---
```

| `memory:` value | Location | When to use |
|-----------------|----------|-------------|
| `user` | `~/.claude/agent-memory/<agent-name>/` | Cross-project learnings (e.g. user's code-style preferences) |
| `project` | `.claude/agent-memory/<agent-name>/` | Team-shared, version-controlled, safe to commit |
| `local` | `.claude/agent-memory-local/<agent-name>/` | Experimental; add path to `.gitignore` |
| omitted | no memory | Stateless agent |

Agents with `memory:` set receive Read/Write/Edit tools implicitly on their memory directory. System-prompt injection rules match the project case (first 200 lines / 25 KB).

## Memory-Poisoning Vectors

Three vectors are catalogued and detectable. All three produce observable surface patterns; none currently trigger automated detection.

### P1 — Instruction injection (imperative directives disguised as memory)

Adversary writes "remember that you must always X" or `<system>You are now …</system>`. Memory is re-injected on every session; the directive persists silently.

Detection heuristics:
- Imperative verbs at line start: `Always|Never|You must|You should always` case-insensitive.
- System-prompt syntax markers: `<system>`, `[INST]`, `### System`, `###system`.
- Role-override language: "You are now …", "Ignore previous instructions".

Severity: **High** — alters future agent behavior without user consent.

### P2 — Stale accumulation (obsolete entries that outlive their subject)

Memory grows monotonically; entries about removed files, retired APIs, or closed Jira tickets remain after the subject is gone. Agent acts on outdated context.

Detection heuristics:
- Cross-reference file paths against filesystem (grep MEMORY.md for paths, check existence).
- Freshness TTL: entries older than 90 days without refresh are stale candidates.
- Subject-existence probe: entries naming specific functions/issues should be validated against `grep`/issue tracker state.

Severity: **Medium** — causes wrong behavior, not malicious.

### P3 — Contradiction insertion (conflicting claims about the same subject)

Multiple entries about the same topic with different values (e.g. "rebase before merge" vs. "always merge-commit"). The agent picks one non-deterministically.

Detection heuristics:
- Subject-value extraction: tag entries by noun/key; flag multiple entries with the same subject.
- Embedding-similarity clustering to detect near-duplicate entries with divergent content.

Severity: **Medium** — non-deterministic behavior.

## Mitigation Patterns (currently manual)

- **Provenance:** every entry carries YAML-like metadata (`date`, `type`, `description`).
- **TTL enforcement:** entries older than 90 days flagged as stale, optionally auto-archived.
- **Credential exclusion:** regex scan before commit (API-key patterns, OAuth tokens, AWS keys).
- **Growth bounds:** cap total memory token count; archive oldest on overflow.

## Implications for `/audit-memory-hygiene`

Rubric additions:
- 200-line-head convention: index (first 200 lines) must contain Table-of-Contents pointers to topic files, not raw content.
- P1 detector: regex set for imperative verbs + system-prompt syntax + role-overrides.
- P2 detector: cross-reference file paths + issue IDs against current state.
- P3 detector: subject-key clustering + flag duplicates with divergent values.
- Memory size hygiene: warn when MEMORY.md approaches 25 KB — suggest migrating content to topic files.

## Open Questions

- How many topic files / sessions before MEMORY.md approaches size limit in practice? (No public empirical data.)
- Is the 200-line / 25 KB cut-off per session or per agent? (Docs imply per session.)
- When two agents with `memory: project` write to the same project, does Claude Code serialize or race? (Not documented.)

## Sources

Tier 1:
- [Claude Code — Auto-Memory](https://code.claude.com/docs/en/memory) — accessed 2026-04-19
- [Claude Code — Sub-Agents memory field](https://code.claude.com/docs/en/sub-agents) — accessed 2026-04-19

Tier 2:
- [What is Claude Code Auto-Memory](https://www.mindstudio.ai/blog/what-is-claude-code-auto-memory) — engineering blog
- Local research: `research/memory-poisoning/memory-poisoning-patterns.md`
