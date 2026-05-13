"""Tests for scripts/regenerate_merge_policy.py."""

from __future__ import annotations

import pathlib
import sys

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import regenerate_merge_policy as rmp  # noqa: E402

EXPECTED = {
    "binary_item_ids": 30,
    "narrative_parent_ids": 15,
    "item_dimension": 31,
    "binary_caps": 19,
    "agent_item_dimension": 36,
}

TOP_KEYS = (
    "policy_version",
    "binary_item_ids",
    "narrative_parent_ids",
    "item_dimension",
    "binary_caps",
    "agent_item_dimension",
)


@pytest.fixture(scope="module")
def rubric_text() -> str:
    return rmp.RUBRIC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def policy(rubric_text: str) -> dict:
    return rmp.parse_rubric(rubric_text)


def test_parse_rubric_counts_match_expected(policy: dict) -> None:
    assert len(policy["binary_item_ids"]) == EXPECTED["binary_item_ids"]
    assert len(policy["narrative_parent_ids"]) == EXPECTED["narrative_parent_ids"]
    assert len(policy["item_dimension"]) == EXPECTED["item_dimension"]
    assert len(policy["binary_caps"]) == EXPECTED["binary_caps"]
    assert len(policy["agent_item_dimension"]) == EXPECTED["agent_item_dimension"]
    # Ground-truth: WS-4 narrative-with-dim contributes; META-2 dedup'd.
    assert policy["item_dimension"]["WS-4"] == "Clarity"
    assert policy["item_dimension"]["META-2"] == "Metadata"


def test_emit_yaml_roundtrip_byte_stable(policy: dict) -> None:
    a = rmp.emit_yaml(policy)
    b = rmp.emit_yaml(rmp.parse_rubric(rmp.RUBRIC.read_text(encoding="utf-8")))
    assert a == b
    assert a.endswith("\n")
    assert a.startswith("# AUTO-GENERATED")


def test_emit_yaml_matches_on_disk_yaml(policy: dict) -> None:
    """Direct emission ↔ on-disk equality (localizes failure to the emitter
    when CLI plumbing in --check is fine)."""
    assert rmp.emit_yaml(policy) == rmp.YAML_OUT.read_text(encoding="utf-8")


def test_emitted_yaml_is_valid_yaml_safe_load(policy: dict) -> None:
    rendered = rmp.emit_yaml(policy)
    loaded = yaml.safe_load(rendered)
    assert tuple(loaded) == TOP_KEYS
    for k, expected_count in EXPECTED.items():
        assert len(loaded[k]) == expected_count
    # binary_caps shape
    assert all(set(entry) == {"item", "dimension", "cap"} for entry in loaded["binary_caps"])


def test_check_mode_passes_on_in_repo_yaml() -> None:
    rc = rmp.main(["--check"])
    assert rc == 0


def test_check_mode_fails_on_corrupt_yaml(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    corrupt = tmp_path / "merge-policy.yaml"
    corrupt.write_text("# corrupted\npolicy_version: '0.0'\n", encoding="utf-8")
    monkeypatch.setattr(rmp, "YAML_OUT", corrupt)
    rc = rmp.main(["--check"])
    assert rc == 2


def test_synthetic_rubric_snippet_parses(tmp_path: pathlib.Path) -> None:
    """Tiny synthetic rubric exercises the parser end-to-end without
    depending on the real rubric counts."""
    snippet = (
        "## Item Inventory\n\n"
        "### Binary-Evaluated Items (skill rubric, 32)\n\n"
        "| Item | Dimension |\n"
        "|---|---|\n"
        "| FOO-1 | Clarity |\n"
        "| BAR-2 | Safety |\n"
        "| BAZ-3 | Metadata |\n\n"
        "### Drop-from-Merge Items (narrative parents, 15)\n\n"
        "| Item | Reason | Dimension |\n"
        "|---|---|---|\n"
        "| OLD-1 | Superseded by FOO-1 | — |\n"
        "| OLD-2 | Drop-from-merge | Clarity |\n\n"
        "## Grade Caps\n\n"
        "| Item | Dimension | Cap |\n"
        "|---|---|---|\n"
        "| FOO-1 | Clarity | C |\n"
        "| BAZ-3 | Metadata | F |\n\n"
        "## Agent Items\n\n"
        "| Item | Dimension |\n"
        "|---|---|\n"
        "| AGT-1 | Clarity |\n"
        "| AGT-2 | Safety |\n"
    )
    # Skip the global EXPECTED_COUNTS validation by parsing tables directly.
    lines = snippet.splitlines(keepends=True)
    binary_idx = rmp._find_table(lines, "Item Inventory", "Binary-Evaluated Items (skill rubric, 32)")
    binary_rows = rmp._parse_pipe_table(lines, binary_idx)
    assert [r[0] for r in binary_rows] == ["FOO-1", "BAR-2", "BAZ-3"]
    narrative_idx = rmp._find_table(lines, "Item Inventory", "Drop-from-Merge Items (narrative parents, 15)")
    narrative_rows = rmp._parse_pipe_table(lines, narrative_idx)
    assert [r[0] for r in narrative_rows] == ["OLD-1", "OLD-2"]
    caps_idx = rmp._find_table(lines, "Grade Caps")
    caps_rows = rmp._parse_pipe_table(lines, caps_idx)
    assert [r[0] for r in caps_rows] == ["FOO-1", "BAZ-3"]
    agent_idx = rmp._find_table(lines, "Agent Items")
    agent_rows = rmp._parse_pipe_table(lines, agent_idx)
    assert [r[0] for r in agent_rows] == ["AGT-1", "AGT-2"]
