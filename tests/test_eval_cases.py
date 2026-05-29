"""Programmatic regression eval harness — replays YAML test cases against
captured/synthesised ``findings.json`` fixtures.

Implements the contract pinned by issue #83. The cases under
``tests/eval_cases/*.yaml`` carry sprint-contract acceptance criteria; the
fixtures under ``tests/fixtures/eval/`` carry (a) the synthetic input artifact
the case is built around, and (b) for ``kind: detection`` and ``kind: clean``
cases, a synthesised ``findings.json`` representing what a well-behaved
``/review-skill`` (or downstream merge layer) should produce on that input.

Behavior cases (``kind: behavior_*``) assert side effects or process behavior
rather than a findings.json: ``behavior_analytics`` (analytics diff-tracking),
``behavior_scaffold`` (scaffold filesystem writes), ``behavior_review`` (review-
orchestrator process behavior — e.g. dimension-traversal completeness, meta-
condition detection), and ``behavior_apply_policy`` (apply-risk policy lookup).
Most ride the universal YAML-structure check here, with the real assertion
validated through ``/run-eval-cases`` (LLM-driven). ``behavior_apply_policy`` is
the exception: its policy lookup is deterministic, so it ALSO has a programmatic
pytest path (``test_apply_policy_lookup``). ``behavior_review`` is LLM-driven like
analytics/scaffold — no programmatic replay path here beyond the structural check.

Schema (per case YAML)
----------------------

::

    id: case-01-real-issue
    kind: detection                       # detection | clean | behavior_analytics |
                                          # behavior_scaffold | behavior_apply_policy |
                                          # behavior_review
    description: <one-line>
    target_skill: review-skill            # which skill the case exercises
    artifacts:
      primary: tests/fixtures/eval/<file> # detection / clean
      # OR a dict of named paths for multi-artifact behavior cases:
      # report_a: ...
      # report_b: ...
    findings_fixture: tests/fixtures/eval/case_01_findings.json
                                          # detection / clean only
    defects:                              # detection only — historical doc
                                          # convention from docs/review-eval-cases.md;
                                          # used for FP/FN scoring with prefix-matching
                                          # against the post-rewrite checklist_items
                                          # the rubric actually emits.
      - { item: SP-2, dim: Safety, sev: High, desc: "..." }
    sprint_contract:                      # display-only criteria (mirrors the
                                          # SKILL.md sprint-contract bullets so
                                          # /run-eval-cases can rebuild its
                                          # report without parsing prose)
      - { id: C1-1, description: "..." }
    expected:                             # the actual machine-checkable contract
      required_findings:                  # findings that MUST appear (canonical
                                          # post-rewrite item names)
        - { item: SP-2b, dim: Safety, severity: [High, Medium] }
      forbidden_findings: []              # findings that MUST NOT appear
      field_invariants:                   # named invariants — see _check_field_invariants
        - "every High/Medium finding has non-empty evidence"
        - "every High/Medium finding has non-empty validation"
        - "every High finding has non-empty current and recommended"
    acceptance:                           # FP/FN gate, detection only
      precision: ">= 0.5"
      recall:    ">= 0.33"
    execution:                            # narrative — consumed by /run-eval-cases,
                                          # not by this harness
      dispatch:
        command: /review-skill
        target_arg: <path>
        orchestration: { ... }
      timeout_seconds: 60
    fix_target:                           # narrative — diagnostic mapping
      artifact: <path>
      reviewer_behavior: <path>
    notes: <free text>

Item-matching strategy
----------------------

Historical defects (e.g. ``SP-2``) and modern emitted items
(e.g. ``SP-2b`` after the rubric's #70 supersession) are matched bidirectionally
by prefix: ``defect.item`` matches if ``finding.checklist_item`` starts with
``defect.item`` OR the reverse. Dimension matching uses an alias table to
collapse common abbreviations (``Meta`` → ``Metadata``, ``PE`` →
``Prompt Engineering``, ``Compl`` → ``Completeness``).
"""

from __future__ import annotations

import itertools
import json
import pathlib
import re
import sys
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator, RefResolver

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

