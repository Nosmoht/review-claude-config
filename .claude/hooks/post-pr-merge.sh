#!/usr/bin/env bash
# PostToolUse hook for Bash — after a `gh pr merge` call in this repo,
# fast-forward the local main branch to origin/main.
#
# Scope: repo-local. The hook is registered in this repo's
# .claude/settings.json and `${CLAUDE_PROJECT_DIR}` confines it to
# sessions opened in this worktree. The hardcoded `main` and `origin`
# names are intentional — this hook is not portable to repos with
# different default-branch or remote names.
#
# Trigger predicate (ALL must hold):
#   - tool_name == "Bash"
#   - tool_input.command begins with `gh pr merge` as a command token
#     (allowing leading whitespace; followed by whitespace or EOL).
#     Embedded matches in commit messages, heredocs, comments are
#     intentionally rejected.
#   - command does NOT contain "--auto" (server-side later-merge; the
#     pull would be premature).
#   - cwd is inside ${CLAUDE_PROJECT_DIR}.
#   - inside a non-submodule git work-tree.
#
# Action: when current branch is main → `git pull origin main --ff-only`;
# otherwise → `git fetch origin main:main` (updates ref in place without
# checkout, fast-forward-only).
#
# Note on tool exit-code: not checked. `git fetch origin main:main` is
# idempotent — if the prior merge failed, origin/main is unchanged and
# the fetch no-ops. Skipping the exit-code check avoids the chained-
# command false-suppress case (`gh pr merge && other-cmd` where the
# trailing command's failure would otherwise mask a successful merge).
#
# Failure mode: fail-safe. Any failure (jq error, network outage,
# divergent main, submodule, missing remote) is suppressed; exit 0.
# The hook never blocks Claude.
set -uo pipefail

input=$(cat)

tool_name=$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null) || exit 0
[[ "$tool_name" != "Bash" ]] && exit 0

cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0
[[ -z "$cmd" ]] && exit 0

# Match `gh pr merge` as a leading command token (allow leading
# whitespace). Refuses embedded matches.
[[ "$cmd" =~ ^[[:space:]]*gh[[:space:]]+pr[[:space:]]+merge([[:space:]]|$) ]] || exit 0

# Auto-merge defers the actual server-side merge; pull would be premature.
[[ "$cmd" == *"--auto"* ]] && exit 0

cwd=$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null) || cwd="$(pwd)"
[[ -z "$cwd" ]] && cwd="$(pwd)"

# Scope to this project. If CLAUDE_PROJECT_DIR is unset (rare), fall
# through to the worktree-check below.
project="${CLAUDE_PROJECT_DIR:-}"
if [[ -n "$project" && "$cwd" != "$project" && "$cwd" != "$project"/* ]]; then
    exit 0
fi

cd "$cwd" 2>/dev/null || exit 0

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# Refuse to operate inside a submodule (its origin/main is unrelated to
# the parent repo's PR).
super=$(git rev-parse --show-superproject-working-tree 2>/dev/null || true)
[[ -n "$super" ]] && exit 0

current=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0

if [[ "$current" == "main" ]]; then
    out=$(git pull origin main --ff-only 2>&1) || {
        printf 'post-pr-merge: ff-pull on main failed: %s\n' "$out" >&2
        exit 0
    }
    printf 'post-pr-merge: local main fast-forwarded\n' >&2
else
    out=$(git fetch origin main:main 2>&1) || {
        printf 'post-pr-merge: local main ref update failed: %s\n' "$out" >&2
        exit 0
    }
    printf 'post-pr-merge: local main ref updated (HEAD on %s)\n' "$current" >&2
fi

exit 0
