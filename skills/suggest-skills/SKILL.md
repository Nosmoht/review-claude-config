---
name: suggest-skills
description: >
  Analyzes a repository to identify missing Claude Code skills with skeleton
  SKILL.md per suggestion. Triggered manually via `/suggest-skills [folder]`.
  Use when scaffolding initial primitives in a target folder that has no
  `.claude/skills/` or `agents/` directory, or when known signals
  (`pyproject.toml`, `Makefile`, repeated error patterns) suggest skill
  candidates that do not yet exist. Do NOT use for repo-structure audit —
  use /audit-repo instead. Do NOT use for existing-skill quality review —
  use /review-claude-config instead.
argument-hint: [folder]
allowed-tools: Agent, Bash, Read, Write, Glob, Grep, WebSearch, WebFetch
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
- `skills/review-claude-config/references/signal-catalog.md` — signal patterns and extraction criteria

Also read shared references (read-only, owned by review-claude-config):
- Read `${CLAUDE_PLUGIN_ROOT}/skills/review-claude-config/references/domain-cache/INDEX.md`. If found, note available domain cache entries for reuse. If not found, skip — no error.

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
- Review reports (`${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`) may exist
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
"Save suggestions report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-suggest-skills.md`?"

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.) Include `repo: <slug>` and optionally `origin: <git-remote-url>` in frontmatter.

If the user declines, skip report writing but still display the report path that would have been used.

**Frontmatter:** Use the frontmatter structure from `references/report-template.md` (see `## Frontmatter` section).

**Body:** Full report content as presented.

Before Write: scan the assembled report (frontmatter `target:` and the entire body) and replace any literal absolute home-directory prefix with `$HOME/`. The `~/.claude/hooks/block-sensitive-content.sh` PreToolUse hook denies Writes containing such prefixes.

Write to: `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-suggest-skills.md`

Use the current date and time for the timestamp. Create `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` if it does not exist.

### Step 3: Confirm and Next Steps

Tell the user the report file path and suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS suggest-skills report`

Then present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Scaffold a suggested skill" (Recommended) — description: `"Run /scaffold-skill plugin <name> for one of the suggested skills"`
- Option 2 label: "Review existing skills" — description: `"Run /review-claude-config <target> to audit current skill quality"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Scaffold a suggested skill": ask which skill from the suggestions, then invoke `/scaffold-skill`. On "Review existing skills": invoke `/review-claude-config` with the target folder. On "Done": acknowledge and stop.

## Quality measurement (mandatory between Phase 4 Step 1 and Step 2)

Without verification, this skill fails at **F7 — Discovery noise** (a candidate skill emits with no concrete recurring signal in the target repo, or duplicates an existing skill, polluting the action queue) and at **F1 — Predicate incompleteness** (a clearly-recurring workflow — e.g. `make deploy` appearing in 5+ CI configs — is missed by both Layer 1 table matching and Layer 2 open reasoning, leaving a gap). `suggest-skills` is pure DISCOVER-class: every emitted row is a heuristic candidate, not a predicate-based finding. Per category template Acknowledged residual #4, **D6 DISCOVERY_PRECISION is REPORTED, not blocking** — precision is feedback-loop-dependent (the user accepts/declines per suggestion downstream via `/scaffold-skill`), and the pipeline cannot close that loop in-session. Layer A STRICT-checks emission-gate completeness (`evidence_class`, `confidence`, extraction-criteria fields are present per row); Layer B distinguishes ADDED (suggestion duplicates an existing skill, or has no signal sources) from DROPPED (a clearly-recurring repo signal not surfaced); Layer C reports D6 with a footnote, never blocks on it.

Run the three layers BEFORE Phase 4 Step 2 (Persist Report). Treat the unsigned report (as presented in Step 1) written to a tempfile as `$REPORT`; treat the analyzed target folder (the value of `$ARGUMENTS` resolved in Phase 1) as `$TARGET`. Sensitive-content sweeps (hardcoded user-home prefixes, RFC1918 IPs) are NOT in Layer A — those are enforced at Write time by the `block-sensitive-content.sh` PreToolUse hook, which is the canonical defense; duplicating the regex here would itself violate the doc-content constraint.

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
               "repo_type", "existing_skills", "suggestions"]
missing_fm = [k for k in REQUIRED_FM if not re.search(rf"^{k}:", fm, re.M)]

