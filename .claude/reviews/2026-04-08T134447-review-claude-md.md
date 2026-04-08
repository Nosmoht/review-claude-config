---
generated_by: review-skill
schema_version: 1
date: 2026-04-08
target: /Users/ntbc/workspace/review-claude-config/skills/review-claude-md/SKILL.md
baseline_version: 2026-04-04
items_reviewed: 1
summary:
  - name: review-claude-md
    type: Skill
    path: skills/review-claude-md/SKILL.md
    overall: B
    score: 87.0
    clarity: B
    completeness: B
    prompt_engineering: B
    context_engineering: B
    goal_alignment: B
    safety: A
    metadata: A
---

### Goal
Evaluate a CLAUDE.md file for structural quality, instruction clarity, and command accuracy across 4 dimensions tailored to configuration documents rather than executable primitives.

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | B | 15% | Explicit 4-phase workflow; one vague conditional in domain research ("or the project domain" query) |
| Completeness | B | 15% | Comprehensive coverage; command inventory step omits the shell-command vs. slash-command distinction |
| Prompt Engineering | B | 15% | Structured output, stepwise flow, grading boundary examples, constraint section; no role priming |
| Context Engineering | B | 15% | Good reference separation; review-report-contract Glob in Phase 3 is redundant (schema already inline) |
| Goal Alignment | B | 20% | Unique command inventory step is the right domain move; path resolution convention underspecified |
| Safety | A | 15% | Confirmation gate before write, explicit read-only hard rule, writes scoped to `.claude/reviews/` |
| Metadata | A | 5% | Complete frontmatter, description accurate with trigger and exclusion, tool list matches usage |
| **Overall** | **B** | **100%** | **Weighted: 87.0 → B** |

### Strengths
- Command Inventory Verification (Phase 2 Step B) is the standout feature — gives Goal Alignment scoring a deterministic, file-system-grounded anchor.
- Safety correctly excluded from CLAUDE.md evaluation with an explicit hard rule.
- Mode detection pattern (orchestrated/standalone) cleanly implemented, consistent with sibling skills.

### Recommendations

#### 1. Specify the shell-command vs. slash-command resolution rule in Step B (Impact: High, Category: Completeness)
**Evidence:** Phase 2 Step B provides only one example (`/review-skill` → `skills/review-skill/SKILL.md`). No rule for maintenance skills under `.claude/skills/`, shell commands (`make validate`, `pytest`, `gh`), or commands with no file counterpart.

**Why it matters:** Command inventory drives GA-1/GA-2 scoring and is marked "never skip this step." Without an explicit resolution rule, evaluators will mark different commands STALE vs. VERIFIED for the same CLAUDE.md.

**Validation:** Re-run against a CLAUDE.md listing both slash commands and `make` targets. GA-1/GA-2 verdicts identical across two runs.

**Current:**
```
For every command listed in the CLAUDE.md:
1. Extract the command path or skill name (e.g., `/review-skill` → `skills/review-skill/SKILL.md`).
2. Use Glob to verify the file exists relative to the CLAUDE.md's directory.
3. Mark each command as **VERIFIED** (file found) or **STALE** (file not found or path mismatch).
```

**Recommended:**
```
For every command listed in the CLAUDE.md:
1. Classify the command:
   - **Slash command** (`/name`): resolve to `skills/name/SKILL.md` first,
     then `.claude/skills/name/SKILL.md` as fallback.
   - **Shell command** (`make`, `pytest`, `git`, `gh`, `uv`): mark as
     SHELL — no file resolution; skip Glob check.
   - **Inline path** (explicit file path): verify the path exists directly.
2. For slash commands, use Glob to verify the resolved path exists.
3. Mark each command as **VERIFIED** (file found), **STALE** (file not found
   or path mismatch), or **SHELL** (non-resolvable shell command, not checked).
```

#### 2. Remove redundant review-report-contract Glob from Phase 3 (Impact: Medium, Category: Context)
**Evidence:** Phase 3 opens with "Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`…" but the recommendation schema is fully inline immediately after. The Glob adds a tool call whose result is unused.

**Why it matters:** JIT Retrieval — load deeper material only when needed. The inline schema already provides all needed structure; the Glob is dead weight.

**Validation:** Phase 3 produces correct recommendation blocks with no runtime Glob for the contract.

**Current:**
```
Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`.
Prefer the `skills/` copy when present; otherwise use the sibling `.claude/skills/` copy.
Use that contract's shared recommendation schema below.
```

**Recommended:**
```
Use the recommendation schema below directly (the contract is referenced in shared references loaded in Phase 1 if needed).
```

#### 3. Tighten domain research query formulation (Impact: Low, Category: Workflow)
**Evidence:** Phase 2 Step A.2: "perform 1 WebSearch for 'Claude Code CLAUDE.md best practices' or the project domain."

**Why it matters:** "The project domain" is not an observable test. Deterministic Conditionals baseline requires branch conditions to be observable. Two models produce different search strings for the same input.

**Validation:** Step A.2 specifies both query strings explicitly.

**Current:**
```
perform 1 WebSearch for "Claude Code CLAUDE.md best practices" or the project domain.
```

**Recommended:**
```
perform 1 WebSearch using "Claude Code CLAUDE.md best practices [project-type]"
where [project-type] is the one-word project type identified in step 1
(e.g., "Kubernetes", "Python service", "TypeScript app").
```
