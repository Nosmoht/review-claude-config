# Cross-Repo Probe Runbook

This runbook defines how to validate the `claude-config` plugin against external (non-self) repositories before declaring Cross-Repo-GA. One probe run = one external repo + one fresh Claude Code session + one structured findings report.

## Why this exists

The plugin is developed and dogfooded inside its own source repo. The internal `make validate` and `/review-claude-config` runs cannot detect:

- hardcoded path assumptions to this repo's layout
- coupling to this repo's `make` targets
- coupling to this repo's `.venv/` location
- domain-cache assumptions tied to this repo's research files
- hook-conflict modes when the consumer already has hooks
- token-cost behavior on different repo sizes
- report quality when the reviewer lacks this repo's domain context

A probe run on an external repo surfaces those failure modes empirically.

## Stop condition for Cross-Repo-GA

Two consecutive probe runs against **different** external repos produce zero Critical or High Cross-Repo-Findings. Probes can produce Medium and Low findings without blocking GA — these become deferred work.

## Probe procedure

### Pre-flight (5 min)

1. Confirm `claude-config@ntbc-plugins` is installed and up to date:

   ```bash
   claude plugin list | grep claude-config
   ```

   If version mismatches the latest tag on `Nosmoht/review-claude-config`, reinstall:

   ```bash
   claude plugin uninstall claude-config@ntbc-plugins
   claude plugin install claude-config@ntbc-plugins
   ```

2. `cd <probe-repo-path>`. The probe is run **from inside** the external repo, not from the source repo of the plugin.

3. Note the probe repo's identity in a scratch line for the finding-bodies later: `<repo-name>` + commit SHA at probe time + stack (Python / TS / Go / etc.) + size (file count, total LOC).

### The 5 probe commands

Run each in a fresh Claude Code session. Capture both Claude's output AND any errors in stderr. Do not edit files in the probe repo — the probe is read-only.

```bash
# 1) Audit the repo's primitive surface
/audit-repo

# 2) Review one of the repo's existing skills (pick the most non-trivial)
/review-skill <relative/path/to/SKILL.md>

# 3) Or, if no existing skill: scaffold a new one in external mode
/scaffold-skill external <relative/target/path> <skill-name>

# 4) Try the full sweep against a small subset
/review-claude-config <relative/scope>

# 5) Inspect the generated reports for grounding-quality
ls $CLAUDE_PLUGIN_DATA/reports/<repo-slug>/
```

### Expected breakage classes

For each command, observe and classify any reibung against the catalog below. Findings outside the catalog are still valid — extend the catalog if a new class emerges.

| Class | Signal | Severity floor |
|---|---|---|
| **Hard-coded path** | Plugin tries to read `~/workspace/review-claude-config/...` from inside probe repo | Critical |
| **Tooling assumption** | Plugin expects `make validate` to exist; probe repo has no Makefile | Critical |
| **Layout assumption** | Plugin expects `skills/`, `.claude/skills/`, `hooks/hooks.json`; probe repo has none | High (if blocks command) / Medium (if just degrades output) |
| **Domain-cache miss** | A domain-cache entry references a file that exists in source repo only | High (if loaded into prompt) / Medium (if optional) |
| **Hook conflict** | Probe repo has its own `hooks.json`; install merges or stomps | Critical |
| **Token-cost regression** | A single command consumes >50k tokens of context | High |
| **Report ungrounded** | Generated report cites this-source-repo's research/baseline files as if they were probe-repo files | Medium |
| **Settings collision** | Plugin assumes a `permissions.allow` rule that's absent | Medium |
| **Cosmetic** | Output mentions "this repo" in a way that confuses a probe-repo user | Low |

### Severity definitions

- **Critical** — command fails or produces incorrect output that misleads the user. Blocks Cross-Repo-GA.
- **High** — command runs but with degraded experience that a real user would notice immediately. Blocks Cross-Repo-GA.
- **Medium** — runs, output usable but suboptimal. Deferrable.
- **Low** — cosmetic, edge-case, or workaround-available. Deferrable.

## Finding-issue template

For each finding, file an issue in `Nosmoht/review-claude-config` with the template below. Apply label `track: cross-repo-validation` plus a severity label (`priority: P0/P1/P2/P3`).

```markdown
## Probe context

- **Probe repo:** `<owner/repo>` at commit `<sha>`
- **Stack:** `<Python / TypeScript / Go / mixed / ...>`
- **Probe session date:** YYYY-MM-DD
- **Triggering command:** `/<command> <args>`

## Symptom

<one paragraph: what happened, what was expected, what actually occurred>

## Reproduction (≤5 steps)

1. Clone or `cd` to `<repo>` at SHA `<sha>`
2. `<command>` ...
3. Observe `<symptom>`

## Severity

**<Critical | High | Medium | Low>** — <one-line justification per the catalog above>

## Root cause hypothesis

<Hardcoded path | Tooling assumption | Layout assumption | Domain-cache miss | Hook conflict | Token-cost | Report ungrounded | Settings collision | Cosmetic | Other>

If "Other": describe.

## Acceptance criteria for fix (R1-R4)

- [ ] R1 — <mechanically checkable assertion: e.g. "command exits 0 on probe repo X without `make` available">
- [ ] R2 — <named artifact change: which file gets edited>
- [ ] R3 — <single-interpretation: e.g. "Plugin must NOT call `make`, fall back to direct script invocation">
- [ ] R4 — Out of scope: <what the fix should NOT touch>

## Source

Cross-Repo Probe Runbook procedure (`docs/cross-repo-probe-runbook.md`), Probe-N session.
```

## After a probe run

1. File one issue per finding using the template above.
2. Apply labels: `track: cross-repo-validation` + appropriate `priority:` + `category:` if obvious.
3. **Critical / High** findings → also `status: ready` (immediate fix candidates).
4. **Medium / Low** findings → also `track: post-ga` (deferred).
5. Post a probe summary comment on a tracking-umbrella issue (one-time creation) listing all N findings filed in this probe.

## Probe sequencing

| Probe | Goal | Stop trigger |
|---|---|---|
| Probe-1 | Surface obvious assumptions | `track: cross-repo-validation` + `status: ready` Critical+High count documented |
| (fix pass) | Implement Critical/High findings | All Critical+High closed |
| Probe-2 | Verify fix-pass holds; surface second-order issues | New Critical+High count reported |
| (fix pass) | Iterate if needed | Hard cap: 2 fix-iterations |
| Probe-3 (optional) | Confirm convergence on a third stack | Zero new Critical+High |

If after 2 fix-iterations Probe-2 still produces Critical+High findings, **stop and re-evaluate** — the architecture may need a more fundamental redesign than per-issue patches can deliver.

## Anti-patterns

- Running the probe inside the source repo's working tree. The probe IS the test of plugin behavior outside its source — that's the whole point.
- Editing probe-repo files during the probe run. The probe is read-only on the probe repo.
- Filing aggregate findings ("everything was broken") instead of per-symptom issues. Per-symptom issues let `/implement-issue` claim them individually.
- Treating Medium findings as Cross-Repo-GA-blockers. Medium is deferrable by definition.
- Skipping Probe-2 because Probe-1 was clean. The stop condition requires **two** consecutive clean probes on **different** repos.

## References

- Memory: `feedback_no_cross_repo_path_references_in_persistent_artifacts` — never embed neighbor-repo absolute paths in committed files
- `CLAUDE.md` §Architecture — current `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/` layout
- `feedback_label_dont_close_for_deferral` — deferral via label, not close