schema_v_m = re.search(r"^schema_version:\s*(\d+)", fm, re.M)
schema_v = int(schema_v_m.group(1)) if schema_v_m else None

EVIDENCE_CLASSES = {"Proven result", "Engineering guidance",
                    "Repo default", "Low-evidence area"}
CONFIDENCES = {"High", "Medium", "Low"}
PRIORITIES = {"High", "Medium", "Low"}
CRITERIA   = {"Recurrence", "Verification",
              "Non-obviousness", "Generalizability"}
REPO_TYPES = {"Application", "Skills-Config", "Mixed"}

# Parse suggestion blocks. Each suggestion starts with `### N. <name> (Priority:`
sugg_blocks = re.split(r"^###\s+\d+\.\s+", body, flags=re.M)[1:]

bad_ec, bad_conf, bad_prio, bad_crit = [], [], [], []
for i, blk in enumerate(sugg_blocks, 1):
    head = blk.split("\n", 1)[0]
    # Priority in heading
    pm = re.search(r"Priority:\s*([A-Za-z]+)", head)
    if not pm or pm.group(1) not in PRIORITIES:
        bad_prio.append(f"sugg#{i}")
    # Evidence Class field
    ecm = re.search(r"\*\*Evidence Class:\*\*\s*([^\n]+)", blk)
    if not ecm or not any(ec in ecm.group(1) for ec in EVIDENCE_CLASSES):
        bad_ec.append(f"sugg#{i}")
    # Confidence field
    cm = re.search(r"\*\*Confidence:\*\*\s*([A-Za-z]+)", blk)
    if not cm or cm.group(1) not in CONFIDENCES:
        bad_conf.append(f"sugg#{i}")
    # Extraction criteria gate (>=3 of 4)
    passed_crit = sum(1 for c in CRITERIA
                      if re.search(rf"{re.escape(c)}\b.*?PASS", blk))
    if passed_crit < 3:
        bad_crit.append(f"sugg#{i}:passed={passed_crit}")

# repo_type membership (frontmatter)
rt_m = re.search(r"^repo_type:\s*([A-Za-z\-]+)", fm, re.M)
repo_type_ok = bool(rt_m) and rt_m.group(1) in REPO_TYPES

# suggestions[] count parity vs body block count
fm_sugg_names = re.findall(r"^\s*-\s+name:\s*([^\n]+)", fm, re.M)
fm_n = len(fm_sugg_names)
body_n = len(sugg_blocks)

# Skeleton starting-point disclaimer presence
skeleton_blocks = re.findall(r"```yaml[\s\S]*?```", body)
missing_disclaimer = sum(
    1 for s in skeleton_blocks
    if "starting-point skeleton" not in s
    and "starting point" not in s.lower()
)

# Determinism (SOFT): if env var set, diff suggestion-name set
det_path = os.environ.get("DETERMINISM_RUN_2_REPORT")
det_diff = None
if det_path and os.path.exists(det_path):
    with open(det_path) as f2: t2 = f2.read()
    names1 = set(re.findall(r"^###\s+\d+\.\s+([\w\-]+)", body, re.M))
    body2 = t2.split("---\n", 2)[-1] if t2.startswith("---") else t2
    names2 = set(re.findall(r"^###\s+\d+\.\s+([\w\-]+)", body2, re.M))
    det_diff = sorted(names1 ^ names2)

rows = []
def add(sev, name, val, ok, note=""):
    flag = "" if ok else (" FAIL" if sev == "STRICT" else " warn")
    rows.append((sev, name, val, flag, note))

add("STRICT", "frontmatter_present",        "yes", bool(fm_match))
add("STRICT", "required_frontmatter_keys",  f"missing={missing_fm}",
    len(missing_fm) == 0)
add("STRICT", "schema_version_pinned",      f"v{schema_v}", schema_v == 1,
    note="bump invalidates analytics consumers")
add("STRICT", "repo_type_in_vocab",         str(rt_m.group(1) if rt_m else None),
    repo_type_ok, note="closed set: Application/Skills-Config/Mixed")
add("STRICT", "suggestion_evidence_class",  f"missing={bad_ec}",
    len(bad_ec) == 0, note="every row needs an evidence_class")
add("STRICT", "suggestion_confidence",      f"missing={bad_conf}",
    len(bad_conf) == 0, note="every row needs a confidence")
