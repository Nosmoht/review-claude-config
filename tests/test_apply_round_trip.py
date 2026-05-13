"""Round-trip contract tests for the apply-* findings.json sidecar pipeline.

This file tests the *contract* described in
``skills/apply-skill-review-findings/SKILL.md`` Step 2.4 (and mirrored across
``apply-agent``, ``apply-rule``, ``apply-review-findings``). The apply-* skills
are SKILL.md files driven by the model, not Python modules — so this test
implements a *reference* applyability gate in Python that mirrors the prose
contract, and asserts:

  1. Synthesized binary findings (produced by
     ``scripts/merge_findings.py:synthesize_binary_findings``) carry a
     ``current`` that is, by construction, never a substring of any plausible
     artifact body. The gate therefore routes them to **Manual-only**.
  2. Empty-anchor findings (current or recommended absent/empty) route to
     Manual-only with the dedicated reason.
  3. Perspective-emitted findings whose ``current`` IS a literal substring of
     the artifact route to **Dispatchable** (positive control).
  4. The synthesized-evidence shape is distinguished from generic anchor-drift
     so the user sees the right Manual-only reason in the Phase 2 table.
  5. At the merge layer, an artifact fix (binary item flips FAIL → PASS) makes
     the previously-emitted High finding disappear from the next sidecar — the
     "fixed findings don't reappear" round-trip property.

Contract drift between the Python reference gate and the SKILL.md prose is a
known limitation: this test cannot directly execute SKILL.md instructions.
The reference gate is the executable translation; if the SKILL.md prose
diverges from it, update both deliberately.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys

import pytest
from jsonschema import Draft202012Validator, RefResolver

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "skills" / "review-claude-config" / "references" / "schemas"

sys.path.insert(0, str(REPO_ROOT / "scripts"))


# ---------------------------------------------------------------------------
# Reference applyability gate — translates SKILL.md Step 2.4 to Python.
#
# Contract source:
#   skills/apply-skill-review-findings/SKILL.md §"Step 2.4: Applyability gate"
#   skills/apply-review-findings/SKILL.md §"2.4 Applyability gate"
#   skills/apply-agent-review-findings/SKILL.md §"Step 2.4: Applyability gate"
#   skills/apply-rule-review-findings/SKILL.md §"Step 2.4: Applyability gate"
#
# All four are textually identical at commit 378c723. The contract is also
# encoded in review-report-contract.md §"Sidecar Emission" as the consumer
# obligation: "before classifying a finding as Dispatchable, consumers MUST
# verify current is a literal substring of the artifact file".
# ---------------------------------------------------------------------------

# Heuristic to recognise the synthesized-evidence shape produced by
# scripts/merge_findings.py:synthesize_binary_findings(). The composed
# evidence_text starts with "line <N>" and includes one of the
# match/trigger/missing keys.
_SYNTHESIZED_EVIDENCE_RE = re.compile(r"^line \d+(?:;\s*(match|trigger|missing)=)")


def classify(finding: dict, artifact_text: str) -> tuple[str, str]:
    """Return (classification, reason) for a single mapped finding.

    classification is "Dispatchable" or "Manual-only".
    reason is a non-empty string for Manual-only, "" for Dispatchable.
    """
    current = finding.get("current") or ""
    recommended = finding.get("recommended") or ""

    if not current or not recommended:
        return "Manual-only", "Missing rewrite anchors"

    if current in artifact_text:
        return "Dispatchable", ""

    if _SYNTHESIZED_EVIDENCE_RE.match(current):
        return (
            "Manual-only",
            "Synthesized evidence summary, not a literal source quote (binary item)",
        )
    return "Manual-only", "Anchor text not found (whitespace, encoding, or quoting drift?)"


# ---------------------------------------------------------------------------
# Sidecar consumption helpers.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def findings_list_validator() -> Draft202012Validator:
    finding_schema = json.loads((SCHEMAS_DIR / "finding.schema.json").read_text(encoding="utf-8"))
    list_schema = json.loads((SCHEMAS_DIR / "findings-list.schema.json").read_text(encoding="utf-8"))
    store = {finding_schema["$id"]: finding_schema, "finding.schema.json": finding_schema}
    resolver = RefResolver.from_schema(list_schema, store=store)
    return Draft202012Validator(list_schema, resolver=resolver)


# ---------------------------------------------------------------------------
# Tests.
# ---------------------------------------------------------------------------


class TestApplyabilityGateContract:
    """Reference gate behaves as specified by SKILL.md Step 2.4."""

    def test_empty_current_is_manual_only(self):
        f = {"current": "", "recommended": "fix"}
        cls, reason = classify(f, "anything")
        assert cls == "Manual-only"
        assert "anchor" in reason.lower()

    def test_empty_recommended_is_manual_only(self):
        f = {"current": "some text", "recommended": ""}
        cls, reason = classify(f, "some text")
        assert cls == "Manual-only"

    def test_both_empty_is_manual_only(self):
        f = {"current": "", "recommended": ""}
        cls, reason = classify(f, "irrelevant")
        assert cls == "Manual-only"

    def test_missing_keys_is_manual_only(self):
        cls, reason = classify({}, "irrelevant")
        assert cls == "Manual-only"

    def test_substring_match_is_dispatchable(self):
        f = {"current": "fetch slightly more data", "recommended": "fetch exactly N records"}
        artifact = "Step 1: read the query.\nStep 2: fetch slightly more data.\nStep 3: write."
        cls, reason = classify(f, artifact)
        assert cls == "Dispatchable"
        assert reason == ""

    def test_non_substring_drift_is_manual_only_with_drift_reason(self):
        # Real-looking quote that doesn't appear verbatim (e.g., whitespace drift).
        f = {"current": "fetch  slightly  more  data", "recommended": "fetch exactly N"}
        artifact = "fetch slightly more data"  # single spaces in artifact
        cls, reason = classify(f, artifact)
        assert cls == "Manual-only"
        assert "drift" in reason.lower()

    def test_synthesized_evidence_is_manual_only_with_synth_reason(self):
        # Shape produced by synthesize_binary_findings — composed evidence string,
        # never a literal artifact substring.
        f = {
            "current": "line 12; match='slightly more'",
            "recommended": "Apply the BOUNDARY PASS exemplar for CLAR-2 in scoring-rubric.md.",
        }
        artifact = "fetch slightly more data on line twelve"
        cls, reason = classify(f, artifact)
        assert cls == "Manual-only"
        assert "synthesized evidence" in reason.lower()
        assert "binary" in reason.lower()

    def test_synthesized_evidence_with_trigger_keyword(self):
        f = {
            "current": "line 42; trigger='abort'",
            "recommended": "Apply the BOUNDARY PASS exemplar for CLAR-3 in scoring-rubric.md.",
        }
        cls, reason = classify(f, "abort here")
        assert cls == "Manual-only"
        assert "synthesized evidence" in reason.lower()

    def test_synthesized_evidence_with_missing_keyword(self):
        f = {
            "current": "line 7; missing=['recovery']",
            "recommended": "Apply the BOUNDARY PASS exemplar for CLAR-4 in scoring-rubric.md.",
        }
        cls, reason = classify(f, "irrelevant body")
        assert cls == "Manual-only"
        assert "synthesized evidence" in reason.lower()


class TestSynthesizedBinaryFindingsAreNonApplyable:
    """The gate's load-bearing invariant: scripts/merge_findings.py emits
    binary findings whose ``current`` always matches the synthesized-evidence
    regex. This test asserts the merge_findings producer side, then runs the
    gate over the result, then asserts the gate routes every synthesized
    finding to Manual-only — closing the round-trip risk that an Edit on
    fake-anchor text would corrupt the artifact.
    """

    def _verdicts_doc(self, **item_verdicts: str) -> dict:
        verdicts: dict[str, dict] = {}
        for idx, (key, verdict) in enumerate(item_verdicts.items()):
            item_id = key.replace("_", "-")
            verdicts[item_id] = {
                "verdict": verdict,
                "evidence": {"line": 100 + idx, "match": f"stub-{item_id}"},
            }
        return {
            "schema_version": 1,
            "artifact_path": "skills/foo/SKILL.md",
            "artifact_type": "skill",
            "verdicts": verdicts,
            "stats": {"pass": 0, "fail": 0, "na": 0, "runner_error": 0},
        }

    def test_synthesized_current_matches_evidence_shape(self):
        from merge_findings import synthesize_binary_findings

        doc = self._verdicts_doc(CLAR_2="FAIL", CLAR_3="FAIL")
        findings = synthesize_binary_findings(doc, "skills/foo/SKILL.md")
        assert findings, "FAILs must produce findings"
        for f in findings:
            assert _SYNTHESIZED_EVIDENCE_RE.match(f["current"]), (
                f"current must match synthesized-evidence shape: {f['current']!r}"
            )

    def test_synthesized_current_is_non_substring_of_typical_artifact(self):
        from merge_findings import synthesize_binary_findings

        # An artifact that contains the matched fragment ("stub-CLAR-2") in a
        # natural context — the composed `current` ("line 100; match='stub-CLAR-2'")
        # is NEVER a substring of such an artifact.
        artifact = (
            "# Skill\n\nStep 1: stub-CLAR-2 occurs naturally on this line.\n"
            "Step 2: stub-CLAR-2 also appears here in plain prose.\n"
        )
        doc = self._verdicts_doc(CLAR_2="FAIL", CLAR_3="FAIL")
        findings = synthesize_binary_findings(doc, "skills/foo/SKILL.md")
        for f in findings:
            assert f["current"] not in artifact

    def test_synthesized_findings_route_to_manual_only(self):
        """The load-bearing assertion: gate(synthesize_binary_findings(FAIL))
        is always Manual-only with the synthesized-evidence reason."""
        from merge_findings import synthesize_binary_findings

        artifact = "any content here including stub-CLAR-2 in natural prose"
        doc = self._verdicts_doc(CLAR_2="FAIL", CLAR_3="FAIL", META_4="FAIL")
        findings = synthesize_binary_findings(doc, "skills/foo/SKILL.md")
        assert findings, "FAILs must produce findings"
        for f in findings:
            cls, reason = classify(f, artifact)
            assert cls == "Manual-only"
            assert "synthesized evidence" in reason.lower(), (
                f"gate should distinguish synthesized shape, got: {reason!r}"
            )


class TestPositiveControlPerspectiveDispatch:
    """A perspective-emitted finding (literal-quote ``current``) routes to
    Dispatchable. Without this positive control, the gate could be a
    blanket-reject and the contract would be vacuously satisfied.
    """

    def test_real_perspective_finding_is_dispatchable(self):
        finding = {
            "id": "PE-1:skills/x/SKILL.md:Prompt Engineering/v1",
            "checklist_item": "PE-1",
            "dimension": "Prompt Engineering",
            "severity": "High",
            "evidence": "instruction reads 'try to'",
            "current": "Try to validate the input format before parsing.",
            "recommended": "Validate the input format before parsing.",
            "perspective": "correctness",
        }
        artifact = (
            "## Workflow\n\nTry to validate the input format before parsing. "
            "Then return early on errors.\n"
        )
        cls, reason = classify(finding, artifact)
        assert cls == "Dispatchable"
        assert reason == ""


class TestRoundTripFixedFindingsDoNotReappear:
    """Producer-level round-trip: when an artifact is fixed (binary item
    transitions FAIL → PASS), synthesize_binary_findings emits no finding
    for that item on the next run. The "fix sticks" property at the merge
    layer.
    """

    def _verdicts_doc(self, **item_verdicts: str) -> dict:
        verdicts: dict[str, dict] = {}
        for idx, (key, verdict) in enumerate(item_verdicts.items()):
            item_id = key.replace("_", "-")
            verdicts[item_id] = {
                "verdict": verdict,
                "evidence": {"line": 100 + idx, "match": f"stub-{item_id}"},
            }
        return {
            "schema_version": 1,
            "artifact_path": "skills/foo/SKILL.md",
            "artifact_type": "skill",
            "verdicts": verdicts,
            "stats": {"pass": 0, "fail": 0, "na": 0, "runner_error": 0},
        }

    def test_fail_emits_finding_pass_emits_none(self):
        from merge_findings import synthesize_binary_findings

        run_a = synthesize_binary_findings(
            self._verdicts_doc(CLAR_2="FAIL"), "skills/foo/SKILL.md"
        )
        run_b = synthesize_binary_findings(
            self._verdicts_doc(CLAR_2="PASS"), "skills/foo/SKILL.md"
        )
        assert any(f["checklist_item"] == "CLAR-2" for f in run_a)
        assert not any(f["checklist_item"] == "CLAR-2" for f in run_b)

    def test_partial_fix_subset_property(self):
        """If only one of multiple FAILs is fixed, the run-B finding ID set
        is a strict subset of run A's — no spurious new High findings."""
        from merge_findings import synthesize_binary_findings

        run_a = synthesize_binary_findings(
            self._verdicts_doc(CLAR_2="FAIL", CLAR_3="FAIL"), "skills/foo/SKILL.md"
        )
        run_b = synthesize_binary_findings(
            self._verdicts_doc(CLAR_2="PASS", CLAR_3="FAIL"), "skills/foo/SKILL.md"
        )
        ids_a = {f["id"] for f in run_a}
        ids_b = {f["id"] for f in run_b}
        assert ids_b < ids_a
        assert all("CLAR-3" in i for i in ids_b)


