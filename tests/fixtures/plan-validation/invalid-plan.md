# Sample plan with hallucinated references

## Goal

Demonstrate that the validator surfaces fabricated paths and bogus
section anchors.

## Plan

The settings code lives in `scripts/merge-policy.yaml` and the canonical
helper is `bin/non-existent-tool.sh`. Both are fabricated.

Read `CLAUDE.md` §"Section That Does Not Exist" — the file is real but
the anchor is invented. The other cited document `docs/missing-doc.md`
is also fake.

## Real cross-reference for negative-test isolation

`README.md` exists, so this path alone should not trigger a failure;
only the hallucinated paths above should fail the gate.
