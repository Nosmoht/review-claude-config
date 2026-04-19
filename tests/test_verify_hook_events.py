"""Tests for scripts/verify_hook_events.py — hook event-to-CLI-version map."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import verify_hook_events
from verify_hook_events import EVENT_MIN_VERSION, parse_semver, verify


class TestParseSemver:
    def test_basic(self):
        assert parse_semver("2.1.114") == (2, 1, 114)

    def test_v_prefix(self):
        assert parse_semver("v2.1.114") == (2, 1, 114)

    def test_invalid(self):
        try:
            parse_semver("bad")
        except ValueError:
            return
        raise AssertionError("expected ValueError")


class TestEventCatalog:
    def test_26_events(self):
        assert len(EVENT_MIN_VERSION) == 26

    def test_known_2026_q1_additions(self):
        assert EVENT_MIN_VERSION["PostToolUseFailure"] == "2.1.76"
        assert EVENT_MIN_VERSION["CwdChanged"] == "2.1.83"
        assert EVENT_MIN_VERSION["FileChanged"] == "2.1.83"
        assert EVENT_MIN_VERSION["TaskCreated"] == "2.1.84"
        assert EVENT_MIN_VERSION["PermissionDenied"] == "2.1.89"


class TestVerify:
    def test_known_event_supported(self, tmp_path):
        h = tmp_path / "hooks.json"
        h.write_text(json.dumps({"hooks": {"PreToolUse": []}}))
        out = verify(h, "2.1.114")
        assert out == [{"event": "PreToolUse", "status": "ok", "details": "min CLI 2.0.0"}]

    def test_known_event_version_too_old(self, tmp_path):
        h = tmp_path / "hooks.json"
        h.write_text(json.dumps({"hooks": {"TaskCreated": []}}))
        out = verify(h, "2.1.80")
        assert out[0]["status"] == "version_too_old"
        assert "2.1.84" in out[0]["details"]

    def test_unknown_event(self, tmp_path):
        h = tmp_path / "hooks.json"
        h.write_text(json.dumps({"hooks": {"FutureEvent": []}}))
        out = verify(h, "2.1.114")
        assert out[0]["status"] == "unknown_event"
        assert "FutureEvent" in out[0]["details"]

    def test_no_cli_version_skips_version_check(self, tmp_path):
        h = tmp_path / "hooks.json"
        h.write_text(json.dumps({"hooks": {"TaskCreated": []}}))
        out = verify(h, None)
        assert out[0]["status"] == "ok"

    def test_top_level_dict_no_hooks_key(self, tmp_path):
        h = tmp_path / "hooks.json"
        h.write_text(json.dumps({"PreToolUse": []}))
        out = verify(h, "2.1.114")
        assert out[0]["event"] == "PreToolUse"
