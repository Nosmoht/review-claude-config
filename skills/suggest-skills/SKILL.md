---
name: suggest-skills
description: >
  Analyzes a repository to identify missing Claude Code skills with skeleton
  SKILL.md per suggestion. Use when setting up Claude Code or expanding skill
  coverage. Do NOT use to audit existing skill quality — use /review-claude-config.
argument-hint: [folder]
allowed-tools: Agent, Read, Write, Glob, Grep, WebSearch, WebFetch
disable-model-invocation: true
---

# Suggest Skills

Analyze a target repository and recommend Claude Code skills that should be created, based on repository signals and domain best practices. This skill combines deterministic signal matching with heuristic open reasoning; it is a discovery aid, not a scientifically closed method for skill-gap detection.

## Argument Handling

- `$ARGUMENTS` is the target folder path. If empty, use the current working directory.
- Validate the folder exists. If the folder has no files, report that and stop.

## Phase 1 — Setup and Discovery

### Step 0: Tool Availability Checks

Attempt a trivial WebSearch (e.g., "Claude Code documentation"). If it fails or is unavailable, set `websearch_available = false` and continue. Suggestions will use model knowledge only, marked `[no web verification]`.

Attempt a trivial WebFetch (e.g., fetch "https://docs.anthropic.com"). If it fails or is unavailable, set `webfetch_available = false` and continue. Analysis agents will use WebSearch snippets only instead of fetching full article content.

### Steps 1-2: Launch in parallel

**1. Load References**

Read these files from the skill's own `references/` directory:
- `references/signal-catalog.md` — signal patterns and extraction criteria

Also read shared references (read-only, owned by review-claude-config):
- Look for `references/domain-cache/INDEX.md` relative to the `review-claude-config` skill directory (sibling skill). If found, note available domain cache entries for reuse. If not found, skip — no error.

**2. Repository Scan Agent**

Launch an Agent (allowed-tools: Glob, Grep, Read) to collect raw repository signals. The agent returns **structured facts per category, not interpretations**.

```
Scan this repository and collect structured facts for each category below.
Return facts only — no skill suggestions or interpretations.

Scan limits: read at most 50 lines per file, scan at most 3 directory levels deep. If the repository is very large (>1000 files at top level), focus on root-level config files and the first level of subdirectories.

ERROR HANDLING:
- If a Glob pattern returns no results, report "NOT FOUND" for that item within the category.
- If a file cannot be read, report under the category: "ERROR: [path] — [reason]" and continue.
- Always produce output for every category, even if empty (use "No results" with brief explanation).

## Category A: Documentation
Search for workflow instructions and manual steps:
- Read CLAUDE.md if it exists. Extract: numbered process steps, "always do X"
  instructions, "before X do Y" patterns, workflow sections, tool usage patterns.
- Glob for .claude/rules/*.md — for each, extract: step count, topic, whether
  it describes a multi-step process.
- Read README.md if it exists. Extract: development workflow sections, setup
  instructions, contributing guides with process steps.
- Report in this exact format:

| Source | Type | Content |
|--------|------|---------|
| [CLAUDE.md/rules/README] | process/instruction/workflow | [extracted text] |

## Category B: Existing Skill/Agent Coverage
Build an inventory of what already exists:
- Glob: <folder>/.claude/skills/*/SKILL.md and <folder>/**/.claude/skills/*/SKILL.md
- Glob: <folder>/.claude/agents/*.md and <folder>/**/.claude/agents/*.md
- For each discovered item: read full content, extract name, description, and
  what workflows/domains it covers.
- Exclude paths containing: node_modules, .git, vendor, dist, build
- Report in this exact format:

| Path | Name | Type | Covers |
|------|------|------|--------|
| [file path] | [item name] | Skill/Agent | [workflows/domains covered] |

## Category C: Tech Stack
Detect languages, frameworks, and infrastructure:
- Glob for: package.json, go.mod, Cargo.toml, pyproject.toml, requirements.txt,
  Gemfile, pom.xml, build.gradle, composer.json
- For package.json: extract "scripts" keys and key dependencies
- Glob for: Dockerfile, docker-compose.yml, *.tf, kustomization.yaml,
  helm/Chart.yaml, k8s/*.yaml
- Report in this exact format:

| Category | Detected |
|----------|----------|
| Languages | [list] |
| Frameworks | [list] |
| Infrastructure | [list] |

## Category D: CI/CD & Automation
Scan pipelines, build targets, and scripts:
- Glob: .github/workflows/*.yml — for each, extract: name, trigger events,
  key steps
- Glob: Makefile, Justfile, Taskfile.yml — extract target names and descriptions
- Glob: scripts/* — list script names and infer purpose from filename/shebang
- Glob: .pre-commit-config.yaml — extract hook names
- Report in this exact format:

| Source | Name | Triggers | Key Steps |
|--------|------|----------|-----------|
| [CI/Makefile/scripts] | [name] | [trigger events] | [key steps] |

## Category E: Git Conventions (static files only)
Analyze git-related configuration and conventions from files on disk:
- Read .gitignore if present — extract patterns revealing project structure
  (build output dirs, generated code paths, ignored environments)
- Glob for .github/CODEOWNERS — extract ownership boundaries
- Read CHANGELOG.md or HISTORY.md if present — note release cadence
- Glob for .github/pull_request_template.md, .github/ISSUE_TEMPLATE/
- Report in this exact format:

| File | Purpose | Content |
|------|---------|---------|
| [path] | [purpose] | [relevant patterns or content] |

## Category F: Quality & Config
Scan for linting, testing, and formatting configuration:
- Glob for: .eslintrc*, .prettierrc*, biome.json, tsconfig.json,
  jest.config*, vitest.config*, pytest.ini, pyproject.toml (check for
  [tool.pytest] section), .pre-commit-config.yaml
- For test configs: note the test framework and any custom configuration
- Report in this exact format:

| Config File | Framework | Type |
|-------------|-----------|------|
| [path] | [framework name] | lint/test/format |

COMPLETION: You are done when all 6 categories (A through F) have a report section. If a category produces no results, include it with "No results."
```