EVAL_CASES_DIR = REPO_ROOT / "tests" / "eval_cases"
SCHEMAS_DIR = REPO_ROOT / "skills" / "review-claude-config" / "references" / "schemas"


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


# VALID_KINDS is a CLOSED set: the only mechanical kind-gate is the
# ``case["kind"] in VALID_KINDS`` assertion in test_yaml_loads_and_has_required_fields.
# Append-only via an AHE-reviewed PR that updates all consumers in lockstep
# (this docstring + tuple, skills/run-eval-cases/SKILL.md §Case kinds,
# docs/review-eval-cases.md). Parity decisions: rules/schema-contract-parity.md.
VALID_KINDS = (
    "detection",
    "clean",
    "behavior_analytics",
    "behavior_scaffold",
    "behavior_apply_policy",
    "behavior_review",
)
DIM_ALIASES = {
    "Meta": "Metadata",
    "PE": "Prompt Engineering",
    "CE": "Context Engineering",
    "Compl": "Completeness",
    "GA": "Goal Alignment",
}


def discover_cases() -> list[pathlib.Path]:
    if not EVAL_CASES_DIR.exists():
        return []
    return sorted(EVAL_CASES_DIR.glob("case_*.yaml"))


CASES = discover_cases()


def _case_id(p: pathlib.Path) -> str:
    return p.stem


def _load_case(p: pathlib.Path) -> dict[str, Any]:
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _canonical_dim(d: str) -> str:
    return DIM_ALIASES.get(d, d)


def _items_match(a: str, b: str) -> bool:
    """Bidirectional prefix match for checklist_item drift across rubric versions."""
    if not a or not b:
        return False
    return a == b or a.startswith(b) or b.startswith(a)


# ---------------------------------------------------------------------------
# Schema validation against finding.schema.json
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def findings_validator():
    finding_schema = json.loads((SCHEMAS_DIR / "finding.schema.json").read_text(encoding="utf-8"))
    list_schema = json.loads((SCHEMAS_DIR / "findings-list.schema.json").read_text(encoding="utf-8"))
    store = {finding_schema["$id"]: finding_schema, "finding.schema.json": finding_schema}
    resolver = RefResolver.from_schema(list_schema, store=store)
    return Draft202012Validator(list_schema, resolver=resolver)


# ---------------------------------------------------------------------------
# Per-case YAML structural validation (every case kind)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case_path", CASES, ids=[_case_id(c) for c in CASES])
def test_yaml_loads_and_has_required_fields(case_path: pathlib.Path) -> None:
    case = _load_case(case_path)
    cid = case.get("id", "<missing-id>")
    for required in ("id", "kind", "description", "target_skill", "sprint_contract"):
        assert required in case, f"{cid}: missing required field {required!r}"
    assert case["kind"] in VALID_KINDS, f"{cid}: invalid kind {case['kind']!r}"
    assert case["sprint_contract"], f"{cid}: sprint_contract empty"
    for item in case["sprint_contract"]:
        assert "id" in item and "description" in item, (
            f"{cid}: sprint_contract item missing id/description: {item}"
        )


# ---------------------------------------------------------------------------
# Detection / clean: programmatic assertions against the synthesised findings.json
# ---------------------------------------------------------------------------


def _detection_or_clean_cases() -> list[pathlib.Path]:
    out = []
    for p in CASES:
        case = _load_case(p)
        if case.get("kind") in ("detection", "clean"):
            out.append(p)
    return out


@pytest.mark.parametrize(
    "case_path", _detection_or_clean_cases(), ids=[_case_id(c) for c in _detection_or_clean_cases()]
)
def test_findings_fixture_validates_against_schema(
    case_path: pathlib.Path, findings_validator
) -> None:
    case = _load_case(case_path)
    cid = case["id"]
    fix = REPO_ROOT / case["findings_fixture"]
    assert fix.exists(), f"{cid}: findings_fixture {fix} not found"
    payload = json.loads(fix.read_text(encoding="utf-8"))
    errors = sorted(findings_validator.iter_errors(payload), key=lambda e: list(e.path))
    assert not errors, f"{cid}: findings.json fails schema:\n" + "\n".join(
        f"  {list(e.path)}: {e.message}" for e in errors
    )


