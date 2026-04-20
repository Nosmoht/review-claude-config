#!/usr/bin/env python3
"""Decide whether a merged review certificate requires escalation.

Rules (all decidable without an LLM call):
  ESC-1: weighted_score within 2.5 points of any grade boundary (60/70/80/90).
  ESC-2: severity set contains "High" AND "Low" but NOT "Medium" (U-shape).
  ESC-3: max-min perspective weighted-score divergence >=20 points
         (computed only over perspectives that produced a weighted_score).
         If fewer than 2 perspectives produced a score, ESC-3 is NULL (not
         triggered).
  ESC-4: --deep flag passed (external to this script — pass --deep to force).
  ESC-5: merged cert has degraded_mode=true (any perspective missing or
         malformed).

Usage:
  python3 escalation_decision.py <merged-cert.json> [--deep]

Output (stdout): JSON:
  {
    "escalation_required": bool,
    "reasons": ["ESC-1: ...", "ESC-5: ..."]
  }
"""

from __future__ import annotations

import json
import pathlib
import sys

GRADE_BOUNDARIES = (60, 70, 80, 90)
ESC1_PROXIMITY = 2.5
ESC3_DIVERGENCE = 20.0


def decide(merged: dict, deep_flag: bool = False) -> dict:
    reasons: list[str] = []

    if deep_flag:
        reasons.append("ESC-4: --deep flag passed by user")

    # ESC-5: degraded_mode
    if merged.get("degraded_mode"):
        missing = ", ".join(merged.get("missing_perspectives", [])) or "unknown"
        reasons.append(f"ESC-5: degraded mode — missing perspectives: {missing}")

    # ESC-1: numeric proximity to grade boundary
    score = merged.get("weighted_score")
    if isinstance(score, (int, float)):
        for boundary in GRADE_BOUNDARIES:
            if abs(score - boundary) <= ESC1_PROXIMITY:
                reasons.append(
                    f"ESC-1: weighted_score {score:.2f} within {ESC1_PROXIMITY} of grade boundary {boundary}"
                )
                break

    # ESC-2: U-shape severity set
    severities = {f.get("severity") for f in merged.get("findings", [])}
    if "High" in severities and "Low" in severities and "Medium" not in severities:
        reasons.append("ESC-2: severity set contains High and Low but no Medium")

    # ESC-3: perspective score divergence
    scores = [v for v in merged.get("perspective_scores", {}).values() if isinstance(v, (int, float))]
    if len(scores) >= 2:
        divergence = max(scores) - min(scores)
        if divergence >= ESC3_DIVERGENCE:
            reasons.append(f"ESC-3: perspective score divergence {divergence:.2f} >= {ESC3_DIVERGENCE}")

    return {"escalation_required": bool(reasons), "reasons": reasons}


def main() -> int:
    args = sys.argv[1:]
    deep = "--deep" in args
    args = [a for a in args if a != "--deep"]
    if len(args) != 1:
        print(
            "Usage: escalation_decision.py <merged-cert.json> [--deep]",
            file=sys.stderr,
        )
        return 2
    cert_path = pathlib.Path(args[0])
    try:
        merged = json.loads(cert_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read merged cert: {e}", file=sys.stderr)
        return 2
    result = decide(merged, deep_flag=deep)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
