---
name: audit-repo
description: >
  Analyzes a repo for needed Claude Code primitives and produces a prioritized
  intervention matrix. Use when setting up or diagnosing a Claude Code
  configuration. Do NOT use for skill-gap suggestion only — use /suggest-skills instead.
argument-hint: [folder]
allowed-tools: Agent, Bash, Read, Write, Glob, Grep, WebSearch, WebFetch
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
- Locate via Glob: `**/review-claude-config/references/signal-catalog.md`
- This provides the Application Signal Table and Skills Repository Signal Table for Phase 4B skill detection

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)

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

#### Signal catalog checks

Using the signal-catalog.md loaded in Phase 1, match Phase 2 scan results
against the Agent Candidate Signal Table.

For each signal row in the table:
1. Check if the Detection Pattern matches Phase 2 findings
2. Check if a corresponding agent already exists (from Phase 1 Step 2 inventory)
3. If the signal matches AND no existing agent covers it → candidate

#### Concern-topology checks (carry-over)

From Phase 2 concern topology:
- Separate lint/test configs per subdirectory → specialized agent per domain
- Security scanning tools in CI (Trivy, Snyk, CodeQL, gitleaks) → security-reviewer agent
- Separate deployment targets (Terraform, Helm, CDK) → infra-architect agent
- CODEOWNERS with clear responsibility boundaries → agent per ownership area

#### Validation gate

Decision: only recommend Agent if concern has BOTH its own toolchain AND its own evaluation criteria. Otherwise recommend Skill.

This is an intentionally conservative repo policy to avoid inflating agent count.

### 4D: Hook/Rule Candidates

#### Signal catalog checks (Rule track)

Using the signal-catalog.md loaded in Phase 1, match Phase 2 scan results
against the Rule Candidate Signal Table.

For each signal row in the table:
1. Check if the Detection Pattern matches Phase 2 findings
2. Check if a corresponding rule already exists (from Phase 1 Step 2 inventory)
3. If the signal matches AND no existing rule covers it → candidate

#### Constraint-extraction checks (carry-over, both tracks)

From Phase 2 constraint extraction:
- Pre-commit hooks (.pre-commit-config.yaml, .husky/) → PostToolUse hooks for formatters
- Branch protection rules → Rule ("Never commit directly to main")
- Secret scanning in CI → PreToolUse hook for secret detection
- .gitignore/.dockerignore patterns → file-write restriction rules
- Mandatory review labels → permission config recommendation

#### Validation gate

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

After presenting, confirm before writing: "Save audit report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-audit-repo.md`?"

Before Write: scan the assembled report (frontmatter `target:`, optional `origin:`, and the entire body including evidence citations and action-plan command paths) and replace any literal absolute home-directory prefix with `$HOME/`. The `~/.claude/hooks/block-sensitive-content.sh` PreToolUse hook denies Writes containing such prefixes.

If confirmed, write the report. Create `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` if it does not exist. If declined, display the path that would have been used.

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

## Quality measurement (mandatory between Phase 5 Step 3 and Step 4)

Without verification, this skill fails at **F1 — Predicate incompleteness** (the intervention matrix misses a high-token-cost component, e.g. a 10K-line reference file omitted from the Component Breakdown) and at **F7 — Discovery noise** (a recommended primitive emits with no concrete gap in the target repo, polluting the action plan). `audit-repo` is partially DISCOVER-shaped — its output mixes (a) predicate-based audit findings (missing CLAUDE.md, missing settings.json, deterministic token thresholds) and (b) heuristic discovery suggestions (intervention-matrix candidates derived from signal patterns). Layer A STRICT-checks the predicate subset, SOFT-warns on the discovery subset; Layer B distinguishes FINDING (verifiable against the target repo) from SUGGESTION (heuristic, low-precision tolerable per D6); Layer C reports D6 but does not block on it (per Acknowledged residual #1 — discovery feedback latency).

Run the three layers BEFORE Phase 5 Step 4 (Present and Persist). Treat the unsigned report at the path computed in Step 3 as `$REPORT`; treat the analyzed target folder as `$TARGET`. Sensitive-content sweeps (hardcoded user-home prefixes, RFC1918 IPs) are NOT in Layer A — those are enforced at Write time by the `block-sensitive-content.sh` PreToolUse hook, which is the canonical defense; duplicating the regex here would itself violate the doc-content constraint.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024), Beyond Consensus (NUS 2025), `skills/review-claude-config/references/evidence-contract.md` (canonical evidence-class vocabulary used in D6), `skills/review-claude-config/references/signal-catalog.md` (catalog-completeness reasoning for D5).

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the produced report file. Any non-zero `STRICT` row → abort and report to user; any `SOFT` row delta → log warning, surface in output footnote, do not auto-persist.