If the repository scan agent fails entirely, report the error to the user and stop.

### Step 3: Classify Repository Type

Based on the scan results, classify the repository as one of two types:

**Application Repository** — Contains source code intended to be built, tested, deployed:
- Has package managers (package.json, go.mod, Cargo.toml, etc.)
- Has CI/CD pipelines, build scripts, test configs
- `.claude/` is a small part of the overall repository
- Signals: Categories C, D, F produced results

**Skills/Config Repository** — Primarily contains Claude Code skills, agents, and supporting references:
- No source code package managers or build tools
- `.claude/skills/` contains multiple skills (≥2)
- May have `research/`, `docs/`, or reference material as primary content
- Review reports (`.claude/reviews/`) may exist
- Signals: Category B produced ≥2 skills, Categories C/D/F produced few or no results

**Mixed Repository** — Has both source code AND significant skill/agent infrastructure:
- Has package managers AND ≥2 skills in `.claude/skills/`
- Apply both signal tables

The classification determines which signal table to use in Phase 2. Report the detected type in the output.

## Phase 2 — Signal Analysis

### Step 0: Build Coverage Map

Before generating suggestions, map what existing skills/agents already cover:
- For each existing skill/agent from Category B, extract the workflows and domains it addresses.
- Any suggestion that duplicates existing coverage is filtered out.
- If >60% of a suggestion's description overlaps with an existing skill, recommend an "enhancement to [existing-skill]" instead of a new skill.

### Step 1: Layer 1 — Table-Based Signal Matching

Launch an analysis Agent that matches scan results against the signal catalog tables. This is deterministic and fast — it catches known patterns.

**For Application Repositories:** Match against the **Application Signal Table**.
**For Skills/Config Repositories:** Match against the **Skills Repository Signal Table**.
**For Mixed Repositories:** Match against both tables.

The agent receives the signal catalog + Category B inventory as a **byte-identical shared prefix**, followed by all scan results. Allowed-tools: Read only (no web research needed for table matching).

```
You are matching repository scan results against a signal catalog.

## Signal Catalog
[Insert signal-catalog.md content here]

## Existing Skills Inventory
[Insert Category B results here]

## All Scan Results
[Insert all category results from Phase 1]

## Your Task

1. For each row in the applicable signal table, check whether the scan
   results contain the detection pattern. Report: MATCH or NO MATCH with
   the specific files/evidence.

2. For each MATCH, check against Existing Skills Inventory for duplicates.
   If >60% overlap with an existing skill, mark as "enhancement" not "new".

3. Return a structured list:

### Table Matches
| Signal | Match? | Evidence | Existing Coverage | Suggestion |
|--------|--------|----------|-------------------|------------|
| [row]  | YES/NO | [files]  | [overlap or none] | [skill name or skip] |

Example rows (for calibration):
| Database migrations | YES | migrations/ dir with 12 files | None | migrate-db |
| Test config without test skill | NO | — | — | — |
```

Layer 1 is deterministic pattern matching against a repo-maintained signal catalog, not a general theory of skill-gap detection.

### Step 2: Layer 2 — Open Reasoning

Launch a second analysis Agent that reasons about the repository — this catches opportunities the table cannot anticipate. The agent receives the full scan results, existing skill inventory, AND the Layer 1 table matches (to avoid duplicating those). This layer is intentionally heuristic, but constrained by evidence and extraction gates.

