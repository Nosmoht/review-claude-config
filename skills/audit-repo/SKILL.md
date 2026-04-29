---
name: audit-repo
description: >
  Analyzes a repo for needed Claude Code primitives and produces a prioritized
  intervention matrix. Use when setting up or diagnosing a Claude Code
  configuration. Do NOT use to suggest skills only — use /suggest-skills.
argument-hint: [folder]
allowed-tools: Agent, Read, Write, Glob, Grep, WebSearch, WebFetch
disable-model-invocation: true
---

# Audit Repo

Analyze a target repository's structure, toolchain, conventions, architecture, and token efficiency to produce a prioritized intervention matrix of recommended Claude Code primitives. This skill uses a mix of deterministic scan signals, evidence-informed guidance, and repo-policy heuristics; it is diagnostic support, not a scientifically closed primitive-derivation engine.

## Argument Handling

- `$ARGUMENTS` is the target folder path. If empty, use the current working directory.
- Validate the folder exists and contains files. If the folder has no files, report that and stop.

## Phase 1 — Setup

### Step 0: Tool Availability Checks

Attempt a trivial WebSearch (e.g., "Claude Code documentation"). If it fails or is unavailable, set `websearch_available = false` and continue. Recommendations will use model knowledge only, marked `[no web verification]`.

Attempt a trivial WebFetch (e.g., fetch "https://docs.anthropic.com"). If it fails or is unavailable, set `webfetch_available = false` and continue.

### Step 1: Load References

Read these files from the skill's own `references/` directory:
- `references/signal-patterns.md` — file patterns per analysis step
- `references/error-class-taxonomy.md` — error classes and primitive mapping
- `references/primitive-decision-matrix.md` — decision rules per primitive type
- `references/token-heuristics.md` — thresholds and scoring formulas
- `references/audit-report-schema.md` — report frontmatter schema and body structure

Read from the sibling `suggest-skills` skill's references:
- Locate via Glob: `**/suggest-skills/references/signal-catalog.md`
- This provides the Application Signal Table and Skills Repository Signal Table for Phase 4B skill detection

Load repo-identification reference to resolve suite-root and repo-slug:
- Locate via Glob: `**/review-claude-config/references/repo-identification.md`

### Step 2: Initial Target Assessment

Check the target folder for existing Claude Code configuration:
- Glob for `<folder>/CLAUDE.md` — note if present, read first 50 lines
- Glob for `<folder>/.claude/skills/*/SKILL.md` — count existing skills
- Glob for `<folder>/.claude/agents/*.md` — count existing agents
- Glob for `<folder>/.claude/rules/*.md` — count existing rules
- Glob for `<folder>/.claude/hooks/` or hooks config — note if present

Record: `existing_claude_config = true|false`, existing item counts.

## Phase 2 — Static Repo Analysis

Launch a **Repo Scanner Agent** to collect structured facts. The agent returns facts per category, not interpretations.

Agent allowed-tools: Glob, Grep, Read, Bash.