```bash
python3 - "$REPORT" "$TARGET" <<'PY'
import re, sys, os
report_path = sys.argv[1]
target_path = sys.argv[2] if len(sys.argv) > 2 else None

with open(report_path) as f: t = f.read()

# parse frontmatter
fm_match = re.match(r"^---\n(.*?)\n---\n", t, re.S)
if not fm_match:
    print("FAIL STRICT frontmatter_present: no YAML frontmatter detected")
    sys.exit(1)
fm = fm_match.group(1)
body = t[fm_match.end():]

REQUIRED_FM = ["generated_by", "schema_version", "date", "target",
               "existing_claude_config", "repo_type", "intervention_count",
               "summary"]
missing_fm = [k for k in REQUIRED_FM if not re.search(rf"^{k}:", fm, re.M)]

schema_v_m = re.search(r"^schema_version:\s*(\d+)", fm, re.M)
schema_v = int(schema_v_m.group(1)) if schema_v_m else None

EVIDENCE_CLASSES = {"repo-policy", "deterministic", "validated",
                    "literature", "advisory", "observation"}
PRIORITIES = {"P0", "P1", "P2"}
CONFIDENCES = {"High", "Medium", "Low"}
ERROR_CLASSES = {"Toolchain", "Navigation", "Convention",
                 "Architecture", "Repetition", "Domain", "Security"}

matrix_rows = re.findall(r"^\|\s*(P[012])\s*\|([^\n]+)\|\s*$", body, re.M)
bad_priority = [r for r in matrix_rows if r[0] not in PRIORITIES]

rows_full = re.findall(r"^\|(?:[^\n]+)\|\s*$", body, re.M)
rows_missing_ec, rows_missing_conf = [], []
bad_error_class = []
for row in rows_full:
    if re.match(r"^\|[\s\-:|]+\|$", row): continue
    if "P0" not in row and "P1" not in row and "P2" not in row: continue
    if not any(ec in row for ec in EVIDENCE_CLASSES): rows_missing_ec.append(row[:80])
    if not any(c in row for c in CONFIDENCES):       rows_missing_conf.append(row[:80])
    # Extract error_class cell (column 3 after priority: primitive | error_class | ...)
    cells = [c.strip() for c in row.strip("|").split("|")]
    if len(cells) >= 3:
        ec_value = cells[2]
        if ec_value and ec_value not in ERROR_CLASSES:
            bad_error_class.append(f"{row[:60]}... error_class={ec_value!r}")

ic_m = re.search(r"^intervention_count:\s*(\d+)", fm, re.M)
ic = int(ic_m.group(1)) if ic_m else None
action_boxes = len(re.findall(r"^- \[ \] \*\*#\d+\*\*", body, re.M))

# Determinism (SOFT): if env var set, diff intervention row set
det_path = os.environ.get("DETERMINISM_RUN_2_REPORT")
det_diff = None
if det_path and os.path.exists(det_path):
    with open(det_path) as f2: t2 = f2.read()
    rows2 = set(re.findall(r"^\|\s*P[012]\s*\|[^\n]+\|\s*$", t2, re.M))
    rows1 = set(re.findall(r"^\|\s*P[012]\s*\|[^\n]+\|\s*$", body, re.M))
    det_diff = sorted(rows1 ^ rows2)

rows = []
def add(sev, name, val, ok, note=""):
    flag = "" if ok else (" FAIL" if sev == "STRICT" else " warn")
    rows.append((sev, name, val, flag, note))

add("STRICT", "frontmatter_present",       "yes", bool(fm_match))
add("STRICT", "required_frontmatter_keys", f"missing={missing_fm}", len(missing_fm) == 0)
add("STRICT", "schema_version_pinned",     f"v{schema_v}", schema_v == 1,
    note="bump invalidates analytics consumers")
add("STRICT", "intervention_priority_valid", f"bad={bad_priority}", len(bad_priority) == 0)
add("STRICT", "intervention_error_class_valid", f"bad={bad_error_class}",
    len(bad_error_class) == 0,
    note="error_class must be in D3 closed set {Toolchain, Navigation, Convention, Architecture, Repetition, Domain, Security}")
add("STRICT", "intervention_matrix_complete_ec",   f"missing={len(rows_missing_ec)}",
    len(rows_missing_ec) == 0,   note="every matrix row needs an evidence_class")
add("STRICT", "intervention_matrix_complete_conf", f"missing={len(rows_missing_conf)}",
    len(rows_missing_conf) == 0, note="every matrix row needs a confidence")
add("STRICT", "action_plan_matches_count", f"boxes={action_boxes} ic={ic}",
    ic is None or action_boxes >= ic, note="checkbox count >= intervention_count")
status_present = bool(re.search(r"^#+\s+Status\b", body, re.M))
add("SOFT",   "status_heading_present", str(status_present), True,
    note="audit-repo uses intervention-matrix instead of a Status enum")
if det_diff is not None:
    add("SOFT", "determinism_matrix_set", f"symmetric_diff={len(det_diff)}",
        len(det_diff) == 0, note="LLM-judged candidates may shift across runs")

fail = 0
print(f"{'severity':8} {'metric':36} {'value':28} {'flag':>6}  note")
for sev, name, val, flag, note in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:8} {name:36} {str(val)[:28]:28} {flag:>6}  {note}")
sys.exit(1 if fail else 0)
PY
```

