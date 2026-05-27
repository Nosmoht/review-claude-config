---
name: quality-patterns
description: Research-backed generation directives for B+ quality skills — translates engineering-baseline evaluator checks into generator actions. Each section is prefixed with the binary rubric item ID it satisfies.
last_refreshed: 2026-05-27
---

Translates `engineering-baseline.md` evaluator checks into generator directives. Load
baseline for full citations. Each directive is prefixed with the binary item ID it
satisfies per `rubric-coverage.md`. Coverage: all 30 binary skill items.

## Metadata Directives

### META-1a Trigger-Match-Primary
Embed the body's primary trigger keyword (filename glob, command name, or domain
noun) verbatim in the `description:` frontmatter field. Token-set overlap between
description and body trigger must be non-zero.

### META-2 Anti-Pattern Example
Include a "Do NOT use for" clause in description. Format:
`Do NOT use for <exclusion> — use /<sibling-command> instead.`
This clause must match `/do ?not use|not for|skip (when|if)/i`.

### META-3a Concrete Trigger
Avoid "as needed", "if appropriate", "when useful" in description. Use a concrete
observable condition: "when file contains `hooks.json`", "when `$ARGUMENTS` points
to a `*.skill.md` file".

### META-3b Sibling-Distinguishability
Cannot be enforced at scaffold time (sibling descriptions are unknown). After
install, run `/validate-primitive-dependencies` to check cross-skill overlap.
Documented as `runtime-OOS` in `rubric-coverage.md`.

### META-3c Discriminating-Keyword-Presence
Include ≥1 domain-specific token in the description that would NOT appear in a
generic skill description. Use the skill's unique domain noun (e.g., `hooks.json`,
`scoring-rubric`, `session-trace`) not generic tokens like "evaluates", "reviews",
"analyzes".

### META-4 Third-Person Description
Write description in third person throughout. Prohibited: `I`, `my`, `me` (case-
sensitive); `you can`, `your` (case-insensitive). Correct: "Evaluates MCP server
configs and produces a quality certificate." Wrong: "I help you review your configs."

### SAMP-2 Frontmatter Sampling-Param Ban
Never include `temperature:`, `top_p:`, or `top_k:` in generated frontmatter.
These parameters cause HTTP 400 on Opus 4.7 native-thinking models.

## Clarity Directives

### CLAR-2 Resolved-Pronoun
When a step references prior tool output, use an explicit antecedent in the same or
immediately-preceding step. Wrong: "parse the output; then process them." Correct:
"parse the grep output; store the matches in `$findings`."

### CLAR-3 Stop/Recovery
Every use of abort, refuse, bail, halt, or timeout MUST name a recovery target within
200 characters. Recovery options: write a stub (e.g., `{"status":"missing"}`), fall
back to a named step, continue to step N, or report and stop.
Wrong: "If the tool fails, abort." Correct: "If the tool fails, abort — write
`{"status":"missing"}` stub and continue to step b.4."

### CLAR-4 Step-Dependency-Mitigation
Every step declaring an upstream dependency (`depends on:`, `after step N`, `requires
output of`) MUST name a failure branch within the same step or reference a named
"Error Handling" / "Fallback" block. Correct: "b.5 depends on b.4 completed; if b.4
wrote a status:missing stub, degrade per b.7."

### WS-2b Conditional-Specificity
Every "If present" or "If absent" occurrence within 500 chars of a block-marker
(`^---[a-z_-]+---$`) MUST be preceded within 400 chars by a prose predicate naming
the marker: "Check whether the prompt contains an orchestration metadata block."

### WS-5b Negation-Positive-Whitelist
Every NEVER / DO NOT / MUST NOT + verb-list must be followed within 200 characters
by a positive whitelist. Pattern: "DO NOT use X, Y. ALLOWED: Z." or "use only A."
Wrong: "NEVER use rm, mv, dd" (no whitelist). Correct: "NEVER use rm, mv. ALLOWED:
`git status`, `git log`."

### WS-6 Quantifier-Range-Anchor
Every bare relative comparator (more, fewer, older, newer, larger, smaller, less,
greater, higher, lower) MUST have a numeric/unit anchor within 80 characters.
Wrong: "older than typical". Correct: "older than 30 days".

### RD-5b Step-Naming-Consistency
Use a single step-naming scheme throughout (PHASE, STEP_LETTER, STEP_NUMBER, or
DOTTED). If ≥2 schemes are mixed, include a mapping clause: "Phase 2 decomposes into
sub-steps b.0–b.7." Markdown heading nesting alone is NOT a mapping clause.

## Context Engineering Directives

### CE-X Compaction-Strategy
If the workflow keeps conversation history ≥10 turns AND uses LLM-based summarization,
include ≥1 sentence justifying why masking is insufficient. Reference
`engineering-baseline.md §"Observation Masking"` cases (a)/(b)/(c).

## Completeness Directives

