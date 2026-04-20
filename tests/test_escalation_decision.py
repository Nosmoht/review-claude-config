"""Tests for scripts/escalation_decision.py."""

from __future__ import annotations

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from escalation_decision import decide  # noqa: E402


def _base():
    return {
        "status": "success",
        "degraded_mode": False,
        "missing_perspectives": [],
        # 85.0 is 5 pts from both 80 and 90 — safely outside ESC-1 proximity
        "weighted_score": 85.0,
        "findings": [],
        "perspective_scores": {"clarity": 84.0, "correctness": 86.0, "integration": 85.0},
    }


class TestESC1:
    def test_trigger_near_boundary(self):
        cert = _base()
        cert["weighted_score"] = 80.1  # within 2.5 of 80
        r = decide(cert)
        assert r["escalation_required"]
        assert any("ESC-1" in x for x in r["reasons"])

    def test_no_trigger_far_from_boundary(self):
        cert = _base()
        cert["weighted_score"] = 85.0  # 5 pts from 80 and 90
        r = decide(cert)
        assert not any("ESC-1" in x for x in r["reasons"])

    def test_exactly_at_boundary(self):
        cert = _base()
        cert["weighted_score"] = 90.0
        r = decide(cert)
        assert any("ESC-1" in x for x in r["reasons"])


class TestESC2:
    def test_u_shape_triggers(self):
        cert = _base()
        cert["findings"] = [
            {"severity": "High"},
            {"severity": "Low"},
        ]
        r = decide(cert)
        assert any("ESC-2" in x for x in r["reasons"])

    def test_with_medium_no_trigger(self):
        cert = _base()
        cert["findings"] = [
            {"severity": "High"},
            {"severity": "Medium"},
            {"severity": "Low"},
        ]
        r = decide(cert)
        assert not any("ESC-2" in x for x in r["reasons"])

    def test_only_high_no_trigger(self):
        cert = _base()
        cert["findings"] = [{"severity": "High"}, {"severity": "High"}]
        r = decide(cert)
        assert not any("ESC-2" in x for x in r["reasons"])


class TestESC3:
    def test_divergence_triggers(self):
        cert = _base()
        cert["weighted_score"] = 82.0  # avoid ESC-1 at 80
        cert["perspective_scores"] = {"clarity": 95.0, "correctness": 70.0, "integration": 82.0}
        r = decide(cert)
        assert any("ESC-3" in x for x in r["reasons"])

    def test_small_divergence_no_trigger(self):
        cert = _base()
        cert["weighted_score"] = 82.0
        cert["perspective_scores"] = {"clarity": 85.0, "correctness": 80.0, "integration": 82.0}
        r = decide(cert)
        assert not any("ESC-3" in x for x in r["reasons"])

    def test_one_perspective_no_esc3(self):
        cert = _base()
        cert["perspective_scores"] = {"clarity": 95.0}
        r = decide(cert)
        # Only one score — cannot compute divergence; ESC-3 silent
        assert not any("ESC-3" in x for x in r["reasons"])


class TestESC4:
    def test_deep_flag(self):
        cert = _base()
        r = decide(cert, deep_flag=True)
        assert any("ESC-4" in x for x in r["reasons"])


class TestESC5:
    def test_degraded_triggers(self):
        cert = _base()
        cert["degraded_mode"] = True
        cert["missing_perspectives"] = ["integration"]
        r = decide(cert)
        assert any("ESC-5" in x for x in r["reasons"])


class TestComposite:
    def test_no_triggers(self):
        r = decide(_base())
        assert r["escalation_required"] is False
        assert r["reasons"] == []

    def test_multiple_simultaneously(self):
        cert = _base()
        cert["weighted_score"] = 80.1  # ESC-1
        cert["degraded_mode"] = True  # ESC-5
        cert["missing_perspectives"] = ["clarity"]
        cert["findings"] = [{"severity": "High"}, {"severity": "Low"}]  # ESC-2
        r = decide(cert, deep_flag=True)  # ESC-4
        assert r["escalation_required"]
        assert len(r["reasons"]) >= 4
