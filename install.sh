#!/usr/bin/env bash
# install.sh — preflight check for review-claude-config plugin install.
#
# This script verifies host prerequisites and prints the canonical
# install commands. It does NOT install the plugin automatically — the
# `claude plugin install` flow is the supported entry point. Running
# this script catches version mismatches before the plugin is fetched.

set -euo pipefail

PLUGIN_NAME="skill-quality"
MARKETPLACE="ntbc-plugins"
MARKETPLACE_REPO="Nosmoht/review-claude-config"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=11

ok()   { printf '  \033[32mok\033[0m  %s\n' "$*"; }
warn() { printf '  \033[33m!!\033[0m  %s\n' "$*"; }
fail() { printf '  \033[31mxx\033[0m  %s\n' "$*"; exit 1; }
info() { printf '  ..  %s\n' "$*"; }

echo "review-claude-config preflight"
echo "------------------------------"

# Claude Code CLI
if command -v claude >/dev/null 2>&1; then
  CLAUDE_VERSION="$(claude --version 2>/dev/null || echo unknown)"
  ok "claude CLI present (${CLAUDE_VERSION})"
else
  fail "claude CLI not found in PATH. Install from https://claude.com/claude-code first."
fi

# Python version
if command -v python3 >/dev/null 2>&1; then
  PY_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  PY_MAJOR="${PY_VERSION%.*}"
  PY_MINOR="${PY_VERSION#*.}"
  if [ "${PY_MAJOR}" -gt "${MIN_PYTHON_MAJOR}" ] || \
     { [ "${PY_MAJOR}" -eq "${MIN_PYTHON_MAJOR}" ] && [ "${PY_MINOR}" -ge "${MIN_PYTHON_MINOR}" ]; }; then
    ok "python3 ${PY_VERSION} (>= ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR})"
  else
    fail "python3 ${PY_VERSION} is too old; need >= ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}."
  fi
else
  fail "python3 not found in PATH."
fi

# Hooks directory sanity check (only relevant when running from a clone)
if [ -d "hooks" ] && [ -f "hooks/hooks.json" ]; then
  ok "hooks/hooks.json present (running from repo clone)"
else
  info "hooks/hooks.json not seen here — running outside repo clone is fine"
fi

echo
echo "Install via personal marketplace:"
echo
echo "  claude plugin marketplace add ${MARKETPLACE_REPO}"
echo "  claude plugin install ${PLUGIN_NAME}@${MARKETPLACE}"
echo
echo "Dev mode (run from a repo clone, takes precedence over marketplace):"
echo
echo "  claude --plugin-dir ."
echo
echo "See README.md for update / rollback flows."