Metric coverage matrix (which failure class each STRICT row catches):

| Layer-A row                              | Catches                |
|------------------------------------------|------------------------|
| `frontmatter_present`                    | F5 (report shape)      |
| `required_frontmatter_keys`              | F5                     |
| `schema_version_pinned`                  | F10                    |
| `intervention_priority_valid`            | F5 (enum drift)        |
| `intervention_error_class_valid`         | F4 (D3 taxonomy drift) |
| `intervention_matrix_complete_ec`        | F7 (D6 emission gate)  |
| `intervention_matrix_complete_conf`      | F7 (D6 emission gate)  |
| `action_plan_matches_count`              | F5 (count drift)       |
| `status_heading_present` (SOFT)          | per template residual  |
| `determinism_matrix_set` (SOFT)          | F6 (LLM judgment)      |

### Layer B — adversarial critic dispatch (FINDING vs SUGGESTION split)

**Layer-B-Gate.** Per `docs/skill-verification-architecture.md`, AUDIT output is structured extraction when predicates are mechanical. Layer B fires when ANY of the following criteria hold for this skill's run:

- (a) The skill's predicate set includes LLM-classified items (closed-set classification, taxonomy mapping, MAST-class assignment, behavioral-signal detection, free-form severity assessment).
- (b) The skill emits free-form prose findings beyond a closed-set predicate match.
- (c) The operator observes judgment-shaped failure modes during a dry-run (false positives traceable to a heuristic, ambiguous classifications, inter-run disagreement).

For purely-mechanical audits (file-exists / regex-match / exit-code only, with no LLM-judged predicates and no free-form prose), skip Layer B and rely on Layer A + Layer C alone. Surface the gate decision in the report under a body heading: `## Layer B (fired: <criterion-met>)` or `## Layer B (skipped: predicates are mechanical)` — do NOT introduce a frontmatter `layer_b_fired` field (no schema-parity treatment defined; surface in body where context is also reported).

