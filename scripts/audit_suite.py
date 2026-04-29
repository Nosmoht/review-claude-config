#!/usr/bin/env python3
"""Run the rubric binary evaluator against the entire skill suite and report
aggregated PASS/FAIL/NA counts per binary item.

Surfaces drift introduced by new rubric items (WS-5b, WS-6/7/8 triggers,
GA-Y/Z/S triggers, CE-CP, SP-IO, COMP-V/Sel, META-3c) across all
skills/*/SKILL.md without running the full /review-claude-config sweep.

Usage:
    python3 scripts/audit_suite.py [--show-fail-paths]

Outputs a markdown table to stdout. With --show-fail-paths, lists the
path of each FAIL per item.
"""

from __future__ import annotations

import pathlib
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from rubric_binary_evaluator import (  # noqa: E402
    BINARY_ITEM_IDS,
    REPO_ROOT,
    evaluate,
)


def main(show_fail_paths: bool = False) -> int:
    skills = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
    print(f"# Suite Audit — {len(skills)} skills\n")

    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"PASS": 0, "FAIL": 0, "NA": 0})
    fail_paths: dict[str, list[str]] = defaultdict(list)

    for path in skills:
        try:
            result = evaluate(path)
        except Exception as e:  # noqa: BLE001
            print(f"# WARN evaluator failed on {path.relative_to(REPO_ROOT)}: {e}")
            continue
        verdicts = result.get("verdicts", {})
        for item_id in BINARY_ITEM_IDS:
            v = verdicts.get(item_id, {}).get("verdict", "?")
            if v in counts[item_id]:
                counts[item_id][v] += 1
                if v == "FAIL":
                    fail_paths[item_id].append(str(path.relative_to(REPO_ROOT)))

    print("## Aggregate Verdict Counts\n")
    print("| Item | PASS | FAIL | NA |")
    print("|------|------|------|-----|")
    for item_id in BINARY_ITEM_IDS:
        c = counts[item_id]
        flag = " ⚠️" if c["FAIL"] > 0 else ""
        print(f"| {item_id}{flag} | {c['PASS']} | **{c['FAIL']}** | {c['NA']} |")

    total_fail = sum(c["FAIL"] for c in counts.values())
    print(f"\n**Total FAIL count across all items + skills: {total_fail}**")

    if show_fail_paths and total_fail > 0:
        print("\n## FAILing Skills per Item\n")
        for item_id in BINARY_ITEM_IDS:
            if fail_paths[item_id]:
                print(f"### {item_id} ({len(fail_paths[item_id])} fails)\n")
                for p in fail_paths[item_id]:
                    print(f"- `{p}`")
                print()

    return 0


if __name__ == "__main__":
    show = "--show-fail-paths" in sys.argv[1:]
    sys.exit(main(show))
