"""Tests for scripts/validate_description_graph.py.

Covers ≥20 cases per plan §3 (tests #1-#20):
  1  no_findings_clean_repo
  2  name_collision_same_kind
  3  name_collision_cross_kind_excluded
  4  reciprocal_asymmetry_canonical_phrase
  5  reciprocal_grammar_lowercase
  6  cluster_conflict_above_threshold
  7  cluster_skipped_when_model2vec_missing
  8  cluster_connected_components
  9  f_grade_token_count
 10  aggregate_budget_warn
 11  aggregate_budget_error
 12  empty_repo
 13  single_primitive_repo
 14  missing_description_field
 15  scrub_strips_user_home
 16  scrub_strips_rfc1918
 17  token_grade_boundaries
 18  format_json_shape
 19  format_text_human_readable
 20  no_homedir_in_script_self
"""
from __future__ import annotations

import importlib
import json
import pathlib
import random
import secrets
import sys
import types

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import validate_description_graph as vdg

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SKILL_TEMPLATE = """\
---
name: {name}
description: {description}
---
# body
"""
AGENT_TEMPLATE = """\
---
name: {name}
description: {description}
---
# body
"""


def _make_skill(tmp_path: pathlib.Path, name: str, description: str) -> pathlib.Path:
    skill_dir = tmp_path / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    p = skill_dir / "SKILL.md"
    p.write_text(SKILL_TEMPLATE.format(name=name, description=description), encoding="utf-8")
    return p


def _make_agent(tmp_path: pathlib.Path, name: str, description: str) -> pathlib.Path:
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    p = agents_dir / f"{name}.md"
    p.write_text(AGENT_TEMPLATE.format(name=name, description=description), encoding="utf-8")
    return p