class TestSidecarRoundTripPipeline:
    """End-to-end: synthesize binary findings -> write_findings_sidecar ->
    read back -> validate against schema -> run gate on each finding.
    Asserts the sidecar payload survives the pipeline byte-coherent and
    the consumer-side gate produces Manual-only for every synthesized
    finding (the apply-* contract).
    """

    def test_sidecar_pipeline_routes_synthesized_to_manual_only(
        self, tmp_path, findings_list_validator
    ):
        from merge_findings import synthesize_binary_findings, write_findings_sidecar

        verdicts_doc = {
            "verdicts": {
                "CLAR-2": {
                    "verdict": "FAIL",
                    "evidence": {"line": 12, "match": "slightly more"},
                },
                "META-4": {
                    "verdict": "FAIL",
                    "evidence": {"line": 7, "match": "you can"},
                },
            }
        }
        findings = synthesize_binary_findings(verdicts_doc, "skills/foo/SKILL.md")
        assert findings, "FAILs must produce findings"

        result = {"findings": findings}
        sidecar_path = tmp_path / "report.findings.json"
        write_findings_sidecar(result, sidecar_path, session_id="round-trip-test")

        loaded = json.loads(sidecar_path.read_text(encoding="utf-8"))
        findings_list_validator.validate(loaded)

        artifact = "Some prose containing slightly more text and you can do this."
        for f in loaded["findings"]:
            cls, reason = classify(f, artifact)
            assert cls == "Manual-only", (
                f"Synthesized finding {f['id']!r} unexpectedly Dispatchable: {f['current']!r}"
            )

    def test_empty_findings_sidecar_is_a_clean_review(self, tmp_path, findings_list_validator):
        """Per review-report-contract.md, findings:[] is the clean-review
        state — apply-* must surface 'No findings' and stop, NOT fall back
        to Markdown. This test pins the empty-array shape as a valid
        sidecar so consumers cannot conflate it with a malformed sidecar.
        """
        from merge_findings import write_findings_sidecar

        sidecar_path = tmp_path / "report.findings.json"
        write_findings_sidecar({"findings": []}, sidecar_path)
        loaded = json.loads(sidecar_path.read_text(encoding="utf-8"))
        findings_list_validator.validate(loaded)
        assert loaded["findings"] == []
        # Consumers branching on empty-array vs malformed: this MUST parse
        # cleanly (i.e., neither a JSON parse error nor a schema violation).


class TestGateReasonStability:
    """The Manual-only reason text is the user-visible signal in the Phase 2
    table. Pin the strings so cosmetic edits cannot accidentally drop the
    'synthesized evidence' / 'drift' distinction.
    """

    def test_drift_reason_pin(self):
        f = {"current": "absent text", "recommended": "x"}
        _, reason = classify(f, "different content")
        assert "whitespace" in reason and "encoding" in reason and "quoting" in reason

    def test_synth_reason_pin(self):
        f = {"current": "line 1; match='x'", "recommended": "x"}
        _, reason = classify(f, "")
        assert "binary item" in reason.lower()
        assert "literal source quote" in reason.lower()