```
You are scanning a repository to collect structured facts for an audit.
Return facts only — no recommendations or interpretations.

SCAN LIMITS:
- Read at most 50 lines per file
- Scan at most 4 directory levels deep
- Cap file listings at 500 files per directory
- BASH RESTRICTIONS: Read-only operations only. ALLOWED commands: find, ls, wc, grep, head, tail, sort, uniq, cat (for ≤50 lines).

ERROR HANDLING:
- If a Glob pattern returns no results, report "NOT FOUND" for that item within the category.
- If a file cannot be read, report under the category: "ERROR: [path] — [reason]" and continue.
- If a Bash command fails, report the command and error output under the category. Do not skip silently.
- Always produce output for every category, even if empty (use "No results" with brief explanation).

## Signal Patterns Reference
[Insert signal-patterns.md content here]

## Category A: Toolchain Detection
Find all build/test/lint/deploy commands:
- Glob for each toolchain signal file from the reference
- For package.json: extract "scripts" section (first 50 lines)
- For Makefile/Justfile: extract target names via Grep
- For CI configs (.github/workflows/*.yml, .gitlab-ci.yml): extract
  step commands via Grep for "run:" patterns
- For pyproject.toml: extract [tool.pytest], [tool.ruff], [project.scripts]
- For Cargo.toml, go.mod, build.gradle: note presence and language
- Report in this exact format:

| Tool | Source File | Commands |
|------|-------------|----------|
| [tool name] | [config file path] | [extracted commands] |

NOT FOUND: [list categories with no detected tools]

## Category B: Ambiguity Measurement
Quantify repository navigation complexity:
- Bash: find . -type f -not -path './.git/*' -not -path '*/node_modules/*' |
  awk -F/ '{print NF-1}' | sort -rn | head -1
  (max directory depth)
- Bash: find . -type d -not -path './.git/*' -not -path '*/node_modules/*' |
  head -100 | while read d; do echo "$(ls -1 "$d" 2>/dev/null | wc -l) $d"; done |
  sort -rn | head -10
  (files per directory, top 10)
- Grep for naming collisions: search for "export class|export function|def |
  func |type " across source files, count duplicate names
- Report in this exact format:

| Metric | Value |
|--------|-------|
| Max depth | [N] |
| Max files/dir | [N] |
| Naming collisions | [N] |
| Sprawl score | [N] (depth × max_files × collisions) |

## Category C: Linter/Formatter Coverage
Classify convention enforcement tiers:
- Glob for each tier's detection files from signal-patterns.md
- For each found linter config: note what conventions it enforces
- Grep CI configs for lint/format/check steps
- Glob for CLAUDE.md, .claude/rules/*.md, .cursorrules — note
  convention instructions found
- Report in this exact format:

| Convention | Tier | Tool/Config |
|-----------|------|-------------|
| [convention type] | Deterministic/CI-enforced/AI-instructed/Undocumented | [config file or "none"] |

## Category D: Architecture Pattern Extraction
Detect architecture patterns:
- Glob for each architecture signature directory set from reference
- Grep for DI framework markers (inversify, tsyringe, Dagger, Spring)
- Glob for ADRs: docs/adr/, docs/decisions/, docs/architecture/
- If hexagonal-like directories found, check import direction via Grep
  (do adapters import from domain, or vice versa?)
- Report in this exact format:
  Pattern: [name or "none detected"]
  Evidence: [directory paths or file patterns]
  ADRs: [yes — path | no]
  DI Framework: [name or "none"]

## Category E: Domain Knowledge Inventory
Check for domain documentation:
- Glob for each domain knowledge source from signal-patterns.md
  (OpenAPI, protobuf, GraphQL, glossary, ADRs, migrations, schemas)
- For each found: note file path and brief content summary (first 20 lines)
- Read README.md first 50 lines for business context sections
- Report in this exact format:

| Type | Path | Summary |
|------|------|---------|
| [doc type] | [file path] | [brief content summary] |

Gaps: [list missing domain docs — e.g., no glossary, no API spec]

COMPLETION: You are done when all 5 categories (A through E) have a report section AND each section either (a) cites ≥1 specific path or filename from the target repo, OR (b) explicitly states "no instances found" together with the search pattern (Glob / Bash command) that was attempted. A bare section heading or a generic statement without paths or attempted-pattern is INCOMPLETE — re-run that category. If a category cannot be fully scanned due to repo size or access issues, report what you found, name the limitation, and state which paths or patterns remain uncovered.
```

If the scan agent fails entirely, report the error to the user and stop.

## Phase 3 — Token Efficiency Analysis

Launch a **Token Analyzer Agent** to compute quantitative metrics.

Agent allowed-tools: Glob, Bash, Read.

