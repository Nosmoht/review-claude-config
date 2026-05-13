#!/usr/bin/env python3
"""Regenerate skills/review-skill/references/merge-policy.yaml from
scoring-rubric.md §Item Inventory + §Grade Caps + §Agent Items.

The rubric is the single source of truth. CI fails on drift via
.github/workflows/policy-consistency.yml — never edit the yaml directly.

Usage:
    python3 scripts/regenerate_merge_policy.py [--check]

--check: exit non-zero if regenerated content differs from on-disk yaml
         (used by CI). Default: write yaml in place.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RUBRIC = REPO_ROOT / "skills/review-claude-config/references/scoring-rubric.md"
YAML_OUT = REPO_ROOT / "skills/review-skill/references/merge-policy.yaml"

EXPECTED_COUNTS: dict[str, int] = {
    "binary_item_ids": 34,
    "narrative_parent_ids": 15,
    "item_dimension": 35,
    "binary_caps": 23,
    "agent_item_dimension": 36,
}

HEADER_LINES = (
    "# AUTO-GENERATED — edit skills/review-claude-config/references/scoring-rubric.md instead.\n"
    "# Regenerate via: python3 scripts/regenerate_merge_policy.py\n"
    "# CI enforces drift via .github/workflows/policy-consistency.yml.\n"
    "# item_dimension: union of binary items + narrative parents that declare a dimension.\n"
)


def _parse_pipe_table(lines: list[str], start_idx: int) -> list[list[str]]:
    """Parse a pipe-delimited markdown table starting at ``start_idx``.

    ``start_idx`` must point at the header row (``| Col | Col |``). The
    separator row that follows is skipped. Parsing stops at the first
    non-pipe-prefixed line. Returns a list of data rows, each a list of
    stripped cell strings.
    """
    rows: list[list[str]] = []
    i = start_idx + 2  # skip header + separator
    while i < len(lines):
        line = lines[i].rstrip("\n")
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
        i += 1
    return rows


def _find_table(lines: list[str], section_h2: str, subsection_h3: str | None = None) -> int:
    """Return the index of the header row of the first pipe-table inside the
    ``## section_h2`` block (and optionally inside the ``### subsection_h3``
    sub-block). Raises ``ValueError`` if not found.
    """
    in_section = False
    in_subsection = subsection_h3 is None
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        if line.startswith("## ") and line[3:].strip() == section_h2:
            in_section = True
            in_subsection = subsection_h3 is None
            continue
        if in_section and line.startswith("## "):
            break  # left the section
        if in_section and subsection_h3 is not None and line.startswith("### "):
            in_subsection = line[4:].strip() == subsection_h3
            continue
        if in_section and in_subsection and line.startswith("|") and i + 1 < len(lines):
            sep = lines[i + 1].strip()
            if sep.startswith("|") and set(sep) <= set("|-: "):
                return i
    raise ValueError(
        f"Could not find pipe-table in section '{section_h2}'"
        + (f" / subsection '{subsection_h3}'" if subsection_h3 else "")
    )


def parse_rubric(text: str) -> dict:
    """Parse the scoring-rubric markdown into the merge-policy dict.

    Returns keys (in deterministic order): ``policy_version``,
    ``binary_item_ids``, ``narrative_parent_ids``, ``item_dimension``,
    ``binary_caps``, ``agent_item_dimension``.
    """
    lines = text.splitlines(keepends=True)

    # 1) §Item Inventory → ###Binary-Evaluated Items (33 rows: Item | Dimension)
    binary_idx = _find_table(lines, "Item Inventory", "Binary-Evaluated Items (skill rubric, 34)")
    binary_rows = _parse_pipe_table(lines, binary_idx)
    binary_item_ids: list[str] = [r[0] for r in binary_rows if r and r[0]]
    item_dimension: dict[str, str] = {}
    for r in binary_rows:
        if len(r) >= 2 and r[0]:
            item_dimension[r[0]] = r[1]

    # 2) §Item Inventory → ###Drop-from-Merge Items (15 rows: Item | Reason | Dimension)
    narrative_idx = _find_table(lines, "Item Inventory", "Drop-from-Merge Items (narrative parents, 15)")
    narrative_rows = _parse_pipe_table(lines, narrative_idx)
    narrative_parent_ids: list[str] = [r[0] for r in narrative_rows if r and r[0]]
    for r in narrative_rows:
        if len(r) >= 3 and r[0]:
            item, dim = r[0], r[2]
            if dim and dim != "—":
                if item in item_dimension:
                    if item_dimension[item] != dim:
                        raise ValueError(
                            f"Dimension conflict for {item}: binary={item_dimension[item]!r} narrative={dim!r}"
                        )
                else:
                    item_dimension[item] = dim

    # 3) §Grade Caps (22 rows: Item | Dimension | Cap)
    caps_idx = _find_table(lines, "Grade Caps")
    caps_rows = _parse_pipe_table(lines, caps_idx)
    binary_caps: list[dict[str, str]] = []
    for r in caps_rows:
        if len(r) >= 3 and r[0]:
            binary_caps.append({"item": r[0], "dimension": r[1], "cap": r[2]})

    # 4) §Agent Items (36 rows: Item | Dimension)
    agent_idx = _find_table(lines, "Agent Items")
    agent_rows = _parse_pipe_table(lines, agent_idx)
    agent_item_dimension: dict[str, str] = {}
    for r in agent_rows:
        if len(r) >= 2 and r[0]:
            agent_item_dimension[r[0]] = r[1]

    policy: dict = {
        "policy_version": "1.0",
        "binary_item_ids": binary_item_ids,
        "narrative_parent_ids": narrative_parent_ids,
        "item_dimension": item_dimension,
        "binary_caps": binary_caps,
        "agent_item_dimension": agent_item_dimension,
    }

    counts = {
        "binary_item_ids": len(binary_item_ids),
        "narrative_parent_ids": len(narrative_parent_ids),
        "item_dimension": len(item_dimension),
        "binary_caps": len(binary_caps),
        "agent_item_dimension": len(agent_item_dimension),
    }
    mismatches = [f"  {k}: expected={EXPECTED_COUNTS[k]} got={v}" for k, v in counts.items() if v != EXPECTED_COUNTS[k]]
    if mismatches:
        raise ValueError("Parsed counts diverge from expected:\n" + "\n".join(mismatches))

    return policy


def emit_yaml(policy: dict) -> str:
    """Serialize ``policy`` to a deterministic YAML string with the
    AUTO-GENERATED header. Top-level keys preserve insertion order.
    ``binary_caps`` entries render as flow-style mappings for compactness.
    """
    chunks: list[str] = [HEADER_LINES]

    head = {k: policy[k] for k in ("policy_version", "binary_item_ids", "narrative_parent_ids")}
    chunks.append(yaml.safe_dump(head, sort_keys=False, default_flow_style=False, allow_unicode=True))

    chunks.append(
        yaml.safe_dump(
            {"item_dimension": policy["item_dimension"]},
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )
    )

    # binary_caps: each entry rendered as flow-style mapping for compactness.
    chunks.append("binary_caps:\n")
    for entry in policy["binary_caps"]:
        flow = yaml.safe_dump(entry, sort_keys=False, default_flow_style=True, allow_unicode=True).strip()
        chunks.append(f"  - {flow}\n")

    chunks.append(
        yaml.safe_dump(
            {"agent_item_dimension": policy["agent_item_dimension"]},
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )
    )

    out = "".join(chunks)
    if not out.endswith("\n"):
        out += "\n"
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero (2) if regenerated content differs from on-disk yaml",
    )
    args = parser.parse_args(argv)

    try:
        text = RUBRIC.read_text(encoding="utf-8")
        policy = parse_rubric(text)
        rendered = emit_yaml(policy)
    except OSError as e:
        print(f"regenerate_merge_policy: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        try:
            rel = RUBRIC.relative_to(REPO_ROOT)
        except ValueError:
            rel = RUBRIC
        print(f"regenerate_merge_policy: {rel}: {e}", file=sys.stderr)
        return 1

    if args.check:
        try:
            current = YAML_OUT.read_text(encoding="utf-8")
        except OSError as e:
            print(f"regenerate_merge_policy: cannot read {YAML_OUT}: {e}", file=sys.stderr)
            return 2
        if current != rendered:
            try:
                rel = YAML_OUT.relative_to(REPO_ROOT)
            except ValueError:
                rel = YAML_OUT
            print(
                f"DRIFT: {rel} is out of date.\nRun: python3 scripts/regenerate_merge_policy.py",
                file=sys.stderr,
            )
            return 2
        return 0

    YAML_OUT.parent.mkdir(parents=True, exist_ok=True)
    YAML_OUT.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