@pytest.mark.parametrize(
    "case_path", _detection_or_clean_cases(), ids=[_case_id(c) for c in _detection_or_clean_cases()]
)
def test_required_findings_present(case_path: pathlib.Path) -> None:
    case = _load_case(case_path)
    cid = case["id"]
    expected = case.get("expected") or {}
    required = expected.get("required_findings") or []
    findings = json.loads((REPO_ROOT / case["findings_fixture"]).read_text(encoding="utf-8"))[
        "findings"
    ]
    for req in required:
        item, dim, sev_set = req["item"], _canonical_dim(req["dim"]), set(req["severity"])
        match = next(
            (
                f
                for f in findings
                if _items_match(f.get("checklist_item", ""), item)
                and _canonical_dim(f.get("dimension", "")) == dim
                and f.get("severity") in sev_set
            ),
            None,
        )
        assert match, (
            f"{cid}: required finding {item!r} (dim={dim}, sev∈{sev_set}) not found "
            f"in fixture; available items={[f.get('checklist_item') for f in findings]}"
        )


@pytest.mark.parametrize(
    "case_path", _detection_or_clean_cases(), ids=[_case_id(c) for c in _detection_or_clean_cases()]
)
def test_forbidden_findings_absent(case_path: pathlib.Path) -> None:
    case = _load_case(case_path)
    cid = case["id"]
    expected = case.get("expected") or {}
    forbidden = expected.get("forbidden_findings") or []
    findings = json.loads((REPO_ROOT / case["findings_fixture"]).read_text(encoding="utf-8"))[
        "findings"
    ]
    for forb in forbidden:
        item = forb["item"]
        dim = _canonical_dim(forb.get("dim", ""))
        for f in findings:
            if _items_match(f.get("checklist_item", ""), item) and (
                not dim or _canonical_dim(f.get("dimension", "")) == dim
            ):
                pytest.fail(f"{cid}: forbidden finding {item} present: {f.get('id')}")


@pytest.mark.parametrize(
    "case_path", _detection_or_clean_cases(), ids=[_case_id(c) for c in _detection_or_clean_cases()]
)
def test_field_invariants(case_path: pathlib.Path) -> None:
    case = _load_case(case_path)
    cid = case["id"]
    expected = case.get("expected") or {}
    invariants = expected.get("field_invariants") or []
    findings = json.loads((REPO_ROOT / case["findings_fixture"]).read_text(encoding="utf-8"))[
        "findings"
    ]
    for inv in invariants:
        if inv == "every High/Medium finding has non-empty evidence":
            for f in findings:
                if f.get("severity") in ("High", "Medium"):
                    assert f.get("evidence"), f"{cid}: {f.get('id')} High/Medium with empty evidence"
        elif inv == "every High/Medium finding has non-empty validation":
            for f in findings:
                if f.get("severity") in ("High", "Medium"):
                    assert f.get(
                        "validation"
                    ), f"{cid}: {f.get('id')} High/Medium with empty validation"
        elif inv == "every High finding has non-empty current and recommended":
            for f in findings:
                if f.get("severity") == "High":
                    assert f.get("current"), f"{cid}: {f.get('id')} High with empty current"
                    assert f.get("recommended"), f"{cid}: {f.get('id')} High with empty recommended"
        else:
            pytest.fail(f"{cid}: unknown field invariant {inv!r}")


# ---------------------------------------------------------------------------
# Detection: precision/recall acceptance against `defects` array
# ---------------------------------------------------------------------------


def _parse_threshold(spec: str) -> tuple[str, float]:
    """Parse a string like '>= 0.5' into (operator, value)."""
    spec = spec.strip()
    for op in (">=", "<=", "==", ">", "<"):
        if spec.startswith(op):
            return op, float(spec[len(op) :].strip())
    raise ValueError(f"unparseable threshold: {spec!r}")


