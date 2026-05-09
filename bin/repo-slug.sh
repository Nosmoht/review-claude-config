#!/usr/bin/env bash
# Canonical repo-slug resolver per references/repo-identification.md.
# Output: lowercase+alphanumeric+hyphen sanitized basename of input dir.
# Argument is treated as a literal path; no shell expansion of the value.
set -euo pipefail
export LC_ALL=C  # Exported (not just shell-var) so `tr` subprocess sees it;
                  # documented BSD-tr byte-semantics safety per POSIX locale rules.

target="${1:-$(pwd)}"
slug=$(basename "$target" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9-')

if [ -z "$slug" ]; then
  echo "repo-slug.sh: sanitize produced empty slug from '$target'" >&2
  exit 1
fi

printf '%s' "$slug"