def _make_plugin(tmp_path: pathlib.Path, name: str, description: str) -> pathlib.Path:
    plugin_dir = tmp_path / ".claude-plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    p = plugin_dir / "plugin.json"
    p.write_text(json.dumps({"name": name, "description": description}), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Test 1 — clean repo exits 0
# ---------------------------------------------------------------------------

def test_no_findings_clean_repo(tmp_path):
    _make_skill(tmp_path, "alpha", "Runs alpha analysis. Use for alpha tasks only.")
    _make_skill(tmp_path, "beta", "Runs beta analysis. Use for beta tasks only.")
    _make_skill(tmp_path, "gamma", "Runs gamma synthesis. Use for gamma aggregation only.")
    prims = vdg.discover_primitives(tmp_path)
    assert len(prims) == 3
    findings = (
        vdg.check_name_collision(prims)
        + vdg.check_reciprocal_symmetry(prims)
        + vdg.check_token_grades(prims)
        + vdg.check_aggregate_budget(prims)
    )
    assert findings == []


# ---------------------------------------------------------------------------
# Test 2 — name collision same kind → error
# ---------------------------------------------------------------------------

def test_name_collision_same_kind(tmp_path):
    (tmp_path / "skills" / "alpha").mkdir(parents=True)
    (tmp_path / "skills" / "alpha-dup").mkdir(parents=True)
    (tmp_path / "skills" / "alpha" / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(name="alpha", description="First alpha."), encoding="utf-8"
    )
    (tmp_path / "skills" / "alpha-dup" / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(name="alpha", description="Second alpha."), encoding="utf-8"
    )
    prims = vdg.discover_primitives(tmp_path)
    findings = vdg.check_name_collision(prims)
    assert len(findings) == 1
    f = findings[0]
    assert f.check == "name_collision"
    assert f.severity == "error"
    assert len(f.primitives) == 2
    assert all("SKILL.md" in p for p in f.primitives)


# ---------------------------------------------------------------------------
# Test 3 — name collision cross-kind is NOT flagged
# ---------------------------------------------------------------------------

def test_name_collision_cross_kind_excluded(tmp_path):
    _make_skill(tmp_path, "common", "Skill with name common.")
    _make_plugin(tmp_path, "common", "Plugin with name common.")
    prims = vdg.discover_primitives(tmp_path)
    findings = vdg.check_name_collision(prims)
    assert findings == []


# ---------------------------------------------------------------------------
# Test 4 — reciprocal asymmetry canonical phrase
# ---------------------------------------------------------------------------

def test_reciprocal_asymmetry_canonical_phrase(tmp_path):
    # A references B but B has no back-ref
    _make_skill(tmp_path, "review-skill", "Reviews a single skill. Do NOT use for agents — use /review-agent instead.")
    _make_skill(tmp_path, "review-agent", "Reviews a single agent. Standalone tool.")
    prims = vdg.discover_primitives(tmp_path)
    findings = vdg.check_reciprocal_symmetry(prims)
    asymmetric = [f for f in findings if f.check == "reciprocal_asymmetry"]
    assert len(asymmetric) >= 1
    sources = {f.metadata["source"] for f in asymmetric}
    assert "review-skill" in sources


# ---------------------------------------------------------------------------
# Test 5 — reciprocal grammar lowercase
# ---------------------------------------------------------------------------

def test_reciprocal_grammar_lowercase(tmp_path):
    _make_skill(tmp_path, "tool-a", "do not use this; use /tool-b")
    _make_skill(tmp_path, "tool-b", "Standalone tool-b description.")
    prims = vdg.discover_primitives(tmp_path)
    findings = vdg.check_reciprocal_symmetry(prims)
    asymmetric = [f for f in findings if f.check == "reciprocal_asymmetry"]
    sources = {f.metadata["source"] for f in asymmetric}
    assert "tool-a" in sources


# ---------------------------------------------------------------------------
# Test 6 — cluster conflict above threshold (requires model2vec)
# ---------------------------------------------------------------------------

def test_cluster_conflict_above_threshold(tmp_path):
    pytest.importorskip("model2vec")
    # s1 and s2 share near-identical descriptions (cosine ≥ 0.85 verified against
    # minishlab/potion-base-8M); s3 is semantically unrelated.
    _make_skill(tmp_path, "s1", "review skill files for quality issues")
    _make_skill(tmp_path, "s2", "review skill source files for quality issues")
    _make_skill(tmp_path, "s3", "schedule remote cron jobs for background execution")
    prims = vdg.discover_primitives(tmp_path)
    findings = vdg.check_semantic_clusters(prims)
    cluster_findings = [f for f in findings if f.check == "cluster_conflict"]
    # Exactly 1 cluster component expected for (s1, s2); s3 is different
    assert len(cluster_findings) == 1


# ---------------------------------------------------------------------------
# Test 7 — cluster skipped when model2vec missing
# ---------------------------------------------------------------------------

def test_cluster_skipped_when_model2vec_missing(monkeypatch):
    monkeypatch.setattr(vdg, "EMBEDDINGS_AVAILABLE", False)
    prims = [
        vdg.Primitive("skill", "skills/a/SKILL.md", "a", "description a"),
        vdg.Primitive("skill", "skills/b/SKILL.md", "b", "description b"),
    ]
    findings = vdg.check_semantic_clusters(prims)
    assert len(findings) == 1
    assert findings[0].check == "cluster_skipped"
    assert findings[0].severity == "warning"


# ---------------------------------------------------------------------------
# Test 8 — connected-component closure emits ONE finding per cluster
# ---------------------------------------------------------------------------

def test_cluster_connected_components(tmp_path):
    pytest.importorskip("model2vec")
    # Four descriptions forming one connected component via union-find transitivity.
    # Pairwise similarities verified against minishlab/potion-base-8M:
    #   (files, source files)=0.949, (files, source)=0.851, (source files, source)=0.907,
    #   (source files, sources)=0.868, (source, sources)=0.956 — all ≥0.85 on at least
    #   one path so all 4 merge into one component.
    for i, suffix in enumerate(["files", "source files", "source", "sources"]):
        _make_skill(tmp_path, f"rev-{i}", f"review skill {suffix} for quality issues")
    prims = vdg.discover_primitives(tmp_path)
    findings = vdg.check_semantic_clusters(prims)
    cluster_findings = [f for f in findings if f.check == "cluster_conflict"]
    # All 4 should be in a single component → ONE finding
    assert len(cluster_findings) == 1
    assert len(cluster_findings[0].primitives) == 4


# ---------------------------------------------------------------------------
# Test 9 — F-grade on description >4000 chars
# ---------------------------------------------------------------------------

def test_f_grade_token_count(tmp_path):
    long_desc = "word " * 1001  # 5005 chars → 1251 tokens > 1000
    _make_skill(tmp_path, "long-skill", long_desc.strip())
    prims = vdg.discover_primitives(tmp_path)
    findings = vdg.check_token_grades(prims)
    assert len(findings) == 1
    assert findings[0].check == "f_grade"
    assert findings[0].severity == "warning"


# ---------------------------------------------------------------------------
# Test 10 — aggregate budget warn (65k–120k)
# ---------------------------------------------------------------------------

def test_aggregate_budget_warn(tmp_path):
    # 70k tokens = 280k chars across 10 skills (28k chars each)
    for i in range(10):
        _make_skill(tmp_path, f"big-{i}", "x" * 28_000)
    prims = vdg.discover_primitives(tmp_path)
    findings = vdg.check_aggregate_budget(prims)
    assert len(findings) == 1
    assert findings[0].check == "aggregate_budget_warn"
    assert findings[0].severity == "warning"


# ---------------------------------------------------------------------------
# Test 11 — aggregate budget error (>120k)
# ---------------------------------------------------------------------------

def test_aggregate_budget_error(tmp_path):
    # 125k tokens = 500k chars
    for i in range(10):
        _make_skill(tmp_path, f"huge-{i}", "x" * 50_000)
    prims = vdg.discover_primitives(tmp_path)
    findings = vdg.check_aggregate_budget(prims)
    assert len(findings) == 1
    assert findings[0].check == "aggregate_budget_error"
    assert findings[0].severity == "error"


# ---------------------------------------------------------------------------
# Test 12 — empty repo → no crash
# ---------------------------------------------------------------------------

def test_empty_repo(tmp_path):
    prims = vdg.discover_primitives(tmp_path)
    assert prims == []
    findings = (
        vdg.check_name_collision(prims)
        + vdg.check_reciprocal_symmetry(prims)
        + vdg.check_token_grades(prims)
        + vdg.check_aggregate_budget(prims)
    )
    assert findings == []


# ---------------------------------------------------------------------------
# Test 13 — single primitive → cluster check doesn't crash
# ---------------------------------------------------------------------------

def test_single_primitive_repo(tmp_path):
    _make_skill(tmp_path, "solo", "solo skill description")
    prims = vdg.discover_primitives(tmp_path)
    assert len(prims) == 1
    # Should not raise
    findings = vdg.check_semantic_clusters(prims)
    # Either skipped or no cluster findings (n<2)
    cluster_findings = [f for f in findings if f.check == "cluster_conflict"]
    assert cluster_findings == []


# ---------------------------------------------------------------------------
# Test 14 — missing description field → description=""
# ---------------------------------------------------------------------------

def test_missing_description_field(tmp_path):
    skill_dir = tmp_path / "skills" / "no-desc"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: no-desc\n---\n# body\n", encoding="utf-8"
    )
    prims = vdg.discover_primitives(tmp_path)
    assert len(prims) == 1
    assert prims[0].name == "no-desc"
    assert prims[0].description == ""