def _eval_threshold(value: float, op: str, target: float) -> bool:
    return {
        ">=": value >= target,
        "<=": value <= target,
        ">": value > target,
        "<": value < target,
        "==": value == target,
    }[op]


def _detection_cases() -> list[pathlib.Path]:
    return [p for p in CASES if _load_case(p).get("kind") == "detection"]


@pytest.mark.parametrize(
    "case_path", _detection_cases(), ids=[_case_id(c) for c in _detection_cases()]
)
def test_acceptance_precision_recall(case_path: pathlib.Path) -> None:
    case = _load_case(case_path)
    cid = case["id"]
    defects = case.get("defects") or []
    if not defects:
        pytest.skip(f"{cid}: no defects array — precision/recall N/A")
    findings = json.loads((REPO_ROOT / case["findings_fixture"]).read_text(encoding="utf-8"))[
        "findings"
    ]

    matched_defects: set[int] = set()
    tp = 0
    fp = 0
    for f in findings:
        f_item = f.get("checklist_item", "")
        f_dim = _canonical_dim(f.get("dimension", ""))
        hit = None
        for i, d in enumerate(defects):
            if i in matched_defects:
                continue
            if _items_match(f_item, d["item"]) and f_dim == _canonical_dim(d["dim"]):
                hit = i
                break
        if hit is not None:
            matched_defects.add(hit)
            tp += 1
        else:
            fp += 1
    fn = len(defects) - len(matched_defects)
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0

    acceptance = case.get("acceptance") or {}
    if "precision" in acceptance:
        op, target = _parse_threshold(acceptance["precision"])
        assert _eval_threshold(precision, op, target), (
            f"{cid}: precision {precision:.3f} fails {acceptance['precision']} (TP={tp} FP={fp})"
        )
    if "recall" in acceptance:
        op, target = _parse_threshold(acceptance["recall"])
        assert _eval_threshold(recall, op, target), (
            f"{cid}: recall {recall:.3f} fails {acceptance['recall']} (TP={tp} FN={fn})"
        )


# ---------------------------------------------------------------------------
# Coverage floor for the case set
# ---------------------------------------------------------------------------


def test_at_least_five_cases() -> None:
    """Issue #83 ports C1-C5 from the SKILL.md inline contracts. Locked here so a
    partial migration cannot silently ship.
    """
    assert len(CASES) >= 5, f"need ≥5 eval cases, have {len(CASES)}"


def test_every_kind_has_coverage() -> None:
    """Every kind declared in VALID_KINDS must have ≥1 exercising case.

    Uniform per-kind floor (not a family-level ``any(behavior_*)`` check): guards
    each declared kind — including each ``behavior_*`` kind individually — against
    becoming a dead enum member with no exercising case (e.g. the last case of a
    kind being deleted). This does NOT guard against a typo in a case file's
    ``kind:`` value — that is caught by the closed-set membership assert in
    test_yaml_loads_and_has_required_fields, which rejects any unknown kind.
    """
    by_kind: dict[str, int] = {}
    for p in CASES:
        case = _load_case(p)
        by_kind[case["kind"]] = by_kind.get(case["kind"], 0) + 1
    for kind in VALID_KINDS:
        assert by_kind.get(kind, 0) >= 1, f"need ≥1 {kind} case, have {by_kind}"


# ---------------------------------------------------------------------------
# Apply-risk policy helpers and tests (issue #125)
# ---------------------------------------------------------------------------

POLICY_DOC = REPO_ROOT / "docs" / "apply-risk-policy.md"
POLICY_MARKER = "<!-- machine-readable-policy:v1 -->"
_POLICY_FENCE_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)


def _load_policy(path: pathlib.Path = POLICY_DOC) -> dict[str, Any]:
    """Locate the marker, then parse the next fenced ```yaml block.

    The regex anchors on \\n```yaml\\n and the closing \\n```\\n, so inner
    triple-backticks (e.g. inside YAML string values for documentation) do
    not confuse the fence-close detection. Rev3 fix for R2.1.
    """
    text = path.read_text(encoding="utf-8")
    idx = text.find(POLICY_MARKER)
    if idx < 0:
        raise ValueError(f"policy marker {POLICY_MARKER!r} not found in {path}")
    remainder = text[idx + len(POLICY_MARKER):]
    m = _POLICY_FENCE_RE.search(remainder)
    if m is None:
        raise ValueError(f"yaml fence not found after marker in {path}")
    return yaml.safe_load(m.group(1))