add("STRICT", "suggestion_priority_valid",  f"bad={bad_prio}",
    len(bad_prio) == 0)
add("STRICT", "extraction_criteria_gate",   f"under_3={bad_crit}",
    len(bad_crit) == 0, note=">=3 of 4 PASS required per Hard Rules")
add("STRICT", "skeleton_disclaimer",        f"missing_in={missing_disclaimer}",
    missing_disclaimer == 0,
    note="starting-point disclaimer required per Hard Rules")
add("SOFT",   "suggestion_count_parity",    f"fm={fm_n} body={body_n}",
    fm_n == body_n, note="frontmatter suggestions[] count vs body block count")
status_present = bool(re.search(r"^#+\s+Status\b", body, re.M))
add("SOFT",   "status_heading_present",     str(status_present), True,
    note="suggest-skills uses priority tiers, no Status enum")
if det_diff is not None:
    add("SOFT", "determinism_suggestion_set", f"symmetric_diff={len(det_diff)}",
        len(det_diff) == 0,
        note="LLM-judged candidates may shift across runs")

fail = 0
print(f"{'severity':8} {'metric':32} {'value':30} {'flag':>6}  note")
for sev, name, val, flag, note in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:8} {name:32} {str(val)[:30]:30} {flag:>6}  {note}")
sys.exit(1 if fail else 0)
PY
```

Metric coverage matrix (which failure class each STRICT row catches):

| Layer-A row                       | Catches                       |
|-----------------------------------|-------------------------------|
| `frontmatter_present`             | F5 (report-shape break)       |
| `required_frontmatter_keys`       | F5                            |
| `schema_version_pinned`           | F10                           |
| `repo_type_in_vocab`              | F5 (enum drift)               |
| `suggestion_evidence_class`       | F7 (D6 emission gate)         |
| `suggestion_confidence`           | F7 (D6 emission gate)         |
| `suggestion_priority_valid`       | F5 (priority-tier drift)      |
| `extraction_criteria_gate`        | F7 (gate enforcement)         |
| `skeleton_disclaimer`             | F5 (hard-rule conformance)    |
| `suggestion_count_parity` (SOFT)  | F5 (frontmatter↔body drift)   |
| `status_heading_present` (SOFT)   | per template residual         |
| `determinism_suggestion_set` SOFT | F6 (LLM judgment variance)    |

### Layer B — adversarial critic dispatch (ADDED vs DROPPED recall)

Dispatch a fresh subagent. The critic operates on the pair `(repo-scan summary, suggestions report)`. Because every row in B is a heuristic suggestion (no FINDING-vs-SUGGESTION split — this skill is pure DISCOVER), the critic's grounding pass asks only "does this suggestion cite at least one observable signal in A?", and the recall pass asks "does A contain a clearly-recurring workflow that B did NOT surface as a suggestion?". DROPPED items here are advisory (per D6, non-blocking), but the critic still surfaces them so the user can decide whether to extend the suggestion set before persistence.

```
Agent({
  description: "Blind suggest-skills critic (ADDED/DROPPED recall)",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind discovery-critic. Two artifacts are attached:\n" +
    "\n" +
    "A: a repo-scan summary from the target repository (file tree + " +
    "CLAUDE.md excerpt + toolchain list + .github/workflows + Makefile " +
    "targets + existing-skill inventory under .claude/skills/ and " +
    ".claude/agents/).\n" +
    "B: a skill-suggestions report containing N suggestion blocks, each " +
    "with: name, priority (High/Medium/Low), score, evidence_class, " +
    "confidence, signal_sources, extraction-criteria pass/fail, " +
    "rationale, skeleton SKILL.md.\n" +
    "\n" +
    "For EACH suggestion block in B:\n" +
    "  GROUNDED — the signal_sources cite a passage or file in A that " +
    "an alert reader would recognize as a recurring workflow signal, AND " +
    "no existing skill in A's .claude/skills/ inventory already covers " +
    "the same workflow.\n" +
    "  ADDED — the suggestion either (i) cites a signal not present in A, " +
    "or (ii) duplicates an existing skill in A's inventory (>60% " +
    "workflow overlap per the skill's documented coverage), or (iii) " +
    "describes a single-command operation that fails the Non-obviousness " +
    "gate.\n" +
    "\n" +
    "Separately, scan A for clearly-recurring workflow signals B did " +
    "NOT surface as a suggestion. Use the signal-catalog categories " +
    "(documentation workflow / tech-stack lifecycle / CI-CD / git " +
    "conventions / quality-config) to recognize candidates. If you find " +
    "a passage in A that meets >=3 of 4 extraction criteria " +
    "(Recurrence, Verification, Non-obviousness, Generalizability) and " +
    "B does not propose a corresponding suggestion, classify as:\n" +
    "  DROPPED — recurring workflow that should have been suggested " +
    "(advisory only — D6 reports, does not block).\n" +
    "\n" +
    "Report ONE block per item. Format:\n" +
    "  [GROUNDED|ADDED|DROPPED]: <suggestion-name or 'no-suggestion'>\n" +
    "  evidence_in_A: '<short quote or path>'\n" +
    "  evidence_in_B: '<short quote or suggestion-name>'\n" +
    "  reason: <=2 sentences\n" +
    "\n" +
    "Do not rate report quality. Do not praise coverage. Report under " +
    "600 words.\n" +
    "\n" +
    "A:\n<paste repo-scan summary; for large repos paste top-level + " +
    "first-level dirs + .github/workflows + Makefile + CLAUDE.md first " +
    "80 lines + existing-skill inventory>\n" +
    "\n" +
    "B:\n<paste $REPORT contents>"
})
```

**Order-swap mandate**: dispatch a second time with artifact labels reversed (A=report, B=repo-scan-summary). Take the union of items flagged across both runs (de-dup by `suggestion-name × evidence_in_A`). Position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791).

Output vocabulary maps to Layer C as: `GROUNDED` → no impact; `ADDED` → D2 NO; `DROPPED` → D5 reported (non-blocking per D6 carve-out). `WEAKENED` is not used for this skill — priority/score recalibration is a Layer A gate, not a critic judgment.

### Layer C — binary rubric (6 yes/no dimensions)

```
D1 FRONTMATTER_CONFORMANT     Frontmatter declares every required key
                              (generated_by, schema_version, date,
                              target, repo_type, existing_skills,
                              suggestions[]) AND schema_version is the
                              pinned value AND repo_type belongs to the
                              closed set {Application, Skills-Config,
                              Mixed}. The skill emits no `### Status`
                              heading by design (priority tiers
                              substitute); D1 covers frontmatter shape
                              only. Catches F5, F10.

