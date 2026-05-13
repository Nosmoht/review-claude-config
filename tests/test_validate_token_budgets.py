"""Tests for scripts/validate_token_budgets.py — token budget enforcement."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import validate_token_budgets
from validate_token_budgets import (
    classify,
    estimate_tokens,
    get_budget,
)
from validate_token_budgets import main as validate_main
from validate_token_budgets import (
    validate_token_budgets as validate_fn,
)


@pytest.fixture(autouse=True)
def _reset_token_budgets_data():
    """Reload module constants before and after each test.

    Existing tests that use monkeypatch to set REPO_ROOT use file names
    that fall through to DEFAULT_BUDGET, so they don't depend on _data
    being reloaded. However, tests that monkeypatch TOKEN_BUDGETS_JSON_PATH
    need fresh _data on entry.

    Reload BEFORE yield: ensures test sees fresh state if a previous test
    polluted the environment. Reload AFTER yield: restores production state
    for subsequent tests.
    """
    validate_token_budgets._reload_data()
    yield
    validate_token_budgets._reload_data()


class TestEstimateTokens:
    def test_basic(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("a" * 400)
        assert estimate_tokens(f) == 100

    def test_empty(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("")
        assert estimate_tokens(f) == 0

    def test_nonexistent(self, tmp_path):
        assert estimate_tokens(tmp_path / "nope.md") == 0


class TestGetBudget:
    def test_rubric(self, tmp_path):
        assert get_budget(tmp_path / "scoring-rubric.md") == 14000

    def test_baseline(self, tmp_path):
        assert get_budget(tmp_path / "engineering-baseline.md") == 4350

    def test_signal_catalog(self, tmp_path):
        assert get_budget(tmp_path / "signal-catalog.md") == 1400

    def test_domain_cache(self, tmp_path):
        p = tmp_path / "skills" / "x" / "references" / "domain-cache" / "cilium.md"
        assert get_budget(p) == 800

    def test_eval_guide(self, tmp_path):
        assert get_budget(tmp_path / "skill-evaluation-guide.md") == 1700

    def test_default(self, tmp_path):
        assert get_budget(tmp_path / "other-file.md") == 500


class TestClassify:
    def test_pass(self):
        assert classify(300, 500) == "PASS"

    def test_warn_at_80_pct(self):
        assert classify(400, 500) == "WARN"

    def test_warn_at_100_pct(self):
        assert classify(500, 500) == "WARN"

    def test_fail_over_budget(self):
        assert classify(501, 500) == "FAIL"

    def test_zero_budget(self):
        assert classify(1, 0) == "FAIL"


class TestValidateTokenBudgets:
    def test_all_pass(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_token_budgets, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-skill" / "references"
        d.mkdir(parents=True)
        (d / "guide.md").write_text("x" * 400)  # 100 tokens, budget 500
        errors = validate_fn()
        assert errors == []

    def test_fail_over_budget(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_token_budgets, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-skill" / "references"
        d.mkdir(parents=True)
        (d / "guide.md").write_text("x" * 2400)  # 600 tokens, budget 500
        errors = validate_fn()
        assert len(errors) == 1
        assert "guide.md" in errors[0]
        assert "600 tokens" in errors[0]

    def test_warn_prints(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(validate_token_budgets, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-skill" / "references"
        d.mkdir(parents=True)
        (d / "guide.md").write_text("x" * 1800)  # 450 tokens, 90% of 500
        errors = validate_fn()
        assert errors == []
        assert "WARN" in capsys.readouterr().out

    def test_named_file_gets_custom_budget(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_token_budgets, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-claude-config" / "references"
        d.mkdir(parents=True)
        # scoring-rubric.md has budget 2000 → 1600 tokens = WARN, not FAIL
        (d / "scoring-rubric.md").write_text("x" * 6400)  # 1600 tokens
        errors = validate_fn()
        assert errors == []

    def test_domain_cache_budget(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_token_budgets, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-claude-config" / "references" / "domain-cache"
        d.mkdir(parents=True)
        (d / "cilium.md").write_text("x" * 3600)  # 900 tokens, budget 800
        errors = validate_fn()
        assert len(errors) == 1
        assert "domain-cache" in errors[0]

    def test_domain_cache_index_skipped(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_token_budgets, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-claude-config" / "references" / "domain-cache"
        d.mkdir(parents=True)
        (d / "INDEX.md").write_text("x" * 10000)  # Would fail if not skipped
        errors = validate_fn()
        assert errors == []

    def test_no_files_returns_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_token_budgets, "REPO_ROOT", tmp_path)
        errors = validate_fn()
        assert len(errors) == 1
        assert "No reference files" in errors[0]

    def test_multiple_failures(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_token_budgets, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-skill" / "references"
        d.mkdir(parents=True)
        (d / "a.md").write_text("x" * 2400)  # 600 tokens
        (d / "b.md").write_text("x" * 3200)  # 800 tokens
        errors = validate_fn()
        assert len(errors) == 2


class TestMain:
    def test_all_pass_returns_zero(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(validate_token_budgets, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-skill" / "references"
        d.mkdir(parents=True)
        (d / "guide.md").write_text("x" * 400)
        result = validate_main()
        assert result == 0
        assert "OK" in capsys.readouterr().out

    def test_failures_return_one(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(validate_token_budgets, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-skill" / "references"
        d.mkdir(parents=True)
        (d / "guide.md").write_text("x" * 2400)
        result = validate_main()
        assert result == 1
        output = capsys.readouterr().out
        assert "ERROR" in output
        assert "over budget" in output

    def test_no_files_returns_one(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(validate_token_budgets, "REPO_ROOT", tmp_path)
        result = validate_main()
        assert result == 1
        output = capsys.readouterr().out
        assert "No reference files" in output
        assert "error(s) found" in output


class TestMissingJsonRaises:
    """Tests for the RuntimeError path when token-budgets.json is missing."""

    def test_missing_json_raises(self, tmp_path, monkeypatch):
        """_load_cached raises RuntimeError when token-budgets.json is absent.

        Hits the missing-file guard that produces a clear error message
        referencing the schema path, rather than a generic FileNotFoundError.
        """
        missing = tmp_path / "token-budgets.json"
        monkeypatch.setenv("TOKEN_BUDGETS_JSON_PATH", str(missing))
        validate_token_budgets._reload_data.__func__ if hasattr(validate_token_budgets._reload_data, "__func__") else None
        # Clear cache so the new env var is picked up
        validate_token_budgets._load_cached.cache_clear()
        with pytest.raises(RuntimeError, match="token-budgets.json missing"):
            validate_token_budgets._load_cached(str(missing))
