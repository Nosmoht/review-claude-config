#!/usr/bin/env python3
"""Parse a perspective agent's Markdown certificate into the JSON shape that
``scripts/merge_findings.py:merge_directory`` consumes.

The agent contract pinned in ``agents/review-perspective-clarity.md`` requires
this Markdown shape:

    [optional prose preamble — Haiku occasionally emits one despite the
     'no prose preamble' Hard Rule]
    ### Perspective
    <name>

    ### Certificate
    | Dimension | Grade | Justification |
    |-----------|-------|---------------|
    | Clarity | A | ... |
    ... 8 rows including 'Overall' ...

    ### Findings

    #### Finding (severity: High, dimension: Clarity, checklist_item: WS-1,
                  primary_focus: true, owner_conflict: false, hint_owner: null)
    Evidence: ...
    Why it matters: ...
    Validation: ...
    Current: ...
    Recommended: ...

    ---

    #### Finding ...

ERROR shortcut: ``### ERROR\\n<reason>`` is emitted when the prompt context is
incomplete or the artifact is unreadable. The parser surfaces that as
``{'error': reason}``.

The parser is deliberately lenient — Haiku output drifts from the strict
contract in small ways (preamble, missing trailing separator, occasional
field-label variants). The cost of brittle parsing is silent failures in the
merge layer; the cost of leniency is bounded because merge_findings.py and
the JSON Schema reject malformed shapes downstream.
"""

from __future__ import annotations

import re
from typing import Any

PERSPECTIVE_RE = re.compile(r"^###\s+Perspective\s*$", re.MULTILINE)
CERTIFICATE_RE = re.compile(r"^###\s+Certificate\s*$", re.MULTILINE)
FINDINGS_RE = re.compile(r"^###\s+Findings\s*$", re.MULTILINE)
ERROR_RE = re.compile(r"^###\s+ERROR\s*$", re.MULTILINE)
FINDING_HEADER_RE = re.compile(r"^####\s+Finding\s*\((.+?)\)\s*$", re.MULTILINE)
SEPARATOR_RE = re.compile(r"^---+\s*$", re.MULTILINE)

VALID_DIMENSIONS = (
    "Clarity",
    "Completeness",
    "Prompt Engineering",
    "Context Engineering",
    "Goal Alignment",
    "Safety",
    "Metadata",
)
VALID_GRADES = frozenset({"A", "B", "C", "D", "F"})

# Finding field labels in canonical order. The parser collects multi-line
# bodies until the next label or the next separator/header.
FIELD_LABELS = (
    "Evidence",
    "Why it matters",
    "Validation",
    "Current",
    "Recommended",
)
FIELD_KEY_MAP = {
    "Evidence": "evidence",
    "Why it matters": "why",
    "Validation": "validation",
    "Current": "current",
    "Recommended": "recommended",
}


def _normalise_severity(raw: str) -> str:
    s = (raw or "").strip()
    low = s.lower()
    if low == "high":
        return "High"
    if low == "medium":
        return "Medium"
    if low == "low":
        return "Low"
    return s  # pass through; merge_findings demotes off-spec to Low


def _parse_bool_or_none(raw: str) -> bool | None:
    s = (raw or "").strip().lower()
    if s in ("true", "yes"):
        return True
    if s in ("false", "no"):
        return False
    if s in ("null", "none", ""):
        return None
    return None


def _parse_string_or_none(raw: str) -> str | None:
    s = (raw or "").strip()
    if s.lower() in ("null", "none", ""):
        return None
    return s


def _parse_finding_header(header_inner: str) -> dict[str, Any]:
    """Parse the comma-separated metadata inside the ``#### Finding (...)``
    parens.

    Tolerant to key whitespace and missing keys. Keys we recognise:
      severity, dimension, checklist_item, primary_focus, owner_conflict,
      hint_owner.
    """
    out: dict[str, Any] = {}
    # Split on `, ` but only when followed by `<key>:`. A naive split breaks
    # if any value carried a comma; in practice the agent contract forbids
    # commas inside header values.
    parts = re.split(r",\s+(?=[A-Za-z_]+:)", header_inner.strip())
    for part in parts:
        if ":" not in part:
            continue
        key, _, val = part.partition(":")
        key = key.strip().lower()
        val = val.strip()
        if key == "severity":
            out["severity"] = _normalise_severity(val)
        elif key == "dimension":
            out["dimension"] = val
        elif key == "checklist_item":
            out["checklist_item"] = val
        elif key == "primary_focus":
            out["primary_focus"] = _parse_bool_or_none(val)
        elif key == "owner_conflict":
            out["owner_conflict"] = _parse_bool_or_none(val)
        elif key == "hint_owner":
            out["hint_owner"] = _parse_string_or_none(val)
    return out


def _parse_grade_table(block: str) -> dict[str, str]:
    """Parse a Markdown grade table into ``{dimension: grade}``.

    Captures only the seven named dimensions; "Overall" is dropped (the merge
    layer recomputes it). Off-spec grades (anything outside A-F) are dropped
    silently — merge_findings handles missing dimensions as F via owner-weighted
    grading on the remaining perspectives.
    """
    out: dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        dim, grade = cells[0], cells[1]
        if dim in VALID_DIMENSIONS and grade in VALID_GRADES:
            out[dim] = grade
    return out


