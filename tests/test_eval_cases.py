"""Programmatic regression eval harness — replays YAML test cases against
captured/synthesised ``findings.json`` fixtures.

Implements the contract pinned by issue #83. The cases under
``tests/eval_cases/*.yaml`` carry sprint-contract acceptance criteria; the
fixtures under ``tests/fixtures/eval/`` carry (a) the synthetic input artifact
the case is built around, and (b) for ``kind: detection`` and ``kind: clean``
cases, a synthesised ``findings.json`` representing what a well-behaved
``/review-skill`` (or downstream merge layer) should produce on that input.

Behavior cases (``kind: behavior_*``) test analytics or scaffold side effects
rather than findings.json; they have no programmatic replay path here. The
harness validates their YAML schema only — actual behavioural validation
happens through ``/run-eval-cases`` (LLM-driven).

Schema (per case YAML)
----------------------

::

    id: case-01-real-issue
    kind: detection                       # detection | clean | behavior_analytics |
                                          # behavior_scaffold
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

import json
import pathlib
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


VALID_KINDS = ("detection", "clean", "behavior_analytics", "behavior_scaffold")
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
    """At least one detection, one clean, one behavior_* case must exist —
    confirms the schema discriminator is exercised across all branches.
    """
    by_kind: dict[str, int] = {}
    for p in CASES:
        case = _load_case(p)
        by_kind[case["kind"]] = by_kind.get(case["kind"], 0) + 1
    assert by_kind.get("detection", 0) >= 1, f"need ≥1 detection case, have {by_kind}"
    assert by_kind.get("clean", 0) >= 1, f"need ≥1 clean case, have {by_kind}"
    assert any(k.startswith("behavior_") for k in by_kind), (
        f"need ≥1 behavior_* case, have {by_kind}"
    )