Allowed-tools: WebSearch, WebFetch, Read. If `webfetch_available = false`, omit WebFetch. If `websearch_available = false`, omit WebSearch.

```
You are analyzing a repository to identify missing Claude Code skills that
a static signal table would NOT catch. Another agent already matched known
patterns — your job is to reason about what else is missing.

Tools available: WebSearch (to validate domain value), WebFetch (to read full
article content), and Read. You are analyzing, not modifying.

[If WebFetch/WebSearch unavailable, omit from this line.]

## Repository Type: [Application / Skills-Config / Mixed]

## Existing Skills Inventory
[Insert Category B results here]

## All Scan Results
[Insert all category results from Phase 1]

## Layer 1 Results (already identified)
[Insert table match results — DO NOT duplicate these]

## Your Task

Think about this repository holistically. Look beyond file-pattern matching:

1. **Workflow gaps.** Read the CLAUDE.md, README, and rules files. Are there
   repeated multi-step processes that no existing skill covers? What does
   the team do manually that could be automated?

2. **Domain gaps.** Based on the tech stack and project structure, what
   domain-specific expertise would improve Claude's effectiveness here?
   Consider: what would a senior engineer joining this project wish they
   had as a skill?

3. **Lifecycle gaps.** Does the project have skills for creation but not
   maintenance? For analysis but not action? For individual items but not
   portfolio-level concerns?

4. **Cross-cutting gaps.** Are there patterns across multiple files/configs
   that suggest a coordinating skill? (e.g., multiple related scripts that
   could be orchestrated, or related configs that drift independently)

For each opportunity you identify:

1. **Validate with WebSearch.** Perform 1-2 WebSearch queries to confirm
   the domain benefits from skill-based automation. If WebSearch is
   unavailable, use model knowledge and mark [no web verification].
   Apply source quality criteria from `skills/review-claude-config/references/source-quality-criteria.md`:
   discard marketing/opinion/outdated content, prefer Tier 1-2 sources.

2. **Apply extraction criteria.** Each suggestion MUST pass at least 3 of 4:
   - Recurrence: Pattern appears in 2+ contexts
   - Verification: Workflow expressible as 5-10 clear steps
   - Non-obviousness: Requires multi-step logic or domain expertise
   - Generalizability: Works across different inputs/projects

3. **Check for duplicates** against both the Existing Skills Inventory
   AND the Layer 1 results.

4. **Assign output signals** for each valid suggestion:
   - `evidence_class`: canonical class from `skills/review-claude-config/references/evidence-contract.md`
   - `confidence`: High / Medium / Low

5. **Generate output** for each valid suggestion:

**Example suggestions (for calibration — show decision logic, not full skeletons):**

### Suggestion: validate-helm-charts
**Discovery Method:** Open reasoning (not table-matched)
**Signal Sources:** 12 Helm chart files in deploy/charts/, CI pipeline runs helm lint
**Signal Strength:** Strong — multiple charts with shared patterns, no validation skill
**Extraction Criteria:**
- Recurrence: PASS — 12 chart files across 3 services
- Verification: PASS — lint, template, dry-run, diff = 5 clear steps
- Non-obviousness: PASS — requires Helm domain knowledge + cluster context
- Generalizability: PASS — works for any Helm-based deployment
**Web Evidence:** Helm best practices confirm value of pre-deploy validation
**Rationale:** Repeated manual helm lint + template + diff cycles; a skill would standardize and catch drift.

### Suggestion: (rejected example — fails extraction criteria)
**Signal Sources:** Single .env.example file
**Extraction Criteria:**
- Recurrence: FAIL — only 1 file, no pattern
- Non-obviousness: FAIL — copying .env.example is a single command
**Decision:** Rejected — fails 2/4 criteria (needs 3/4). Single-command operations do not justify skills.

**Your suggestions follow this format:**

### Suggestion: [skill-name]

**Discovery Method:** Open reasoning (not table-matched)
**Evidence Class:** [Proven result / Engineering guidance / Repo default / Low-evidence area]
**Confidence:** [High/Medium/Low]
**Signal Sources:** [what you observed that triggered this]
**Signal Strength:** [Strong/Moderate] with justification
**Extraction Criteria:**
- Recurrence: [PASS/FAIL] — [evidence]
- Verification: [PASS/FAIL] — [evidence]
- Non-obviousness: [PASS/FAIL] — [evidence]
- Generalizability: [PASS/FAIL] — [evidence]
**Web Evidence:** [what WebSearch confirmed, or "[no web verification]"]
**Rationale:** [1-2 sentences on why this skill adds value]
**Skeleton SKILL.md:**
```yaml
---
name: [skill-name]
description: "[description with natural trigger keywords, max 1024 chars]"
allowed-tools: [minimal tool set needed]
---