D2 EVIDENCE_GROUNDED          Every suggestion's signal_sources cite at
                              least one observable passage or file in
                              $TARGET (no Layer-B ADDED items survive),
                              AND no suggestion duplicates an existing
                              skill from Category B inventory at >60%
                              overlap. Catches F2, F9, plus the
                              duplicate-skill case from Phase 2 Step 0.

D3 TAXONOMY_DISJOINT          No two suggestions cite identical
                              signal_sources AND name an overlapping
                              workflow span; suggestion names are
                              unique across the report. Trivially YES
                              when only one suggestion fires per
                              workflow signal. Catches F4 (per-skill
                              variant: same evidence span surfacing as
                              two candidates).

D4 PRIORITY_CALIBRATED        Each suggestion's priority (High/Medium/
                              Low) matches the score band declared in
                              Phase 3 Step 2 (7-9 = High, 4-6 = Medium,
                              1-3 = Low) AND the score value is the
                              arithmetic sum of Signal+Impact+
                              Feasibility (1-3 each, max 9). Catches
                              F8.

D5 RULE_CATALOG_COMPLETENESS  Layer-B critic surfaced ZERO ADDED
                              items (every suggestion cites a real
                              signal AND does not duplicate existing
                              coverage). DROPPED items are surfaced
                              but routed to D6 per the discovery-class
                              carve-out — D5 itself does not block on
                              DROPPED for this skill. Catches F1, F3 at
                              the emission gate only.