Dispatch a fresh subagent. The critic must distinguish FINDING (verifiable against the target repo's deterministic state — e.g. a missing CLAUDE.md, a file >2000 LOC, a sprawl score >100) from SUGGESTION (heuristic — e.g. "a deploy-validator skill would be useful because CI has deploy steps"). FINDING rows are checked for grounding; SUGGESTION rows are checked for emission-gate completeness only (evidence_class + confidence + non-empty evidence cell).

```
Agent({
  description: "Blind audit-repo critic (FINDING vs SUGGESTION recall)",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind audit-critic. Two artifacts are attached:\n" +
    "\n" +
    "A: a repo-scan summary (file tree + CLAUDE.md excerpt + toolchain " +
    "list + top-20 largest source files + existing-primitive inventory) " +
    "from the target repository.\n" +
    "B: an audit report containing an Intervention Matrix (rows: priority " +
    "| primitive | error_class | token_impact | evidence_class | " +
    "confidence | evidence).\n" +
    "\n" +
    "For EACH row in B, first classify the row as:\n" +
    "  FINDING — predicate-based (missing CLAUDE.md, sprawl >100, " +
    "files >2000 LOC, missing toolchain section) — verifiable against A.\n" +
    "  SUGGESTION — heuristic (recommended new skill/agent/hook) — " +
    "judgment-call against A.\n" +
    "\n" +
    "Then judge each row:\n" +
    "  GROUNDED — evidence in A matches the row's claim AND severity/" +
    "priority is calibrated (FINDING rows only — SUGGESTION rows pass on " +
    "emission-gate completeness alone).\n" +
    "  WEAKENED — FINDING with priority/token_impact stronger than " +
    "evidence in A supports.\n" +
    "  ADDED — row cites no evidence resolvable in A (FINDING only — " +
    "SUGGESTION may legitimately cite repo-pattern absence).\n" +
    "\n" +
    "Separately, scan A for signals B did NOT flag. Use the audit's own " +
    "error-class taxonomy (Toolchain, Navigation, Convention, " +
    "Architecture, Repetition, Domain, Security) to recognize misses. " +
    "If you find a passage in A that an alert reader would expect to " +
    "trigger a FINDING row in B but none cites it, classify as:\n" +
    "  DROPPED — predicate that should have fired but did not " +
    "(FINDING-class only; DROPPED-SUGGESTION is out of scope per D6 " +
    "discovery-feedback latency).\n" +
    "\n" +
    "Report ONE block per item. Format:\n" +
    "  [GROUNDED|WEAKENED|ADDED|DROPPED]: row-# (or 'no-row' for " +
    "DROPPED) | class=[FINDING|SUGGESTION]\n" +
    "  evidence_in_A: '<short quote or path>'\n" +
    "  evidence_in_B: '<short quote or row-#>'\n" +
    "  reason: <≤2 sentences>\n" +
    "\n" +
    "Do not rate report quality. Do not summarize. Report under 600 words.\n" +
    "\n" +
    "A:\n<paste repo-scan summary; for large repos paste top-level + " +
    "first-level dirs + top-20 files by size + CLAUDE.md first 80 lines>\n" +
    "\n" +
    "B:\n<paste $REPORT contents>"
})
```

**Order-swap mandate**: dispatch a second time with artifact labels reversed (A=report, B=repo-scan-summary). Take the union of items flagged across both runs (de-dup by `row-# × evidence_in_A`). Position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791).

Output vocabulary maps to Layer C as: `GROUNDED` → no impact; `ADDED` → D2 NO; `WEAKENED` → D4 NO; `DROPPED` (FINDING-class) → D5 NO; `DROPPED` (SUGGESTION-class) → D6 reported (non-blocking).

### Layer C — binary rubric (6 yes/no dimensions)

```
D1 FRONTMATTER_CONFORMANT     Frontmatter declares every required key
                              (generated_by, schema_version, date, target,
                              existing_claude_config, repo_type,
                              intervention_count, summary[]) AND
                              schema_version is the pinned value. The
                              skill emits no `### Status` heading by
                              design; D1 covers frontmatter shape only.
                              Catches F5, F10.

D2 EVIDENCE_GROUNDED (FINDING) Every FINDING row's evidence cell cites a
                              resolvable path/metric/excerpt in $TARGET
                              (Layer A excerpt-presence check passed AND
                              no Layer-B ADDED items on FINDING rows).
                              SUGGESTION rows exempt — judged in D6.
                              Catches F2, F9.

D3 TAXONOMY_DISJOINT          No two rows assign distinct error_class or
                              primitive type to the same evidence span.
                              error_class is drawn from the documented
                              closed set {Toolchain, Navigation,
                              Convention, Architecture, Repetition,
                              Domain, Security}. Catches F4.