# ---------------------------------------------------------------------------
# Test 15 — scrub strips user-home paths (runtime-constructed)
# ---------------------------------------------------------------------------

def test_scrub_strips_user_home():
    # Construct at runtime so no stable user-home path appears in source
    for prefix in ("/Users", "/home"):
        rand_user = secrets.token_hex(4)
        literal = f"{prefix}/{rand_user}/secret/path"
        scrubbed = vdg.scrub(literal)
        assert literal not in scrubbed, f"scrub() did not remove {literal!r}"
        assert "<USER-HOME>" in scrubbed


# ---------------------------------------------------------------------------
# Test 16 — scrub strips RFC1918 addresses (runtime-constructed)
# ---------------------------------------------------------------------------

def test_scrub_strips_rfc1918():
    # Construct at runtime: random 172.16.x.x address
    second = random.randint(16, 31)
    third = random.randint(0, 255)
    fourth = random.randint(1, 254)
    literal = f"172.{second}.{third}.{fourth}"
    scrubbed = vdg.scrub(literal)
    assert literal not in scrubbed, f"scrub() did not remove RFC1918 {literal!r}"
    assert "<INTERNAL-IP>" in scrubbed


# ---------------------------------------------------------------------------
# Test 17 — token grade boundaries monotonicity (hypothesis)
# ---------------------------------------------------------------------------

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402


