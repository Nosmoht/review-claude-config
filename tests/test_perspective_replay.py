"""Adversarial behavior replay tests for perspective agents.

Implements the contract pinned by issue #82: snapshot fixtures, no VCR.
Each case directory under ``tests/fixtures/agent_outputs/<case_id>/`` carries:

  - ``{perspective}.md``  — captured or synthesised perspective certificate where
    ``perspective`` matches ``expected.perspective`` in ``case.yaml``
    (default ``clarity.md`` for fixtures that do not declare ``expected.perspective``).
    Captures come from the local session JSONL ledger; synthesised fixtures
    emulate Haiku-style output for behaviours real captures do not exhibit.
  - ``case.yaml``   — test definition with assertions and provenance.

The harness mocks the dispatch step by feeding the recorded Markdown into
``scripts.perspective_certificate_parser.parse_certificate``, then exercises
``scripts.merge_findings.merge_directory`` as a downstream smoke. Per-case
assertions live entirely on the parser output so the agent's emission is
under test, not the merge layer's owner-weighted-grade arithmetic.

case.yaml schema
----------------

::

    case_id: clear_antecedent_01
    category: clear_antecedent  # clear_antecedent | ambiguous | empty | injection
    artifact_path: skills/scaffold-skill/SKILL.md
    provenance:
      source: capture                # capture | synthesised
      session_id: <uuid>             # required for source=capture
      line_offset: 318               # required for source=capture
      captured_at: 2026-04-27
      rubric_sha: <40-char blob sha> # of agents/review-perspective-clarity.md
                                     # at capture/synthesis time. When the
                                     # current blob SHA drifts, fixtures may
                                     # have rotted — refresh required.
      agent_dispatch: <string>       # capture-only: the subagent_type used
                                     # (e.g. "claude-config:review-perspective-clarity")
      rationale: <string>            # synthesised-only: why this case exists
    expected:
      perspective: clarity       # required
      error_present: false       # default false; true → agent emitted `### ERROR`
      dimensions:                # subset; missing keys are not asserted
        Clarity: C
      no_grade_A: false          # injection-class assertion: every dim grade ≠ A
      findings:
        count: 9                 # exact count, or null = skip
        severity_counts:         # subset; missing severities not asserted
          High: 2
        must_include_checklist_items: [WS-1, WS-2]
        must_not_include_checklist_items: []
        all_severities_at_most_low: false  # negative-class: H+M findings == 0
    attack:
      class: null                # null | injection_simple | injection_authority |
                                 # injection_role_swap | injection_tool_escalation
    notes: free text

A case dir with no ``case.yaml`` is skipped (allows raw fixture parking
without enforcing assertions yet).

apply_caps interaction
----------------------

The replay harness's primary assertions live on the **parser** output —
i.e. the dict the agent's Markdown body deserialised to. The merge-layer
call (``merge_directory(tmp_path)``) is an integration smoke that confirms
the parser emits a shape ``merge_directory`` can read; it intentionally
runs with ``apply_caps=False`` because no ``binary_verdicts.json`` is
written into ``tmp_path``.

Production runs ``apply_caps=True`` and drops perspective findings on
``BINARY_ITEM_IDS | NARRATIVE_PARENT_IDS`` (see
``scripts/merge_findings.py:594``). This is by design — those items are
re-synthesised deterministically by ``synthesize_binary_findings``. The
replay test deliberately does NOT exercise that path on the per-case
parametrise loop, because doing so would make assertions on items like
``WS-2`` / ``RD-5`` / ``IJ-1`` impossible (they would always be dropped).

The dedicated ``test_caps_smoke_drops_binary_items`` test below exercises
caps explicitly on the pilot snapshot ``clear_antecedent_02`` (which
contains 5 findings on dropped items) so the production drop behaviour
has a regression guard.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from merge_findings import merge_directory, PERSPECTIVES  # noqa: E402
from perspective_certificate_parser import (  # noqa: E402
    VALID_DIMENSIONS,
    parse_certificate,
)

FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "agent_outputs"


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_cases() -> list[pathlib.Path]:
    """Return every case dir that carries a ``case.yaml``.

    Sorted lexicographically so pytest report ordering is stable across runs.
    """
    return sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir() and (p / "case.yaml").exists())


def _case_id(path: pathlib.Path) -> str:
    return path.name


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------


def _assert_parser_output(case_id: str, cert: dict[str, Any], expected: dict[str, Any]) -> None:
    """Apply every ``expected:`` assertion against ``cert`` (parser output).

    Each branch raises an ``AssertionError`` carrying the case id so failures
    in the parametrised test point at the offending case directly.
    """
    if "perspective" in expected:
        assert (
            cert["perspective"] == expected["perspective"]
        ), f"{case_id}: perspective {cert['perspective']!r} != {expected['perspective']!r}"

    if expected.get("error_present", False):
        assert cert["error"] is not None, f"{case_id}: expected ### ERROR shortcut, got cert"
    else:
        assert cert["error"] is None, f"{case_id}: unexpected error: {cert['error']!r}"

    for dim, expected_grade in (expected.get("dimensions") or {}).items():
        assert dim in cert["dimensions"], f"{case_id}: dimension {dim!r} missing from parser output"
        assert (
            cert["dimensions"][dim] == expected_grade
        ), f"{case_id}: {dim} grade {cert['dimensions'][dim]!r} != {expected_grade!r}"

    if expected.get("no_grade_A", False):
        offenders = {d: g for d, g in cert["dimensions"].items() if g == "A"}
        assert (
            not offenders
        ), f"{case_id}: dimension(s) graded A under attack — {offenders!r}"

    findings_spec = expected.get("findings") or {}
    findings = cert["findings"]

    if findings_spec.get("count") is not None:
        assert len(findings) == findings_spec["count"], (
            f"{case_id}: finding count {len(findings)} != {findings_spec['count']}"
        )

    sev_counts = findings_spec.get("severity_counts") or {}
    for sev, expected_n in sev_counts.items():
        actual = sum(1 for f in findings if f["severity"] == sev)
        assert actual == expected_n, f"{case_id}: severity={sev} count {actual} != {expected_n}"

    items = [f["checklist_item"] for f in findings]
    for must in findings_spec.get("must_include_checklist_items") or []:
        assert must in items, f"{case_id}: required checklist_item {must!r} not in findings"
    for must_not in findings_spec.get("must_not_include_checklist_items") or []:
        assert (
            must_not not in items
        ), f"{case_id}: forbidden checklist_item {must_not!r} present in findings"

    if findings_spec.get("all_severities_at_most_low", False):
        bad = [f for f in findings if f["severity"] in ("High", "Medium")]
        assert not bad, (
            f"{case_id}: cosmetic-only input must yield no H/M findings, "
            f"got {[f['checklist_item'] for f in bad]}"
        )


def _neutral_sibling(perspective: str) -> dict[str, Any]:
    """Build a placeholder sibling cert: all-B, no findings.

    Real merges run with three perspectives; the replay harness only swaps in
    the captured clarity cert, so the other two need stubs to keep merge_directory
    out of degraded_mode for owner-weighted dimensions owned by correctness or
    integration. Stubs add no findings, so they can never affect the
    Clarity-perspective assertions.
    """
    return {
        "perspective": perspective,
        "dimensions": dict.fromkeys(VALID_DIMENSIONS, "B"),
        "findings": [],
        "artifact_frontmatter": {"allowed_tools": ["Read"]},
        "weighted_score": 85.0,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


CASES = discover_cases()


@pytest.mark.parametrize("case_dir", CASES, ids=[_case_id(c) for c in CASES])
def test_replay_case(case_dir: pathlib.Path, tmp_path: pathlib.Path) -> None:
    """Per-case parser+merge replay.

    Steps:
      1. Read ``case.yaml`` and ``{expected.perspective}.md`` (default ``clarity.md``).
      2. Parse the Markdown to a JSON-shaped dict.
      3. Apply ``expected:`` assertions to the parser output.
      4. Write the parsed cert plus two neutral sibling stubs to ``tmp_path``,
         invoke ``merge_directory``, and assert the merge layer runs without
         entering ``status=failure`` — this is the integration smoke.
    """
    case = yaml.safe_load((case_dir / "case.yaml").read_text(encoding="utf-8"))
    case_id = case["case_id"]
    artifact_path = case["artifact_path"]
    expected = case.get("expected") or {}
    # Cert file name matches expected.perspective. Pre-existing fixtures that do not
    # declare expected.perspective default to "clarity" (backward-compatible).
    # When expected.perspective is explicitly set to a non-clarity value, the named
    # file MUST exist — no silent fallback (would mask a missing fixture file).
    _ep = (expected.get("perspective") or "clarity").strip()
    _cert_file = case_dir / f"{_ep}.md"
    if not _cert_file.exists():
        if _ep == "clarity":
            raise FileNotFoundError(f"{case_id}: clarity.md missing in {case_dir}")
        else:
            raise FileNotFoundError(
                f"{case_id}: expected cert file {_cert_file} not found "
                f"(expected.perspective={_ep!r})"
            )
    md = _cert_file.read_text(encoding="utf-8")
    perspective_override = _cert_file.stem
    cert = parse_certificate(
        md,
        artifact_path=artifact_path,
        perspective_override=perspective_override,
    )
    _assert_parser_output(case_id, cert, expected)

    # Integration smoke — write all three perspective JSONs to a tmp dir and
    # confirm merge_directory consumes the cert. This catches regressions
    # where a parser change emits a shape merge_directory cannot read.
    for _p in PERSPECTIVES:
        _slot = cert if _p == perspective_override else _neutral_sibling(_p)
        (tmp_path / f"{_p}.json").write_text(json.dumps(_slot), encoding="utf-8")

    result = merge_directory(tmp_path)
    if expected.get("error_present", False):
        # ERROR shortcut — clarity has empty dimensions/findings, merge still
        # succeeds (owner-weighted owners pull C from sibling stubs) but the
        # clarity perspective's contribution is null.
        assert result["status"] in {"success", "partial"}, f"{case_id}: merge status {result['status']}"
    else:
        assert result["status"] == "success", f"{case_id}: merge status {result['status']!r}"
        assert result["degraded_mode"] is False, f"{case_id}: merge entered degraded_mode"
        # Verify findings from the real cert flowed through (neutral siblings add none).
        assert len(result["findings"]) >= len(cert["findings"]), (
            f"{case_id}: expected ≥{len(cert['findings'])} findings from real "
            f"{perspective_override!r} cert in merge output, got {len(result['findings'])}"
        )
        # Also verify checklist items from must_include are present in merge output.
        _must_include = expected.get("findings", {}).get("must_include_checklist_items", [])
        if _must_include:
            _result_items = {f.get("checklist_item") for f in result["findings"]}
            for _item in _must_include:
                assert _item in _result_items, (
                    f"{case_id}: required checklist_item {_item!r} missing from merge "
                    f"output (expected perspective: {perspective_override!r})"
                )


def test_at_least_twelve_cases() -> None:
    """Issue #82 requires twelve cases for the pilot — four per category.

    Locked here so a partial commit cannot ship with fewer cases.
    """
    by_category: dict[str, int] = {}
    for case_dir in CASES:
        case = yaml.safe_load((case_dir / "case.yaml").read_text(encoding="utf-8"))
        by_category[case["category"]] = by_category.get(case["category"], 0) + 1
    assert sum(by_category.values()) >= 12, f"need 12 cases, have {by_category}"
    for cat in ("clear_antecedent", "ambiguous", "empty", "injection"):
        assert by_category.get(cat, 0) >= 4, f"need ≥4 {cat} cases, have {by_category.get(cat, 0)}"


def test_negative_case_present() -> None:
    """Issue #82 validation point: ≥1 case where the agent's emission has zero
    H/M findings. The case.yaml signals this via
    ``expected.findings.all_severities_at_most_low: true``.
    """
    found = False
    for case_dir in CASES:
        case = yaml.safe_load((case_dir / "case.yaml").read_text(encoding="utf-8"))
        if (case.get("expected", {}).get("findings", {}) or {}).get(
            "all_severities_at_most_low", False
        ):
            found = True
            break
    assert found, "no negative case (cosmetic input → no H/M findings) declared"


def test_injection_case_no_grade_A() -> None:
    """Issue #82 validation point: ≥1 injection case where the agent does not
    emit a Grade-A response under attack. The case.yaml signals this via
    ``expected.no_grade_A: true``.
    """
    found = False
    for case_dir in CASES:
        case = yaml.safe_load((case_dir / "case.yaml").read_text(encoding="utf-8"))
        if case.get("category") != "injection":
            continue
        if case.get("expected", {}).get("no_grade_A", False):
            found = True
            break
    assert found, "no injection case asserts no_grade_A under attack"


def test_caps_smoke_drops_binary_items(tmp_path: pathlib.Path) -> None:
    """Production-path smoke: ``merge_directory`` with ``binary_verdicts.json``
    drops perspective findings on ``BINARY_ITEM_IDS | NARRATIVE_PARENT_IDS``.

    The captured pilot ``clear_antecedent_02`` carries six findings, of which
    five (RD-5, COMP-X, COMP-Y, COMP-Z, RL-9) are members of those sets and
    must be dropped under caps. The remaining finding (WS-3) is on a
    non-binary item and must survive. This single fixture is sufficient to
    detect a regression in the drop logic — adding more cases here is
    redundant; ``tests/test_merge_findings.py`` already exercises the drop
    logic exhaustively in isolation.
    """
    case_dir = FIXTURES_DIR / "clear_antecedent_02"
    # clear_antecedent_02 is a clarity-only fixture; clarity.md is intentional here.
    md = (case_dir / "clarity.md").read_text(encoding="utf-8")
    cert = parse_certificate(
        md,
        artifact_path="skills/review-skill/SKILL.md",
        perspective_override="clarity",
    )

    (tmp_path / "clarity.json").write_text(json.dumps(cert), encoding="utf-8")
    (tmp_path / "correctness.json").write_text(
        json.dumps(_neutral_sibling("correctness")), encoding="utf-8"
    )
    (tmp_path / "integration.json").write_text(
        json.dumps(_neutral_sibling("integration")), encoding="utf-8"
    )
    # Stub binary_verdicts.json — all PASS so no synthesised findings appear,
    # but its presence sets ``apply_caps=True`` and triggers the drop pass.
    verdicts_doc = {
        "artifact_path": "skills/review-skill/SKILL.md",
        "artifact_type": "skill",
        "verdicts": {},
        "stats": {"runner_error": 0},
    }
    (tmp_path / "binary_verdicts.json").write_text(json.dumps(verdicts_doc), encoding="utf-8")

    result = merge_directory(tmp_path)
    assert result["status"] == "success"
    assert result["binary_evaluator_status"] == "present"
    assert result["dropped_perspective_findings"] >= 5, (
        f"expected ≥5 drops on binary/narrative parent items, got "
        f"{result['dropped_perspective_findings']}"
    )
    surviving_items = {f.get("checklist_item") for f in result["findings"]}
    # WS-3 is non-binary and must survive.
    assert "WS-3" in surviving_items, f"WS-3 missing from surviving items: {surviving_items}"
    # Every dropped item must NOT appear.
    for dropped in ("RD-5", "COMP-X", "COMP-Y", "COMP-Z", "RL-9"):
        assert dropped not in surviving_items, (
            f"{dropped} should have been dropped but survived: {surviving_items}"
        )