### COMP-V Verifiable-Predicate
Every "complete when" / "success when" / "done when" criterion MUST contain ≥1
programmatically-verifiable component within 200 chars: numeric threshold, regex
marker, exit-code check, schema reference, or tool-output binding. Wrong: "complete
when the review is finished." Correct: "complete when `make validate` exits 0."

### COMP-W Termination-Criteria
Iterative skills (for each / retry / iterate / while / until / loop) MUST declare an
explicit termination predicate distinct from the COMP-X success criterion. Pattern:
"stop when", "terminate after N iterations", "escalate after 3 consecutive failures".
Wrong: "retry on failure". Correct: "retry up to 3 times; after 3 failures, escalate."

### COMP-X Success-Criteria
Define an explicit success condition, not just output format. For review skills
(description primary verb ∈ review/audit/classify/evaluate/score/certify): include a
convergence predicate (re-run variance, identical finding set, ≤N-letter grade Δ).
Wrong: "review complete when every checklist item has a verdict." Correct: "review
succeeds when dimension-grade variance ≤1 letter vs prior run."

### COMP-Y Verification-Method
Use a programmatic check or explicit binary LLM item (not holistic assessment).
Forbidden patterns: "looks good", "seems correct", "appears valid". Use "verify",
"validate", "check", "assert" with a named predicate.

### COMP-Z Evidence-Trail
Output specification MUST include evidence/citation/quote/verified-against language.
The output contract must record WHY a verdict was reached, not just what it is.

### AH-2b Default-Handling-Pair
When the body references `$ARGUMENTS` or a required user-supplied parameter, include
a named missing-argument handler within 200 chars of the first reference. Options:
(a) fall back to a named default value; (b) prompt the user via AskUserQuestion;
(c) stop with a usage-error message. Wrong: implicit assumption that argument exists.
Correct: "If `$ARGUMENTS` is empty, default to `**/SKILL.md` and prompt the user."

## Prompt Engineering Directives

### SAMP-1 Body Sampling-Param Ban
Exclude hardcoded `temperature`, `top_p`, `top_k` from the generated body text
(regex: `/\b(temperature|top_p|top_k)\s*[:=]/i`). FAIL caps Prompt Engineering at C.

## Safety Directives

### SP-2b Tool-Archetype-Binding
For each entry in `allowed-tools` / `tools` frontmatter, include a binding sentence
within 200 chars of an archetype keyword (restricted to, allowlisted, limited to,
scoped to, used only for). Read-only archetype (`allowed-tools` ⊆ {Read, Glob, Grep,
NotebookRead, WebSearch}) is auto-NA. Wrong: seven-tool list with Write/Bash/Edit and
no binding. Correct: "Bash is allowlisted to exactly two commands: `make validate`,
`git status`."

### SP-4b Tier-A-Constraint-Sentence
Tier-A tool combinations (Write + any of Bash/Agent/WebFetch) require a constraint
sentence per Tier-A tool naming the path/directory/command/url scope. Forbidden:
blanket "Tier A is acceptable." Required pattern: "Write is restricted to
`$PLUGIN_DATA/reports/<repo-slug>/` path."

### IJ-1b Input-Validation-Pair
When `allowed-tools` contains Write or Edit AND the body references external input
(`$ARGUMENTS`, user-supplied path, fetched URL, MCP-tool output), include BOTH:
(a) a validation predicate (validate matches pattern / regex / allowlist lookup);
(b) a write-gate predicate (AskUserQuestion / confirm / approval / ExitPlanMode
before Write). Either alone is a FAIL.

### RL-1b Termination-Regex
Agentic skills (body contains Agent/Task/subagent dispatch, loop verbs, or
Write/Bash/Edit) MUST include a numeric or enum termination predicate matching one of:
max N iterations, max wait N minutes, status: terminal/success/partial/failure/done.
Wrong: AskUserQuestion loop with no documented turn budget.

### RL-3b Retry-Ceiling
Every use of retry / regenerate / redisplay / ask again / adjust MUST have a numeric
cap within 400 chars (before or after). Pattern: "maximum 3 reflection cycles",
"up to 3 retries", "after 3 consecutive failures". Wrong: "redisplay and confirm
again" with no cap.

### RL-4b Escalation-Trigger
Autonomous / self-executing / multi-step / dispatch paths MUST include ≥1 named HITL
or partial-status branch. Required literals: (a) AskUserQuestion, confirm, or
approval on the happy path; (b) `status: partial` on a fallback path; (c) escalate /
on escalation / partial result / fallback to user step. Subjective "named escalate
step" is insufficient.

### RL-9b Credential-Scope-Regex
Agentic skills that read user-supplied paths OR write content quoted from external
files MUST include ≥1 credential-scope rule. Required patterns: redact token-like
substrings (e.g., `/[A-Za-z0-9_-]{20,}/`), truncate at N chars, skip `.env`/`.ssh`/
credential files, or name the token-like pattern explicitly.