def _decide(
    policy: dict[str, Any],
    ec: str | None,
    conf: str,
    br: str,
    ct: str,
) -> dict[str, bool]:
    o = policy["overrides"]
    # Priority O3 → O1 → O2 → baseline (short-circuit BEFORE matrix lookup)
    if ec is None and o.get("null_evidence_class_block"):
        return {"auto_apply_allowed": False, "human_review_required": True}
    if ec == "Low-evidence area" and o.get("low_evidence_block"):
        return {"auto_apply_allowed": False, "human_review_required": True}
    if br == "security-sensitive" and o.get("security_sensitive_ask_first"):
        return {"auto_apply_allowed": False, "human_review_required": True}
    for row in policy["matrix"]:
        if row["evidence_class"] == ec and row["confidence"] == conf:
            return {
                "auto_apply_allowed": row["auto_apply_allowed"],
                "human_review_required": row["human_review_required"],
            }
    return {"auto_apply_allowed": False, "human_review_required": True}  # safe fallback


def _apply_policy_cases() -> list[pathlib.Path]:
    return [p for p in CASES if _load_case(p).get("kind") == "behavior_apply_policy"]


def _parse_markdown_matrix_table(text: str) -> list[tuple[str, str, bool, bool]]:
    """Extract (evidence_class, confidence, auto_apply_allowed, human_review_required)
    tuples from the §Decision Matrix table. R2.5 fix — used for table↔YAML drift check.
    """
    section = text.split("## Decision Matrix", 1)[1].split("## ", 1)[0]
    rows: list[tuple[str, str, bool, bool]] = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 4:
            continue
        if cells[0] in ("evidence_class", "---") or cells[0].startswith("---") or cells[0] == "":
            continue
        if cells[2] not in ("true", "false") or cells[3] not in ("true", "false"):
            continue
        rows.append((cells[0], cells[1], cells[2] == "true", cells[3] == "true"))
    return rows


# ---------------------------------------------------------------------------
# Parametrized eval-case test for behavior_apply_policy cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "case_path",
    _apply_policy_cases(),
    ids=[_case_id(c) for c in _apply_policy_cases()],
)
def test_apply_policy_lookup(case_path: pathlib.Path) -> None:
    case = _load_case(case_path)
    cid = case["id"]
    policy = _load_policy()
    expected = case["expected"]
    if "policy_lookup" in expected:
        for spec in expected["policy_lookup"]:
            inp, out = spec["input"], spec["output"]
            got = _decide(
                policy,
                inp["evidence_class"],
                inp["confidence"],
                inp["blast_radius"],
                inp["change_type"],
            )
            assert got == out, f"{cid}: {inp} → {got}, expected {out}"
    elif "policy_lookup_parametric" in expected:
        p = expected["policy_lookup_parametric"]
        fixed, cart, out = p["fixed"], p["cartesian"], p["output"]
        keys = sorted(cart.keys())
        for combo in itertools.product(*[cart[k] for k in keys]):
            inp = dict(fixed)
            inp.update(dict(zip(keys, combo)))
            got = _decide(
                policy,
                inp.get("evidence_class"),
                inp.get("confidence"),
                inp.get("blast_radius"),
                inp.get("change_type"),
            )
            assert got == out, f"{cid}: {inp} → {got}, expected {out}"
    else:
        pytest.fail(
            f"{cid}: behavior_apply_policy missing policy_lookup or policy_lookup_parametric"
        )


# ---------------------------------------------------------------------------
# Structural invariant tests for the policy doc itself
# ---------------------------------------------------------------------------


