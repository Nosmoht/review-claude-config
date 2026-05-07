#!/usr/bin/env bash
# Wrapper for validate_description_graph.py used by `make validate-descriptions`.
# Exit 0 on warnings-only (exit 1 from validator) — tolerated by make validate.
# Exit 2 propagated as-is (errors present, CI must fail).
set -uo pipefail
PY="${PYTHON:-python3}"
"${PY}" scripts/validate_description_graph.py "$@" || ec=$?
ec="${ec:-0}"
if [ "${ec}" -eq 1 ]; then
  echo "validate_description_graph: warnings only (exit 1) — tolerated by make validate" >&2
  exit 0
fi
exit "${ec}"