# [Skill Name]

[2-4 sentence outline of what the skill would do]

## Key Steps
1. [step]
2. [step]
3. [step]

## Notes
This is a starting-point skeleton, not a production-ready skill.
```
**Recommended Reference Files:**
- references/[file].md — [what it would contain]

If you find no additional opportunities beyond Layer 1, report that explicitly.
Do not invent suggestions just to produce output.
```

If a Phase 2 analysis agent fails, report the failure with partial results and continue with the other layer.

## Phase 3 — Consolidation and Prioritization

The orchestrator (not a subagent) merges suggestions across category agents:

### Step 1: Deduplicate

Merge overlapping suggestions from different categories. If two agents suggest similar skills, combine their signal sources and keep the stronger evidence.

### Step 2: Score

Score each suggestion on three axes (1-3 each):

| Axis | 3 (High) | 2 (Medium) | 1 (Low) |
|------|----------|------------|---------|
| **Signal Strength** | 3+ independent signals across categories | 2 signals or strong single signal | 1 weak signal |
| **Impact** | Core workflow, high frequency, error-prone | Regular workflow, moderate frequency | Occasional workflow |
| **Feasibility** | Workflow clearly expressible in 5-10 steps | Workflow definable but complex | Workflow vague or requires extensive research |

**Priority** = Signal + Impact + Feasibility (max 9):
- 7-9 = **High** priority
- 4-6 = **Medium** priority
- 1-3 = **Low** priority

These scores are repo-level prioritization heuristics. Use them for ordering, not as evidence or certainty signals.

### Step 3: Filter

- Cap total suggestions at 10 after deduplication. If more than 10 remain, keep only the top 10 by priority score.
- Drop suggestions scoring below 4 (Low) unless fewer than 3 suggestions remain — always show at least the top 3 if available.
- Drop suggestions that fail the false positive gates:
  - Single-command operations don't justify skills (fails Non-obviousness)
  - No web evidence AND weak signal → drop
  - Fails Generalizability → too project-specific, drop

## Phase 4 — Presentation and Persistence

### Step 1: Present Report

Read `references/report-template.md` for the report body structure (see `## Report Body` section). Present the full report to the user, substituting actual values for all placeholder fields.

### Step 2: Persist Report

After presenting all suggestions, confirm before writing:
"Save suggestions report to `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-suggest-skills.md`?"

If the user declines, skip report writing but still display the report path that would have been used.

**Frontmatter:** Use the frontmatter structure from `references/report-template.md` (see `## Frontmatter` section).

**Body:** Full report content as presented.

Write to: `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-suggest-skills.md`

Use the current date and time for the timestamp. Create `<target>/.claude/reviews/` if it does not exist.

### Step 3: Confirm and Next Steps

Tell the user the report file path and suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS suggest-skills report`

Then end your response with this menu (substitute `<target>` with the analyzed folder):

---
**What's next?**
1. Scaffold a suggested skill → `/scaffold-skill plugin <name>`
2. Review existing skills → `/review-claude-config <target>`
3. Done

_Type a number to continue._

---

When the user responds: **1** → ask which skill from the suggestions, then invoke `/scaffold-skill`. **2** → invoke `/review-claude-config` with the target folder. **3** → acknowledge and stop.

## Hard Rules

- **Read-only on target repository.** Never modify any existing file in the analyzed repository. The only file this skill writes is the suggestions report at `<target>/.claude/reviews/YYYY-MM-DDTHHMMSS-suggest-skills.md`.
- **Every suggestion needs evidence.** Concrete repository signal + web-validated rationale (or `[no web verification]` if WebSearch unavailable).
- **Expose uncertainty honestly.** Every suggestion must include `evidence_class` and `confidence` using the canonical evidence vocabulary plus an explicit certainty signal.
- **No duplicates.** Cross-check every suggestion against existing skills/agents inventory.
- **Extraction criteria gate.** Every suggestion must pass at least 3 of 4 criteria (Recurrence, Verification, Non-obviousness, Generalizability).
- **Skeletons are starting points.** Every skeleton must include the note: "This is a starting-point skeleton, not a production-ready skill." Skeletons conform to the [Agent Skills Specification](https://agentskills.io/specification): `name` + `description` required.
- **Present all suggestions before asking** about follow-up actions.
- **Error handling.** If the Phase 1 scan agent fails entirely, report the error and stop. If a Phase 2 analysis agent fails, report the failure with partial results and continue with remaining categories. Never silently skip.
- **Graceful degradation.** Works without WebSearch (model knowledge only, marked accordingly). Works without WebFetch (WebSearch snippets only).