```
You are analyzing a repository for token efficiency. Return metrics only.

SCAN LIMITS:
- Read at most 50 lines per file
- Scan at most 4 directory levels deep
- BASH RESTRICTIONS: Read-only operations only. ALLOWED commands: find, ls, wc, grep, head, tail, sort, uniq, cat (for ≤50 lines).

ERROR HANDLING:
- If a Glob pattern returns no results, report "NOT FOUND" for that item within the category.
- If a file cannot be read, report under the category: "ERROR: [path] — [reason]" and continue.
- If a Bash command fails, report the command and error output under the category. Do not skip silently.
- Always produce output for every category, even if empty (use "No results" with brief explanation).

## Token Heuristics Reference
[Insert token-heuristics.md content here]

## Metric A: File Size Distribution
Find the largest source files:
- Bash: find . -name '*.ts' -o -name '*.py' -o -name '*.go' -o -name '*.rs'
  -o -name '*.java' -o -name '*.js' -o -name '*.tsx' -o -name '*.jsx' |
  grep -v node_modules | grep -v .git |
  xargs wc -l 2>/dev/null | sort -rn | head -20
- Classify each file: >2000 (severe), >1000 (critical), >500 (token sink)
- Estimate total token cost for top 10 files using language-specific density
- Report in this exact format:

| File | Lines | Classification | Est. Tokens |
|------|-------|---------------|-------------|
| [path] | [N] | severe/critical/token sink | [N] |

## Metric B: Navigation Sprawl Score
Compute the score from Phase 2 Category B results:
- Use max_depth, max_files_per_dir, naming_collision_count
- Formula: max_depth × max_files_per_dir × max(naming_collisions, 1)
- Classify: >100 (P0 architecture map needed), 30-100 (selective hints),
  <30 (no intervention)
- Report in this exact format:
  Score: [N]
  Classification: [P0 architecture map needed / selective hints / no intervention]
  Breakdown: depth [N] × files/dir [N] × collisions [N]

## Metric C: Build Error Verbosity
Classify detected build tools by verbosity:
- Match each detected toolchain against the verbosity table in reference
- Report in this exact format:

| Toolchain | Verbosity | Token Cost |
|-----------|-----------|------------|
| [tool] | low/medium/high | [classification] |

## Metric D: Monorepo Scope Isolation
If monorepo markers found:
- Count workspace packages/modules
- Bash: grep -rn "from '@" --include='*.ts' --include='*.tsx' |
  grep -v node_modules | wc -l
  (cross-package import count for JS/TS monorepos)
- For Go: count cross-module imports
- Report in this exact format:
  Packages: [N]
  Cross-imports: [N]
  Assessment: [isolation assessment text]

## Metric E: Context Burn Rate Estimate
Based on repo characteristics:
- Average file size × estimated reads per task type (from reference)
- Flag if average file size > 300 lines (high burn rate)
- Report in this exact format:

| Task Type | Est. Tokens |
|-----------|-------------|
| Simple edit | [N]K |
| Exploration + edit | [N]K |
| Multi-file refactor | [N]K |

COMPLETION: You are done when all 5 metrics (A through E) have a report section AND each section either (a) reports concrete numeric values per the metric's exact format table (file paths + line counts for A; computed score + breakdown for B; toolchain + verbosity classification for C; package + cross-import counts for D; per-task-type token estimates for E), OR (b) reports "N/A" with the specific cause (e.g., "Bash command X failed", "no monorepo markers found", "Glob pattern Y returned 0 matches"). A bare section heading or a placeholder like `[N]` left unfilled is INCOMPLETE — re-run that metric. If a metric cannot be computed, name the failing command or pattern, not just "N/A".
```

If the analyzer agent fails, report partial results and continue.

## Phase 4 — Primitives Derivation

The orchestrator synthesizes Phase 2 + Phase 3 results using error-class-taxonomy.md and primitive-decision-matrix.md as decision guides. This runs inline (not as a sub-agent) because it requires judgment that benefits from the full conversation context. The synthesis is evidence-informed, but several mappings remain repo-policy or heuristic decisions rather than benchmark-settled science.

### 4A: CLAUDE.md Gaps

Review Phase 2 results against CLAUDE.md requirements:
- **Toolchain**: Are build/test/lint/deploy commands discoverable from config files? If not → CLAUDE.md P0
- **Architecture**: Is the architecture pattern explicitly documented (ADRs or CLAUDE.md)? If implicit only → CLAUDE.md P1
- **Scope**: Is it a monorepo with cross-package boundaries? → CLAUDE.md P0 scope isolation rules
- **Domain**: Are domain docs referenced? No glossary + complex domain → CLAUDE.md P2
- **Navigation**: Is sprawl score >100? → CLAUDE.md P0 architecture map with entry points
- **Large files**: Any files >500 LOC? → CLAUDE.md hints for relevant sections

For each gap, include: specific evidence from Phase 2, concrete content suggestion (not just "add toolchain commands" but "add these specific commands found in package.json: [list]"), plus an `evidence_class` and `confidence` assignment for the recommendation.

### 4B: Skill Candidates

#### Structural repetition checks

From Phase 2 Category B (ambiguity) and scan results:
- Are there ≥5 structurally similar files (components, services, handlers, migrations)?
- Are there multi-step workflows in CI that could run locally?
- Are there existing codegen templates (plop, hygen, cookiecutter)?

#### Signal catalog checks

Using the signal-catalog.md loaded in Phase 1, match Phase 2 scan results against the Application Signal Table (or Skills Repository Signal Table if `repo_type` is Skills-Config or Mixed):

