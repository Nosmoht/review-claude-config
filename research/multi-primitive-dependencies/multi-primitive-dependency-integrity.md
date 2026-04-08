---
last_refreshed: 2026-04-08
---

# Multi-Primitive Dependency Integrity in Claude Code

## Provenance Metadata

- Strongest source tier: Tier 1
- Source basis: Anthropic official documentation (code.claude.com, platform.claude.com) + verified GitHub issue reports from anthropics/claude-code + Tier 2 production case studies and tooling (SkillCheck, claude-rules-doctor, agnix, Medium engineering post)
- Last reviewed: 2026-04-08

**Sources:**
- [Extend Claude with skills — Claude Code Docs](https://code.claude.com/docs/en/skills) (Tier 1 — Anthropic official)
- [Hooks reference — Claude Code Docs](https://code.claude.com/docs/en/hooks) (Tier 1 — Anthropic official)
- [BUG: PreToolUse hooks exit code ignored — anthropics/claude-code #21988](https://github.com/anthropics/claude-code/issues/21988) (Tier 2 — production bug with evidence)
- [BUG: Sub-agents load skills from global directory instead of project directory — anthropics/claude-code #10061](https://github.com/anthropics/claude-code/issues/10061) (Tier 2 — production bug with evidence)
- [BUG: Path-scoped rules not automatically loaded — anthropics/claude-code #16853](https://github.com/anthropics/claude-code/issues/16853) (Tier 2 — production bug with evidence)
- [The Silent Failure Mode in Claude Code Hook Every Dev Should Know About — Medium](https://thinkingthroughcode.medium.com/the-silent-failure-mode-in-claude-code-hook-every-dev-should-know-about-0466f139c19f) (Tier 2 — engineering blog with production evidence)
- [Your SKILL.md Works in Claude Code but Silently Fails in VS Code — DEV Community](https://dev.to/moonrunnerkc/your-skillmd-works-in-claude-code-but-silently-fails-in-vs-code-k9b) (Tier 2 — engineering blog with concrete failure cases)
- [SkillCheck — Validate Agent Skills for Claude, Cursor, VS Code](https://www.getskillcheck.com/) (Tier 2 — production tooling)
- [claude-rules-doctor — GitHub](https://github.com/nulone/claude-rules-doctor) (Tier 2 — production tooling)
- [agnix — GitHub](https://github.com/agent-sh/agnix) (Tier 2 — production tooling)

## Key Finding

Cross-primitive dependency failures in Claude Code are predominantly **silent**: broken references do not raise errors at load time but instead cause primitives to be silently skipped, misconfigured, or resolved against the wrong scope. The three highest-failure-rate dependency types — verified by confirmed production bugs — are: (1) hook exit-code contracts (non-zero but non-2 codes cause silent non-blocking behavior), (2) subagent `skills:` field resolution (project-local skills silently ignored in favor of global), and (3) rule `paths:` glob matching (malformed or unmatched globs cause rules to load globally or not at all). Static path analysis and glob matching are reliable detection heuristics without LLM inference.

---

## Evidence

### Dependency Types Between Claude Code Primitives

#### Taxonomy of Cross-Primitive Links

Based on official documentation (Tier 1), the following dependency relationships exist between Claude Code primitives:

| Dependency Type | From Primitive | To Primitive | Link Mechanism |
|---|---|---|---|
| skill→skill | Skill (`context: fork`) | Subagent, other Skill | `agent:` field in frontmatter selects a named subagent; `skills:` field in subagent loads named skills |
| hook→script | Hook (any type) | Shell script / Python file | `command:` field path in hooks.json or skill frontmatter |
| hook→skill | Hook (`type: agent`) | Skill | `prompt:` drives a subagent that may auto-load matching skills |
| agent→skill | Subagent | Skill | `skills:` frontmatter field; list of named skills preloaded at subagent startup |
| rule→file | Rule | Codebase files | `paths:` YAML frontmatter glob patterns; rule loads only when matching files are active |
| skill→file | Skill | Supporting files | Prose references in `SKILL.md` body (e.g., `see [reference.md](reference.md)`) |
| skill→tool | Skill | MCP tool / built-in tool | `allowed-tools:` frontmatter field; grants tool access scoped to skill execution |
| hook→env | Hook | Environment variable | `$CLAUDE_PROJECT_DIR`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}` path interpolation |

**Source:** [Claude Code Skills Docs](https://code.claude.com/docs/en/skills), [Claude Code Hooks Docs](https://code.claude.com/docs/en/hooks) (Tier 1)

---

### Runtime Failure Modes for Broken References

#### Silent Non-Blocking: Hook Exit Code 1

**Source:** [GitHub #21988 — PreToolUse hooks exit code ignored](https://github.com/anthropics/claude-code/issues/21988) (Tier 2, confirmed production bug)

- Claude Code's hook protocol designates **only exit code 2** as blocking. Exit codes 1 and all other non-zero values are classified as non-blocking errors.
- A hook exiting with code 1 causes Claude Code to display `PreToolUse:<HookName> hook error` in the transcript, then **proceeds with tool execution anyway**.
- This is a **phantom block**: the terminal output implies the operation was stopped; the tool runs regardless.
- Uncaught Python exceptions default to exit code 1, meaning any unhandled exception in a validator hook silently degrades to non-blocking.
- The issue was closed as a duplicate of older confirmed bugs (#3514, #13756, #4669), indicating the failure pattern is systemic and long-standing.
- **Detection requirement:** Static analysis must check that all hook scripts use `sys.exit(2)` (not `sys.exit(1)`) for blocking intent, and that all except clauses also call `sys.exit(2)`.

#### Silent Scope Error: Subagent Skill Resolution

**Source:** [GitHub #10061 — Sub-agents load skills from global directory](https://github.com/anthropics/claude-code/issues/10061) (Tier 2, confirmed production bug, closed "not planned")

- When a skill's `context: fork` or an agent's `skills:` field references a named skill, subagents invoked via the Task tool resolve the skill name **only against `~/.claude/skills/`** (global), ignoring project-local `.claude/skills/`.
- Expected precedence (enterprise > personal > project) is not applied in subagent contexts.
- A project skill with the same name as a global skill is **silently shadowed** — the global version runs, the project version is never loaded.
- Issue closed as "not planned", meaning the failure mode is **by-design-persistent** as of 2026-04.
- **Detection requirement:** When a subagent `skills:` field lists a skill name, static analysis must verify the skill exists at the expected scope level (project-local vs global) and flag cases where a global skill would shadow a project skill.

#### Silent Load Failure: Rule Path Glob Matching

**Source:** [GitHub #16853 — Path-scoped rules not automatically loaded](https://github.com/anthropics/claude-code/issues/16853) (Tier 2, confirmed production bug, open)

- Rules in `.claude/rules/` with `paths:` frontmatter glob patterns are silently not injected into context when working with matching files.
- The rule does not appear in `/context` or `/memory` output at all — there is no "available but not loaded" indicator.
- Malformed glob variants (unquoted multi-path strings, invalid brace expansions) are accepted without parse errors but may match zero files.
- The `claude-rules-doctor` tool (Tier 2) confirms this as a production failure pattern: it classifies rules as **DEAD** when `paths:` is specified but zero files in the repo match the glob, and **WARNING** for invalid YAML, empty arrays, or non-string values.
- **Detection requirement:** Glob pattern validation against actual repo filesystem contents is a reliable heuristic. A rule with a non-empty `paths:` array that matches zero files is a broken dependency.

#### Silent Non-Load: Vague Skill Descriptions

**Source:** [DEV Community — SKILL.md Silent Failures](https://dev.to/moonrunnerkc/your-skillmd-works-in-claude-code-but-silently-fails-in-vs-code-k9b) (Tier 2)

- Agent-driven skill loading is description-match driven. Claude decides whether to invoke a skill based on the `description` field.
- Vague descriptions (e.g., "Helps with infrastructure") cause skills to never activate in auto-dispatch scenarios — the skill exists but is never matched.
- This is a **behavioral dependency failure**, not a file-system failure: the skill file is valid, but the cross-primitive activation contract (description → trigger) is broken.
- **Detection requirement:** Description quality heuristics (verb-first, presence of trigger phrases, ≤250 char limit) are static and do not require LLM inference.

#### Silent Failure: Supporting File References

**Source:** [DEV Community — SKILL.md Silent Failures](https://dev.to/moonrunnerkc/your-skillmd-works-in-claude-code-but-silently-fails-in-vs-code-k9b) (Tier 2)

- Relative file paths in a skill's body (e.g., `see [reference.md](reference.md)`, `scripts/validate.sh`) are not validated at load time.
- Tools do not check whether referenced supporting files exist. A renamed or deleted supporting file causes a **silent dereference failure**: Claude attempts to read the file and receives an error at runtime.
- Path traversal attempts (`../../secrets.env`) go undetected statically, creating a security surface (CWE-59).
- **Detection requirement:** Glob-based filesystem existence check for all relative paths referenced in skill body prose is reliable and LLM-free.

#### Cross-Platform Path Resolution Failures

**Source:** [Claude Code Hooks on Windows, Linux, and macOS (2026)](https://claudefa.st/blog/tools/hooks/cross-platform-hooks) (Tier 3 — unverified, flagged)

- Hardcoded path separators in hook `command:` fields fail on Windows (forward-slash vs backslash).
- The `$CLAUDE_PROJECT_DIR` and `${CLAUDE_PLUGIN_ROOT}` environment variables are the documented portable alternatives.
- **Claim status:** Unverified (single Tier 3 source). The pattern is consistent with platform portability norms but cannot be cross-validated at Tier 1/2.

---

### Detection Heuristics (LLM-Free Static Analysis)

The following heuristics are validated by production tooling (Tier 2) and official documentation (Tier 1) as reliable without LLM inference:

| Check | Implementation | Failure Signal |
|---|---|---|
| Glob pattern → file existence | Filesystem glob against repo root | `paths:` array non-empty, zero matches → DEAD |
| Hook script path existence | File existence check on `command:` value after env var substitution | File not found → broken dependency |
| Skill name resolution | Name lookup in `~/.claude/skills/` and `.claude/skills/` | Named skill not found in either scope → broken `skills:` reference |
| Relative path existence in skill body | Regex extract markdown links + file existence check | Linked file absent → broken supporting file reference |
| Hook exit code semantics | Grep for `sys.exit(1)` in Python hook scripts | Any `sys.exit` with argument other than 0 or 2 → silent non-blocking risk |
| Description character count | `len(description)` | >250 chars → truncated, trigger phrases may be lost |
| `name` field vs directory name | String equality check | Mismatch → cross-tool activation failure (VS Code) |
| `allowed-tools:` field values | Token split + lookup against known tool names | Unknown tool name → silent no-op at runtime |

**Sources:** [claude-rules-doctor](https://github.com/nulone/claude-rules-doctor), [SkillCheck](https://www.getskillcheck.com/), [agnix](https://github.com/agent-sh/agnix), [Claude Code Skills Docs](https://code.claude.com/docs/en/skills) (mix of Tier 1 and Tier 2)

---

### Production Failure Pattern Summary

Three confirmed production failure patterns (all from closed or open GitHub issues against anthropics/claude-code):

1. **Hook exit-code phantom block** (bugs #21988, #3514, #13756, #4669): Most critical — security validators appear to work but don't block. Systemic and long-standing.
2. **Subagent skill scope shadowing** (#10061, closed "not planned"): Permanent behavioral gap — project skills silently ignored when subagents run. Particularly dangerous in plugin and enterprise contexts where skill overrides are expected.
3. **Rule path glob silent skip** (#16853, open): Affects any team relying on context scoping — path-scoped rules simply don't load, with no visible diagnostic.

---

## Rubric Guidance

### Dependency Types and Review Dimensions

| Dependency Type | Failing Review Dimension | Rationale |
|---|---|---|
| Hook `command:` path → script | **Safety** (primary), **Completeness** | A missing or wrong-exit-code hook script defeats the hook's enforcement intent. Safety dimension must penalize hooks whose scripts don't exist or whose exit code semantics are incorrect. |
| Skill `agent:` / `context: fork` → subagent | **Completeness**, **Goal Alignment** | A fork to a named subagent that doesn't exist produces a silent runtime failure. The skill cannot achieve its stated goal. |
| Subagent `skills:` → named skills | **Completeness**, **Context Engineering** | Missing skills in the preload list leave the subagent without declared context. Context Engineering dimension should penalize missing skill references. |
| Rule `paths:` → repo files | **Completeness**, **Goal Alignment** | A rule with a dead glob is never applied — its goal is never achieved. |
| Skill body → supporting files | **Completeness** | Prose references to non-existent files break the skill's operational flow. |
| Skill `description:` → activation | **Metadata** (primary), **Goal Alignment** | A description that cannot trigger auto-dispatch breaks the activation contract. Metadata dimension owns description quality; Goal Alignment owns whether the skill can actually be invoked. |
| Hook exit code semantics | **Safety** | Exit code 1 in a blocking hook is a safety defect, not a style issue. Must be High severity. |

### Detection Heuristics for Reviewers

Reviewers should perform these checks statically before any LLM-based quality evaluation:

1. **For every hook `command:` field**: resolve the path (substituting `$CLAUDE_PROJECT_DIR` / `${CLAUDE_PLUGIN_ROOT}`) and check file existence. Flag missing files as High severity (Safety).
2. **For every Python hook script**: grep for `sys.exit` calls. Flag any non-zero, non-2 exit values as High severity (Safety). Flag bare `except:` clauses without `sys.exit(2)` as Medium severity.
3. **For every rule `paths:` array**: run glob against repo filesystem. Flag zero-match globs as High severity (Completeness + Goal Alignment).
4. **For every skill referencing `agent:` or subagent `skills:` fields**: verify the named agent/skill exists in the expected scope. Flag unresolved names as High severity (Completeness).
5. **For every relative markdown link in skill body**: check file existence relative to skill directory. Flag missing files as Medium severity (Completeness).
6. **For every `description:` field**: check character count (>250 = truncation risk), verb-first pattern, and presence of at least one trigger phrase. Flag violations as Medium severity (Metadata).

### Severity Classification

| Finding | Severity | Dimension |
|---|---|---|
| Hook script path does not exist | High | Safety |
| Hook exit code 1 used for blocking intent | High | Safety |
| Rule `paths:` glob matches zero files | High | Goal Alignment |
| Subagent `skills:` references non-existent skill | High | Completeness |
| Supporting file referenced in body does not exist | Medium | Completeness |
| Skill `name` mismatches directory name | Medium | Metadata |
| Description >250 chars or missing trigger phrases | Medium | Metadata |
| `allowed-tools:` contains unrecognized tool name | Low | Completeness |

---

## Unverified Claims

- **Cross-platform hook path failure (Windows backslash):** Single Tier 3 source only ([claudefa.st](https://claudefa.st/blog/tools/hooks/cross-platform-hooks)). The pattern is consistent with general cross-platform norms but is not corroborated at Tier 1 or Tier 2. Do not treat as confirmed production failure.
- **Hallucinated fallback behavior:** No source documented Claude hallucinating a skill's behavior when a skill reference is missing. The observed pattern is silent skip, not hallucinated fallback. Absence of evidence is not evidence of absence — this remains an open sub-question.
- **HTTP hook failure on missing endpoint:** The official docs state non-2xx and connection failure produce "non-blocking error, execution continues" — this is Tier 1 sourced — but no production case study confirms the runtime UX. Treat the documented behavior as authoritative.
