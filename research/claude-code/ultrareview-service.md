---
last_refreshed: 2026-04-19
---

# Claude Code /ultrareview Service

Reference for the `/ultrareview` cloud multi-agent PR-review service, released GA 2026-04-16 (Claude Code v2.1.111). Used to decide whether the local review plugin should emit recommendations to invoke `/ultrareview` on high-risk PRs.

## TL;DR

- `/ultrareview` is an Anthropic-managed cloud service that runs a fleet of reviewer agents on a PR in a remote sandbox, with a verification pass to filter false positives before surfacing findings.
- Cost: **$15–$25 per review** on average, token-based billing. Not $5–$20 as the earlier rev2 plan claimed.
- **No programmatic API trigger**: invocation is only via `@claude review` / `@claude review once` PR comments or the GitHub UI. A local skill cannot trigger `/ultrareview` directly.
- Not available on Bedrock/Vertex/Foundry; Anthropic-direct only.
- Customization via `REVIEW.md` (highest priority) falls back to `CLAUDE.md`.
- Findings are **informational**: no approval or merge-block. User resolves.

## Trigger Modes

Configured per repository:

| Mode | Behavior |
|------|----------|
| Once after PR creation | Runs exactly once on PR open |
| After every push | Re-runs on every push (highest cost) |
| Manual | Runs only on explicit `@claude review` or `@claude review once` comment |

## Output Format

- Inline code comments with severity icon (🔴 Important, 🟡 Nit, 🟣 Pre-existing).
- Check Run details with severity table (`file:line:issue`).
- Files-Changed annotations as a fallback if inline comments are rejected.
- PR summary in the review body.

## Customization Priority

1. **REVIEW.md** in the repo root (highest): injected as system-prompt override.
   - Severity recalibration ("only 🔴 in production code").
   - Nit-volume cap ("max 5 nits per review").
   - Skip rules (generated code, lockfiles, vendored deps).
   - Repo-specific checks ("new API routes must have tests").
2. **CLAUDE.md**: newly-introduced violations are flagged as nits.

## Cost Model

- Billing: token-based, separate line item on the Anthropic bill.
- Scaling factors: PR size, codebase complexity, finding verification intensity.
- Spend cap: configurable via `claude.ai/admin-settings/usage`.
- Avg latency: ~20 minutes; timeouts possible on very large diffs.

## Feedback Loop

Users 👍/👎 findings in the PR UI. Reactions aggregate post-merge and tune the reviewer. Re-review requires an explicit `@claude review` comment — reactions alone do not trigger re-review.

## Limitations (as of 2026-04-16)

| Limitation | Detail |
|------------|--------|
| No programmatic API | Only `@claude review` PR comment or GitHub UI invoke it. Local skills cannot. |
| Cloud-only | Not on Bedrock/Vertex/Foundry. |
| Model version opaque | Docs do not state which Claude model is used. |
| Verification architecture opaque | "Parallelized checks" — unclear if verification runs in parallel or sequentially. |
| Informational only | No merge-block or approval semantics. |

## Implications for Review Plugin

- **Integration gap**: the local review plugin cannot invoke `/ultrareview` programmatically. At most, a local `/review-*` skill can emit a text recommendation ("Consider `@claude review` on this PR for adversarial cloud review").
- **Complementary surfaces**: `/ultrareview` covers GitHub PRs; local review plugin covers skill/agent/rule/hook/MCP/settings artifacts. No overlap; decide per artifact-type.
- **Open decision (Q4 in roadmap)**: should the review plugin's thesis ("local, self-contained, free") even mention a paid cloud service? Default answer: emit an optional recommendation phrase, do not gate.

## Open Questions

- Model version used for `/ultrareview`? (Opus 4.7 inferred but undocumented.)
- Programmatic API trigger planned? (No announcement.)
- Re-review semantics on new commits when mode is "after every push"? (Implied auto-rerun but not explicit.)

## Sources

Tier 1:
- [Claude Code — Code Review](https://code.claude.com/docs/en/code-review) — accessed 2026-04-19
- [claude-code releases](https://github.com/anthropics/claude-code/releases) — v2.1.111 release notes 2026-04-16

Tier 2 (cost data):
- Anthropic customer-facing pricing announcement 2026-04-16.