@given(chars=st.integers(min_value=0, max_value=40_000))
@settings(max_examples=200)
def test_token_grade_boundaries(chars):
    grade = vdg._grade(chars)
    tokens = chars // 4
    # Monotonicity: grade should correspond to correct bucket
    if tokens <= 100:
        assert grade == "A"
    elif tokens <= 300:
        assert grade == "B"
    elif tokens <= 600:
        assert grade == "C"
    elif tokens <= 1000:
        assert grade == "D"
    else:
        assert grade == "F"


# ---------------------------------------------------------------------------
# Test 18 — format_json shape
# ---------------------------------------------------------------------------

def test_format_json_shape(tmp_path):
    _make_skill(tmp_path, "a", "skill a description")
    prims = vdg.discover_primitives(tmp_path)
    findings = vdg.check_name_collision(prims)
    out = vdg.format_json(findings, len(prims))
    data = json.loads(out)
    assert isinstance(data["findings"], list)
    assert isinstance(data["summary"], dict)
    assert data["summary"]["total_primitives"] == 1


# ---------------------------------------------------------------------------
# Test 19 — format_text is human-readable (non-JSON first line)
# ---------------------------------------------------------------------------

def test_format_text_human_readable(tmp_path):
    _make_skill(tmp_path, "x", "x description")
    prims = vdg.discover_primitives(tmp_path)
    out = vdg.format_text([], len(prims))
    first_line = out.splitlines()[0]
    try:
        json.loads(first_line)
        raise AssertionError(f"First line is valid JSON: {first_line!r}")
    except json.JSONDecodeError:
        pass  # Expected — should be human-readable text


# ---------------------------------------------------------------------------
# Test 20 — script source has no literal user-home prefixes
# (marker comments carve out the _HOMEDIR_RE regex literal)
# ---------------------------------------------------------------------------

def test_no_homedir_in_script_self():
    script_path = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "validate_description_graph.py"
    source = script_path.read_text(encoding="utf-8")
    # Remove the regex-literal block (which must contain /Users and /home as pattern)
    lines = source.splitlines()
    filtered_lines = []
    in_block = False
    for line in lines:
        if "# REGEX-LITERAL-BEGIN" in line:
            in_block = True
            continue
        if "# REGEX-LITERAL-END" in line:
            in_block = False
            continue
        if not in_block:
            filtered_lines.append(line)
    filtered = "\n".join(filtered_lines)
    # Check no hardcoded user-home paths outside the regex literal
    import re
    homedir_re = re.compile(r"(/Users|/home)/[A-Za-z]")
    match = homedir_re.search(filtered)
    assert match is None, f"Found user-home literal outside regex block at: {match.group()!r}"