D4 PRIORITY_CALIBRATED        Each row's priority (P0/P1/P2) matches the
                              priority bands declared in Phase 5 Step 1
                              ("P0 = CLAUDE.md basics + critical
                              navigation; P1 = hooks + skills + security;
                              P2 = agents + domain"). No Layer-B
                              WEAKENED items survive. Catches F8.

D5 RULE_CATALOG_COMPLETENESS  Layer-B critic surfaced ZERO `DROPPED`
                              items at FINDING class. FINDING-class
                              predicates are the audit's load-bearing
                              promise; SUGGESTION-class DROPPED maps to
                              D6 (reported, not blocking). Catches F1,
                              F3.

D6 DISCOVERY_PRECISION        Every Intervention Matrix row (FINDING
                              and SUGGESTION alike) cites an
                              `evidence_class` from the canonical six-
                              token set (repo-policy, deterministic,
                              validated, literature, advisory,
                              observation) AND a `confidence` from
                              {High, Medium, Low} AND a non-empty
                              evidence cell. SUGGESTION-class DROPPED
                              items from Layer-B are appended to the
                              report as a footnote ("Layer-B suggested
                              N additional candidates not in this
                              matrix") but D6 stays YES — discovery
                              precision is reported, NOT blocking.
                              Catches F7 (emission-time only).
```

Layer-A row → Dimension mapping:
- `frontmatter_present`, `required_frontmatter_keys`, `schema_version_pinned` → D1
- `intervention_matrix_complete_ec`, `intervention_matrix_complete_conf` → D6
- `intervention_priority_valid` → D4
- `intervention_error_class_valid` → D3
- `action_plan_matches_count` → D1

Layer-B item → Dimension mapping:
- `ADDED` (FINDING) → D2 NO
- `WEAKENED` (FINDING) → D4 NO
- `DROPPED` (FINDING) → D5 NO
- `DROPPED` (SUGGESTION) → D6 footnote (no block)
- `GROUNDED` → no impact

### Reconciliation outcomes

- **All STRICT pass + zero ADDED/WEAKENED/DROPPED(FINDING)** → proceed to Phase 5 Step 4 (Present and Persist).
- **Any STRICT fail OR any ADDED/WEAKENED/DROPPED(FINDING)** → patch inline: drop fabricated rows, recalibrate priorities, add dropped predicate firings. Re-run Layer A on the patched report. Max 2 iterations. If still failing after iteration 2, surface to user with the full ledger and DO NOT persist the report.
- **Only SOFT warnings** (e.g. determinism symmetric-diff non-empty, `DROPPED` items at SUGGESTION class) → append a footnote ("Discovery precision: Layer-B suggested N candidates not in this matrix; matrix may vary across runs") and proceed.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Discovery-class precision feedback latency** — D6 only checks emission-time fields (evidence_class, confidence, non-empty evidence). The user-rejection rate that defines F7 requires post-acceptance feedback (the maintainer accepts/declines per row via `/apply-audit-findings`); the pipeline cannot close the loop in-session.
2. **Cross-repo pattern correlation** — the pipeline judges one report against one target repo. A pattern visible only across multiple audited repos (e.g., a slowly-emerging skill candidate detectable only when 10 audits are co-analyzed) escapes both Layers A and B. Mitigation: cross-repo analysis is `/review-analytics`'s remit, not this skill's.
3. **Heuristic-extraction-gate calibration** — Phase 4B's 3/4 extraction-criteria gate (Recurrence, Verification, Non-obviousness, Generalizability) is a repo-policy heuristic, not a benchmark-settled filter. D6 checks that each SUGGESTION row exposes its gate-pass evidence; it does not validate that the gate itself maps to long-run user-acceptance rate.
4. **Repo-scan completeness** — Layer B's critic sees a summarized scan of the target repo (file tree + sampled top files + CLAUDE.md excerpt), not the full repo content. A DROPPED predicate hidden in a file the scan summary did not include cannot be surfaced. Mitigation: Phase 2's scan agent enforces completion criteria per Category; gaps surface as "no instances found" rows visible to the critic.

The Output report MUST list which residual classes apply when the critic surfaces SUGGESTION-class DROPPED items or when SOFT determinism warnings fire, so the user has one last human-glance opportunity.

## Hard Rules

- **Read-only on target repository.** Never modify any existing file. The only file this skill writes is the audit report at `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-audit-repo.md`.
- **Bash scope.** At the top level, Bash is used only for `bash bin/repo-slug.sh "$(pwd)"` (slug resolution). All other Bash use is restricted to Phase 2/3 sub-agents, which explicitly prohibit write commands.
- **Scan limits enforced.** Max 50 lines per file read, max 4 directory levels, max 500 files per listing. For very large repos (>5000 files), focus on root configs and first-level subdirectories.
- **Every recommendation needs evidence.** Cite specific file paths, metrics, or absence evidence. Never recommend a primitive without explaining what analysis data supports it.
- **Expose uncertainty honestly.** Every intervention must include `evidence_class` and `confidence`; do not present heuristic or repo-policy mappings as settled science.
- **No generation.** This skill produces a diagnostic matrix, not actual primitives. Recommend `/scaffold-skill`, manual CLAUDE.md creation, or hook setup — don't create them.
- **Present all findings before asking** about persistence or follow-up actions.
- **Error handling.** If Phase 2 scan agent fails entirely, report the error and stop. If Phase 3 analyzer fails, report partial results and continue to Phase 4 with available data. Never silently skip.
- **Graceful degradation.** Works without WebSearch (model knowledge only for validation, marked accordingly). Works without WebFetch.
- **Stop conditions.** If target folder does not exist, has no files, or is not accessible: report and stop immediately.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