D6 DISCOVERY_PRECISION        Every suggestion row cites an
                              `evidence_class` from the canonical four-
                              token set (Proven result, Engineering
                              guidance, Repo default, Low-evidence
                              area) AND a `confidence` from {High,
                              Medium, Low} AND passes >=3 of 4
                              extraction criteria (Recurrence,
                              Verification, Non-obviousness,
                              Generalizability). Any DROPPED items
                              from Layer-B are appended to the report
                              as a footnote ("Layer-B suggested N
                              additional candidates not in this
                              report") but D6 stays YES — discovery
                              precision is REPORTED, NOT blocking, per
                              category template Acknowledged residual
                              #4. Catches F7 (emission-time only).
```

Layer-A row → Dimension mapping:
- `frontmatter_present`, `required_frontmatter_keys`, `schema_version_pinned`, `repo_type_in_vocab` → D1
- `suggestion_evidence_class`, `suggestion_confidence`, `extraction_criteria_gate` → D6
- `suggestion_priority_valid` → D4
- `skeleton_disclaimer` → D1 (hard-rule conformance)

Layer-B item → Dimension mapping:
- `ADDED` → D2 NO (signal absent or duplicates existing skill)
- `DROPPED` → D6 footnote (advisory only, non-blocking)
- `GROUNDED` → no impact

### Reconciliation outcomes

- **All STRICT pass + zero ADDED** → proceed to Phase 4 Step 2 (Persist Report). If DROPPED items exist, append them as a footnote ("Layer-B suggested N additional candidates not in this report") before persistence.
- **Any STRICT fail OR any ADDED** → patch inline: drop suggestions that duplicate existing skills, drop suggestions with no observable signal in $TARGET, restore missing fields. Re-run Layer A on the patched report. Max 2 iterations. If still failing after iteration 2, surface to user with the full ledger and DO NOT persist the report.
- **Only SOFT warnings** (e.g. determinism symmetric-diff non-empty, suggestion-count parity drift, DROPPED items at D6) → append a footnote ("Discovery precision: Layer-B suggested N candidates not in this report; suggestion set may vary across runs") and proceed.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Discovery-class precision feedback latency** — D6 only checks emission-time fields (evidence_class, confidence, extraction-criteria pass count). The user-rejection rate that defines F7 requires post-acceptance feedback (the maintainer accepts/declines per suggestion via `/scaffold-skill`); the pipeline cannot close the loop in-session. This is the load-bearing residual for `suggest-skills` per category template Acknowledged residual #4.
2. **Cross-repo pattern correlation** — the pipeline judges one report against one target repo. A skill candidate visible only across multiple audited repos (e.g., a `deploy-validator` pattern detectable only when 10 repo audits are co-analyzed) escapes both Layers A and B. Mitigation: cross-repo analysis is `/review-analytics`'s remit.
3. **Heuristic extraction-criteria calibration** — the 3/4 gate (Recurrence, Verification, Non-obviousness, Generalizability) is a repo-policy heuristic, not a benchmark-settled filter. D6 checks that each suggestion exposes its gate-pass evidence; it does not validate that the gate itself maps to long-run user-acceptance rate.
4. **Repo-scan completeness** — Layer B's critic sees a summarized scan of the target repo (file tree + sampled top files + CLAUDE.md excerpt + existing-skill inventory), not the full repo content. A DROPPED workflow hidden in a file the scan summary did not include cannot be surfaced. Mitigation: Phase 1's scan agent enforces completion criteria per Category A-F; gaps surface as "No results" rows visible to the critic.

The Output report MUST list which residual classes apply when the critic surfaces DROPPED items or when SOFT determinism warnings fire, so the user has one last human-glance opportunity.

## Hard Rules

- **Read-only on target repository.** Never modify any existing file in the analyzed repository. The only file this skill writes is the suggestions report at `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-suggest-skills.md`.
- **Every suggestion needs evidence.** Concrete repository signal + web-validated rationale (or `[no web verification]` if WebSearch unavailable).
- **Expose uncertainty honestly.** Every suggestion must include `evidence_class` and `confidence` using the canonical evidence vocabulary plus an explicit certainty signal.
- **No duplicates.** Cross-check every suggestion against existing skills/agents inventory.
- **Extraction criteria gate.** Every suggestion must pass at least 3 of 4 criteria (Recurrence, Verification, Non-obviousness, Generalizability).
- **Skeletons are starting points.** Every skeleton must include the note: "This is a starting-point skeleton, not a production-ready skill." Skeletons conform to the [Agent Skills Specification](https://agentskills.io/specification): `name` + `description` required.
- **Present all suggestions before asking** about follow-up actions.
- **Error handling.** If the Phase 1 scan agent fails entirely, report the error and stop. If a Phase 2 analysis agent fails, report the failure with partial results and continue with remaining categories. Never silently skip.
- **Graceful degradation.** Works without WebSearch (model knowledge only, marked accordingly). Works without WebFetch (WebSearch snippets only).

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
