# Adversarial Behavior Snapshots — Perspective Agents

File-based snapshot fixtures for `tests/test_perspective_replay.py`. Implements
the contract pinned by issue #82.

## Why snapshots, not VCR

Perspective agents (`agents/review-perspective-{clarity,correctness,integration}.md`)
are dispatched through the Claude Code harness `Agent` tool, not through the
Anthropic Python SDK. There is no HTTP boundary the test harness can intercept,
so VCR-style cassette libraries are architecturally inapplicable. Each fixture
is the verbatim Markdown body the agent returned — captured from a real session
JSONL or synthesized to model a specific adversarial behavior.

## Layout

```
agent_outputs/
  <case_id>/
    case.yaml      # test definition (artifact, expected verdicts, attack class)
    clarity.md     # captured/synthesized perspective certificate (Markdown)
```

`case.yaml` schema is documented in `tests/test_perspective_replay.py`. The
Markdown follows the output contract pinned in
`agents/review-perspective-clarity.md` — `### Perspective`, `### Certificate`
(8-row Grade table), `### Findings` with `#### Finding (severity: ..., …)`
sub-blocks. Real Haiku output may include a prose preamble before
`### Perspective`; the parser tolerates that.

## Capture method (real-run snapshots)

For cases with category `clear_antecedent`, snapshots are extracted from the
local session ledger:

```
$HOME/.claude/projects/<project-slug>/<sessionId>.jsonl
```

The orchestrator dispatches the perspective agent via the `Agent` tool. The
JSONL records the dispatch as an `assistant` event with a `tool_use` block, and
the agent's response as a `user` event with a matching `tool_result` block.
The extraction routine pairs them by `tool_use_id` and writes the result body
to `<case_id>/clarity.md`.

Each captured file's `case.yaml` cites the source session id and line offset
under `provenance:` for traceability.

## Synthesis (adversarial cases)

For categories `ambiguous`, `empty`, and `injection`, fixtures are handcrafted
to model the behavior a well-aligned agent SHOULD produce under the named
attack class. The replay test asserts the merge layer correctly handles those
outputs. Whether the live agent actually produces them under attack is a
separate, deferred question (out-of-scope per issue #82, "Real-LLM nightly
regression").

## Refreshing snapshots

Snapshots are deliberately frozen. If the agent prompt or rubric changes such
that captured Markdown no longer reflects current agent behavior, regenerate
the affected fixtures and bump their `provenance.captured_at` field. Do NOT
edit captured fixtures by hand — that would defeat the regression-detection
purpose.