For each signal row in the table:
1. Check if the file pattern matches any Phase 2 findings (e.g., "Database migrations" matches if `migrations/` was found in Category E)
2. Check if a corresponding skill already exists (from Phase 1 Step 2 skill inventory)
3. If the signal matches AND no existing skill covers it → candidate

#### Validation gate

Each candidate (from either source) must pass 3/4 extraction criteria:
- **Recurrence**: pattern appears in 2+ files/contexts
- **Verification**: workflow expressible as 5-10 clear steps
- **Non-obviousness**: requires domain expertise or multi-step logic
- **Generalizability**: works across different inputs/projects

Do NOT recommend skills for single-command operations, simple aliases, or workflows with fewer than 3 distinct steps.

This gate is a repo-level heuristic filter. Treat it as a decision aid, not as a universal law of skill design.

In the intervention matrix, include a `signal_source` for each Skill row: "repetition" for structural checks, or the signal name from the catalog (e.g., "Database migrations", "Test config without test skill").

### 4C: Agent Candidates

From Phase 2 concern topology:
- Separate lint/test configs per subdirectory → specialized agent per domain
- Security scanning tools in CI (Trivy, Snyk, CodeQL, gitleaks) → security-reviewer agent
- Separate deployment targets (Terraform, Helm, CDK) → infra-architect agent
- CODEOWNERS with clear responsibility boundaries → agent per ownership area

Decision: only recommend Agent if concern has BOTH its own toolchain AND its own evaluation criteria. Otherwise recommend Skill.

This is an intentionally conservative repo policy to avoid inflating agent count.

### 4D: Hook/Rule Candidates

From Phase 2 constraint extraction:
- Pre-commit hooks (.pre-commit-config.yaml, .husky/) → PostToolUse hooks for formatters
- Branch protection rules → Rule ("Never commit directly to main")
- Secret scanning in CI → PreToolUse hook for secret detection
- .gitignore/.dockerignore patterns → file-write restriction rules
- Mandatory review labels → permission config recommendation

Decision: if check is a single command with boolean output → Hook. If judgment needed → Rule.

Treat this as an evidence-informed heuristic split, not a benchmark-settled primitive-selection theorem.

## Phase 5 — Needs Matrix and Report

### Step 1: Assemble the Intervention Matrix

For each identified gap from Phase 4:
1. Assign **error class** from taxonomy (Toolchain, Navigation, Convention, Architecture, Repetition, Domain, Security)
2. Assign **primitive type** (CLAUDE.md, Skill, Agent, Hook, Rule)
3. Assign **priority**: P0 (CLAUDE.md basics + critical navigation), P1 (hooks + skills + security), P2 (agents + domain)
4. Assign **token impact**: High/Medium/Low from Phase 3 metrics
5. Assign **evidence_class** using the canonical classes from `skills/review-claude-config/references/evidence-contract.md`
6. Assign **confidence**:
   - High: strong deterministic repo evidence and/or explicit external validation
   - Medium: solid repo evidence with meaningful interpretation or repo-policy mapping
   - Low: inference-heavy or thinly corroborated recommendation
7. Cite **evidence**: specific file paths, metrics, or absence evidence

Sort by priority (P0 first), then by token impact (High first).

### Step 2: Optional Web Validation

If `websearch_available = true`, validate the top 3 P0 recommendations:
- 1-2 WebSearch queries to check if the recommended primitives align with best practices for the detected tech stack
- Apply source quality criteria from `skills/review-claude-config/references/source-quality-criteria.md`: discard marketing/opinion/outdated content, prefer Tier 1-2 sources
- Mark validated recommendations accordingly

### Step 3: Build Report

Assemble the report following `references/audit-report-schema.md`:

**Frontmatter:** All required fields from schema (generated_by, schema_version, date, target, existing_claude_config, languages, repo_type, intervention_count, p0/p1/p2 counts, summary array). Include `repo: <slug>` and `origin: <git-remote-url>` (origin is optional — omit if no remote configured).

**Body:**

Read `references/report-template.md` for the report body structure. Substitute actual values for all placeholder fields.

#### Action Plan Generation

After completing the Recommendations section, append a `## Action Plan` section to the report. Generate one checkbox per row in the Intervention Matrix, sorted P0→P2 then Token Impact High→Low.

Command mapping:

| Primitive | Command |
|-----------|---------|
| CLAUDE.md | `/apply-audit-findings <report-path>` |
| Hook      | `/apply-audit-findings <report-path>` |
| Rule      | `/apply-audit-findings <report-path>` |
| Skill     | `/scaffold-skill plugin <kebab-name>` |
| Agent     | `manual setup` |

