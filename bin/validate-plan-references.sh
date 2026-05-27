#!/usr/bin/env bash
# Validate path + section-anchor citations in a plan markdown file.
# Exit 0 if every backticked path exists and every §"header" found in a
# co-cited markdown file (or no co-cited file). Exit 1 with one MISSING-*
# line per failure on stdout. Pre-ExitPlanMode hallucination gate.
# See issue #204 for context and the Liu et al. (FSE 2025) evidence base.
set -euo pipefail
export LC_ALL=C

plan="${1:-}"
[[ -n "$plan" && -f "$plan" ]] || { echo "validate-plan-references: usage: $0 <plan-path>" >&2; exit 2; }

repo_root=$(git -C "$(dirname "$plan")" rev-parse --show-toplevel 2>/dev/null || dirname "$plan")
fails=0

# Strip fenced code blocks before extraction so example paths inside ```...``` don't count.
body=$(awk 'BEGIN{f=0} /^```/{f=!f; next} f==0' "$plan")

# Path check: backticked tokens matching a file-extension whitelist.
# shellcheck disable=SC2016 # literal backticks bound the markdown inline-code regex
paths=$(printf '%s\n' "$body" | grep -oE '`[A-Za-z0-9_./-]+\.(py|md|ya?ml|json|toml|sh|txt)`' | tr -d '`' | sort -u)
while IFS= read -r p; do
  [[ -z "$p" ]] && continue
  [[ -e "$repo_root/$p" || -e "$p" ]] || { echo "MISSING-PATH: $p"; fails=$((fails + 1)); }
done <<< "$paths"

# Anchor check: each §"header" must resolve in the nearest preceding `*.md` token in the same paragraph.
while IFS= read -r para; do
  [[ "$para" != *'§"'* ]] && continue
  # shellcheck disable=SC2016
  file_re='`[A-Za-z0-9_./-]+\.md`'
  file=$(printf '%s' "$para" | grep -oE "$file_re" | tail -1 | tr -d '`' || true)
  while IFS= read -r anchor; do
    [[ -z "$anchor" ]] && continue
    if [[ -z "$file" ]]; then
      echo "WARN-ANCHOR-NO-FILE: §\"$anchor\"" >&2
      continue
    fi
    target="$repo_root/$file"; [[ -f "$target" ]] || target="$file"
    grep -qE "^#{1,6}[[:space:]]+${anchor}\$" "$target" 2>/dev/null \
      || { echo "MISSING-ANCHOR: §\"$anchor\" in $file"; fails=$((fails + 1)); }
  done < <(printf '%s' "$para" | grep -oE '§"[^"]+"' | sed -E 's/^§"(.*)"$/\1/' | sort -u)
done < <(printf '%s' "$body" | awk 'BEGIN{RS=""} {print; print "\n"}')

exit $(( fails > 0 ? 1 : 0 ))
