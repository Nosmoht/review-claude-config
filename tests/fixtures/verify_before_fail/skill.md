---
name: _test-verify-before-fail-real-references
description: >
  Synthetic test fixture for verifying the integration-perspective
  verify-before-fail gate. References ONLY existing primitives. Pass
  condition for the regression test = no false-positive missing-primitive
  findings emitted by the integration agent. Use ONLY as a test fixture
  (name prefixed with underscore so skill-discovery globs filter it).
allowed-tools: Read, Agent
---

# Verify-Before-Fail Test Fixture

Phase 1: Invoke `Agent(subagent_type=review-perspective-clarity)` for clarity review.

Phase 2: Invoke `Agent(subagent_type=review-perspective-correctness)` for correctness review.

Phase 3: Invoke `Agent(subagent_type=review-perspective-integration)` for integration review.

All three referenced agents exist at `agents/review-perspective-{clarity,correctness,integration}.md`.