Format per item: `- [ ] **#<row>** [<error_class>] <gap> → <command>`

Group under priority headers (`### P0 — Immediate`, `### P1 — Short-term`, `### P2 — Medium-term`). Omit empty tiers. For >10 interventions, list P0 items individually; collapse P1/P2 to a single line: `- [ ] Apply remaining P[N] findings (N items) → /apply-audit-findings <report-path>`.

Always append a Verification group:
- `- [ ] Re-run /audit-repo <target> to verify coverage`
- `- [ ] Run /review-claude-config <target> to evaluate created primitives`

**Example** (3-row matrix: row 1=CLAUDE.md/P0, row 2=Skill/P1, row 3=Hook/P1):

| Row | Checkbox output |
|-----|----------------|
| 1 | `- [ ] **#1** [Toolchain] Add build/test/lint commands to CLAUDE.md → /apply-audit-findings .../2026-04-04T120000-audit-repo.md` |
| 2 | `- [ ] **#2** [Repetition] Scaffold deploy-validator skill → /scaffold-skill plugin deploy-validator` |
| 3 | `- [ ] **#3** [Convention] Add pre-commit hook config → /apply-audit-findings .../2026-04-04T120000-audit-repo.md` |

### Step 4: Present and Persist

Present the full report to the user.

After presenting, confirm before writing: "Save audit report to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-audit-repo.md`?"

If confirmed, write the report. Create `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/` if it does not exist. If declined, display the path that would have been used.

Suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS audit-repo report`

### Step 5: What's Next?

After all output is complete, end your response with this menu. Substitute actual values: `<report-path>` with the saved report path (or the path that would have been used), `<target>` with the analyzed folder, `N` with the total intervention count from the frontmatter, `M` with the p0_count, and `<top-skill-name>` with the highest-priority Skill primitive from the intervention matrix (kebab-case). Omit item 2 entirely if no Skill primitives exist. If the report was not saved, replace item 1's command with "Save the report first, then `/apply-audit-findings`".

If intervention_count is 0, end the response with:
```
---
No interventions found — the repository is well-configured.
Run `/suggest-skills <target>` to explore skill opportunities beyond the audit scope.
---
```

Otherwise:

Present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Apply audit findings" (Recommended) — description: `"Run /apply-audit-findings <report-path> to create N interventions (M× P0)"`
- Option 2 label: "Scaffold recommended skill" — description: `"Run /scaffold-skill plugin <top-skill-name> to create the highest-priority skill"`
- Option 3 label: "Explore skill opportunities" — description: `"Run /suggest-skills <target> to discover additional skill gaps"`
- Option 4 label: "Done" — description: `"End the workflow"`

On "Apply audit findings": invoke `/apply-audit-findings` with the report path. On "Scaffold recommended skill": invoke `/scaffold-skill plugin <top-skill-name>` directly. On "Explore skill opportunities": invoke `/suggest-skills` with the target folder. On "Done": acknowledge and stop.

## Hard Rules

- **Read-only on target repository.** Never modify any existing file. The only file this skill writes is the audit report at `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-audit-repo.md`.
- **Bash only in sub-agents.** Bash is intentionally excluded from top-level allowed-tools and only granted to Phase 2/3 sub-agents. Sub-agent instructions explicitly prohibit write commands.
- **Scan limits enforced.** Max 50 lines per file read, max 4 directory levels, max 500 files per listing. For very large repos (>5000 files), focus on root configs and first-level subdirectories.
- **Every recommendation needs evidence.** Cite specific file paths, metrics, or absence evidence. Never recommend a primitive without explaining what analysis data supports it.
- **Expose uncertainty honestly.** Every intervention must include `evidence_class` and `confidence`; do not present heuristic or repo-policy mappings as settled science.
- **No generation.** This skill produces a diagnostic matrix, not actual primitives. Recommend `/scaffold-skill`, manual CLAUDE.md creation, or hook setup — don't create them.
- **Present all findings before asking** about persistence or follow-up actions.
- **Error handling.** If Phase 2 scan agent fails entirely, report the error and stop. If Phase 3 analyzer fails, report partial results and continue to Phase 4 with available data. Never silently skip.
- **Graceful degradation.** Works without WebSearch (model knowledge only for validation, marked accordingly). Works without WebFetch.
- **Stop conditions.** If target folder does not exist, has no files, or is not accessible: report and stop immediately.