def test_policy_doc_structural_invariants() -> None:
    text = POLICY_DOC.read_text(encoding="utf-8")
    # Frontmatter — exactly 2 fence delimiters
    assert sum(1 for line in text.splitlines() if line == "---") == 2
    p = _load_policy()
    assert len(p["matrix"]) == 12, f"matrix must have 12 rows, has {len(p['matrix'])}"
    seen = {(r["evidence_class"], r["confidence"]) for r in p["matrix"]}
    assert len(seen) == 12, "matrix rows must be distinct (ec, conf) pairs"
    for o_key in ("low_evidence_block", "security_sensitive_ask_first", "null_evidence_class_block"):
        assert p["overrides"].get(o_key) is True, f"override {o_key} must be true"
    # Markdown table ↔ YAML drift — strict per-row tuple match (R2.5 fix)
    md_rows = _parse_markdown_matrix_table(text)
    assert len(md_rows) == 12, f"Markdown table must have 12 data rows, has {len(md_rows)}"
    yaml_tuples = {
        (r["evidence_class"], r["confidence"], r["auto_apply_allowed"], r["human_review_required"])
        for r in p["matrix"]
    }
    md_tuples = set(md_rows)
    assert yaml_tuples == md_tuples, (
        f"Markdown table and YAML matrix disagree.\n"
        f"  in YAML only: {yaml_tuples - md_tuples}\n"
        f"  in Markdown only: {md_tuples - yaml_tuples}"
    )


def test_policy_doc_marker_missing(tmp_path: pathlib.Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("# no marker here\n", encoding="utf-8")
    with pytest.raises(ValueError, match="marker"):
        _load_policy(bad)


def test_policy_doc_yaml_fence_missing(tmp_path: pathlib.Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text(f"# x\n{POLICY_MARKER}\nno fence follows\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fence"):
        _load_policy(bad)


def test_load_policy_handles_inner_backticks(tmp_path: pathlib.Path) -> None:
    """R2.1 fix — _load_policy must not be confused by triple-backticks inside YAML body."""
    ok = tmp_path / "ok.md"
    body = (
        f"# x\n{POLICY_MARKER}\n```yaml\n"
        f"matrix:\n"
        f"  - evidence_class: \"Proven result\"\n"
        f"    confidence: high\n"
        f"    auto_apply_allowed: true\n"
        f"    human_review_required: false\n"
        f"    notes: |\n"
        f"      example with literal backticks: ```fenced inside string```\n"
        f"overrides:\n"
        f"  null_evidence_class_block: true\n"
        f"```\n"
    )
    ok.write_text(body, encoding="utf-8")
    got = _load_policy(ok)
    assert len(got["matrix"]) == 1
    assert got["overrides"]["null_evidence_class_block"] is True


def test_decide_missing_evidence_class() -> None:
    """R2 / O3 — missing evidence_class label always blocks auto-apply."""
    policy = _load_policy()
    got = _decide(policy, None, "high", "single-file", "formatting")
    assert got == {"auto_apply_allowed": False, "human_review_required": True}


def test_decide_security_sensitive_blocks_proven_high() -> None:
    """R2 — explicit O2 unit test (not just via case_08)."""
    policy = _load_policy()
    got = _decide(policy, "Proven result", "high", "security-sensitive", "formatting")
    assert got == {"auto_apply_allowed": False, "human_review_required": True}


def test_decide_eleven_row_matrix_falls_to_safe_default() -> None:
    """R2.2 fix — pick a NON-Low-evidence row so O1 doesn't short-circuit; assert fallback."""
    policy = _load_policy()
    # Row 0 is (Proven result, high) — does NOT trigger O1/O2/O3.
    missing_row = policy["matrix"][0]
    assert missing_row["evidence_class"] == "Proven result" and missing_row["confidence"] == "high", (
        "matrix row order must put Proven result/high first; rev3 test depends on it"
    )
    truncated = {**policy, "matrix": policy["matrix"][1:]}  # remove the row we'll query
    got = _decide(
        truncated,
        missing_row["evidence_class"],
        missing_row["confidence"],
        "single-file",
        "formatting",
    )
    assert got == {"auto_apply_allowed": False, "human_review_required": True}, (
        "with the matched row removed, _decide must fall through the matrix loop and return "
        "safe-default — if this passes by short-circuit instead, the test is vacuous"
    )