def _parse_finding_body(body: str) -> dict[str, str]:
    """Walk ``body`` line by line, extracting the five canonical fields.

    A field starts on a line ``<Label>: <text>``; continuation lines belong to
    that field until the next recognised label or the end of the body. Empty
    lines are preserved within a field — Haiku occasionally emits multi-paragraph
    Recommended blocks.
    """
    out: dict[str, str] = {}
    current_label: str | None = None
    current_lines: list[str] = []

    def _flush() -> None:
        nonlocal current_label, current_lines
        if current_label is not None:
            out[FIELD_KEY_MAP[current_label]] = "\n".join(current_lines).strip()
        current_label = None
        current_lines = []

    for line in body.splitlines():
        # Match a field-label prefix at line start. Tolerate up to 4 leading
        # spaces — Haiku occasionally indents labels under nested list items
        # or after a quote block, and treating those as continuation drops
        # the field silently. Beyond 4 spaces is markdown code-block territory
        # (literal content), not field-label intent.
        matched_label = None
        stripped = line.lstrip(" ")
        leading = len(line) - len(stripped)
        if leading <= 4:
            for label in FIELD_LABELS:
                prefix = f"{label}:"
                if stripped.startswith(prefix):
                    matched_label = label
                    rest = stripped[len(prefix) :].lstrip()
                    break
        if matched_label is not None:
            _flush()
            current_label = matched_label
            current_lines = [rest]
        elif current_label is not None:
            current_lines.append(line)
        # else: line outside any field (e.g. preamble before first label) — drop
    _flush()
    return out


def parse_certificate(
    markdown: str,
    *,
    artifact_path: str = "",
    perspective_override: str | None = None,
) -> dict[str, Any]:
    """Parse an agent's Markdown certificate into a merge-ready dict.

    ``artifact_path`` is stamped onto every finding so merge_findings'
    canonicalize_perspective_ids() can build deterministic IDs. Perspective
    agents do not emit a dedicated path field — the embedded ``at <path>:<line>``
    fragments inside Evidence lines are not reliably structured.

    ``perspective_override`` lets the harness force a perspective name in the
    rare case the agent emits an empty or off-spec ``### Perspective`` block.

    Returns a dict whose top-level shape matches what
    ``scripts/merge_findings.py:merge_directory`` expects:

        {
            'perspective': str | None,
            'dimensions': {<dim>: <grade>, ...},
            'findings': [<finding_dict>, ...],
            'artifact_frontmatter': {},
            'error': str | None,  # only set on ERROR shortcut
        }
    """
    text = markdown or ""

    # ERROR shortcut — capture the reason and return early.
    err = ERROR_RE.search(text)
    if err:
        # The reason is the first non-empty line after the header.
        tail = text[err.end() :].lstrip("\n")
        reason = tail.split("\n", 1)[0].strip()
        return {
            "perspective": perspective_override,
            "dimensions": {},
            "findings": [],
            "artifact_frontmatter": {},
            "error": reason or "unspecified",
        }

    # Locate the canonical sections. Preamble before `### Perspective` is dropped.
    psp_match = PERSPECTIVE_RE.search(text)
    cert_match = CERTIFICATE_RE.search(text)
    finds_match = FINDINGS_RE.search(text)

    perspective_name: str | None = perspective_override
    if perspective_name is None and psp_match is not None:
        # Read the next non-empty line.
        tail = text[psp_match.end() :]
        for line in tail.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                perspective_name = line
                break

    # Grade table block — between Certificate header and either Findings header
    # or end of text.
    dimensions: dict[str, str] = {}
    if cert_match is not None:
        cert_start = cert_match.end()
        cert_end = finds_match.start() if finds_match is not None else len(text)
        dimensions = _parse_grade_table(text[cert_start:cert_end])

    # Findings block — split on '#### Finding' headers.
    findings: list[dict[str, Any]] = []
    if finds_match is not None:
        block = text[finds_match.end() :]
        # Iterate matches and pair each header with the slice up to the next
        # header (or the end of the block).
        headers = list(FINDING_HEADER_RE.finditer(block))
        for i, m in enumerate(headers):
            inner = m.group(1)
            body_start = m.end()
            body_end = headers[i + 1].start() if i + 1 < len(headers) else len(block)
            body = block[body_start:body_end]
            # Strip trailing separator line(s) — they are visual, not data.
            body = SEPARATOR_RE.sub("", body).strip()

            meta = _parse_finding_header(inner)
            fields = _parse_finding_body(body)

            finding: dict[str, Any] = {
                "severity": meta.get("severity") or "",
                "dimension": meta.get("dimension") or "",
                "checklist_item": meta.get("checklist_item") or "",
                "primary_focus": meta.get("primary_focus", False),
                "owner_conflict": meta.get("owner_conflict", False),
                "hint_owner": meta.get("hint_owner"),
                "evidence": fields.get("evidence", ""),
                "why": fields.get("why", ""),
                "validation": fields.get("validation", ""),
                "current": fields.get("current", ""),
                "recommended": fields.get("recommended", ""),
                "path": artifact_path,
                "line_range": "",
                "perspective": perspective_name or "",
            }
            # Build a stable ID compatible with merge_findings'
            # canonicalize_perspective_ids: <item>:<path>:<dim>/v1 — overwritten
            # by canonicaliser when the dimension is pinned.
            item = finding["checklist_item"]
            dim = finding["dimension"]
            if item and artifact_path and dim:
                finding["id"] = f"{item}:{artifact_path}:{dim}/v1"

            findings.append(finding)

    return {
        "perspective": perspective_name,
        "dimensions": dimensions,
        "findings": findings,
        "artifact_frontmatter": {},
        "error": None,
    }
